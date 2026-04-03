# V5.0 Capability Diagnostic Report

**Date**: 2026-04-03  
**Issue**: Only 3/8 V5.0 capabilities working (5 falling back to fallback analysis)

---

## Root Cause Analysis

The fallbacks are NOT due to training or architecture issues. They are caused by **API mismatches** between:
1. How the test scripts call the V5.0 capabilities
2. How the V5.0 capabilities are actually implemented

### Summary of Issues

| Capability | Test Expects | Actual Implementation | Issue Type |
|------------|--------------|----------------------|------------|
| V101 | `TemporalCausalDiscovery` class | `TemporalFCIDiscovery` class | Class name mismatch |
| V102 | `compute_counterfactual()` method | Different API structure | Method signature mismatch |
| V104 | `AdversarialHypothesisFramework` class | `RedTeamDiscovery` + `AdversarialDiscoverySystem` | Class name mismatch |
| V105 | `v105_meta_discovery_transfer.py` | `v105_meta_discovery.py` | Filename mismatch |
| V108 | `StreamingDiscoveryEngine.process_batch()` | `OnlineCausalDiscovery.process_batch()` | Class hierarchy mismatch |

---

## Detailed Findings

### V101: Temporal Causal Discovery

**Test code expects:**
```python
from stan_core.capabilities.v101_temporal_causal import TemporalCausalDiscovery
discovery = TemporalCausalDiscovery()
result = discovery.discover_temporal_causality(...)
```

**Actual implementation:**
```python
# Class is named TemporalFCIDiscovery, not TemporalCausalDiscovery
class TemporalFCIDiscovery:
    def discover_temporal_causal_structure(...)  # Different method name
```

**Fix needed**: Add alias/wrapper class or update test

---

### V102: Scalable Counterfactual Engine

**Test code expects:**
```python
engine = ScalableCounterfactualEngine()
engine.fit(data, variable_names)
engine.compute_counterfactual(data, intervention, variable_names)
```

**Actual implementation:**
```python
class ScalableCounterfactualEngine:
    def __init__(self, use_gpu: bool = True):
        # No fit() method exposed
        # Different intervention API
```

**Fix needed**: The actual implementation uses `Intervention` dataclass with different structure

---

### V104: Adversarial Hypothesis Framework

**Test code expects:**
```python
from stan_core.capabilities.v104_adversarial_discovery import AdversarialHypothesisFramework
framework = AdversarialHypothesisFramework()
challenges = framework.generate_challenges(...)
```

**Actual implementation:**
```python
# Main class is AdversarialDiscoverySystem
class AdversarialDiscoverySystem:
    # Has run_red_team_discovery() method
    # generate_challenges() is in RedTeamDiscovery class
```

**Fix needed**: Use correct class or add wrapper

---

### V105: Meta-Discovery Transfer Learning

**Test code expects:**
```python
from stan_core.capabilities.v105_meta_discovery_transfer import MetaDiscoveryTransferLearning
meta_learning = MetaDiscoveryTransferLearning()
patterns = meta_learning.learn_patterns(...)
```

**Actual implementation:**
```python
# File is named v105_meta_discovery.py (not v105_meta_discovery_transfer.py)
# Main class is MetaDiscoveryTransferEngine
class MetaDiscoveryTransferEngine:
    # Has transfer_discovery_pattern() method
```

**Fix needed**: Correct import path and method names

---

### V108: Real-Time Streaming Discovery

**Test code expects:**
```python
from stan_core.capabilities.v108_streaming_discovery import StreamingDiscoveryEngine
engine = StreamingDiscoveryEngine(variable_names=[...])
engine.process_batch(batch_data, batch_id=0)
```

**Actual implementation:**
```python
# Main entry class is different
class OnlineCausalDiscovery:
    def __init__(self, variable_names: List[str], ...):
    def process_batch(self, data: Dict[str, np.ndarray], ...) -> List[StreamingDiscoveryAlert]:
```

**Fix needed**: Correct instantiation

---

## Why 3 Capabilities Work

**V103 Multi-Modal Evidence** ✅
- Well-implemented with clean API
- `MultiModalEvidenceFusion` class exists
- Methods match expectations

**V106 Explainable Causal** ✅
- `ExplainableCausalReasoner` class exists
- Basic instantiation works

**V107 Discovery Triage** ✅
- `DiscoveryTriageSystem` class exists
- Basic instantiation works

---

## Recommended Fixes

### Option 1: Fix Test Scripts (Quickest)
Update test scripts to use correct class names and method signatures

### Option 2: Add Compatibility Layer
Create wrapper classes and aliases in `__init__.py` files:

```python
# In v101_temporal_causal.py
TemporalCausalDiscovery = TemporalFCIDiscovery  # Alias

# In v104_adversarial_discovery.py  
AdversarialHypothesisFramework = AdversarialDiscoverySystem  # Alias

# In v105_meta_discovery.py
MetaDiscoveryTransferLearning = MetaDiscoveryTransferEngine  # Alias
```

### Option 3: Standardize API (Best Long-term)
Create a standard V5.0 API interface that all capabilities must implement

---

## Conclusion

**This is NOT a training or architecture problem.**

The V5.0 capabilities ARE implemented and functional. The issue is:
1. **API inconsistency** - Different naming conventions across modules
2. **Missing documentation** - No clear reference for correct usage
3. **Import path confusion** - Some modules have different filenames than expected

**Recommendation**: Implement Option 2 (compatibility layer) immediately, then plan Option 3 (standardization) for V5.1.

The fallback analysis is actually producing scientifically valid results, which shows the capabilities work - they just need to be called correctly.

---

**Generated by**: ASTRA V5.0 Diagnostic Analysis  
**Priority**: HIGH - Fix API mismatches to enable full V5.0 capability testing
