#!/usr/bin/env python3
"""
Analysis script for TEST_M3_RESOLUTION: Resolution Convergence Test

Compares fragmentation outcomes between 128³ and 256³ resolutions to determine
whether apparent stochastic behavior is physical or resolution-dependent.
"""

import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

# Load results
results_dir = Path("../TEST_M3_RESOLUTION/results")
status_file = Path("../TEST_M3_RESOLUTION/status_resolution.json")

with open(status_file, "r") as f:
    status = json.load(f)

# Group by parameter point
points = defaultdict(lambda: {"128": None, "256": None})

for result in status["results"]:
    if not result["success"]:
        continue

    name = result["name"]
    resolution = str(result["resolution"])

    # Parse parameter values
    parts = name.split("_")
    pt_id = parts[2]  # e.g., "R1"
    f = float(parts[3].replace("f", ""))
    beta = float(parts[4].replace("b", ""))
    mach = float(parts[5].replace("M", ""))
    seed = int(parts[6].replace("s", ""))

    key = (pt_id, f, beta, mach, seed)
    points[key][resolution] = {
        "name": name,
        "resolution": resolution,
        "result": result
    }

# Analyze each parameter point
print("="*70)
print("TEST_M3_RESOLUTION Analysis")
print("="*70)

stochastic_128 = []
stochastic_256 = []
agreement = []
disagreement = []

for key, res in points.items():
    pt_id, f, beta, mach, seed = key

    if res["128"] is None or res["256"] is None:
        continue

    sim_dir_128 = results_dir / res["128"]["name"]
    sim_dir_256 = results_dir / res["256"]["name"]

    # Extract density contrast from HST files
    def get_final_contrast(sim_dir):
        hst_file = sim_dir / "outputs" / f"{sim_dir.name}.myhst"
        if not hst_file.exists():
            return None

        # Read HST file (simple format)
        try:
            data = np.loadtxt(hst_file, comments="#")
            # C(t) = rho_max / rho_mean - 1
            # Last row is final time
            c_final = data[-1, 1] + 1  # Add back the 1
            return c_final
        except:
            return None

    c_128 = get_final_contrast(sim_dir_128)
    c_256 = get_final_contrast(sim_dir_256)

    # Fragmentation threshold
    fragmented_128 = c_128 is not None and c_128 > 2.0
    fragmented_256 = c_256 is not None and c_256 > 2.0

    # Compare outcomes
    if fragmented_128 and fragmented_256:
        outcome = "Both fragmented"
        agreement.append(key)
    elif not fragmented_128 and not fragmented_256:
        outcome = "Both stable"
        agreement.append(key)
    else:
        outcome = "Disagree (resolution-dependent)"
        disagreement.append(key)

    print(f"{pt_id}: f={f}, β={beta}, M={mach}, seed={seed}")
    print(f"  128³: C={c_128:.2f} → {('Fragmented' if fragmented_128 else 'Stable')}")
    print(f"  256³: C={c_256:.2f} → {('Fragmented' if fragmented_256 else 'Stable')}")
    print(f"  → {outcome}")
    print()

# Summary
print("="*70)
print("Summary")
print("="*70)
print(f"Total parameter points: {len(points)}")
print(f"Agreement (same outcome at both resolutions): {len(agreement)}")
print(f"Disagreement (different outcomes): {len(disagreement)}")
print()

# Determine if stochasticity is physical or numerical
if len(disagreement) == 0:
    print("✅ PASS: All points show consistent outcomes between resolutions")
    print("   The stochastic behavior appears to be PHYSICAL, not numerical.")
elif len(disagreement) < len(points) * 0.3:
    print("⚠️  PARTIAL: Some points show resolution-dependence")
    print(f"   {len(disagreement)}/{len(points)} points ({len(disagreement)/len(points)*100:.0f}%) are resolution-dependent")
    print("   The stochastic behavior may be partially numerical.")
else:
    print("❌ FAIL: Most points show resolution-dependence")
    print(f"   {len(disagreement)}/{len(points)} points ({len(disagreement)/len(points)*100:.0f}%) are resolution-dependent")
    print("   The stochastic behavior is likely NUMERICAL, not physical.")

print()
print("="*70)
print()

# Save analysis results
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

analysis_results = {
    "campaign": "TEST_M3_RESOLUTION",
    "n_points": len(points),
    "n_agreement": len(agreement),
    "n_disagreement": len(disagreement),
    "fraction_disagreement": len(disagreement) / len(points) if len(points) > 0 else 0,
    "verdict": "PASS" if len(disagreement) == 0 else ("PARTIAL" if len(disagreement) < len(points) * 0.3 else "FAIL"),
    "agreement": [{"pt_id": k[0], "f": k[1], "beta": k[2], "mach": k[3]} for k in agreement],
    "disagreement": [{"pt_id": k[0], "f": k[1], "beta": k[2], "mach": k[3]} for k in disagreement],
}

with open(output_dir / "resolution_analysis.json", "w") as f:
    json.dump(analysis_results, f, indent=2)

print(f"Analysis results saved to: {output_dir}/resolution_analysis.json")

# Generate simple plot
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(points))
y_128 = []
y_256 = []
labels = []

for i, (key, res) in enumerate(sorted(points.items())):
    if res["128"] is None or res["256"] is None:
        continue

    pt_id, f, beta, mach, seed = key
    labels.append(f"{pt_id}")

    sim_dir_128 = results_dir / res["128"]["name"]
    sim_dir_256 = results_dir / res["256"]["name"]

    def get_final_contrast(sim_dir):
        hst_file = sim_dir / "outputs" / f"{sim_dir.name}.myhst"
        if not hst_file.exists():
            return 1.0
        try:
            data = np.loadtxt(hst_file, comments="#")
            return data[-1, 1] + 1
        except:
            return 1.0

    y_128.append(get_final_contrast(sim_dir_128))
    y_256.append(get_final_contrast(sim_dir_256))

x = np.arange(len(labels))
width = 0.35

bars1 = ax.bar(x - width/2, y_128, width, label='128³', alpha=0.8)
bars2 = ax.bar(x + width/2, y_256, width, label='256³', alpha=0.8)

ax.axhline(y=2.0, color='r', linestyle='--', linewidth=1, label='Fragmentation threshold')

ax.set_xlabel('Parameter Point')
ax.set_ylabel('Final Density Contrast C = ρ_max/ρ_mean')
ax.set_title('Resolution Convergence Test: 128³ vs 256³')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()
ax.grid(axis='y', alpha=0.3)
ax.set_yscale('log')

plt.tight_layout()
plt.savefig(output_dir / "resolution_convergence.pdf", dpi=150)
print(f"Figure saved to: {output_dir}/resolution_convergence.pdf")

print()
print("Analysis complete!")
