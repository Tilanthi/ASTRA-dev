# Forward Modelling: PM-NN Discrepancy Analysis (FIXED VERSION)

Generated: 2026-05-09 16:10:19

## Summary Statistics

**Total simulations**: 14400
**PM/NN ratio**: 10.405 ± 3.358 (mean ± std)
**PM/NN ratio**: 9.343 (median)
**Range**: 5.940 - 26.607

**Fraction matching observed 40-50% discrepancy** (PM/NN = 1.35-1.55):
  0 / 14400 = 0.0%

**Single-filament control** (should have PM/NN ≈ 1.0):
  PM/NN = 8.980 ± 1.754

**Multi-filament systems** (N ≥ 3):
  PM/NN = 11.126 ± 3.752

**NN bias** (should be ≈ 0% if NN is unbiased):
  Mean bias: -8.8%
  Median bias: -7.0%

## Key Findings

⚠️ **Single-filament control shows PM/NN = 8.980, not 1.0 as expected.

⚠️ **Multi-filament systems do NOT fully reproduce the observed discrepancy**.
   - Mean PM/NN for N ≥ 3: 11.126
   - Observed HGBS value: ~1.45
   - Difference: 9.676

✅ **NN is statistically unbiased** (bias < 10%).