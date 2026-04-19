#!/usr/bin/env python3
"""
Transition Mapping Campaign v2 — April 2026
=============================================
240 Athena++ sims mapping f=1.5–2.5 × β=0.5–1.5 transition.

CORRECT PHYSICS (v2): f and β are independent via:
  - f = line-mass supercriticality = 2 * four_pi_G / pi
        (varying four_pi_G = effective gravitational constant)
  - β = plasma beta = 2*rho0*cs^2/B0^2  (independent of f)
  - wavelength = 2*lambda_J = 4*pi / sqrt(four_pi_G)  (always 2 Jeans lengths)

Uses PROVEN filament_spacing pgen (uniform box, sinusoidal perturbation).
No filament profile → no dt-death from out-of-equilibrium collapse.

Stability threshold β_crit = 2/3 is INDEPENDENT of f (derived from
dispersion relation for mode k = k_J/2). Verified in previous campaigns.

Grid (240 sims):
  Main: 11 f × 6 β × 3 M × 1 seed (phase=0) = 198
  Transition zone 2nd seed: f ∈ {1.7–2.3} × 6 β × M=2 × phase=1 = 42
  Total = 240
"""

import subprocess, sys, math

SSH_KEY  = "/shared/keys/astra-climate.key"
SSH_HOST = "fetch-agi@34.143.130.135"
SSH_OPTS = ["-i", SSH_KEY, "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ServerAliveInterval=10", "-o", "ConnectTimeout=20"]

ATHENA   = "/home/fetch-agi/athena/bin/athena"   # still has filament_spacing pgen
BASEDIR  = "/home/fetch-agi/transition_mapping_v2"
NPROC    = 32
BATCH_SZ = 7

# --- Recompile athena for filament_spacing pgen ---
# (filament_transition is no longer needed; fall back to filament_spacing)
# The binary already supports filament_spacing — we just need to recompile.

def four_pi_G_from_f(f_val):
    """Gravitational constant for target supercriticality f.
    f = 2*four_pi_G/pi  →  four_pi_G = f*pi/2
    """
    return f_val * math.pi / 2.0

def wavelength_from_f(f_val):
    """Seeded wavelength = 2 lambda_J = 4*pi / sqrt(four_pi_G)."""
    fpg = four_pi_G_from_f(f_val)
    return 4.0 * math.pi / math.sqrt(fpg)

# Parameter grid
f_values     = [1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5]
beta_values  = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
mach_values  = [1.0, 2.0, 3.0]
trans_f      = [1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3]   # gets 2nd seed

def ftag(f): return f"{f:.1f}".replace(".", "p")
def btag(b): return f"{b:.1f}".replace(".", "p")
def mtag(m): return f"{m:.1f}".replace(".", "p")

sims = []
# Main grid: 198 sims
for f in f_values:
    for b in beta_values:
        for m in mach_values:
            sims.append(dict(
                run_id=f"TM2_f{ftag(f)}_b{btag(b)}_M{mtag(m)}_p0",
                f=f, beta=b, mach=m, phase=0.0,
                four_pi_G=four_pi_G_from_f(f),
                wavelength=wavelength_from_f(f),
            ))

# Transition 2nd seed: 42 sims (M=2 only)
for f in trans_f:
    for b in beta_values:
        sims.append(dict(
            run_id=f"TM2_f{ftag(f)}_b{btag(b)}_M2p0_p1",
            f=f, beta=b, mach=2.0, phase=1.0,
            four_pi_G=four_pi_G_from_f(f),
            wavelength=wavelength_from_f(f),
        ))

assert len(sims) == 240, f"Expected 240, got {len(sims)}"
print(f"v2 Catalogue: {len(sims)} sims")
print(f"  f=1.5 → four_pi_G={four_pi_G_from_f(1.5):.4f}, λ={wavelength_from_f(1.5):.4f}")
print(f"  f=2.0 → four_pi_G={four_pi_G_from_f(2.0):.4f}, λ={wavelength_from_f(2.0):.4f}")
print(f"  f=2.5 → four_pi_G={four_pi_G_from_f(2.5):.4f}, λ={wavelength_from_f(2.5):.4f}")
print(f"  β_crit = 2/3 = 0.667 (independent of f — verified)")


def athinput(s):
    return f"""\
<comment>
problem   = transition mapping v2  f={s['f']:.2f}  beta={s['beta']:.2f}  M={s['mach']:.1f}  phase={s['phase']:.0f}
configure = --prob=filament_spacing -b --mpi --self_gravity=fft -fft --eos=isothermal

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
four_pi_G    = {s['four_pi_G']:.8f}
mach_number  = {s['mach']}
plasma_beta  = {s['beta']}
wavelength   = {s['wavelength']:.8f}
perturb_ampl = 0.01
phase_offset = {s['phase']:.1f}
"""


# Build remote bash script
lines = [
    "#!/bin/bash", "set -e",
    f"ATHENA={ATHENA}",
    f"BASEDIR={BASEDIR}", "CAMPAIGN=C5_transition_v2", "",
    "echo '=== Transition Mapping v2 — April 2026 ==='",
    "echo '240 sims: independent f (via 4piG) and beta (via B0)'",
    "echo '====================================================='", "",
]

# Recompile for filament_spacing pgen
lines += [
    "echo '--- Recompiling Athena++ for filament_spacing pgen ---'",
    "cd /home/fetch-agi/athena",
    "export CPATH=/usr/include/hdf5/openmpi",
    "export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/hdf5/openmpi",
    "python3 configure.py --prob=filament_spacing --coord=cartesian --eos=isothermal --flux=hlld -b -mpi --grav=fft -fft -hdf5 > /tmp/configure.log 2>&1",
    "make -j32 > /tmp/make.log 2>&1 && echo 'COMPILE OK' || { echo 'COMPILE FAILED'; cat /tmp/make.log | tail -20; exit 1; }",
    f"ATHENA={ATHENA}",
    "",
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

n_batches = math.ceil(len(sims) / BATCH_SZ)
for b_idx in range(n_batches):
    batch = sims[b_idx*BATCH_SZ:(b_idx+1)*BATCH_SZ]
    lines.append(f"echo '--- Batch {b_idx+1}/{n_batches}: {len(batch)} sims ---'")
    lines.append("echo 'Start: '$(date)")
    for s in batch:
        lines.append(f"launch_sim {s['run_id']}")
    lines.append("wait")
    lines.append(f"echo 'Batch {b_idx+1} complete: '$(date)")
    lines.append("")

lines += [
    "echo '====================================================='",
    "echo 'ALL 240 SIMS COMPLETE: '$(date)",
]

remote_script = "\n".join(lines) + "\n"

REMOTE_SCRIPT = "/home/fetch-agi/launch_transition_v2.sh"
MASTER_LOG    = "/home/fetch-agi/transition_v2_master.log"

print("\nUploading v2 launch script …")
r = subprocess.run(
    ["ssh"] + SSH_OPTS + [SSH_HOST,
     f"cat > {REMOTE_SCRIPT} && chmod +x {REMOTE_SCRIPT} && echo UPLOAD_OK"],
    input=remote_script, capture_output=True, text=True, timeout=30
)
if "UPLOAD_OK" not in r.stdout:
    print(f"FAILED: {r.stdout}\n{r.stderr}"); sys.exit(1)
print(f"  Uploaded ✓  ({n_batches} batches, {len(remote_script)//1024} KB)")

print("Launching with nohup …")
r3 = subprocess.run(
    ["ssh"] + SSH_OPTS + [SSH_HOST,
     f"nohup bash {REMOTE_SCRIPT} > {MASTER_LOG} 2>&1 & echo NOHUP_PID=$!"],
    capture_output=True, text=True, timeout=25
)
print(f"  {r3.stdout.strip()}")

print()
print("=" * 60)
print("TRANSITION MAPPING v2 LAUNCHED")
print("=" * 60)
print(f"  240 sims, {n_batches} batches of ≤{BATCH_SZ}")
print(f"  f via four_pi_G; β via plasma_beta (independent)")
print(f"  Using proven filament_spacing pgen (no dt-death)")
print(f"  Monitor: 'tail -20 {MASTER_LOG}'")
