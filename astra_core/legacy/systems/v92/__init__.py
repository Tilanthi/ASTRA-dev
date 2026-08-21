"""
V92 Automated Scientific Discovery Engine
=========================================

This module represents the pinnacle of STAN's evolution - an automated
scientific discovery system capable of generating hypotheses, discovering
causal relationships, applying mathematical intuition, and designing experiments.
"""

# v92_system.py has a baselined syntax error (tests/known_broken_syntax.txt);
# quarantined so the remaining v92 modules stay importable.
try:
    from .v92_system import (
        V92CompleteSystem,
        V92Config,
        ScientificDiscovery,
        create_v92_system,
        create_v92_explorer,
        create_v92_validator,
        create_v92_mathematician,
        create_v92_experimentalist
    )
except (ImportError, SyntaxError):
    V92CompleteSystem = None
    V92Config = None
    ScientificDiscovery = None
    create_v92_system = None
    create_v92_explorer = None
    create_v92_validator = None
    create_v92_mathematician = None
    create_v92_experimentalist = None

from .hypothesis_engine import (
    HypothesisGenerator,
    Hypothesis,
    HypothesisType
)

from .mathematical_intuition import (
    MathematicalIntuitionModule,
    MathematicalConjecture,
    Proof,
    MathDomain,
    ProofStatus
)

from .causal_discovery import (
    CausalDiscoveryEngine,
    CausalModel,
    CausalRelation,
    Intervention,
    Counterfactual,
    DiscoveryMethod
)

from .experimental_design import (
    ExperimentalDesignEngine,
    ExperimentalDesign,
    ExperimentalVariable,
    Treatment,
    ExperimentalType,
    SimulationResult
)

__all__ = [
    # Main system
    'V92CompleteSystem',
    'V92Config',
    'ScientificDiscovery',
    'create_v92_system',
    'create_v92_explorer',
    'create_v92_validator',
    'create_v92_mathematician',
    'create_v92_experimentalist',

    # Hypothesis generation
    'HypothesisGenerator',
    'Hypothesis',
    'HypothesisType',

    # Mathematical intuition
    'MathematicalIntuitionModule',
    'MathematicalConjecture',
    'Proof',
    'MathDomain',
    'ProofStatus',

    # Causal discovery
    'CausalDiscoveryEngine',
    'CausalModel',
    'CausalRelation',
    'Intervention',
    'Counterfactual',
    'DiscoveryMethod',

    # Experimental design
    'ExperimentalDesignEngine',
    'ExperimentalDesign',
    'ExperimentalVariable',
    'Treatment',
    'ExperimentalType',
    'SimulationResult'
]