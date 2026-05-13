# CTZM_PERP Campaign — Perpendicular-Field Transition Zone Mapping

**Date**: 2026-05-13
**Objective**: Test whether smooth λ/W evolution across f=1.2-1.5 is geometry-independent
**Field Geometry**: PERPENDICULAR (θ=90°) — matches HGBS filament orientation

## Campaign Summary

- **Total sims**: 96
- **Parameter space**: f=[1.2,1.3,1.4,1.5] × β=[0.3,0.5,1.0,2.0] × M=[1.0,2.0] × seeds=[0,1,2]
- **Domain**: 256×64×64, L=8λ_J
- **B-field**: Perpendicular to filament axis (θ=90°)
- **HDF5**: dt=0.02 tJ with inline λ/W analysis
- **Expected wall time**: ~12 hours (96 sims × ~7.5 min each)

## Science Motivation

The longitudinal CTZM campaign (May 2026) demonstrated:
1. 100% beading across f=1.2-1.5 (0% radial collapse)
2. Smooth λ/W evolution (R² > 0.92 for β=0.3, 0.5, 1.0)
3. No discontinuity at proposed f~1.35 breakpoint

**Open question**: Is smooth evolution a general feature of filament fragmentation, or specific to longitudinal field geometry?

## Expected Outcomes

### If smooth evolution is geometry-independent:
- Perpendicular-field sims will also show continuous λ/W(f) with high R²
- Strengthens extrapolation argument for HGBS filaments (which are predominantly perpendicular to B-field)
- Can claim: "Smooth evolution is robust across field geometries"

### If geometry-dependent:
- Perpendicular fields may show discontinuous evolution or early onset of radial collapse
- Would reveal fundamental difference in fragmentation physics
- Requires geometry-specific theoretical models

## File Structure

```
ctzm_perp_may2026/
├── README.md                    # This file
├── ctzm_perp_runner.py          # Campaign runner (96 sims)
└── [results will be added after campaign completion]
    ├── ctzm_perp_results.json   # Full per-sim results
    ├── ctzm_perp_summary.json   # Aggregated statistics
    └── figures/                  # Analysis plots
```

## Running the Campaign

```bash
# On astra-climate (220 vCPU)
cd /data/ctzm_perp_runs
python3 /path/to/ctzm_perp_runner.py
```

## Key Differences from Longitudinal CTZM

| Parameter | Longitudinal CTZM | Perpendicular CTZM |
|-----------|-------------------|-------------------|
| B-field geometry | θ=0° | θ=90° |
| HGBS relevance | ~10% of filaments | ~90% of filaments |
| Magnetic suppression | Radial collapse via flux-freezing | Transverse compression |
| Expected behavior | Smooth λ/W(f) shown | UNKNOWN — this test |

## Deliverables

1. **ctzm_perp_results.json**: Full per-sim results with λ/W measurements
2. **ctzm_perp_summary.json**: Aggregated statistics and smooth-test results
3. **Figure**: λ/W vs f for different β (comparison with longitudinal CTZM)
4. **Final report**: Geometry-dependence assessment

## Integration with Paper

If perpendicular-field CTZM confirms smooth evolution:
- Add statement to Section 3.2.1: "The smooth evolution of λ/W across the critical transition zone is geometry-independent, holding for both longitudinal and perpendicular field configurations."
- Strengthens extrapolation validation significantly
- Addresses referee concern about perpendicular-field extrapolation directly

## Contact

Campaign designed by: Claude (ASTRA System)
Date: 2026-05-13
Referee context: Resolves extrapolation uncertainty for HGBS filament geometry
