# New result folded into Paper II: the continuous-driving test

Paper II previously ended: *"the one field geometry able to shorten the mode is not
simulated, and driven turbulence is not tested, so what sets the observed
distribution remains open."* The driven half of that has now been done.

## Setup
Athena++ ships a continuously driven turbulence module (`turb_flag = 3`); it was
never used because our problem generator seeds once at t=0. No code change was
needed. Campaign: **15 runs**, f = 1.5 supercritical Gaussian production profile,
β = 1, axial box lengthened to **L_x = 48 λ_J** at production cell size so several
groups can form. Three undriven controls (different seeds) plus twelve driven runs
across three injection bands (axial modes 3–6, 6–12, 12–24) and two amplitudes;
OU correlation time 0.3 t_J, solenoidal fraction 0.6.

Runs are compared **at matched fragmentation onset** (first snapshot with axial
contrast > 3.5), not matched time, because driving shortens the onset.

## Result — negative, and informative

| | N cores | f_occ | gap CoV | F(6 λ_J) |
|---|---|---|---|---|
| Undriven controls (3) | 8–15 | 0.012–0.026 | 1.34–1.60 (med **1.50**) | 1.00–1.93 (med **1.54**) |
| Driven (4 at onset) | 16–18 | 0.023–0.034 | 0.40–1.44 (med **0.57**) | 0.08–0.99 (med **0.38**) |
| **Observed (Paper I)** | — | **0.06–0.27** | 0.65–1.37 | **1.6–25** |

Driving does what one would naively expect in one respect — it roughly doubles the
fragment count and the occupancy fraction. But it moves the point process in the
**wrong direction**: the gap dispersion falls from 1.50 to 0.57 and the Fano factor
from 1.54 to 0.38, i.e. from mildly over-dispersed to *sub-Poissonian*. Neither the
driven nor the undriven runs come near the observed over-dispersion, and the
simulated occupancy fraction is an order of magnitude too low.

## Why this matters

A statistically homogeneous driver stirs every stretch of the filament equally, so
it supplies extra seed power rather than the persistent axial modulation of the
line mass the observations require. The conclusion is now a positive statement
rather than an open question: **the observations call for an inhomogeneous
assembly history, not more turbulence.**

## Caveats stated in the paper
Seven of fifteen runs had reached onset when the analysis was made; the remainder
are still integrating through the timestep runaway and are deposited without
measurements. One driving prescription (solenoidal-dominated, OU) at two amplitudes.

## Bookkeeping
Load-bearing runs 93 → **108**; total 2270 → **2285**; new row in the accounting
table; Data Availability updated to match.
