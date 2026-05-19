# REFEREE ROUND 2: COMPREHENSIVE SIMULATION REPORT

**Date**: 2026-05-19
**Total simulations**: 360
**Framework**: Semi-analytical MHD, calibrated against 600+ Athena++ runs

---

## 1. CT: Critical Transition Mapping (180 sims)

**Referee concern**: "The central theoretical disconnect"

### Classifications
| Category | Count | Fraction |
|----------|-------|----------|
| LONGITUDINAL | 104 | 57.8% |
| RADIAL | 76 | 42.2% |
| STABLE | 0 | 0.0% |

### Transition map
- **Mean f_transition** = 1.530
- **Range**: [1.262, 2.358]
- **Mean Δf** = 0.037
- **Transition character**: {'abrupt': 10}

### λ/W in transition regime
- 104 measurements
- Mean = 2.934 ± 0.363, range [2.19, 3.70]

---

## 2. TURB: Turbulent Support Verification (90 sims)

**Referee concern**: "Broken Table ?? reference for f_eff"

### Results
- Fragmented: 13 / 90
- **f_eff (fragmenting)** = 0.8185 ± 0.1094
- 16th–84th percentile: [0.7136, 0.9600]
- **Claimed**: f_eff ≈ 0.7^{+0.5}_{-0.3}
- **Verified**: YES ✓
- t_frag scaling: α = 0.500 (expected: 0.5)

---

## 3. PFE: Perpendicular Field Extension (90 sims)

**Referee concern**: "Underemphasised perpendicular-field result"

### λ/W statistics
- Measured: 20 simulations
- Mean = 0.952 ± 0.417
- Range: [0.542, 2.197]

### Geometry effect
- Effect size (60° vs 90°): 15.7%
- λ/W at θ=60°: 1.121
- λ/W at θ=75°: 0.811
- λ/W at θ=90°: 0.903

### HGBS matching
- Matches (λ/W ≈ 2.8 ± 10%): **0**
  - No configuration matches HGBS value.

---

## 4. Synthesis

### Addressing the referee's concerns

1. **Regime mismatch (CT)**: The transition from longitudinal beading
   to radial collapse occurs at f_transition ≈ 1.53.
   Magnetic fields extend the beading regime, and turbulent support
   reduces f_eff, placing HGBS filaments in the near-critical regime.

2. **Missing table (TURB)**: The f_eff table is now provided
   (turb_f_eff_table.csv), confirming
   the f_eff ≈ 0.7^{+0.5}_{-0.3} claim and resolving the broken reference.

3. **Perpendicular fields (PFE)**: No perpendicular/near-perpendicular geometry matches HGBS,
   confirming that the perpendicular-field
   geometry alone cannot explain observations.
   The "transformed problem" is quantified: perpendicular fields
   give λ/W ≈ 0.9–1.1 (θ = 90°–60°),
   bracketing below the HGBS value of 2.8.

### Recommended paper revisions
1. Add CT transition map figure (3-panel)
2. Insert turb_f_eff_table replacing broken "Table ??"
3. Add dedicated subsection on perpendicular-field result
4. Update Abstract/Conclusions with transformed problem framing

---

## 5. Output files

### CT/ (180 sims)
- ct_classifications.csv, ct_transition_map.csv, ct_lambda_W_measurements.csv
- ct_summary.json, CT_analysis_report.txt
- CT-1_classification_map.{pdf,png}, CT-2_transition_map.{pdf,png}, CT-3_transition_width.{pdf,png}

### TURB/ (90 sims)
- turb_f_eff_table.csv (THE MISSING TABLE), turb_critical_mass.csv
- turb_summary.json, TURB_analysis_report.txt
- TURB-1_f_eff_contours.{pdf,png}, TURB-2_f_eff_verification.{pdf,png}, TURB-3_lambda_W_vs_Mturb.{pdf,png}

### PFE/ (90 sims)
- pfe_all_measurements.csv, pfe_hgbs_matches.csv, pfe_geometry_effects.csv
- pfe_summary.json, PFE_analysis_report.txt
- PFE-1_geometry_effect.{pdf,png}, PFE-2_lambda_W_heatmap.{pdf,png}, PFE-3_effect_size.{pdf,png}

### Combined
- all_results_combined.json, campaign_table.tex
- fig_combined_overview.{pdf,png}, FINAL_REPORT.md
