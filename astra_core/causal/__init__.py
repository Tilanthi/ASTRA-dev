"""
Causal Reasoning Engine

Implements true causal inference beyond correlation:
- Structural Causal Models (SCM)
- Causal discovery algorithms (PC, GES, FCI, temporal)
- Intervention planning (do-calculus)
- Counterfactual reasoning
- Causal explanation generation

V47+ Enhancements:
- Bayesian structure learning (posterior over DAGs)
- Expected Information Gain calculator (active discovery)
- Online causal learning (streaming updates)
- Simulation-based inference (likelihood-free inference)
"""

from .model.scm import StructuralCausalModel, Variable, StructuralEquation
from .model.intervention import Intervention, InterventionPlanner
from .model.counterfactual import CounterfactualQuery, CounterfactualEngine
from .discovery.pc_algorithm import PCAlgorithm
from .discovery.ges_algorithm import GESAlgorithm
from .discovery.temporal_discovery import TemporalCausalDiscovery
from .discovery.independence import ConditionalIndependenceTest

# V47+ Enhanced causal discovery
try:
    from .discovery.bayesian_structure_learning import (
        InferenceMethod,
        DAGPosteriorSample,
        BayesianStructureLearningResult,
        BayesianStructureLearner,
        create_bayesian_structure_learner,
    )
except ImportError:
    InferenceMethod = None
    DAGPosteriorSample = None
    BayesianStructureLearningResult = None
    BayesianStructureLearner = None
    create_bayesian_structure_learner = None

try:
    from .discovery.eig_calculator import (
        NoiseModel,
        ObservationPlan,
        EIGResult,
        LatentConfounderModel,
        ExpectedInformationGainCalculator,
        create_eig_calculator,
    )
except ImportError:
    NoiseModel = None
    ObservationPlan = None
    EIGResult = None
    LatentConfounderModel = None
    ExpectedInformationGainCalculator = None
    create_eig_calculator = None

try:
    from .discovery.online_causal_learning import (
        UpdateMethod,
        ConceptDriftDetector,
        OnlineLearningResult,
        OnlineCausalLearner,
        create_online_causal_learner,
    )
except ImportError:
    UpdateMethod = None
    ConceptDriftDetector = None
    OnlineLearningResult = None
    OnlineCausalLearner = None
    create_online_causal_learner = None

# V47+ Simulation-based inference
try:
    from .inference import (
        SBIMethod,
        SBIResult,
        SimulatorInterface,
        SimulationBasedInferenceEngine,
        create_sbi_engine,
        default_summary_statistics,
    )
except ImportError:
    SBIMethod = None
    SBIResult = None
    SimulatorInterface = None
    SimulationBasedInferenceEngine = None
    create_sbi_engine = None
    default_summary_statistics = None

__all__ = [
    "StructuralCausalModel",
    "Variable",
    "StructuralEquation",
    "Intervention",
    "InterventionPlanner",
    "CounterfactualQuery",
    "CounterfactualEngine",
    "PCAlgorithm",
    "GESAlgorithm",
    "TemporalCausalDiscovery",
    "ConditionalIndependenceTest",
    # V47+ Enhanced modules
    "InferenceMethod",
    "DAGPosteriorSample",
    "BayesianStructureLearningResult",
    "BayesianStructureLearner",
    "create_bayesian_structure_learner",
    "NoiseModel",
    "ObservationPlan",
    "EIGResult",
    "LatentConfounderModel",
    "ExpectedInformationGainCalculator",
    "create_eig_calculator",
    "UpdateMethod",
    "ConceptDriftDetector",
    "OnlineLearningResult",
    "OnlineCausalLearner",
    "create_online_causal_learner",
    "SBIMethod",
    "SBIResult",
    "SimulatorInterface",
    "SimulationBasedInferenceEngine",
    "create_sbi_engine",
    "default_summary_statistics",
]
