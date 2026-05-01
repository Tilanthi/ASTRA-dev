#!/usr/bin/env python3
"""
Post-Processing Analysis Script

Analyzes completed simulation results and generates summary statistics
for the peer review validation campaign.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List
import numpy as np

# Configuration
STATUS_DIR = "../output/status"
RUN_LIST_PATH = "../simulations/run_list.json"
OUTPUT_DIR = "../output/analysis"

def load_results() -> List[Dict]:
    """Load all simulation status files."""
    status_files = []
    status_dir = Path(STATUS_DIR)

    if not status_dir.exists():
        print(f"Error: Status directory {STATUS_DIR} not found")
        return status_files

    for status_file in status_dir.glob("status_*.json"):
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                status_files.append(data)
        except Exception as e:
            print(f"Warning: Could not load {status_file}: {e}")

    return status_files

def analyze_dtc_reruns(results: List[Dict]) -> Dict:
    """
    Analyze Priority 1 (DTC) re-runs.

    Quantifies what fraction of original DTC "STABLE" classifications
    were timeout artifacts.
    """
    dtc_results = [r for r in results if r['run_id'].startswith('dtc_rerun_')]

    if not dtc_results:
        return {"error": "No DTC re-run results found"}

    frag_count = sum(1 for r in dtc_results if r['status'] == 'FRAG')
    stable_count = sum(1 for r in dtc_results if r['status'] == 'STABLE')
    timeout_count = sum(1 for r in dtc_results if r['status'] == 'TIMEOUT')
    failed_count = sum(1 for r in dtc_results if r['status'] == 'FAILED')
    total = len(dtc_results)

    # Calculate fraction that were timeout artifacts
    frag_fraction = frag_count / total if total > 0 else 0

    # Analyze by f value
    f_values = {}
    for r in dtc_results:
        f = r['f']
        if f not in f_values:
            f_values[f] = {'FRAG': 0, 'STABLE': 0, 'TIMEOUT': 0, 'FAILED': 0}
        f_values[f][r['status']] += 1

    # Calculate mean t_frag for FRAG cases
    t_frag_values = [r['t_frag'] for r in dtc_results if r['status'] == 'FRAG']
    mean_t_frag = np.mean(t_frag_values) if t_frag_values else 0
    std_t_frag = np.std(t_frag_values) if t_frag_values else 0

    return {
        "total_dtc_reruns": total,
        "frag_count": frag_count,
        "stable_count": stable_count,
        "timeout_count": timeout_count,
        "failed_count": failed_count,
        "frag_fraction": frag_fraction,
        "mean_t_frag": mean_t_frag,
        "std_t_frag": std_t_frag,
        "by_f_value": f_values,
        "interpretation": f"{frag_fraction*100:.1f}% of original DTC STABLE points fragmented with longer runtime"
    }

def analyze_resolution_reruns(results: List[Dict]) -> Dict:
    """
    Analyze Priority 2 (Resolution) re-runs.

    Compares 256^3 results with 128^3 reference to assess convergence.
    """
    res_results = [r for r in results if r['run_id'].startswith('res_rerun_')]

    if not res_results:
        return {"error": "No resolution re-run results found"}

    comparisons = []

    for r in res_results:
        run_id = r['run_id']
        if 'ref_tfrag_128' in r:
            ref_tfrag = r['ref_tfrag_128']
            tfrag_256 = r['t_frag'] if r['status'] == 'FRAG' else None

            if tfrag_256:
                diff = tfrag_256 - ref_tfrag
                rel_diff = abs(diff) / ref_tfrag if ref_tfrag > 0 else 0
                converged = rel_diff < 0.05

                comparisons.append({
                    "run_id": run_id,
                    "f": r['f'],
                    "beta": r['beta'],
                    "mach": r['mach'],
                    "tfrag_128": ref_tfrag,
                    "tfrag_256": tfrag_256,
                    "diff": diff,
                    "rel_diff": rel_diff,
                    "converged": converged
                })

    if not comparisons:
        return {"error": "No valid resolution comparisons (no FRAG at 256^3)"}

    converged_count = sum(1 for c in comparisons if c['converged'])
    not_converged_count = len(comparisons) - converged_count

    mean_rel_diff = np.mean([c['rel_diff'] for c in comparisons])
    std_rel_diff = np.std([c['rel_diff'] for c in comparisons])

    return {
        "total_comparisons": len(comparisons),
        "converged_count": converged_count,
        "not_converged_count": not_converged_count,
        "convergence_rate": converged_count / len(comparisons),
        "mean_rel_diff": mean_rel_diff,
        "std_rel_diff": std_rel_diff,
        "comparisons": comparisons,
        "interpretation": f"{converged_count}/{len(comparisons)} show <5% difference (converged)"
    }

def generate_summary_report(dtc_analysis: Dict, res_analysis: Dict) -> str:
    """Generate markdown summary report."""
    report = []
    report.append("# Peer Review Validation Campaign - Summary Report")
    report.append("")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # DTC Re-run Summary
    report.append("## Priority 1: DTC Re-run Results")
    report.append("")

    if "error" not in dtc_analysis:
        report.append(f"Total simulations: {dtc_analysis['total_dtc_reruns']}")
        report.append(f"- **FRAG** (fragmented): {dtc_analysis['frag_count']}")
        report.append(f"- **STABLE** (no fragmentation): {dtc_analysis['stable_count']}")
        report.append(f"- **TIMEOUT** (incomplete): {dtc_analysis['timeout_count']}")
        report.append(f"- **FAILED** (crashes): {dtc_analysis['failed_count']}")
        report.append("")

        frag_fraction = dtc_analysis['frag_fraction']
        report.append(f"**Key Result:** {frag_fraction*100:.1f}% of original DTC STABLE points fragmented with longer runtime")
        report.append("")

        if dtc_analysis['mean_t_frag'] > 0:
            report.append(f"Mean t_frag for FRAG cases: {dtc_analysis['mean_t_frag']:.3f} +/- {dtc_analysis['std_t_frag']:.3f} t_J")
            report.append("")

        report.append("### By f-value")
        report.append("")
        report.append("| f | FRAG | STABLE | TIMEOUT | FAILED |")
        report.append("|---|------|--------|---------|--------|")
        for f in sorted(dtc_analysis['by_f_value'].keys()):
            counts = dtc_analysis['by_f_value'][f]
            report.append(f"| {f:.1f} | {counts['FRAG']} | {counts['STABLE']} | {counts['TIMEOUT']} | {counts['FAILED']} |")
    else:
        report.append(f"Error: {dtc_analysis['error']}")

    report.append("")
    report.append("")

    # Resolution Re-run Summary
    report.append("## Priority 2: Resolution Convergence Results")
    report.append("")

    if "error" not in res_analysis:
        report.append(f"Valid comparisons: {res_analysis['total_comparisons']}")
        report.append(f"- **Converged** (<5% difference): {res_analysis['converged_count']}")
        report.append(f"- **Not converged** (>5% difference): {res_analysis['not_converged_count']}")
        report.append("")

        conv_rate = res_analysis['convergence_rate']
        report.append(f"**Key Result:** {conv_rate*100:.1f}% of parameter points show resolution convergence")
        report.append("")

        report.append(f"Mean relative difference: {res_analysis['mean_rel_diff']*100:.2f}% +/- {res_analysis['std_rel_diff']*100:.2f}%")
        report.append("")

        report.append("### Detailed Comparisons")
        report.append("")
        report.append("| Run ID | f | beta | M | t_128 | t_256 | diff | rel_diff | converged |")
        report.append("|--------|---|-----|---|-------|-------|------|----------|------------|")
        for c in res_analysis['comparisons']:
            report.append(f"| {c['run_id']} | {c['f']} | {c['beta']} | {c['mach']} | {c['tfrag_128']:.3f} | {c['tfrag_256']:.3f} | {c['diff']:+.3f} | {c['rel_diff']*100:.1f}% | {c['converged']} |")
    else:
        report.append(f"Error: {res_analysis['error']}")

    report.append("")
    report.append("")

    # Overall Conclusions
    report.append("## Overall Conclusions")
    report.append("")
    report.append("### DTC Reliability")
    if "error" not in dtc_analysis:
        frag_frac = dtc_analysis['frag_fraction']
        if frag_frac > 0.5:
            report.append(f"**MAJOR IMPACT:** {frag_frac*100:.1f}% of DTC STABLE points were timeout artifacts.")
            report.append("The DTC transition map significantly overestimates stability.")
        elif frag_frac > 0.2:
            report.append(f"**MODERATE IMPACT:** {frag_frac*100:.1f}% of DTC STABLE points were timeout artifacts.")
            report.append("The DTC transition map requires uncertainty quantification.")
        else:
            report.append(f"**MINOR IMPACT:** Only {frag_frac*100:.1f}% of DTC STABLE points were timeout artifacts.")
            report.append("The DTC transition map is largely reliable.")
    else:
        report.append("Unable to assess DTC reliability (no results available).")

    report.append("")
    report.append("### Resolution Convergence")
    if "error" not in res_analysis:
        conv_rate = res_analysis['convergence_rate']
        mean_diff = res_analysis['mean_rel_diff']
        if conv_rate > 0.8:
            report.append(f"**GOOD CONVERGENCE:** {conv_rate*100:.1f}% of points show <5% resolution dependence.")
            report.append("128^3 resolution is adequate for this parameter space.")
        elif conv_rate > 0.5:
            report.append(f"**MODERATE CONVERGENCE:** {conv_rate*100:.1f}% of points show <5% resolution dependence.")
            report.append(f"Mean resolution dependence: {mean_diff*100:.2f}%.")
            report.append("Resolution uncertainty should be propagated to results.")
        else:
            report.append(f"**POOR CONVERGENCE:** Only {conv_rate*100:.1f}% of points show <5% resolution dependence.")
            report.append(f"Mean resolution dependence: {mean_diff*100:.2f}%.")
            report.append("Higher resolution or resolution correction required.")
    else:
        report.append("Unable to assess resolution convergence (no results available).")

    report.append("")

    return "\n".join(report)

def main():
    """Main analysis workflow."""
    print("Peer Review Validation Campaign - Analysis")
    print("=" * 60)

    # Load results
    results = load_results()
    print(f"Loaded {len(results)} status files")

    if not results:
        print("Error: No results found. Check that simulations have completed.")
        sys.exit(1)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Analyze DTC re-runs
    print("\nAnalyzing Priority 1 (DTC) re-runs...")
    dtc_analysis = analyze_dtc_reruns(results)
    print(json.dumps(dtc_analysis, indent=2))

    # Analyze resolution re-runs
    print("\nAnalyzing Priority 2 (Resolution) re-runs...")
    res_analysis = analyze_resolution_reruns(results)
    print(json.dumps(res_analysis, indent=2))

    # Generate summary report
    print("\nGenerating summary report...")
    summary = generate_summary_report(dtc_analysis, res_analysis)

    summary_path = os.path.join(OUTPUT_DIR, "ANALYSIS_SUMMARY.md")
    with open(summary_path, 'w') as f:
        f.write(summary)

    print(f"Summary report written to {summary_path}")

    # Save JSON outputs
    dtc_json_path = os.path.join(OUTPUT_DIR, "dtc_analysis.json")
    with open(dtc_json_path, 'w') as f:
        json.dump(dtc_analysis, f, indent=2)

    res_json_path = os.path.join(OUTPUT_DIR, "resolution_analysis.json")
    with open(res_json_path, 'w') as f:
        json.dump(res_analysis, f, indent=2)

    print(f"JSON results saved to {OUTPUT_DIR}/")

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
