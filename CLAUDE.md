# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ASTRA** (Autonomous System for Scientific Discovery in Astrophysics) is a unified AGI-inspired framework for autonomous hypothesis generation and validation in astronomy and astrophysics. The system integrates ~303,000 lines of clean, functional code across modular cognitive capabilities.

**Version**: 4.7
**AGI Capability Estimate**: 70-75%

### IMPORTANT: Naming Convention

The system was previously known as "STAN-XI-ASTRO" or "STAN". **It must now be referred to exclusively as "ASTRA"** in all:
- Academic papers and documentation
- External communications
- User-facing text
- Paper titles and abstracts

The internal codebase (module names, file paths, function names) retains the original "stan" naming for backward compatibility, but all external references should use "ASTRA".

**Full name**: ASTRA: Autonomous System for Scientific Discovery in Astrophysics
**Subtitle**: An AGI-inspired framework for autonomous hypothesis generation and validation

---

## CRITICAL: Persistent Memory Initialization

**IMPORTANT**: At the start of EVERY session, initialize the persistent memory system. This ensures:
- Previous session context is restored
- Known hallucinations are loaded and prevented
- User preferences are applied
- Anti-hallucination protection is active

```python
# RUN THIS AT SESSION START
from stan_core.memory.persistent import create_integrator, quick_hallucination_check

integrator = create_integrator()
integrator.initialize_session()
```

### Before Making Any Factual Claim

ALWAYS verify numerical claims against the hallucination register:

```python
result = integrator.verify_claim_before_output("54 MHz observations")
if not result.safe:
    # Use the correct value instead
    correct = result.hallucination_match.correct_value
```

### Known Hallucinations

The hallucination register is stored in `~/.stan_persistent/hallucination_register.json`.
To view or manage entries:

```python
from stan_core.memory.persistent import BootstrapMemory
bm = BootstrapMemory()
bm.list_hallucinations()  # View all entries
bm.remove_hallucination("54 MHz")  # Remove if no longer needed
```

### Document Review Protocol

When reviewing ANY document:
1. Extract key info first (frequencies, sample sizes, instruments)
2. Verify each claim with `quick_hallucination_check()`
3. Include mandatory anti-hallucination verification table in all reviews

### Checkpoint During Long Sessions

```python
# Periodically save session state
integrator.create_session_checkpoint({"current_task": "your task description"})
```

---

## Quick Start

### Basic System Usage

```python
from stan_core import create_stan_system

# Create system with auto-optimized capabilities
system = create_stan_system()

# Answer queries with automatic capability selection
result = system.answer("What causes filament width variations?")
print(result['answer'])
```

### V4.0 Revolutionary Capabilities

```python
from stan_core.v4_revolutionary import create_v4_system, IntegrationMode

# Create V4.0 system with MCE, ASC, CRN, MMOL capabilities
system = create_v4_system()

# Process with different integration modes
result = system.process_query("Anze query", mode=IntegrationMode.FULL)
```

### Individual Capability Usage

```python
# Meta-Context Engine
from stan_core.metacognitive.meta_context_engine import create_meta_context_engine
mce = create_meta_context_engine()
result = mce.layer_context(query, dimensions=["temporal", "perceptual"])

# Domain modules
from stan_core.domains import DomainRegistry
registry = DomainRegistry()
registry.load_all_domains()
result = registry.process_query("pulsar timing analysis")

# Physics engine
from stan_core.physics import UnifiedPhysicsEngine
physics = UnifiedPhysicsEngine()
result = physics.compute("blackbody", {"temperature": 5778, "wavelength": 500e-7})

# MAML optimizer
from stan_core.reasoning.maml_optimizer import create_maml_optimizer
optimizer = create_maml_optimizer(model_fn, loss_fn, n_inner_steps=5)
```

---

## Testing

### Run All Tests

```bash
# Run V4.0 capability tests
python stan_core/tests/v4/run_tests.py

# Run specialist capability tests (66 V45 capabilities)
python stan_core/tests/test_specialist_capabilities.py

# Run Phase 2-4 enhancement tests
python stan_core/tests/test_phase_2_4.py
```

### Run Specific Tests

```bash
# V4.0 individual capabilities
python stan_core/tests/v4/run_tests.py --mce        # Meta-Context Engine
python stan_core/tests/v4/run_tests.py --asc        # Autocatalytic Self-Compiler
python stan_core/tests/v4/run_tests.py --crn        # Cognitive-Relativity Navigator
python stan_core/tests/v4/run_tests.py --mmol       # Multi-Mind Orchestration
python stan_core/tests/v4/run_tests.py --integration # Integration tests
```

### Test Individual Components

```python
# Test physics modules
python -c "from stan_core.physics.relativistic_physics import RelativisticPhysics; print(RelativisticPhysics.schwarzschild_radius(1.989e33))"

# Test domain modules
python -c "from stan_core.domains.high_energy import create_high_energy_domain; d = create_high_energy_domain(); print(d.get_capabilities())"

# Test MAML optimizer
python -c "from stan_core.reasoning.maml_optimizer import MAMLOptimizer; print('MAML imported')"
```

---

## Architecture Overview

### System Layers (Bottom to Top)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Entry Points (Top Layer)                     │
│  create_stan_system() | create_v4_system() | process_query()   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                 V4.0 Revolutionary Capabilities                  │
│  MCE (Context) | ASC (Self-Improvement) | CRN (Abstraction)    │
│  MMOL (7 Specialized Minds)                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Domain Architecture                          │
│  BaseDomainModule → DomainRegistry → Specialized Domains        │
│  (9 domains: ISM, Star Formation, Exoplanets, GW, Cosmology,   │
│   Solar System, Time Domain, High-Energy, Galactic Archaeology) │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                Cross-Domain Meta-Learning                       │
│  MAMLOptimizer | CrossDomainMetaLearner | AdaptationResult      │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   Physics & Causal Engines                      │
│  UnifiedPhysicsEngine | StructuralCausalModel | PCAlgorithm      │
│  PhysicsCurriculum | PhysicalAnalogicalReasoner                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  Memory & Knowledge Systems                     │
│  MORKOntology | MemoryGraph | VectorStore | WorkingMemory       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Capabilities Registry                         │
│  66+ specialist capabilities (V36-V94) with auto-selection      │
└─────────────────────────────────────────────────────────────────┘
```

### Module Communication Patterns

**Domain Hot-Swapping**: All domain modules inherit from `BaseDomainModule` with standardized `process_query()` interface. Domains are loaded/unloaded at runtime via `DomainRegistry`. No system restart required.

**Graceful Degradation**: Every import wrapped in try/except with fallback. Check `BASE_UNIFIED_AVAILABLE`, `DomainRegistry`, etc. for availability before use. System continues in degraded mode when components missing.

**Meta-Learning Coordination**: `CrossDomainMetaLearner` observes all domain queries, builds transfer learning models, enables few-shot adaptation. Connected to `MAMLOptimizer` for inner-loop optimization.

**Multi-Mind Orchestration**: 7 specialized minds (Physics, Empathy, Politics, Poetry, Mathematics, Causal, Creative) process queries in parallel. `MindArbitrator` resolves conflicts using anticipatory confidence prediction.

---

## Key Design Patterns

### 1. Capability Auto-Selection

The system automatically selects capabilities based on task analysis. Do not manually invoke capabilities unless specifically testing individual components.

```python
# WRONG: Manual capability selection
result = system.reasoning.causal_discovery(query)

# CORRECT: Let system auto-select
result = system.answer(query)  # Auto-selects best capabilities
```

### 2. Module Registration Pattern

All domain modules use `@register_domain` decorator or explicit `DomainModuleRegistry.register()`. This enables runtime discovery and hot-swapping.

```python
from stan_core.domains import BaseDomainModule, register_domain

@register_domain
class MyDomain(BaseDomainModule):
    def get_default_config(self):
        return DomainConfig(
            domain_name="my_domain",
            version="1.0.0",
            keywords=["keyword1", "keyword2"],
            capabilities=["capability1", "capability2"]
        )
```

### 3. Factory Function Pattern

All major components use factory functions for creation, not direct constructors. This enables configuration injection and graceful fallback.

```python
# Use factory functions
system = create_stan_system()
mce = create_meta_context_engine()
optimizer = create_maml_optimizer(model_fn, loss_fn)

# NOT: system = UnifiedSTANSystem()  # Avoid direct constructors
```

### 4. Physics Curriculum Learning

Physics capabilities develop through staged curriculum (`ComplexityLevel.BASIC` → `EXPERT`). Do not skip stages. Use `PhysicsCurriculum.get_next_stage()` for progression.

---

## File Organization Conventions

### Capability Files

- **V36-V50 capabilities**: `stan_core/capabilities/vXX_*.py`
- **Physics modules**: `stan_core/physics/*.py` (relativistic_physics.py, quantum_mechanics.py, nuclear_astro.py)
- **Domain modules**: `stan_core/domains/<domain_name>/__init__.py`
- **Meta-learning**: `stan_core/reasoning/maml_optimizer.py`, `cross_domain_meta_learner.py`

### Memory Hierarchy

- **MORK Ontology**: `stan_core/memory/mork_ontology.py` (concept hierarchies)
- **Memory Graph**: `stan_core/memory/context_graph.py` (context relationships)
- **Working Memory**: `stan_core/memory/working/` (7±2 capacity constraint)

### Test Files

- **Integration tests**: `stan_core/tests/v4/test_v4_integration.py`
- **Capability tests**: `stan_core/tests/test_specialist_capabilities.py`
- **Validation**: `stan_core/tests/validation_benchmarks.py`

---

## Important Constants

### Physics Constants (CGS units)

Defined in `UnifiedPhysicsEngine.constants`:
- `G`: 6.674e-8 (gravitational)
- `c`: 2.998e10 (speed of light)
- `h`: 6.626e-27 (Planck)
- `k_B`: 1.381e-16 (Boltzmann)
- `M_sun`: 1.989e33 (solar mass)
- `R_sun`: 6.957e10 (solar radius)

### Abstraction Scale (CRN)

0 = atomic facts, 50 = concepts, 100 = pure philosophy

### Cognitive Frames (MCE)

PREDICTIVE, ANALYTICAL, EMOTIONAL, CREATIVE, CRITICAL, SYNTHETIC, NARRATIVE, CONTEMPLATIVE

---

## Common Pitfalls

1. **Missing Imports**: Always check for import availability. Most imports wrapped in try/except with None fallback. Test `if MODULE is not None:` before use.

2. **Direct Construction**: Never directly instantiate capability classes. Use factory functions: `create_<module>()`.

3. **Hardcoded Physics Values**: Always use `UnifiedPhysicsEngine.constants`, never hardcode physical constants.

4. **Skipping Initialization**: Domain modules must call `.initialize(global_config)` after creation before `.process_query()`.

5. **Backup File Accumulation**: Run `cleanup_stan_core.py` if directory exceeds expected size. Backup files (`*.backup`) from `cleanup_bloat.py` can accumulate to GBs.

---

## PDF Generation Requirements

When generating PDF documents using `stan_core/utils/pdf_generator.py`:

### Critical Rules

1. **NEVER convert single asterisks to italic**: The markdown `*text*` pattern MUST NOT be converted to `<i>text</i>` because asterisks are used in mathematical expressions (e.g., `dyn*cm^2/g^2`). Converting this would produce broken output like `dyn<i>cm^2/g^2</i>`.

2. **Only convert bold formatting**: Only `**text**` should be converted to `<b>text</b>`. This is safe because double asterisks are rarely used in scientific notation.

3. **Escape HTML properly**: All HTML special characters (`<`, `>`, `&`) must be escaped to `&lt;`, `&gt;`, `&amp;` EXCEPT for the intentionally converted bold tags.

4. **Convert unicode to ASCII**: All non-ASCII characters must be converted to ASCII equivalents. Greek letters become names (alpha, beta, gamma), mathematical symbols become ASCII approximations (± -> +/-, × -> x, etc.).

5. **Test PDF output**: Always verify generated PDFs do not contain:
   - Raw HTML tags like `<i>`, `</i>`, `<b>` appearing as visible text
   - Markdown formatting like `**bold**` appearing literally
   - Unicode replacement characters (boxes, question marks)
   - Broken formatting from asterisk-to-italic conversion

### Implementation Pattern

```python
def _process_inline_formatting(self, text: str) -> str:
    # Step 1: Protect bold tags with placeholders
    text = re.sub(r'\*\*([^*]+?)\*\*', r'%%BOLD_START%%\1%%BOLD_END%%', text)

    # Step 2: Escape ALL HTML special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    # Step 3: Restore protected bold tags
    text = text.replace('%%BOLD_START%%', '<b>')
    text = text.replace('%%BOLD_END%%', '</b>')

    # DO NOT convert single * to <i> - causes math expression corruption!
    return text
```

---

## Development Workflow

1. **Test before modifying**: Always run relevant tests first to establish baseline
2. **Respect graceful degradation**: Any new module must have try/except imports and fallback behavior
3. **Use factory functions**: Create via `create_<module>()` pattern
4. **Register new domains**: Use `@register_domain` decorator for discoverability
5. **Update exports**: Add new public classes to `__all__` in module `__init__.py`

---

## Post-Upgrade Verification Testing

**CRITICAL**: After any substantial upgrade to STAN functionality or stan_core components, comprehensive verification testing MUST be performed to ensure all dependencies, files, and components remain properly linked.

### When to Run Comprehensive Tests

Run the comprehensive system verification after:
- Adding new domain modules
- Modifying core architecture (unified.py, unified_enhanced.py)
- Updating physics engine or models
- Changes to memory systems
- Adding or modifying reasoning capabilities
- Refactoring module dependencies
- Any changes to import chains or module registration

### Comprehensive Test Procedure

```bash
# Run the comprehensive system test
python stan_core/comprehensive_system_test.py

# Expected output: All 18 capabilities should PASS (100%)
```

The comprehensive test verifies:
- **75 Domain Modules**: Import, instantiation, and query handling (100% pass rate required)
- **Memory Systems**: MORK Ontology, Context Graph, Working Memory, Episodic Memory
- **Physics Engine**: UnifiedPhysicsEngine with all models and constraints
- **Causal Discovery**: V50, V70, and astrophysical causal discovery engines
- **Advanced Reasoning**: Swarm reasoning, hierarchical Bayesian meta-learning
- **V4 Capabilities**: Meta-Context Engine (if available)
- **Orchestrator Integration**: create_stan_system(), answer(), process_query()

### Fix-Test Loop

If errors are found:
1. **Fix the identified error** (missing imports, broken dependencies, incorrect signatures, etc.)
2. **Re-run the comprehensive test**
3. **Repeat** until ALL capabilities pass (100% pass rate)
4. **Document the fix** if it's a recurring pattern

### Test Files Reference

- **Comprehensive Test**: `stan_core/comprehensive_system_test.py`
- **Domain Validation**: `stan_core/tests/validation_benchmarks.py`
- **V4 Integration Tests**: `stan_core/tests/v4/test_v4_integration.py`
- **Specialist Capabilities**: `stan_core/tests/test_specialist_capabilities.py`

### Verification Report

After successful verification, update the verification report:
```bash
# Update RASTI/SYSTEM_VERIFICATION_COMPLETE.md with current status
```

The report should document:
- Date and version of verification
- All 75 domains with PASS status
- All 18+ advanced capabilities with PASS status
- Cross-module dependency verification
- Any issues found and resolved

---

## Code Statistics

- **Total Lines**: 280,808
- **Python Files**: 514
- **Directory Size**: ~9 MB (after cleanup from 3.6 GB of backups)
- **Specialist Capabilities**: 66 (V45 baseline)
- **Domain Modules**: 75 (23 core + 48 astrophysics)
- **Physics Stages**: 15 learning stages (relativistic, quantum, nuclear)
