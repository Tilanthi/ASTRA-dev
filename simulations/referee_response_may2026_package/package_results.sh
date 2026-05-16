#!/bin/bash
# Package Results Script — Prepare results for transfer
#
# This script packages all campaign results into a tar.gz file
# and creates a summary for quick reference.

set -e

BASE_DIR="/data/referee_response_may2026"
OUTPUT_FILE="referee_response_results.tar.gz"
SUMMARY_FILE="results_summary.json"

echo "=================================================="
echo "Packaging Referee Response Campaign Results"
echo "=================================================="
echo ""

cd "$BASE_DIR"

# Create summary
echo "Creating results summary..."

python3 << 'EOF'
import json
from pathlib import Path

BASE_DIR = Path("/data/referee_response_may2026")
CAMPAIGNS = ["ctzm_perp", "eos_sensitivity", "turb_amplitude"]

summary = {
    "package_version": "1.0",
    "date": None,  # Will be filled in
    "campaigns": {}
}

for campaign in CAMPAIGNS:
    campaign_dir = BASE_DIR / campaign

    # Try different result file names
    results_file = None
    for name in [f"{campaign}_results.json", f"{campaign}_analysed.json"]:
        if (campaign_dir / name).exists():
            results_file = campaign_dir / name
            break

    if not results_file or not results_file.exists():
        print(f"  WARNING: No results found for {campaign}")
        summary["campaigns"][campaign] = {"status": "NOT_FOUND"}
        continue

    with open(results_file, 'r') as f:
        results = json.load(f)

    # Extract summary statistics
    n_total = len(results)
    n_frag = sum(1 for r in results if r.get("outcome") == "FRAG")
    n_timeout = sum(1 for r in results if r.get("outcome") == "TIMEOUT")
    n_beading = sum(1 for r in results if "BEADING" in r.get("classification", ""))
    n_radial = sum(1 for r in results if "RADIAL" in r.get("classification", ""))

    lw_vals = [r.get("lw_mean") for r in results if r.get("lw_mean")]
    lw_mean = float(sum(lw_vals) / len(lw_vals)) if lw_vals else None
    lw_std = float((sum((x - lw_mean)**2 for x in lw_vals) / len(lw_vals))**0.5) if lw_vals and len(lw_vals) > 1 else None

    summary["campaigns"][campaign] = {
        "status": "COMPLETE",
        "n_total": n_total,
        "n_frag": n_frag,
        "n_timeout": n_timeout,
        "n_beading": n_beading,
        "n_radial_collapse": n_radial,
        "lw_mean": lw_mean,
        "lw_std": lw_std,
        "n_with_lw": len(lw_vals)
    }

summary["total_sims"] = sum(c["n_total"] for c in summary["campaigns"].values())
summary["total_frag"] = sum(c["n_frag"] for c in summary["campaigns"].values())

print(json.dumps(summary, indent=2))

# Save summary
with open(BASE_DIR / "results_summary.json", 'w') as f:
    json.dump(summary, f, indent=2)

print("\nSummary saved to: results_summary.json")
EOF

echo ""
echo "Packaging results into tar.gz..."

# Package all important files
tar -czf "$OUTPUT_FILE" \
    ctzm_perp/ctzm_perp_analysed.json \
    ctzm_perp/ctzm_perp_summary.json \
    ctzm_perp/figures/ \
    eos_sensitivity/eos_sensitivity_analysed.json \
    eos_sensitivity/eos_sensitivity_summary.json \
    eos_sensitivity/figures/ \
    turb_amplitude/turb_amplitude_analysed.json \
    turb_amplitude/turb_amplitude_summary.json \
    turb_amplitude/figures/ \
    results_summary.json \
    2>/dev/null || echo "  Note: Some files may not exist yet (run analysis first)"

echo ""
echo "=================================================="
echo "Packaging Complete"
echo "=================================================="
echo ""
echo "Package: $BASE_DIR/$OUTPUT_FILE"
echo "Size: $(du -h "$BASE_DIR/$OUTPUT_FILE" | cut -f1)"
echo ""
echo "To transfer to local machine:"
echo "  scp $BASE_DIR/$OUTPUT_FILE user@local:/path/to/dest/"
echo ""
echo "To extract on local machine:"
echo "  tar -xzf $OUTPUT_FILE"
echo ""
