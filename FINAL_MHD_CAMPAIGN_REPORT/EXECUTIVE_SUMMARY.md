# EXECUTIVE SUMMARY
## ASTRA MHD Simulation Campaign — Filament Fragmentation

**Date:** 12 April 2026  
**PI:** Glenn J. White (Open University)

---

### The Question

Why do cores along ISM filaments have spacing λ/W = 2.1 when classical theory (IM92) predicts 4.0?

### What We Did

Three-phase Athena++ MHD simulation campaign (~85 hours on 16 cores):

| Phase | What | Result |
|-------|------|--------|
| **1. Turbulence** | Driven MHD at β=0.1, 1.0 | Turbulent dynamo at β=1 gives v_A/c_s ≈ 1.5–1.8 |
| **2. Supercritical filaments** | Self-gravity, μ/μ_crit=6.6 | λ/W ≈ 0.97, β-independent (gravity dominates) |
| **3. Near-critical filaments** | μ/μ_crit ≈ 1.2–1.7 | **FAILED** — CFL stiffness makes explicit MHD infeasible |

### The Answer

**Analytical magnetic tension model**, calibrated by Phase 1 turbulence sims:

> **λ_frag / W ≈ 2.2** (matches observed 2.1 to within 5%)

The mechanism: axial magnetic tension along the filament provides an extra restoring force that shortens the fragmentation wavelength. This requires β ~ 1 (equipartition) fields, consistent with ISM observations.

### Key Caveats

1. The prediction is **analytical**, not from direct simulation of the near-critical regime
2. Phase 2 simulations confirm fragmentation physics but were in the wrong regime (μ/μ_crit=6.6)
3. Direct numerical confirmation requires **implicit MHD + AMR + HPC**

### For the Paper

- **Claim:** Magnetic tension model predicts λ/W ≈ 2.2, matching observations
- **Claim:** Isotropic B-pressure model ruled out (predicts 7–8×, makes it worse)
- **Don't claim:** Simulations reproduce 2.1× spacing (they don't — supercritical regime gives ~1×)
- **Do note:** Near-critical regime is a defined HPC project for future work

### Files

- Full report: `FINAL_REPORT.md`
- Figures: `figures/fig1–fig5` (PNG + PDF, 300 dpi)
- Data: `campaign_results.json`
