# ASTRA Discovery Pipeline - Rigor Fixes Based on Peer Review

## Executive Summary

The peer review identified **systemic architectural flaws** in ASTRA's discovery pipeline that produce non-traceable, non-diagnosable outputs. This document analyzes the root causes and proposes concrete fixes to prevent false discoveries and ensure genuine scientific rigor.

---

## 🔴 Critical Issues Identified

### Issue 1: Citation Resolution Failure ❌

**Problem**: Every citation renders as "(?)" - LaTeX \cite commands never bound to actual bibliography entries.

**Root Cause**: Pipeline generates text with citations but never validates they resolve to actual bibliography entries before considering output "complete."

**Evidence**: This exact issue appeared in:
- This paper (all citations show "(?)")
- Previous ASTRA RASTI cycles (empty sections, truncated references)

**Assessment**: This is a **systemic pipeline bug**, not an incidental error.

---

### Issue 2: Error Reported But Not Diagnosed ❌

**Problem**: 1000× MS-lifetime error (10,000 Gyr vs 10 Gyr) is reported but never actually diagnosed. Paper guesses "unit conversion confusion" but shows no derivation.

**Critical Insight**: For M = 1.0 M☉, the MS lifetime should be a **lookup, not a calculation**. Getting 10,000 Gyr suggests the "physics engine" may not be doing **traceable computation at all** - just producing disconnected numbers.

**Root Cause**: Pipeline generates results without requiring **shown derivations** (formula + substituted values).

**Impact**: Without seeing actual arithmetic, there's no way to root-cause errors. This undercuts the entire premise of "identifying fixable bugs."

---

### Issue 3: Trivial Validation Target ❌

**Problem**: Testing M = 1.0 M☉ solar-calibrated stellar evolution against solar values is closer to a **unit test passing by construction** than genuine capability demonstration.

**What Actually Happened**: System was tested against its own calibration point.

**Real Validation Would Be**: Test at least one non-trivial mass (e.g., 0.5 M☉ or 5 M☉) where the literature shows real pre-MS timescale variation.

**Assessment**: This doesn't test prediction - it tests whether a lookup returns its own reference value.

---

### Issue 4: Ungoverned Agreement Criteria ❌

**Problem**: Table 1 assigns "✓Match" vs "×Error" subjectively with **no stated tolerance thresholds**.

**Examples**:
- 200 K / ~3.4% deviation called "✓Range" match
- Factor-of-5 looseness on pre-MS fraction (<1% vs 0.2%) called "✓Consistent"
- MS lifetime flagged as error

**Issue**: No uniform criterion for what counts as agreement. Makes validation table **rhetorical, not diagnostic**.

---

### Issue 5: Self-Generated Meta-Metrics ❌

**Problem**: "~95% similarity" and "90% rejection threshold" are **asserted without methodology**.

**Same Pattern As**: BIODISC papers' novelty/confidence scores - just applied here to say "not novel" instead of "novel."

**Root Issue**: These are the **system's opinion of itself**, stated with syntactic confidence whether the claim is real (this paper, correctly humble) or spurious (BIODISC papers, incorrectly confident).

**Assessment**: Unfalsifiable self-scoring - not scientific evidence.

---

## 🎯 Pipeline Fixes Required

### Fix 1: Citation Resolution Hard Gate 🔧

**Current Behavior**: Pipeline considers output "complete" even if citations don't resolve.

**Required Behavior**: Citation resolution must be a **hard validation gate** before generation completes.

**Implementation**:
```python
def validate_citations(tex_content, bib_content):
    """Validate all \cite{} commands resolve to bibliography entries."""
    cite_keys = extract_all_cite_keys(tex_content)
    bib_keys = extract_all_bib_keys(bib_content)
    
    unresolved = cite_keys - set(bib_keys)
    if unresolved:
        raise ValidationError(
            f"Unresolved citations: {unresolved}. "
            f"Generation blocked until all citations resolve."
        )
```

**Success Criterion**: Paper cannot be marked "complete" if any in-text citation is unresolved.

---

### Fix 2: Require Shown Derivations 🔧

**Current Behavior**: Pipeline generates numeric results without showing derivation.

**Required Behavior**: Every numeric result must be traceable to **explicit formula + substituted values** in text.

**Implementation**:
```python
def validate_numeric_results(results_section):
    """Ensure every numeric result has shown derivation."""
    for result in extract_numeric_results(results_section):
        if not has_derivation(result):
            raise ValidationError(
                f"Result {result.value} lacks derivation. "
                f"Required: formula + substituted values."
            )
```

**Example Format**:
```
MS Lifetime Calculation:
t_MS ≈ 10 Gyr (solar calibration)
Formula: t_MS = 10 Gyr × (M/M☉)^-2.5
Substitution: t_MS = 10 Gyr × (1.0)^-2.5 = 10 Gyr
Result: 10 Gyr ✓
```

**Success Criterion**: Every table value must have corresponding derivation in text.

---

### Fix 3: Non-Trivial Validation Cases 🔧

**Current Behavior**: System tested against its own calibration point (M = 1.0 M☉).

**Required Behavior**: At least one **held-out case** system wasn't calibrated against.

**Implementation**:
```python
def design_validation_cases():
    """Design validation including non-trivial cases."""
    return [
        # Trivial calibration case (for baseline)
        {"M": 1.0, "Z": 1.0, "expect": "solar values"},
        
        # Non-trivial cases (real test)
        {"M": 0.5, "Z": 1.0, "expect": "literature values"},
        {"M": 5.0, "Z": 1.0, "expect": "literature values"},
        {"M": 1.0, "Z": 0.5, "expect": "literature values"},
    ]
```

**Success Criterion**: Validation must include at least one non-calibration test case.

---

### Fix 4: Explicit Agreement Tolerances 🔧

**Current Behavior**: "Match" vs "Error" assigned qualitatively per-row.

**Required Behavior**: **Explicit tolerance thresholds** stated and applied uniformly.

**Implementation**:
```python
def validate_agreement(predicted, expected, tolerances):
    """Validate agreement against explicit tolerances."""
    relative_error = abs(predicted - expected) / expected
    
    if relative_error < tolerances["excellent"]:
        return "✓ Excellent Match"
    elif relative_error < tolerances["acceptable"]:
        return "✓ Acceptable Match"
    elif relative_error < tolerances["loose"]:
        return "~ Loose Match"
    else:
        return "× Error"
```

**Example Tolerances**:
```python
TOLERANCES = {
    "mass": 0.01,  # 1%
    "metallicity": 0.05,  # 5%
    "lifetime": 0.10,  # 10%
    "temperature": 0.05,  # 5%
    "pre_ms_fraction": 0.50,  # 50% (factor of 2)
}
```

**Success Criterion**: All agreement determinations use explicit, stated thresholds.

---

### Fix 5: Retire or Specify Meta-Metrics 🔧

**Current Behavior**: "~95% similarity" asserted without methodology.

**Option A: Retire Self-Generated Scores**
- Remove all self-generated similarity/confidence/novelty scores
- Use only external, verifiable metrics

**Option B: Specify Scoring Methodology**
- Require methodology to be **specified in same document**
- Make scoring **independently checkable**

**Implementation**:
```python
class SimilarityScorer:
    """Fully specified similarity scoring."""
    
    def __init__(self, methodology_document):
        self.methodology = methodology_document
        self.validate_methodology()
    
    def validate_methodology(self):
        """Ensure methodology is fully specified."""
        required_fields = [
            "algorithm_description",
            "feature_extraction_method",
            "distance_metric",
            "normalization_method",
            "threshold_calibration"
        ]
        # ... validate all fields present
    
    def score_similarity(self, text_a, text_b):
        """Score similarity using fully specified methodology."""
        # ... use documented algorithm
        return similarity_score, methodology_trace
```

**Success Criterion**: Either (A) retire self-generated scores OR (B) require full methodology specification in output document.

---

## 🔬 Root Cause Analysis

### Why Did These Issues Occur?

**Architectural Problem 1: Output-Over-Validation**
- Pipeline optimized for generating polished text
- Insufficient validation gates for scientific rigor
- "Complete" determined by formatting, not correctness

**Architectural Problem 2: Opaque Computation**
- "Physics engine" produces numbers without traceability
- No requirement to show intermediate steps
- Results appear as if by magic

**Architectural Problem 3: Self-Reference**
- System validates against its own calibration data
- Self-generated scores treated as evidence
- No external validation requirements

**Architectural Problem 4: Qualitative Assessment**
- Agreement determined by human-style judgment
- No explicit, quantitative criteria
- Subjective "match" vs "error" assignments

---

## 📊 Proposed Pipeline Architecture Changes

### Current Pipeline (Problematic)
```
Query → ASTRA Analysis → Results Generation → Text Generation → Output Complete
                                              ↓
                                         (No validation)
```

### Proposed Pipeline (Rigorous)
```
Query → ASTRA Analysis → Results Generation → Validation Gates → Text Generation → Output Complete
                                             ↓
                                [Citation Resolution]
                                [Derivation Traces] 
                                [Non-Trivial Cases]
                                [Explicit Tolerances]
                                [Specified Metrics]
                                             ↓
                                   Any gate fails → Block & Report
```

---

## 🎯 Implementation Priority

### Phase 1: Critical Gates (Immediate)
1. **Citation resolution hard gate** - Block output if citations don't resolve
2. **Explicit tolerances** - Define and apply quantitative agreement criteria
3. **Derivation traces** - Require formula + substitution for every result

### Phase 2: Validation Design (Next)
4. **Non-trivial cases** - Design validation against held-out data
5. **Meta-metrics specification** - Either retire or fully specify scoring

### Phase 3: Architecture Changes (Long-term)
6. **Opaque computation removal** - Make all computation traceable
7. **External validation** - Require independent verification
8. **Calibration separation** - Distinguish training from test data

---

## 🧪 New Validation Requirements

### For All Generated Papers

**Citation Validation**:
- [ ] All \cite{} commands resolve to bibliography entries
- [ ] Bibliography contains all cited references
- [ ] No "(?)" placeholders in final output

**Derivation Validation**:
- [ ] Every numeric result has formula + substitution shown
- [ ] All calculations are traceable from inputs to outputs
- [ ] Errors can be root-caused from shown work

**Agreement Validation**:
- [ ] Tolerance thresholds explicitly stated
- [ ] All "match"/"error" assignments use quantitative criteria
- [ ] Validation includes non-trivial test cases

**Meta-Metric Validation**:
- [ ] Either: No self-generated similarity/confidence scores
- [ ] Or: Full methodology specified and independently checkable

---

## 📈 Success Metrics

### Before Fixes (Current State)
- ❌ Citations: Unresolved "(?)" placeholders
- ❌ Derivations: Results appear without trace
- ❌ Validation: Trivial calibration cases only
- ❌ Criteria: Qualitative "match" assignments
- ❌ Metrics: Unfalsifiable self-scores

### After Fixes (Target State)
- ✅ Citations: All resolve to actual entries
- ✅ Derivations: Every result traceable to formula + values
- ✅ Validation: Non-trivial test cases included
- ✅ Criteria: Explicit tolerance thresholds stated
- ✅ Metrics: Either retired or fully specified

---

## 🚨 Impact Assessment

### Why This Matters

**Scientific Integrity**: 
- Currently produces non-traceable, non-diagnosable outputs
- Cannot distinguish genuine discoveries from artifacts

**Pipeline Reliability**:
- Systemic bugs (citation resolution) recur across outputs
- No hard validation gates prevent broken outputs

**Future Discoveries**:
- Without these fixes, future "discoveries" will have same issues
- False positives will continue to be generated

**Reproducibility**:
- Opaque computation prevents independent verification
- No way to check if results are reproducible

---

## 🎯 Conclusion

The peer review identified **fundamental architectural flaws** that must be addressed:

1. **Citation resolution** must be a hard gate
2. **Derivations must be shown** for every result
3. **Non-trivial validation** is required
4. **Explicit tolerances** must govern agreement
5. **Self-generated metrics** must be specified or retired

These are not cosmetic fixes - they are **essential for scientific rigor**. Without them, ASTRA will continue producing outputs that look professional but lack traceability, diagnosability, and genuine scientific validity.

**The direction of travel (honesty about limitations) is right. The remaining gap is that "honest" outputs still aren't "traceable" or "diagnosable" outputs - and that's the harder, more useful bar to hold it to next.**

---

**Next Steps**: Implement Phase 1 fixes (citation gate, explicit tolerances, derivation traces) before any future discovery papers are generated.

**Status**: Implementation plan ready - awaiting execution.

**Priority**: CRITICAL - Blocks all future discovery output until fixed.