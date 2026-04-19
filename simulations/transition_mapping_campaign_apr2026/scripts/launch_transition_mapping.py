#!/usr/bin/env python3
"""
Transition Mapping Campaign — April 2026
=========================================
240 Athena++ MHD sims mapping the fragmentation transition at f ≈ 1.7–2.3

NEW PHYSICS: Uses filament_transition pgen where f and β are INDEPENDENT:
  - f = line-mass supercriticality, controlled by rho_contrast (filament density)
      f = (rho_contrast - 1) * pi^3 * sigma^2  (sigma=0.3)
      f = (rho_contrast - 1) * 2.7905
  - β = plasma beta (magnetic pressure relative to background), independent of f
  - M = Mach number of initial perturbation velocity
  - phase_offset = 0 (cos) or 1 (sin) — the two "seeds"

Grid (240 sims total):
  Main: 11 f × 6 β × 3 M × 1 seed (phase=0) = 198 sims
  Transition extra: f ∈ {1.7–2.3} × 6 β × M=2.0 × phase=1 = 7×6×1 = 42 sims
  Total: 198 + 42 = 240

f values:  1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5
β values:  0.5, 0.7, 0.9, 1.1, 1.3, 1.5
M values:  1.0, 2.0, 3.0
f_crit = √3 ≈ 1.732 (stability boundary from β-sweep)

Filament profile: Gaussian in x2-x3 plane, σ=0.3 λ_J, axis along x1
Grid: 256×64×64, domain [-8,8]×[-2,2]×[-2,2] λ_J
32 MPI procs per sim, 7 concurrent (224 vCPUs)
"""

import subprocess, sys, math

SSH_KEY  = "/shared/keys/astra-climate.key"
SSH_HOST = "fetch-agi@34.143.130.135"
SSH_OPTS = ["-i", SSH_KEY, "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=20"]

ATHENA   = "/home/fetch-agi/athena/bin/athena"
BASEDIR  = "/home/fetch-agi/transition_mapping"
NPROC    = 32
BATCH_SZ = 7

# Physical parameters
SIGMA    = 0.3          # filament width in λ_J units
F_FACTOR = math.pi**3 * SIGMA**2   # f = (rho_c - 1) * F_FACTOR

# Parameter grid
f_values       = [1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5]
beta_values    = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
mach_values    = [1.0, 2.0, 3.0]
transition_f   = [1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3]  # gets 2nd seed at M=2

def rho_c_from_f(f_val):
    """Filament peak density for target supercriticality f."""
    return 1.0 + f_val / F_FACTOR

def ftag(f): return f"{f:.1f}".replace(".", "p")
def btag(b): return f"{b:.1f}".replace(".", "p")
def mtag(m): return f"{m:.1f}".replace(".", "p")

# Build simulation catalogue
sims = []

# Main grid: 11 × 6 × 3 × 1 seed = 198
for f in f_values:
    for b in beta_values:
        for m in mach_values:
            sims.append(dict(
                run_id = f"TM_f{ftag(f)}_b{btag(b)}_M{mtag(m)}_p0",
                f=f, beta=b, mach=m, phase=0,
                rho_c=rho_c_from_f(f),
            ))

# Transition-zone 2nd seed: 7 × 6 × 1 (M=2) × 1 = 42
for f in transition_f:
    for b in beta_values:
        sims.append(dict(
            run_id = f"TM_f{ftag(f)}_b{btag(b)}_M2p0_p1",
            f=f, beta=b, mach=2.0, phase=1,
            rho_c=rho_c_from_f(f),
        ))

assert len(sims) == 240, f"Expected 240 sims, got {len(sims)}"
print(f"Simulation catalogue: {len(sims)} sims")
print(f"f_factor = {F_FACTOR:.5f}  (f = (rho_c - 1) × {F_FACTOR:.5f})")
print(f"f=1.5 → rho_c={rho_c_from_f(1.5):.4f},  f=2.5 → rho_c={rho_c_from_f(2.5):.4f}")
print()


def athinput(s):
    return f"""\
<comment>
problem   = transition mapping  f={s['f']:.2f}  beta={s['beta']:.2f}  M={s['mach']:.1f}  phase={s['phase']}
configure = --prob=filament_transition -b --mpi --self_gravity=fft -fft --eos=isothermal

<job>
problem_id = {s['run_id']}

<output1>
file_type  = hdf5
variable   = cons
dt         = 0.2
id         = out

<time>
cfl_number = 0.3
nlim       = -1
tlim       = 4.0

<mesh>
nx1        = 256
x1min      = -8.0
x1max      =  8.0
ix1_bc     = periodic
ox1_bc     = periodic

nx2        = 64
x2min      = -2.0
x2max      =  2.0
ix2_bc     = periodic
ox2_bc     = periodic

nx3        = 64
x3min      = -2.0
x3max      =  2.0
ix3_bc     = periodic
ox3_bc     = periodic

<meshblock>
nx1        = 32
nx2        = 32
nx3        = 32

<hydro>
gamma           = 1.0
iso_sound_speed = 1.0

<gravity>
grav_mean_rho = 1.0

<problem>
four_pi_G      = 39.478418
mach_number    = {s['mach']}
plasma_beta    = {s['beta']}
wavelength     = 2.0
perturb_ampl   = 0.01
rho_contrast   = {s['rho_c']:.6f}
filament_sigma = {SIGMA}
phase_offset   = {s['phase']:.1f}
"""


# Build remote bash script
lines = [
    "#!/bin/bash", "set -e",
    f"ATHENA={ATHENA}", f"BASEDIR={BASEDIR}", "CAMPAIGN=C5_transition_mapping", "",
    "echo '=== Transition Mapping Campaign — April 2026 ==='",
    f"echo '240 sims: 11f × 6β × 3M + 42 transition-zone seeds'",
    "echo '========================================================='", "",
]

lines.append("echo '--- Writing 240 input files ---'")
for s in sims:
    rundir = f"$BASEDIR/$CAMPAIGN/{s['run_id']}"
    sentinel = f"EOF_{s['run_id']}"
    lines.append(f"mkdir -p {rundir}")
    lines.append(f"cat > {rundir}/{s['run_id']}.in << '{sentinel}'")
    lines.append(athinput(s))
    lines.append(sentinel)

lines.append("echo 'All input files written'")
lines.append("")

# Launch helper
lines += [
    "launch_sim() {",
    "  local rid=$1",
    f"  local rundir=$BASEDIR/$CAMPAIGN/$rid",
    "  local logfile=$rundir/run.log",
    f"  mpirun -np {NPROC} $ATHENA -i $rundir/$rid.in -d $rundir > $logfile 2>&1 &",
    "  echo \"  Launched $rid  PID=$!\"",
    "}",
    "",
]

# Batches
n_batches = math.ceil(len(sims) / BATCH_SZ)
for b_idx in range(n_batches):
    batch = sims[b_idx*BATCH_SZ:(b_idx+1)*BATCH_SZ]
    lines.append(f"echo '--- Batch {b_idx+1}/{n_batches}: {len(batch)} sims ---'")
    lines.append(f"echo 'Start: '$(date)")
    for s in batch:
        lines.append(f"launch_sim {s['run_id']}")
    lines.append("wait")
    lines.append(f"echo 'Batch {b_idx+1} complete: '$(date)")
    lines.append("")

lines += [
    "echo '========================================================='",
    "echo 'ALL 240 SIMS COMPLETE: '$(date)",
    "",
]

remote_script = "\n".join(lines) + "\n"

# Upload
REMOTE_SCRIPT = "/home/fetch-agi/launch_transition_mapping.sh"
MASTER_LOG    = "/home/fetch-agi/transition_mapping_master.log"

print("Uploading launch script to astra-climate …")
r = subprocess.run(
    ["ssh"] + SSH_OPTS + [SSH_HOST,
     f"cat > {REMOTE_SCRIPT} && chmod +x {REMOTE_SCRIPT} && echo UPLOAD_OK"],
    input=remote_script, capture_output=True, text=True, timeout=30
)
if "UPLOAD_OK" not in r.stdout:
    print(f"Upload FAILED!\nstdout: {r.stdout}\nstderr: {r.stderr}")
    sys.exit(1)
print(f"  Uploaded ✓  ({len(remote_script)//1024} KB, {n_batches} batches)")

r2 = subprocess.run(
    ["ssh"] + SSH_OPTS + [SSH_HOST, f"wc -l {REMOTE_SCRIPT}"],
    capture_output=True, text=True, timeout=15
)
print(f"  Remote script: {r2.stdout.strip()}")

print("\nLaunching with nohup …")
r3 = subprocess.run(
    ["ssh"] + SSH_OPTS + [SSH_HOST,
     f"nohup bash {REMOTE_SCRIPT} > {MASTER_LOG} 2>&1 & echo NOHUP_PID=$!"],
    capture_output=True, text=True, timeout=20
)
pid_line = r3.stdout.strip()
print(f"  {pid_line}")
if r3.stderr:
    print(f"  stderr: {r3.stderr.strip()}")

print()
print("=" * 65)
print("TRANSITION MAPPING CAMPAIGN LAUNCHED")
print("=" * 65)
print(f"  240 sims in {n_batches} batches of ≤{BATCH_SZ}")
print(f"  New pgen: filament_transition (independent f and β)")
print(f"  f=√(rho_c-1)/{F_FACTOR:.4f}  →  rho_c varies 1.54–1.90")
print(f"  β = 0.5–1.5 (independent of f)")
print(f"  Grid: 256×64×64, 32 MPI/sim, 7 concurrent")
print(f"  Monitor: ssh ... 'tail -20 {MASTER_LOG}'")
