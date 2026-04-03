"""
STAR-Learn: Self-Teaching Autonomous Recursive Learner for STAN_IX_ASTRO

A comprehensive autonomous self-teaching architecture that enables STAN to:
1. Generate its own training problems
2. Evaluate solutions using intrinsic rewards
3. Improve iteratively without human intervention
4. Transfer knowledge across domains
5. Make genuine scientific discoveries
6. Coordinate via stigmergy for emergent intelligence
7. Modify its own architecture safely

Components:
- SelfRewardingEngine: Intrinsic reward calculation for discoveries
- AutonomousTrainingLoop: Self-teaching iteration manager
- CurriculumGenerator: Autonomous problem generation
- RecursiveImprover: Metacognitive self-improvement
- StigmergicMemory: Biological field persistence
- BenchmarkSuite: Evaluation metrics

V2.0 Enhancements:
- EnhancedRewardCalculator: Embedding-based novelty detection
- PhysicsDataLibrary: Real-world scientific datasets
- PhysicalLawDiscovery: Law discovery from data
- MultiAgentSwarm: Collaborative multi-agent discovery
- ContinuousLearningSystem: arXiv literature integration

V2.5 MAJOR Enhancements (AGI Capabilities):
- CausalDiscoveryEngine: True causal reasoning (PC Algorithm, Do-Calculus)
- TheoryConstructionSystem: Build complete scientific theories
- AutonomousExperimentSystem: Design and run experiments autonomously
- MetaLearningSystem: Learn to learn, few-shot adaptation
- ConsciousnessSimulator: Metacognitive awareness and theory of mind

V3.0 Astronomy Specialization (MAJOR STEP FORWARD):
- AstronomyCausalDiscoverySystem: Gas dynamics, filament formation, radiative transfer
- SPH Simulation: Smoothed Particle Hydrodynamics for gas dynamics and star formation
- InterstellarChemistryNetwork: Molecular reaction networks and deuterium fractionation
- StellarPhysics & HII Regions: Stellar evolution, ionization, feedback
- MultiWavelengthFusion: Radio, mm, sub-mm, IR data combination and analysis

Version: 3.0.0
Date: 2026-03-16
"""

from .self_rewarding import (
    SelfRewardingEngine,
    IntrinsicReward,
    RewardComponent,
    RewardConfig
)

from .autonomous_loop import (
    AutonomousTrainingLoop,
    TrainingIteration,
    IterationResult,
    LoopConfig
)

from .curriculum_generator import (
    CurriculumGenerator,
    GeneratedProblem,
    ProblemDifficulty,
    DomainTask,
    CurriculumConfig
)

from .recursive_improver import (
    RecursiveImprover,
    ImprovementStrategy,
    ImprovementResult,
    MetacognitiveState,
    ImproverConfig
)

from .stigmergic_memory import (
    StigmergicMemory,
    BiologicalFieldState,
    PheromoneTrail,
    DiscoverySignature,
    StigmergicConfig
)

from .benchmark_suite import (
    BenchmarkSuite,
    BenchmarkResult,
    SelfTeachingMetrics,
    BenchmarkConfig,
    TIER_1_TESTS,
    TIER_2_TESTS,
    TIER_3_TESTS,
    TIER_4_TESTS
)

# V2.0 Enhanced Modules
try:
    from .embedding_novelty import (
        EnhancedRewardCalculator,
        EmbeddingVector,
        ScientificKnowledgeGraph,
        SimpleEmbeddingModel,
        create_enhanced_reward_calculator
    )
except ImportError:
    EnhancedRewardCalculator = None
