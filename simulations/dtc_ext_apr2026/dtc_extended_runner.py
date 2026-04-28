#!/usr/bin/env python3
"""
DTC-EXTENDED Verification Campaign — Apr 2026

PURPOSE: Verify whether the DTC β=0.3, M=1 stable ridge is:
  (A) Genuinely stable (survives to tlim=4.0 t_J in DTC-domain geometry), OR
  (B) A domain artefact (also radially collapses, DTC tlim=1.5 was too short to see it)

DESIGN:
  Domain: 4×4×2 λ_J (DTC-matching: x1=4, x2=±2, x3=±1)
  Mesh: 128×128×64, meshblocks 32×32×32 → 32 total, np=16
  tlim: 4.0 t_J (vs DTC's 1.5 t_J — >2.5× extended)
  HDF5: dt=0.1 t_J — captures collapse at t~0.3 t_J if it occurs
  Timeout: 7200s (2 hours — conservative for stable sims that run to tlim)

TEST CASES:
  DTC STABLE (from DTC campaign) — do they stay stable to 4.0 t_J?
    f=1.4, β=0.3, M=1, seeds 42+137
    f=1.6, β=0.3, M=1, seeds 42+137
    f=2.0, β=0.3, M=1, seeds 42+137
  DTC FRAG control — should fragment quickly (validates setup):
    f=1.4, β=1.0, M=1, seed 42
  Total: 7 sims
"""

import json, re, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

ATHENA_EXE     = "/home/fetch-agi/athena/bin/athena"
OUTPUT_BASE    = Path("/data/dtc_ext_runs")
NP_PER_SIM     = 16
MAX_CONCURRENT = 7       # all 7 at once: 7×16=112 CPUs
TIMEOUT_SEC    = 7200    # 2 hours — stable sims reach tlim naturally in ~200s
DT_FRAG_THRESHOLD = 1e-8

FOUR_PI_G = 39.478417604357

CONFIGS = [
    # DTC stable cases extended to tlim=4.0
    dict(f=1.4, beta=0.3, seed=42,  label="DTC_STABLE"),
    dict(f=1.4, beta=0.3, seed=137, label="DTC_STABLE"),
    dict(f=1.6, beta=0.3, seed=42,  label="DTC_STABLE"),
    dict(f=1.6, beta=0.3, seed=137, label="DTC_STABLE"),
    dict(f=2.0, beta=0.3, seed=42,  label="DTC_STABLE"),
    dict(f=2.0, beta=0.3, seed=137, label="DTC_STABLE"),
    # DTC FRAG control (β=1.0 always fragmented in DTC)
    dict(f=1.4, beta=1.0, seed=42,  label="DTC_FRAG_CONTROL"),
]

CYCLE_PAT = re.compile(r'cycle=(\d+)\s+time=([0-9.e+\-]+)\s+dt=([0-9.e+\-]+)')

OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def make_athinput(f, beta, seed):
    sim_id = f"dtcext_f{f}_beta{beta}_s{seed}"
    return f"""<job>
problem_id = {sim_id}

<time>
cfl_number = 0.3
nlim       = -1
tlim       = 4.0

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
nx1 = 128
nx2 = 128
nx3 = 64
x1min = 0.0
x1max = 4.0
x2min = -2.0
x2max = 2.0
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

def read_stdout_dt(stdout_path):
    t_frag = None; dt_min = float('inf'); t_final = None
    try:
        with open(stdout_path, 'r', errors='replace') as fh:
            for line in fh:
                m = CYCLE_PAT.search(line)
                if not m: continue
                t = float(m.group(2)); dt = float(m.group(3))
                t_final = t
                if dt < dt_min: dt_min = dt
                if t_frag is None and dt < DT_FRAG_THRESHOLD:
                    t_frag = round(t, 6)
    except Exception:
        pass
    return t_frag, (dt_min if dt_min < float('inf') else None), t_final

def run_sim(cfg):
    f, beta, seed, label = cfg['f'], cfg['beta'], cfg['seed'], cfg['label']
    sim_id  = f"dtcext_f{f}_beta{beta}_s{seed}"
    sim_dir = OUTPUT_BASE / sim_id
    sim_dir.mkdir(exist_ok=True)

    status_file   = sim_dir / "status.json"
    stdout_file   = sim_dir / "stdout.txt"
    athinput_path = sim_dir / "athinput"

    if status_file.exists():
        st = json.load(open(status_file))
        if st.get("outcome") in ("FRAG", "STABLE", "OK"):
            log(f"  SKIP {sim_id} ({st['outcome']})")
            return st

    with open(athinput_path, 'w') as fh:
        fh.write(make_athinput(f, beta, seed))

    log(f"  START {sim_id} [{label}]")
    t_start = time.time()

    try:
        result = subprocess.run(
            ["mpirun", "--oversubscribe", "-np", str(NP_PER_SIM),
             ATHENA_EXE, "-i", str(athinput_path)],
            cwd=str(sim_dir),
            stdout=open(stdout_file, 'w'),
            stderr=subprocess.STDOUT,
            timeout=TIMEOUT_SEC
        )
        exit_code = result.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        exit_code = -1; timed_out = True
        subprocess.run(["pkill", "-f", f"athena.*{sim_id}"], capture_output=True)

    wall_s = round(time.time() - t_start, 1)
    t_frag, dt_min, t_final = read_stdout_dt(stdout_file)

    if t_frag is not None:
        outcome = "FRAG"
    elif timed_out:
        outcome = "TIMEOUT"
    elif exit_code == 0 or (t_final is not None and t_final >= 3.9):
        outcome = "STABLE"  # reached ~tlim naturally
    else:
        outcome = "FAILED"

    status = dict(sim_id=sim_id, f=f, beta=beta, seed=seed, label=label,
                  outcome=outcome, t_frag=t_frag, dt_min=dt_min,
                  t_final=t_final, wall_s=wall_s, exit_code=exit_code)

    with open(status_file, 'w') as fh:
        json.dump(status, fh, indent=2)

    log(f"  DONE {sim_id}: {outcome}  t_frag={t_frag}  t_final={t_final:.3f}  wall={wall_s}s")
    return status

def main():
    log("="*65)
    log("DTC-EXTENDED Verification Campaign")
    log("Domain: 4x4x2 lambda_J  Mesh: 128x128x64  np=16  tlim=4.0 t_J")
    log(f"7 sims: 6 DTC-stable cases + 1 DTC-FRAG control")
    log(f"Output: {OUTPUT_BASE}")
    log("="*65)

    t0 = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as ex:
        futures = {ex.submit(run_sim, cfg): cfg for cfg in CONFIGS}
        for fut in as_completed(futures):
            r = fut.result(); results.append(r)
            n_frag   = sum(1 for x in results if x.get('outcome')=='FRAG')
            n_stable = sum(1 for x in results if x.get('outcome')=='STABLE')
            n_other  = len(results) - n_frag - n_stable
            log(f"  Progress: {len(results)}/7  FRAG={n_frag} STABLE={n_stable} other={n_other}")

    wall_h = (time.time()-t0)/3600
    log("="*65)
    log("CAMPAIGN COMPLETE")
    for r in sorted(results, key=lambda x: (x.get('f',0), x.get('beta',0))):
        log(f"  {r['sim_id']:35} {r['outcome']:8}  t_frag={r.get('t_frag')}  t_final={r.get('t_final')}")
    log(f"  Wall: {wall_h:.2f} h")
    log("="*65)

    out = OUTPUT_BASE / "dtc_ext_results.json"
    with open(out,'w') as fh:
        json.dump({"completed": datetime.utcnow().isoformat(),
                   "results": results}, fh, indent=2)
    log(f"Results: {out}")

if __name__ == "__main__":
    main()
