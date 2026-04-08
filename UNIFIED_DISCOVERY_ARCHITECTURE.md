# ASTRA Unified Discovery Architecture
## Theory-Data Integration for Closed-Loop Scientific Discovery

**Date**: 2026-04-06
**Version**: 1.0

---

## Executive Summary

ASTRA has evolved through three major phases:

### Phase 1: Empirical Pattern Discovery (Completed)
- Numerical data analysis, pattern recognition, statistical testing
- Hypothesis generation from data patterns
- Confidence tracking through Bayesian updates

### Phase 2: Theoretical Innovation (Completed)
- 7 advanced theory discovery modules
- Conceptual blending, information physics, paradoxes
- Mathematical structure discovery, constraint transfer

### Phase 3: **Unified Discovery** (This Implementation)
- **Closed-loop theory-data integration**
- Theories predict → Data validates → Theories refine → Cycle repeats
- **The scientific method, automated**

---

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                     UNIFIED DISCOVERY ENGINE                         │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    CYCLE ORCHESTRATOR                           │  │
│  │  ┌────────────┐   ┌────────────┐   ┌────────────┐           │  │
│  │  │   THEORY   │   │    DATA    │   │  REFINEMENT │           │  │
│  │  │ GENERATION │   │ DISCOVERY  │   │   ENGINE    │           │  │
│  │  └─────┬──────┘   └─────┬──────┘   └─────┬──────┘           │  │
│  │        │                │                │                   │  │
│  │        └────────────────┴────────────────┘                   │  │
│  │                     │                                       │  │
│  │              ┌─────▼─────────┐                             │  │
│  │              │ VALIDATION    │                             │  │
│  │              │   BRIDGE      │                             │  │
│  │              └─────┬─────────┘                             │  │
│  │                    │                                       │  │
│  │  ┌─────────────────┴────────────────────────┐               │  │
│  │  │     THEORY-DATA FEEDBACK & INTEGRATION        │               │  │
│  │  └───────────────────────────────────────────────┘               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Input: Theoretical modules + Data cache                               │
│  Output: Validated, refined theories with confidence tracking        │
└───────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Theory-Data Validation Bridge (`theory_data_validator.py`)

**Purpose**: Connect theoretical predictions with numerical validation

**Key Features**:
- Extract numerical predictions from theoretical frameworks
- Validate predictions against real astronomical data
- Quantify theory-data agreement (correlation, RMS error, K-S test)
- Identify discrepancy types (systematic bias, scale mismatch, outliers)
- Generate specific refinement suggestions based on data feedback
- Track theory evolution over validation cycles

**Key Classes**:
- `TheoryPrediction`: Encapsulates theoretical predictions
- `ValidationResult`: Result of validating against data
- `TheoryRefinement`: Suggested modifications based on discrepancies
- `TheoryEvolution`: Tracks theory improvement over time

**Example Workflow**:
```python
validator = TheoryDataValidator()

# Theory predicts: v = sqrt(G*M/r) (Newtonian)
theory = TheoryPrediction(
    theory_name="Newtonian Gravity",
    prediction_type="functional",
    mathematical_form="v = sqrt(G*M/r)"
)

# Validate against galaxy rotation data
result = validator.validate_theoretical_prediction(theory, rotation_data)

# Result: Status, agreement score, refinements
if result.status == ValidationStatus.DISAGREED:
    refinements = result.refinement_suggestions
    # "Add MOND correction term: v = sqrt(G*M/r + a0)"
```

---

### 2. Unified Discovery Engine (`unified_discovery_engine.py`)

**Purpose**: Orchestrates closed-loop discovery across all modules

**Key Features**:
- **Theory-Data Parallel Discovery**: Run both theory generation and data discovery simultaneously
- **Validation Loop**: Automatically validate all theories against appropriate data
- **Refinement Engine**: Generate theory refinements based on data feedback
- **Integration**: Cross-domain insights from theory-data agreement
- **Tracking**: Monitor theory confidence evolution over cycles

**Discovery Modes**:
1. **THEORY_FIRST**: Generate theory → Validate → Refine if needed
2. **DATA_FIRST**: Find pattern → Explain theoretically → Validate
3. **PARALLEL**: Both simultaneously (recommended)
4. **REFINEMENT**: Focus on improving existing theories

**Key Methods**:
- `run_unified_discovery_cycle()`: Main discovery cycle
- `_generate_theoretical_predictions()`: From all 7 theory modules
- `_discover_patterns_from_data()`: Unsupervised discovery
- `_integrate_theory_data_insights()`: Cross-domain synthesis

---

## Integration with ASTRA Engine

### Update Engine Imports

```python
# In astra_live_backend/engine.py

from .theory_data_validator import TheoryDataValidator, TheoryPrediction
from .unified_discovery_engine import UnifiedDiscoveryEngine, DiscoveryMode
```

### Initialize in `__init__`:

```python
# Unified discovery engine (Phase 13: Theory-Data Integration)
if THEORY_MODULES_AVAILABLE:
    self.theory_validator = TheoryDataValidator()
    self.unified_engine = UnifiedDiscoveryEngine()
    self._unified_discovery_interval = 20  # Run every 20 cycles
    self._last_unified_discovery_cycle = 0
```

### Add to UPDATE Phase:

```python
# In engine.py update() method

# Unified discovery: runs every N cycles (default: 20)
# This is where theory and data truly integrate
if self._unified_discovery_enabled and (self.cycle_count - self._last_unified_discovery_cycle >= self._unified_discovery_interval):
    result = self.unified_engine.run_unified_discovery_cycle(
        mode=DiscoveryMode.PARALLEL
    )

    # Log results
    self._log("UPDATE", "UNIFIED_DISCOVERY",
              f"Cycle {result.cycle_id}: {result.theories_validated} validated, "
              f"{result.theories_refined} refined, "
              f"confidence gain: {result.overall_confidence_gain:+.3f}")

    self._last_unified_discovery_cycle = self.cycle_count
```

---

## Example Discovery Cycle

### Scenario: Galaxy Rotation Curves

#### Step 1: Theory Generation
```python
# From information_physics.py
"Theory: Entropic gravity predicts MOND-like behavior at low acceleration"
```

#### Step 2: Data Discovery
```python
# From unsupervised_discovery.py
"Discovery: Galaxy rotation data shows flattening at low accelerations"
```

#### Step 3: Validation Bridge
```python
# theory_data_validator.py
"Theory prediction vs data: Agreement = 0.87"
"Status: VALIDATED"
```

#### Step 4: Cross-Domain Integration
```python
# unified_discovery_engine.py
"Insight: Entropic gravity + MOND-like data → Theory strengthened"
"Confidence trajectory: 0.6 → 0.87"
```

#### Step 5: Refinement (if needed)
```python
# If disagreement detected
"Refinement: Add interpolation function for transition region"
"New confidence: 0.92"
```

---

## Expected Discoveries

### Short-term (within current data)
1. **Validated entropic gravity** with MOND-like regime
2. **Discovered scaling relations** with theoretical explanations
3. **Cross-domain constraints** confirmed by data
4. **Refined theoretical parameters** based on data feedback

### Medium-term (with new data)
1. **Theory-data convergence** on contested topics (H₀ tension, σ₈)
2. **Automated theory refinement** based on data feedback
3. **Multi-method convergence** on physical phenomena
4. **Discovery of intermediate regimes** requiring hybrid theories

### Long-term
1. **Novel theoretical frameworks** validated by data
2. **Automated scientific discovery** of publishable results
3. **Theory-driven experiment design** for validation
4. **Closed-loop theory improvement** matching human scientists

---

## API Endpoints

```bash
# Run unified discovery cycle
curl -X POST "http://localhost:8787/api/unified/discover" \
  -H "Content-Type: application/json" \
  -d '{"mode": "parallel", "data_source": "sdss"}'

# Get discovery summary
curl "http://localhost:8787/api/unified/summary"

# Get top candidates
curl "http://localhost:8787/api/unified/candidates?n=10"

# Get full candidate report
curl "http://localhost:8787/api/unified/candidate/{theory_name}/report"

# Validate specific theory
curl -X POST "http://localhost:8787/api/unified/validate" \
  -H "Content-Type: application/json" \
  -d '{"theory_name": "Entropic Gravity", "data": [...]}'
```

---

## Comparison: Before vs After

### Before (Phase 2):
```
Theory modules → Generate novel concepts
     ↓
Numerical modules → Find patterns in data
     ↓
Independent paths, no integration
```

### After (Phase 3):
```
Theory modules → Generate predictions
     ↓
Validation Bridge → Test against data
     ↓
     ↓
     ↙   ↘
Disagreement? → Yes → Refinement Engine → Modify theory
     ↓
     ↓
     ↙   ↘
Agreement? → Yes → Theory strengthened
     ↓
Unified output: Validated, refined theories
```

---

## Key Innovations

### 1. **Theory-Data Feedback Loop**
Theories are no longer static; they evolve based on data feedback, just like in real science.

### 2. **Quantified Discrepancy Analysis**
Not just "theory disagrees with data" but specifically:
- Systematic bias (constant offset)
- Scale mismatch (amplitude wrong)
- Local outliers (missing physics)

### 3. **Specific Refinement Suggestions**
Not just "refine theory" but:
- "Add term: + 0.3" (specific parameter)
- "Change power law exponent from 2.0 to 2.3" (data-driven)
- "Add regime-dependent term for r > 10" (regional)

### 4. **Theory Evolution Tracking**
Each theory tracks:
- All validation results
- Confidence trajectory over time
- Refinements applied
- Overall improvement

### 5. **Multi-Mode Discovery**
Different strategies for different situations:
- Theory-first: Testing specific theoretical frameworks
- Data-first: Explaining unexpected patterns
- Parallel: Both simultaneously (most common)

---

## Testing

```python
from astra_live_backend.unified_discovery_engine import UnifiedDiscoveryEngine
from astra_live_backend.theory_data_validator import TheoryDataValidator, TheoryPrediction

# Test validator
validator = TheoryDataValidator()

theory = TheoryPrediction(
    theory_name="Test Theory",
    prediction_type="functional",
    mathematical_form="y = 2*x + 1",
    variables={'x': 'input', 'y': 'output'},
    parameters={},
    confidence=0.7
)

data = np.array([1, 3, 5, 7, 9])
predicted = 2*data + 1

result = validator.validate_theoretical_prediction(theory, data)
print(f"Agreement: {result.agreement_score:.3f}")
print(f"Status: {result.status.value}")

# Test unified engine
engine = UnifiedDiscoveryEngine()
result = engine.run_unified_discovery_cycle()

print(f"\nCycle {result.cycle_id}:")
print(f"  Generated: {result.theories_generated}")
print(f"  Validated: {result.theories_validated}")
print(f"  Refined: {result.theories_refined}")
```

---

## Impact on ASTRA's Capabilities

### Capabilities Matrix

| Capability | Phase 1 | Phase 2 | Phase 3 (Unified) |
|-----------|---------|---------|------------------|
| Pattern discovery | ✅ | ✅ | ✅ |
| Statistical testing | ✅ | ✅ | ✅ |
| Novel theoretical concepts | ❌ | ✅ | ✅ |
| Theory validation | ❌ | ❌ | ✅ |
| Theory refinement | ❌ | ❌ | ✅ |
| Theory-data integration | ❌ | ❌ | ✅ |
| Closed-loop discovery | ❌ | ❌ | ✅ |

### New Discovery Types

1. **Validated Theories**: Theories that have been tested against data
2. **Refined Theories**: Theories improved based on data feedback
3. **Theory-Data Convergence**: Independent theory and data pointing to same conclusion
4. **Discrepancy-Driven Discoveries**: New physics from systematic theory-data mismatches

---

## Conclusion

The Unified Discovery Engine represents a **fundamental evolution** in ASTRA's capabilities:

**From**: Independent theoretical and numerical discovery
**To**: Integrated closed-loop scientific discovery

This mirrors how human scientists work:
1. Propose theory
2. Test against data
3. Refine if needed
4. Repeat

**Status**: ✅ **COMPLETE AND READY FOR INTEGRATION**

Files created:
- `astra_live_backend/theory_data_validator.py` (Theory-Data Validation Bridge)
- `astra_live_backend/unified_discovery_engine.py` (Unified Discovery Engine)
- `UNIFIED_DISCOVERY_ARCHITECTURE.md` (This document)

**Next**: Integrate into ASTRA's UPDATE phase and begin unified discovery cycles.
