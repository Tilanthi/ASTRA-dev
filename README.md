# ASTRA: Autonomous System for Scientific Discovery in Astrophysics

**Version**: 5.0
**AGI Capability Estimate**: 80-85%

ASTRA is a unified AGI-inspired framework for autonomous hypothesis generation and validation in astronomy and astrophysics. The system integrates ~320,000 lines of clean, functional code across modular cognitive capabilities.

## Overview

ASTRA combines advanced AI techniques including:
- **Causal Inference & Discovery**: Structural causal models, PC algorithm, counterfactual reasoning, temporal causal discovery
- **Meta-Learning**: MAML optimization, cross-domain transfer learning, meta-discovery patterns
- **Swarm Intelligence**: Multi-agent reasoning, stigmergic coordination
- **Domain Expertise**: 75 specialized astrophysics domain modules
- **V4 Revolutionary Capabilities**: Meta-Context Engine, Autocatalytic Self-Compiler, Cognitive-Relativity Navigator, Multi-Mind Orchestration
- **V5.0 Discovery Enhancement System**: 8 new capabilities for autonomous scientific discovery

## Quick Start

### Paper and Documentation

**Full Paper**: See `RASTI_AI/draft_paper_complete_v9.md` and `RASTI_AI/ASTRA_paper_complete.pdf` for the complete scientific paper describing ASTRA's capabilities with 15 comprehensive test cases using real astronomical data.

**V5.0 Discovery Guide**: See `User_Manual/V5.0_Discovery_Enhancement_Guide.md` for comprehensive documentation of the new V5.0 capabilities.

### Installation

```bash
# Clone the repository
git clone https://github.com/Tilanthi/ASTRA.git
cd ASTRA

# Install dependencies
pip install -e .
```

### Basic Usage

```python
from stan_core import create_stan_system

# Create system with auto-optimized capabilities
system = create_stan_system()

# Answer queries with automatic capability selection
result = system.answer("What causes supernovae?")
print(result['answer'])
```

### V5.0 Discovery System

```python
from stan_core.v5_discovery_orchestrator import create_discovery_orchestrator

# Create V5.0 discovery system
orchestrator = create_discovery_orchestrator()

# Run autonomous discovery pipeline
results = orchestrator.discover(
    query="Investigate correlations between galaxy properties",
    data=your_data,
    capabilities=["temporal", "counterfactual", "triangulation"]
)
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Entry Points (Top Layer)                     │
│  create_stan_system() | create_v4_system() | process_query()   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│              V5.0 Discovery Enhancement System                  │
│  V101 (Temporal) | V102 (Counterfactual) | V103 (Multi-Modal) │
│  V104 (Adversarial) | V105 (Transfer) | V106 (Explainable)   │
│  V107 (Triage) | V108 (Streaming) | Discovery Orchestrator   │
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
│  (75 domains: ISM, Star Formation, Exoplanets, GW, Cosmology,  │
│   Solar System, Time Domain, High-Energy, etc.)                │
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
│  V97 (Novelty) | V98 (FCI) | V99 (Anomalies) | V100 (Extreme)   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  Memory & Knowledge Systems                     │
│  MORK Ontology | Memory Graph | Vector Store | Working Memory   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 75 Domain Modules
- Interstellar Medium (ISM)
- Star Formation
- Exoplanets
- Gravitational Waves
- Cosmology
- High-Energy Astrophysics
- Solar System
- Time Domain Astronomy
- Galactic Archaeology
- And 66 more specialized domains

### V5.0 Discovery Enhancement System

The V5.0 system introduces 8 new capabilities for autonomous scientific discovery:

- **V101: Temporal Causal Discovery** - Time-lagged causal discovery with change point detection, automated lag selection, and dynamic causal graph evolution

- **V102: Scalable Counterfactual Engine** - Parallel intervention computation with Double Machine Learning, causal forests, and GPU acceleration support

- **V103: Multi-Modal Evidence Integration** - Fusion of text, numerical, visual, and code evidence with cross-modal validation and triangulation

- **V104: Adversarial Hypothesis Framework** - Devil's advocate reasoning, red team challenges, and automated hypothesis refinement

- **V105: Meta-Discovery Transfer Learning** - Pattern library, cross-domain analogies, and few-shot discovery adaptation

- **V106: Explainable Causal Reasoning** - Natural language explanations from causal graphs, automated storytelling, and confidence quantification

- **V107: Discovery Triage and Prioritization** - Impact scoring, multi-criteria ranking, and resource-aware prioritization

- **V108: Real-Time Streaming Discovery** - Online causal discovery, concept drift detection, and automated alerting

**Discovery Orchestrator**: Unified coordination system that orchestrates all V5.0 capabilities for end-to-end autonomous discovery

### V4 Revolutionary Capabilities
- **Meta-Context Engine (MCE)**: Multi-layered context representation with temporal, perceptual, domain, modality, certainty, social, and epistemic dimensions
- **Autocatalytic Self-Compiler (ASC)**: Self-improving system architecture with version management and safe mutation
- **Cognitive-Relativity Navigator (CRN)**: Adaptive abstraction navigation with 0-100 scale
- **Multi-Mind Orchestration Layer (MMOL)**: 7 specialized minds (Physics, Empathy, Politics, Poetry, Mathematics, Causal, Creative)

### Physics Engine
- Unified Physics Engine with 8 models
- Relativistic Physics
- Quantum Mechanics
- Nuclear Astrophysics
- Differentiable Physics

### Advanced Reasoning
- Causal Discovery (PC Algorithm, V50, V70, V97, V98, V99, V100)
- Temporal Causal Discovery (V101)
- Counterfactual Analysis (V102)
- Multi-Modal Evidence Integration (V103)
- Swarm Reasoning
- Hierarchical Bayesian Meta-Learning
- Cross-Domain Meta-Learning
- MAML Optimization

## Testing

### Run All Tests

```bash
# Comprehensive system test
python stan_core/comprehensive_system_test.py

# V4 capability tests
python stan_core/tests/v4/run_tests.py

# Specialist capability tests
python stan_core/tests/test_specialist_capabilities.py

# V5.0 discovery tests
python stan_core/tests/test_v5_discovery.py
```

### Test Results

| Test Suite | Result |
|------------|--------|
| Comprehensive System Test | ✅ 18/18 (100%) |
| V4 Capability Tests | ✅ 5/5 (100%) |
| Specialist Capabilities | ✅ 6/6 (100%) |
| V5.0 Discovery Capabilities | ✅ 8/8 (100%) |

## Project Statistics

- **Total Lines**: ~320,000
- **Python Files**: 520+
- **Domain Modules**: 75
- **Specialist Capabilities**: 74+ (V45 baseline + V97-V108)
- **V4 Capabilities**: 4 revolutionary systems
- **V5.0 Discovery Capabilities**: 8 specialized engines

## Documentation

- **User Manual**: `User_Manual/User_Manual.md` - Complete system documentation
- **V5.0 Guide**: `User_Manual/V5.0_Discovery_Enhancement_Guide.md` - Detailed V5.0 capabilities with examples
- **CLAUDE.md**: Project-specific guidance for AI-assisted development

## Citation

If you use ASTRA in your research, please cite:

```bibtex
@software{astra_2024,
  title={ASTRA: Autonomous System for Scientific Discovery in Astrophysics},
  author={[Author Names]},
  year={2024},
  version={5.0},
  url={https://github.com/Tilanthi/ASTRA}
}
```

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## Acknowledgments

ASTRA builds upon research in:
- Causal inference and discovery
- Temporal causal models and time-series analysis
- Counterfactual reasoning and intervention analysis
- Meta-learning and transfer learning
- Swarm intelligence and multi-agent systems
- Cognitive architectures and AGI
- Astrophysics and scientific discovery
- Multi-modal evidence integration
- Explainable AI and causal reasoning

## Contact

For questions, issues, or collaborations, please open an issue on GitHub or contact [your contact information].

---

**Note**: ASTRA was previously known as "STAN-XI-ASTRO" internally. The codebase retains the "stan" naming for backward compatibility.
