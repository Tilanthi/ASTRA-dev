#!/usr/bin/env python3
"""
POWERLAW_VALIDATION_V1 Campaign Runner — Peer Review Response
Priority 5: High-resolution (2×) power-law exponent validation
30 sims: f=[1.2..3.0 ×10], β=[0.5,1.0,2.0], seed=42 only

Resolution: 512×128×128 (64 cells/λ_J, 2× baseline)
Domain: 8×2×2 λ_J (x1=[0,8], x2=x3=[-1,1])
Meshblock: 32×32×32 → 16×4×4=256 total → np=64 (4/proc)
max_concurrent=3 (3×64=192 CPUs)
tlim=2.0 t_J, HST only (no HDF5 — just timing for power law)
"""
import os, json, re, subprocess, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

ATHENA_EXE   = "/home/fetch-agi/athena/bin/athena"
OUTPUT_BASE  = Path("/data/peer_review_response_runs/POWERLAW_VALIDATION_V1")
LOG_FILE     = OUTPUT_BASE / "campaign.log"
STATUS_FILE  = OUTPUT_BASE / "results.json"
NP_PER_SIM   = 64
MAX_CONC     = 3
TIMEOUT_SEC  = 1800
DT_FRAG      = 1e-8
FOUR_PI_G    = 39.478417604357

F_VALUES    = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
BETA_VALUES = [0.5, 1.0, 2.0]
SEEDS       = [42]

log_lock = threading.Lock()
_results = []
_rlock = threading.Lock()

OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with log_lock:
        print(line, flush=True)
        with open(LOG_FILE, "a") as fh:
            fh.write(line + "\n")

def make_athinput(f, beta, seed, rundir):
    sid = f"POWERLAW_f{f}_beta{beta}_s{seed}"
    txt = f"""<job>
problem_id = {sid}

<time>
cfl_number = 0.3
nlim       = -1
tlim       = 2.0

<output1>
file_type  = hst
dt         = 0.005
id         = hst

<mesh>
nx1 = 512
nx2 = 128
nx3 = 128
x1min = 0.0
x1max = 8.0
x2min = -1.0
x2max = 1.0
x3min = -1.0
x3max = 1.0
ix1_bc = periodic
ox1_bc = periodic
ix2_bc = periodic
ox2_bc = periodic
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 32
nx2 = 32
nx3 = 32

<hydro>
iso_sound_speed = 1.0

<gravity>
grav_mean_rho = {f}

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f}
plasma_beta     = {beta}
mach_number     = 1.0
W_core          = 0.3
perturb_ampl    = 0.0001
random_seed     = {seed}
bfield_geometry = longitudinal
theta_deg       = 0.0
"""
    inp = rundir / "athinput"
    inp.write_text(txt)
    return str(inp)

CYCLE_PAT = re.compile(r'time=([0-9.e+\-]+)\s+dt=([0-9.e+\-]+)')

def find_tfrag_from_hst(hst_path):
    try:
        with open(hst_path) as f:
            lines = [l for l in f if not l.startswith('#') and l.strip()]
        for line in reversed(lines):
            p = line.split()
            if len(p) >= 2 and float(p[1]) >= DT_FRAG:
                return float(p[0])
        if lines:
            return float(lines[-1].split()[0])
    except: pass
    return None

def run_sim(f, beta, seed):
    sid = f"POWERLAW_f{f}_beta{beta}_s{seed}"
    rundir = OUTPUT_BASE / sid
    rundir.mkdir(parents=True, exist_ok=True)

    hst_path = rundir / f"{sid}.hst"
    if hst_path.exists():
        tf = find_tfrag_from_hst(hst_path)
        if tf is not None:
            log(f"SKIP {sid}: already done")
            return {"id": sid, "f": f, "beta": beta, "seed": seed,
                    "outcome": "FRAG", "t_frag": tf, "skipped": True}

    inp = make_athinput(f, beta, seed, rundir)
    cmd = ["mpirun", "-np", str(NP_PER_SIM), ATHENA_EXE, "-i", inp,
           "-d", str(rundir)]
    t0 = time.time()
    stdout_lines = []
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 cwd=str(rundir), text=True)
        last_dt = 1.0
        outcome = "TIMEOUT"
        t_frag = None
        for line in proc.stdout:
            stdout_lines.append(line)
            m = CYCLE_PAT.search(line)
            if m:
                sim_t = float(m.group(1))
                dt_v  = float(m.group(2))
                last_dt = dt_v
                if dt_v < DT_FRAG:
                    outcome = "FRAG"
                    t_frag = sim_t
                    proc.kill(); break
        proc.wait(timeout=60)
        wall = time.time() - t0
        if outcome != "FRAG":
            hst = rundir / f"{sid}.hst"
            tf = find_tfrag_from_hst(str(hst)) if hst.exists() else None
            if tf is not None:
                outcome = "FRAG"; t_frag = tf
        tfstr = 'N/A' if t_frag is None else '{:.4f}'.format(t_frag)
        log(f"{outcome:8s} {sid}  t_frag={tfstr}  dt={last_dt:.2e}  wall={wall:.0f}s")
    except Exception as e:
        outcome, t_frag, wall = "FAILED", None, time.time()-t0
        log(f"FAILED  {sid}  error={e}")
    with open(rundir / "stdout.txt", "w") as fh:
        fh.writelines(stdout_lines)
    res = {"id": sid, "f": f, "beta": beta, "seed": seed,
           "outcome": outcome, "t_frag": t_frag, "wall_s": wall}
    with _rlock:
        _results.append(res)
        with open(STATUS_FILE, "w") as fh:
            json.dump(_results, fh, indent=2)
    return res

def main():
    sims = [(f, b, s) for f in F_VALUES for b in BETA_VALUES for s in SEEDS]
    log(f"POWERLAW_VALIDATION_V1: {len(sims)} sims | np={NP_PER_SIM} | max_conc={MAX_CONC}")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_CONC) as ex:
        futs = {ex.submit(run_sim, f, b, s): (f,b,s) for (f,b,s) in sims}
        for fut in as_completed(futs):
            _ = fut.result()
    n_frag = sum(1 for r in _results if r["outcome"]=="FRAG")
    n_to   = sum(1 for r in _results if r["outcome"]=="TIMEOUT")
    log(f"DONE  FRAG={n_frag}/{len(sims)}  TIMEOUT={n_to}  wall={time.time()-t0:.0f}s")
    with open(STATUS_FILE, "w") as fh:
        json.dump(_results, fh, indent=2)

if __name__ == "__main__":
    main()
