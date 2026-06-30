# Paper Revision Plan for Referee Response

## Current Status
- **Page count**: 26 pages (need to reduce to ≤25 pages)
- **Abstract word count**: 803 words (need to reduce to ≤250 words)
- **Referee mentions**: 39 occurrences to remove
- **NN Analysis**: Running, awaiting results for all 8 HGBS regions

## Priority Issues to Fix

### 1. Central Methodological Problem (Issue #1)
**Current state**: Paper uses pairwise median statistic
**Problem**: L/3 convergence artifact for large-N filaments
**Solution**: 
- Replace pairwise median with nearest-neighbor (NN) spacing as primary statistic
- Use NN analysis results for all 8 HGBS regions
- Update abstract, results, and conclusions to emphasize NN results

**Abstract changes needed**:
- Remove: "primary sample comprises 4 robust HGBS regions"
- Replace with: "We computed nearest-neighbor (adjacent-core) spacing for all 8 HGBS regions"
- Update primary result to NN-based measurement
- Remove sentence "Full nearest-neighbor analysis for all HGBS regions is ongoing"

### 2. Remove All Referee Mentions (Issue #3, Issue #6)
**39 occurrences found**:
- Line 33: "referee response campaigns" → "targeted campaigns"
- Line 35: "Referee Response Campaigns" → "Additional Campaigns" or remove
- Line 145: "Referee concern regarding Serpens distance" → "Distance uncertainty concerns"
- Line 156: "address the referee's concern directly" → "address this concern"
- Line 200: "Referee concern and motivation" → "Statistical methodological concern"
- Line 598: "Referee Response Campaigns" section → remove or rename
- Line 605: "referee correctly identified" → remove
- Line 616: "referee noted that" → remove
- Line 620: "referee identified" → remove
- Line 635: "referee identified" → remove
- Line 675, 684, 688, 698, 710, 712, 724, 738, 740, 752, 766: Multiple occurrences
- Line 788, 810, 841, 847: Multiple occurrences

**Search/replace pattern**:
- "referee concern" → "concern"
- "referee response" → "targeted" or remove
- "Referee Response Campaigns" → "Additional Campaigns" or remove section
- "referee correctly identified" → remove sentence
- "referee noted" → remove or rephrase
- "address the referee's concern" → "address this concern"

### 3. Abstract Reduction (Issue #11)
**Current**: 803 words (way over 250-word limit)
**Target**: 250 words

**Strategy**:
1. Focus on key scientific question and main result
2. Use NN spacing as primary observational result
3. Mention key theoretical findings (magnetic tension, field geometry)
4. Note critical limitation (extrapolation regime)
5. Remove verbose simulation campaign descriptions

**Draft revised abstract** (~250 words):
```
We present a systematic analysis of core spacing along filaments in the Herschel Gould Belt Survey (HGBS), 
combined with self-gravitating MHD simulations to test theoretical explanations for the observed fragmentation scale. 
We computed proper nearest-neighbor (adjacent-core) spacing statistics directly from HGBS skeleton and core catalog 
data for all 8 high-confidence regions. The weighted mean nearest-neighbor spacing across the robust sample 
(Orion B, Aquila, Perseus, Taurus) is [X] ± [Y] pc, corresponding to [Z]× the characteristic filament width of 
0.10 pc. This differs from the classical prediction of 4× by a factor of [N].

We examine three primary explanations. First, hierarchical fragmentation: fiber-resolved analysis in Orion B 
shows that fiber-to-core spacing recovers the classical 4× prediction. Second, magnetic tension along filaments: 
for longitudinal magnetic fields with plasma β ~ 1–3, the theoretical prediction is λ/W ≈ 2.4–3.2, overlapping 
with our measurement. Third, magnetic field geometry: our simulations reveal that perpendicular-field filaments 
fragment at substantially shorter wavelengths (λ/W ≈ 1.25) than longitudinal-field filaments (λ/W ≈ 2.8–4.4).

We present MHD simulations using Athena++ spanning the (Mach, plasma β) parameter space relevant to molecular 
cloud filaments. The simulations reveal three distinct fragmentation regimes and reproduce expected timescales from 
linear MHD stability theory. Critical limitation: direct measurement of λ/W from simulations was only possible 
for near-critical filaments (f ≈ 1.0–1.2); all supercritical simulations (f ≥ 1.5) underwent radial collapse before 
longitudinal beading developed, requiring theoretical extrapolation for comparison with HGBS observations.
```

### 4. Page Reduction (Issue #2)
**Current**: 26 pages
**Target**: ≤25 pages

**Reduction strategies** (1 page ≈ 400-500 words or several figures/tables):
1. Remove or condense "Referee Response Campaigns" section (~0.5 pages)
2. Reduce simulation campaign enumeration in abstract (~0.2 pages)
3. Condense some simulation sub-sections (~0.3 pages)

**Specific cuts**:
- Section 4.9.7 "Referee Response Campaigns" - rename to "Additional Campaigns" and reduce content
- Remove verbose campaign enumeration from abstract (already planned)
- Consider moving some simulation details to supplementary material

### 5. Consistency Issues (Issue #4, Issue #5, Issue #13)
**Inconsistent simulation counts**:
- Abstract: "432 simulations, April–June 2026"
- Section 4.9: "289 simulations, April–May 2026"
- Section 4.9: "2000 Athena++ simulations"
- Conclusions: "2,860 simulations"
- Acknowledgements: "2,860"

**Fix**: Create single summary table and use consistent number throughout.

**Width normalization inconsistency**:
- Issue 4: Width-corrected values only in Executive Summary and Section 4.9.5
- Should appear in abstract and primary results

**Fix**: Add width-corrected comparison to abstract and main results.

**Text formatting errors**:
- Issue 13: Run-on sentences in Section 3.2 and 4.9.3

**Fix**: Add proper spaces between words.

## Implementation Order

1. **Wait for NN analysis results** → Use NN spacing as primary statistic throughout
2. **Revise abstract** → Reduce to 250 words, use NN results
3. **Remove referee mentions** → Global search/replace
4. **Fix consistency issues** → Simulation counts, width normalization
5. **Reduce page count** → Condense sections, remove verbose descriptions
6. **Fix formatting errors** → Add spaces, fix references
7. **Verify all values** → Deep read as external astronomer

## Files to Edit

1. `filament_spacing_streamlined_mnras.tex` - Main paper
2. `references_complete.bib` - Fix corrupted entries
3. Figures - Check all figure references are valid
