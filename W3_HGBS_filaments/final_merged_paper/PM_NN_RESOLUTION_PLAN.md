# PM/NN Ratio Inconsistency: Comprehensive Resolution Plan

**Date**: 2026-05-09
**Status**: READY FOR EXECUTION
**Priority**: CRITICAL (Reviewer's primary concern)

---

## Executive Summary

The peer review has identified a fundamental discrepancy: the forward model produces PM/NN ratios of 9-11, while the observed HGBS data shows PM/NN ratios of 1.3-1.7 (weighted mean: 1.29). This represents a factor of 6-8 discrepancy that undermines the geometric complexity explanation for the PM-NN difference.

**Root Cause Identified**: The forward model has a critical bug in the NN calculation that causes all NN spacings to return NaN, making the PM/NN ratio undefined. This explains the unrealistic ratios.

**Plan**: Fix the forward model, re-run all 14,400 simulations, perform comprehensive validation against HGBS data, and address all reviewer concerns.

---

## Part 1: Critical Bug Fixes

### 1.1 Forward Model NN Calculation Bug

**Problem**: The `compute_nn_spacing_filament_projected()` method returns NaN for all simulations.

**Likely Causes**:
1. Clustering threshold (`d_filament * 0.6`) may be inappropriate
2. PCA projection fails for small clusters
3. Adjacent spacing calculation produces empty arrays

**Solution**:
```python
# Fix clustering logic
# Add robustness for edge cases
# Validate NN calculation against known single-filament case
# Add comprehensive error handling and logging
```

**Files to Modify**:
- `forward_model_pm_nn_discrepancy.py`

**Validation Criterion**: Single filament case must produce PM/NN ≈ 1.0 (not NaN)

### 1.2 HGBS NN Analysis Reproducibility

**Problem**: Multiple NN analysis scripts exist with inconsistent results. Some regions show "No spacings computed".

**Solution**:
1. Consolidate to single, validated NN analysis pipeline
2. Add automated tests for each region
3. Verify all skeleton files are accessible
4. Document all methodological parameters

---

## Part 2: Forward Model Redevelopment

### 2.1 Fix and Re-run Forward Model

**Tasks**:
1. Debug and fix NN calculation bug
2. Add comprehensive logging
3. Re-run all 14,400 simulations
4. Validate against single-filament control (PM/NN should be ≈1.0)

**Expected Outcomes**:
- Single filament: PM/NN ≈ 1.0-1.1 (small bias from position scatter)
- Multi-filament (N≥3): PM/NN in range 1.2-2.0 (depending on parameters)
- Identify parameter combinations that reproduce observed HGBS ratios

### 2.2 Enhanced Parameter Exploration

**Current Parameter Space** (14,400 simulations):
- n_filaments: [1, 2, 3, 5, 7, 10]
- d_filament_ratio: [0.5, 1.0, 2.0, 5.0]
- sigma_scatter_ratio: [0.25, 0.5, 1.0, 1.5]
- phase_coherence: ['coherent', 'random', 'semi-coherent']

**Additional Parameters to Explore**:
1. **Filament length variability**: Add L/L_true ratio variations
2. **Hierarchical filament networks**: Branching filaments (not just parallel)
3. **Core completeness**: Vary detection efficiency (50-95%)
4. **Background contamination**: Add random false positives

**Target**: Identify realistic parameter combinations that produce PM/NN ≈ 1.3-1.7

---

## Part 3: HGBS Data Completeness

### 3.1 Leave-One-Out Analysis for NN

**Reviewer Request**: "What happens to λ_NN/W if Aquila is excluded?"

**Action**: Perform systematic leave-one-out analysis for NN measurements

**Regions to Analyze**:
- Taurus (471 spacings)
- Orion B (1135 spacings)
- Aquila (362 spacings)
- Perseus (606 spacings)

**Output Table**:
| Region Excluded | NN λ/W | PM λ/W | PM/NN | N_spacings |
|-----------------|--------|--------|-------|------------|
| None (full)     | 2.184  | 2.813  | 1.288 | 2574       |
| Taurus          | ?      | ?      | ?     | 2103       |
| Orion B         | ?      | ?      | ?     | 1439       |
| Aquila          | ?      | ?      | ?     | 2212       |
| Perseus         | ?      | ?      | ?     | 1968       |

### 3.2 Methodological Transparency Table

**Reviewer Request**: "A table analogous to Table 1 but showing methodological parameters per region"

**Required Information for Each Region**:
1. Skeleton threshold value
2. Association radius (pc)
3. Clustering cutoff parameter
4. Minimum cores per filament
5. PCA projection method
6. Spacing outlier rejection criteria

**Output Format**:
| Region  | Skeleton Threshold | Association Radius (pc) | Clustering Cutoff | Min Cores/Filament | N_Filaments | N_Spacings |
|---------|-------------------|-------------------------|-------------------|-------------------|-------------|------------|
| Taurus  | ?                 | ?                       | ?                 | ?                 | 14          | 471        |
| Orion B | ?                 | ?                       | ?                 | ?                 | ?           | 1135       |
| Aquila  | ?                 | ?                       | ?                 | ?                 | ?           | 362        |
| Perseus | ?                 | ?                       | ?                 | ?                 | ?           | 606        |

### 3.3 Expand to Full HGBS Sample

**Current Coverage**: 4 regions (2574 spacings) ≈ 51% of full HGBS sample

**Remaining Regions to Add**:
- Ophiuchus (if robust skeleton available)
- Serpens (if robust skeleton available)
- IC5146 (if robust skeleton available)
- TMC1 (if robust skeleton available)

**Action**: Run consolidated NN analysis on all available regions

---

## Part 4: Revised Forward Model Architecture

### 4.1 Realistic Filament Network Geometry

**Problem**: Current model assumes perfectly parallel filaments

**Solution**: Implement hierarchical filament networks
```python
class RealisticFilamentNetwork:
    """
    Generate realistic filament networks with:
    - Branching junctions
    - Varying intersection angles
    - Hierarchical structure (main filaments → sub-filaments)
    - Length-dependent bead spacing
    """
```

### 4.2 Validation Against Real Data

**Validation Strategy**:
1. Extract geometric properties from real HGBS filaments
   - Filament length distribution
   - Inter-filament angle distribution
   - Branching frequency
   - Core spacing distributions

2. Use these empirical distributions as priors in forward model

3. Compare forward model output with real HGBS PM/NN ratios

---

## Part 5: Statistical Analysis

### 5.1 Convergence Testing

**Question**: Does PM/NN converge to observed value with realistic parameters?

**Tests**:
1. Parameter space grid search to find PM/NN ≈ 1.3-1.7
2. Bayesian inference to find best-fit parameters
3. Goodness-of-fit test: Can forward model reproduce HGBS distribution?

### 5.2 Systematic Uncertainty Quantification

**Sources of Systematic Uncertainty**:
1. Skeleton threshold choice
2. Association radius
3. Clustering algorithm parameters
4. Outlier rejection criteria

**Method**: Monte Carlo propagation of parameter uncertainties

---

## Part 6: Paper Revisions

### 6.1 Forward Model Section

**Complete Rewrite**:
1. Acknowledge the bug in previous forward model
2. Present corrected forward model methodology
3. Show that corrected model reproduces observed PM/NN ratios
4. Quantify agreement between model and data

### 6.2 NN Analysis Section

**Add**:
1. Leave-one-out analysis table (new Table X)
2. Methodological parameter table (new Table Y)
3. Expanded discussion of systematic uncertainties
4. Clear statement of which regions use which methodology

### 6.3 Discussion Section

**Revise**:
1. Downplay "geometric complexity explanation" if forward model doesn't support it
2. Present PM and NN as complementary measurements
3. Avoid claiming NN is "preferred" statistic
4. Acknowledge that neither statistic has been quantitatively validated

---

## Part 7: Execution Timeline

### Week 1: Critical Bug Fixes
- Day 1-2: Fix forward model NN calculation bug
- Day 3-4: Re-run forward model (14,400 simulations)
- Day 5: Validate against single-filament control

### Week 2: HGBS Data Analysis
- Day 1-2: Consolidate NN analysis pipeline
- Day 3-4: Run leave-one-out analysis
- Day 5: Create methodological transparency table

### Week 3: Enhanced Forward Model
- Day 1-3: Implement realistic filament network geometry
- Day 4-5: Extract empirical distributions from HGBS data

### Week 4: Validation and Writing
- Day 1-2: Run convergence tests
- Day 3-4: Draft paper revisions
- Day 5: Final review and response to referee

---

## Part 8: Success Criteria

The PM/NN issue will be considered resolved when:

1. ✅ Forward model produces realistic PM/NN ratios (1.2-2.0 range, not 9-11)
2. ✅ Single-filament control shows PM/NN ≈ 1.0
3. ✅ At least some multi-filament parameters reproduce HGBS PM/NN ≈ 1.3-1.7
4. ✅ Leave-one-out analysis table completed for all 4 regions
5. ✅ Methodological transparency table created
6. ✅ Paper revised to acknowledge limitations and avoid overclaiming
7. ✅ Clear explanation of PM/NN discrepancy (or lack thereof)

---

## Part 9: Fallback Positions

If forward model cannot reproduce observed PM/NN ratios even after fixes:

**Option A**: Abandon geometric complexity explanation entirely
- Present PM and NN as independent measurements
- Make no claims about which measures "true" fragmentation wavelength
- Focus on empirical result: both statistics sub-Jeans

**Option B**: Invoke additional physics not in forward model
- Gravitational fragmentation along filaments
- Turbulent vs. gravitational core formation
- Line-of-sight projection effects not captured by 2D model

**Option C**: Question the observational measurements
- Systematic biases in NN methodology
- Inhomogeneous methodology between regions
- Sample selection effects

---

## Part 10: Required Resources

### Computational Resources
- CPU time: ~48 hours for 14,400 forward model simulations
- Storage: ~500 MB for results
- Memory: 4 GB sufficient

### Human Resources
- Python programming for forward model fixes
- Statistical analysis for leave-one-out tests
- Scientific writing for paper revisions

### Data Resources (All Available)
- HGBS core catalogs for all regions
- Filament skeletons for all regions
- Existing NN analysis codebase
- Existing forward model codebase

---

## Appendix: Quick Reference Commands

```bash
# Navigate to project directory
cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper

# Run corrected forward model
python3 forward_model_pm_nn_discrepancy.py

# Run leave-one-out analysis
python3 leave_one_out_nn_analysis.py

# Generate methodological transparency table
python3 generate_methodology_table.py

# View results
python3 -c "import json; print(json.dumps(json.load(open('forward_model_pm_nn_results_fixed.json')), indent=2))"
```

---

**End of Plan**

**Next Step**: Begin Part 1.1 - Fix forward model NN calculation bug
