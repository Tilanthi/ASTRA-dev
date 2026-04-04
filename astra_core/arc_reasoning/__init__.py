"""
STAN ARC Reasoning Module
"""

# Import next-generation solver
try:
    from .next_gen_solver import (
        SemanticConcept,
        SemanticAnalyzer,
        AbstractionEngine,
        TransformationPrimitive,
        Rotate90,
        Rotate180,
        Rotate270,
        ReflectHorizontal,
        ReflectVertical,
        Transpose,
        ColorMap,
        Identity,
        TransformationHypothesis,
        HypothesisGenerator,
        NextGenARC_Solver as NextGenARC,
    )
    _next_gen_available = True
except ImportError:
    _next_gen_available = False
    SemanticConcept = None
    SemanticAnalyzer = None
    AbstractionEngine = None
    TransformationPrimitive = None
    Rotate90 = None
    Rotate180 = None
    Rotate270 = None
    ReflectHorizontal = None
    ReflectVertical = None
    Transpose = None
    ColorMap = None
    Identity = None
    TransformationHypothesis = None
    HypothesisGenerator = None
    NextGenARC = None

# Import improved solver
try:
    from .improved_solver import ImprovedARC_Solver, SolutionHypothesis
    _improved_available = True
except ImportError:
    _improved_available = False
    ImprovedARC_Solver = None
    SolutionHypothesis = None

# Import causal solver
try:
    from .causal_arc_solver import CausalARC_Solver, GridObject, extract_objects
    _causal_available = True
except ImportError:
    _causal_available = False
    CausalARC_Solver = None
    GridObject = None
    extract_objects = None

# Import ensemble solver
try:
    from .ensemble_arc_solver import EnsembleARC_Solver, SolverPrediction
    _ensemble_available = True
except ImportError:
    _ensemble_available = False
    EnsembleARC_Solver = None
    SolverPrediction = None

# Import advanced solver (new - integrates all innovative approaches)
try:
    from .advanced_arc_solver import AdvancedARC_Solver, StatisticalPatternEngine, GridFeatures
    _advanced_available = True
except ImportError:
    _advanced_available = False
    AdvancedARC_Solver = None
    StatisticalPatternEngine = None
    GridFeatures = None

# Import super ensemble solver (combines all approaches)
try:
    from .super_ensemble_solver import SuperEnsembleSolver
    _super_ensemble_available = True
except ImportError:
    _super_ensemble_available = False
    SuperEnsembleSolver = None

# Import neuro-symbolic hybrid solver (NEW - integrates neural + symbolic)
try:
    from .neuro_symbolic_solver import (
        NeuroSymbolicHybridSolver,
        HybridSolution,
        FeatureExtractor,
        PatternMemory,
        SymbolicReasoner,
        DiscoveryEngine,
    )
    _neuro_symbolic_available = True
except ImportError:
    _neuro_symbolic_available = False
    NeuroSymbolicHybridSolver = None
    HybridSolution = None
    FeatureExtractor = None
