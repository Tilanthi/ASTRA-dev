#!/usr/bin/env python3
"""
Step 2: Post-processing analysis of DTC campaign.
Reads HST files for C(t) history and classifies fragmentation.
Computes P(frag | f, beta, M) and beta_crit(f, M).
"""
import json, os, glob, re, math
import numpy as np

SIMBASE = "/data/dtc_runs"
MANIFEST = os.path.join(SIMBASE, "manifest.json")
RESULTS  = os.path.join(SIMBASE, "dtc_analysis_results.json")

with open(MANIFEST) as f:
    manifest = json.load(f)

print(f"Loaded {len(manifest)} manifest entries")

# Grid parameters
f_vals    = sorted(set(round(s["f"],    1) for s in manifest))
beta_vals = sorted(set(round(s["beta"], 1) for s in manifest))
mach_vals = sorted(set(round(s["mach"], 1) for s in manifest))
seeds     = sorted(set(s["seed"] for s in manifest))

print(f"f values:    {f_vals}")
print(f"beta values: {beta_vals}")
print(f"mach values: {mach_vals}")
print(f"seeds:       {seeds}")

# --- Read HST files for each sim ---
def read_hst(run_dir, run_id):
    """Read Athena++ history file. Returns dict with arrays."""
    hst_path = os.path.join(run_dir, f"{run_id}.hst")
    if not os.path.exists(hst_path):
        return None
    try:
        data = np.loadtxt(hst_path, comments="#")
        if data.ndim == 1:
            data = data.reshape(1, -1)
        return {
            "time":   data[:, 0],
            "dt":     data[:, 1],
            "mass":   data[:, 2],
            "ke1":    data[:, 6],
            "ke2":    data[:, 7],
            "ke3":    data[:, 8],
            "grav_E": data[:, 9],
            "me1":    data[:, 10],
            "me2":    data[:, 11],
            "me3":    data[:, 12],
        }
    except Exception as e:
        return None

def compute_C_from_hst(hst, rho_c, rho_bg=1.0):
    """
    Estimate density contrast C from gravitational energy.
    grav_E ≈ -G * integral(rho^2) dV, so |grav_E| grows with C.
    We use |grav_E|_final / |grav_E|_initial as a proxy.
    """
    if hst is None or len(hst["grav_E"]) < 2:
        return 1.0
    ge = np.abs(hst["grav_E"])
    if ge[0] == 0:
        return 1.0
    return float(ge[-1] / ge[0])

# --- Process each sim ---
results = []
for s in manifest:
    run_id  = s["run_id"]
    run_dir = s["run_dir"]
    rho_c   = s["rho_c"]

    hst = read_hst(run_dir, run_id)
    fragmented = (s["status"] == "timeout_frag")

    # C proxy from gravitational energy ratio
    C_proxy = compute_C_from_hst(hst, rho_c)

    # t_final and dt_final from HST
    t_final  = float(hst["time"][-1]) if hst is not None else s.get("t_final", 0.0)
    dt_final = float(hst["dt"][-1])   if hst is not None else 0.0
    n_steps  = len(hst["time"])       if hst is not None else 0

    # KE ratio (turbulent energy dissipation indicator)
    ke1_ratio = 1.0
    if hst is not None and hst["ke1"][0] > 0:
        ke1_ratio = float(hst["ke1"][-1] / hst["ke1"][0])

    results.append({
        "run_id":     run_id,
        "f":          s["f"],
        "beta":       s["beta"],
        "mach":       s["mach"],
        "seed":       s["seed"],
        "phase":      s["phase"],
        "status":     s["status"],
        "fragmented": fragmented,
        "t_final":    round(t_final, 6),
        "dt_final":   float(f"{dt_final:.4e}"),
        "C_proxy":    round(C_proxy, 4),
        "ke1_ratio":  round(ke1_ratio, 4),
        "n_snaps":    s.get("n_snaps", 0),
    })

print(f"\nProcessed {len(results)} sims")

# --- Compute P(frag | f, beta, M) ---
# Group by (f, beta, mach), count fragmented seeds
grid = {}
for r in results:
    key = (r["f"], r["beta"], r["mach"])
    if key not in grid:
        grid[key] = {"n_total": 0, "n_frag": 0, "n_ok": 0, "C_proxies": [], "t_finals": []}
    grid[key]["n_total"] += 1
    if r["fragmented"]:
        grid[key]["n_frag"] += 1
    else:
        grid[key]["n_ok"] += 1
    grid[key]["C_proxies"].append(r["C_proxy"])
    grid[key]["t_finals"].append(r["t_final"])

# Build P_frag table
p_frag_table = []
for (fv, beta, mach), g in sorted(grid.items()):
    p_frag = g["n_frag"] / g["n_total"]
    stochastic = (0 < p_frag < 1)
    p_frag_table.append({
        "f": fv, "beta": beta, "mach": mach,
        "n_total": g["n_total"], "n_frag": g["n_frag"], "n_ok": g["n_ok"],
        "P_frag": round(p_frag, 4),
        "stochastic": stochastic,
        "C_proxy_mean": round(float(np.mean(g["C_proxies"])), 4),
        "t_final_mean": round(float(np.mean(g["t_finals"])), 4),
    })

# --- Compute beta_crit(f, M) ---
# beta_crit = threshold beta where P_frag transitions from 0 → 1
# Use linear interpolation between last stable and first unstable beta
beta_crit_table = []
for fv in f_vals:
    for mach in mach_vals:
        row = sorted([p for p in p_frag_table if p["f"] == fv and p["mach"] == mach],
                     key=lambda x: x["beta"])
        if not row:
            continue
        # Find transition
        beta_crit = None
        crit_type = "unknown"
        for i in range(len(row) - 1):
            if row[i]["P_frag"] == 0 and row[i+1]["P_frag"] > 0:
                # Linear interpolation
                b0, b1 = row[i]["beta"], row[i+1]["beta"]
                p0, p1 = row[i]["P_frag"], row[i+1]["P_frag"]
                beta_crit = round(b0 + (b1 - b0) * (0.5 - p0) / (p1 - p0), 3) if p1 > p0 else (b0 + b1) / 2
                crit_type = "interpolated"
                break
        if beta_crit is None:
            if row[0]["P_frag"] == 1.0:
                beta_crit = row[0]["beta"] - 0.1
                crit_type = "below_grid"  # all fragmented, crit below lowest beta
            elif row[-1]["P_frag"] == 0.0:
                beta_crit = row[-1]["beta"] + 0.1
                crit_type = "above_grid"  # all stable, crit above highest beta
        beta_crit_table.append({
            "f": fv, "mach": mach,
            "beta_crit": beta_crit,
            "crit_type": crit_type,
        })

# --- Summary statistics ---
n_total   = len(results)
n_frag    = sum(1 for r in results if r["fragmented"])
n_ok      = n_total - n_frag
n_stoch   = sum(1 for p in p_frag_table if p["stochastic"])

print(f"\n=== ANALYSIS SUMMARY ===")
print(f"Total sims:          {n_total}")
print(f"Fragmented (FRAG):   {n_frag} ({100*n_frag/n_total:.1f}%)")
print(f"Stable (OK):         {n_ok} ({100*n_ok/n_total:.1f}%)")
print(f"Stochastic points:   {n_stoch} (1/2 seeds FRAG)")
print(f"\nP_frag by Mach:")
for mach in mach_vals:
    rows = [r for r in results if r["mach"] == mach]
    nf = sum(1 for r in rows if r["fragmented"])
    print(f"  M={mach:.1f}: {nf}/{len(rows)} FRAG ({100*nf/len(rows):.1f}%)")

print(f"\nP_frag by f:")
for fv in f_vals:
    rows = [r for r in results if r["f"] == fv]
    nf = sum(1 for r in rows if r["fragmented"])
    print(f"  f={fv:.1f}: {nf}/{len(rows)} FRAG ({100*nf/len(rows):.1f}%)")

print(f"\nbeta_crit summary:")
for mach in mach_vals:
    rows = [b for b in beta_crit_table if b["mach"] == mach]
    crits = [b["beta_crit"] for b in rows if b["beta_crit"] is not None]
    if crits:
        print(f"  M={mach:.1f}: beta_crit range [{min(crits):.2f}, {max(crits):.2f}]")

# Save results
output = {
    "summary": {
        "n_total": n_total, "n_frag": n_frag, "n_ok": n_ok,
        "frag_fraction": round(n_frag/n_total, 4),
        "n_stochastic_points": n_stoch,
        "f_values": f_vals, "beta_values": beta_vals,
        "mach_values": mach_vals, "seeds": seeds,
    },
    "sim_results":    results,
    "p_frag_table":   p_frag_table,
    "beta_crit_table": beta_crit_table,
}

with open(RESULTS, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nResults saved to {RESULTS}")
