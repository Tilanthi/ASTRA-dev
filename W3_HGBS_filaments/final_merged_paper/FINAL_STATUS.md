# Paper Revisions Complete - Final Status

## ✅ All Tasks Completed

### Referee Concerns Addressed

**Concern 1: Rigid Cylinder BC** ✓
- Added explicit caveat box explaining artificial geometry
- Distinguished clearly between CAN/CANNOT show
- Added note about physical scatter matching HGBS (21% CV)

**Concern 2: Perpendicular-Field Gap (29%)** ✓
- Strengthened quantitative analysis of hourglass morphology
- Acknowledged that simple geometric interpolation widens gap
- Listed alternative mechanisms (turbulent pressure, accretion, observational bias)

**Concern 3: 0.33% Matching Rate** ✓
- **Critical correction**: Changed from 4 matches to 0 matches in HGBS window
- All λ/W values are ≥ 3.75, outside HGBS bounds [2.52, 3.08]
- Added contrast with rigid cylinder positive result
- Strengthened Interpretation B discussion

**Concern 4: Width Normalisation** ✓
- Added new subsection on Gaussian vs. Ostriker profiles
- Quantified expected magnitude (~5-10% effect)
- Clarified uncertainty (11.9% 1σ vs. 31% full range)
- Listed required future work

**Concern 5: Power Law Exponent** ✓
- Added T2 campaign decomposition with explicit equations
- Quantified: α_hydro = 0.452, Δα_hydro = 0.048 (44%)
- Quantified: Δα_MHD = 0.062 (56%)

### Page Reduction ✓
- **Before**: 26 pages (1 over MNRAS limit)
- **After**: 25 pages ✓ (meets requirement)

**Trims applied**:
1. Condensed Executive Summary of Limitations (7→3 lines)
2. Trimmed Distance Uncertainties section (removed VLBI paragraph, condensed validation)
3. Removed redundant "Recommendation for future work" paragraphs
4. Condensed Conclusions section (8 bullet points → 6 streamlined points)

## Current Paper Status

- **Page count**: 25 pages ✓ (meets MNRAS requirement)
- **Compilation**: Successful
- **All referee concerns**: Addressed ✓
- **Citations**: Resolved (bibtex run)

## Key Messages for Referee Response

### 1. RTC Zero Matching Rate (Concern 3)
"The RTC campaign's complete absence of HGBS matches (all λ/W ≥ 3.75) with free boundaries suggests that real molecular cloud filaments may require additional physics (non-ideal MHD, accretion, hierarchical fragmentation) or environmental confinement to reproduce observed spacings."

### 2. Rigid Cylinder Positive Result (Concern 1)
"The rigid cylinder campaign (λ/W = 2.65 ± 0.57 at f ≥ 2.6) demonstrates that self-gravity can produce HGBS-compatible spacing when radial collapse is suppressed. This boundary-condition sensitivity underscores that fragmentation morphology depends critically on filament confinement physics."

### 3. Perpendicular-Field Gap (Concern 2)
"Simple geometric interpolation from perpendicular (λ/W ≈ 2.02) to longitudinal geometries cannot close the 29% gap. Additional physics—turbulent pressure support, accretion-driven lengthening, or observational bias toward sampling longitudinal-field interiors—is required."

### 4. Profile Shape Systematic (Concern 4)
"The Gaussian vs. Ostriker profile choice introduces ~5-10% systematic uncertainty in λ/W—smaller than the 21% region-to-region scatter in HGBS spacings. The post-hoc width normalisation factor of 1.61 has 11.9% 1σ uncertainty, not the 31% full range."

### 5. Power Law Decomposition (Concern 5)
"The measured exponent α = 0.39 ± 0.01 deviates from free-fall expectation (α = 0.5) by 22%. T2 campaign decomposition: Δα_hydro = 0.048 (44% from Gaussian profile non-linear hydrodynamics) + Δα_MHD = 0.062 (56% from flux-freezing effects)."

## Files Created

1. `analyze_rtc_restricted.py` - RTC restricted subspace analysis
2. `analyze_rtc_distribution.py` - RTC λ/W distribution analysis  
3. `verify_rtc_matches.py` - Verification of HGBS matches
4. `check_4_matches.py` - Check of 4 matches in broader window
5. `REFEREE_RESPONSE_SUMMARY.md` - Summary of analysis and revisions
6. `TRIMMING_RECOMMENDATIONS.md` - Page trimming strategy

## Next Steps for User

1. **Review the revised paper** (`filament_spacing_streamlined_mnras.pdf`)
2. **Verify all referee concern responses** are adequately addressed
3. **Prepare referee response letter** using the key messages above
4. **Consider additional simulations** if needed (Ostriker IC, oblique-angle λ/W)
5. **Submit to MNRAS** when ready

## Critical Findings to Emphasize

1. **Zero HGBS matches in RTC** - strengthens Interpretation B
2. **Rigid cylinder success** - boundary conditions are critical
3. **Page count met** - 25 pages within MNRAS limit
4. **All concerns addressed** - comprehensive response prepared

---

**Date**: June 6, 2026
**Paper**: filament_spacing_streamlined_mnras.tex
**Status**: Ready for referee response and submission
