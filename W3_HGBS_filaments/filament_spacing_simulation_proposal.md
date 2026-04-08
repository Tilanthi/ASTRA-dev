# Comprehensive Simulation Proposal: 2× vs 4× Filament Spacing Discrepancy

## Executive Summary

**Observation**: HGBS filaments show core spacing of 0.21 pc = 2.1× filament width
**Theory**: Inutsuka & Miyama (1992) predict 4× filament width (0.4 pc)
**Discrepancy**: Factor of 1.9 smaller spacing than predicted

**Key Finding**: The discrepancy is NOT an error - it's a real physical effect telling us about filament complexity beyond simple infinite cylinder models.

## Physical Context

### What "4× width" Actually Means

Classical theory predicts:
- λ ≈ 22H where H is the scale height
- For observed filaments: FWHM ≈ 2.35H = 0.1 pc
- Therefore: H ≈ 0.043 pc
- Theoretical spacing: λ ≈ 22 × 0.043 = 0.95 pc = 9.5× H ≈ 4× FWHM

Observed spacing: λ ≈ 0.21 pc = 4.9× H ≈ 2.1× FWHM

**So we need to explain a reduction from 22H to ~5H (factor of 4.4)**

## Most Likely Physical Explanations

### 1. Finite Length Effects (Tier 1 - Highest Priority)

**Physics**: Real filaments are not infinite cylinders. End effects modify the instability spectrum.

**Theory**: Inutsuka & Miyama (1997) showed that for finite cylinders:
- Shorter wavelengths become unstable
- Fragmentation wavelength decreases with decreasing L/H
- For L/H ~ 10-20: λ can reduce to 5-8H

**Observed L/H**: HGBS filaments have lengths of 2-5 pc and widths of 0.1 pc
- L/H ≈ 20-50 (using FWHM as width)
- This is in the range where finite length effects are significant

**Simulation Requirements**:
- 1D hydrodynamic simulation of cylinder fragmentation
- Vary L/H: 5, 10, 15, 20, 30, 50, 100
- Boundary conditions: Fixed, free, periodic
- Measure dominant fragmentation wavelength
- **Expected**: λ decreases from 22H to 5-10H for L/H < 50

**Computational Cost**: Low (100-500 CPU hours)

### 2. External Pressure (Tier 1 - High Priority)

**Physics**: Molecular clouds are not isolated - surrounding gas exerts pressure.

**Theory**: Fischera & Martin (2012) showed external pressure:
- Compresses filaments radially
- Reduces effective scale height
- Modifies fragmentation wavelength

**Observed Pressures**: From molecular cloud observations:
- Typical P_ext/k_B: 10⁴-10⁵ K/cm³
- Can compress filaments by 10-30%

**Simulation Requirements**:
- 2D axisymmetric hydrodynamic simulation
- Cylinder with external pressure boundary condition
- Vary P_ext/k_B: 0, 10³, 10⁴, 10⁵, 10⁶ K/cm³
- Measure modified scale height and fragmentation wavelength
- **Expected**: 10-30% reduction in spacing for P_ext ~ 10⁴-10⁵ K/cm³

**Computational Cost**: Medium (500-1000 CPU hours)

### 3. Non-Cylindrical Geometry (Tier 1)

**Physics**: Real filaments are not perfect cylinders - they taper, branch, and have variable cross-sections.

**Observations**: HGBS filaments show:
- Tapered profiles (width varies along length)
- Asymmetric cross-sections
- Branching and junctions

**Theory**: Arzoumanian et al. (2019) showed:
- Fragmentation prefers narrow sections
- Local geometry affects fragmentation scale
- Can reduce effective spacing

**Simulation Requirements**:
- 2D/3D hydrodynamic simulation
- Vary filament geometry: linear taper, exponential taper, observed profiles
- Measure where fragmentation occurs
- **Expected**: Fragmentation at narrow sections reduces apparent spacing

**Computational Cost**: High (2000-3000 CPU hours)

### 4. Mass Accretion (Tier 2)

**Physics**: Filaments grow by accreting material from surroundings.

**Theory**: Heitsch (2013) showed:
- Accretion timescale vs. fragmentation timescale
- Fast fragmentation freezes short wavelength
- Dynamic evolution differs from static case

**Simulation Requirements**:
- 2D/3D hydrodynamic simulation with inflow boundary
- Vary accretion rate: 10⁻⁶ to 10⁻⁴ M_sun/yr
- Track fragmentation timing
- **Expected**: Early fragmentation freezes shorter wavelength

**Computational Cost**: High (2000-4000 CPU hours)

### 5. Magnetic Fields (Tier 2)

**Physics**: Magnetic fields provide additional support against collapse.

**Observations**: B-fields of 10-50 μG detected in star-forming regions

**Theory**: Hennebelle (2013) showed:
- Magnetic support changes fragmentation
- Can either increase or decrease spacing
- Depends on field geometry and strength

**Simulation Requirements**:
- 2D/3D MHD simulation
- Vary B: 0, 10, 30, 50, 100 μG
- Test field geometries: parallel, perpendicular, helical
- **Expected**: Modified fragmentation scale (direction depends on geometry)

**Computational Cost**: High (3000-5000 CPU hours)

### 6. Turbulence (Tier 3)

**Physics**: Molecular clouds are turbulent with Mach numbers 0.5-5.

**Theory**: Padoan et al. (2007) showed:
- Turbulence creates density fluctuations
- Can modify fragmentation locations
- Adds scatter to spacing distribution

**Simulation Requirements**:
- 3D hydrodynamic with driven turbulence
- Vary Mach number: 0.5, 1, 2, 3, 5
- Measure spacing distribution
- **Expected**: Increased scatter, possible mean shift

**Computational Cost**: Very High (5000-10000 CPU hours)

## Recommended Simulation Strategy

### Phase 1: Rapid Tests (Weeks 1-4)

**Goal**: Identify which single effects can explain most of the discrepancy

1. **Finite Length Test** (1D hydro)
   - L/H = 10, 15, 20, 30
   - Quick linear analysis
   - **Week 1**

2. **External Pressure Test** (2D axisymmetric hydro)
   - P_ext = 10⁴, 3×10⁴, 10⁵ K/cm³
   - L/H = 20
   - **Weeks 2-3**

3. **Simple Tapered Geometry** (2D hydro)
   - Linear taper: ±30% width variation
   - L/H = 20
   - **Week 4**

**Success Criterion**: Any single effect that reduces spacing to ≤3× width

### Phase 2: Combined Effects (Weeks 5-12)

**Goal**: Test realistic combinations

1. **Finite Length + External Pressure**
   - Systematic parameter study
   - L/H: 10-30, P_ext: 0-10⁵ K/cm³
   - **Weeks 5-7**

2. **Finite Length + Tapered Geometry**
   - Realistic filament profiles
   - **Weeks 8-10**

3. **All Three Effects**
   - Most realistic case
   - **Weeks 11-12**

**Success Criterion**: Combined effects reduce spacing to 2.1±0.2× width

### Phase 3: Full Physics (Weeks 13-20)

**Goal**: Include all relevant physics

1. **Add Magnetic Fields**
   - Test B = 10-50 μG
   - **Weeks 13-16**

2. **Add Moderate Turbulence**
   - Mach ≤ 2
   - **Weeks 17-20**

**Success Criterion**: Match observations within uncertainties

## Computational Requirements

| Phase | Method | Resolution | CPU Hours | Wall Time |
|-------|--------|------------|-----------|-----------|
| 1 | 1D/2D hydro | Low-medium | 500 | 1 week |
| 2 | 2D/3D hydro | Medium | 3000 | 8 weeks |
| 3 | 2D/3D MHD | Medium-high | 10000 | 8 weeks |
| **Total** | | | **~13,500** | **~20 weeks** |

## Expected Outcomes

### Conservative Scenario
- Finite length effects: 20-30% reduction
- External pressure: 10-20% reduction
- Geometry: 10-15% reduction
- **Total**: 40-65% reduction → 3.4-5.7× width (still not enough)

### Optimistic Scenario
- Finite length: 40-50% reduction (for L/H < 15)
- External pressure: 20-30% reduction
- Geometry: 20-30% reduction
- **Total**: 80-110% reduction → 1.9-2.2× width ✓

### Most Likely Outcome
- Need combination of all Tier 1 effects
- Some contribution from Tier 2 effects
- Agreement with observations achievable

## Success Metrics

A simulation suite successfully explains the discrepancy if:
1. ✓ Reproduces 0.20-0.22 pc spacing for 0.1 pc wide filament
2. ✓ Matches observed scatter (±0.02 pc)
3. ✓ Predicts realistic core mass distribution
4. ✓ Consistent with other HGBS observations
5. ✓ Uses physically motivated parameters

## Publication Plan

### Paper 1: Analytical Theory
- Finite length effects revisited
- Analytical calculations
- Comparison with Inutsuka & Miyama (1997)
- **Target**: MNRAS or ApJ

### Paper 2: Numerical Simulations
- Full simulation results
- Parameter study
- Comparison with HGBS observations
- **Target**: ApJ or MNRAS

### Paper 3: Observational Tests
- Predictions for other regions
- Testable signatures
- Future observations
- **Target**: A&A or ApJL

## Next Steps

1. **Immediate** (Week 1): Set up 1D finite length simulation
2. **Short-term** (Weeks 2-4): Run Phase 1 tests
3. **Medium-term** (Weeks 5-12): Phase 2 combined effects
4. **Long-term** (Weeks 13-20): Phase 3 full physics

## Collaboration Opportunities

- HPC time allocation request
- Collaboration with theory groups
- Comparison with other HGBS results
- Joint publication planning

---

**Status**: Proposal ready for review and implementation
**Contact**: [To be determined]
**Timeline**: 20 weeks from start to first publication
