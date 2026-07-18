# TAURUS RT Post-Processing Results: Analysis Summary (2026-07-18)

## Survey: 519 runs across parameter grid (f, beta, T_isrf, kappa)

### Key results:
1. **Global M-T coupling captured**: median slope = -7.23 K/dex (r=-0.85),
   consistent with observed IC5146 (-1.82 to -9.57 K/dex).
2. **T_isrf controls slope steepness**: T_isrf=12 -> -6.1, 15 -> -7.6, 20 -> -10.2 K/dex.
   Directly confirms the radiation-field-driver hypothesis.
3. **ZERO spatial variation**: max F=0.08 (observed IC5146: 6.78).
   Uniform ISRF -> spatially uniform M-T slope.
4. **This matches the active-vs-quiescent differential**:
   - Uniform ISRF sim (all runs) -> uniform slope -> matches Taurus L1495 (F=1.26).
   - Observed IC5146/Orion A (F>5) -> requires varying ISRF.

### Conclusion:
The RT post-processing confirms that:
- The self-shielding physics is correct (global M-T slope reproduced).
- The ISRF strength controls the coupling strength (steeper for stronger ISRF).
- Spatial variation requires a SPATIALLY VARYING ISRF (not just any ISRF).
- The single-filament + uniform-ISRF paradigm captures local physics
  but cannot reproduce cloud-scale M-T variation.

### Next step:
Re-run RT with T_isrf(x,y,z) varying spatially (OB association model).
If F > 3 with varying ISRF: the radiation-field-driver hypothesis is
confirmed end-to-end (observations + simulations).
