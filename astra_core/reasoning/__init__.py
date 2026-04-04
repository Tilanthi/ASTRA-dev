"""
Advanced Capabilities: AGI-like Inference Enhancements for STAN

This package provides advanced reasoning capabilities that enhance STAN's
AGI-like inference abilities across multiple versions:

V39 Capabilities:
Phase 1 (Quick wins):
1. Abductive Inference Engine - Inference to best explanation
2. Active Experiment Design - Information-theoretic experiment selection
3. Episodic Memory - Experience-based reasoning

Phase 2 (Core capability):
4. Causal Discovery - Learn causal structure from data
5. Meta-Learning Layer - Learn-to-learn across tasks

Phase 3 (Advanced):
6. Abstraction Learning - Discover new symbolic templates (V40: sympy simplification)
7. Neural-Symbolic Bridge - Fuse LLM breadth with symbolic rigor (V40: math parsing)
8. Uncertainty Planning - Plan under belief uncertainty (V40: question-aware decisions)

V40 New Capabilities:
9. Symbolic Math Engine - Algebraic manipulation, equation solving, calculus
10. Proof Validator - Mathematical proof structure validation
11. Quantitative Reasoner - Statistical tests, probability, dimensional analysis
12. Capability Orchestrator - Intelligent routing and cross-module communication
13. Learning Feedback Loop - Learn from failures, adjust parameters
14. LLM Inference - Claude API integration for complex reasoning
15. External Knowledge - Wolfram Alpha, arXiv, Wikipedia, PubMed integration

V41 AGI Enhancements:
16. Unified World Model - Shared belief state across all modules
17. Integration Bus - Event-based cross-module communication
18. Dynamic Replanning - Adaptive execution with real-time plan adjustment
19. Counterfactual Reasoning - "What if" analysis using causal models
20. Analogical Reasoning - Cross-domain knowledge transfer
21. Theory Synthesis - Pattern-to-law promotion and theory building
22. Metacognition - Self-reflective reasoning quality monitoring
23. Active Knowledge Acquisition - Goal-directed knowledge seeking
24. Multi-Agent Deliberation - Internal debate and consensus building
25. Continuous Learning - Experience-based improvement
26. V41 Orchestrator - Unified AGI-like reasoning coordinator

V42 Core Enhancement Modules:
27. Probabilistic Program Synthesis - Automatic forward model generation
28. Hierarchical Bayesian Meta-Learning - Prior transfer across tasks
29. Symbolic Regression with Physics Constraints - Equation discovery
30. Active Inference Framework - Free energy minimization for perception/action
31. Nested Sampling with Dynamic Allocation - Evidence calculation & multimodal posteriors
32. Differentiable Physics Engine - Gradient-based optimization through physics
33. Uncertainty Decomposition - Separate aleatoric/epistemic/model-form uncertainty
34. Anomaly-Driven Discovery Loop - Turn anomalies into scientific discoveries
35. Cross-Survey Knowledge Fusion - Multi-survey data combination
36. Learned Proposal Distributions - Adaptive MCMC proposals
37. Calibrated Confidence Estimation - Proper probability calibration
38. Falsification-First Hypothesis Testing - Popperian scientific method

V43 Astrophysics-Aware Reasoning:
39. Observational Likelihood - Connect forward models to data with beam convolution
40. Physical Process Library - Encyclopedia of ISM mechanisms
41. ISM Knowledge Base - Expert domain knowledge (phases, tracers, dust, B-fields)
42. Astrophysical Causal Discovery - Physics-constrained, bias-aware causality
43. Astrophysical Theory Synthesis - Build theories from patterns
44. Multiwavelength Reconciliation - Integrate X-ray/optical/IR/radio
45. Observational Strategy - Design discriminating tests

V44 ARC-AGI Integration (NEW):
46. ARC-AGI Integration - Grid-based pattern recognition and transformation synthesis
47. Formal Logic Enhanced - Z3 SMT solver and Prolog integration
48. Answer Verification - Backward chaining and symbolic verification
49. Self-Reflection Enhanced - Contradiction detection and calibration
50. Active Information Enhanced - Knowledge gap seeking
51. Swarm Reasoning - Multi-agent collaborative problem-solving

Date: 2025-12-12
Version: 44.0
"""

# V39 Capabilities
from .abductive_inference import (
    AbductiveInferenceEngine,
    Hypothesis,
    Observation,
    Explanation,
    AbductiveResult
)

from .active_experiment import (
    Experiment,
    ExperimentResult,
    InformationGainEstimator
)

# ActiveExperimentDesigner not available, set to None
ActiveExperimentDesigner = None

from .episodic_memory import (
    EpisodicMemory,
    Episode,
    ReasoningTrace,
    PatternExtractor
)

from .causal_discovery import (
    CausalGraph,
    IndependenceTest,
    PartialCorrelationTest
)

# CausalDiscoveryEngine and StructureLearner not available, set to None
CausalDiscoveryEngine = None
StructureLearner = None

from .meta_learning import (
    MetaLearner,
    Strategy,
    TaskSignature,
    StrategyLibrary
)

# V47+ Meta-learning enhancements
try:
    from .maml_optimizer import (
        MAMLOptimizer,
        TaskBatch,
        MetaLearningState,
        AdaptationResult,
        MetaUpdateResult,
        MAMLVariant,
        TaskUncertaintyQuantifier,
        create_maml_optimizer
    )
except ImportError:
    MAMLOptimizer = None
    TaskBatch = None
    MetaLearningState = None
    AdaptationResult = None
    MetaUpdateResult = None
    MAMLVariant = None
    TaskUncertaintyQuantifier = None
    create_maml_optimizer = None

try:
    from .cross_domain_meta_learner import (
        CrossDomainMetaLearner,
        DomainSimilarity,
        DomainFeatures,
        adapt_to_new_domain
    )
except ImportError:
    CrossDomainMetaLearner = None
    DomainSimilarity = None
    DomainFeatures = None
    adapt_to_new_domain = None

from .abstraction_learning import (
    LearnedTemplate,
    SymbolicOperation,
    OperationLibrary,
    SymbolicRegressor
)

# AbstractionLearner, TemplateComposer, AbstractionValidator not available, set to None
AbstractionLearner = None
TemplateComposer = None
AbstractionValidator = None

from .neural_symbolic_bridge import (
    SymbolicStructure,
    NeuralProposal,
    NeuralToSymbolicTranslator,
    MathematicalExpressionTranslator,
    SymbolicToNeuralTranslator
)

# NeuralSymbolicBridge and HybridReasoner not available, set to None
NeuralSymbolicBridge = None
HybridReasoner = None

from .uncertainty_planning import (
    UncertaintyPlanner,
    BeliefState,
    Policy,
    POMDPLite,
    QuestionAnswerPlanner  # V40
)

# V40 New Capabilities
from .symbolic_math_engine import (
    SymbolicMathEngine,
    MathExpression,
    EquationSolution,
    DerivativeResult,
    IntegralResult,
    SimplificationResult,
    VerificationResult,
    MathOperationType,
    ExpressionType
)

# EquationSystem and MathProblemClassifier not available, set to None
EquationSystem = None
MathProblemClassifier = None

from .proof_validator import (
    MathematicalProofValidator,
    ProofStructure,
    ProofStep,
    LogicalStatement,
    ValidationResult,
    ProofParser,
    LogicalValidator,
    CircularityDetector,
    InductionValidator
)

from .quantitative_reasoner import (
    StatisticalTestSelector,
    StatisticalInterpreter,
    DimensionalAnalyzer,
    ProbabilityCalculator,
    StatisticalTestRecommendation,
    DimensionalAnalysisResult,
    ProbabilityResult,
    NumericalEstimate
)

# QuantitativeReasoner and NumericalEstimator not available, set to None
QuantitativeReasoner = None
NumericalEstimator = None

from .capability_orchestrator import (
    CapabilityOrchestrator,
    CapabilityType,
    ProblemCategory,
    ExecutionPlan,
    OrchestrationResult,
    ProblemClassifier,
    ExecutionPlanner,
    ResultCombiner
)

# CausalExperimentBridge not available, set to None
CausalExperimentBridge = None

from .learning_feedback import (
    FailureAnalyzer,
    FailureAnalysis,
    Learning,
    ParameterState,
    FeedbackRecord
)

# LearningFeedbackLoop, LearningExtractor, ParameterManager, LearningPropagator not available, set to None
LearningFeedbackLoop = None
LearningExtractor = None
ParameterManager = None
LearningPropagator = None

# V40: LLM Inference
from .llm_inference import (
    LLMInferenceEngine,
    LLMRequest,
    LLMResponse,
    ModelType,
    ReasoningMode as LLMReasoningMode,  # Renamed to avoid conflict
    PromptTemplate,
    ResponseCache,
    ConversationTurn
)

# HLEOptimizedReasoner not available, set to None
HLEOptimizedReasoner = None

# V40: External Knowledge Sources
from .external_knowledge import (
    KnowledgeSourceType,
    KnowledgeQuery,
    KnowledgeResult,
    WolframResult,
    ArxivPaper,
    PubMedArticle,
    KnowledgeCache,
    WolframAlphaClient
)

# ArxivClient, WikipediaClient, PubMedClient, ExternalKnowledgeAggregator not available, set to None
ArxivClient = None
WikipediaClient = None
PubMedClient = None
ExternalKnowledgeAggregator = None

# V41: Unified World Model
from .unified_world_model import (
    UnifiedWorldModel,
    Belief as WorldBelief,
    Hypothesis as WorldHypothesis,
    CausalGraph as WorldCausalGraph,
    CausalEdge,
    Constraint,
    AbstractionTemplate,
    Evidence,
    EvidenceSource,
    BeliefState as WorldBeliefState
)

# get_world_model not available, set to None
get_world_model = None

# V41: Integration Bus
from .integration_bus import (
    IntegrationBus,
    Event,
    EventType,
    EventPriority,
    Subscription,
    EventHistory
)

# get_integration_bus and StandardHandlers not available, set to None
get_integration_bus = None
StandardHandlers = None

# V41: Dynamic Replanning
try:
    from .dynamic_replanning import (
        DynamicExecutor,
        ReplanningEngine,
        ReplanningDecision,
        ExecutionState,
        CapabilityExecution,
        InformationGainEstimator as ReplanInfoGainEstimator,
        AdaptiveCapabilitySelector
    )
except ImportError:
    DynamicExecutor = None
    ReplanningEngine = None
    ReplanningDecision = None
    ExecutionState = None
    CapabilityExecution = None
    ReplanInfoGainEstimator = None
    AdaptiveCapabilitySelector = None

# V41: Counterfactual Reasoning
try:
    from .counterfactual_reasoning import (
        CounterfactualEngine,
        StructuralCausalModel,
        CounterfactualQuery,
        CounterfactualResult,
        ContrastiveExplanation,
        CausalEffect,
        Intervention,
        InterventionType
    )
except ImportError:
    CounterfactualEngine = None
    StructuralCausalModel = None
    CounterfactualQuery = None
    CounterfactualResult = None
    ContrastiveExplanation = None
    CausalEffect = None
    Intervention = None
    InterventionType = None

# V41: Analogical Reasoning
try:
    from .analogical_reasoning import (
        AnalogyFinder,
        StructureMapper,
        SemanticTemplateComposer,
        Analogy,
        AnalogyType,
        StructuralMapping,
        DomainRepresentation,
        StructuralElement,
        SolutionTransfer
    )
except ImportError:
    AnalogyFinder = None
    StructureMapper = None
    SemanticTemplateComposer = None
    Analogy = None
    AnalogyType = None
    StructuralMapping = None
    DomainRepresentation = None
    StructuralElement = None
    SolutionTransfer = None

# V41: Theory Synthesis
from .theory_synthesis import (
    TheorySynthesizer,
    get_theory_synthesizer,
    Pattern,
    PatternType,
    Law,
    LawStatus,
    Theory,
    TheoryStatus,
    ConsistencyLevel,
    ConsistencyReport,
    Prediction,
    PatternToLawPromoter,
    LawToTheoryComposer,
    ConsistencyChecker,
    TheoryUnifier,
    PredictionGenerator
)

# V41: Metacognition
from .metacognition import (
    MetacognitiveController,
    get_metacognitive_controller,
    ReasoningQuality,
    UncertaintyType,
    BiasType,
    ReasoningStrategy,
    ReasoningTrace as MetaReasoningTrace,
    UncertaintyProfile,
    BiasReport,
    StrategyRecommendation,
    MetacognitiveInsight,
    ReasoningQualityAssessor,
    UncertaintyMonitor,
    BiasDetector,
    StrategySelector
)

# V41: Active Knowledge Acquisition
from .active_knowledge_acquisition import (
    ActiveKnowledgeAcquirer,
    get_knowledge_acquirer,
    KnowledgeType,
    SourceType,
    AcquisitionPriority,
    KnowledgeGap,
    Query,
    AcquiredKnowledge,
    LearningCurriculum,
    KnowledgeGapIdentifier,
    QueryOptimizer,
    SourceSelector,
    InformationValueEstimator,
    CurriculumBuilder
)

# V41: Multi-Agent Deliberation
from .multi_agent_deliberation import (
    MultiAgentDeliberator,
    get_deliberator,
    AgentRole,
    ArgumentType,
    DeliberationPhase,
    ConsensusLevel as DeliberationConsensusLevel,
    DeliberationAgent,
    Argument,
    Position,
    Consensus,
    DeliberationSession,
    AgentFactory,
    ArgumentEvaluator,
    ConsensusBuilder,
    DeliberationFacilitator
)

# V41: Continuous Learning
try:
    from .continuous_learning import (
        ContinuousLearner,
        get_continuous_learner,
        ExperienceType,
        LearningSignal,
        ConsolidationStrategy,
        Experience,
        LearnedPattern,
        LearnedSkill,
        KnowledgeItem,
        ExperienceStore,
        PatternExtractor as LearningPatternExtractor,
        KnowledgeConsolidator,
        SkillTransferEngine
    )
except ImportError:
    ContinuousLearner = None
    get_continuous_learner = None
    ExperienceType = None
    LearningSignal = None
    ConsolidationStrategy = None
    Experience = None
    LearnedPattern = None
    LearnedSkill = None
    KnowledgeItem = None
    ExperienceStore = None
    LearningPatternExtractor = None
    KnowledgeConsolidator = None
    SkillTransferEngine = None

# V41: Orchestrator (Main Entry Point)
try:
    from .v41_orchestrator import (
        V41Orchestrator,
        get_orchestrator,
        reason,
        ReasoningMode,
        TaskComplexity,
        ReasoningTask,
        ReasoningResult,
        CapabilityRouter
    )
except ImportError:
    V41Orchestrator = None
    get_orchestrator = None
    reason = None
    ReasoningMode = None
    TaskComplexity = None
    ReasoningTask = None
    ReasoningResult = None
    CapabilityRouter = None

__all__ = [
    # Abductive Inference
    'AbductiveInferenceEngine',
    'Hypothesis',
    'Observation',
    'Explanation',
    'AbductiveResult',

    # Active Experiment
    'ActiveExperimentDesigner',
    'Experiment',
    'ExperimentResult',
    'InformationGainEstimator',

    # Episodic Memory
    'EpisodicMemory',
    'Episode',
    'ReasoningTrace',
    'PatternExtractor',

    # Causal Discovery
    'CausalDiscoveryEngine',
    'CausalGraph',
    'IndependenceTest',
    'StructureLearner',

    # Meta-Learning
    'MetaLearner',
    'Strategy',
    'TaskSignature',
    'StrategyLibrary',

    # Abstraction Learning
    'AbstractionLearner',
    'LearnedTemplate',
    'TemplateComposer',
    'AbstractionValidator',

    # Neural-Symbolic Bridge
    'NeuralSymbolicBridge',
    'SymbolicStructure',
    'NeuralProposal',
    'HybridReasoner',
    'MathematicalExpressionTranslator',

    # Uncertainty Planning
    'UncertaintyPlanner',
    'BeliefState',
    'Policy',
    'POMDPLite',
    'QuestionAnswerPlanner',

    # V40: Symbolic Math Engine
    'SymbolicMathEngine',
    'MathExpression',
    'EquationSolution',
    'DerivativeResult',
    'IntegralResult',
    'SimplificationResult',
    'VerificationResult',
    'EquationSystem',
    'MathProblemClassifier',

    # V40: Proof Validator
    'MathematicalProofValidator',
    'ProofStructure',
    'ProofStep',
    'LogicalStatement',
    'ValidationResult',
    'ProofParser',
    'LogicalValidator',
    'CircularityDetector',
    'InductionValidator',

    # V40: Quantitative Reasoner
    'QuantitativeReasoner',
    'StatisticalTestSelector',
    'StatisticalInterpreter',
    'DimensionalAnalyzer',
    'ProbabilityCalculator',
    'NumericalEstimator',
    'StatisticalTestRecommendation',
    'DimensionalAnalysisResult',
    'ProbabilityResult',

    # V40: Capability Orchestrator
    'CapabilityOrchestrator',
    'CapabilityType',
    'ProblemCategory',
    'ExecutionPlan',
    'OrchestrationResult',
    'ProblemClassifier',
    'ExecutionPlanner',
    'ResultCombiner',
    'CausalExperimentBridge',

    # V40: Learning Feedback Loop
    'LearningFeedbackLoop',
    'FailureAnalyzer',
    'LearningExtractor',
    'ParameterManager',
    'LearningPropagator',
    'FailureAnalysis',
    'Learning',
    'FeedbackRecord',

    # V40: LLM Inference
    'LLMInferenceEngine',
    'LLMRequest',
    'LLMResponse',
    'ModelType',
    'LLMReasoningMode',
    'PromptTemplate',
    'ResponseCache',
    'ConversationTurn',
    'HLEOptimizedReasoner',

    # V40: External Knowledge Sources
    'KnowledgeSourceType',
    'KnowledgeQuery',
    'KnowledgeResult',
    'WolframResult',
    'ArxivPaper',
    'PubMedArticle',
    'KnowledgeCache',
    'WolframAlphaClient',
    'ArxivClient',
    'WikipediaClient',
    'PubMedClient',
    'ExternalKnowledgeAggregator',

    # V41: Unified World Model
    'UnifiedWorldModel',
    'WorldBelief',
    'WorldHypothesis',
    'WorldCausalGraph',
    'CausalEdge',
    'Constraint',
    'AbstractionTemplate',
    'Evidence',
    'EvidenceSource',
    'WorldBeliefState',

    # V41: Integration Bus
    'IntegrationBus',
    'Event',
    'EventType',
    'EventPriority',
    'Subscription',
    'EventHistory',

    # V41: Dynamic Replanning
    'DynamicExecutor',
    'ReplanningEngine',
    'ReplanningDecision',
    'ExecutionState',
    'CapabilityExecution',
    'ReplanInfoGainEstimator',
    'AdaptiveCapabilitySelector',

    # V41: Counterfactual Reasoning
    'CounterfactualEngine',
    'StructuralCausalModel',
    'CounterfactualQuery',
    'CounterfactualResult',
    'ContrastiveExplanation',
    'CausalEffect',
    'Intervention',
    'InterventionType',

    # V41: Analogical Reasoning
    'AnalogyFinder',
    'StructureMapper',
    'SemanticTemplateComposer',
    'Analogy',
    'AnalogyType',
    'StructuralMapping',
    'DomainRepresentation',
    'StructuralElement',
    'SolutionTransfer',

    # V41: Theory Synthesis
    'TheorySynthesizer',
    'get_theory_synthesizer',
    'Pattern',
    'PatternType',
    'Law',
    'LawStatus',
    'Theory',
    'TheoryStatus',
    'ConsistencyLevel',
    'ConsistencyReport',
    'Prediction',
    'PatternToLawPromoter',
    'LawToTheoryComposer',
    'ConsistencyChecker',
    'TheoryUnifier',
    'PredictionGenerator',

    # V41: Metacognition
    'MetacognitiveController',
    'get_metacognitive_controller',
    'ReasoningQuality',
    'UncertaintyType',
    'BiasType',
    'ReasoningStrategy',
    'MetaReasoningTrace',
    'UncertaintyProfile',
    'BiasReport',
    'StrategyRecommendation',
    'MetacognitiveInsight',
    'ReasoningQualityAssessor',
    'UncertaintyMonitor',
    'BiasDetector',
    'StrategySelector',

    # V41: Active Knowledge Acquisition
    'ActiveKnowledgeAcquirer',
    'get_knowledge_acquirer',
    'KnowledgeType',
    'SourceType',
    'AcquisitionPriority',
    'KnowledgeGap',
    'Query',
    'AcquiredKnowledge',
    'LearningCurriculum',
    'KnowledgeGapIdentifier',
    'QueryOptimizer',
    'SourceSelector',
    'InformationValueEstimator',
    'CurriculumBuilder',

    # V41: Multi-Agent Deliberation
    'MultiAgentDeliberator',
    'get_deliberator',
    'AgentRole',
    'ArgumentType',
    'DeliberationPhase',
    'DeliberationConsensusLevel',
    'DeliberationAgent',
    'Argument',
    'Position',
    'Consensus',
    'DeliberationSession',
    'AgentFactory',
    'ArgumentEvaluator',
    'ConsensusBuilder',
    'DeliberationFacilitator',

    # V41: Continuous Learning
    'ContinuousLearner',
    'get_continuous_learner',
    'ExperienceType',
    'LearningSignal',
    'ConsolidationStrategy',
    'Experience',
    'LearnedPattern',
    'LearnedSkill',
    'KnowledgeItem',
    'ExperienceStore',
    'LearningPatternExtractor',
    'KnowledgeConsolidator',
    'SkillTransferEngine',

    # V41: Orchestrator (Main Entry Point)
    'V41Orchestrator',
    'get_orchestrator',
    'reason',
    'ReasoningMode',
    'TaskComplexity',
    'ReasoningTask',
    'ReasoningResult',
    'CapabilityRouter',

    # V42: Probabilistic Program Synthesis
    'ProbabilisticProgramSynthesizer',
    'get_program_synthesizer',
    'SynthesisResult',
    'ProbabilisticProgram',
    'ProgramGenerator',
    'ProgramEvaluator',
    'PhysicsLibrary',

    # V42: Hierarchical Bayesian Meta-Learning
    'HierarchicalBayesianMetaLearner',
    'get_metalearner',
    'TransferResult',
    'LearnedPrior',
    'PriorType',
    'TaskSimilarityComputer',

    # V42: Symbolic Regression
    'SymbolicRegressionEngine',
    'get_symbolic_regression_engine',
    'DiscoveredEquation',
    'GeneticProgramming',
    'DimensionalAnalyzer',
    'PhysicsConstraint',
    'Dimension',

    # V42: Active Inference
    'ActiveInferenceAgent',
    'get_active_inference_agent',
    'FreeEnergyMinimizer',
    'PredictiveCoder',
    'ActionSelector',
    'ActiveInferenceBelief',
    'ActiveInferenceAction',

    # V42: Nested Sampling
    'NestedSampler',
    'create_nested_sampler',
    'NestedSamplingResult',
    'DynamicLivePointAllocator',
    'MultiModalDetector',
    'EvidenceCalculator',

    # V42: Differentiable Physics
    'DifferentiablePhysicsEngine',
    'get_differentiable_physics_engine',
    'DualNumber',
    'GradientResult',
    'HessianResult',
    'SensitivityAnalysis',
    'GradientOptimizer',
    'FisherInformationEstimator',

    # V42: Uncertainty Decomposition
    'UncertaintyDecomposer',
    'get_uncertainty_decomposer',
    'DecomposedUncertainty',
    'UncertaintyComponent',
    'UncertaintyTypeV42',
    'AleatoricEstimator',
    'EpistemicEstimator',

    # V42: Anomaly Discovery
    'AnomalyDrivenDiscoveryLoop',
    'get_discovery_loop',
    'AnomalyDetector',
    'AnomalyCharacterizer',
    'HypothesisGenerator',
    'DiscoveryIntegrator',
    'AnomalyV42',
    'ValidatedDiscovery',

    # V42: Cross-Survey Fusion
    'CrossSurveyFusionEngine',
    'get_cross_survey_fusion_engine',
    'CrossMatcher',
    'MeasurementCombiner',
    'JointPosteriorCalculator',
    'FusedSource',
    'JointPosterior',

    # V42: Learned Proposals
    'AdaptiveProposalManager',
    'create_adaptive_proposal_manager',
    'ProposalMemoryBank',
    'GaussianProposal',
    'MixtureProposal',
    'DifferentialEvolutionProposal',

    # V42: Calibrated Confidence
    'CalibratedConfidenceEstimator',
    'get_calibrated_confidence_estimator',
    'PlattScalingCalibrator',
    'IsotonicCalibrator',
    'CoverageCalibrator',
    'CalibrationResult',
    'CoverageAnalysis',

    # V42: Falsification Testing
    'FalsificationEngine',
    'get_falsification_engine',
    'TestDesignGenerator',
    'SeverityCalculator',
    'FalsificationReport',
    'TestSeverity',
    'TestOutcome',
    'HypothesisV42',

    # V43: Astrophysics-Aware Reasoning
    'BeamConvolver',
    'SpectralLikelihood',
    'ImageLikelihood',
    'CubeLikelihood',
    'MultiWavelengthLikelihood',
    'CalibrationUncertaintyPropagator',
    'get_spectral_likelihood',
    'get_image_likelihood',
    'ProcessCategory',
    'PhysicalProcess',
    'ProcessLibrary',
    'MechanismMatcher',
    'ProcessChainBuilder',
    'get_process_library',
    'find_process',
    'explain_observable',
    'ISMPhase',
    'ISMPhaseProperties',
    'MolecularTracer',
    'DustProperties',
    'MagneticFieldMethod',
    'SFRelation',
    'ISMKnowledgeBase',
    'get_ism_knowledge_base',
    'what_traces',
    'get_critical_density',
    'ConservationLaw',
    'ObservationalBias',
    'AstroCausalGraph',
    'BiasAwareCausalDiscovery',
    'PhysicsConstrainedGraph',
    'MechanismIdentifier',
    'LatentPhysicsProposer',
    'DynamicalCausalModel',
    'AstrophysicalCausalDiscovery',
    'discover_causal_structure',
    'identify_mechanism_for_correlation',
    'AstroPatternType',
    'ConfidenceLevel',
    'ObservedPattern',
    'AstroPhysicalLaw',
    'Mechanism',
    'AstroPrediction',
    'MechanismTheory',
    'PatternIdentifier',
    'LawPromoter',
    'TheoryComparator',
    'AstroPredictionGenerator',
    'TheoryBuilder',
    'get_turbulent_sf_theory',
    'get_magnetic_sf_theory',
    'identify_pattern',
    'build_theory_from_patterns',
    'compare_sf_theories',
    'WavelengthDomain',
    'EmissionMechanism',
    'MultiWavObservation',
    'PhysicalComponent',
    'DomainBelief',
    'Tension',
    'UnifiedModel',
    'MultiWavelengthBelief',
    'DomainReconciler',
    'TensionDetector',
    'SEDIntegrator',
    'PhysicalStateInferrer',
    'reconcile_observations',
    'detect_wavelength_tensions',
    'build_sed_from_observations',
    'TelescopeType',
    'ObservationType',
    'Telescope',
    'Instrument',
    'ObservationPlan',
    'StrategyHypothesis',
    'CriticalTest',
    'ObservationDesigner',
    'DiscriminatingTestFinder',
    'SensitivityCalculator',
    'FollowupPrioritizer',
    'design_observation_for_hypothesis',
    'find_critical_test',
    'calculate_detection_limit',
    'prioritize_followup',
    'get_telescope_database',

    # V44: ARC-AGI Integration
    'ARCTaskType',
    'SolutionStrategy',
    'ARCTask',
    'ARCSolution',
    'PatternDiscovery',
    'ARCAGIReasoner',
    'get_arc_reasoner',
    'reset_arc_reasoner',
    'solve_arc_task',
    'analyze_arc_patterns',
    'load_arc_task_from_json',
    'ARC_AVAILABLE',

    # V42 GPQA: Test-Time Search
    'TestTimeSearch',
    'SearchConfig',
    'SearchResult',
    'ReasoningPath',
    'create_gpqa_search',
    'create_fast_search',
    'create_thorough_search',

    # V42 GPQA: Adaptive Compute
    'AdaptiveComputeManager',
    'ComputeBudget',
    'DifficultyLevel',
    'DifficultyEstimator',
    'DifficultySignals',
    'EarlyStoppingMonitor',
    'create_adaptive_manager',

    # V42 GPQA: Enhanced Self-Consistency
    'EnhancedSelfConsistencyGPQA',
    'ConsistencyResultGPQA',
    'ReasoningChain',
    'DiverseChainGenerator',
    'ChainQualityScorer',
    'GPQAReasoningStrategy',

    # V42 GPQA: Step-wise Retrieval
    'StepWiseRetrieval',
    'RetrievalResultGPQA',
    'ScientificKnowledgeBase',
    'KnowledgeGapGPQA',
    'KnowledgeGapType',
    'ReasoningState',
    'RetrievedFact',
    'GapIdentifier',

    # V42 GPQA: Contrastive Explanation
    'ContrastiveExplainer',
    'ContrastiveAnalysis',
    'ChoiceExplanation',
    'ExplanationType',
    'ContradictionDetector',
    'ExplanationGenerator',
    'analyze_choices',
    'explain_wrong_answers',

    # V42 GPQA: Domain Strategies
    'GPQAStrategyEngine',
    'GPQAStrategyResult',
    'GPQADomain',
    'GPQADomainStrategy',
    'GPQA_PHYSICS_STRATEGY',
    'GPQA_CHEMISTRY_STRATEGY',
    'GPQA_BIOLOGY_STRATEGY',
    'apply_gpqa_strategy',
    'get_domain_checklist',

    # V42 GPQA: Enhanced Math Engine
    'EnhancedMathEngine',
    'MathResult',
    'GPQADimensionalAnalyzer',
    'SymbolicSolver',
    'NumericalEvaluator',
    'Unit',
    'Quantity',
    'GPQA_CONSTANTS',
    'GPQA_UNITS',
    'gpqa_solve_problem',
    'gpqa_verify_answer',
    'gpqa_check_dimensions',

    # V50: World Simulator
    'PhysicsEngine',
    'ChemistryReactor',
    'BiologicalPathwaySimulator',
    'WorldCounterfactualEngine',
    'WorldModelInterface',
    'create_world_simulator',
    'create_physics_engine',
    'create_chemistry_reactor',
    'create_biology_simulator',

    # V50: Program Synthesis
    'ReasoningPrimitiveLibrary',
    'ProgramSynthesizer',
    'ExecutionEngine',
    'ProgramLearner',
    'PrimitiveType',
    'ReasoningPrimitive',
    'ReasoningProgram',
    'SynthesisResult',
    'create_program_synthesizer',
    'create_program_synthesis_reasoner',

    # V50: Causal Engine
    'CausalStructureLearner',
    'MechanismDiscovery',
    'InterventionPlanner',
    'CausalCounterfactualReasoner',
    'CausalInferenceEngine',
    'CausalNode',
    'V50CausalEdge',
    'V50CausalGraph',
    'V50Intervention',
    'create_causal_engine',

    # V50: Meta-Learner
    'V50FailureAnalyzer',
    'StrategyAbstractor',
    'CurriculumGenerator',
    'CompetenceTracker',
    'MetaLearningSystem',
    'FailureType',
    'V50FailureAnalysis',
    'V50Strategy',
    'create_meta_learner',

    # V50: Adversarial Debate
    'ProposerAgent',
    'CriticAgent',
    'RedTeamAgent',
    'VerifierAgent',
    'ArbitratorAgent',
    'DebateArena',
    'AdversarialDebateReasoner',
    'DebateArgument',
    'DebateClaim',
    'DebateResult',
    'create_debate_reasoner',

    # V50: Abstraction Learning
    'ConceptHierarchy',
    'AbstractionEngine',
    'V50AnalogyFinder',
    'KnowledgeTransferEngine',
    'HierarchicalAbstractionLearner',
    'AbstractionLevel',
    'Concept',
    'V50Analogy',
    'create_abstraction_learner',

    # Backward Compatibility Aliases
    'LLMInference',
    'ProofValidator',
    'TheorySynthesis',
]

# V42: Probabilistic Program Synthesis
try:
    from .probabilistic_program_synthesis import (
        ProbabilisticProgramSynthesizer,
        get_program_synthesizer,
        SynthesisResult,
        ProbabilisticProgram,
        ProgramGenerator,
        ProgramEvaluator,
        PhysicsLibrary,
    )
except ImportError:
    ProbabilisticProgramSynthesizer = None
    get_program_synthesizer = None
    SynthesisResult = None
    ProbabilisticProgram = None
    ProgramGenerator = None
    ProgramEvaluator = None
    PhysicsLibrary = None

# V42: Hierarchical Bayesian Meta-Learning
try:
    from .hierarchical_bayesian_metalearning import (
        HierarchicalBayesianMetaLearner,
        get_metalearner,
        TransferResult,
        LearnedPrior,
        PriorType,
        TaskSimilarityComputer,
        TaskSignature as MetaTaskSignature,
    )
except ImportError:
    HierarchicalBayesianMetaLearner = None
    get_metalearner = None
    TransferResult = None
    LearnedPrior = None
    PriorType = None
    TaskSimilarityComputer = None
    MetaTaskSignature = None

# V42: Symbolic Regression with Physics Constraints
try:
    from .symbolic_regression import (
        SymbolicRegressionEngine,
        get_symbolic_regression_engine,
        DiscoveredEquation,
        GeneticProgramming,
        DimensionalAnalyzer,
        PhysicsConstraint,
        Dimension,
    )
except ImportError:
    SymbolicRegressionEngine = None
    get_symbolic_regression_engine = None
    DiscoveredEquation = None
    GeneticProgramming = None
    DimensionalAnalyzer = None
    PhysicsConstraint = None
    Dimension = None

# V42: Active Inference Framework
try:
    from .active_inference import (
        ActiveInferenceAgent,
        get_active_inference_agent,
        FreeEnergyMinimizer,
        PredictiveCoder,
        ActionSelector,
        Belief as ActiveInferenceBelief,
        Action as ActiveInferenceAction,
    )
except ImportError:
    ActiveInferenceAgent = None
    get_active_inference_agent = None
    FreeEnergyMinimizer = None
    PredictiveCoder = None
    ActionSelector = None
    ActiveInferenceBelief = None
    ActiveInferenceAction = None

# V42: Nested Sampling with Dynamic Allocation
try:
    from .nested_sampling import (
        NestedSampler,
        create_nested_sampler,
        NestedSamplingResult,
        DynamicLivePointAllocator,
        MultiModalDetector,
        EvidenceCalculator,
    )
except ImportError:
    NestedSampler = None
    create_nested_sampler = None
    NestedSamplingResult = None
    DynamicLivePointAllocator = None
    MultiModalDetector = None
    EvidenceCalculator = None

# V42: Differentiable Physics Engine
try:
    from .differentiable_physics import (
        DifferentiablePhysicsEngine,
        get_differentiable_physics_engine,
        DualNumber,
        GradientResult,
        HessianResult,
        SensitivityAnalysis,
        GradientOptimizer,
        FisherInformationEstimator,
    )
except ImportError:
    DifferentiablePhysicsEngine = None
    get_differentiable_physics_engine = None
    DualNumber = None
    GradientResult = None
    HessianResult = None
    SensitivityAnalysis = None
    GradientOptimizer = None
    FisherInformationEstimator = None

# V42: Uncertainty Decomposition
try:
    from .uncertainty_decomposition import (
        UncertaintyDecomposer,
        get_uncertainty_decomposer,
        DecomposedUncertainty,
        UncertaintyComponent,
        UncertaintyType as UncertaintyTypeV42,
        AleatoricEstimator,
        EpistemicEstimator,
    )
except ImportError:
    UncertaintyDecomposer = None
    get_uncertainty_decomposer = None
    DecomposedUncertainty = None
    UncertaintyComponent = None
    UncertaintyTypeV42 = None
    AleatoricEstimator = None
    EpistemicEstimator = None

# V42: Anomaly-Driven Discovery Loop
try:
    from .anomaly_discovery import (
        AnomalyDrivenDiscoveryLoop,
        get_discovery_loop,
        AnomalyDetector,
        AnomalyCharacterizer,
        HypothesisGenerator,
        DiscoveryIntegrator,
        Anomaly as AnomalyV42,
        ValidatedDiscovery,
    )
except ImportError:
    AnomalyDrivenDiscoveryLoop = None
    get_discovery_loop = None
    AnomalyDetector = None
    AnomalyCharacterizer = None
    HypothesisGenerator = None
    DiscoveryIntegrator = None
    AnomalyV42 = None
    ValidatedDiscovery = None

# V42: Cross-Survey Knowledge Fusion
try:
    from .cross_survey_fusion import (
        CrossSurveyFusionEngine,
        get_cross_survey_fusion_engine,
        CrossMatcher,
        MeasurementCombiner,
        JointPosteriorCalculator,
        FusedSource,
        JointPosterior,
    )
except ImportError:
    CrossSurveyFusionEngine = None
    get_cross_survey_fusion_engine = None
    CrossMatcher = None
    MeasurementCombiner = None
    JointPosteriorCalculator = None
    FusedSource = None
    JointPosterior = None

# V42: Learned Proposal Distributions
try:
    from .learned_proposals import (
        AdaptiveProposalManager,
        create_adaptive_proposal_manager,
        ProposalMemoryBank,
        GaussianProposal,
        MixtureProposal,
        DifferentialEvolutionProposal,
    )
except ImportError:
    AdaptiveProposalManager = None
    create_adaptive_proposal_manager = None
    ProposalMemoryBank = None
    GaussianProposal = None
    MixtureProposal = None
    DifferentialEvolutionProposal = None

# V42: Calibrated Confidence Estimation
try:
    from .calibrated_confidence import (
        CalibratedConfidenceEstimator,
        get_calibrated_confidence_estimator,
        PlattScalingCalibrator,
        IsotonicCalibrator,
        CoverageCalibrator,
        CalibrationResult,
        CoverageAnalysis,
    )
except ImportError:
    CalibratedConfidenceEstimator = None
    get_calibrated_confidence_estimator = None
    PlattScalingCalibrator = None
    IsotonicCalibrator = None
    CoverageCalibrator = None
    CalibrationResult = None
    CoverageAnalysis = None

# V42: Falsification-First Hypothesis Testing
try:
    from .falsification_testing import (
        FalsificationEngine,
        get_falsification_engine,
        TestDesignGenerator,
        SeverityCalculator,
        FalsificationReport,
        TestSeverity,
        TestOutcome,
        Hypothesis as HypothesisV42,
    )
except ImportError:
    FalsificationEngine = None
    get_falsification_engine = None
    TestDesignGenerator = None
    SeverityCalculator = None
    FalsificationReport = None
    TestSeverity = None
    TestOutcome = None
    HypothesisV42 = None

# V43: Astrophysics-Aware Reasoning
try:
    from .observational_likelihood import (
        BeamConvolver,
        SpectralLikelihood,
        ImageLikelihood,
        CubeLikelihood,
        MultiWavelengthLikelihood,
        CalibrationUncertaintyPropagator,
        get_spectral_likelihood,
        get_image_likelihood,
    )
except ImportError:
    BeamConvolver = None
    SpectralLikelihood = None
    ImageLikelihood = None
    CubeLikelihood = None
    MultiWavelengthLikelihood = None
    CalibrationUncertaintyPropagator = None
    get_spectral_likelihood = None
    get_image_likelihood = None

try:
    from .physical_process_library import (
        ProcessCategory,
        PhysicalProcess,
        ProcessLibrary,
        MechanismMatcher,
        ProcessChainBuilder,
        get_process_library,
        find_process,
        explain_observable,
    )
except ImportError:
    ProcessCategory = None
    PhysicalProcess = None
    ProcessLibrary = None
    MechanismMatcher = None
    ProcessChainBuilder = None
    get_process_library = None
    find_process = None
    explain_observable = None

try:
    from .ism_knowledge_base import (
        ISMPhase,
        ISMPhaseProperties,
        MolecularTracer,
        DustProperties,
        MagneticFieldMethod,
        SFRelation,
        ISMKnowledgeBase,
        get_ism_knowledge_base,
        what_traces,
        get_critical_density,
    )
except ImportError:
    ISMPhase = None
    ISMPhaseProperties = None
    MolecularTracer = None
    DustProperties = None
    MagneticFieldMethod = None
    SFRelation = None
    ISMKnowledgeBase = None
    get_ism_knowledge_base = None
    what_traces = None
    get_critical_density = None

try:
    from .astrophysical_causal_discovery import (
        ConservationLaw,
        ObservationalBias,
        CausalEdge,
        LatentVariable,
        CausalGraph as AstroCausalGraph,
        BiasAwareCausalDiscovery,
        PhysicsConstrainedGraph,
        MechanismIdentifier,
        LatentPhysicsProposer,
        DynamicalCausalModel,
        AstrophysicalCausalDiscovery,
        discover_causal_structure,
        identify_mechanism_for_correlation,
    )
except ImportError:
    ConservationLaw = None
    ObservationalBias = None
    AstroCausalGraph = None
    BiasAwareCausalDiscovery = None
    PhysicsConstrainedGraph = None
    MechanismIdentifier = None
    LatentPhysicsProposer = None
    DynamicalCausalModel = None
    AstrophysicalCausalDiscovery = None
    discover_causal_structure = None
    identify_mechanism_for_correlation = None
    LatentVariable = None

try:
    from .astrophysical_theory_synthesis import (
        AstroPatternType,
        ConfidenceLevel,
        ObservedPattern,
        PhysicalLaw as AstroPhysicalLaw,
        Mechanism,
        Prediction as AstroPrediction,
        MechanismTheory,
        PatternIdentifier,
        LawPromoter,
        TheoryComparator,
        PredictionGenerator as AstroPredictionGenerator,
        TheoryBuilder,
        get_turbulent_sf_theory,
        get_magnetic_sf_theory,
        identify_pattern,
        build_theory_from_patterns,
        compare_sf_theories,
    )
except ImportError:
    AstroPatternType = None
    ConfidenceLevel = None
    ObservedPattern = None
    AstroPhysicalLaw = None
    Mechanism = None
    AstroPrediction = None
    MechanismTheory = None
    PatternIdentifier = None
    LawPromoter = None
    TheoryComparator = None
    AstroPredictionGenerator = None
    TheoryBuilder = None
    get_turbulent_sf_theory = None
    get_magnetic_sf_theory = None
    identify_pattern = None
    build_theory_from_patterns = None
    compare_sf_theories = None

from .multiwavelength_reconciliation import (
    WavelengthDomain,
    EmissionMechanism,
    Observation as MultiWavObservation,
    PhysicalComponent,
    DomainBelief,
    Tension,
    UnifiedModel,
    MultiWavelengthBelief,
    DomainReconciler,
    TensionDetector,
    SEDIntegrator,
    PhysicalStateInferrer,
    reconcile_observations,
    detect_wavelength_tensions,
    build_sed_from_observations,
)

from .observational_strategy import (
    TelescopeType,
    ObservationType,
    Telescope,
    Instrument,
    ObservationPlan,
    Hypothesis as StrategyHypothesis,
    CriticalTest,
    ObservationDesigner,
    DiscriminatingTestFinder,
    SensitivityCalculator,
    FollowupPrioritizer,
    design_observation_for_hypothesis,
    find_critical_test,
    calculate_detection_limit,
    prioritize_followup,
    get_telescope_database,
)

# V44: ARC-AGI Integration
try:
    from .arc_agi_integration import (
        ARCTaskType,
        SolutionStrategy,
        ARCTask,
        ARCSolution,
        PatternDiscovery,
        ARCAGIReasoner,
        get_arc_reasoner,
        reset_arc_reasoner,
        solve_arc_task,
        analyze_arc_patterns,
        load_arc_task_from_json,
        ARC_AVAILABLE,
    )
except ImportError:
    ARCTaskType = None
    SolutionStrategy = None
    ARCTask = None
    ARCSolution = None
    PatternDiscovery = None
    ARCAGIReasoner = None
    get_arc_reasoner = None
    reset_arc_reasoner = None
    solve_arc_task = None
    analyze_arc_patterns = None
    load_arc_task_from_json = None
    ARC_AVAILABLE = None

# V42 GPQA: Test-Time Search
try:
    from .test_time_search import (
        TestTimeSearch,
        SearchConfig,
        SearchResult,
        ReasoningPath,
        create_gpqa_search,
        create_fast_search,
        create_thorough_search
    )
except ImportError:
    TestTimeSearch = None
    SearchConfig = None
    SearchResult = None
    ReasoningPath = None
    create_gpqa_search = None
    create_fast_search = None
    create_thorough_search = None

# V42 GPQA: Adaptive Compute
try:
    from .adaptive_compute import (
        AdaptiveComputeManager,
        ComputeBudget,
        DifficultyLevel,
        DifficultyEstimator,
        DifficultySignals,
        EarlyStoppingMonitor,
        create_adaptive_manager
    )
except ImportError:
    AdaptiveComputeManager = None
    ComputeBudget = None
    DifficultyLevel = None
    DifficultyEstimator = None
    DifficultySignals = None
    EarlyStoppingMonitor = None

# V42 GPQA: Enhanced Self-Consistency
try:
    from .enhanced_self_consistency import (
        EnhancedSelfConsistency as EnhancedSelfConsistencyGPQA,
        ConsistencyResult as ConsistencyResultGPQA,
        ReasoningChain,
        DiverseChainGenerator,
        ChainQualityScorer,
        ReasoningStrategy as GPQAReasoningStrategy
    )
except ImportError:
    EnhancedSelfConsistencyGPQA = None
    ConsistencyResultGPQA = None
    ReasoningChain = None
    DiverseChainGenerator = None
    ChainQualityScorer = None
    GPQAReasoningStrategy = None

# V42 GPQA: Step-wise Retrieval (RAISE)
try:
    from .stepwise_retrieval import (
        StepWiseRetrieval,
        RetrievalResult as RetrievalResultGPQA,
        ScientificKnowledgeBase,
        KnowledgeGap as KnowledgeGapGPQA,
        KnowledgeGapType,
        ReasoningState,
        RetrievedFact,
        GapIdentifier
    )
except ImportError:
    StepWiseRetrieval = None
    RetrievalResultGPQA = None
    ScientificKnowledgeBase = None
    KnowledgeGapGPQA = None
    KnowledgeGapType = None
    ReasoningState = None
    RetrievedFact = None
    GapIdentifier = None

# V42 GPQA: Contrastive Explanation
try:
    from .contrastive_explanation import (
        ContrastiveExplainer,
        ContrastiveAnalysis,
        ChoiceExplanation,
        ExplanationType,
        ContradictionDetector,
        ExplanationGenerator,
        analyze_choices,
        explain_wrong_answers
    )
except ImportError:
    ContrastiveExplainer = None
    ContrastiveAnalysis = None
    ChoiceExplanation = None
    ExplanationType = None
    ContradictionDetector = None
    ExplanationGenerator = None
    analyze_choices = None
    explain_wrong_answers = None

# V42 GPQA: Domain Strategies
try:
    from .gpqa_strategies import (
        GPQAStrategyEngine,
        StrategyResult as GPQAStrategyResult,
        GPQADomain,
        DomainStrategy as GPQADomainStrategy,
        PHYSICS_STRATEGY as GPQA_PHYSICS_STRATEGY,
        CHEMISTRY_STRATEGY as GPQA_CHEMISTRY_STRATEGY,
        BIOLOGY_STRATEGY as GPQA_BIOLOGY_STRATEGY,
        apply_gpqa_strategy,
        get_domain_checklist
    )
except ImportError:
    GPQAStrategyEngine = None
    GPQAStrategyResult = None
    GPQADomain = None
    GPQADomainStrategy = None
    GPQA_PHYSICS_STRATEGY = None
    GPQA_CHEMISTRY_STRATEGY = None
    GPQA_BIOLOGY_STRATEGY = None
    apply_gpqa_strategy = None
    get_domain_checklist = None

# V42 GPQA: Enhanced Math Engine
try:
    from .enhanced_math_engine import (
        EnhancedMathEngine,
        MathResult,
        DimensionalAnalyzer as GPQADimensionalAnalyzer,
        SymbolicSolver,
        NumericalEvaluator,
        Unit,
        Quantity,
        CONSTANTS as GPQA_CONSTANTS,
        UNITS as GPQA_UNITS,
        solve_problem as gpqa_solve_problem,
        verify_answer as gpqa_verify_answer,
        check_dimensions as gpqa_check_dimensions
    )
except ImportError:
    EnhancedMathEngine = None
    MathResult = None
    GPQADimensionalAnalyzer = None
    SymbolicSolver = None
    NumericalEvaluator = None
    Unit = None
    Quantity = None
    GPQA_CONSTANTS = None
    GPQA_UNITS = None
    gpqa_solve_problem = None
    gpqa_verify_answer = None
    gpqa_check_dimensions = None

# V50: Discovery Engine Components
try:
    from .v50_world_simulator import (
        PhysicsEngine,
        ChemistryReactor,
        BiologicalPathwaySimulator,
        CounterfactualEngine as WorldCounterfactualEngine,
        WorldModelInterface,
        create_world_simulator,
        create_physics_engine,
        create_chemistry_reactor,
        create_biology_simulator
    )
except ImportError:
    PhysicsEngine = None
    ChemistryReactor = None
    BiologicalPathwaySimulator = None
    WorldCounterfactualEngine = None
    WorldModelInterface = None
    create_world_simulator = None
    create_physics_engine = None
    create_chemistry_reactor = None
    create_biology_simulator = None

try:
    from .v50_program_synthesis import (
        ReasoningPrimitiveLibrary,
        ProgramSynthesizer,
        ExecutionEngine,
        ProgramLearner,
        PrimitiveType,
        ReasoningPrimitive,
        ReasoningProgram,
        SynthesisResult,
        create_program_synthesizer,
        create_program_synthesis_reasoner
    )
except ImportError:
    ReasoningPrimitiveLibrary = None
    ProgramSynthesizer = None
    ExecutionEngine = None
    ProgramLearner = None
    PrimitiveType = None
    ReasoningPrimitive = None
    ReasoningProgram = None
    SynthesisResult = None
    create_program_synthesizer = None
    create_program_synthesis_reasoner = None

try:
    from .v50_causal_engine import (
        CausalStructureLearner,
        MechanismDiscovery,
        InterventionPlanner,
        CounterfactualReasoner as CausalCounterfactualReasoner,
        CausalInferenceEngine,
        CausalNode,
        CausalEdge as V50CausalEdge,
        CausalGraph as V50CausalGraph,
        Intervention as V50Intervention,
        create_causal_engine
    )
except ImportError:
    CausalStructureLearner = None
    MechanismDiscovery = None
    InterventionPlanner = None
    CausalCounterfactualReasoner = None
    CausalInferenceEngine = None
    CausalNode = None
    V50CausalEdge = None
    V50CausalGraph = None
    V50Intervention = None
    create_causal_engine = None

try:
    from .v50_meta_learner import (
        FailureAnalyzer as V50FailureAnalyzer,
        StrategyAbstractor,
        CurriculumGenerator,
        CompetenceTracker,
        MetaLearningSystem,
        FailureType,
        FailureAnalysis as V50FailureAnalysis,
        Strategy as V50Strategy,
        create_meta_learner
    )
except ImportError:
    V50FailureAnalyzer = None
    StrategyAbstractor = None
    CurriculumGenerator = None
    CompetenceTracker = None
    MetaLearningSystem = None
    V50FailureAnalysis = None
    V50Strategy = None
    create_meta_learner = None

try:
    from .v50_adversarial_debate import (
        ProposerAgent,
        CriticAgent,
        RedTeamAgent,
        VerifierAgent,
        ArbitratorAgent,
        DebateArena,
        AdversarialDebateReasoner,
        Argument as DebateArgument,
        Claim as DebateClaim,
        DebateResult,
        create_debate_reasoner
    )
except ImportError:
    ProposerAgent = None
    CriticAgent = None
    RedTeamAgent = None
    VerifierAgent = None
    ArbitratorAgent = None
    DebateArena = None
    AdversarialDebateReasoner = None
    DebateArgument = None
    DebateClaim = None
    DebateResult = None
    create_debate_reasoner = None

try:
    from .v50_abstraction_learning import (
        ConceptHierarchy,
        AbstractionEngine,
        AnalogyFinder as V50AnalogyFinder,
        KnowledgeTransferEngine,
        HierarchicalAbstractionLearner,
        AbstractionLevel,
        Concept,
        Analogy as V50Analogy,
        create_abstraction_learner
    )
except ImportError:
    ConceptHierarchy = None
    AbstractionEngine = None
    V50AnalogyFinder = None
    KnowledgeTransferEngine = None
    HierarchicalAbstractionLearner = None
    AbstractionLevel = None
    Concept = None
    V50Analogy = None
    create_abstraction_learner = None

# =========================================================================
# V60 Cognitive Agent Architecture
# =========================================================================

# V60: Predictive World Models
try:
    from .v60_predictive_world_models import (
        PredictiveWorldModelSystem,
        WorldModelLibrary,
        PhysicsWorldModel,
        ChemistryWorldModel,
        BiologyWorldModel,
        CausalWorldModel,
        ModelType as V60ModelType,
        DomainType,
        PredictionType,
        Observation as V60Observation,
        Prediction as V60Prediction,
        create_world_model_system,
        create_physics_model,
        create_chemistry_model,
        create_biology_model,
        create_causal_model
    )
except ImportError:
    PredictiveWorldModelSystem = None
    WorldModelLibrary = None
    PhysicsWorldModel = None
    ChemistryWorldModel = None
    BiologyWorldModel = None
    CausalWorldModel = None
    V60ModelType = None
    DomainType = None
    PredictionType = None
    V60Observation = None
    V60Prediction = None
    create_world_model_system = None
    create_physics_model = None
    create_chemistry_model = None
    create_biology_model = None
    create_causal_model = None

# V60: Grounded Representations
try:
    from .v60_grounded_representations import (
        GroundedRepresentationSystem,
        ConceptRepresentation,
        FeatureSpace,
        ConceptHierarchy as V60ConceptHierarchy,
        CompositionEngine,
        GroundingEngine,
        AnalogyEngine,
        CompositionType,
        GroundingType,
        AbstractionLevel as V60AbstractionLevel,
        create_representation_system,
        create_concept,
        create_grounding
    )
except ImportError:
    GroundedRepresentationSystem = None
    ConceptRepresentation = None
    FeatureSpace = None
    V60ConceptHierarchy = None
    CompositionEngine = None
    GroundingEngine = None
    AnalogyEngine = None
    CompositionType = None
    GroundingType = None
    V60AbstractionLevel = None
    create_representation_system = None
    create_concept = None
    create_grounding = None

# V60: Persistent Memory
try:
    from .v60_persistent_memory import (
        PersistentMemorySystem,
        WorkingMemory,
        EpisodicMemory as V60EpisodicMemory,
        SemanticMemory,
        MemoryConsolidator,
        MemoryRetriever,
        MemoryItem,
        Episode as V60Episode,
        SemanticConcept,
        MemoryType,
        RetrievalStrategy,
        ConsolidationMode,
        create_memory_system,
        create_standard_memory,
        create_large_memory,
        create_fast_memory
    )
except ImportError:
    PersistentMemorySystem = None
    WorkingMemory = None
    V60EpisodicMemory = None
    SemanticMemory = None
    MemoryConsolidator = None
    MemoryRetriever = None
    MemoryItem = None
    V60Episode = None
    SemanticConcept = None
    MemoryType = None
    RetrievalStrategy = None
    ConsolidationMode = None
    create_memory_system = None
    create_standard_memory = None
    create_large_memory = None
    create_fast_memory = None

# V60: Active Knowledge Acquisition
try:
    from .v60_active_knowledge import (
        ActiveKnowledgeSystem,
        GapDetector,
        HypothesisGenerator as V60HypothesisGenerator,
        ExperimentDesigner as V60ExperimentDesigner,
        KnowledgeIntegrator,
        CuriosityEngine,
        KnowledgeGap as V60KnowledgeGap,
        Hypothesis as V60Hypothesis,
        Experiment as V60Experiment,
        KnowledgeIntegration,
        KnowledgeGapType as V60KnowledgeGapType,
        HypothesisStatus,
        ExperimentType as V60ExperimentType,
        CuriositySource,
        create_active_knowledge_system,
        create_gap_detector,
        create_hypothesis_generator,
        create_curiosity_engine
    )
except ImportError:
    ActiveKnowledgeSystem = None
    GapDetector = None
    V60HypothesisGenerator = None
    V60ExperimentDesigner = None
    KnowledgeIntegrator = None
    CuriosityEngine = None
    V60KnowledgeGap = None
    V60Hypothesis = None
    V60Experiment = None
    KnowledgeIntegration = None
    V60KnowledgeGapType = None
    HypothesisStatus = None
    V60ExperimentType = None
    CuriositySource = None
    create_active_knowledge_system = None
    create_gap_detector = None
    create_hypothesis_generator = None
    create_curiosity_engine = None

# V60: Cognitive Self-Modification
try:
    from .v60_cognitive_self_modification import (
        CognitiveSelfModificationSystem,
        PerformanceMonitor,
        BottleneckDetector,
        StrategyEvaluator,
        ModificationEngine,
        SafeModificationApplier,
        PerformanceSnapshot,
        BottleneckAnalysis,
        ModificationProposal,
        Strategy as V60ModStrategy,
        ModificationType,
        PerformanceMetric,
        ModificationStatus,
        SafetyLevel,
        create_self_modification_system,
        create_performance_monitor,
        create_strategy_evaluator,
        create_strategy
    )
except ImportError:
    CognitiveSelfModificationSystem = None
    PerformanceMonitor = None
    BottleneckDetector = None
    StrategyEvaluator = None
    ModificationEngine = None
    SafeModificationApplier = None
    PerformanceSnapshot = None
    BottleneckAnalysis = None
    ModificationProposal = None
    V60ModStrategy = None
    ModificationType = None
    PerformanceMetric = None
    ModificationStatus = None
    SafetyLevel = None
    create_self_modification_system = None
    create_performance_monitor = None
    create_strategy_evaluator = None
    create_strategy = None

# V60: Active Inference Controller
try:
    from .v60_active_inference import (
        ActiveInferenceController,
        FreeEnergyComputer,
        PredictiveProcessor,
        ActionSelector,
        BeliefUpdater,
        ModelLearner,
        Belief as V60Belief,
        PredictionError,
        Policy,
        GenerativeModel,
        InferenceMode,
        BeliefType,
        HierarchyLevel,
        create_active_inference_controller,
        create_generative_model,
        create_belief,
        create_policy
    )
except ImportError:
    ActiveInferenceController = None
    FreeEnergyComputer = None
    PredictiveProcessor = None
    ActionSelector = None
    BeliefUpdater = None
    ModelLearner = None
    V60Belief = None
    PredictionError = None
    Policy = None
    GenerativeModel = None
    InferenceMode = None
    BeliefType = None
    HierarchyLevel = None
    create_active_inference_controller = None
    create_generative_model = None
    create_belief = None
    create_policy = None

# V60: Cognitive Agent (Integrated System)
try:
    from .v60_cognitive_agent import (
        V60CognitiveAgent,
        V60Config,
        V60Result,
        CognitiveMode,
        AgentState,
        CognitiveTask,
        CognitiveContext,
        create_v60_agent,
        create_v60_standard,
        create_v60_fast,
        create_v60_deep,
        create_v60_discovery,
        create_v60_gpqa
    )
except ImportError:
    V60CognitiveAgent = None
    V60Config = None
    V60Result = None
    CognitiveMode = None
    AgentState = None
    CognitiveTask = None
    CognitiveContext = None
    create_v60_agent = None
    create_v60_standard = None
    create_v60_fast = None
    create_v60_deep = None
    create_v60_discovery = None
    create_v60_gpqa = None

__version__ = '60.0'


# =========================================================================
# Backward Compatibility Aliases
# =========================================================================

# Aliases for common import names
LLMInference = LLMInferenceEngine  # For backward compatibility
ProofValidator = MathematicalProofValidator  # For backward compatibility
TheorySynthesis = TheorySynthesizer  # For backward compatibility
