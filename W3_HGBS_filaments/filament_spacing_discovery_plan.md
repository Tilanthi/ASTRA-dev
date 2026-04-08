# Discovery Plan: Why is Observed Core Spacing ~2× Width, Not 4×?

## Executive Summary

Classical cylindrical fragmentation theory (Inutsuka & Miyama 1992) predicts fragmentation at 4× the filament width (~0.4 pc for 0.1 pc wide filaments). Observations consistently show ~2× spacing (~0.21 pc). This discovery plan will systematically test physical explanations through numerical simulations.

## Priority Ranking of Hypotheses

Based on physical realism and observational support:

### Tier 1: Most Likely (Primary Investigation)
1. **Finite Length Effects** - Direct analytical prediction (Inutsuka & Miyama 1997)
2. **External Pressure** - Observed in real molecular clouds
3. **Mass Accretion/Dynamic Evolution** - Filaments are not static

### Tier 2: Secondary Investigation
4. **Non-Cylindrical Geometry** - Observed filament profiles
5. **Magnetic Fields** - Detected in star-forming regions
6. **Turbulence** - Ubiquitous in molecular clouds

### Tier 3: Tertiary Investigation
7. **Projection Effects** - Geometric, likely minor contribution

## Simulation Suite

### Suite A: Finite Length Effects (Highest Priority)

**Model**: 1D Hydrodynamic Cylindrical Fragmentation with Finite Boundaries

**Method**: Grid-based hydrodynamics (Athena++ or similar)

**Parameters**:
- Length-to-width ratios (L/H): 5, 10, 20, 30, 50, 100
- Boundary conditions: Fixed, free, periodic
- Initial perturbation spectrum: Thermal noise, imposed modes
- Resolution: 1024-4096 zones along axis

**Metrics**:
- Dominant fragmentation wavelength
- Growth rates of instability modes
- Comparison with infinite cylinder theory

**Expected Outcome**: Quantify reduction from 4× as function of L/H

**Computational Cost**: Low-Medium (~100-500 CPU hours)

---

### Suite B: External Pressure Effects

**Model**: 2D Axisymmetric Cylinder with External Pressure

**Method**: Grid-based hydrodynamics with AMR (FLASH, Athena++)

**Parameters**:
- External pressure: 0, 10³, 10⁴, 10⁵ K/cm³
- Pressure ratio (P_ext/P_int): 0.1-10
- Mach number: 0.5-2.0
- Temperature: 10-20 K

**Metrics**:
- Modified scale height
- Fragmentation wavelength
- Critical mass-per-unit-length

**Expected Outcome**: External pressure compresses filaments, reducing spacing

**Computational Cost**: Medium (~500-1000 CPU hours)

---

### Suite C: Mass Accretion and Dynamic Evolution

**Model**: 2D/3Cylindrical Filament with Radial Inflow

**Method**: SPH (Gadget, Phantom) or Grid-based with source terms

**Parameters**:
- Accretion rate: 10⁻⁶ to 10⁻⁴ M_sun/yr
- Accretion duration: 0.1-2.0 free-fall times
- Initial mass: Subcritical to supercritical
- Accretion geometry: Isotropic, anisotropic

**Metrics**:
- Fragmentation timing (when does it occur?)
- Fragmentation wavelength
- Core mass distribution
- Comparison with static case

**Expected Outcome**: Early fragmentation freezes shorter wavelength

**Computational Cost**: Medium-High (~1000-2000 CPU hours)

---

### Suite D: Non-Cylindrical Geometry

**Model**: 2D/3D Tapered Filament

**Method**: Grid-based (Athena++) with curvilinear coordinates

**Parameters**:
- Tapering profiles: Linear, exponential, observed
- Width variation: ±50% along length
- Cross-section shape: Circular, elliptical
- Density profiles: Plummer, Gaussian, observed

**Metrics**:
- Local fragmentation scale
- Preferred fragmentation sites
- Wavelength variation along filament

**Expected Outcome**: Fragmentation occurs at narrow sections

**Computational Cost**: High (~2000-3000 CPU hours)

---

### Suite E: Magnetic Fields (MHD)

**Model**: 2D/3D MHD Cylindrical Fragmentation

**Method**: MHD codes (Athena++, Zeus-MP, Pencil Code)

**Parameters**:
- Magnetic field strength: 1-100 μG
- Field geometry: Parallel, perpendicular, helical
- Plasma beta: 0.1-10
- Alfvén Mach number: 0.1-5

**Metrics**:
- Modified fragmentation wavelength
- Growth rates with magnetic support
- Critical mass-per-unit-length with B-fields

**Expected Outcome**: B-fields provide support, may increase or decrease spacing

**Computational Cost**: High (~2000-4000 CPU hours)

---

### Suite F: Turbulent Fragmentation

**Model**: 3D Turbulent Filament

**Method**: SPH or Grid-based with driven turbulence

**Parameters**:
- Mach number: 0.5-5 (subsonic to supersonic)
- Turbulent driving: Compressive, solenoidal, mixed
- Driving scale: 0.1-1 × filament length
- Injection spectrum: Kolmogorov, Burgers

**Metrics**:
- Core spacing distribution
- Scatter in spacing
- Comparison with thermal case

**Expected Outcome**: Turbulence increases scatter, may modify mean spacing

**Computational Cost**: Very High (~5000-10000 CPU hours)

---

### Suite G: Combined Effects (Realistic Scenarios)

**Model**: Multi-physics simulations combining top effects

**Combinations**:
1. Finite Length + External Pressure
2. Finite Length + Mass Accretion
3. External Pressure + Magnetic Fields
4. All three + Moderate Turbulence

**Method**: Appropriate combination of above methods

**Expected Outcome**: Realistic filament behavior matching observations

**Computational Cost**: Very High (~5000-15000 CPU hours)

## Numerical Methods Comparison

| Method | Strengths | Weaknesses | Best For |
|--------|-----------|------------|----------|
| **Grid-based (Athena++)** | Sharp shock handling, good for hydro/MHD | Geometry constraints | Suites A, B, E |
| **SPH (Gadget, Phantom)** | Flexible geometry, good for dynamics | Resolution issues | Suites C, F |
| **AMR (FLASH, Enzo)** | Adaptive resolution, large dynamic range | Computational cost | Suites B, D, G |
| **Spectral Methods** | High accuracy for smooth flows | Boundary conditions | Suite A (analytic) |

## Observational Constraints

**Target Observations** (from HGBS regions):
- Filament width: 0.10 ± 0.01 pc
- Core spacing: 0.21 ± 0.01 pc (2.1× width)
- Length-to-width ratios: ~10-50
- External pressure: 10⁴-10⁵ K/cm³ (estimated)
- Magnetic field: 10-50 μG (observations)

## Success Criteria

A simulation suite successfully explains the 2× spacing if:
1. Reproduces 0.20-0.22 pc spacing for 0.1 pc wide filament
2. Matches observed scatter (~±0.02 pc)
3. Predicts correct core mass distribution
4. Consistent with other HGBS observations
5. Physically justified parameters

## Timeline

**Phase 1** (Weeks 1-4): Suites A and B (Finite length + External pressure)
**Phase 2** (Weeks 5-8): Suite C (Mass accretion)
**Phase 3** (Weeks 9-12): Suites D and E (Geometry + Magnetic fields)
**Phase 4** (Weeks 13-16): Suite F (Turbulence)
**Phase 5** (Weeks 17-20): Suite G (Combined effects + refinement)

## Computational Requirements

**Total CPU Hours**: ~20,000-40,000
**Storage**: ~10-50 TB (depending on resolution)
**Software**: Athena++, FLASH, Gadget-3/4, or equivalent

## Expected Outcomes

1. **Quantitative understanding** of which effects reduce spacing from 4× to 2×
2. **Predictive framework** for core spacing in different environments
3. **Testable predictions** for future observations
4. **Revised theoretical model** for filament fragmentation
5. **Publication-ready results** explaining the discrepancy

## Collaboration Needs

- High-performance computing resources
- Expertise in filament instability theory
- Access to simulation codes and validation data
- Comparison with existing HGBS catalog products
