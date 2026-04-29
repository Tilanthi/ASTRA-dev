# Executive Summary: Compute Cluster Simulation Package

## Overview
This package contains simulation specifications designed to definitively resolve ALL critical gaps identified in peer review of the filament spacing paper.

## Critical Gaps Addressed

### 1. λ/W Measurements for Perpendicular-Field Configurations (PRIMARY GAP)
**Issue**: Paper claims perpendicular fields don't suppress fragmentation based on t_frag, but doesn't measure λ/W for perpendicular fields (~90% of HGBS filaments).

**Solution**: Campaign 1 - 96 simulations with extended runtime and dense snapshots to directly measure λ/W for θ = 90°.

**Expected Output**: λ/W values for perpendicular-field configurations, determining if they produce classical (~4.0) or modified (~2.8) wavelengths.

### 2. Multi-Fibre Bundle Simulations (MOST PROMISING EXPLANATION)
**Issue**: Hierarchical structure explanation (fiber-to-core spacing recovers classical prediction) was never tested with actual fiber bundle simulations.

**Solution**: Campaign 2 - 120 simulations of 2-8 fibre bundles measuring apparent spacing compression.

**Expected Output**: Compression factor vs. N_fibres, testing if √N_fibres model explains observed factor of 1.4 discrepancy.

### 3. Non-Ideal MHD Effects (SECONDARY PRIORITY)
**Issue**: Paper uses ideal MHD, but real filaments have ambipolar diffusion and Hall effect.

**Solution**: Campaign 3 - 80 simulations measuring dispersion relation in linear growth phase to determine λ_max with non-ideal effects.

**Expected Output**: λ vs. coupling strength, determining if non-ideal MHD moves predictions toward or away from observations.

### 4. Near-Critical Baseline Validation (VALIDATION PRIORITY)
**Issue**: Paper's theoretical predictions (λ/W ≈ 3.5-4.0) depend on extrapolation from limited near-critical data.

**Solution**: Campaign 4 - 90 simulations with λ/W measurements for f ≤ 1.2 at two resolutions.

**Expected Output**: Validated baseline λ/W calibration for field-geometry extrapolation.

## Execution Summary

### Computational Requirements
- **Minimum**: 64 cores, 500 GB storage, 1-2 weeks wall-clock
- **Recommended**: 128 cores, 1 TB storage, 1 month wall-clock (for all 4 campaigns)
- **Optimal**: 256 cores, 2 TB storage, 1 month wall-clock (all campaigns with validation)

### Timeline
- **Phase 1** (Weeks 1-2): Campaigns 1 + 4 → Critical baseline + primary gap
- **Phase 2** (Weeks 3-6): Campaign 2 → Conditional on Phase 1 results
- **Phase 3** (Weeks 7-10): Campaign 3 → Tertiary, if needed

### Deliverables
For each campaign:
1. λ/W measurements for all parameter combinations
2. Quality-assured dataset with flags
3. Summary statistics and comparison with observations
4. Reproducible analysis scripts

## Getting Started
See `README.md` for detailed instructions. Key steps:
1. Extract package: `tar -xzf compute_cluster_simulation_specs.tar.gz`
2. Configure cluster: Edit `cluster_config.yaml`
3. Install dependencies: `pip install -r requirements.txt`
4. Run test: `python run_single_simulation.py --campaign campaign1 --f 1.5 --beta 1.0`

## Success Criteria
Each campaign is successful if:
1. **Completion rate**: >70% of simulations achieve 'GOOD' quality flag
2. **Physical reasonableness**: λ/W values in physically plausible range (1-10)
3. **Clear trends**: Parameter dependencies are well-constrained (or absence of trend is established)
4. **Comparison with observations**: Definitive statement on agreement/disagreement with λ/W ≈ 2.8

## Priority Matrix

| Campaign | Priority | Compute Cost | Scientific Value | Run First? |
|----------|----------|--------------|------------------|-----------|
| 1: Perp λ/W | HIGHEST | Medium | HIGH | YES |
| 4: Near-crit | VALIDATION | Low | HIGH | YES |
| 2: Multi-fibre | SECONDARY | High | VERY HIGH | Conditional |
| 3: Non-ideal | TERTIARY | Very High | MEDIUM | Last |

## Bottom Line
This package provides **definitive tests** for all major peer review concerns. Campaigns 1 + 4 alone (1-2 weeks of compute time) will resolve the most critical issues:
- Perpendicular-field λ/W gap (PRIMARY concern)
- Baseline validation for theoretical extrapolations

Campaign 2 (multi-fibre) is the "most promising explanation" and should be run if Campaign 1 results warrant.

Campaign 3 (non-ideal MHD) is tertiary and only needed if other campaigns are inconclusive.

## For GitHub Deployment
Compress this entire directory and push to:
```
https://github.com/glenn/ASTRA-dev/blob/main/W3_HGBS_filaments/final_merged_paper/compute_cluster_simulation_specs.tar.gz
```

Full path after deployment will be provided for cluster download.

---

**Status**: READY FOR DEPLOYMENT  
**Last Updated**: 29 April 2026
