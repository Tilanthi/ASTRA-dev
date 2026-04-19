#!/usr/bin/env python3
"""Launch FG_t45_b050 and FG_t45_b075 — the two missing theta=45 simulations."""
import subprocess, json, math, time, os
from pathlib import Path

ATHENA_BIN = Path("/home/fetch-agi/athena_fieldgeo/bin/athena")
WORK_DIR   = Path("/home/fetch-agi/option_b_runs")
STATUS_FILE = Path("/home/fetch-agi/option_b_t45_missing_status.json")
N_PROCS = 8
L = 8.0

# λ_MJ(θ,β) = sqrt(1 + 2*sin²θ / β)   (in units of λ_Jeans=1)
def lmj(theta_deg, beta):
    t = math.radians(theta_deg)
    return math.sqrt(1.0 + 2.0 * math.sin(t)**2 / beta)

# seed wavelength = largest mode fitting >= lmj in box (L/n for integer n)
def seed_wavelength(lmj_val, L=8.0):
    n = int(L / lmj_val)        # floor(L/λ_MJ)
    if n < 1:
        n = 1
    return L / n

SIMS = [
    {"name": "FG_t45_b050", "theta": 45.0, "beta": 0.50},
    {"name": "FG_t45_b075", "theta": 45.0, "beta": 0.75},
]

def make_athinput(sim):
    name  = sim['name']
    theta = sim['theta']
    beta  = sim['beta']
    lmj_val = lmj(theta, beta)
    wl = seed_wavelength(lmj_val)

    return f"""<comment>
problem   = field_geometry
name      = {name}
theta_deg = {theta}
beta      = {beta:.2f}
lmj_pred  = {lmj_val:.4f}

<job>
problem_id = {name}
restart_filename = /dev/null

<output1>
file_type  = hdf5
variable   = prim
dt         = 0.5000
id         = prim

<time>
cfl_number  = 0.3
nlim        = -1
tlim        = 15.0000
integrator  = vl2
xorder      = 2
ncycle_out  = 500

<mesh>
nx1   = 128
x1min = 0.0
x1max = {L:.4f}
ix1_bc = periodic
ox1_bc = periodic
nx2   = 128
x2min = 0.0
x2max = {L:.4f}
ix2_bc = periodic
ox2_bc = periodic
nx3   = 128
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
mach_number  = 3.0000
plasma_beta  = {beta:.4f}
theta_deg    = {theta:.2f}
wavelength   = {wl:.6f}
perturb_ampl = 1.0000e-02
"""

status = {}

for sim in SIMS:
    name = sim['name']
    run_dir = WORK_DIR / name
    run_dir.mkdir(parents=True, exist_ok=True)

    # Write athinput
    inp_path = run_dir / f"{name}.in"
    with open(inp_path, "w") as f:
        f.write(make_athinput(sim))

    lmj_val = lmj(sim['theta'], sim['beta'])
    wl = seed_wavelength(lmj_val)
    print(f"{name}: θ={sim['theta']}° β={sim['beta']:.2f} "
          f"λ_MJ={lmj_val:.4f} λ_seed={wl:.4f}")
    print(f"  Input: {inp_path}")

    # Launch
    cmd = (f"mpirun --allow-run-as-root -np {N_PROCS} {ATHENA_BIN} "
           f"-i {inp_path} -d {run_dir}")
    print(f"  Launching: {cmd}")
    proc = subprocess.Popen(
        cmd, shell=True,
        stdout=open(run_dir / "stdout.txt", "w"),
        stderr=open(run_dir / "stderr.txt", "w"),
    )
    status[name] = {"pid": proc.pid, "status": "running", "start": time.time()}
    print(f"  PID={proc.pid}")
    time.sleep(2)

with open(STATUS_FILE, "w") as f:
    json.dump(status, f, indent=2)

print("\nAll launched. Status written to", STATUS_FILE)
print("Monitor: ls -lth /home/fetch-agi/option_b_runs/FG_t45_b05*/*.athdf 2>/dev/null | head")
