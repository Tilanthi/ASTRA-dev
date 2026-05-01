#!/usr/bin/env python3
"""
Step 1: Reconstruct full 539-entry DTC manifest from disk.
Classifies each sim as completed or timeout_frag based on HST last time.
"""
import json, os, glob, re, math

SIMBASE = "/data/dtc_runs"
MANIFEST = os.path.join(SIMBASE, "manifest.json")
G_code = 0.20977
cs = 1.0
TLIM = 1.5

dirs = sorted(glob.glob(os.path.join(SIMBASE, "DTC_f*_b*_M*_s*")))
print(f"Found {len(dirs)} simulation directories")

manifest = []
stats = {"completed": 0, "timeout_frag": 0, "no_hst": 0}

for d in dirs:
    run_id = os.path.basename(d)
    m = re.match(r"DTC_f([\dp]+)_b([\dp]+)_M([\dp]+)_s(\d+)", run_id)
    if not m:
        print(f"WARNING: can't parse {run_id}")
        continue

    fv   = float(m.group(1).replace("p", "."))
    beta = float(m.group(2).replace("p", "."))
    mach = float(m.group(3).replace("p", "."))
    seed = int(m.group(4))

    # Compute physical parameters
    rho_c = 2.0 * fv * cs**2 / (math.sqrt(2.0 * math.pi) * G_code)
    B0    = cs * math.sqrt(2.0 * rho_c / beta)

    # Determine phase
    phase = "primary" if mach <= 3.0 else "extended"

    # Read HST to get last simulation time
    hst_path = os.path.join(d, f"{run_id}.hst")
    status = "no_hst"
    t_final = 0.0

    if os.path.exists(hst_path):
        try:
            with open(hst_path) as hf:
                lines = [l for l in hf if not l.startswith("#") and l.strip()]
            if lines:
                t_final = float(lines[-1].split()[0])
                # Completed = sim reached within 5% of tlim
                status = "completed" if t_final >= 0.95 * TLIM else "timeout_frag"
        except Exception as e:
            print(f"WARNING: HST read error for {run_id}: {e}")
            status = "timeout_frag"
    else:
        print(f"WARNING: no HST for {run_id}")

    stats[status if status in stats else "no_hst"] += 1

    # Count snapshots
    snaps = sorted(glob.glob(os.path.join(d, f"{run_id}.prim.*.athdf")))
    n_snaps = len(snaps)

    manifest.append({
        "run_id":      run_id,
        "f":           fv,
        "beta":        beta,
        "mach":        mach,
        "seed":        seed,
        "rho_c":       round(rho_c, 6),
        "B0":          round(B0, 6),
        "config_path": os.path.join(d, "athinput.dtc"),
        "run_dir":     d,
        "phase":       phase,
        "status":      status,
        "t_final":     round(t_final, 6),
        "n_snaps":     n_snaps,
    })

# Save reconstructed manifest
with open(MANIFEST, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\nReconstructed manifest: {len(manifest)} entries")
print(f"Status breakdown: {stats}")

phases = {}
for s in manifest:
    p = s["phase"]
    phases[p] = phases.get(p, 0) + 1
print(f"Phases: {phases}")

by_status = {}
for s in manifest:
    k = (s["phase"], s["status"])
    by_status[k] = by_status.get(k, 0) + 1
for k, v in sorted(by_status.items()):
    print(f"  {k[0]:10s} {k[1]:15s}: {v}")
