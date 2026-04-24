#!/usr/bin/env python3
"""
Generate Summary Report

Creates comprehensive summary report combining DTC re-run and
resolution convergence analysis results.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Configuration
STATUS_DIR = "../output/status"
RUN_LIST_PATH = "../simulations/run_list.json"
OUTPUT_DIR = "../output/analysis"

def load_status_files() -> Dict[str, Dict]:
    """Load all status files."""
    status_files = {}
    status_dir = Path(STATUS_DIR)

    if not status_dir.exists():
        return status_files

    for status_file in status_dir.glob("status_*.json"):
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                run_id = data['run_id']
                status_files[run_id] = data
        except Exception as e:
            print(f"Warning: Could not load {status_file}: {e}")

    return status_files

def generate_dtc_summary(status_files: Dict[str, Dict]) -> Dict:
    """Generate DTC re-run summary."""
    dtc_results = [s for s in status_files.values() if s['run_id'].startswith('dtc_rerun_')]

    if not dtc_results:
        return {"error": "No DTC results found"}

    frag = sum(1 for s in dtc_results if s['status'] == 'FRAG')
    stable = sum(1 for s in dtc_results if s['status'] == 'STABLE')
    timeout = sum(1 for s in dtc_results if s['status'] == 'TIMEOUT')
    failed = sum(1 for s in dtc_results if s['status'] == 'FAILED')

    total = len(dtc_results)
    frag_frac = frag / total if total > 0 else 0

    return {
        "total": total,
        "frag": frag,
        "stable": stable,
        "timeout": timeout,
        "failed": failed,
        "frag_fraction": frag_frac,
        "interpretation": f"{frag_frac*100:.1f}% of DTC STABLE points were timeout artifacts"
    }

def generate_resolution_summary(status_files: Dict[str, Dict], run_list: Dict) -> Dict:
    """Generate resolution convergence summary."""
    res_sims = [s for s in run_list['simulations'] if s['priority'] == 2]
    comparisons = []

    for sim in res_sims:
        run_id = sim['run_id']
        if run_id in status_files:
            status_256 = status_files[run_id]
            tfrag_256 = status_256.get('t_frag')
            tfrag_128 = sim.get('ref_tfrag_128')

            if tfrag_256 and tfrag_128 and status_256['status'] == 'FRAG':
                rel_diff = abs(tfrag_256 - tfrag_128) / tfrag_128
                converged = rel_diff < 0.05
                comparisons.append({
                    'run_id': run_id,
                    'converged': converged,
                    'rel_diff': rel_diff
                })

    if not comparisons:
        return {"error": "No resolution comparisons available"}

    converged_count = sum(1 for c in comparisons if c['converged'])
    conv_rate = converged_count / len(comparisons)

    return {
        "total": len(comparisons),
        "converged": converged_count,
        "not_converged": len(comparisons) - converged_count,
        "convergence_rate": conv_rate,
        "interpretation": f"{conv_rate*100:.1f}% show <5% resolution dependence"
    }

def generate_markdown_report(dtc_summary: Dict, res_summary: Dict) -> str:
    """Generate markdown summary report."""
    report = []
    report.append("# Peer Review Validation Campaign - Summary Report")
    report.append("")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("---")
    report.append("")

    # DTC Summary
    report.append("## Priority 1: DTC Re-run Results")
    report.append("")
    report.append("### Summary Statistics")
    report.append("")

    if "error" not in dtc_summary:
        report.append(f"| Metric | Count |")
        report.append(f"|--------|-------|")
        report.append(f"| Total simulations | {dtc_summary['total']} |")
        report.append(f"| **FRAG** (fragmented) | {dtc_summary['frag']} |")
        report.append(f"| **STABLE** (no fragmentation) | {dtc_summary['stable']} |")
        report.append(f"| **TIMEOUT** (incomplete) | {dtc_summary['timeout']} |")
        report.append(f"| **FAILED** (crashes) | {dtc_summary['failed']} |")
        report.append("")

        frag_frac = dtc_summary['frag_fraction']
        report.append(f"**Key Result:** {dtc_summary['interpretation']}")
        report.append("")

        # Impact assessment
        if frag_frac > 0.5:
            report.append("### Impact Assessment: **MAJOR**")
            report.append("")
            report.append(f"The DTC transition map significantly overestimates stability. {frag_frac*100:.1f}% of")
            report.append("original STABLE classifications were timeout artifacts. Figure 2 in the revised")
            report.append("manuscript should include uncertainty quantification reflecting these findings.")
        elif frag_frac > 0.2:
            report.append("### Impact Assessment: **MODERATE**")
            report.append("")
            report.append(f"The DTC transition map requires uncertainty quantification. {frag_frac*100:.1f}% of")
            report.append("original STABLE classifications were timeout artifacts. The manuscript should")
            report.append("discuss this limitation explicitly.")
        else:
            report.append("### Impact Assessment: **MINOR**")
            report.append("")
            report.append(f"The DTC transition map is largely reliable. Only {frag_frac*100:.1f}% of original")
            report.append("STABLE classifications were timeout artifacts. The original results stand with")
            report.append("minor caveats.")
    else:
        report.append(f"**Error:** {dtc_summary['error']}")

    report.append("")
    report.append("---")
    report.append("")

    # Resolution Summary
    report.append("## Priority 2: Resolution Convergence Results")
    report.append("")
    report.append("### Summary Statistics")
    report.append("")

    if "error" not in res_summary:
        report.append(f"| Metric | Count |")
        report.append(f"|--------|-------|")
        report.append(f"| Total comparisons | {res_summary['total']} |")
        report.append(f"| **Converged** (<5% difference) | {res_summary['converged']} |")
        report.append(f"| **Not converged** (>5% difference) | {res_summary['not_converged']} |")
        report.append("")

        conv_rate = res_summary['convergence_rate']
        report.append(f"**Key Result:** {res_summary['interpretation']}")
        report.append("")

        # Impact assessment
        if conv_rate > 0.8:
            report.append("### Impact Assessment: **GOOD CONVERGENCE**")
            report.append("")
            report.append(f"{conv_rate*100:.1f}% of parameter points show <5% resolution dependence.")
            report.append("128^3 resolution is adequate for this parameter space. No resolution correction")
            report.append("needed in the manuscript.")
        elif conv_rate > 0.5:
            report.append("### Impact Assessment: **MODERATE CONVERGENCE**")
            report.append("")
            report.append(f"{conv_rate*100:.1f}% of parameter points show <5% resolution dependence.")
            report.append("Resolution uncertainty should be quantified and propagated to results. The")
            report.append("manuscript should discuss this as a systematic uncertainty.")
        else:
            report.append("### Impact Assessment: **POOR CONVERGENCE**")
            report.append("")
            report.append(f"Only {conv_rate*100:.1f}% of parameter points show <5% resolution dependence.")
            report.append("Resolution dependence is significant. The manuscript should either (a) present")
            report.append("256^3 results as primary, or (b) apply resolution correction factors.")
    else:
        report.append(f"**Error:** {res_summary['error']}")

    report.append("")
    report.append("---")
    report.append("")

    # Overall Conclusions
    report.append("## Overall Conclusions and Recommendations")
    report.append("")
    report.append("### For Peer Review Response")
    report.append("")
    report.append("These results provide quantitative constraints on the two main referee concerns:")
    report.append("")
    report.append("1. **DTC Reliability**: ")
    if "error" not in dtc_summary:
        report.append(f"   - {dtc_summary['frag_fraction']*100:.1f}% of DTC STABLE points were timeout artifacts")
        report.append("   - This quantifies the uncertainty in Figure 2")
    else:
        report.append("   - Unable to assess (no DTC results available)")
    report.append("")
    report.append("2. **Resolution Convergence**: ")
    if "error" not in res_summary:
        report.append(f"   - {res_summary['convergence_rate']*100:.1f}% of points show resolution convergence")
        report.append("   - This quantifies the resolution uncertainty")
    else:
        report.append("   - Unable to assess (no resolution results available)")
    report.append("")
    report.append("### For Manuscript Revision")
    report.append("")
    report.append("Based on these results, the revised manuscript should:")
    report.append("")
    report.append("1. **Add uncertainty quantification** to Figure 2 (DTC transition map)")
    report.append("2. **Discuss resolution dependence** as a systematic uncertainty")
    report.append("3. **Be transparent** about timeout limitations in original campaigns")
    report.append("4. **Present limitations upfront** rather than burying them in discussion")
    report.append("")

    return "\n".join(report)

def main():
    """Main report generation workflow."""
    print("Generating Summary Report")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load data
    print("Loading simulation results...")
    status_files = load_status_files()

    if not status_files:
        print("Error: No status files found. Run simulations first.")
        sys.exit(1)

    with open(RUN_LIST_PATH, 'r') as f:
        run_list = json.load(f)

    print(f"Loaded {len(status_files)} status files")

    # Generate summaries
    print("\nGenerating DTC summary...")
    dtc_summary = generate_dtc_summary(status_files)

    print("Generating resolution summary...")
    res_summary = generate_resolution_summary(status_files, run_list)

    # Generate markdown report
    print("\nGenerating markdown report...")
    report = generate_markdown_report(dtc_summary, res_summary)

    # Save report
    report_path = os.path.join(OUTPUT_DIR, "SUMMARY_REPORT.md")
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"Report saved to {report_path}")

    # Save JSON summaries
    json_path = os.path.join(OUTPUT_DIR, "summary.json")
    with open(json_path, 'w') as f:
        json.dump({
            "dtc_summary": dtc_summary,
            "resolution_summary": res_summary,
            "generated_at": datetime.now().isoformat()
        }, f, indent=2)

    print(f"JSON summary saved to {json_path}")

    print("\nReport generation complete!")

if __name__ == "__main__":
    main()
