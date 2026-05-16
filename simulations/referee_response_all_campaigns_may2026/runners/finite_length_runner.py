#!/usr/bin/env python3
"""
FINITE_LENGTH_V1 Campaign Runner — Peer Review Response (CRITICAL Priority 1)
120 sims: f=[1.2,1.5,1.8,2.2,2.6], β=[0.5,1.0,2.0], L=[2,4,6,8] λ_J, seeds=[42,137]

Finite-length filament in ambient medium — embedded in periodic domain.
Domain: x1=[0, L_fil+2.0], x2=x3=[-0.75,0.75] (1λ_J buffer each end)
Meshblock: 32×24×24 | Resolution: 32 cells/λ_J
np varies by L:
  L=2: domain 4.0 λ_J → 128×48×48 → 4×2×2=16 meshblocks → np=8  max_conc=28
  L=4: domain 6.0 λ_J → 192×48×48 → 6×2×2=24 meshblocks → np=12 max_conc=18
  L=6: domain 8.0 λ_J → 256×48×48 → 8×2×2=32 meshblocks → np=16 max_conc=14
  L=8: domain 10.0 λ_J → 320×48×48 → 10×2×2=40 meshblocks → np=20 max_conc=11
HDF5 at dt=0.1 t_J, tlim=3.0 t_J (longer to see late longitudinal frag)

REQUIRES: /home/fetch-agi/athena/bin/athena_finite_length
"""
import os, json, re, subprocess, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

ATHENA_EXE   = "/home/fetch-agi/athena/bin/athena_finite_length"
OUTPUT_BASE  = Path("/data/peer_review_response_runs/FINITE_LENGTH_V1")
LOG_FILE     = OUTPUT_BASE / "campaign.log"
STATUS_FILE  = OUTPUT_BASE / "results.json"
TIMEOUT_SEC  = 1200
DT_FRAG      = 1e-8
FOUR_PI_G    = 39.478417604357

F_VALUES    = [1.2, 1.5, 1.8, 2.2, 2.6]
BETA_VALUES = [0.5, 1.0, 2.0]
L_VALUES    = [2.0, 4.0, 6.0, 8.0]
SEEDS       = [42, 137]

# Domain configuration per L_fil value
# L_tot = L_fil + 2.0 (1 λ_J buffer each end)
DOMAIN_CFG = {
    2.0: {"nx1": 128, "x1max": 4.0,  "np": 8,  "max_conc": 28},
    4.0: {"nx1": 192, "x1max": 6.0,  "np": 12, "max_conc": 18},
    6.0: {"nx1": 256, "x1max": 8.0,  "np": 16, "max_conc": 14},
    8.0: {"nx1": 320, "x1max": 10.0, "np": 20, "max_conc": 11},
}

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

def make_athinput(f, beta, L_fil, seed, rundir):
    dcfg = DOMAIN_CFG[L_fil]
    nx1  = dcfg["nx1"]
    x1max = dcfg["x1max"]
    l_str = f"{L_fil:.0f}".replace('.','p')
    sid = f"FINLEN_f{f}_beta{beta}_L{l_str}_s{seed}"
    txt = f"""<job>
problem_id = {sid}

<time>
cfl_number = 0.3
nlim       = -1
tlim       = 3.0

<output1>
file_type  = hst
dt         = 0.01
id         = hst

<output2>
file_type  = hdf5
dt         = 0.1
id         = snap
variable   = prim

<mesh>
nx1 = {nx1}
nx2 = 48
nx3 = 48
x1min = 0.0
x1max = {x1max}
x2min = -0.75
x2max = 0.75
x3min = -0.75
x3max = 0.75
ix1_bc = periodic
ox1_bc = periodic
ix2_bc = periodic
ox2_bc = periodic
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 32
nx2 = 24
nx3 = 24

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
filament_length = {L_fil}
rho_ambient     = 0.01
end_taper       = 0.5
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

def run_sim(f, beta, L_fil, seed):
    l_str = f"{L_fil:.0f}".replace('.','p')
    sid = f"FINLEN_f{f}_beta{beta}_L{l_str}_s{seed}"
    rundir = OUTPUT_BASE / sid
    rundir.mkdir(parents=True, exist_ok=True)

    hst_path = rundir / f"{sid}.hst"
    if hst_path.exists():
        tf = find_tfrag_from_hst(hst_path)
        if tf is not None:
            log(f"SKIP {sid}")
            return {"id": sid, "f": f, "beta": beta, "L_fil": L_fil, "seed": seed,
                    "outcome": "FRAG", "t_frag": tf, "skipped": True}

    dcfg = DOMAIN_CFG[L_fil]
    np_sim = dcfg["np"]
    inp = make_athinput(f, beta, L_fil, seed, rundir)
    cmd = ["mpirun", "-np", str(np_sim), ATHENA_EXE, "-i", inp, "-d", str(rundir)]
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
                if time.time() - t0 > TIMEOUT_SEC:
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

    # Clean HDF5 after recording t_frag (we have what we need for λ/W from snapshot)
    # Keep for now — analysis script will clean them up
    res = {"id": sid, "f": f, "beta": beta, "L_fil": L_fil, "seed": seed,
           "outcome": outcome, "t_frag": t_frag, "wall_s": wall}
    with _rlock:
        _results.append(res)
        with open(STATUS_FILE, "w") as fh:
            json.dump(_results, fh, indent=2)
    return res

def main():
    # Run L batches in order (smallest first — fastest)
    sims = [(f, b, L, s) for L in L_VALUES for f in F_VALUES for b in BETA_VALUES for s in SEEDS]
    total = len(sims)
    log(f"FINITE_LENGTH_V1: {total} sims across 4 L values")
    t0 = time.time()

    # Group by L and run with appropriate concurrency
    for L_fil in L_VALUES:
        batch = [(f, b, L_fil, s) for f in F_VALUES for b in BETA_VALUES for s in SEEDS]
        max_conc = DOMAIN_CFG[L_fil]["max_conc"]
        log(f"--- L={L_fil}λ_J batch: {len(batch)} sims, max_conc={max_conc} ---")
        with ThreadPoolExecutor(max_workers=max_conc) as ex:
            futs = {ex.submit(run_sim, f, b, L_fil, s): (f,b,L_fil,s) for (f,b,L_fil,s) in batch}
            for fut in as_completed(futs):
                _ = fut.result()
        log(f"--- L={L_fil}λ_J batch DONE ---")

    n_frag = sum(1 for r in _results if r["outcome"]=="FRAG")
    n_to   = sum(1 for r in _results if r["outcome"]=="TIMEOUT")
    log(f"COMPLETE FINITE_LENGTH_V1  FRAG={n_frag}/{total}  TIMEOUT={n_to}  wall={time.time()-t0:.0f}s")
    with open(STATUS_FILE, "w") as fh:
        json.dump(_results, fh, indent=2)

if __name__ == "__main__":
    main()
