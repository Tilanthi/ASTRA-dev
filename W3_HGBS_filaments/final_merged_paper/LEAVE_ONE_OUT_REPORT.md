# Leave-One-Out Analysis: NN Measurements

**Analysis Date**: 2026-05-09

## Executive Summary

**Full Sample (4 regions):**
- NN λ/W: 2.184
- PM λ/W: 2.813
- PM/NN ratio: 1.288
- Total spacings: 2574

## Sensitivity Analysis

The analysis addresses the reviewer's question: *"What happens to λ_NN/W if Aquila is excluded?"*

When each region is systematically excluded:

### Excluding Taurus:
- NN λ/W changes from 2.184 → 2.285
  (Δ = +0.101, +4.6%)
- PM/NN changes from 1.288 → 1.313
  (Δ = +0.025, +1.9%)

### Excluding OrionB:
- NN λ/W changes from 2.184 → 2.372
  (Δ = +0.188, +8.6%)
- PM/NN changes from 1.288 → 1.080
  (Δ = -0.208, -16.1%)

### Excluding Aquila:
- NN λ/W changes from 2.184 → 2.206
  (Δ = +0.022, +1.0%)
- PM/NN changes from 1.288 → 1.227
  (Δ = -0.061, -4.7%)

### Excluding Perseus:
- NN λ/W changes from 2.184 → 1.914
  (Δ = -0.270, -12.4%)
- PM/NN changes from 1.288 → 1.524
  (Δ = +0.236, +18.3%)

## Key Findings

1. **Most influential region**: Perseus
   - Excluding Perseus changes PM/NN by 0.236

2. **Answering reviewer's specific question about Aquila**:
   - Excluding Aquila changes PM/NN from 1.288 → 1.227
   - ΔPM/NN = -0.061 (-4.7%)
   - Despite having only 362 spacings (14% of total), Aquila's exclusion has a moderate effect.

3. **Robustness assessment**:
   - Maximum change in PM/NN from excluding any single region: 0.236
   - The weighted mean shows **moderate sensitivity** to regional variations.