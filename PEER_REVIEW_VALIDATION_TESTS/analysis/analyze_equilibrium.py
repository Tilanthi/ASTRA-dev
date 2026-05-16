#!/usr/bin/env python3
"""
Analysis script for TEST_M2_EQUILIBRIUM: Initial Conditions Test

Compares profile-based vs. uniform initial conditions to establish whether
DTC results are robust to IC choice.
"""

import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

# Load results
results_dir = Path("../TEST_M2_EQUILIBRIUM/results")
status_file = Path("../TEST_M2_EQUILIBRIUM/status_equilibrium.json")

with open(status_file, "r") as f:
    status = json.load(f)

# Group by parameter point
points = defaultdict(lambda: {"profile": None, "uniform": None})

for result in status["results"]:
    if not result["success"]:
        continue

    name = result["name"]
    ic_type = result["ic_type"]

    # Parse parameter values
    parts = name.split("_")
    pt_id = parts[2]  # e.g., "E1"
    f = float(parts[3].replace("f", ""))
    beta = float(parts[4].replace("b", ""))
    mach = float(parts[5].replace("M", ""))

    key = (pt_id, f, beta, mach)
    points[key][ic_type] = {
        "name": name,
        "ic_type": ic_type,
        "result": result
    }

# Analyze each parameter point
print("="*70)
print("TEST_M2_EQUILIBRIUM Analysis")
print("="*70)

agreement = []
disagreement = []
differences = []

for key, res in points.items():
    pt_id, f, beta, mach = key

    if res["profile"] is None or res["uniform"] is None:
        continue

    sim_dir_profile = results_dir / res["profile"]["name"]
    sim_dir_uniform = results_dir / res["uniform"]["name"]

    def get_metrics(sim_dir):
        hst_file = sim_dir / "outputs" / f"{sim_dir.name}.myhst"
        if not hst_file.exists():
            return None, None, None

        try:
            data = np.loadtxt(hst_file, comments="#")

            # Final density contrast
            c_final = data[-1, 1] + 1

            # Growth rate from linear phase (C < 3)
            linear_idx = data[:, 1] < 2.0
            if np.sum(linear_idx) > 10:
                t = data[linear_idx, 0]
                c = data[linear_idx, 1] + 1
                ln_c = np.log(c - 1)
                # Fit ln(C-1) ∝ γt
                gamma = np.polyfit(t, ln_c, 1)[0]
            else:
                gamma = None

            # Estimate spacing from dominant wavelength (using power spectrum)
            # For now, use fragmentation status
            fragmented = c_final > 2.0

            return c_final, gamma, fragmented
        except:
            return None, None, None

    c_profile, gamma_profile, frag_profile = get_metrics(sim_dir_profile)
    c_uniform, gamma_uniform, frag_uniform = get_metrics(sim_dir_uniform)

    if c_profile is None or c_uniform is None:
        continue

    # Relative difference
    rel_diff_c = abs(c_profile - c_uniform) / ((c_profile + c_uniform) / 2)

    # Compare outcomes
    if frag_profile == frag_uniform:
        outcome = "Agreement" if rel_diff_c < 0.2 else "Partial agreement"
        agreement.append((key, rel_diff_c))
    else:
        outcome = "Qualitative disagreement"
        disagreement.append((key, rel_diff_c))

    differences.append((key, c_profile, c_uniform, gamma_profile, gamma_uniform))

    print(f"{pt_id}: f={f}, β={beta}, M={mach}")
    print(f"  Profile IC:   C={c_profile:.2f}, γ={gamma_profile:.2f}, {('Frag' if frag_profile else 'Stable')}")
    print(f"  Uniform IC:    C={c_uniform:.2f}, γ={gamma_uniform:.2f}, {('Frag' if frag_uniform else 'Stable')}")
    print(f"  Relative diff: {rel_diff_c*100:.1f}%")
    print(f"  → {outcome}")
    print()

# Summary
print("="*70)
print("Summary")
print("="*70)
print(f"Total parameter points: {len(points)}")
print(f"Agreement (same outcome, <20% diff): {len(agreement)}")
print(f"Disagreement (different outcomes): {len(disagreement)}")
print()

# Mean relative difference
if differences:
    mean_rel_diff = np.mean([d[1] for d in differences])
    print(f"Mean relative difference in C_final: {mean_rel_diff*100:.1f}%")

# Determine robustness
if len(disagreement) == 0 and mean_rel_diff < 0.2:
    print("✅ PASS: IC choice has minimal effect on outcomes")
    print("   DTC results are ROBUST to initial conditions.")
elif len(disagreement) == 0:
    print("⚠️  PARTIAL: IC choice affects C_final but not qualitative outcomes")
    print(f"   Mean difference: {mean_rel_diff*100:.0f}%")
    print("   DTC results are mostly robust but show systematic IC dependence.")
else:
    print("❌ FAIL: IC choice qualitatively affects fragmentation outcomes")
    print(f"   {len(disagreement)}/{len(points)} points show different fragmentation status")
    print("   DTC results are NOT robust to initial conditions.")

print()
print("="*70)
print()

# Save analysis results
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

analysis_results = {
    "campaign": "TEST_M2_EQUILIBRIUM",
    "n_points": len(points),
    "n_agreement": len(agreement),
    "n_disagreement": len(disagreement),
    "mean_relative_difference": mean_rel_diff if differences else 0,
    "verdict": "PASS" if (len(disagreement) == 0 and mean_rel_diff < 0.2) else ("PARTIAL" if len(disagreement) == 0 else "FAIL"),
    "agreement": [{"pt_id": k[0], "f": k[1], "beta": k[2], "mach": k[3]} for k, _ in agreement],
    "disagreement": [{"pt_id": k[0], "f": k[1], "beta": k[2], "mach": k[3]} for k, _ in disagreement],
}

with open(output_dir / "equilibrium_analysis.json", "w") as f:
    json.dump(analysis_results, f, indent=2)

print(f"Analysis results saved to: {output_dir}/equilibrium_analysis.json")

# Generate comparison plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: C_final comparison
ax = axes[0]
labels = [d[0][0] for d in differences]
c_profile = [d[1] for d in differences]
c_uniform = [d[2] for d in differences]

x = np.arange(len(labels))
width = 0.35

bars1 = ax.bar(x - width/2, c_profile, width, label='Profile IC', alpha=0.8)
bars2 = ax.bar(x + width/2, c_uniform, width, label='Uniform IC', alpha=0.8)

ax.axhline(y=2.0, color='r', linestyle='--', linewidth=1, label='Fragmentation threshold')

ax.set_xlabel('Parameter Point')
ax.set_ylabel('Final Density Contrast C = ρ_max/ρ_mean')
ax.set_title('Initial Conditions Comparison: Profile vs. Uniform')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Plot 2: Relative difference
ax = axes[1]
rel_diffs = [abs(d[1] - d[2]) / ((d[1] + d[2])/2) * 100 for d in differences]

ax.bar(labels, rel_diffs, alpha=0.8, color='orange')
ax.axhline(y=20, color='r', linestyle='--', linewidth=1, label='20% threshold')
ax.set_xlabel('Parameter Point')
ax.set_ylabel('Relative Difference (%)')
ax.set_title('Relative Difference in C_final')
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / "equilibrium_comparison.pdf", dpi=150)
print(f"Figure saved to: {output_dir}/equilibrium_comparison.pdf")

print()
print("Analysis complete!")
