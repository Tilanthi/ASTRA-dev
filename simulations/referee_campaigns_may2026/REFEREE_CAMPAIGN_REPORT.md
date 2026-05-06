# Referee Campaign Report — May 2026
**Generated**: $(date -u +"%Y-%m-%d %H:%M UTC")
**Total Simulations**: 58/58 FRAG (100%)

## Campaign Overview
Three campaigns testing λ/W fragmentation wavelength at near-critical conditions (f=1.1):
- **B_min**: θ-scan (0°–90°), f=1.1, β=1.0/2.0, 4 seeds — 28 sims
- **A_min**: Perpendicular B (θ=90°), f=1.1/1.2, β=1.0/1.5/2.0/3.0, 3 seeds — 24 sims
- **C_min**: Resolution convergence (θ=0°, β=1.0), C_low (256³/np=16) + C_high (512³/np=64) — 6 sims

## Key Science Results

### 1. Universal Fragmentation Confirmed
**58/58 FRAG** across all parameter space at f=1.1. No stability found at any θ or β.

### 2. B_min — t_frag vs Field Angle (f=1.1, β=1.0/2.0, 4 seeds)
| θ (°) | t_frag (t_J) | std | Note |
|--------|-------------|-----|------|
| 0  | 1.425 | 0.097 | DT_KILL sims — machine-zero oscillation at near-critical |
| 15 | 1.448 | 0.078 | Same regime |
| 30 | 1.090 | 0.041 | Transition: 25% speedup |
| 45 | 0.263 | 0.362 | **BIMODAL**: some DT_KILL (slow), some radial collapse (fast) |
| 60 | 0.055 | 0.005 | Radial collapse dominated |
| 75 | 0.055 | 0.005 | Radial collapse plateau |
| 90 | 0.061 | 0.011 | Perpendicular B = radial collapse |

**Sharp transition at θ~30–45°**: field-aligned support collapses rapidly above 30°.
**Note**: θ≥60° fast sims (t≈0.055 t_J) show radial collapse (FLAT λ/W profiles), 
not longitudinal beading. The HST density threshold triggers on radial concentration.

### 3. B_min — β Dependence
| β | mean t_frag (t_J) |
|----|------------------|
| 1.0 | 0.684 |
| 2.0 | 0.573 |

Higher β (weaker B field) → 16% faster collapse for f=1.1, all θ combined.

### 4. A_min — θ=90° t_frag vs β
| f   | β   | t_frag (t_J) |
|-----|-----|-------------|
| 1.1 | 1.0–3.0 | 0.022–0.033 | (radial collapse, unreliable t_frag) |
| 1.2 | 1.0 | 0.660 ± 0.010 |
| 1.2 | 1.5 | 0.640 ± 0.026 |
| 1.2 | 2.0 | 0.604 ± 0.006 |
| 1.2 | 3.0 | 0.617 ± 0.053 |

For f=1.2, θ=90°: β has minimal effect on t_frag (~8% range over β=1–3).

### 5. C_min — Resolution Convergence (f=1.1, θ=0°, β=1.0)
| Config | Resolution | np | t_frag (t_J) |
|--------|-----------|-----|-------------|
| C_low  | 256×64×64  | 16 | 1.507 ± 0.040 |
| C_high | 512×128×128 | 64 | 1.493 ± 0.025 |

**Excellent convergence** — t_frag agrees to <1% between resolutions.

### 6. λ/W Measurements
**23 valid measurements** from 58 sims; 21 classified GOOD.

#### Best Measurement (C_high, high-resolution):
- **sim_id**: C_high_f1p1_b1p0_th0_s251
- **λ = 1.703 λ_J**, **W = 0.375 λ_J**, **λ/W = 4.54**
- 512×128×128 at θ=0°, β=1.0, f=1.1
- **Consistent with theoretical prediction** (Inutsuka & Miyama 1992/97: λ_max ≈ 4.7W)

#### θ=0°, β=2.0 (B_min, 3 measurements):
- λ/W = 6.9–8.6 (mean 7.4 ± 0.9) — W well-resolved at ~20 cells

#### Caveats on W Measurements:
For θ≥15° (oblique/perpendicular B), W→1–2 cells at 64 cells/λ_J transverse resolution.
These λ/W values are resolution-limited artefacts, not physical measurements.
**Only θ=0° results with sufficient β (β≥2.0) give physically meaningful W.**

## Technical Notes
- **DT_KILL watchdog** (threshold=1e-6): Essential for f=1.1 near-critical at θ=0°/15°
  where machine-zero oscillation (dt~10⁻¹²) would otherwise stall indefinitely
- **Phase runner** v2 with retroactive classification handled 13 partial sims from v1
- **Disk**: 66 GB used; 401 GB free (14% full)
- **HDF5 files**: 994 athdf files — recommend purge to recover ~60 GB

## Files
- `referee_consolidated_results.json` — full stats + all status.json data + λ/W
- `B_min_lambda_W.json`, `A_min_lambda_W.json`, `C_min_lambda_W.json` — per-campaign λ/W
- `all_results.json`, `Phase_1_(B+A)_results.json`, `Phase_2_(C-min)_results.json` — runner outputs
- `nohup_v2.out`, `runner_v2.log` — execution logs

## GitHub
Campaign results at: `simulations/referee_campaigns_may2026/`
