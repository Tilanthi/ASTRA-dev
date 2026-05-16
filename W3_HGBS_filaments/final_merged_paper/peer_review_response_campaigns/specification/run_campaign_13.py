#!/usr/bin/env python3
"""
Campaign 13: Independent β Validation
======================================

Resolves the question: Can β-constraints from λ/W be validated against
independent Zeeman and polarimetry measurements?

This is a RESEARCH campaign - no new simulations required.
Compiles literature β measurements for HGBS regions and compares
with λ/W-derived β predictions using Campaign 7 calibration.

Author: ASTRA Peer Review Response
Date: 2026-04-30
"""

import os
import json
import numpy as np
from datetime import datetime

# =============================================================================
# CAMPAIGN SPECIFICATION
# =============================================================================

CAMPAIGN_ID = "C13_Beta_Validation"
CAMPAIGN_NAME = "Literature β Compilation and Validation"

# HGBS regions
HGBS_REGIONS = [
    'Taurus',
    'OrionB',
    'Aquila',
    'Perseus',
    'Ophiuchus',
    'Serpens',
    'TMC1',
    'CRA',
]

# Campaign 7 calibration for λ/W → β conversion
# From campaign 7 results (f = 1.0-1.2, longitudinal field)
CAMPAIGN_7_CALIBRATION = {
    0.3: 4.74,   # β = 0.3 → λ/W = 4.74
    0.5: 4.38,   # β = 0.5 → λ/W = 4.38
    1.0: 3.19,   # β = 1.0 → λ/W = 3.19
    1.5: 2.86,   # β = 1.5 → λ/W = 2.86
    2.0: 2.80,   # β = 2.0 → λ/W = 2.80
}

# Robust λ/W measurements from paper (Table 1)
PAPER_LAMBDA_W = {
    'Taurus': 1.98,
    'OrionB': 3.56,
    'Aquila': 2.77,
    'Perseus': 2.89,
    'Ophiuchus': 2.76,
    'Serpens': 3.51,
    'TMC1': 2.18,
    'CRA': 2.90,
}

# Output configuration
OUTPUT_BASE = "/data/peer_response_runs/C13"

# =============================================================================
# β PREDICTION FROM λ/W
# =============================================================================

def beta_from_lambda_w(lambda_W):
    """Convert λ/W to β using Campaign 7 calibration (inverse interpolation)."""

    # Interpolate from Campaign 7 data
    beta_values = np.array(list(CAMPAIGN_7_CALIBRATION.keys()))
    lambda_W_values = np.array(list(CAMPAIGN_7_CALIBRATION.values()))

    # Inverse interpolation: given λ/W, find β
    if lambda_W < lambda_W_values.min():
        # Extrapolate (with warning)
        beta_low = beta_values[0]
        lambda_low = lambda_W_values[0]
        beta_high = beta_values[1]
        lambda_high = lambda_W_values[1]

        # Linear extrapolation
        slope = (beta_high - beta_low) / (lambda_high - lambda_low)
        beta_pred = beta_low + slope * (lambda_W - lambda_low)

        return beta_pred, True  # True = extrapolated

    elif lambda_W > lambda_W_values.max():
        # Extrapolate (with warning)
        beta_low = beta_values[-2]
        lambda_low = lambda_W_values[-2]
        beta_high = beta_values[-1]
        lambda_high = lambda_W_values[-1]

        # Linear extrapolation
        slope = (beta_high - beta_low) / (lambda_high - lambda_low)
        beta_pred = beta_high + slope * (lambda_W - lambda_high)

        return beta_pred, True  # True = extrapolated

    else:
        # Interpolate
        beta_pred = np.interp(lambda_W, lambda_W_values, beta_values)
        return beta_pred, False  # False = interpolated

# =============================================================================
# LITERATURE β MEASUREMENTS (Template)
# =============================================================================

LITERATURE_BETA_TEMPLATE = {
    'Taurus': {
        'measurements': [
            {
                'method': 'Zeeman',
                'citation': 'Author et al. (Year)',
                'beta': None,  # To be filled
                'uncertainty': None,  # To be filled
                'tracer': 'OH/CI/etc',
            },
        ],
    },
    'OrionB': {
        'measurements': [],
    },
    'Aquila': {
        'measurements': [],
    },
    'Perseus': {
        'measurements': [],
    },
    'Ophiuchus': {
        'measurements': [],
    },
    'Serpens': {
        'measurements': [],
    },
    'TMC1': {
        'measurements': [],
    },
    'CRA': {
        'measurements': [],
    },
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""

    print("="*70)
    print(f"CAMPAIGN 13: Literature β Compilation and Validation")
    print("="*70)
    print()

    print(f"Objective: Compare λ/W-derived β predictions with independent")
    print(f"Zeeman/polarimetry measurements from literature")
    print()
    print(f"This is a RESEARCH campaign - no new simulations required")
    print()

    # Create output directory
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    # Step 1: Generate β predictions from λ/W
    print("STEP 1: Generate β predictions from λ/W measurements")
    print("-"*70)

    predictions = []
    for region, lambda_W in PAPER_LAMBDA_W.items():
        beta_pred, extrapolated = beta_from_lambda_w(lambda_W)
        predictions.append({
            'region': region,
            'lambda_W': lambda_W,
            'beta_pred': beta_pred,
            'extrapolated': extrapolated,
        })

        status = "EXTRAPOLATED" if extrapolated else "interpolated"
        print(f"  {region:<12} λ/W = {lambda_W:.2f} → β = {beta_pred:.2f} ({status})")

    print()

    # Step 2: Create literature search template
    print("STEP 2: Create literature search template")
    print("-"*70)

    template_file = f"{OUTPUT_BASE}/literature_beta_template.json"
    with open(template_file, 'w') as f:
        json.dump(LITERATURE_BETA_TEMPLATE, f, indent=2)

    print(f"  Template saved: {template_file}")
    print()

    # Step 3: Create comparison analysis script
    print("STEP 3: Create comparison analysis script")
    print("-"*70)

    analysis_script = f"{OUTPUT_BASE}/analyze_beta_comparison.py"
    with open(analysis_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""')
        f.write(f'Beta Comparison Analysis Script')
        f.write(f'Generated: {datetime.now().isoformat()}\n')
        f.write('"""\n\n')
        f.write('import json\n')
        f.write('import numpy as np\n')
        f.write('import matplotlib.pyplot as plt\n\n')
        f.write('# Campaign 7 calibration\n')
        f.write('CAMPAIGN_7_CALIBRATION = {\n')
        for beta, lambda_W in CAMPAIGN_7_CALIBRATION.items():
            f.write(f'    {beta}: {lambda_W},\n')
        f.write('}\n\n')
        f.write('def beta_from_lambda_w(lambda_W):\n')
        f.write('    """Convert λ/W to β using Campaign 7 calibration."""\n')
        f.write('    beta_values = np.array(list(CAMPAIGN_7_CALIBRATION.keys()))\n')
        f.write('    lambda_W_values = np.array(list(CAMPAIGN_7_CALIBRATION.values()))\n')
        f.write('    return np.interp(lambda_W, lambda_W_values, beta_values)\n\n')
        f.write('def main():\n')
        f.write(f'    # Load literature beta measurements\n')
        f.write(f'    template_file = "{template_file}"\n')
        f.write(f'    # TODO: Fill in literature measurements before running\n')
        f.write('    with open(template_file) as f:\n')
        f.write('        lit_data = json.load(f)\n')
        f.write('    \n')
        f.write('    # Paper λ/W measurements\n')
        f.write('    paper_lambda_W = {\n')
        for region, lambda_W in PAPER_LAMBDA_W.items():
            f.write(f'        "{region}": {lambda_W},\n')
        f.write('    }\n')
        f.write('    \n')
        f.write('    # Generate predictions\n')
        f.write('    results = []\n')
        f.write('    for region, lambda_W in paper_lambda_W.items():\n')
        f.write('        beta_pred = beta_from_lambda_w(lambda_W)\n')
        f.write('        results.append({\n')
        f.write('            "region": region,\n')
        f.write('            "lambda_W": lambda_W,\n')
        f.write('            "beta_pred": beta_pred,\n')
        f.write('        })\n')
        f.write('    \n')
        f.write('    # Compare with literature measurements\n')
        f.write('    print("BETA COMPARISON TABLE")\n')
        f.write('    print("="*70)\n')
        f.write('    print(f\'{"Region":<12} {"λ/W":<8} {"β_pred":<10} {"β_lit":<10} {"Δβ":<10} {"Method":<20}\')\n')
        f.write('    print("-"*70)\n')
        f.write('    \n')
        f.write('    for region in lit_data.keys():\n')
        f.write('        # Find prediction\n')
        f.write('        pred = next((r for r in results if r["region"] == region), None)\n')
        f.write('        if not pred:\n')
        f.write('            continue\n')
        f.write('        \n')
        f.write('        # Get literature measurements\n')
        f.write('        for meas in lit_data[region]["measurements"]:\n')
        f.write('            if meas["beta"] is None:\n')
        f.write('                continue  # Skip unfilled entries\n')
        f.write('            \n')
        f.write('            beta_lit = meas["beta"]\n')
        f.write('            delta_beta = pred["beta_pred"] - beta_lit\n')
        f.write('            \n')
        f.write(f'            print(f\'{region:<12} {pred["lambda_W"]:<8.2f} {pred["beta_pred"]:<10.2f} {beta_lit:<10.2f} {delta_beta:<10.2f} {meas["method"]:<20}\')\n')
        f.write('    \n')
        f.write('    # Statistical analysis\n')
        f.write('    deltas = []\n')
        f.write('    for region in lit_data.keys():\n')
        f.write('        pred = next((r for r in results if r["region"] == region), None)\n')
        f.write('        if not pred:\n')
        f.write('            continue\n')
        f.write('        for meas in lit_data[region]["measurements"]:\n')
        f.write('            if meas["beta"] is not None:\n')
        f.write('                deltas.append(pred["beta_pred"] - meas["beta"])\n')
        f.write('    \n')
        f.write('    if deltas:\n')
        f.write('        print()\n')
        f.write('        print("STATISTICAL SUMMARY")\n')
        f.write('        print("-"*70)\n')
        f.write('        print(f"Mean |Δβ|: {np.mean(np.abs(deltas)):.2f}")\n')
        f.write('        print(f"Std |Δβ|: {np.std(deltas):.2f}")\n')
        f.write('        print(f"Within 0.5: {sum(1 for d in deltas if abs(d) < 0.5)}/{len(deltas)} regions")\n')
        f.write('    \n')
        f.write('    # Create scatter plot\n')
        f.write('    beta_preds = []\n')
        f.write('    beta_lits = []\n')
        f.write('    region_names = []\n')
        f.write('    \n')
        f.write('    for region in lit_data.keys():\n')
        f.write('        pred = next((r for r in results if r["region"] == region), None)\n')
        f.write('        if not pred:\n')
        f.write('            continue\n')
        f.write('        for meas in lit_data[region]["measurements"]:\n')
        f.write('            if meas["beta"] is not None:\n')
        f.write('                beta_preds.append(pred["beta_pred"])\n')
        f.write('                beta_lits.append(meas["beta"])\n')
        f.write('                region_names.append(region)\n')
        f.write('    \n')
        f.write('    if beta_preds:\n')
        f.write('        fig, ax = plt.subplots(figsize=(8, 8))\n')
        f.write('        \n')
        f.write('        # Plot 1:1 line\n')
        f.write('        beta_min = min(min(beta_preds), min(beta_lits))\n')
        f.write('        beta_max = max(max(beta_preds), max(beta_lits))\n')
        f.write('        ax.plot([beta_min, beta_max], [beta_min, beta_max], \'k--\', alpha=0.3, label="1:1")\n')
        f.write('        \n')
        f.write('        # Plot points\n')
        f.write('        for i, region in enumerate(region_names):\n')
        f.write('            ax.scatter(beta_preds[i], beta_lits[i], s=100, label=region)\n')
        f.write('        \n')
        f.write('        ax.set_xlabel("β from λ/W (Campaign 7)")\n')
        f.write('        ax.set_ylabel("β from literature")\n')
        f.write('        ax.set_title("β Validation: λ/W vs Independent Measurements")\n')
        f.write('        ax.legend()\n')
        f.write('        ax.grid(True, alpha=0.3)\n')
        f.write('        \n')
        f.write(f'        plt.savefig("{OUTPUT_BASE}/beta_comparison.pdf")\n')
        f.write(f'        print(f"\\nFigure saved: {OUTPUT_BASE}/beta_comparison.pdf")\n')
        f.write('    \n')
        f.write('if __name__ == "__main__":\n')
        f.write('    main()\n')

    os.chmod(analysis_script, 0o755)
    print(f"  Analysis script: {analysis_script}")
    print()

    # Step 4: Create literature search guide
    print("STEP 4: Create literature search guide")
    print("-"*70)

    guide_file = f"{OUTPUT_BASE}/LITERATURE_SEARCH_GUIDE.md"
    with open(guide_file, 'w') as f:
        f.write('# Literature β Measurement Search Guide\n\n')
        f.write('## Objective\n\n')
        f.write('Compile independent magnetic field strength measurements for HGBS regions\n')
        f.write('to validate β constraints derived from λ/W using Campaign 7 calibration.\n\n')
        f.write('## Methods to Search\n\n')
        f.write('1. **Zeeman Effect**\n')
        f.write('   - Tracers: OH, HI, CI\n')
        f.write('   - Direct measurement of line-of-sight B field\n')
        f.write('   - Key papers: Crutcher 2012, 2019 reviews\n\n')
        f.write('2. **Dust Polarimetry**\n')
        f.write('   - Tracers: Thermal dust emission\n')
        f.write('   - Plane-of-sky B field orientation\n')
        f.write('   - Key papers: Planck 2016, HGBS papers\n\n')
        f.write('3. **Goldreich-Kylafis Effect**\n')
        f.write('   - Tracers: CO lines\n')
        f.write('   - B field orientation\n\n')
        f.write('4. **Chandrasekhar-Fermi Method**\n')
        f.write('   - Combines polarimetry with turbulence\n')
        f.write('   - B field strength estimate\n\n')
        f.write('## Regions to Search\n\n')
        for region in HGBS_REGIONS:
            f.write(f'- **{region}**\n')
        f.write('\n')
        f.write('## Expected β Values from λ/W (Campaign 7 calibration)\n\n')
        f.write('| Region | λ/W | β_pred |\n')
        f.write('|--------|-----|--------|\n')
        for pred in predictions:
            region = pred['region']
            lambda_W = pred['lambda_W']
            beta_pred = pred['beta_pred']
            f.write(f'| {region} | {lambda_W:.2f} | {beta_pred:.2f} |\n')
        f.write('\n')
        f.write('## Steps\n\n')
        f.write('1. Search ADS/arXiv for each region + method\n')
        f.write('2. Fill in template.json with measurements\n')
        f.write('3. Run analysis script to generate comparison\n')
        f.write('4. Assess consistency: |Δβ| < 0.5?\n\n')
        f.write('## Key References\n\n')
        f.write('- Crutcher et al. 2010, 2012: Zeeman reviews\n')
        f.write('- Planck Collaboration 2016: Polarimetry\n')
        f.write('- HGBS survey papers: Region-specific analyses\n\n')

    print(f"  Guide saved: {guide_file}")
    print()

    # Save specification
    spec_file = f"{OUTPUT_BASE}/campaign_specification.json"
    spec_data = {
        "campaign_id": CAMPAIGN_ID,
        "campaign_name": CAMPAIGN_NAME,
        "date": datetime.now().isoformat(),
        "objective": "Validate λ/W-derived β against independent measurements",
        "n_simulations": 0,  # Research campaign
        "campaign_type": "literature_review",
        "campaign_7_calibration": CAMPAIGN_7_CALIBRATION,
        "paper_lambda_W": PAPER_LAMBDA_W,
        "predictions": predictions,
    }

    with open(spec_file, 'w') as f:
        json.dump(spec_data, f, indent=2)

    print(f"Specification saved: {spec_file}")
    print()

    print("="*70)
    print("CAMPAIGN 13 SPECIFICATION COMPLETE")
    print("="*70)
    print()
    print(f"Files created:")
    print(f"  - {spec_file}")
    print(f"  - {template_file}")
    print(f"  - {analysis_script}")
    print(f"  - {guide_file}")
    print()
    print("Next steps:")
    print("1. Conduct literature search for β measurements")
    print("2. Fill in literature_beta_template.json")
    print("3. Run analysis: python analyze_beta_comparison.py")
    print("4. Assess consistency: |Δβ| < 0.5?")
    print()

if __name__ == "__main__":
    main()
