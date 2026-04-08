# PEER REVIEW: Universal Core Spacing in Molecular Cloud Filaments

**Reviewer**: G. J. White (self-review)
**Date**: 8 April 2026
**Recommendation**: **Major Revisions Required**

---

## SUMMARY

This paper presents a comprehensive analysis of core spacing across all 9 HGBS regions (5,411 cores) and attempts to explain the observed 2× filament width spacing through linear perturbation theory and 3D simulations. The observational analysis is thorough and the 2D linear theory results are compelling. However, the 3D simulation section requires significant updates based on new results.

---

## MAJOR ISSUES (Must Address)

### 1. 3D Simulation Results Section is Severely Outdated

**Current text (Section 7.3)**: Claims "no cores formed" in 1 Myr simulations

**New reality**: Strategic validation (17 simulations, 3-5 Myr) shows:
- All simulations formed cores successfully
- Spacings: 0.062-0.093 pc (60-70% smaller than observed)
- Best match: 0.093 pc (56% error)

**Required action**: Completely rewrite Section 7.3 to reflect actual 3D results. The current text is misleading.

### 2. Missing Honest Assessment of 3D Limitations

**Current text (Section 8.2.3)**: "The 3D framework provides a validated methodology"

**Problem**: Our 3D simulations show 60-70% errors. This is NOT a validated methodology for quantitative predictions.

**Required action**: Clearly state that 3D simulations are qualitative only, demonstrating core formation but not yet quantitative accuracy.

### 3. Contradictory Trend Statements

**Current text (Section 3.3)**: "Quiescent regions (Taurus, CRA): Lower pressure, longer filaments → smaller spacings"

**Problem**: CRA (0.215 pc) is larger than the mean, not smaller. The trend is more complex.

**Required action**: Rephrase to accurately reflect the data: "Quiescent regions show mixed behavior, with Taurus at the low end and CRA near the mean."

### 4. Missing 3D Results Discussion

**Current text**: No discussion of why 3D spacings are 60-70% too small

**Required action**: Add discussion in Section 8 explaining:
- Simplified solver lacks advection
- Small domain (0.4 pc) constrains core formation
- Non-linear effects not captured
- This explains why 2D linear theory remains superior

---

## MODERATE ISSUES (Should Address)

### 5. Placeholder DOI

**Current text**: `https://doi.org/10.5281/zenodo.XXXXXX`

**Required action**: Either remove or change to: "Code will be made available upon acceptance"

### 6. Missing Figure References

**Current text**: Mentions Figure 1 but no figure included

**Required action**: Either add figure or remove figure references

### 7. Unclear Uncertainty Accounting

**Current text**: Weighted mean uncertainty is 0.007 pc (3%) but individual regions have 10-15% errors

**Required action**: Add sentence explaining: "The weighted mean uncertainty is smaller than individual measurements because random errors decrease as √N when combining 638 independent measurements."

### 8. Abstract Structure

**Current text**: Numbered list in abstract (unconventional)

**Suggestion**: Convert numbered list to flowing text for better readability

### 9. Table 1 Missing Data

**Current text**: Orion B shows "--" for prestellar fraction

**Required action**: Either add data or add footnote explaining why unavailable

---

## MINOR ISSUES (Optional but Recommended)

### 10. Consistent Precision
- Paper uses both "2×" and "2.13×" - be consistent about when to use rounded vs exact values

### 11. Missing Projection Effect in Table 2 Caption
- Add: "Uncertainties are measurement errors only; systematic ~21% projection uncertainty affects all regions equally"

### 12. Weak Conclusion Sentence
- Last sentence of conclusions is vague. Consider: "This work provides the most complete HGBS filament analysis to date and establishes 2D linear perturbation theory as the current best method for predicting core spacing."

---

## STRENGTHS (Keep These)

1. **Comprehensive sample**: All 9 HGBS regions with 5,411 cores
2. **W3 inclusion**: Important high-pressure test case
3. **2D linear theory**: Excellent agreement (<1% discrepancy)
4. **Region-by-region matching**: Demonstrates environmental dependence
5. **Complete methodology**: Code and parameters fully documented

---

## RECOMMENDED REVISION STRUCTURE

1. **Update Section 7 (3D Simulations)** with strategic validation results
2. **Add Section 8.4**: "Why 2D Linear Theory Outperforms 3D Simulations"
3. **Revise Abstract**: Convert numbered list to text
4. **Update Conclusion**: Emphasize 2D theory as current best method
5. **Fix all contradictory statements**
6. **Remove placeholder DOIs**

---

## ESTIMATED REVISION TIME

- Major text updates: 2-3 hours
- New section writing: 1 hour
- Proofreading: 1 hour
- **Total**: 4-5 hours

---

## FINAL ASSESSMENT

The paper has strong observational and 2D theoretical components. The main weakness is the outdated 3D simulation section, which currently misrepresents the results. With the recommended revisions, this paper will be suitable for submission to MNRAS or A&A.

**Recommendation**: Major revisions required, but paper is salvageable and will be strong after updates.
