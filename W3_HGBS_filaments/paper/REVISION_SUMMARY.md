# REVISION SUMMARY

**Paper**: Universal Core Spacing in Molecular Cloud Filaments: Complete HGBS Analysis with Linear Theory Validation

**Date**: 8 April 2026
**Status**: ✅ MAJOR REVISIONS COMPLETE

---

## CHANGES MADE

### 1. Updated Title (Changed)
- **Old**: "...with Linear Theory and 3D Simulation Framework"
- **New**: "...with Linear Theory Validation"
- **Reason**: Reflects that 3D simulations are not yet successful; 2D linear theory is the validated method

### 2. Revised Abstract (Major Rewrite)
- **Old**: Numbered list format, claimed "3D simulation framework provides complete methodology"
- **New**: Flowing text format, honest assessment:
  > "While our 3D simulations successfully demonstrate core formation, they produce spacings 60--70\% smaller than observed, revealing important limitations of simplified solvers. This establishes 2D linear perturbation theory as the current most accurate method..."

### 3. Fixed Environmental Trend Description (Section 3.3)
- **Old**: "Quiescent regions (Taurus, CRA): Lower pressure, longer filaments → smaller spacings"
- **New**: "The 20% variation in spacing (0.188--0.225 pc) correlates with environment, though not monotonically"
- **Added**: Actual data showing the non-monotonic relationship

### 4. Added Uncertainty Explanation (Section 3.4)
- **New paragraph**: "The uncertainties reported...are measurement errors derived from the standard error of the mean for each region. The weighted mean uncertainty (0.007 pc) is smaller than individual measurements because random errors decrease as √N when combining 638 independent measurements across all regions."

### 5. Completely Rewrote Section 7 (3D Simulations)
- **Old Section 7.3**: "no cores formed" in 1 Myr simulations
- **New Section 7.3**: Full results from strategic validation:
  - Table 4 with actual 3D results (0.062-0.093 pc, all 56-71% error)
  - Honest assessment of limitations
  - No false claims of success

### 6. Added New Section 7.4: "Why 3D Simulations Underpredict Spacing"
- **Content**: Explains that simplified solver lacks:
  - Advection (crucial for mass transport)
  - Large enough domain
  - Non-linear effects
  - Proper physics

### 7. Added New Section 8.2.3: "Why 2D Linear Theory Outperforms 3D Simulations"
- **Content**: Clear statement that 2D theory is superior because it includes the physical mechanisms that 3D simplified solver lacks
- **Key sentence**: "This establishes 2D linear perturbation theory as the current most accurate method for predicting core spacing in molecular cloud filaments."

### 8. Updated Conclusions
- **Old**: Vague statement about "3D framework provides validated methodology"
- **New**: Specific acknowledgment:
  > "Simplified 3D simulations demonstrate core formation but underpredict spacing by 60--70%"
  > "This work establishes 2D linear perturbation theory as the current most accurate method"

### 9. Fixed DOI Placeholder
- **Old**: `https://doi.org/10.5281/zenodo.XXXXXX`
- **New**: "Code will be made available upon acceptance"

### 10. Removed Simplified Grid Description
- **Old**: "Grid: 64×16×16 cells" (asymmetric)
- **New**: "Grid: 64×64×64 cells (262,144 cells total)" (symmetric, matches actual runs)

### 11. Improved Conclusion Sentence
- **Old**: Generic statement about "most complete HGBS filament analysis"
- **New**: Specific claim about 2D linear theory being best method:
  > "This work establishes 2D linear perturbation theory as the current most accurate method for predicting core spacing in molecular cloud filaments, while providing a validated methodology and roadmap for future 3D validation efforts."

### 12. Removed Over-Optimistic 3D Claims
Throughout the paper, removed statements like:
- "3D framework provides validated methodology"
- "First step toward definitive numerical validation" (changed to "demonstration of core formation")
- Claims that 3D would work with more resources (changed to honest assessment of limitations)

---

## PAPER STATISTICS

| Metric | Value |
|--------|-------|
| Pages | 14 |
| File size | 295 KB |
| Tables | 5 |
| Sections | 10 |
| References | ~10 |

---

## KEY SCIENTIFIC CLAIMS (Now Accurate)

1. **Observations**: 0.213 ± 0.007 pc spacing across all 9 HGBS regions (5,411 cores) ✅
2. **2D Linear Theory**: Predicts 0.213 pc (<1% error) ✅
3. **3D Simulations**: Demonstrate core formation but underpredict spacing by 60-70% ✅
4. **Primary Conclusion**: 2D linear theory is the current most accurate method ✅

---

## PEER REVIEW STATUS

**Before revision**: Major issues (misleading 3D claims, contradictory statements)
**After revision**: ✅ **All major issues addressed**

The paper now:
- ✅ Accurately reports 3D simulation results
- ✅ Explains why 3D underpredicts spacing
- ✅ Establishes 2D linear theory as superior method
- ✅ Provides honest roadmap for future 3D work
- ✅ Ready for submission to MNRAS or A&A

---

## FILES CREATED

1. `PEER_REVIEW_COMMENTS.md` - Detailed peer review
2. `filament_spacing_revised.tex` - Revised LaTeX source
3. `filament_spacing_revised.pdf` - Revised paper (14 pages, 295 KB)
4. `REVISION_SUMMARY.md` - This document
