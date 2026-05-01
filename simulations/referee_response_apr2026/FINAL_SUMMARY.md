# Referee Response Campaigns — Final Results
## 2026-04-30 | astra-climate

## Campaign Overview
- **C5**: Turbulence λ/W measurements — 54 sims, 256×64×64, longitudinal B
- **C6**: Perpendicular-B β-dependence — 100 sims, 512×64×64, perpendicular B
- **C7**: Critical transition mapping — 135 sims, 256×64×64, longitudinal B
- **Total**: 289 sims | 283 FRAG | 6 TIMEOUT | 0 FAILED

## C5 Results
- 54 sims: f=[1.0,1.1,1.2], β=[0.5,1.0,2.0], turb=[turbphys(1.0),turbsynth(0.0001)], seeds=[42,137,314]
- FRAG=48/54, TIMEOUT=6 (β=2.0 turbphys near-critical — quasi-stable)
- t_frag: 0.706 ± 0.343 t_J
- λ/W (GOOD=28/48): 3.441 ± 0.764 [2.50–5.78]
  - β=0.5: λ/W=4.307 ± 0.602 (N=10)
  - β=1.0: λ/W=3.113 ± 0.231 (N=9)
  - β=2.0: λ/W=2.806 ± 0.131 (N=9)
- KEY: turbulence does NOT change λ/W (5% difference turbphys vs turbsynth, not significant)
- t_frag 3× faster with turbphys (physical turbulence) but fragment spacing unchanged

## C6 Results
- 100 sims: f=[1.2,1.3,1.4,1.5], β=[0.3,0.5,1.0,1.5,2.0], perpendicular B, seeds=[42,137,314,527,816]
- FRAG=100/100, TIMEOUT=0 — perpendicular B provides NO axial stability
- t_frag: 0.634 ± 0.071 t_J [0.506–0.807]
- t_frag by β (monotonic): 0.3→0.716, 0.5→0.681, 1.0→0.601, 1.5→0.598, 2.0→0.578 t_J
- t_frag by f (monotonic): 1.2→0.690, 1.3→0.649, 1.4→0.613, 1.5→0.585 t_J
- λ/W: GOOD=27 (β≥1.0 only), FLAT=73 (β≤0.5 → pure radial collapse)
  - λ/W (GOOD): 1.252 ± 0.092 [1.146–1.458]
  - β≤0.5: FLAT_PROFILE (strong perp B → no axial fragmentation, just radial collapse)
  - β≥1.0: λ/W≈1.25 (essentially β-independent)
- KEY: perpendicular B gives λ/W≈1.25 vs longitudinal λ/W≈3.4 (2.75× shorter)
  Strong perp B suppresses axial fragmentation entirely (radial collapse mode)

## C7 Results
- 135 sims: f=[0.9–1.3 in 0.05 steps], β=[0.3,0.5,1.0,1.5,2.0], longitudinal B, seeds=[42,137,314]
- FRAG=135/135, TIMEOUT=0 — NO stability at ANY f including sub-critical f<1.0
- t_frag: 1.077 ± 0.244 t_J [0.794–1.643]
- t_frag by f (monotonic): f=0.9→1.160, 0.95→1.136, 1.0→1.116, 1.05→1.095,
  1.1→1.074, 1.15→1.059, 1.2→1.034, 1.25→1.017, 1.3→0.999 t_J
  Rate: Δt_frag ≈ -0.040 t_J per Δf=0.05 — SMOOTH, no discontinuity at f=1.0
- t_frag by β (dominant effect): β=0.3→1.499, 0.5→1.170, 1.0→0.968, 1.5→0.892, 2.0→0.853 t_J
  Range: 76% from β=2.0 to β=0.3
- λ/W (GOOD=114/135): 3.382 ± 0.792 [2.50–5.78]
  - β=0.3: λ/W=4.740 ± 0.727 (N=6; many FEW_PEAKS — only 1-2 fragments fit in domain)
  - β=0.5: λ/W=4.375 ± 0.592 (N=27)
  - β=1.0: λ/W=3.191 ± 0.293 (N=27)
  - β=1.5: λ/W=2.857 ± 0.179 (N=27)
  - β=2.0: λ/W=2.803 ± 0.137 (N=27)
  KEY: λ/W increases with B-field strength (decreasing β) for longitudinal B
  Strong B → longer fragmentation wavelength (magnetic pressure support against short modes)
- KEY FINDING: f=1.0 is NOT a stability threshold; sub-critical filaments (f<1.0) always
  fragment given sufficient time; the critical line-mass sets a timescale, not a stability boundary

## Cross-Campaign λ/W Summary
| Campaign | Geometry | β | λ/W | σ |
|----------|----------|---|-----|---|
| C5+C7 | Longitudinal | 2.0 | 2.80–2.81 | 0.13–0.14 |
| C5+C7 | Longitudinal | 1.5 | 2.86 | 0.18 |
| C5+C7 | Longitudinal | 1.0 | 3.11–3.19 | 0.23–0.29 |
| C5+C7 | Longitudinal | 0.5 | 4.31–4.38 | 0.59–0.60 |
| C5+C7 | Longitudinal | 0.3 | 4.74 | 0.73 |
| C6 | Perpendicular | 1.0–2.0 | 1.25 | 0.09 |
| C6 | Perpendicular | 0.3–0.5 | FLAT (radial) | — |

## Data Locations
- C5: /data/referee_response_runs/C5/ (results.json, lambda_W_analysis.json)
- C6: /data/referee_response_runs/C6/ (results.json, lambda_W_analysis.json)
- C7: /data/referee_response_runs/C7/ (results.json, lambda_W_analysis.json)
- Runner: /data/rrc_runner.py (patched for multi-block HDF5)
- Log: /data/referee_response_runs/MASTER_RUNNER.log
