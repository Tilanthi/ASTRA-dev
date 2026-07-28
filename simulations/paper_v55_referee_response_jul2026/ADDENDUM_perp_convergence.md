# ADDENDUM — Perpendicular-field resolution spot-check (result)
## For the v55/v56 referee response (Referee 2 M1, Referee 1 #1)

**Prepared by:** ASTRA-PA · **Date:** 2026-07-28

### What this is
The doubled-resolution spot-check that Referee 2 requested (option a of M1: "run at least a
doubled-resolution spot check for the perpendicular ideal-MHD and ambipolar configurations ... and report
whether λ/W_fil is stable under refinement") has now reached the measurement epoch. This addendum reports the
**definitive outcome** and supersedes the earlier, prematurely-worded "preliminary" note.

### Setup
Two representative perpendicular ambipolar configurations (θ=90°, η_AD=0.05), rerun at **doubled transverse
resolution** (512×64×64 → 512×128×128, so the local Jeans length is resolved by N_J ≳ 4 cells at the beading
epoch, versus N_J ≈ 1–2 in the production runs). Everything else identical (same pgen, seed, boundaries,
ambient confinement). Analysis is the identical peak-detection algorithm used throughout the paper, at the
maximum-interior-peak-count epoch.

### Result — the perpendicular fragmentation wavelength is NOT numerically converged

| Configuration | 64³ (N_J≈1–2): λ/W_fil, peaks | 128³ (N_J≈4): λ/W_fil, peaks | change |
|---|---|---|---|
| f=1.2, β=1.0 | **1.00**, 9 | **0.46**, 21 | λ/W ×0.46; peaks ×2.3 |
| f=1.5, β=2.0 | **0.96**, 9 | **1.25**, 11 | λ/W ×1.30; peaks ×1.2 |

**Doubling the resolution changes the measured perpendicular λ/W_fil by a factor of ~2, and in *inconsistent
directions* between the two configurations (one halves, one increases ~30%), while the peak count changes by
up to ×2.3.** This is the textbook signature of numerical non-convergence: the measured "fragmentation
wavelength" tracks the grid, not a physical scale. (Both resolutions, moreover, make the measurement during
deep radial collapse, C ~ 10⁴–10⁵, where the transverse-averaged profile has grid-dependent sub-structure.)

`hires_convergence_result.json` contains the numbers; `figures/perp_convergence.png` shows them.

### What this means for the paper (definitive support for the downgrade)
This is a **data-backed confirmation** of Referee 2's M1 and Referee 1's #1: the perpendicular λ/W numbers
(≈ 0.85–1.4 in the paper) are **resolution-dependent artefacts and cannot be quoted as physical results.**

- **Adopt the reframing (v56 instructions §0/M1) as established, now with evidence:** the perpendicular case
  must be presented as *"we cannot obtain a numerically converged perpendicular fragmentation wavelength — the
  value changes by a factor ~2 under a doubling of resolution (Appendix/this spot-check)"*, NOT as a demonstrated
  λ/W. Remove the specific perpendicular λ/W values from any results table that implies they are on equal
  footing with the (converged) longitudinal numbers; keep them only as resolution-limited illustrations.
- **The population-weighted synthesis** (which multiplies these unconverged perpendicular numbers by 0.9)
  inherits this non-convergence — reinforcing the recommendation (M5) to label it Speculative/illustrative,
  not Established.
- **Nothing here weakens the two solid results:** the observational sub-Jeans NN spacing (converged, robust)
  and the longitudinal supercritical agreement (Truelove-satisfied, 128³/256³-converged) stand unchanged.

### Honest scope / caveats
- This is a **2-configuration spot check at 2 resolutions** — exactly what Referee 2 asked for to *demonstrate
  non-convergence*, but not a full convergence study. A definitive *converged* perpendicular wavelength would
  need more configurations and ≥3 resolutions (ideally with AMR), which remains future work and is the honest
  thing to state as the required next step.
- The runs were measured at the maximum-peak-count epoch (t ≈ 0.42–0.44 t_J); they were then in terminal
  radial collapse (dt → the CFL kill threshold) and were stopped once the measurement was captured.

### Bottom line
The higher-resolution spot-check **settles the central question of the last two referee rounds**: the
perpendicular-field simulations are **not numerically converged**, so the perpendicular "tension" must be
presented as a *preliminary, resolution-limited* discrepancy — precisely the wording change both referees
required. This is now supported by direct evidence rather than by the Truelove cell-count argument alone.
