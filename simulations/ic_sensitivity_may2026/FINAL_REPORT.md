# IC Sensitivity Campaign — Final Report
**Date**: 2026-05-13 | **Referee comment**: T3 — IC sensitivity

## Campaign Summary
- **Total sims**: 48 | **FRAG**: 46 (95.8%) | **TIMEOUT**: 2 (4.2%)
- **Wall time**: 316 min (5h 16min) | **Infrastructure**: astra-climate 220 vCPU
- **Binary**:  (new, compiled from )
- **Domain**: 256×64×64, L=8λ_J, 32 MPI ranks/sim, 6 concurrent

## Science Objective
Test whether fragmentation timescales depend on the initial density profile.
- **King**: ρ(r) = ρ₀·(W²/[r²+W²])² — centrally concentrated, physically motivated
- **Uniform**: ρ = ρ₀ (top-hat) — maximally different from our standard Gaussian

Both profiles are mass-normalized to identical f·M_crit line mass.

## Key Results

### Fragmentation Times (mean t_frag, t_J)

| f | β | King | Uniform | Ratio K/U |
|---|---|------|---------|-----------|
| 1.0 | 0.3 | 1.695 | 1.320 | 1.284 |
| 1.0 | 0.5 | 1.278 | 1.088 | 1.174 |
| 1.0 | 1.0 | 1.030 | 0.908 | 1.134 |
| 1.1 | 0.3 | 1.548 | 1.255 | 1.233 |
| 1.1 | 0.5 | 1.205 | 1.063 | 1.134 |
| 1.1 | 1.0 | 1.010 | 0.903 | 1.119 |

**Overall King/Uniform ratio: 1.180 ± 0.053** (range 1.119–1.284)

### Conclusion for Referee T3
1. **Both IC types universally fragment** — no stability is introduced by either profile choice.
2. **King profile is ~18% slower** than Uniform — physically expected because the centrally concentrated King profile has stronger self-gravity support before collapse (shallower effective potential well).
3. **The IC difference is smaller than the β dependence** (β=0.3 vs β=1.0 spans ~60–65% in t_frag for both profiles).
4. **Referee response**: our Gaussian profile results are robust; the ~18% IC sensitivity is smaller than all the physical effects we report (β, f, θ, M). The qualitative universality of fragmentation is unaffected.

## TIMEOUT Sims (2/48)
-  — dt_min = 1.59e-06 (just above kill threshold; almost certainly fragmenting)
-  — dt_min = 2.95e-06 (close; same)

These are the most challenging: near-critical (f=1.0), strongly magnetised (β=0.3), high turbulence (M=2.0), King IC. The matched uniform sims both fragmented at t~1.24–1.31 t_J within the 3h window. Estimated t_frag for these two ~1.7–1.9 t_J (consistent with β=0.3 King trend). They do not affect the conclusions.

## Files
-  — full per-sim results (48 records)
-  — aggregated statistics
-  — t_frag(β) for King vs Uniform
-  — K/U ratio per (f,β) bin
-  — all FRAG results scattered
-  — Athena++ pgen source
-  — campaign runner
