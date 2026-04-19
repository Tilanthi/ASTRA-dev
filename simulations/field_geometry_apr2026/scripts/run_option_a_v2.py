#!/usr/bin/env python3
"""
run_option_a_v2.py — Single-fibre High-Resolution Fibre Fragmentation
======================================================================
Designed to test the magnetic Jeans fragmentation formula INSIDE a fibre.

Key improvements over Option A v1 (n_fibers=3/4, L=16):
  1. Single isolated fibre (n_fibers=1) — no inter-fibre coupling
  2. SMALLER BOX L=8 λ_J (same NX=256) → dx=0.03125 λ_J (2× finer)
  3. n_modes=10 → λ_min = L/10 = 0.8 λ_J  < λ_MJ,fibre(β=0.7)=0.982
     BOTH stable (λ<λ_MJ) and unstable (λ>λ_MJ) modes seeded
  4. DT_OUTPUT=0.02 — finer time sampling of early growth

Theoretical predictions:
  β=0.70: λ_MJ,fibre = 0.982 λ_J → expect ~8 cores (L/λ_MJ = 8.15)
           Calibrated: λ_frag = 1.11×0.982 = 1.09 λ_J → ~7 cores
  β=0.90: λ_MJ,fibre = 0.898 λ_J → expect ~8-9 cores (L/λ_MJ = 8.91)
           Calibrated: λ_frag = 1.11×0.898 = 0.997 λ_J → ~8 cores

Unstable modes in L=8 box (λ > λ_MJ,fibre):
  β=0.70: n ≤ 8 (λ ≥ 1.0 λ_J > 0.982)  ← modes 1-8 unstable
  β=0.90: n ≤ 8 (λ ≥ 1.0 λ_J > 0.898)  ← modes 1-8 unstable; mode 9 stable

Authors: Glenn J. White (Open University)
         ASTRA multi-agent system — 2026-04-19
"""

import subprocess, json, math, time, os
from pathlib import Path

ATHENA_BIN  = Path("/home/fetch-agi/athena_fiber_src/bin/athena")
WORK_DIR    = Path("/home/fetch-agi/option_a_v2_runs")
STATUS_FILE = Path("/home/fetch-agi/option_a_v2_status.json")

N_PROCS    = 8
L          = 8.0        # λ_J  (HALF the original L=16)
NX         = 256        # cells per dim  (same as original → dx = L/NX = 0.03125 λ_J)
N_MODES    = 10         # seeds λ = L/1,...,L/10 = 8,...,0.8 λ_J
PERTURB    = 0.05       # 5% amplitude
TLIM       = 0.30       # t_J  (captures up to ~3.75 fibre free-fall times before crash)
DT_OUTPUT  = 0.02       # t_J  (15 snapshots max: t=0, 0.02, ..., 0.28)
SIGMA_FIBE = 0.60       # λ_J  Gaussian width (FWHM = 2.355×0.6 = 1.41 λ_J)
RHO_CONTR  = 4.0        # ρ_c / ρ_bg
MACH       = 3.0
FIBER_X2   = L / 2.0   # centre of box in x2
FIBER_X3   = L / 2.0   # centre of box in x3

def lmj_fiber(beta):
    lj_bg  = 1.0
    lj_fib = lj_bg / math.sqrt(RHO_CONTR)
    return lj_fib * math.sqrt(1.0 + 2.0 / beta)

def lmj_bg(beta):
    return math.sqrt(1.0 + 2.0 / beta)

SIMS = [
    {"name": "FIB1_HR_b07", "beta": 0.70},
    {"name": "FIB1_HR_b09", "beta": 0.90},
]

def make_athinput(sim):
    name  = sim['name']
    beta  = sim['beta']
    lmj_f = lmj_fiber(beta)
    lmj_b = lmj_bg(beta)

    return f"""<comment>
problem       = fiber_structure
name          = {name}
description   = Single-fibre HR: L=8, 256^3, n_modes=10 (seeds lambda~0.8-8 lJ)
lmj_bg        = {lmj_b:.4f}  lmj_fiber = {lmj_f:.4f}
unstable_nmax = {int(L/lmj_f)}   (modes n<=this are unstable; lambda_min_seed={L/N_MODES:.3f})

<job>
problem_id = {name}
restart_filename = /dev/null

<output1>
file_type  = hdf5
variable   = prim
dt         = {DT_OUTPUT:.4f}
id         = prim

<time>
cfl_number  = 0.3
nlim        = -1
tlim        = {TLIM:.4f}
integrator  = vl2
xorder      = 2
ncycle_out  = 200

<mesh>
nx1   = {NX}
x1min = 0.0
x1max = {L:.4f}
ix1_bc = periodic
ox1_bc = periodic
nx2   = {NX}
x2min = 0.0
x2max = {L:.4f}
ix2_bc = periodic
ox2_bc = periodic
nx3   = {NX}
x3min = 0.0
x3max = {L:.4f}
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 32
nx2 = 32
nx3 = 32

<hydro>
iso_sound_speed = 1.0

<field>
b_norm_factor = 1.0

<gravity>
grav_mean_rho  = 1.0
output_phi     = yes

<problem>
four_pi_G    = 39.478418
mach_number  = {MACH:.4f}
plasma_beta  = {beta:.4f}
n_fibers     = 1
rho_contrast = {RHO_CONTR:.4f}
sigma_fiber  = {SIGMA_FIBE:.4f}
n_modes      = {N_MODES}.0
perturb_ampl = {PERTURB:.4e}
fiber_x2_0  = {FIBER_X2:.4f}
fiber_x3_0  = {FIBER_X3:.4f}
"""

status = {}

WORK_DIR.mkdir(parents=True, exist_ok=True)

for sim in SIMS:
    name    = sim['name']
    beta    = sim['beta']
    run_dir = WORK_DIR / name
    run_dir.mkdir(parents=True, exist_ok=True)

    inp_path = run_dir / f"{name}.in"
    with open(inp_path, "w") as f:
        f.write(make_athinput(sim))

    lmj_f = lmj_fiber(beta)
    lmj_b = lmj_bg(beta)
    n_unstable = int(L / lmj_f)
    print(f"\n{name}: β={beta:.2f}")
    print(f"  λ_MJ,fibre = {lmj_f:.4f} λ_J  (fibre interior, B⊥fibre)")
    print(f"  λ_MJ,bg    = {lmj_b:.4f} λ_J  (background)")
    print(f"  Unstable modes: n=1..{n_unstable} (λ={L/n_unstable:.3f}..{L:.1f} λ_J)")
    print(f"  Stable   modes: n={n_unstable+1}..{N_MODES} (λ={L/(n_unstable+1):.3f}..{L/N_MODES:.1f} λ_J)")
    print(f"  λ_min seeded: {L/N_MODES:.2f} λ_J  ({'<' if L/N_MODES < lmj_f else '>='} λ_MJ,fibre)")
    print(f"  Expected cores: ~{int(round(L/lmj_f))} (theory) / ~{int(round(L/(1.11*lmj_f)))} (calibrated)")
    print(f"  Input: {inp_path}")

    cmd = (f"mpirun --allow-run-as-root -np {N_PROCS} {ATHENA_BIN} "
           f"-i {inp_path} -d {run_dir}")
    print(f"  Launch: {cmd}")

    proc = subprocess.Popen(
        cmd, shell=True,
        stdout=open(run_dir / "stdout.txt", "w"),
        stderr=open(run_dir / "stderr.txt", "w"),
    )
    status[name] = {
        'pid': proc.pid, 'status': 'running',
        'start': time.time(), 'beta': beta,
        'lmj_fiber': lmj_f, 'lmj_bg': lmj_b,
    }
    print(f"  PID={proc.pid}")
    time.sleep(3)

with open(STATUS_FILE, "w") as f:
    json.dump(status, f, indent=2)

print(f"\nAll launched. Status: {STATUS_FILE}")
print(f"Monitor: ls -lth {WORK_DIR}/FIB1_HR_*/*.athdf 2>/dev/null | head -10")
print(f"Stdout:  tail -f {WORK_DIR}/FIB1_HR_b07/stdout.txt")
