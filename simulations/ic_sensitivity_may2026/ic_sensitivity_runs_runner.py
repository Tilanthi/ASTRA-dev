#!/usr/bin/env python3
"""
IC Sensitivity Campaign Runner — Referee Response May 2026
48 sims: ic_type=[king,uniform] × f=[1.0,1.1] × beta=[0.3,0.5,1.0] × M=[1.0,2.0] × seeds=[1,2]
Domain: 256×64×64, L=8λ_J, longitudinal B
Binary: /home/fetch-agi/athena/bin/athena_ic
"""

import json, os, signal, subprocess, sys, time, math, shutil, glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────
ATHENA_BIN  = "/home/fetch-agi/athena/bin/athena_ic"
BASE_DIR    = Path("/data/ic_sensitivity_runs")
FOUR_PI_G   = 39.4784176044
CS          = 1.0
DT_KILL     = 1.0e-6
POLL        = 8.0           # seconds between dt polls
NP          = 32            # MPI ranks: 256×64×64 / 32³ = 32 meshblocks
MAX_CONC    = 6             # 6 × 32 = 192 vCPUs (safe on 220-vCPU node)
WALL_TIME   = 10800         # 3h per sim
TLIM        = 5.0           # generous — near-critical f=1.0 may need ~1.5 t_J
HDF5_DT     = 0.1           # snapshot interval (t_J)
KEEP_HDF5   = 3             # keep last N snapshots per sim

# ── Parameter space ────────────────────────────────────────────────────────
IC_TYPES = ["king", "uniform"]
F_LIST   = [1.0, 1.1]
BETA_LIST = [0.3, 0.5, 1.0]
MACH_LIST = [1.0, 2.0]
SEEDS    = [1, 2]

# W_core (filament half-width in λ_J)
W_CORE   = 0.3

# Build sim list
def build_sim_list():
    sims = []
    for ic in IC_TYPES:
        for f in F_LIST:
            for beta in BETA_LIST:
                for mach in MACH_LIST:
                    for seed in SEEDS:
                        f_str    = f"{f:.1f}".replace('.','p')
                        b_str    = f"{beta:.1f}".replace('.','p')
                        m_str    = f"{mach:.1f}".replace('.','p')
                        run_id   = f"IC_{ic}_f{f_str}_b{b_str}_m{m_str}_s{seed}"
                        sims.append({
                            "run_id": run_id,
                            "ic_type": ic,
                            "f": f,
                            "beta": beta,
                            "mach": mach,
                            "seed": seed,
                        })
    return sims

# ── Input file generator ───────────────────────────────────────────────────
def make_athinput(run_dir: Path, p: dict) -> Path:
    """Write standard Athena++ input file for this sim."""
    f       = p["f"]
    beta    = p["beta"]
    mach    = p["mach"]
    seed    = p["seed"]
    ic_type = p["ic_type"]

    # Domain: 8λ_J along filament, 2λ_J transverse (matching prior campaigns)
    x1min, x1max = -4.0, 4.0   # 8 λ_J
    x2min, x2max = -1.0, 1.0   # 2 λ_J
    x3min, x3max = -1.0, 1.0

    # Derived B field for <mhd> section (not actually read by our pgen, but needed
    # so that Athena++ initialises the field arrays before ProblemGenerator runs)
    # We just use beta; pgen computes B0 itself.
    # Bz is not set here — it's computed inside ProblemGenerator.

    athinput = f"""<comment>
problem   = IC sensitivity test ({ic_type} profile)
run_id    = {p['run_id']}

<job>
problem_id = filament_ic_sensitivity

<time>
cfl_number = 0.3
nlim       = -1
tlim       = {TLIM}

<mesh>
nx1        = 256
x1min      = {x1min}
x1max      = {x1max}
ix1_bc     = periodic
ox1_bc     = periodic

nx2        = 64
x2min      = {x2min}
x2max      = {x2max}
ix2_bc     = periodic
ox2_bc     = periodic

nx3        = 64
x3min      = {x3min}
x3max      = {x3max}
ix3_bc     = periodic
ox3_bc     = periodic

<meshblock>
nx1        = 32
nx2        = 32
nx3        = 32

<hydro>
iso_sound_speed = {CS}

<gravity>
grav_mean_rho = 1.0

<output1>
file_type  = hst
dt         = 0.01

<output2>
file_type  = hdf5
variable   = prim
dt         = {HDF5_DT}

<problem>
four_pi_G   = {FOUR_PI_G}
f_line_mass = {f}
plasma_beta = {beta}
mach_number = {mach}
W_core      = {W_CORE}
perturb_ampl = 1.0e-4
random_seed = {seed}
ic_type     = {ic_type}
"""
    inp = run_dir / "athinput.ic_sensitivity"
    inp.write_text(athinput)
    return inp

# ── Run a single simulation ────────────────────────────────────────────────
def run_sim(p: dict) -> dict:
    run_id  = p["run_id"]
    run_dir = BASE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    inp_file = make_athinput(run_dir, p)
    log_file = run_dir / "stdout.txt"

    cmd = [
        "mpirun", "--oversubscribe", "-np", str(NP),
        ATHENA_BIN, "-i", str(inp_file),
        "-d", str(run_dir),
    ]

    t_start = time.time()
    t_frag  = None
    outcome = "TIMEOUT"
    dt_min  = 999.0

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        while True:
            elapsed = time.time() - t_start

            # Wall-time kill
            if elapsed > WALL_TIME:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                outcome = "TIMEOUT"
                break

            # Poll returncode
            rc = proc.poll()
            if rc is not None:
                outcome = "COMPLETE" if rc == 0 else "FAILED"
                break

            # Scan HST for dt_min → FRAG detection
            hst_files = list(run_dir.glob("*.hst"))
            if hst_files:
                try:
                    lines = hst_files[0].read_text().split('\n')
                    for line in reversed(lines):
                        if line.strip() and not line.startswith('#'):
                            cols = line.split()
                            if len(cols) >= 2:
                                t_now = float(cols[0])
                                dt_val = float(cols[1])
                                if dt_val < dt_min:
                                    dt_min = dt_val
                                if dt_val < DT_KILL:
                                    t_frag  = t_now
                                    outcome = "FRAG"
                                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                                    proc.wait(timeout=5)
                                    break
                            break
                except Exception:
                    pass
                if outcome == "FRAG":
                    break

            time.sleep(POLL)

    except Exception as e:
        outcome = f"ERROR: {e}"

    wall = time.time() - t_start

    # Purge HDF5 — keep last KEEP_HDF5 snapshots
    hdf5s = sorted(run_dir.glob("*.athdf"))
    if len(hdf5s) > KEEP_HDF5:
        for f_del in hdf5s[:-KEEP_HDF5]:
            try:
                f_del.unlink()
            except Exception:
                pass
    # Remove XDMF files
    for xf in run_dir.glob("*.xdmf"):
        try:
            xf.unlink()
        except Exception:
            pass

    result = {
        "run_id":  run_id,
        "ic_type": p["ic_type"],
        "f":       p["f"],
        "beta":    p["beta"],
        "mach":    p["mach"],
        "seed":    p["seed"],
        "outcome": outcome,
        "t_frag":  t_frag,
        "dt_min":  dt_min,
        "wall_s":  round(wall, 1),
    }

    status = f"{'FRAG' if outcome=='FRAG' else outcome:8s} t={t_frag:.4f}" if t_frag else f"{'FRAG' if outcome=='FRAG' else outcome:8s}"
    print(f"[{run_id}] {status}  wall={wall:.0f}s  dt_min={dt_min:.2e}", flush=True)
    return result

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    sims = build_sim_list()
    print(f"IC Sensitivity Campaign: {len(sims)} sims | NP={NP} | MAX_CONC={MAX_CONC}")
    print(f"IC types: {IC_TYPES} | f: {F_LIST} | beta: {BETA_LIST} | mach: {MACH_LIST} | seeds: {SEEDS}")
    print("─" * 70)

    results = []
    t_launch = time.time()

    with ThreadPoolExecutor(max_workers=MAX_CONC) as pool:
        futures = {pool.submit(run_sim, s): s for s in sims}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            # Save incremental results
            out = BASE_DIR / "ic_sensitivity_results.json"
            out.write_text(json.dumps(results, indent=2))

    total_wall = time.time() - t_launch
    n_frag    = sum(1 for r in results if r["outcome"] == "FRAG")
    n_timeout = sum(1 for r in results if r["outcome"] == "TIMEOUT")
    n_other   = len(results) - n_frag - n_timeout

    print("\n" + "=" * 70)
    print(f"CAMPAIGN COMPLETE: {len(results)} sims in {total_wall/60:.1f} min")
    print(f"  FRAG={n_frag}  TIMEOUT={n_timeout}  OTHER={n_other}")

    # Summary by ic_type
    for ic in IC_TYPES:
        sub = [r for r in results if r["ic_type"] == ic and r["outcome"] == "FRAG"]
        if sub:
            tfrags = [r["t_frag"] for r in sub]
            print(f"  {ic:8s}: {len(sub)} FRAG, mean t_frag = {sum(tfrags)/len(tfrags):.4f} t_J")

    out = BASE_DIR / "ic_sensitivity_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved: {out}")

if __name__ == "__main__":
    main()
