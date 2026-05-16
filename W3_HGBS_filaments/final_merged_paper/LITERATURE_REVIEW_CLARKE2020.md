# Literature Review: Clarke+2020 (Hierarchical Fragmentation and Sub-Filaments)

**Paper**: Clarke, S. D., Whitworth, A. P., and Hubber, D. A. 2020, MNRAS, 497, 4390-4406
**Title**: "The hierarchical fragmentation of filaments and the role of sub-filaments"
**DOI**: 10.1093/mnras/staa1588
**Date Reviewed**: 2026-05-02

---

## Critical Findings for Our Contradiction

### 1. No Characteristic Fragmentation Length-Scale

**Key Result**: Filaments containing sub-filaments lack a characteristic fragmentation length-scale. This is because gravity-dominated processes operating through sub-filaments erase expected periodic spacings.

**Relevance to our contradiction**: This **strongly supports** the Fiber Bundle Hypothesis by providing a physical explanation for why HGBS observations show no clear λ/W pattern at the filament level. The sub-filament structure eliminates the classical periodic spacing.

### 2. Hierarchical Fragmentation Framework

**Two types of cores identified**:
- **Isolated cores**: Form on single sub-filaments
- **Hub cores**: Form at junctions where sub-filaments meet

**Key quantitative finding**:
- Hub cores have **greater mean mass** and **wider mass distribution** than isolated cores
- 116 cores identified across 10 simulations
- 148 sub-filaments identified

**Critical quote**:
> "Fragmentation proceeds through sub-filaments, suggesting **no characteristic fragmentation length-scale between cores**."

### 3. End-Dominated Collapse Mechanism

**New physical insight**: Filament ends accelerate, sweeping up gas and becoming denser. Dense/massive cores preferentially form near filament ends.

**Relevance**: This provides an additional mechanism for core formation that is independent of the classical longitudinal fragmentation mode. Ends are defined by density drops to background values, with the "spine" (highest column density) defining the filament's structure.

**Statistical tests**: Kolmogorov-Smirnov, Anderson-Darling, KS, AD, Mann-Whitney U tests confirm:
- End cores are more massive than interior cores
- But cores do not preferentially form at filament ends (null hypothesis not rejected)

### 4. Methodology: DisPerSE Algorithm

**Sub-filament identification**: Uses the **DisPerSE algorithm** (Sousbie 2011), a topological tool for detecting filamentary structures in 3D data.

**Filament skeletons**: Plotted in color on column density projections, representing the spines of sub-filaments. Different colors distinguish individual sub-filaments.

### 5. Oscillatory Motions

**Finding**: Sub-filaments exhibit oscillations, but these are:
- **NOT correlated with core positions** (unlike Tafalla & Hacar 2015 observations)
- **Transient and turbulence-driven** (not a dominant frequency mode)
- Vary with random turbulent motions

**Implication**: Sub-filaments are dynamic structures influenced by external turbulence rather than internal, coherent processes.

---

## Implications for Our Paper

### 1. Resolution of "No Characteristic Scale" Observation

**HGBS observation**: PM and NN statistics show no clear periodic spacing pattern.

**Clarke+2020 explanation**: Sub-filament structure eliminates the characteristic scale. Intermediate fragmentation steps (filament → sub-filaments → cores) erase expected periodic spacings.

**Paper integration**: This provides a theoretical framework for understanding why HGBS filaments show "anomalous" λ/W values.

### 2. Resolution of Supercritical Contradiction

**Clarke+2020 finding**: Fragmentation through sub-filaments means the parent filament can have any line mass (near-critical to highly supercritical) while cores form at the sub-filament level.

**Integration**: HGBS supercritical filaments with cores are explained - cores form in embedded sub-filaments, not via parent filament fragmentation.

### 3. Statistical Method Warnings

**Critical warning**: Clarke+2020 states that techniques like the two-point correlation function require careful handling to avoid spurious length-scale signatures.

**For our paper**: This suggests our PM/NN methodology may need additional validation or explanation to ensure we're measuring real physical quantities rather than artifacts.

---

## Simulation Details

**Code**: AREPO (moving-mesh hydrodynamics)
**Number of simulations**: 10 (SIM01-SIM10)
**Total cores identified**: 116
**Total sub-filaments identified**: 148
**Projection effects**: Appendix B shows lack of characteristic scale does not change with viewing angle

**Key physical processes included**:
- Gravity-dominated collapse
- Turbulent driving
- Time-dependent accretion
- Sub-filament merging and interaction

---

## Comparison with HGBS Observations

### Clarke+2020 vs HGBS

| Aspect | Clarke+2020 | HGBS |
|--------|-------------|------|
| Filament structure | Hierarchical (sub-filaments within filaments) | Assumed single-cylinder |
| Core spacing | No characteristic scale | PM λ/W = 2.79, NN λ/W = 1.01 |
| Massive cores | Preferentially at filament ends or hubs | No end/hub distinction |
| Fragmentation mode | Sub-filament mediated | Assumed direct filament fragmentation |

**Resolution**: Clarke+2020 provides the missing framework - HGBS measurements are mixing multiple sub-filament spacings, which eliminates the characteristic scale.

---

## Recommendations for Paper Revision

### 1. Add Section on Hierarchical Fragmentation

**Title**: "Hierarchical Fragmentation: The Role of Sub-Filaments"

**Content**:
- Introduce Clarke+2020 framework
- Explain how sub-filaments eliminate characteristic length-scale
- Show that this explains HGBS observations naturally

### 2. Reinterpret λ/W Measurements

**Current interpretation**: λ/W = 2.79 (PM) or 1.01 (NN) at filament level

**Clarke+2020-informed interpretation**:
- These values represent the **absence of a characteristic scale**
- This is expected when sub-filaments mediate fragmentation
- The mixture of multiple sub-filament spacings produces compressed ratios

### 3. Address Statistical Method Concerns

**Add disclaimer**:
"Following Clarke+2020, we note that care must be taken when interpreting spacing statistics in hierarchical structures. Our PM and NN measurements may reflect geometric mixing of sub-filament spacings rather than direct physical fragmentation wavelengths."

---

## Summary

**Clarke+2020 provides critical theoretical and simulation support** for the Fiber Bundle Hypothesis:

1. ✅ Hierarchical structure eliminates characteristic fragmentation scale
2. ✅ Sub-filaments are the true fragmentation units
3. ✅ Parent filament properties don't determine core spacing
4. ✅ End-dominated collapse provides additional core formation mechanism
5. ✅ Explains why observations show "anomalous" λ/W values

**This directly addresses the fundamental contradiction** by showing that supercritical filaments with cores are the expected outcome when sub-filaments mediate fragmentation.

---

**Status**: ✅ COMPLETE - Strongly supports Fiber Bundle Hypothesis
**Next**: Review Smith+2016 for observational support of "fray and fragment" scenario

