# Referee Response Summary: O6-O9

**Date**: 2026-05-12
**Paper**: filament_spacing_streamlined_mnras.tex (29 pages)

## O6: Figure 1 Labels Confusing ✅ RESOLVED

**Issue**: Caption listed regions in order of increasing spacing, but x-axis showed different ordering

**Fix**: Updated caption to clarify alphabetical ordering

**Old caption**:
```
From left to right: Taurus (0.198 pc), Ophiuchus (0.206 pc), TMC1 (0.195 pc), 
CRA (0.248 pc), Perseus (0.248 pc), Serpens (0.331 pc), Orion B (0.313 pc), 
Aquila (0.346 pc).
```

**New caption**:
```
Regions are plotted in alphabetical order from left to right. Values: Aquila 
(0.346 pc), CRA (0.248 pc), Ophiuchus (0.206 pc), Orion B (0.313 pc), Perseus 
(0.248 pc), Serpens (0.331 pc), Taurus (0.198 pc), TMC1 (0.195 pc).
```

**Location**: Line 313

---

## O7: Table 4 Discrepancy ✅ RESOLVED

**Issue**: Taurus "original HGBS" value (0.206 pc) vs current pairwise median (0.198 pc) not explicitly noted

**Fix**: Added explanatory note (Note 6) to table

**Added note**:
```latex
(6) \textbf{Taurus discrepancy}: The current Taurus spacing (0.198 pc) differs 
from the original HGBS value (0.206 pc) due to a -4\% distance revision (140 pc 
to 135 pc with Gaia DR3). This small change reflects Gaia DR3's improved distance 
precision for nearby regions.
```

**Location**: Line 344 (table notes)

---

## O8: Misleading Migration Studies Statement ✅ RESOLVED

**Issue**: Statement that 0.01-0.05 pc displacement is "small compared to ~0.3 pc spacing" is misleading - it's 25% for NN spacing

**Old text**:
```
Context from migration studies: Observational studies of protostellar migration 
suggest typical displacement scales of 0.01--0.05 pc, small compared to our measured 
core spacings of ~0.3 pc.
```

**New text**:
```
Context from migration studies: Observational studies of protostellar migration 
suggest typical displacement scales of 0.01--0.05 pc. For our measured nearest-neighbor 
spacings of ~0.2 pc (Taurus, Ophiuchus, CRA), a 0.05 pc displacement represents a ~25% 
perturbation---not negligible. For the pairwise median values of ~0.28 pc, the same 
displacement represents an ~18% effect. Protostellar migration could therefore introduce 
systematic uncertainty at the 10--25% level.
```

**Location**: Line 80

---

## O9: LaTeX Cross-Reference Errors ✅ RESOLVED

**Issue**: Multiple undefined references (Figure ?? and Section ??)

**All fixed references**:

| Old Reference | Issue | Fix |
|--------------|-------|-----|
| `\ref{sec:DTC}` | Case sensitivity (should be sec:dtc) | Changed to `\ref{sec:dtc}` |
| `\ref{fig:dtc_probability}` | Wrong label | Changed to `\ref{fig:dtc_pfrag}` |
| `\ref{sec:ic_sensitivity}` | Section doesn't exist | Changed to `\ref{fig:ic_sensitivity}` |
| `\ref{sec:campaign_5}` | Section doesn't exist | Added `\label{sec:campaign_5}` to subsection |
| `\ref{sec:magnetic}` | Section doesn't exist | Added `\label{sec:magnetic}` to subsection |
| `\ref{sec:R7}` | Section doesn't exist | Added `\label{sec:R7}` to subsection |
| `\ref{sec:campaign_6}` | Section doesn't exist | Added `\label{sec:campaign_6}` to subsection |

**Locations**:
- Line 364: Fixed sec:DTC → sec:dtc
- Line 449: Fixed fig:dtc_probability → fig:dtc_pfrag
- Line 547: Fixed sec:ic_sensitivity → fig:ic_sensitivity
- Line 755: Added \label{sec:campaign_5} to Turbulence Effects subsection
- Line 634: Added \label{sec:magnetic} to Theory subsection
- Line 809: Added \label{sec:R7} to Perpendicular-Field Domain Convergence subsection
- Line 805: Added \label{sec:campaign_6} to Extended-Domain Measurements subsection

---

## Verification

**PDF Compilation**: ✅ SUCCESS
- 29 pages generated
- No undefined reference errors
- All cross-references now resolve correctly

**Changes Summary**:
- 1 figure caption updated (O6)
- 1 table note added (O7)
- 1 text paragraph updated (O8)
- 7 cross-references fixed (O9)

---

## Key Messages for Referee Response

**O6**: "Updated Figure 1 caption to clarify that regions are plotted in alphabetical order, not in order of increasing spacing as previously stated."

**O7**: "Added explicit note (Note 6) to Table 4 explaining that the Taurus discrepancy (0.198 vs 0.206 pc) reflects the -4% distance revision from Gaia DR3."

**O8**: "Corrected migration studies statement to acknowledge that 0.05 pc displacement represents a 25% perturbation for NN spacings (~0.2 pc), which is not negligible. Now states this could introduce 10-25% systematic uncertainty."

**O9**: "Fixed all 7 LaTeX cross-reference errors. All undefined references now resolved. PDF compiles successfully with no cross-reference warnings."

---

## Files Updated

1. `filament_spacing_streamlined_mnras.tex` - Main paper with all fixes
2. `filament_spacing_streamlined_mnras.pdf` - Compiled PDF (29 pages)
