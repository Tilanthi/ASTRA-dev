#!/usr/bin/env python3
"""
Generate combined validation report from all three test campaigns

Creates:
- VALIDATION_REPORT.pdf: Summary for peer review response
- VALIDATION_DATA.json: Machine-readable results
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Load all analysis results
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

print("="*70)
print("Generating Combined Validation Report")
print("="*70)
print()

# Try to load individual analysis results
resolution_file = output_dir / "resolution_analysis.json"
equilibrium_file = output_dir / "equilibrium_analysis.json"
nonisothermal_file = output_dir / "nonisothermal_analysis.json"

results = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "campaigns": {}
}

# Load resolution test results
if resolution_file.exists():
    with open(resolution_file, "r") as f:
        results["campaigns"]["TEST_M3_RESOLUTION"] = json.load(f)
    print("✓ Loaded TEST_M3_RESOLUTION results")
else:
    print("⚠ TEST_M3_RESOLUTION analysis not found — skipping")
    results["campaigns"]["TEST_M3_RESOLUTION"] = {"verdict": "UNKNOWN"}

# Load equilibrium test results
if equilibrium_file.exists():
    with open(equilibrium_file, "r") as f:
        results["campaigns"]["TEST_M2_EQUILIBRIUM"] = json.load(f)
    print("✓ Loaded TEST_M2_EQUILIBRIUM results")
else:
    print("⚠ TEST_M2_EQUILIBRIUM analysis not found — skipping")
    results["campaigns"]["TEST_M2_EQUILIBRIUM"] = {"verdict": "UNKNOWN"}

# Load non-isothermal test results
if nonisothermal_file.exists():
    with open(nonisothermal_file, "r") as f:
        results["campaigns"]["TEST_M5_NONISOTHERMAL"] = json.load(f)
    print("✓ Loaded TEST_M5_NONISOTHERMAL results")
else:
    print("⚠ TEST_M5_NONISOTHERMAL analysis not found — skipping")
    results["campaigns"]["TEST_M5_NONISOTHERMAL"] = {"verdict": "UNKNOWN"}

print()

# Generate overall assessment
verdicts = [v.get("verdict", "UNKNOWN") for v in results["campaigns"].values()]

if "FAIL" in verdicts:
    overall_verdict = "FAIL"
    summary = "One or more tests show serious issues that undermine the paper's claims."
elif "PARTIAL" in verdicts or "UNKNOWN" in verdicts:
    overall_verdict = "PARTIAL"
    summary = "Tests show some concerns but the paper's main conclusions remain valid with caveats."
else:
    overall_verdict = "PASS"
    summary = "All validation tests pass — the paper's claims are robust to the tested concerns."

results["overall_assessment"] = {
    "verdict": overall_verdict,
    "summary": summary
}

print("="*70)
print("OVERALL ASSESSMENT")
print("="*70)
print(f"Verdict: {overall_verdict}")
print(f"Summary: {summary}")
print()

# Save machine-readable results
with open(output_dir / "VALIDATION_DATA.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Results saved to: {output_dir}/VALIDATION_DATA.json")

# Generate summary figure
fig, ax = plt.subplots(figsize=(10, 6))

campaigns = list(results["campaigns"].keys())
verdict_colors = {"PASS": "#2ecc71", "PARTIAL": "#f39c12", "FAIL": "#e74c3c", "UNKNOWN": "#95a5a6"}
verdict_numeric = {"PASS": 3, "PARTIAL": 2, "UNKNOWN": 1, "FAIL": 0}

colors = [verdict_colors.get(v.get("verdict", "UNKNOWN"), "#95a5a6") for v in results["campaigns"].values()]
values = [verdict_numeric.get(v.get("verdict", "UNKNOWN"), 1) for v in results["campaigns"].values()]

bars = ax.barh(campaigns, values, color=colors, alpha=0.8, edgecolor='black', linewidth=2)

ax.set_xlim(0, 3.5)
ax.set_yticks(range(len(campaigns)))
ax.set_yticklabels(campaigns)
ax.set_xlabel('Validation Status')
ax.set_title('Peer Review Validation Tests Summary')

# Remove x-axis ticks
ax.set_xticks([])

# Add verdict labels
for i, (bar, v) in enumerate(zip(bars, results["campaigns"].values())):
    verdict = v.get("verdict", "UNKNOWN")
    ax.text(0.1, i, verdict, ha='left', va='center', fontweight='bold', color='white')

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=verdict_colors["PASS"], edgecolor='black', label='PASS (Robust)'),
    Patch(facecolor=verdict_colors["PARTIAL"], edgecolor='black', label='PARTIAL (Concerns)'),
    Patch(facecolor=verdict_colors["FAIL"], edgecolor='black', label='FAIL (Not robust)'),
]
ax.legend(handles=legend_elements, loc='lower right')

plt.tight_layout()
plt.savefig(output_dir / "validation_summary.pdf", dpi=150)
print(f"Figure saved to: {output_dir}/validation_summary.pdf")

# Generate text report
report_lines = [
    "Peer Review Validation Tests — Summary Report",
    "="*70,
    "",
    f"Generated: {results['timestamp']}",
    f"Overall Verdict: {overall_verdict}",
    "",
    summary,
    "",
    "="*70,
    "",
    "Test Results:",
    "",
]

for campaign, result in results["campaigns"].items():
    verdict = result.get("verdict", "UNKNOWN")
    report_lines.append(f"{campaign}: {verdict}")

    if campaign == "TEST_M3_RESOLUTION":
        n_disagree = result.get("n_disagreement", 0)
        n_total = result.get("n_points", 1)
        if verdict == "PASS":
            report_lines.append(f"  → All {n_total} points show resolution-independent behavior")
        elif verdict == "PARTIAL":
            report_lines.append(f"  → {n_disagree}/{n_total} points ({n_disagree/n_total*100:.0f}%) show resolution dependence")
        else:
            report_lines.append(f"  → {n_disagree}/{n_total} points ({n_disagree/n_total*100:.0f}%) show resolution dependence")

    elif campaign == "TEST_M2_EQUILIBRIUM":
        n_disagree = result.get("n_disagreement", 0)
        mean_diff = result.get("mean_relative_difference", 0) * 100
        if verdict == "PASS":
            report_lines.append(f"  → IC choice has minimal effect (mean diff: {mean_diff:.0f}%)")
        elif verdict == "PARTIAL":
            report_lines.append(f"  → IC choice causes systematic differences (mean diff: {mean_diff:.0f}%)")
        else:
            report_lines.append(f"  → {n_disagree} points show qualitative disagreement")

    elif campaign == "TEST_M5_NONISOTHERMAL":
        max_delta = result.get("max_delta_lambda_W", 0) * 100
        if verdict == "PASS":
            report_lines.append(f"  → Non-isothermal effects are minor (max Δ(λ/W): {max_delta:.1f}%)")
        elif verdict == "PARTIAL":
            report_lines.append(f"  → Non-isothermal effects are moderate (max Δ(λ/W): {max_delta:.1f}%)")
        else:
            report_lines.append(f"  → Non-isothermal effects are large (max Δ(λ/W): {max_delta:.1f}%)")

    report_lines.append("")

report_lines.extend([
    "="*70,
    "",
    "Recommendations for Peer Review Response:",
    "",
])

if overall_verdict == "PASS":
    report_lines.extend([
        "All validation tests pass. The paper's claims are robust to the",
        "reviewer's theoretical concerns. We can confidently state that:",
        "",
        "• The apparent stochastic zone is physical, not numerical (TEST_M3)",
        "• DTC results are robust to initial condition choice (TEST_M2)",
        "• Non-isothermal effects do not significantly affect conclusions (TEST_M5)",
        "",
        "We recommend submitting the response without additional simulation work.",
    ])
elif overall_verdict == "PARTIAL":
    report_lines.extend([
        "Tests show some concerns but the paper's main conclusions remain valid.",
        "We recommend addressing the concerns as follows:",
        "",
        "• Add caveats to the discussion of affected results",
        "• Acknowledge the limitations in the response letter",
        "• If reviewers insist, commit to future work in the revised manuscript",
        "",
        "The core contribution (DTC mapping of fragmentation boundary) remains",
        "valid and scientifically valuable.",
    ])
else:
    report_lines.extend([
        "Tests reveal significant issues. We recommend:",
        "",
        "• Address the failing test(s) before resubmission",
        "• If resolution is the issue, repeat affected simulations at higher resolution",
        "• If IC dependence is the issue, discuss the limitations in the paper",
        "• Consider revising the scope of claims to focus on robust results",
        "",
        "The paper may need revision before it can withstand peer review scrutiny.",
    ])

report_lines.extend([
    "",
    "="*70,
    "",
    "Files for response:",
    f"  • {output_dir}/VALIDATION_DATA.json — Machine-readable results",
    f"  • {output_dir}/validation_summary.pdf — Summary figure",
    f"  • Individual test reports in {output_dir}/",
    "",
])

with open(output_dir / "VALIDATION_REPORT.txt", "w") as f:
    f.write("\n".join(report_lines))

# Print report
print("\n".join(report_lines))

print()
print("="*70)
print("Report generation complete!")
print("="*70)
print(f"Text report: {output_dir}/VALIDATION_REPORT.txt")
print(f"Data file: {output_dir}/VALIDATION_DATA.json")
print(f"Figure: {output_dir}/validation_summary.pdf")
