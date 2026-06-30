# Section 4 Restructuring Plan for Option B

## Current Structure (Problematic)

```
Section 4: MHD SIMULATIONS (line 291)
├── 4.1 Campaign Overview (line 293)
├── 4.2 Simulation Methodology (line 320)
├── 4.3 Critical Negative Result: Regime-Dependent Fragmentation Behavior (line 337)
├── 4.4 Definitive Transition Campaign (DTC) (line 352)
├── 4.5 Simulation Validation (line 381)
├── 4.6 Three-Regime Framework (line 431)
├── 4.7 Supercritical Filament Campaign (line 449)
├── 4.8 Gravity-Dominated Regime (line 572)
├── 4.9 Field Geometry Campaign (line 578)
├── 4.10 Additional Campaigns (289 simulations, April--May 2026) (line 646)
│   ├── [Multiple sub-subsections]
├── [June 2026 campaigns without clear subsection header]
│   ├── [Campaigns P1-P4, THEO-1, THEO-4]
│   ├── 4.11.7 RTC (line 756) ← **PRIMARY RESULT, BURIED HERE**
│   └── 4.11.8 Rigid Cylinder (line 785)
```

## New Structure (Proposed)

```
Section 4: MHD SIMULATION RESULTS
├── 4.1 Overview and Methodology (condensed)
├── 4.2 THE PRIMARY RESULT: RTC Null Result (MOVED FROM 4.11.7)
│   ├── Physical ISM turbulence, free boundaries, 1,200 simulations
│   ├── Zero HGBS matches - all λ/W ≥ 3.75
│   ├── Implications: ideal MHD inadequate
│   └── [RTC figure - make prominent]
├── 4.3 Critical Negative Result: Regime-Dependent Fragmentation Behavior
│   ├── Near-critical: beading (measurable λ/W)
│   ├── Supercritical: radial collapse (no λ/W measurement)
│   └── This creates extrapolation gap
├── 4.4 Field Geometry: The Perpendicular-Field Crisis
│   ├── 90% of filaments should have λ/W ≈ 1.25 (or ≈2.0 width-normalized)
│   ├── Below observed values
│   └── [Field geometry figures - condense from 5 to 2]
├── 4.5 Supercritical Fragmentation Timescales
│   ├── 1/t_frag ∝ f^0.39
│   ├── Independent of β and M
│   └── [Condensed t_frag figure]
├── 4.6 Definitive Transition Campaign (DTC)
│   ├── Transition boundary mapping
│   ├── Timeout artifact resolution
│   └── [Move detailed heatmaps to appendix]
├── 4.7 Three-Regime Framework
│   ├── Magnetically subcritical / regulated / thermally dominated
│   └── [Regime diagram]
├── 4.8 Boundary Condition Sensitivity: Rigid Cylinders
│   ├── Reflecting walls produce HGBS-compatible spacing
│   ├── But are unphysical
│   └── [Rigid cylinder figure]
├── 4.9 Validation and Numerical Convergence (CONDENSED)
│   ├── Resolution, IC, EOS validation
│   ├── [Move detailed figures to appendix]
├── 4.10 Additional Campaigns Summary (CONDENSED)
│   ├── Brief (~1 page) summary
│   └── [Move full details to appendix]
```

## Content Moves Required

### Major Moves

1. **RTC content (lines 756-784)** → Move to new 4.2
2. **Rigid cylinder content (lines 785-812)** → Move to new 4.8
3. **Field geometry content (lines 578-645)** → Move to new 4.4 (earlier, emphasized)

### Condensations

1. **DTC (lines 352-380)** → Condense, move heatmaps to appendix
2. **Validation (lines 381-430)** → Condense to ~1 page, move figures to appendix
3. **Additional campaigns (lines 646-755)** → Summarize in ~1 page, move details to appendix
4. **Supercritical campaign (lines 449-571)** → Keep t_frag results, condense methodology

### Cross-Reference Updates

- Update all `\ref{sec:rtc}` to point to new 4.2 location
- Update all `\ref{sec:rigid_cylinder}` to point to new 4.8 location
- Update Discussion references to RTC

## Implementation Steps

1. [ ] Extract RTC content (lines 756-784)
2. [ ] Create new 4.2 subsection with RTC content
3. [ ] Extract Rigid cylinder content (lines 785-812)
4. [ ] Prepare for new 4.8 placement
5. [ ] Extract Field geometry content (lines 578-645)
6. [ ] Prepare for new 4.4 placement
7. [ ] Condense DTC section
8. [ ] Condense Validation section
9. [ ] Condense Additional campaigns
10. [ ] Update all cross-references
11. [ ] Verify section numbering

## Estimated Impact

- **Page reduction**: Section 4 from ~16 pages to ~10-12 pages (-25% to -38%)
- **Focus improvement**: Primary result (RTC) moves from line 756 to early position
- **Reader experience**: Clear narrative arc instead of campaign-by-campaign listing

## Figure Changes

### Figures to Emphasize
- RTC λ/W distribution → Make larger, place prominently in new 4.2
- Perpendicular vs longitudinal → Keep in new 4.4
- Rigid cylinder summary → Keep in new 4.8

### Figures to Move/Remove
- DTC stable ridge re-run → Appendix
- Resolution convergence → Appendix
- IC sensitivity → Appendix
- Multiple t_frag heatmaps → Remove/reduce
- Adiabatic density profiles → Appendix

---

**Status**: Plan created, ready for implementation
**Next step**: Begin content extraction and reorganization
