# Definitive 2D Fragmentation Transition Campaign
# Complete Parameter Space Mapping: f ∈ [1.4, 2.2], β ∈ [0.3, 1.2]

## Campaign Goal

Definitively map the 2D fragmentation transition boundary in (f, β) space to determine:
1. Whether the transition depends primarily on f, β, or a combination
2. The exact functional form of the transition boundary
3. Whether Mach number affects the transition location
4. Statistical robustness through multiple random seeds

## Simulation Grid: 648 Runs Total

### Primary Grid: 9 × 6 × 3 × 2 = 324

| Parameter | Values | Count | Rationale |
|-----------|--------|-------|-----------|
| f (supercriticality) | 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2 | 9 | Covers transition zone with margin |
| β (plasma beta) | 0.3, 0.5, 0.7, 0.9, 1.1, 1.3 | 6 | From strong suppression to weak B field |
| M (Mach) | 1.0, 2.0, 3.0 | 3 | Subsonic to transonic turbulence |
| Seeds | 42, 137 | 2 | Statistical robustness |

### Extended Grid: 9 × 6 × 1 × 2 = 108 (Mach 4.0, 5.0)

**Additional 108 simulations** at M = 4.0, 5.0 to test supersonic regime:
- Same f and β grids as primary
- Only seed 42, 137
- Tests whether high Mach changes transition boundary

### Resolution & Domain

- **Grid**: 256 × 256 × 256 cells (same as moderate supercriticality)
- **Meshblocks**: 64³ cells (4×4×4 decomposition = 64 meshblocks)
- **Domain**: 16λ_J × 4λ_J × 4λ_J (periodic)
- **Runtime**: 4.0 t_J with 40 snapshots (every 0.1 t_J)
- **Outputs**: VTK (every 1.0 t_J) + TAB files (every 0.1 t_J)

### Physics Configuration

**Code Units** (consistent with moderate supercriticality campaign):
- Sound speed: c_s = 1
- Critical density: ρ_crit = 1
- Gravitational constant: 4πG = 2.636 (for ρ_c = 10)
- Jeans length: λ_J = 2π (for ρ_c = 1)

**Filament Profile**:
- Gaussian: ρ(r) = ρ_c exp(-r²/2)
- Width: W = 1
- Central density: ρ_c = 2f / (√(2π) × G_code)

**Magnetic Field**:
- Geometry: Uniform along filament axis (x-direction)
- Strength: B₀ = c_s √(2ρ_c/β)

**Turbulence**:
- Spectrum: Kolmogorov
- Mach: M = σ_turb/c_s
- Random seed: 42, 137 for reproducibility

## Expected Scientific Outcomes

### Hypothesis Testing

**H1: Transition depends on f only**
- Prediction: Vertical boundary in (f, β) plane
- Test: Is C_final independent of β at fixed f?

**H2: Transition depends on β only**
- Prediction: Horizontal boundary in (f, β) plane
- Test: Is C_final independent of f at fixed β?

**H3: Transition depends on combination f·β or f/β**
- Prediction: Diagonal boundary in (f, β) plane
- Test: Does transition follow f·β = constant or f/β = constant?

**H4: Mach number affects transition**
- Prediction: Boundary shifts with M
- Test: Compare transition location at M = 1.0, 2.0, 3.0, 4.0, 5.0

### Expected Results Grid

Based on moderate supercriticality campaign (β = 2/f² line):

| f \ β | 0.3 | 0.5 | 0.7 | 0.9 | 1.1 | 1.3 |
|-------|-----|-----|-----|-----|-----|-----|
| **1.4** | ? | ? | ? | **FRAG** | ? | ? |
| **1.5** | ? | ? | ? | **FRAG** | ? | ? |
| **1.6** | ? | ? | **TRANS** | **FRAG** | **FRAG** | ? |
| **1.7** | ? | **SUPP** | **TRANS** | **FRAG** | **FRAG** | ? |
| **1.8** | **SUPP** | **SUPP** | **TRANS** | **FRAG** | **FRAG** | **FRAG** |
| **1.9** | **SUPP** | **SUPP** | **SUPP** | **TRANS** | **FRAG** | **FRAG** |
| **2.0** | **SUPP** | **SUPP** | **SUPP** | **TRANS** | **FRAG** | **FRAG** |
| **2.1** | **SUPP** | **SUPP** | **SUPP** | **SUPP** | **TRANS** | **FRAG** |
| **2.2** | **SUPP** | **SUPP** | **SUPP** | **SUPP** | **TRANS** | **FRAG** |

Legend:
- **FRAG**: Vigorous fragmentation (C_final > 2.0)
- **SUPP**: Suppressed (C_final < 1.2)
- **TRANS**: Transition zone (1.2 < C_final < 2.0)
- **?**: Unknown (to be determined)

## Computational Requirements

### Per Simulation
- **Memory**: ~8 GB (64 cores)
- **Time**: ~3-5 hours on 64 cores
- **Disk**: ~5 GB (outputs)

### Full Campaign (648 simulations)
- **Core-hours**: ~155,000 (155k)
- **Wall time**: ~77 hours on 200 cores (3.2 days)
- **Disk**: ~3.2 TB

### Ray Cluster Configuration
- **Workers**: 200 (recommended)
- **CPUs per worker**: 1
- **Memory per worker**: 8 GB
- **Concurrent simulations**: 3-4 (64 cores each)

## Execution Strategy

### Phase 1: Primary Grid (32 simulations, ~2 days)
- f ∈ [1.4, 2.2], β ∈ [0.3, 1.3], M ∈ [1.0, 2.0, 3.0]
- Maps transition zone with statistical robustness

### Phase 2: Extended Grid (108 simulations, ~12 hours)
- M = 4.0, 5.0 on same (f, β) grid
- Tests supersonic regime

### Phase 3: Analysis & Boundary Mapping
- Extract C_final, n_cores, λ_frag for all runs
- Fit functional form to transition boundary
- Test Mach dependence

## Deliverables

### Data Products
1. **Complete dataset**: 648 × (C_final, n_cores, λ_frag, λ/W)
2. **Transition boundary**: Functional fit f_crit(β) or β_crit(f)
3. **Mach dependence**: Δf(M) or Δβ(M) if Mach affects transition
4. **Visualization**: 2D colormap of C_final(f, β) for each M

### Scientific Outputs
1. **Definitive answer**: Whether transition depends on f, β, or combination
2. **HGBS constraints**: Allowed (f, β) region for λ/W ≈ 2.11
3. **Predictive model**: For any (f, β, M), predict fragmentation state
4. **Paper-ready figures**: 3-4 publication-quality figures

## Success Criteria

1. **Complete coverage**: No gaps in (f, β) space around transition
2. **Statistical robustness**: 2 seeds per parameter set
3. **Mach independence**: Test whether M affects transition
4. **Definitive boundary**: Functional form with uncertainty quantification
5. **No follow-up needed**: This campaign should be the final word on transition

---
*Campaign designed for ASTRA filament spacing paper - April 2026*
*Total runtime: ~3 days on 200 vCPUs*
*Final MHD campaign - no additional runs needed*
