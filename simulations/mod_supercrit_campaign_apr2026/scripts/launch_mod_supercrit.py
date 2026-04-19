#!/usr/bin/env python3
"""
Moderate Supercriticality Campaign — April 2026
================================================
5×5 grid: f ∈ {1.5, 2.0, 2.5, 3.0, 3.5} × M ∈ {1.0, 2.0, 3.0, 4.0, 5.0}
where f = √(2/β)  →  β = 2/f²

25 simulations total.  Grid: 256×64×64, same filament_spacing problem as sweep campaigns.
Runs in batches of 7 (224 vCPUs / 32 per sim).

Usage (from agent container or astra-climate):
    python3 launch_mod_supercrit.py
"""

import subprocess, sys, math

SSH_KEY  = "/shared/keys/astra-climate.key"
SSH_HOST = "fetch-agi@34.143.130.135"
SSH_OPTS = ["-i", SSH_KEY, "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=20"]

ATHENA   = "/home/fetch-agi/athena/bin/athena"
BASEDIR  = "/home/fetch-agi/mod_supercrit"
NPROC    = 32          # MPI ranks per sim (= meshblocks: 8×2×2=32)
BATCH_SZ = 7           # concurrent sims (7×32 = 224 vCPUs)


# ── Parameter grid ──────────────────────────────────────────────────
f_values = [1.5, 2.0, 2.5, 3.0, 3.5]
M_values = [1.0, 2.0, 3.0, 4.0, 5.0]

sims = []
for f in f_values:
    beta = round(2.0 / f**2, 6)
    ftag = f"{f:.1f}".replace(".", "p")
    btag = f"{beta:.4f}".replace(".", "p")
    for mach in M_values:
        mtag = f"{mach:.1f}".replace(".", "p")
        run_id = f"MSC_f{ftag}_M{mtag}"
        sims.append(dict(
            run_id = run_id,
            f      = f,
            beta   = beta,
            mach   = mach,
            ftag   = ftag,
            mtag   = mtag,
        ))

assert len(sims) == 25, f"Expected 25 sims, got {len(sims)}"
print(f"Simulation catalogue: {len(sims)} sims")
for s in sims:
    print(f"  {s['run_id']}  f={s['f']:.1f}  β={s['beta']:.4f}  M={s['mach']:.1f}")


# ── Athena++ input file template ─────────────────────────────────────
def athinput(s):
    return f"""\
<comment>
problem   = moderate supercriticality sweep (f={s['f']:.1f}, M={s['mach']:.1f})
configure = --prob=filament_spacing -b --mpi --self_gravity=fft -fft
f_value   = {s['f']:.4f}
beta_value = {s['beta']:.6f}

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
four_pi_G    = 39.478418
mach_number  = {s['mach']}
plasma_beta  = {s['beta']:.6f}
wavelength   = 2.0
perturb_ampl = 0.01
"""


# ── Build remote bash script ─────────────────────────────────────────
lines = [
    "#!/bin/bash",
    "set -e",
    f"ATHENA={ATHENA}",
    f"BASEDIR={BASEDIR}",
    f"CAMPAIGN=C4_mod_supercrit",
    "",
    "echo '=== Moderate Supercriticality Campaign — April 2026 ==='",
    f"echo '25 sims: f={f_values} × M={M_values}'",
    "echo '=================================================================='",
    "",
]

# Write all input files
lines.append("echo '--- Writing input files ---'")
for s in sims:
    rundir = f"$BASEDIR/$CAMPAIGN/{s['run_id']}"
    sentinel = f"EOF_{s['run_id']}"
    lines.append(f"mkdir -p {rundir}")
    lines.append(f"cat > {rundir}/{s['run_id']}.in << '{sentinel}'")
    lines.append(athinput(s))
    lines.append(sentinel)
    lines.append(f"echo '  wrote {s['run_id']}.in'")
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
for b in range(n_batches):
    batch = sims[b*BATCH_SZ:(b+1)*BATCH_SZ]
    lines.append(f"echo '--- Batch {b+1}/{n_batches}: {len(batch)} sims ---'")
    lines.append(f"echo 'Start: '$(date)")
    for s in batch:
        lines.append(f"launch_sim {s['run_id']}")
    lines.append("wait")
    lines.append(f"echo 'Batch {b+1} complete: '$(date)")
    lines.append("")

lines += [
    "echo '=================================================================='",
    "echo 'ALL 25 SIMS COMPLETE: '$(date)",
    "",
]

remote_script = "\n".join(lines) + "\n"


# ── Upload and launch on astra-climate ──────────────────────────────
REMOTE_SCRIPT = "/home/fetch-agi/launch_mod_supercrit.sh"
MASTER_LOG    = "/home/fetch-agi/mod_supercrit_master.log"

print("\nUploading launch script to astra-climate …")
r = subprocess.run(
    ["ssh"] + SSH_OPTS + [SSH_HOST,
     f"cat > {REMOTE_SCRIPT} && chmod +x {REMOTE_SCRIPT} && echo UPLOAD_OK"],
    input=remote_script, capture_output=True, text=True, timeout=30
)
if "UPLOAD_OK" not in r.stdout:
    print(f"Upload FAILED!\nstdout: {r.stdout}\nstderr: {r.stderr}")
    sys.exit(1)
print("  Script uploaded ✓")

# Verify line count
r2 = subprocess.run(
    ["ssh"] + SSH_OPTS + [SSH_HOST, f"wc -l {REMOTE_SCRIPT}"],
    capture_output=True, text=True, timeout=15
)
print(f"  Remote script: {r2.stdout.strip()}")

# Launch with nohup
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
print("=" * 60)
print("CAMPAIGN LAUNCHED SUCCESSFULLY")
print("=" * 60)
print(f"  25 sims in 4 batches of 7/7/7/4")
print(f"  Monitor with:")
print(f"    ssh -i /shared/keys/astra-climate.key {SSH_HOST} \\")
print(f"      'tail -30 {MASTER_LOG}'")
print(f"    ssh -i /shared/keys/astra-climate.key {SSH_HOST} \\")
print(f"      'ps aux | grep mpirun | grep -v grep | wc -l'")
