# ASTRA stan_core Migration Guide

**Version**: 1.0
**Date**: April 2026
**Refactoring**: Remove Vxxx version numbers for coherent structure

---

## Overview

The stan_core codebase has been refactored to remove confusing Vxxx version numbers from directory and file names. This creates a cleaner, more professional organization that is easier to navigate and understand.

---

## What Changed

### Directory Renames

| Old Path | New Path | Notes |
|----------|----------|-------|
| `v7_autonomous_research/` | `autonomous_research/` | V7.0 system |
| `v4_revolutionary/` | `revolutionary/` | V4.0 capabilities |
| `v5_discovery/` | `discovery_enhancement/` | V5.0 discovery |
| `v100/` | `simulation/` | V100 simulation system |
| `core_legacy/` | `legacy_archives/systems/` | Archived legacy systems |

### Capability File Reorganization

**36 capability files** have been reorganized into logical subdirectories:

```
capabilities/
├── causal/              # Causal inference (5 files)
├── discovery/            # Discovery capabilities (6 files)
├── learning/             # Learning capabilities (5 files)
├── cognitive/            # Cognitive capabilities (5 files)
├── memory/               # Memory capabilities (1 file)
├── metacognitive/        # Meta-cognitive capabilities (6 files)
├── synthesis/            # Synthesis capabilities (4 files)
├── multimodal/           # Multimodal capabilities (2 files)
└── integration/          # Integration capabilities (2 files)
```

### Test Directory Reorganization

| Old Path | New Path |
|----------|----------|
| `tests/v4/` | `tests/test_revolutionary/` |
| `tests/v5/` | `tests/test_discovery/` |
| (new) | `tests/test_autonomous_research/` |

---

## Migration Guide for Users

### Updating Your Imports

If your code imports from the old versioned locations, you need to update your imports:

#### Old Import Style (Deprecated)

```python
# OLD - These still work but will show deprecation warnings
from stan_core.v7_autonomous_research import create_v7_scientist
from stan_core.capabilities.v50_causal_engine import CausalEngine
from stan_core.capabilities.v70_meta_scientific import MetaScientific
from stan_core.capabilities.v105_meta_discovery import MetaDiscovery
```

#### New Import Style (Recommended)

```python
# NEW - Use these instead
from stan_core.autonomous_research import create_scientist
from stan_core.capabilities.causal import CausalEngine
from stan_core.capabilities.metacognitive import MetaScientific
from stan_core.capabilities.discovery import MetaDiscovery
```

### Specific Import Mappings

| Old Import | New Import |
|------------|------------|
| `from stan_core.v7_autonomous_research import create_v7_scientist` | `from stan_core.autonomous_research import create_scientist` |
| `from stan_core.capabilities.v50_causal_engine import ...` | `from stan_core.capabilities.causal import ...` |
| `from stan_core.capabilities.v105_meta_discovery import ...` | `from stan_core.capabilities.discovery import ...` |
| `from stan_core.capabilities.v70_meta_scientific import ...` | `from stan_core.capabilities.metacognitive import ...` |
| `from stan_core.capabilities.v50_meta_learner import ...` | `from stan_core.capabilities.learning import ...` |
| `from stan_core.capabilities.v60_cognitive_agent import ...` | `from stan_core.capabilities.cognitive import ...` |
| `from stan_core.capabilities.v70_analogical_transfer import ...` | `from stan_core.capabilities.synthesis import ...` |
| `from stan_core.capabilities.v102_counterfactual_engine import ...` | `from stan_core.capabilities.synthesis import ...` |

---

## Migration Examples

### Example 1: Using Autonomous Research

**Before:**
```python
from stan_core.v7_autonomous_research import create_v7_scientist

scientist = create_v7_scientist()
questions = scientist.generate_research_questions("ism")
```

**After:**
```python
from stan_core.autonomous_research import create_scientist

scientist = create_scientist()
questions = scientist.generate_research_questions("ism")
```

### Example 2: Using Causal Capabilities

**Before:**
```python
from stan_core.capabilities.v50_causal_engine import CausalEngine
from stan_core.capabilities.v98_fci_causal_discovery import FCIDiscovery
from stan_core.capabilities.v106_explainable_causal import ExplainableCausal
```

**After:**
```python
from stan_core.capabilities.causal import (
    CausalEngine,
    FCIDiscovery,
    ExplainableCausal
)
```

### Example 3: Using Metacognitive Capabilities

**Before:**
```python
from stan_core.capabilities.v70_meta_scientific import MetaScientific
from stan_core.capabilities.v70_synthetic_intelligence import SyntheticIntelligence
from stan_core.capabilities.v70_hypothesis_generator import HypothesisGenerator
```

**After:**
```python
from stan_core.capabilities.metacognitive import (
    MetaScientific,
    SyntheticIntelligence,
    HypothesisGenerator
)
```

### Example 4: Using Discovery Capabilities

**Before:**
```python
from stan_core.capabilities.v105_meta_discovery import MetaDiscovery
from stan_core.capabilities.v104_adversarial_discovery import AdversarialDiscovery
from stan_core.capabilities.v70_algorithmic_discovery import AlgorithmicDiscovery
```

**After:**
```python
from stan_core.capabilities.discovery import (
    MetaDiscovery,
    AdversarialDiscovery,
    AlgorithmicDiscovery
)
```

---

## Backward Compatibility

### Deprecation Warnings

Old imports will continue to work but will show deprecation warnings:

```python
# This still works but warns:
from stan_core.v7_autonomous_research import create_v7_scientist
# Warning: "Importing from stan_core.v7_autonomous_research is deprecated. 
#          Use stan_core.autonomous_research instead. Will be removed in version 8.0."
```

### Migration Timeline

- **Current (Version 7.0)**: Old imports work with deprecation warnings
- **Version 7.5**: Old imports work but warnings are more frequent
- **Version 8.0**: Old imports removed, only new imports supported

---

## Finding What You Need

### If You Used V7 Autonomous Research

```python
# Old:
from stan_core.v7_autonomous_research import V7AutonomousScientist, create_v7_scientist

# New:
from stan_core.autonomous_research import V7AutonomousScientist, create_scientist
```

### If You Used V50 Capabilities

```python
# Old:
from stan_core.capabilities.v50_causal_engine import CausalEngine
from stan_core.capabilities.v50_meta_learner import MetaLearner

# New:
from stan_core.capabilities.causal import CausalEngine
from stan_core.capabilities.learning import MetaLearner
```

### If You Used V70 Capabilities

```python
# Old:
from stan_core.capabilities.v70_meta_scientific import MetaScientific
from stan_core.capabilities.v70_analogical_transfer import AnalogicalTransfer

# New:
from stan_core.capabilities.metacognitive import MetaScientific
from stan_core.capabilities.synthesis import AnalogicalTransfer
```

---

## New Directory Structure for Reference

```
stan_core/
├── autonomous_research/      # V7.0 system (no v7 in name)
├── revolutionary/             # V4.0 capabilities (no v4 in name)
├── discovery_enhancement/     # V5.0 discovery (no v5 in name)
├── simulation/                # V100 simulation (no v100 in name)
├── legacy_archives/           # Archived legacy systems
│   └── systems/
│       ├── v36_system.py
│       ├── v37_system.py
│       └── ... (all archived)
├── capabilities/              # Unified capabilities (organized by function)
│   ├── causal/
│   ├── discovery/
│   ├── learning/
│   ├── cognitive/
│   ├── memory/
│   ├── metacognitive/
│   ├── synthesis/
│   ├── multimodal/
│   └── integration/
├── tests/                     # Unified tests
│   ├── test_revolutionary/
│   ├── test_discovery/
│   └── test_autonomous_research/
└── [all other directories - unchanged]
```

---

## Benefits of New Structure

1. **No Version Confusion**: No more wondering which version to use
2. **Logical Organization**: Capabilities grouped by function
3. **Professional Appearance**: Clean, coherent structure
4. **Easier Navigation**: Find what you need by category
5. **Better Scalability**: Easy to add new capabilities
6. **Maintainable**: Clear separation of concerns

---

## Need Help?

If you encounter issues migrating to the new structure:

1. Check this migration guide
2. Look at the refactoring plan: `stan_core/REFACTORING_PLAN.md`
3. Check for deprecation warnings in your code
4. Update imports following the examples above
5. Test your code after migration

---

## Summary

- **176 files changed** in the refactoring
- **36 capability files** reorganized into 9 subdirectories
- **4 major directories** renamed (v7, v4, v5, v100)
- **Legacy systems** archived for future reference
- **New imports** are cleaner and more intuitive
- **Old imports** still work with deprecation warnings

The refactored structure is **backward compatible** but we recommend migrating to the new import style for cleaner code.

---

**Document Version**: 1.0
**Last Updated**: 2026-04-03
**Refactoring Branch**: refactor/remove-version-numbers
