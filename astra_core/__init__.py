"""
STAN-CORE V4.0: Unified AGI System - All Capabilities Integrated
================================================================

This is the unified STAN system that integrates ALL capabilities from V36-V94
plus the V4 causal reasoning enhancements and V4.0 revolutionary capabilities
into a single, optimized system.

Core Integrated Capabilities:
- Symbolic causal reasoning (V36)
- Swarm intelligence & memory (V37)
- Bayesian inference & tools (V38)
- Advanced reasoning capabilities (V39)
- Formal logic & causal models (V40)
- Self-reflection & analogical reasoning (V41)
- GPQA-optimized scientific reasoning (V42-V50)
- Neural-symbolic integration (V80)
- Metacognitive consciousness (V90)
- Embodied social AGI (V91)
- Scientific discovery (V92)
- Self-modifying architecture (V93)
- Embodied learning (V94)
- True causal reasoning (V4): discovery, intervention, counterfactuals

V4.0 Revolutionary Capabilities (NEW):
- Meta-Context Engine (MCE): Dynamic context layering with predictive, analytical, emotional frames
- Autocatalytic Self-Compiler (ASC): Recursive self-improvement through architecture rewriting
- Cognitive-Relativity Navigator (CRN): Multi-scale abstraction reasoning (0-100 zoom)
- Multi-Mind Orchestration Layer (MMOL): Specialized sub-minds with anticipatory arbitration

The system automatically selects optimal capabilities based on the task.

Directory Structure:
-------------------
astra_core_v4/
    core/           - Unified system + Legacy version cores (V36-V94)
    capabilities/   - Advanced reasoning capabilities
    memory/         - MORK ontology, vector stores, graph memory, episodic, semantic, etc.
    intelligence/   - Swarm orchestration, pheromones, evolution
    solvers/        - Problem-specific solvers (ARC-AGI)
    knowledge/      - Domain priors and ontology definitions
    causal/         - True causal reasoning (V4 addition)
    discovery/      - Scientific discovery engine
    simulation/     - Physics and market simulators
    trading/        - Trading analysis
    metacognitive/  - Meta-cognitive monitoring
    neural/         - Neural network training
    creative/       - Creative cognition
    tests/          - Integration tests
    utils/          - Utility functions

Version: 4.0.0 (Unified Architecture with V4 Causal Extensions + Phase 2-4 Enhancements)
Date: March 19, 2026
"""

__version__ = "4.0.0"

# =============================================================================
# UNIFIED SYSTEM - All Capabilities Integrated (V36-V94 + V4)
# =============================================================================
try:
    from .core.unified import (
        UnifiedSTANSystem, UnifiedConfig, TaskType, TaskAnalyzer,
        create_unified_stan_system
    )
except ImportError:
    UnifiedSTANSystem = None
    UnifiedConfig = None
    TaskType = None
    TaskAnalyzer = None
    create_unified_stan_system = None

# =============================================================================
# V4 Causal Reasoning Components
# =============================================================================
try:
    from .causal.model.scm import StructuralCausalModel, Variable, StructuralEquation
    from .causal.discovery.pc_algorithm import PCAlgorithm
    from .causal.discovery.temporal_discovery import TemporalCausalDiscovery
    from .causal.model.intervention import Intervention
    from .causal.model.counterfactual import CounterfactualQuery
except ImportError:
    StructuralCausalModel = None
    Variable = None
    StructuralEquation = None
    PCAlgorithm = None
    TemporalCausalDiscovery = None
    Intervention = None
    CounterfactualQuery = None

# =============================================================================
# V47+ Enhanced Causal Discovery
# =============================================================================
try:
    from .causal.discovery.bayesian_structure_learning import (
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
    from .causal.discovery.eig_calculator import (
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
    from .causal.discovery.online_causal_learning import (
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

try:
    from .causal.inference import (
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

# =============================================================================
# Memory Systems (Merged from both astra_core and astra_core_v4)
# =============================================================================
try:
    from .memory import (
        # MORK Ontology (from astra_core)
        MORKOntology, OntologyNode, SemanticRelation, SemanticRelationType,
        ExpandedMORK, MORKConcept, ScientificDomain,
        # Memory Graph (from astra_core)
        MemoryGraph, GraphNode, GraphEdge, NodeType, EdgeType,
        # Vector Store (from astra_core)
        MilvusVectorStore, VectorBackend, DistanceMetric, InMemoryVectorIndex,
        # RRF Fusion (from astra_core)
        ThreeWayRRF, RRFResult,
    )
except ImportError:
    MORKOntology = None
# =============================================================================
# PHASE 2-4 ENHANCEMENTS: Domain Expansion, Physics Integration, Validation
# =============================================================================
# These represent the enhanced capabilities added to address RASTI paper limitations

# -----------------------------------------------------------------------------
# Domain System (Phase 2): Modular domain architecture for specialized astronomy
# -----------------------------------------------------------------------------
try:
    from .domains import (
        # Base domain module interface
        BaseDomainModule,
        DomainConfig,
        DomainQueryResult,
        CrossDomainConnection,
        DomainModuleRegistry,
        register_domain,
    )
    from .domains.registry import DomainRegistry as DomainsRegistry
except ImportError:
    BaseDomainModule = None
    DomainConfig = None
    DomainQueryResult = None
    CrossDomainConnection = None
    DomainModuleRegistry = None
    register_domain = None
    DomainsRegistry = None

# Available domain modules
try:
    from .domains.exoplanets import ExoplanetDomain
    from .domains.gravitational_waves import GravitationalWavesDomain
    from .domains.cosmology import CosmologyDomain
    from .domains.solar_system import SolarSystemDomain
    from .domains.time_domain import TimeDomainDomain
except ImportError:
    ExoplanetDomain = None
    GravitationalWavesDomain = None
    CosmologyDomain = None
    SolarSystemDomain = None
    TimeDomainDomain = None

# -----------------------------------------------------------------------------
# Cross-Domain Meta-Learning (Phase 2): Rapid domain adaptation
# -----------------------------------------------------------------------------
try:
    from .reasoning.cross_domain_meta_learner import (
        CrossDomainMetaLearner,
        DomainSimilarity,
        DomainFeatures,
        AdaptationResult,
    )
except ImportError:
    CrossDomainMetaLearner = None
    DomainSimilarity = None
    DomainFeatures = None
    AdaptationResult = None

# -----------------------------------------------------------------------------
# Unified Physics Engine (Phase 3): Differentiable physics with constraints
# -----------------------------------------------------------------------------
try:
    from .physics import (
        # Main physics engine
        UnifiedPhysicsEngine,
        PhysicsDomain,
        PhysicsResult,
        PhysicsConstraint,
        # Physics intuition development
        PhysicsCurriculum,
        PhysicalAnalogicalReasoner,
        # Learning and reasoning
        ComplexityLevel,
        LearningStage,
        PhysicalAnalogy,
        Phenomenon,
    )
except ImportError:
    UnifiedPhysicsEngine = None
    PhysicsDomain = None
    PhysicsResult = None
    PhysicsConstraint = None
    PhysicsCurriculum = None
    PhysicalAnalogicalReasoner = None
    ComplexityLevel = None
    LearningStage = None
    PhysicalAnalogy = None
    Phenomenon = None

# -----------------------------------------------------------------------------
# Enhanced Unified System (Phase 4): Integration of all enhancements
# -----------------------------------------------------------------------------
try:
    from .core.unified_enhanced import (
        EnhancedUnifiedSTANSystem,
        EnhancedUnifiedConfig,
        create_enhanced_stan_system,
    )
except ImportError:
    EnhancedUnifiedSTANSystem = None
    EnhancedUnifiedConfig = None
    create_enhanced_stan_system = None

# -----------------------------------------------------------------------------
# Validation Framework (Phase 4): Benchmarking and testing
# -----------------------------------------------------------------------------
try:
    from .tests.validation_benchmarks import (
        ValidationSuite,
        BenchmarkResult,
        create_validation_suite,
        run_validation_suite,
    )
except ImportError:
    ValidationSuite = None
    BenchmarkResult = None
    create_validation_suite = None
    run_validation_suite = None

# Export aliases for backwards compatibility
create_stan_system = create_enhanced_stan_system

# =============================================================================
# PDF Generator (Publication-Ready Paper Generation)
# =============================================================================
try:
    from .utils.pdf_generator import (
        PDFGenerator,
        PDFFormat,
        TextAlign,
        PDFSection,
        PDFTable,
        PDFCodeBlock,
        generate_stan_paper_with_figures,
        create_publication_pdf_from_markdown,
        REPORTLAB_AVAILABLE,
        FPDF_AVAILABLE,
    )
except ImportError:
    PDFGenerator = None
    PDFFormat = None
    TextAlign = None
    PDFSection = None
    PDFTable = None
    PDFCodeBlock = None
    generate_stan_paper_with_figures = None
    create_publication_pdf_from_markdown = None
    REPORTLAB_AVAILABLE = False
    FPDF_AVAILABLE = False
