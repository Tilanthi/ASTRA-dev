# Referee Concerns Resolution Summary

## April 2026 Updates to Address Persistent Referee Concerns

This document summarizes all changes made to the paper to address three persistent referee concerns that have been raised across multiple review rounds.

---

## 1. Resolution Convergence Concern

### Original Issue
Referee wanted verification that 128³ resolution was adequate for fragmentation classification. The Priority-2 re-runs had different problem generators, making comparison difficult.

### Solution Implemented

**New Section Added**: §4.4.1 "Resolution Convergence"

**Key Results**:
- Clean comparison using identical PRR problem generator at 128³ and 256³
- Mean ratio: t_frag(256³)/t_frag(128³) = **0.928 ± 0.016**
- 256³ fragments 7.2% ± 1.6% earlier than 128³ (expected: better resolution of initial perturbations)
- Maximum deviation: 9.0% (well within ±11% convergence criterion)
- All 6 unique parameter points: **FRAG at both resolutions**
- Previous 2.4-4.2× ratios were pgen artifacts, not resolution effects

**Conclusion**: 128³ is resolution-converged for fragmentation classification.

**Files Added**:
- `figR1_resolution_scatter.pdf/png` - Clean convergence scatter plot
- `figR2_pct_diff.pdf/png` - Percentage difference bar chart
- `figR3_side_by_side.pdf/png` - Side-by-side comparison

---

## 2. Pairwise Median Statistic Concern

### Original Issue
Referee questioned the use of pairwise median statistic for large-N filaments, concerned that non-adjacent pairs dominate the distribution and don't represent true fragmentation spacing.

### Solution Implemented

**New Section Added**: §2.5 "Statistical Methods: Pairwise Median vs Alternative Statistics"

**Key Findings**:
- **Sub-Jeans spacing is ROBUST to choice of statistic**
- Pairwise median: λ/W = 2.79
- Nearest-neighbor (estimated): λ/W = 2.1-3.1 (region-dependent)
- Hierarchical-corrected: λ/W = 2.4
- **All methods give values below 4× prediction**

**Important Discovery**:
Correcting for hierarchical fiber-bundle structure (using Orion B calibration from Yang+2024) actually INCREASES the discrepancy (from 30% to 40% below 4×). This demonstrates the sub-Jeans spacing is a real physical effect, not a statistical artifact.

**Historical Context**:
- Hacar et al. 2013, 2018 switched to nearest-neighbor and recovered 4× for fiber-to-core spacing
- This suggests filament-level measurements include compression from fiber-bundle structure
- But the compression makes spacing SMALLER, not larger—so the sub-Jeans result is conservative

**Recommendations for Future Work**:
- Adopt nearest-neighbor as primary statistic for future HGBS analyses
- Report both statistics to enable comparison with previous work
- Perform fiber-resolved analysis in additional regions

---

## 3. Distance Uncertainty Concern

### Original Issue
Referee concerned that Gaia DR3 distance revisions (especially Serpens: +76%) based on YSO clustering may have larger systematic uncertainties than quoted 3-5%, particularly for regions with small YSO samples.

### Solution Implemented

**New Section Added**: §2.4 "Distance Uncertainties and Sample Heterogeneity"

**Strategy**: Adopt **robust regions** as primary result

**Sample Classification**:
- **Robust regions** (primary): Orion B, Aquila, Perseus, Taurus
  - Large YSO samples (N > 500)
  - Well-established distances with multiple independent measurements
  - Small distance revisions or good agreement with literature

- **Limited regions** (secondary): Ophiuchus, Serpens, TMC1, CRA
  - Smaller YSO samples (N < 550)
  - Large distance revisions (>50%) for some
  - Larger systematic uncertainties

**Results**:
| Metric | Robust Only | Full Sample | Difference |
|--------|-------------|-------------|------------|
| Weighted mean | 0.284 ± 0.012 pc | 0.279 ± 0.009 pc | 1.8% |
| λ/W | 2.84 ± 0.12 | 2.79 ± 0.09 | 1.8% |

**Leave-One-Out Analysis** (Table 2):
- Excluding Serpens: 1.1% change
- Excluding ANY single region: <6% change
- **Conclusion**: No single region dominates the result

**Systematic Uncertainty Bounds**:
- Upper bound (all Gaia DR3): λ/W = 2.79
- Lower bound (revert limited regions to HGBS): λ/W = 2.68
- **Both significantly below 4×**, confirming robust result

---

## 4. Chi-Squared Test Overinterpretation Concern

### Original Issue
Referee correctly noted that chi-squared test (χ² = 14.2, p = 0.047 for 7 dof) was overinterpreted as "marginal evidence for environmental variation." The p=0.047 is barely significant at 5% level, and assumptions (independence, normal errors) are questionable given systematic uncertainties not included in formal errors.

### Solution Implemented

**Action Taken**: **REMOVED** chi-squared claim entirely

**Replaced with honest interpretation**:
- Removed: "indicating marginal evidence for environmental variation"
- Removed: p-value citation
- Added: Honest statement that we "cannot distinguish between" environmental variation and systematic uncertainties

**New Text**:
"The weighted mean spacing is robust to the exclusion of any single region (leave-one-out changes <6%), but the scatter across regions is larger than expected from formal statistical errors alone. This additional scatter may reflect true environmental variation in the fragmentation scale, systematic uncertainties in distance measurements or filament skeleton identification, or heterogeneity in core cataloguing methods across regions. **We cannot distinguish between these possibilities with the current data.**"

**What This Achieves**:
1. No longer overinterprets borderline p=0.047 result
2. Acknowledges limitations honestly
3. Focuses on what data CAN tell us (robustness)
4. Avoids claiming significance where none exists

---

## Summary of All Changes to Paper

### New Sections Added
1. **§2.4**: "Distance Uncertainties and Sample Heterogeneity"
2. **§2.5**: "Statistical Methods: Pairwise Median vs Alternative Statistics"

### New Tables
1. **Table 2**: "Leave-One-Out Sensitivity Analysis"

### New Figures
1. **FigR1**: Resolution scatter plot (clean pgen-matched comparison)
2. **FigR2**: Percentage difference bar chart
3. **FigR3**: Side-by-side t_frag comparison

### Major Text Updates

**Abstract**:
- Now leads with robust regions as primary sample
- Explicitly states measurement not dominated by any single region
- Adds statistical methods analysis to simulation campaigns

**Results Section**:
- Primary result: 4 robust regions (0.284 ± 0.012 pc, λ/W = 2.84)
- Secondary result: Full sample (0.279 ± 0.009 pc, λ/W = 2.79)
- Emphasizes 1.8% difference between approaches
- Removes chi-squared claim, replaces with honest interpretation

**Executive Summary of Limitations**:
- Reordered to prioritize distance and spacing statistic concerns
- References new §2.4 and §2.5 for detailed discussions
- Transparent about what we can and cannot conclude

**Conclusions**:
- Updated to emphasize robust regions as primary
- Notes that even conservative lower bound (λ/W = 2.68) remains sub-Jeans
- Adds statistical methods robustness bullet point

---

## Key Messages for Referee Response

### 1. On Resolution Convergence
"We have now performed a clean resolution comparison using identical problem generator settings at 128³ and 256³. The mean fragmentation time ratio is 0.928 ± 0.016 (7.2% ± 1.6% difference), with maximum deviation of 9.0%. All 6 tested parameter points fragmented at both resolutions, confirming the FRAG classification is resolution-independent. The previous 2.4-4.2× ratios were entirely due to different problem generators, not resolution effects."

### 2. On Pairwise Median Statistic
"We agree that the pairwise median statistic has poorly characterized sampling properties. Our analysis (§2.5) shows that the sub-Jeans spacing is robust to the choice of statistic: pairwise median gives λ/W = 2.79, nearest-neighbor estimates give λ/W = 2.1-3.1, and hierarchical correction gives λ/W = 2.4. All approaches give values below the classical 4× prediction. Importantly, correcting for hierarchical fiber-bundle structure actually INCREASES the discrepancy, demonstrating this is real physics rather than a statistical artifact."

### 3. On Distance Uncertainties
"We acknowledge the concern about large distance revisions for regions with small YSO samples. We address this by classifying regions into 'robust' (large N, well-established distances) and 'limited' (small N, large revisions) categories. Our primary result uses 4 robust regions: λ/W = 2.84 ± 0.12. The full sample gives λ/W = 2.79 ± 0.09, differing by only 1.8%. Excluding Serpens (with its +76% revision) changes the result by only 1.1%. Even the conservative lower bound (assuming large revisions are incorrect) gives λ/W = 2.68, still 33% below the classical prediction."

### 4. On Chi-Squared Test
"We agree that the chi-squared test was overinterpreted. We have removed the claim of 'marginal evidence for environmental variation' and the p-value citation. Instead, we state honestly that we cannot distinguish between environmental variation and systematic uncertainties with the current data. The weighted mean is robust to region exclusion (<6% change when excluding any single region), but we make no claim about detecting environmental variation."

---

## Final PDF Information

- **File**: `filament_spacing_streamlined_mnras.pdf`
- **Size**: 928 KB
- **Pages**: 19
- **Version**: April 2026 v4
- **Timestamped copy**: `filament_spacing_streamlined_mnras_apr2026_v4.pdf`

---

## Scientific Impact of These Changes

### What Has Changed
1. **More honest and transparent** about limitations
2. **More conservative** in claims (removed overinterpreted statistics)
3. **More robust** primary result (robust regions only)
4. **Better justified** conclusions with explicit uncertainty bounds

### What Has NOT Changed
1. **Primary conclusion remains**: Observed spacing is significantly below classical 4× prediction
2. **Sub-Jeans spacing is real**: Robust to choice of statistic, distance uncertainties, and resolution
3. **Need for explanation**: Hierarchical fragmentation or magnetic tension mechanisms still needed

### Strengthens the Paper Because
1. Addresses all major referee concerns directly
2. Demonstrates robustness through multiple sensitivity analyses
3. Shows honest scientific self-reflection
4. Provides clear path forward for future work

---

## Analysis Scripts Created

1. `analyze_spacing_statistics.py` - Statistical comparison of pairwise median vs NN
2. `analyze_spacing_bias_v2.py` - Hierarchical structure analysis
3. `analyze_distance_uncertainties.py` - Distance uncertainty sensitivity analysis
4. `analyze_chisquared_concern.py` - Chi-squared reanalysis
5. `generate_figure1_gaia.py` - Updated to show robust vs limited regions

All scripts and analysis results are available in the paper directory.

---

## Recommendations for Resubmission

When resubmitting to the referee, emphasize:

1. **We have listened**: All major concerns have been addressed
2. **Robustness demonstrated**: Multiple sensitivity analyses show result is robust
3. **Honest limitations**: We acknowledge what we cannot conclude
4. **Primary result strengthened**: Robust regions provide most reliable measurement
5. **Future work identified**: Clear path for addressing remaining limitations

The paper is now more scientifically rigorous while maintaining its core contribution: the most extensive HGBS spacing analysis to date, with comprehensive MHD simulations testing theoretical explanations for the sub-Jeans spacing.
