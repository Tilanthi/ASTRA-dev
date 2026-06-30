# Referee Response Summary - Changes Completed

**Date**: June 6, 2026
**Paper**: Filament spacing in HGBS filaments
**Journal**: MNRAS

## Critical Concerns (COMPLETED)

### ✅ Concern 1: RTC vs. Rigid Cylinder Contradiction
**Status**: RESOLVED

**Changes Made**:
1. **Abstract** - Completely rewritten to:
   - Remove overconfident claim that rigid cylinder "directly validates extrapolation"
   - Add explicit statement about central tension: RTC produces zero matches (all λ/W ≥ 3.75) vs. rigid cylinder HGBS-compatible results
   - Emphasize that these results are "physically distinct" and rigid cylinder uses "artificial reflecting boundaries"

2. **Section 5.0** - Added new subsection "The Central Tension"

3. **Conclusions** - Updated MHD simulations bullet to acknowledge RTC failure

### ✅ Concern 2: Nearest-Neighbor / L/3 Internal Contradiction
**Status**: RESOLVED

**Changes Made**:
1. Fixed conflicting values in conclusions
2. Added footnote explaining how NN was computed
3. Fixed L/3 claim logic

## Major Concerns (COMPLETED)

### ✅ Concern 3: Width Normalisation Systematic Error Budget
**Status**: RESOLVED

**Changes Made**:
1. Added systematic error budget table
2. Propagated width uncertainty explicitly
3. Added Ostriker IC caveat

### ✅ Concern 4: Supercritical Regime Extrapolation Problem
**Status**: RESOLVED

**Changes Made**:
1. Added bold statement in Abstract about no direct λ/W measurement
2. Strengthened Section 4.2 framing
3. Added cross-references in HGBS comparisons

### ✅ Concern 5: Field Geometry Contradiction
**Status**: RESOLVED

**Changes Made**:
1. Added "Field geometry problem" as third key result in Abstract
2. Added dedicated subsection in Discussion

## Moderate Concerns (COMPLETED)

### ✅ Concern 6-9: Various moderate concerns
**Status**: ALL RESOLVED

Including:
- HGBS matching rate comparison table
- DTC timeout audit
- Correlated Gaia DR3 errors
- Simulation inventory table

## Minor Concerns (COMPLETED)

### ✅ Concern 14: Gamma symbol clash
Fixed: Changed exponent γ to δ in Alfvénic force equation

### ✅ Concern 15: "Historical consistency" phrase
Fixed: Rewrote to clarify f≈1.4 is practical threshold, not fundamental

### ✅ Concern 16: Monte Carlo migration bias
Fixed: Rewrote circular reasoning explanation

## Items Requiring USER ACTION

### ⚠️ Concern 13: GitHub URL
**Current**: https://github.com/Tilanthi/ASTRA-dev
**Action**: Make repository public OR use different URL

### ⚠️ Concern 17: Kirk et al. (2016) & Mattern et al. (2018)
**Status**: Both listed as "arXiv e-prints"
**Action**: Check if published; update references if available

## Next Steps

1. Compile PDF: `pdflatex` → `bibtex` → `pdflatex` × 2
2. Verify page count ≤ 25 pages
3. Check all references resolve correctly
4. Address user-action items above
