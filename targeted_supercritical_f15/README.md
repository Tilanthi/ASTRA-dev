# Targeted Supercritical f=1.5 Campaign

## Purpose

This campaign addresses the **supercritical extrapolation gap** identified in peer review. All 654 existing supercritical simulations (f ≥ 1.5) show pure radial collapse with no longitudinal beading. This campaign tests whether extending the simulation domain allows beading to develop at the low-supercritical boundary (f = 1.5).

## Key Innovation: Extended Domain

**Standard domain**: 8λ_J × 1λ J × 1λ J (allows 2-3 fragmentation wavelengths)
**Extended domain**: 24λ J × 1λ J × 1λ J (allows 8+ fragmentation wavelengths)

The 3× longer domain provides more time/space for longitudinal beading to develop before radial collapse dominates.

## Campaign Specifications

### Parameter Point

```
f = 1.5          (Low-supercritical boundary)
β = 1.0          (Intermediate field strength)
M = 1.0          (Fiducial turbulence)
θ = 0°           (Longitudinal B-field)
Seeds: 5         (42, 137, 251, 367, 499)
```

### Domain & Resolution

```
Lx = 24 λ J
Ly = 1 λ J
Lz = 1 λ J

Nx = 1536
Ny = 64
Nz = 64

Uniform grid: dx = dy = dz = 0.0156 λ J
```

### Runtime

```
Max time: 2.0 t_J
Output interval: 0.1 t_J (20 snapshots per sim)
Wall timeout: 6 hours
```

## Usage

### 1. Generate Configurations

```bash
python3 generate_configs.py
```

Creates 5 .athinput files in `./configs/` directory.

### 2. Compile Athena++

```bash
cd athena++
./configure
make
```

Ensure the filament problem generator is available.

### 3. Run Campaign

```bash
python3 run_campaign.py
```

Runs all 5 simulations. Can take 1-2 days depending on cluster performance.

### 4. Analyze Results

```bash
python3 analyze_results.py
```

Classifies simulations into:
- **BEADING**: Clear longitudinal peaks (amplitude > 0.15)
- **TRANSITIONAL**: Weak beading (amplitude 0.05-0.15)
- **RADIAL_COLLAPSE**: No longitudinal structure

Extracts λ/W measurements where applicable.

## Success Criteria

### If BEADING is detected:

1. **Direct λ/W measurement** at f = 1.5
2. **Validation** of extrapolation from near-critical (f = 1.0-1.2)
3. **Paper update**: Add new section "Supercritical Fragmentation: Direct Measurements"
4. **Figure 11 update**: Include f=1.5 data point

### If RADIAL_COLLAPSE persists:

1. **Confirmation** that f = 1.5 is genuine regime transition
2. **Reinforced extrapolation uncertainty**: No direct λ/W measurement possible at f ≥ 1.5
3. **Paper update**: Add clarification about extended-domain test results

## Resource Requirements

```
Per simulation:
  - 16 MPI ranks
  - 4-8 GB RAM
  - 5 GB disk (100 snapshots)
  - 4-6 hours wall time

Total campaign:
  - 5 simulations
  - ~100-150 CPU-hours
  - ~25 GB disk
  - 1-2 days elapsed time
```

## Integration with Main Paper

### Text Changes Already Made

1. **Softened extrapolation language** (Section 5.9.3)
   - Changed: "validates extrapolation" → "does NOT by itself validate"
   - Added explicit conditioning on extrapolation assumption

2. **Figure 11**: Supercritical extrapolation gap visualization

3. **Abstract**: Explicit conditioning of theory-observation comparisons

### Pending Integration (After Results)

**If BEADING detected**: Add new section with λ/W measurement

**If RADIAL_COLLAPSE confirmed**: Add clarification text

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Insufficient beading time | 3× extended domain provides more wavelengths |
| Excessive computational cost | Only 5 sims at single parameter point |
| Inconclusive mixed results | Time-series analysis tracks beading vs collapse |
| CFL limit from collapse | Monitor for runaway collapse, document if triggered |

## Comparison with Previous Campaigns

| Campaign | Sims | Domain | Purpose |
|----------|------|--------|---------|
| DTC | 540 | 8λ J | Map transition boundary |
| BRIDGE | 200 | 16λ J | Test β-dependence |
| Supercritical | 654 | 8λ J | f = 1.5-3.0 regime |
| **This** | **5** | **24λ J** | **Extended domain test** |

## Files

- `generate_configs.py` - Config generation
- `run_campaign.py` - Execution script
- `analyze_results.py` - Classification and λ/W extraction
- `configs/` - Configuration files (created by generator)
- `TARGETED_SUPERCRITICAL_F15_CAMPAIGN.md` - Full specification

## Timeline

1. Config generation: 1 day
2. Simulation execution: 1-2 days
3. Analysis: 4 hours
4. Paper integration: 2 hours

**Total**: 3-4 days from start to paper-ready results

## Contact

**Questions about this campaign**: See TARGETED_SUPERCRITICAL_F15_CAMPAIGN.md

**Main paper**: filament_spacing_fiber_bundle.tex

---

**Status**: Ready for deployment
**Priority**: HIGH (addresses primary peer review concern)
**Date**: 2026-05-03
