# Nearest-Neighbor (NN) Analysis Status
**Date**: 2026-05-01

## Summary

The paper has been updated with L-dependent bias correction results from Campaign 10. The corrected NN spacing is an order of magnitude smaller than classical theory predicts.

## Key Results

### Original Paper (Biased)
- **Statistic**: Pairwise median
- **Robust regions**: λ/W = 2.84 ± 0.12
- **Interpretation**: Sub-Jeans spacing (30% below classical λ/W ≈ 4)

### L-Dependent Bias Correction
- **Method**: Campaign 10 periodic beading tests with L-dependent bias factors
  - L = 5 pc → bias = 4.0×
  - L = 8.5 pc → bias = 7.93×
  - L = 12 pc → bias = 11.01×
- **Corrected NN spacing**: λ/W = 0.30 ± 0.03
- **Interpretation**: Order of magnitude smaller than classical theory

### Alternative: Single 7.0× Bias Factor
- **Method**: Campaign 10 mean bias (ignoring L-dependence)
- **Corrected NN spacing**: λ/W = 0.41 ± 0.04
- **Interpretation**: Still far from classical theory

## Two Possible Interpretations

### Interpretation 1: Finer Fragmentation
Real HGBS filaments fragment much more finely than classical idealized theory predicts.
- Classical theory assumes isolated, uniform filaments
- Real filaments are hierarchical, turbulent, and complex
- The true fragmentation spacing may be ~10× smaller than λ ≈ 4W

### Interpretation 2: Bias Correction Inapplicable
The L/3 bias correction derived from periodic beading test cases does not apply to complex hierarchical filaments.
- Campaign 10 tested idealized patterns (periodic beading, uniform, random)
- Real HGBS filaments have hierarchical structure (fiber bundles)
- The bias factor for hierarchical structures may be much smaller

## What Would Resolve This Uncertainty?

### Full NN Analysis from Raw HGBS Data
Compute nearest-neighbor spacing directly from raw HGBS skeleton maps and core catalogs for all 8 regions:

**Required data**:
- HGBS skeleton maps (FITS files)
- HGBS core catalogs with positions

**Analysis steps**:
1. Extract filament skeletons from each region
2. Associate cores with filaments
3. Compute position of each core along filament
4. Calculate NN (adjacent-core) spacing along filaments
5. Compute median and uncertainty for each region
6. Combine results with appropriate weighting

**Why this is definitive**:
- No bias correction needed (direct measurement)
- Accounts for actual filament geometry
- Resolves the uncertainty between the two interpretations

### Current Status
- **Taurus NN analysis**: λ/W = 2.17 ± 0.52 (one region only)
- **Attempted full NN analysis**: Failed due to catalog file encoding issues
- **Bias correction approach**: Uncertain due to L-dependence and applicability to hierarchical filaments

## Paper Updates Made

### Abstract
- Added L-dependent bias factor range (4.0× to 11.0×)
- Updated corrected NN spacing to 0.030 ± 0.003 pc (λ/W = 0.30 ± 0.03)
- Acknowledged uncertainty: correction may not apply to complex filaments

### Executive Summary
- Updated with L-dependent bias correction
- Clarified two possible interpretations
- Emphasized need for full NN analysis

### Campaign 10 Section
- Updated to discuss L-dependent bias factors
- Added interpretation uncertainty
- Removed claim that correction "recovers classical theory"

## Recommendation

The paper should present three values:
1. **Published pairwise median**: λ/W = 2.84 (biased, for comparison with literature)
2. **L-dependent bias correction**: λ/W = 0.30 (uncertain interpretation)
3. **Taurus NN direct measurement**: λ/W = 2.17 ± 0.52 (single region, large uncertainty)

And acknowledge that:
- The true fragmentation spacing is uncertain
- Bias correction may not apply to hierarchical filaments
- Full NN analysis from raw HGBS data is required for definitive results

## Files Updated

- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/filament_spacing_streamlined_mnras.tex`
- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/filament_spacing_streamlined_mnras.pdf`

## Analysis Scripts Created

- `compute_corrected_nn_spacing.py`: Uses 7.0× mean bias factor
- `compute_ldependent_nn_spacing.py`: Uses L-dependent bias factors (preferred)
- `compute_full_nn_analysis.py`: Attempts full NN analysis from raw data (incomplete)

## Results Files

- `corrected_nn_spacing_results.json`: Results from 7.0× bias correction
- `ldependent_nn_spacing_results.json`: Results from L-dependent bias correction
