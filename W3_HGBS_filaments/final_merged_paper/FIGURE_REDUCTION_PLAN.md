# Figure Reduction Plan - Option B Implementation

**Date**: 2026-06-06
**Status**: Ready for execution
**Goal**: Reduce from ~20 figures to ~12-15, emphasize RTC null result

---

## Current Figure Inventory

### 1. fig:spacing (Figure 1) - Observational Results
**Status**: KEEP (Core observational result)

**Figures**:
- `figure1_spacing_comparison.pdf` - ✅ KEEP (Main observational result)
- `fig1_pfrag_heatmaps.pdf` - ✅ KEEP (DTC main result)
- `fig1_dtc_stable_ridge_rerun.pdf` - ❌ REMOVE (Validation detail)
- `figR1_resolution_scatter.pdf` - 📦 MOVE TO APPENDIX (Validation)

**Rationale**: This is the primary observational comparison - must keep.

---

### 2. fig:resolution (Figure) - Validation
**Status**: MOVE TO APPENDIX

**Figures**:
- `figR1_resolution_scatter.pdf` - 📦 MOVE TO APPENDIX

**Rationale**: Standard validation test - not core science.

---

### 3. fig:ic_sensitivity (Figure) - Validation
**Status**: MOVE TO APPENDIX

**Figures**:
- `fig5_phase2_ic_sensitivity.pdf` - 📦 MOVE TO APPENDIX

**Rationale**: Shows no effect - can state in text.

---

### 4. fig:eos_sensitivity (Figure) - Validation
**Status**: MOVE TO APPENDIX

**Figures**:
- `fig6_phase3_eos_sensitivity.pdf` - 📦 MOVE TO APPENDIX

**Rationale**: Supporting validation - not central to main narrative.

---

### 5. fig:regime (Figure*) - Three-Regime Framework
**Status**: KEEP BUT SIMPLIFY

**Figures**:
- `fig_regime_diagram_mhd.pdf` - ✅ KEEP (Framework overview)
- `fig1_tfrag_combined.pdf` - ✅ KEEP (t_frag results)
- `fig2_tfrag_heatmap_combined.pdf` - ❌ REMOVE (Redundant)
- `fig4_mach_highbeta_extensions.pdf` - ❌ REMOVE (Shows no dependence)
- `fig5_nearcrit_tfrag.pdf` - 📦 MOVE TO APPENDIX (Supporting detail)
- `fig3_lambda_W_theory.pdf` - ✅ KEEP (Theory comparison)
- `fig1_beading_threshold_M1.pdf` - ❌ REMOVE (M2 sufficient)
- `fig1_beading_threshold_M2.pdf` - ✅ KEEP (Beading threshold)
- `fig2_lambda_W_comparison.pdf` - ✅ KEEP (Perpendicular vs longitudinal - KEY)
- `fig3_oblique_calibration.pdf` - ❌ REMOVE (Calibration detail)

**Rationale**: Keep framework and key comparisons, remove redundancy.

---

### 6. fig:adia_comparison (Figure*) - Adiabatic Campaign
**Status**: PARTIAL KEEP

**Figures**:
- `fig4_adia_comparison.pdf` - 📦 MOVE TO APPENDIX (Supporting)
- `fig5_adia_density_profiles.pdf` - 📦 MOVE TO APPENDIX (Supporting)
- `cross_campaign_lambdaW.pdf` - ✅ KEEP (RTC-related results, IMPORTANT)
- `RC_lW_summary.png` - ✅ KEEP (Rigid cylinder result)

**Rationale**: Keep cross-campaign comparison (shows RTC context) and rigid cylinder (boundary condition context). Move adiabatic details to appendix.

---

### 7. fig:dtc_pfrag (Figure*) - DTC Heatmaps
**Status**: KEEP (Main DTC result)

**Figures**:
- `fig1_pfrag_heatmaps.pdf` - ✅ KEEP (DTC main visualization)

**Note**: Already included in fig:spacing as multi-panel figure.

---

### 8. fig:dtc_rerun (Figure*) - DTC Re-run
**Status**: REMOVE (Already shown elsewhere)

**Figures**:
- `fig1_dtc_stable_ridge_rerun.pdf` - ❌ REMOVE

**Rationale**: Validation detail - already discussed in text.

---

## Summary of Actions

### Remove Entirely (5 figures):
1. `fig1_dtc_stable_ridge_rerun.pdf` - DTC re-run validation
2. `fig2_tfrag_heatmap_combined.pdf` - Redundant heatmap
3. `fig4_mach_highbeta_extensions.pdf` - Shows no dependence
4. `fig1_beading_threshold_M1.pdf` - M2 sufficient
5. `fig3_oblique_calibration.pdf` - Calibration detail

### Move to Appendix (4 figures):
1. `figR1_resolution_scatter.pdf` - Resolution convergence
2. `fig5_phase2_ic_sensitivity.pdf` - IC sensitivity
3. `fig6_phase3_eos_sensitivity.pdf` - EOS sensitivity
4. `fig5_nearcrit_tfrag.pdf` - Near-critical details
5. `fig4_adia_comparison.pdf` - Adiabatic comparison
6. `fig5_adia_density_profiles.pdf` - Adiabatic profiles

### Keep and Emphasize (10 figures):
1. `figure1_spacing_comparison.pdf` - Observational result (Fig 1)
2. `fig1_pfrag_heatmaps.pdf` - DTC main result
3. `fig_regime_diagram_mhd.pdf` - Framework
4. `fig1_tfrag_combined.pdf` - t_frag results
5. `fig3_lambda_W_theory.pdf` - Theory
6. `fig1_beading_threshold_M2.pdf` - Beading threshold
7. `fig2_lambda_W_comparison.pdf` - Perpendicular vs longitudinal (KEY - perpendicular-field crisis)
8. `cross_campaign_lambdaW.pdf` - Cross-campaign (RTC context)
9. `RC_lW_summary.png` - Rigid cylinder (boundary conditions)
10. Additional as needed for RTC prominence

---

## Expected Outcome

**Before**: ~20 figures across 5 figure environments
**After**: ~10-12 figures across 3-4 figure environments
**Page reduction**: ~2-3 pages (figures take significant space)
**Emphasis**: RTC result and perpendicular-field crisis now prominent

---

## Execution Order

1. Comment out figures to REMOVE
2. Remove references to removed figures from text
3. Move validation figures to appendix (create appendix if needed)
4. Recompile and verify page count
5. Check all figure references resolve correctly
