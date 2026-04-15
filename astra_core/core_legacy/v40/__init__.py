# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
STAN V40 Enhanced - AGI-Adjacent Reasoning System

V40 adds advanced reasoning capabilities on top of V39.1:

Phase 1 - Immediate Improvements:
- Real LLM Integration with Adaptive Prompting
- Enhanced External Knowledge Grounding
- Improved Answer Verification

Phase 2 - Core Reasoning Enhancements:
- Multi-Step Decomposition Engine
- Hypothesis Generation & Testing Loop
- Formal Logic Integration (Z3 SMT Solver)

Phase 3 - Advanced Capabilities:
- Neural-Symbolic Theorem Prover
- Causal World Model
- Meta-Cognitive Controller

Phase 4 - AGI-Adjacent:
- Continuous Learning System
- Self-Improvement Loop

Target: 75-85% accuracy on HLE (up from 44% in V39.1)

Date: 2025-12-11
Version: 40.0
"""

from .multi_step_decomposition import (
    MultiStepDecomposer,
    ProblemDecomposition,
    SubProblem,
    DecompositionStrategy,
    CompositionEngine
)

from .hypothesis_engine import (
    HypothesisEngine,
    Hypothesis,
    HypothesisTest,
    EvidenceType,
    HypothesisStatus,
    MentalExperiment
)

from .formal_logic import (
    FormalLogicEngine,
    Z3Solver,
    PrologEngine,
    LogicalProof,
    Constraint,
    ProofStep
)

from .theorem_prover import (
    NeuralTheoremProver,
    ProofSketch,
    ProofVerifier,
    CounterexampleSearch,
    TheoremStatus
)

from .causal_world_model import (
    CausalWorldModel,
    CausalMechanism,
    Intervention,
    Counterfactual,
    CausalQuery
)

from .meta_cognitive import (
    MetaCognitiveController,
    ReasoningStrategy,
    ResourceBudget,
    ConfidenceEstimator,
    StrategySelector
)

from .continuous_learning import (
    ContinuousLearner,
    LearningEvent,
    PatternLibrary,
    FailureAnalyzer,
    CurriculumManager
)

from .enhanced_knowledge import (
    EnhancedKnowledgeRetrieval,
    GoogleScholarAPI,
    StackExchangeAPI,
    KnowledgeFusion,
    SourceRanker
)

from .answer_verification import (
    AnswerVerifier,
    BackwardChainer,
    SymbolicMathVerifier,
    UnitConsistencyChecker,
    ConstraintValidator
)

from .v40_system import (
    V40CompleteSystem,
    V40Config,
    V40Mode,
    V40Stats,
    create_v40_standard,
    create_v40_fast,
    create_v40_deep
)

__all__ = [
    # Multi-Step Decomposition
    'MultiStepDecomposer',
    'ProblemDecomposition',
    'SubProblem',
    'DecompositionStrategy',
    'CompositionEngine',

    # Hypothesis Engine
    'HypothesisEngine',
    'Hypothesis',
    'HypothesisTest',
    'EvidenceType',
    'HypothesisStatus',
    'MentalExperiment',

    # Formal Logic
    'FormalLogicEngine',
    'Z3Solver',
    'PrologEngine',
    'LogicalProof',
    'Constraint',
    'ProofStep',

    # Theorem Prover
    'NeuralTheoremProver',
    'ProofSketch',
    'ProofVerifier',
    'CounterexampleSearch',
    'TheoremStatus',

    # Causal World Model
    'CausalWorldModel',
    'CausalMechanism',
    'Intervention',
    'Counterfactual',
    'CausalQuery',

    # Meta-Cognitive Controller
    'MetaCognitiveController',
    'ReasoningStrategy',
    'ResourceBudget',
    'ConfidenceEstimator',
    'StrategySelector',

    # Continuous Learning
    'ContinuousLearner',
    'LearningEvent',
    'PatternLibrary',
    'FailureAnalyzer',
    'CurriculumManager',

    # Enhanced Knowledge
    'EnhancedKnowledgeRetrieval',
    'GoogleScholarAPI',
    'StackExchangeAPI',
    'KnowledgeFusion',
    'SourceRanker',

    # Answer Verification
    'AnswerVerifier',
    'BackwardChainer',
    'SymbolicMathVerifier',
    'UnitConsistencyChecker',
    'ConstraintValidator',

    # V40 System
    'V40CompleteSystem',
    'V40Config',
    'V40Mode',
    'V40Stats',
    'create_v40_standard',
    'create_v40_fast',
    'create_v40_deep',
]
