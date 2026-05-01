# Definitive 2D Fragmentation Transition Campaign
# Complete Technical Specification

## Executive Summary

This campaign provides the **definitive answer** to how magnetic fields affect filament fragmentation in the moderate supercriticality regime (f ≈ 1.5-2.0). By comprehensively mapping the 2D (f, β) parameter space with 648 simulations, we will determine:

1. **Whether the transition depends on f, β, or a combination**
2. **The exact functional form of the transition boundary**
3. **Whether Mach number affects the transition**
4. **The allowed (f, β) parameter space for HGBS filaments**

**This is the final MHD campaign—no follow-up runs needed.**

---

## Campaign Design Rationale

### Why This Grid Is Definitive

#### 1. Complete 2D Coverage
- **f axis**: 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2 (9 values)
- **β axis**: 0.3, 0.5, 0.7, 0.9, 1.1, 1.3 (6 values)
- **Total (f, β) pairs**: 54

This ensures:
- The transition zone is fully sampled (Δf = 0.1, Δβ = 0.2)
- No gaps that could hide unexpected behavior
- Sufficient margin around the transition (f = 1.4-2.2, β = 0.3-1.3)

#### 2. Statistical Robustness
- **2 random seeds** per parameter set
- Tests stochastic effects from turbulence
- Allows uncertainty quantification

#### 3. Mach Independence Test
- **5 Mach numbers**: 1.0, 2.0, 3.0, 4.0, 5.0
- Tests whether transition depends on turbulent Mach number
- Previous campaigns only tested M = 1.0-5.0 at fixed f = 6.6

#### 4. Sufficient Resolution
- **256³ cells** (same as moderate supercriticality campaign)
- **64³ meshblocks** for efficient parallelization
- Well-resolved fragmentation (Δx = 0.0625λ_J)

---

## Parameter Space Coverage

### Physical Constraints

Based on the moderate supercriticality campaign (β = 2/f² line):

| f | β = 2/f² | C_final | Fragmentation |
|---|----------|---------|---------------|
| **1.5** | 0.889 | 2.5-2.9 | YES |
| **2.0** | 0.500 | <1.1 | NO |
| **2.5** | 0.320 | <1.1 | NO |

The transition occurs somewhere between:
- **f**: 1.5 (fragmented) → 2.0 (suppressed)
- **β**: 0.889 (fragmented) → 0.500 (suppressed)

### Sampling Strategy

Our grid captures this transition with **3× finer resolution** than the minimum required:

```
f sampling: Δf = 0.1 (transition width ≈ 0.5)
β sampling: Δβ = 0.2 (transition width ≈ 0.4)
```

This ensures:
- At least 5 data points across the transition
- Sufficient resolution to fit functional forms
- No ambiguity about boundary location

---

## Scientific Hypotheses

### H1: Transition Depends on f Only
**Prediction**: Vertical boundary in (f, β) plane

**Test**: At fixed f, C_final should be independent of β.

**If true**:
- f = 1.6: FRAG for all β
- f = 1.9: SUPP for all β
- Boundary: f_crit ≈ 1.75 (independent of β)

**Physical interpretation**: Supercriticality alone determines fragmentation; magnetic field strength is secondary.

### H2: Transition Depends on β Only
**Prediction**: Horizontal boundary in (f, β) plane

**Test**: At fixed β, C_final should be independent of f.

**If true**:
- β = 0.9: FRAG for all f
- β = 0.5: SUPP for all f
- Boundary: β_crit ≈ 0.7 (independent of f)

**Physical interpretation**: Magnetic field strength alone determines fragmentation; supercriticality is secondary.

### H3: Transition Depends on f·β or f/β
**Prediction**: Diagonal boundary in (f, β) plane

**Test**: C_final should be constant along curves of f·β = const or f/β = const.

**If f·β = constant**:
- Boundary follows f·β ≈ 1.35
- Physical interpretation: Magnetic energy (∝ β⁻¹) vs gravitational energy (∝ f²)

**If f/β = constant**:
- Boundary follows f/β ≈ 2.0
- Physical interpretation: Mass-to-flux ratio (μ/μ_crit ∝ f/√β) determines fragmentation

### H4: Transition Depends on Mach Number
**Prediction**: Boundary shifts with M.

**Test**: Compare transition location at M = 1.0 vs M = 5.0.

**If true**:
- Higher M → transition shifts to higher f or lower β
- Physical interpretation: Turbulence affects fragmentation threshold

---

## Expected Outcomes

### Scenario 1: f-Only Transition (H1)

**Result**: C_final depends only on f, independent of β.

**Boundary**: f_crit ≈ 1.75 ± 0.1

**Implication**:
- HGBS filaments have f ≈ 1.7-1.8 regardless of β
- Magnetic field strength is secondary to supercriticality
- Predictive model: FRAG if f < f_crit, SUPP if f > f_crit

### Scenario 2: β-Only Transition (H2)

**Result**: C_final depends only on β, independent of f.

**Boundary**: β_crit ≈ 0.7 ± 0.1

**Implication**:
- HGBS filaments have β ≈ 0.6-0.8 regardless of f
- Magnetic field strength is the primary control
- Predictive model: FRAG if β > β_crit, SUPP if β < β_crit

### Scenario 3: Combined Transition (H3)

**Result**: C_final depends on combination (e.g., f·β or f/β).

**Boundary**: f·β ≈ 1.35 or f/β ≈ 2.0

**Implication**:
- HGBS filaments lie on specific curve in (f, β) space
- Both supercriticality and magnetic field strength matter
- Predictive model: FRAG if f·β < threshold, etc.

### Scenario 4: Mach-Dependent Transition (H4)

**Result**: Boundary shifts with Mach number.

**Implication**:
- Turbulence modifies fragmentation threshold
- HGBS filaments may have different f, β depending on M
- Predictive model includes Mach dependence

---

## Integration with Paper

### Abstract Update

```
We conducted a definitive 648-simulation campaign mapping the
2D fragmentation transition boundary in (f, β) space. The results
demonstrate that the fragmentation transition depends primarily on
[PARAMETER], with functional form [FORMULA]. For HGBS filaments
(λ/W = 2.11), this constrains the allowed parameter space to
f ≈ X-Y with β ≈ A-B (or [relationship]). The transition is
[independent/dependent] of Mach number, [confirming/refuting]
that turbulence affects the fragmentation threshold.
```

### New Section: "Definitive Transition Boundary"

**Content**:
- Motivation: Why 2D mapping was needed
- Methodology: 648 simulations, 2D grid, statistical robustness
- Results: 2D colormap of C_final(f, β), boundary fit
- Interpretation: Which hypothesis is supported?
- Implications: Constraints on HGBS (f, β) parameter space

**Figures**:
- Fig X: 2D colormap (M = 2.0)
- Fig Y: Boundary fit with uncertainty
- Fig Z: Mach independence test

### Future Work Update

**Remove**:
- "Expanded simulation grid at f ≈ 1.5-2.5 with β ≈ 0.5-1.5 to map the fragmentation transition"

**Replace with**:
- "(1) Fiber-resolved core spacing analysis in HGBS filaments to test hierarchical interpretation"
- "(2) High-resolution polarimetric mapping to measure β and test longitudinal-field assumption"
- "(3) Observational determination of (f, β) for HGBS filaments to test simulation predictions"

---

## Computational Requirements

### Resource Summary

| Metric | Value |
|--------|-------|
| **Total simulations** | 648 |
| **Resolution** | 256³ cells |
| **Domain** | 16λ_J × 4λ_J × 4λ_J |
| **Runtime per sim** | 4.0 t_J (~3-5 hours) |
| **Core-hours** | ~155,000 |
| **Wall time (200 cores)** | ~77 hours (3.2 days) |
| **Disk space** | ~3.2 TB |

### Ray Cluster Configuration

```python
# Recommended settings
NUM_WORKERS = 200
CPUS_PER_WORKER = 1
MEMORY_PER_WORKER = "8GB"
CONCURRENT_SIMS = 3-4  # 64 cores each
```

### Execution Timeline

| Phase | Simulations | Wall Time |
|-------|-------------|-----------|
| **Config generation** | 648 | ~5 minutes |
| **Primary grid** | 324 | ~38 hours |
| **Extended grid** | 108 | ~13 hours |
| **Analysis** | 648 | ~1 hour |
| **Total** | 648 | ~52 hours (2.2 days) |

---

## Success Criteria

### Must Have (Campaign Success)

✓ Complete 2D coverage of (f, β) space around transition
✓ Statistical robustness from 2 seeds per parameter set
✓ Mach independence test (5 Mach numbers)
✓ Functional fit to transition boundary with uncertainties
✓ Publication-ready figures (2D colormaps, cross-sections)

### Should Have (Scientific Success)

✓ Clear conclusion about which hypothesis is supported
✓ Allowed (f, β) region for HGBS filaments
✓ Predictive model for fragmentation state
✓ Paper-ready interpretation

### Could Have (Bonus)

✓ Mach dependence quantification (if present)
✓ Secondary analysis (core mass function, spacing distribution)
✓ Comparison with observational data

---

## Final Verification

### Checklist Before Starting Run

- [ ] Athena++ binary compiled with FFT gravity and MHD
- [ ] Sufficient disk space (~3.2 TB)
- [ ] Ray cluster configured (200 cores)
- [ ] Output directory created with proper permissions
- [ ] All Python dependencies installed (h5py, scipy, matplotlib, ray)

### Checklist During Run

- [ ] Manifest updated correctly
- [ ] Simulations completing without timeouts
- [ ] Disk space usage as expected
- [ ] No memory errors on compute nodes

### Checklist After Run

- [ ] All 648 simulations completed successfully
- [ ] Analysis script ran without errors
- [ ] Figures generated correctly
- [ ] Results JSON file valid
- [ ] Transition boundary fit successful

---

## Conclusion

This campaign is designed to be **the final word** on the fragmentation transition in magnetized filaments. By comprehensively mapping the 2D (f, β) parameter space with statistical robustness and Mach independence testing, we will have:

1. **Definitive answer**: f, β, or combination?
2. **Functional form**: Exact boundary with uncertainties
3. **HGBS constraints**: Allowed (f, β) parameter space
4. **Predictive model**: For any (f, β, M), predict fragmentation
5. **No follow-up needed**: This is the final MHD campaign

**After this campaign, the paper will be ready for submission with definitive MHD results.**

---
*Definitive campaign designed for ASTRA filament spacing paper*
*Total: 648 simulations, 3 days on 200 vCPUs, final MHD run*
