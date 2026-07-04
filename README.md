# ASTRA: Autonomous Scientific Discovery in Astrophysics

ASTRA is a unified AGI-inspired framework for autonomous hypothesis generation and validation in astronomy and astrophysics. The system integrates ~320,000 lines of clean, functional code across modular cognitive capabilities.

## Overview

ASTRA combines advanced AI techniques including:

- **Causal Inference & Discovery**: Structural causal models, PC algorithm, counterfactual reasoning, temporal causal discovery
- **Meta-Learning**: MAML optimization, cross-domain transfer learning, meta-discovery patterns
- **Swarm Intelligence**: Multi-agent reasoning, stigmergic coordination
- **Domain Expertise**: 75 specialized astrophysics domain modules
- **Theory Engine**: Advanced theoretical reasoning and hypothesis generation
- **Meta-Cognitive Systems**: Multi-layered context representation, self-improvement, abstraction navigation

## Quick Start

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
from astra_core import create_stan_system

# Create system with auto-optimized capabilities
system = create_stan_system()

# Answer queries with automatic capability selection
result = system.answer("What causes supernovae?")
print(result['answer'])
```

### Discovery System

```python
from astra_core.discovery_orchestrator import create_discovery_orchestrator

# Create discovery system
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
│                    Entry Points                                 │
│  create_stan_system() | process_query()                        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Theory Engine                                │
│  Theoretical reasoning | Hypothesis generation | Validation    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│              Meta-Cognitive Capabilities                        │
│  Meta-Context Engine | Self-Compiler | Abstraction Navigator  │
│  Multi-Mind Orchestration                                      │
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
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  Memory & Knowledge Systems                     │
│  MORK Ontology | Memory Graph | Vector Store | Working Memory   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 75 Domain Modules

Specialized astrophysics domains including:
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

### Theory Engine

Advanced theoretical reasoning capabilities:
- Hypothesis generation from first principles
- Theoretical model development
- Mathematical derivation and validation
- Physical consistency checking
- Novel theoretical prediction

### Discovery Enhancement System

Comprehensive discovery capabilities:
- **Temporal Causal Discovery** - Time-lagged causal discovery with change point detection
- **Counterfactual Engine** - Parallel intervention computation with advanced ML
- **Multi-Modal Evidence Integration** - Fusion of text, numerical, and visual evidence
- **Adversarial Hypothesis Framework** - Devil's advocate reasoning and refinement
- **Meta-Discovery Transfer Learning** - Cross-domain analogies and adaptation
- **Explainable Reasoning** - Natural language explanations and confidence quantification
- **Discovery Triage** - Impact scoring and resource-aware prioritization
- **Real-Time Discovery** - Online causal discovery and automated alerting

### Genuine Literature Validation (NEW v2.0)

Advanced scientific validation system:
- **Multi-Stage Validation Pipeline** - 5-stage validation (literature, semantic, citation, formula, statistical)
- **Query Optimization System** - Intelligent multi-strategy literature search (60-80%+ success rate)
- **Real arXiv/ADS Integration** - Live scientific paper retrieval and comparison
- **Semantic Similarity Analysis** - Machine learning-based novelty detection using SPECTER model
- **Scientific Term Extraction** - Handles astronomical abbreviations and technical concepts
- **Citation Validation** - Detects hallucinated references by cross-checking literature
- **Formula & Statistical Validation** - Mathematical consistency and statistical rigor checks
- **Autonomous Discovery Operation** - Continuous 1-minute discovery cycles with genuine validation

### Meta-Cognitive Capabilities

- **Meta-Context Engine**: Multi-layered context representation across temporal, perceptual, domain, modality, and epistemic dimensions
- **Autocatalytic Self-Compiler**: Self-improving system architecture with version management
- **Cognitive-Relativity Navigator**: Adaptive abstraction navigation across scales
- **Multi-Mind Orchestration**: 7 specialized minds (Physics, Empathy, Politics, Poetry, Mathematics, Causal, Creative)

### Physics Engine

- Unified Physics Engine with 8 models
- Relativistic Physics
- Quantum Mechanics
- Nuclear Astrophysics
- Differentiable Physics

### Advanced Reasoning

- Causal Discovery (PC Algorithm, multiple specialized engines)
- Temporal Causal Discovery
- Counterfactual Analysis
- Multi-Modal Evidence Integration
- Swarm Reasoning
- Hierarchical Bayesian Meta-Learning
- Cross-Domain Meta-Learning
- MAML Optimization

## Testing

### Run All Tests

```bash
# Comprehensive system test
python astra_core/comprehensive_system_test.py

# Specialist capability tests
python astra_core/tests/test_specialist_capabilities.py

# Discovery system tests
python astra_core/tests/test_discovery_capabilities.py
```

### Test Results

| Test Suite | Result |
|------------|--------|
| Comprehensive System Test | ✅ 18/18 (100%) |
| Specialist Capabilities | ✅ 6/6 (100%) |
| Domain Integration | ✅ 75/75 (100%) |

## Project Statistics

- **Total Lines**: ~320,000
- **Python Files**: 520+
- **Domain Modules**: 75
- **Specialist Capabilities**: 74+
- **Meta-Cognitive Systems**: 4
- **Discovery Capabilities**: 8

## Documentation

- **User Manual**: `User_Manual/User_Manual.md` - Complete system documentation
- **CLAUDE.md**: Project-specific guidance for AI-assisted development
- **Paper**: `RASTI_AI/draft_paper_complete_v9.md` - Complete scientific paper with test cases

## Citation

If you use ASTRA in your research, please cite:

```bibtex
@software{astra_2024,
  title={ASTRA: Autonomous Scientific Discovery in Astrophysics},
  author={[Author Names]},
  year={2024},
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

**Note**: ASTRA was previously known as "STAN-XI-ASTRO" internally. The codebase has been renamed from `stan_core` to `astra_core` for consistency with the ASTRA project name. Function names like `create_stan_system()` are retained for API backward compatibility.
