# External Review Traces: Complete Removal

## Date: 2026-05-03

This document summarizes the complete removal of all traces of external review, referee comments, or peer review feedback from the paper. The paper now reads as if it was written organically without any reference to external input.

---

## PHILOSOPHY OF THE REVISION

The goal is not to "anonymize" referee comments but to **completely remove any indication that the paper was reviewed externally**. Every phrase that suggests:
- Someone raised a concern/question
- The authors are responding to feedback
- Certain points were identified by others
- Something deserves "more prominent treatment" based on external input

...has been rewritten to sound like the authors' own scientific judgment.

---

## PROBLEMATIC PHASES FIXED

### 1. "Warrants careful scrutiny" (Line 160)

**Before:**
```
An important concern regarding Serpens distance. The exceptional +76% distance revision for Serpens... warrants careful scrutiny... This concern is warranted because:
```

**After:**
```
Serpens distance revision. The exceptional +76% distance revision for Serpens... is notably large compared to other HGBS regions... Three factors motivate careful examination of this value:
```

**Key change:** Removed defensive language "concern is warranted" and replaced with neutral "factors motivate careful examination."

---

### 2. "To address this concern directly" (Line 171)

**Before:**
```
To address this concern directly, we classify regions into two categories:
```

**After:**
```
Accordingly, we classify regions into two categories:
```

**Key change:** Removed explicit reference to addressing a concern; replaced with "Accordingly" which suggests logical flow.

---

### 3. "Methodological concern" (Line 215)

**Before:**
```
Methodological concern. A critical gap limitation of the pairwise median statistic...
```

**After:**
```
Methodological limitation of the pairwise median statistic. A critical gap limitation of the pairwise median statistic...
```

**Key change:** Changed "concern" to "limitation" which sounds like the authors' own assessment, not a response to external input.

---

### 4. "To definitively address the L/3 convergence concern" (Line 242)

**Before:**
```
To definitively address the L/3 convergence concern, we performed a series of controlled tests...
```

**After:**
```
We performed a series of controlled tests using synthetic filament catalogs with known fragmentation wavelengths to determine which statistic...
```

**Key change:** Removed explicit statement of "addressing a concern"; reframed as straightforward scientific investigation.

---

### 5. "Addresses the concern that" (Line 423)

**Before:**
```
The analysis addresses the concern that Aquila's large distance revision (+68%) might dominate the weighted mean.
```

**After:**
```
We tested whether Aquila's large distance revision (+68%) affects the weighted mean.
```

**Key change:** Changed "addresses the concern" to "we tested whether" - sounds like the authors' own scientific inquiry.

---

### 6. "We address these statistical concerns" (Line 993)

**Before:**
```
We address these statistical concerns in Section X... showing that our primary conclusion... is robust to these uncertainties.
```

**After:**
```
Section X... examine these uncertainties, showing that our primary conclusion... is robust to these variations.
```

**Key change:** Removed active "we address" language; replaced with passive statement about what the sections do.

---

### 7. "To address several outstanding questions" (Line 892)

**Before:**
```
To address several outstanding questions and provide definitive answers to outstanding questions, we conducted an additional targeted simulations...
```

**After:**
```
We conducted an additional set of 289 Athena++ simulations across three targeted simulation sets to investigate specific aspects of fragmentation behavior.
```

**Key change:** Removed "outstanding questions" phrasing; replaced with neutral "investigate specific aspects."

---

### 8. "To address critical gaps identified in peer review" (Line 824)

**Before:**
```
To address critical gaps identified in peer review---specifically the need for (1) near-critical fragmentation detection...
```

**After:**
```
We conducted the field geometry simulations comprising 314 additional Athena++ simulations across four phases to investigate (1) near-critical fragmentation detection...
```

**Key change:** Completely removed reference to "peer review"; replaced with neutral "to investigate."

---

### 9. "Was not adequately appreciated in previous analyses or in our original submission" (Line 219)

**Before:**
```
We acknowledge this as a critical limitation... that was not adequately appreciated in previous HGBS analyses or in our original submission.
```

**After:**
```
This critical limitation... has important implications: the pairwise median values reported throughout this paper should be interpreted as...
```

**Key change:** Removed defensive "was not adequately appreciated in our original submission"; reframed as straightforward statement of implications.

---

### 10. "A critical gap noted that..." (Line 434)

**Before:**
```
A critical gap noted that the 3D projection correction applied to PM measurements deserves more prominent treatment.
```

**After:**
```
The 3D projection correction applied to PM measurements has important implications for comparison with classical theory.
```

**Key change:** Removed "noted that... deserves more prominent treatment"; replaced with statement about implications.

---

### 11. "A critical gap additional constraint" (Line 481)

**Before:**
```
A critical gap additional constraint comes from high-resolution studies...
```

**After:**
```
An important constraint comes from high-resolution studies...
```

**Key change:** Fixed grammatical error and removed "critical gap" phrasing; replaced with "important constraint."

---

### 12. "A critical gap question is whether" (Line 389)

**Before:**
```
A critical gap question is whether the weighted mean NN/PM ratio of 0.72 is dominated by any single region...
```

**After:**
```
An important question is whether the weighted mean NN/PM ratio of 0.72 is dominated by any single region...
```

**Key change:** Removed "critical gap" phrasing; replaced with "important question."

---

### 13. Figure paths with "peer_review_analysis/" (Lines 835-882)

**Before:**
```
includegraphics[width=0.45\textwidth]{peer_review_analysis/fig1_beading_threshold_M1.pdf}
```

**After:**
```
includegraphics[width=0.45\textwidth]{figures/fig1_beading_threshold_M1.pdf}
```

**Key change:** All figure paths updated to use `figures/` directory instead of `peer_review_analysis/`.

---

## COMPLETE REMOVAL SUMMARY

| Original Phrase | Count | Replacement | Status |
|----------------|-------|-------------|--------|
| "warrants careful scrutiny" | 1 | "is notably large... factors motivate careful examination" | ✅ Removed |
| "To address this concern directly" | 1 | "Accordingly, we..." | ✅ Removed |
| "Methodological concern" | 1 | "Methodological limitation" | ✅ Removed |
| "To definitively address the... concern" | 1 | "We performed..." | ✅ Removed |
| "addresses the concern that" | 1 | "We tested whether" | ✅ Removed |
| "We address these statistical concerns" | 1 | "Section X... examine" | ✅ Removed |
| "To address several outstanding questions" | 2 | "We conducted... to investigate" | ✅ Removed |
| "identified in peer review" | 1 | Completely removed | ✅ Removed |
| "was not adequately appreciated in our original submission" | 1 | Completely removed | ✅ Removed |
| "A critical gap noted that... deserves more prominent treatment" | 1 | "has important implications" | ✅ Removed |
| "A critical gap question is whether" | 1 | "An important question is whether" | ✅ Removed |
| "peer_review_analysis/" (figure paths) | 6 | "figures/" | ✅ Fixed |

---

## PHRASES KEPT (BENIGN CONTEXTS)

The following phrases were **kept** because they represent the authors' own scientific assessment, not responses to external input:

- **"remains an open question"** - Scientific statement about what is unknown
- **"challenging to explain"** - Scientific assessment of difficulty
- **"Most concerning is Ophiuchus"** - Author's own evaluation of the data
- **"significant challenge"** - Scientific statement about the problem being studied
- **"critical issue"** - Author's identification of an important problem
- **"To address the critical gap in..."** - Addressing a gap in understanding, not external review

---

## VERIFICATION

### Final counts of problematic phrases:
- **"referee"**: 0 instances ✅
- **"Referee"**: 0 instances ✅
- **"peer"**: 0 instances ✅
- **"identified in peer review"**: 0 instances ✅
- **"original submission"**: 0 instances ✅
- **"concern is warranted"**: 0 instances ✅
- **"deserves more prominent treatment"**: 0 instances ✅
- **"peer_review_analysis/"**: 0 instances ✅

### Compilation status:
✅ Paper compiles successfully
- Pages: 31
- Size: 1.0 MB
- No critical LaTeX errors related to these changes

---

## RESULT

The paper now reads as if it was written organically by the authors without any reference to external review, referee comments, or peer review feedback. All phrases that suggested the authors were responding to external input have been rewritten to sound like the authors' own scientific judgment and inquiry.

**Date Completed:** 2026-05-03
