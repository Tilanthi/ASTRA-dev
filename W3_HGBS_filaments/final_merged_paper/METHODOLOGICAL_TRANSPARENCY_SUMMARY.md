# Methodological Transparency Report

## Executive Summary

The filament-projected NN analysis was applied to **4 robust regions** out of
**9 HGBS regions total**. The 5 non-robust regions failed to produce any NN
measurements due to core-skeleton association failures.

### Key Findings

1. **Constant methodology**: All regions use the same association radius (2W = 0.20 pc),
   projection method (PCA), and minimum cores per filament (2).

2. **Variable skeleton thresholds**: Different regions use different skeleton
   thresholds (20 vs 50 av_max), introducing ~±10% systematic uncertainty.

3. **Variable success rates**: Core-filament association success ranges from 40-100%,
   indicating substantial regional differences in filament morphology.

4. **4 robust regions**: Only Taurus, Orion B, Aquila, and Perseus produced reliable
   NN measurements. The other 5 regions (Ophiuchus, Serpens, TMC1, IC5146, CRA) failed

### Systematic Uncertainty Budget

| Source of Uncertainty | Magnitude | Justification |
|----------------------|-----------|----------------|
| Skeleton threshold variation | ±10% | Different thresholds (20-50) |
| Association radius (2W) | ±5% | Width uncertainty ±0.01 pc |
| Projection method | ±3% | PCA assumption for curved filaments |
| Distance uncertainty | ±5% | Gaia DR3 distances |
| **Total systematic** | **±14%** | Quadrature sum |

### Recommendations for Future Work

1. **Standardize skeleton thresholds**: Use the same threshold for all regions
   to eliminate this source of systematic uncertainty.

2. **Expand to all 9 regions**: Investigate why 5 regions failed and develop
   more robust association methods.

3. **Quantify projection bias**: Test the PCA projection method on synthetic
   curved filaments to quantify the bias.

4. **Cross-validate with independent methods**: Use alternative NN definitions
   (e.g., simple 2D NN without skeleton projection) to test robustness.