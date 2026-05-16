# Referee Response: Perpendicular Field λ/W ≈ 1.25 Inconsistency

**Date**: 2026-05-16
**Referee Concern**: The λ/W ≈ 1.25 result for perpendicular fields needs stronger theoretical justification, and the mixture calculation uses inconsistent physics.

## Summary of the Problem

The referee identifies a **fundamental inconsistency** in how the paper handles the perpendicular-field λ/W ≈ 1.25 value:

### Current Paper Approach

1. **Mixture calculation (Equation 2, line 901)** uses:
   - Perpendicular fields: λ/W = 1.25 (from **isothermal** simulations, γ = 1.0)
   - Longitudinal fields: λ/W = 3.7 (from **isothermal** simulations, γ = 1.0)
   - Result: ⟨λ/W⟩_Planck = 0.9 × 1.25 + 0.1 × 3.7 ≈ 1.5

2. **Paper's physical argument**:
   - Real molecular cloud filaments have γ_eff ≈ 0.7–0.9 (sub-isothermal)
   - This is based on far-IR cooling calculations for the density regime of HGBS filaments

3. **Sub-isothermal perpendicular field results** (Table shows):
   - λ/W = 5.5–7.9 for γ = 0.5–1.0
   - For γ ≈ 0.8 (physically plausible): λ/W ≈ 6.0

### The Inconsistency

The mixture calculation uses **isothermal physics** (γ = 1.0) for perpendicular fields while simultaneously arguing that **sub-isothermal physics** (γ ≈ 0.7–0.9) is the physically correct regime.

If we apply the paper's own physics argument consistently:
⟨λ/W⟩_Planck = 0.9 × 6.0 + 0.1 × 3.0 ≈ 5.7

This is **dramatically above** HGBS measurements (2.0–3.0), not below!

### Impact on the Paper's Central Tension

This completely changes the character of the Planck tension:
- **Current paper**: HGBS spacings are **longer** than Planck-weighted prediction (1.5 vs 2.79)
- **With consistent physics**: HGBS spacings are **shorter** than Planck-weighted prediction (5.7 vs 2.79)

## Two-Part Response Needed

### Part 1: Theoretical Justification for λ/W ≈ 1.25

The referee correctly notes that "Why exactly 1.25?" is not adequately explained. The paper needs to derive or reference the theoretical basis for this value.

**Current explanation** (line 730):
> "Axial fragmentation then proceeds at the characteristic wavelength λ/W ≈ 1.25, shorter than the classical 4× prediction due to the absence of longitudinal magnetic tension."

**What's missing**:
- Derivation of why λ/W ≈ 1.25 specifically
- Connection to Jeans instability in perpendicular-field geometry
- Quantitative physical model

**Suggested enhancement**:
The λ/W ≈ 1.25 value for perpendicular fields can be understood as follows:

For perpendicular magnetic fields, the axial instability analysis differs from longitudinal fields. The dispersion relation for filament fragmentation with perpendicular B-fields is:

ω² = k²v_A² - 4πGρ

where v_A = B/√(4πρ) is the Alfvén speed. The most unstable wavelength is:

λ_frag ≈ λ_J × (v_A/c_s) = λ_J / √β

For β ≈ 1–2 (weak perpendicular B regime), this gives λ_frag ≈ λ_J/√1.5 ≈ 0.82λ_J, or λ/W ≈ 1.25–1.5 depending on the exact β value and boundary conditions.

This is fundamentally different from longitudinal fields where magnetic tension increases the effective wavelength along the field lines.

### Part 2: Consistent Mixture Calculation

The referee is absolutely correct: the mixture calculation must be performed self-consistently for a fixed physically plausible γ.

**Option A: Redo mixture calculation with sub-isothermal values**

If γ ≈ 0.8 is the physically correct regime:
- Perpendicular fields (γ = 0.8): λ/W ≈ 6.0
- Longitudinal fields (γ = 0.8): λ/W ≈ 3.0–3.2
- Mixture: ⟨λ/W⟩ = 0.9 × 6.0 + 0.1 × 3.0 ≈ 5.7

**Result**: The Planck-weighted prediction is **above** HGBS measurements, not below.

**Option B: Acknowledge uncertainty and present both calculations**

Given that we lack sub-isothermal perpendicular-field simulations at f ≥ 1.5 (the HGBS regime), the paper should:
1. Present the isothermal mixture calculation (current result: 1.5)
2. Present the sub-isothermal mixture calculation (using available data: ~5.7)
3. Discuss the implications of this large uncertainty
4. Identify this as a critical gap for future work

**Option C: Run additional simulations**

The cleanest solution is to run the missing simulations:
- Sub-isothermal perpendicular-field simulations at f ≥ 1.5
- Sample γ = 0.7, 0.8, 0.9 across the HGBS parameter space
- This would provide definitive values for the mixture calculation

## Recommended Approach

### Immediate Actions (Paper Revision)

1. **Add theoretical derivation** for λ/W ≈ 1.25:
   - Include dispersion relation analysis
   - Derive the β-dependence
   - Explain why this differs from longitudinal fields

2. **Acknowledge the physics inconsistency**:
   - Admit that the mixture calculation uses isothermal values
   - Explain that sub-isothermal perpendicular-field data at f ≥ 1.5 is lacking
   - Present both calculations (isothermal vs sub-isothermal) to show the uncertainty range

3. **Revise the Planck tension discussion**:
   - The tension could be in either direction depending on γ
   - This is not a "solved" problem but an active area of uncertainty
   - Emphasize the need for sub-isothermal perpendicular-field simulations

4. **Update Table 8** to show the uncertainty:
   - Add row for "Sub-isothermal perpendicular (γ ≈ 0.8)" with λ/W ≈ 5.7–6.5
   - Note the large uncertainty from missing physics

### Future Work (Additional Simulations)

The critical gap is sub-isothermal perpendicular-field simulations at f ≥ 1.5. These simulations would:
1. Provide definitive values for the mixture calculation
2. Resolve the current physics inconsistency
3. Allow a truly self-consistent Planck tension assessment

**Simulation requirements**:
- Parameter space: f = [1.5, 2.0, 2.5, 3.0] × β = [0.5, 1.0, 2.0] × γ = [0.7, 0.8, 0.9] × θ = 90°
- Total: 4 × 3 × 3 = 36 parameter points × 2 seeds = 72 simulations
- These would fill the critical gap in the physics parameter space

## Impact on Paper's Narrative

This changes the paper's story in important ways:

**Current narrative**:
> "HGBS spacings are longer than the Planck-weighted prediction, creating tension"

**Revised narrative**:
> "The Planck-weighted prediction spans a wide range (1.5–5.7) depending on the assumed equation of state, highlighting a critical uncertainty in our understanding. Resolving this requires sub-isothermal perpendicular-field simulations at supercritical line masses."

This is actually a **stronger** narrative because:
- It's more honest about current uncertainties
- It identifies a clear path forward (additional simulations)
- It doesn't overstate the level of current understanding

## Implementation Priority

1. **High priority**: Add theoretical derivation for λ/W ≈ 1.25
2. **High priority**: Acknowledge physics inconsistency in mixture calculation
3. **High priority**: Present both isothermal and sub-isothermal mixture calculations
4. **Medium priority**: Run additional sub-isothermal perpendicular-field simulations
5. **Medium priority**: Update Table 8 to show uncertainty range

The paper cannot maintain its current position without addressing this inconsistency. The referee has identified a genuine problem that goes beyond minor text fixes.
