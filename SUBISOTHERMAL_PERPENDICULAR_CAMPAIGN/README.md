# Sub-Isothermal Perpendicular Field Campaign
# Critical simulations to resolve Planck mixture calculation uncertainty

## Campaign Goal

Resolve the critical gap identified in the filament spacing paper: sub-isothermal perpendicular-field simulations at supercritical line masses (f ≥ 1.5).

## Scientific Motivation

Current mixture calculation spans ⟨λ/W⟩_Planck ≈ 1.5–5.7 depending on assumed equation of state:
- Isothermal (γ = 1.0): ⟨λ/W⟩_Planck ≈ 1.5 (below HGBS measurements)
- Sub-isothermal (γ ≈ 0.8): ⟨λ/W⟩_Planck ≈ 5.7 (above HGBS measurements)

This campaign will definitively measure λ/W for perpendicular fields with γ < 1 at f ≥ 1.5, allowing self-consistent Planck tension assessment.

## Parameter Space

### Fixed Parameters
- Field geometry: θ = 90° (perpendicular to filament axis)
- Mach number: M = 1.0 (start with subsonic, can expand to M = 2.0)
- Resolution: 256^3 (validated resolution from convergence tests)
- Domain size: Standard filament campaign dimensions
- Boundary conditions: Periodic in axial direction, outflow in transverse directions

### Variable Parameters
- Line-mass fraction: f = [1.5, 2.0, 2.5, 3.0]
- Plasma beta: β = [0.5, 1.0, 2.0]
- Adiabatic index: γ = [0.7, 0.8, 0.9]
- Random seeds: [0, 1]

Total simulations: 4 × 3 × 3 × 2 = 72

## Simulation Naming Convention

Format: subiso_perp_f{f}_beta{beta}_gamma{gamma}_seed{seed}

Examples:
- subiso_perp_f1.5_beta0.5_gamma0.7_seed0
- subiso_perp_f3.0_beta2.0_gamma0.9_seed1

## Expected Outcomes

### Primary Measurements
1. Fragmentation wavelength: λ/W (via peak-finding and periodogram analysis)
2. Fragmentation time: t_frag (in units of t_J)
3. Classification: FRAG, STABLE_PARTIAL, or FLAT_PROFILE
4. Core properties: Mass, position, spacing when applicable

### Success Criteria
- Detect longitudinal beading in ≥80% of simulations
- Measure λ/W with uncertainty <15% across parameter space
- Identify γ-dependence trends for perpendicular fields
- Enable self-consistent Planck mixture calculation

## Resource Requirements

- Ray cluster: 220 vCPUs
- Memory per simulation: ~4-8 GB RAM (256^3 resolution)
- Disk per simulation: ~10-20 GB output
- Walltime per simulation: ~4-8 hours (depending on parameter)
- Total walltime: ~24-48 hours with 220 vCPUs (parallel execution)

## Analysis Pipeline

1. **Peak-finding analysis**: Detect axial density peaks
2. **Periodogram analysis**: Measure characteristic wavelength
3. **Classification**: Categorize fragmentation outcome
4. **λ/W calculation**: Compute spacing in units of filament width
5. **Statistical analysis**: Aggregate results across parameter space
6. **Mixture calculation**: Compute Planck-weighted prediction

## Deliverables

1. **Simulation data**: All 72 simulation outputs archived
2. **Results database**: CSV with λ/W, t_frag, classification for each run
3. **Analysis plots**: 
   - λ/W vs f for different γ values
   - λ/W vs β for different γ values
   - t_frag heatmaps in (f, β) plane
   - Comparison with isothermal perpendicular results
4. **Mixture calculation**: Updated ⟨λ/W⟩_Planck with uncertainty bounds
