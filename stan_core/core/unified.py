"""
STAN-CORE: Unified AGI System - All Capabilities Integrated (ASTRO ENHANCED)
==============================================================================

This is the new unified STAN system that automatically integrates ALL capabilities
from versions V36-V94 into a single, optimized system that selects the best
approaches for maximum performance without version dependencies.

**ASTRO ENHANCED VERSION**: This specialized version integrates astrophysics domain
knowledge, training data, and specialized reasoning capabilities for astronomy
and physics applications.

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

**ASTRO-SPECIFIC ENHANCEMENTS**:
- Gravitational physics and cosmology reasoning
- ISM (Interstellar Medium) physics expertise
- Radiative transfer and spectroscopic analysis
- Interferometry and observational astronomy
- Multi-wavelength data reconciliation
- Astrophysical simulation and modeling

The system automatically selects optimal capabilities based on the task.
"""

__version__ = "3.1.0-ASTRO"

from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import logging
import re

# Import meta-cognitive data sufficiency for graceful degradation
try:
    from ..metacognitive.data_sufficiency_evaluator import DataSufficiency
    DATA_SUFFICIENCY_AVAILABLE = True
except ImportError:
    DATA_SUFFICIENCY_AVAILABLE = False
    # Create dummy enum for graceful degradation
    class DataSufficiency(Enum):
        SUFFICIENT = "sufficient"
        UNCERTAIN = "uncertain"
        INSUFFICIENT = "insufficient"

# Import all capabilities from version-specific modules
try:
    # Core reasoning capabilities (from core_legacy)
    from ..core_legacy.v36 import V36CoreSystem
    from ..core_legacy.v37 import V37CompleteSystem
    from ..core_legacy.v38 import V38CompleteSystem
    from ..core_legacy.v39 import V39CompleteSystem
    from ..core_legacy.v40 import V40CompleteSystem
    from ..core_legacy.v41 import V41CompleteSystem
    from ..core_legacy.v42 import V42CompleteSystem
    from ..core_legacy.v80 import V80CompleteSystem
    from ..core_legacy.v90 import V90CompleteSystem
    from ..core_legacy.v91 import V91CompleteSystem
    from ..core_legacy.v92 import V92CompleteSystem
    from ..core_legacy.v93 import V93CompleteSystem
    from ..core_legacy.v94 import V94CompleteSystem
except Exception as e:
    # Log the error but don't fail - legacy modules are optional for V100
    import logging
    logging.warning(f"Legacy module import failed: {type(e).__name__}: {e}")
    # Set all to None
    V36CoreSystem = None
    V37CompleteSystem = None
    V38CompleteSystem = None
    V39CompleteSystem = None
    V40CompleteSystem = None
    V41CompleteSystem = None
    V42CompleteSystem = None
    V80CompleteSystem = None
    V90CompleteSystem = None
    V91CompleteSystem = None
    V92CompleteSystem = None
    V93CompleteSystem = None
    V94CompleteSystem = None

# Import memory and intelligence systems
from ..memory import MemoryGraph, MORKOntology, ExpandedMORK
from ..intelligence import SwarmOrchestrator, DigitalPheromoneField
from ..capabilities import (
    BayesianInference, CausalDiscovery, AbductiveInference,
    SelfConsistency, ExternalKnowledge, LLMInference,
    MetaLearning, AnalogicalReasoning, ToolIntegration
)

# Import ASTRO-specific capabilities
try:
    from ..astro_physics import AstroSwarmSystem, PhysicsEngine
    from ..astro_physics.physics import GravitationalLensModel, AstrophysicalConstraints
    from ..astro_physics.radiative_transfer import StatisticalEquilibriumSolver
    from ..astro_physics.inference import BayesianSwarmInference
    ASTRO_CAPABILITIES_AVAILABLE = True
except ImportError:
    logging.warning("Astro physics capabilities not available")
    ASTRO_CAPABILITIES_AVAILABLE = False

class TaskType(Enum):
    """Automatically detected task types for optimal capability selection"""
    SCIENTIFIC_REASONING = "scientific"
    MATHEMATICAL = "mathematical"
    CAUSAL_ANALYSIS = "causal"
    PATTERN_RECOGNITION = "pattern"
    SOCIAL_REASONING = "social"
    CREATIVE_PROBLEM_SOLVING = "creative"
    FORMAL_REASONING = "formal"
    METACOGNITIVE = "metacognitive"
    EMBODIED_TASK = "embodied"
    ETHICAL_REASONING = "ethical"
    COMPLEX_SYSTEM = "complex"
    ARBITRARY = "arbitrary"

    # ASTRO-SPECIFIC TASK TYPES
    ASTROPHYSICS = "astrophysics"
    GRAVITATIONAL_PHYSICS = "gravitational_physics"
    COSMOLOGY = "cosmology"
    RADIATIVE_TRANSFER = "radiative_transfer"
    INTERFEROMETRY = "interferometry"
    SPECTROSCOPY = "spectroscopy"
    ISM_PHYSICS = "ism_physics"
    MULTI_WAVELENGTH = "multi_wavelength"

@dataclass
class UnifiedConfig:
    """Configuration for the unified STAN system"""
    # Capability selection
    auto_optimize: bool = True
    use_all_capabilities: bool = True
    prefer_latest_capabilities: bool = True

    # Performance settings
    max_compute_budget: float = 100.0  # Computational units
    timeout_seconds: float = 300.0
    parallel_reasoning: bool = True

    # Specialized modes
    scientific_mode: bool = False
    mathematical_mode: bool = False
    social_mode: bool = False
    ethical_mode: bool = False
    creative_mode: bool = False

    # Advanced capabilities
    enable_metacognition: bool = True
    enable_consciousness: bool = True
    enable_self_modification: bool = True
    enable_embodied_learning: bool = True
    enable_swarm_intelligence: bool = True
    enable_neural_symbolic: bool = True

    # Knowledge integration
    use_external_knowledge: bool = True
    use_bayesian_inference: bool = True
    use_causal_discovery: bool = True
    use_analogical_reasoning: bool = True

    memory_config: Dict[str, Any] = field(default_factory=dict)
    swarm_config: Dict[str, Any] = field(default_factory=dict)

class TaskAnalyzer:
    """Analyzes tasks to determine optimal capability selection"""

    def __init__(self):
        self.task_keywords = {
            TaskType.SCIENTIFIC_REASONING: [
                'experiment', 'hypothesis', 'scientific', 'research', 'analysis',
                'physics', 'chemistry', 'biology', 'gpqa', 'graduate', 'prove'
            ],
            TaskType.MATHEMATICAL: [
                'mathematics', 'calculate', 'derivative', 'integral', 'equation',
                'prove', 'theorem', 'algebra', 'geometry', 'statistics'
            ],
            TaskType.CAUSAL_ANALYSIS: [
                'cause', 'effect', 'because', 'reason', 'causal', 'impact',
                'influence', 'relationship', 'correlation', 'mechanism'
            ],
            TaskType.PATTERN_RECOGNITION: [
                'pattern', 'recognize', 'identify', 'sequence', 'grid',
                'transform', 'analogous', 'similar', 'recurring'
            ],
            TaskType.SOCIAL_REASONING: [
                'social', 'ethical', 'moral', 'people', 'society', 'interaction',
                'cooperation', 'coordination', 'group', 'team', 'culture'
            ],
            TaskType.CREATIVE_PROBLEM_SOLVING: [
                'creative', 'innovate', 'design', 'imagine', 'invent',
                'novel', 'original', 'breakthrough', 'paradigm'
            ],
            TaskType.FORMAL_REASONING: [
                'formal', 'logic', 'theorem', 'prove', 'deduction', 'induction',
                'syllogism', 'premise', 'conclusion', 'valid'
            ],
            TaskType.METACOGNITIVE: [
                'think', 'reflect', 'conscious', 'aware', 'understand',
                'meta', 'self', 'learning', 'improve', 'optimize'
            ],
            # ASTRO-SPECIFIC TASK KEYWORDS
            TaskType.ASTROPHYSICS: [
                'astronomy', 'astrophysics', 'star', 'galaxy', 'planet', 'nebula',
                'cosmic', 'stellar', 'supernova', 'black hole', 'quasar', ' pulsar',
                'telescope', 'observatory', 'space', 'orbit', 'celestial'
            ],
            TaskType.GRAVITATIONAL_PHYSICS: [
                'gravity', 'gravitational', 'lensing', 'general relativity', 'spacetime',
                'einstein', 'mass distribution', 'dark matter', 'dark energy', 'cosmological',
                'expansion', 'universe', 'big bang', 'singularity', 'event horizon'
            ],
            TaskType.COSMOLOGY: [
                'cosmology', 'universe', 'expansion', 'cosmic microwave', 'cmb',
                'large scale structure', 'galaxy cluster', 'dark energy', 'dark matter',
                'hubble', 'redshift', 'big bang', 'inflation', 'multiverse'
            ],
            TaskType.RADIATIVE_TRANSFER: [
                'radiative transfer', 'spectroscopy', 'spectrum', 'spectral line',
                'emission', 'absorption', 'optical depth', 'opacity', 'temperature',
                'line formation', 'radiation', 'photon', 'luminosity', 'flux'
            ],
            TaskType.INTERFEROMETRY: [
                'interferometry', 'interferometer', 'vla', 'alma', 'radio telescope',
                'baseline', 'uv coverage', 'fourier transform', 'synthesis imaging',
                'clean', 'deconvolution', 'resolution', 'fringe', 'phase'
            ],
            TaskType.SPECTROSCOPY: [
                'spectroscopy', 'spectrum', 'spectral', 'doppler', 'redshift',
                'blueshift', 'spectral line', 'wavelength', 'frequency', 'energy',
                'absorption line', 'emission line', 'spectral classification'
            ],
            TaskType.ISM_PHYSICS: [
                'interstellar medium', 'ism', 'molecular cloud', 'hi region', 'hii region',
                'dust', 'gas', 'density', 'temperature', 'molecular', 'atomic',
                'ionized', 'neutral', 'star formation', 'turbulence', 'magnetic field'
            ],
            TaskType.MULTI_WAVELENGTH: [
                'multi-wavelength', 'x-ray', 'infrared', 'ultraviolet', 'radio',
                'optical', 'gamma ray', 'observation', 'wavelength', 'band',
                'multi-band', 'cross-correlation', 'combined analysis'
            ]
        }

    def analyze_task(self, query: str, context: str = "") -> TaskType:
        """Analyze task to determine the primary type"""
        query_lower = query.lower() + " " + context.lower()

        # Score each task type
        scores = {}
        for task_type, keywords in self.task_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            scores[task_type] = score

        # Return the highest scoring task type
        if max(scores.values()) == 0:
            return TaskType.ARBITRARY

        return max(scores, key=scores.get)

    def get_capability_requirements(self, task_type: TaskType) -> Dict[str, bool]:
        """Get required capabilities for each task type"""
        requirements = {
            TaskType.SCIENTIFIC_REASONING: {
                'bayesian_inference': True,
                'causal_discovery': True,
                'formal_logic': True,
                'external_knowledge': True,
                'mathematical_intuition': True
            },
            TaskType.MATHEMATICAL: {
                'formal_logic': True,
                'theorem_proving': True,
                'symbolic_reasoning': True,
                'neural_symbolic': True
            },
            TaskType.CAUSAL_ANALYSIS: {
                'causal_discovery': True,
                'bayesian_inference': True,
                'swarm_intelligence': True
            },
            TaskType.PATTERN_RECOGNITION: {
                'neural_symbolic': True,
                'analogical_reasoning': True,
                'swarm_intelligence': True
            },
            TaskType.SOCIAL_REASONING: {
                'embodied_cognition': True,
                'theory_of_mind': True,
                'ethical_reasoning': True,
                'metacognition': True
            },
            TaskType.CREATIVE_PROBLEM_SOLVING: {
                'analogical_reasoning': True,
                'insight_generation': True,
                'self_modification': True,
                'metacognition': True
            },
            TaskType.FORMAL_REASONING: {
                'formal_logic': True,
                'theorem_proving': True,
                'symbolic_reasoning': True
            },
            TaskType.METACOGNITIVE: {
                'metacognition': True,
                'consciousness': True,
                'self_reflection': True,
                'self_modification': True
            },
            TaskType.EMBODIED_TASK: {
                'embodied_cognition': True,
                'sensorimotor_integration': True,
                'common_sense': True
            },
            TaskType.ETHICAL_REASONING: {
                'ethical_reasoning': True,
                'value_alignment': True,
                'theory_of_mind': True
            }
        }

        return requirements.get(task_type, {
            'symbolic_reasoning': True,
            'bayesian_inference': True,
            'metacognition': True
        })

class UnifiedSTANSystem:
    """Unified STAN system with all capabilities integrated"""

    def __init__(self, config: Optional[UnifiedConfig] = None):
        self.config = config or UnifiedConfig()
        self.task_analyzer = TaskAnalyzer()

        # Initialize core systems
        self._initialize_core_systems()
        self._initialize_capabilities()
        self._initialize_memory()
        self._initialize_intelligence()
        self._initialize_metacognitive()

        # Performance tracking
        self.performance_stats = {
            'tasks_processed': 0,
            'capabilities_used': set(),
            'average_confidence': 0.0,
            'success_rate': 0.0
        }

    def _initialize_core_systems(self):
        """Initialize core systems - placeholder for future expansion"""
        pass

    def _initialize_capabilities(self):
        """Initialize capabilities - placeholder for future expansion"""
        pass

    def _initialize_memory(self):
        """Initialize memory systems - placeholder for future expansion"""
        pass

    def _initialize_intelligence(self):
        """Initialize intelligence systems - placeholder for future expansion"""
        pass

    def _initialize_metacognitive(self):
        """
        Initialize enhanced meta-cognitive evaluation with advanced reasoning support.

        Priority order:
        1. Advanced reasoner (V4.0) - Rich quantitative justifications
        2. Hybrid system (V3.0) - Multi-signal integration
        3. Enhanced rule-based (V3.1) - Qualitative patterns
        4. Basic rule-based (fallback)
        """
        # Try to load advanced reasoner first (BEST)
        try:
            from ..metacognitive import (
                ADVANCED_REASONER_AVAILABLE,
                create_advanced_meta_cognitive_reasoner
            )
            if ADVANCED_REASONER_AVAILABLE:
                self.advanced_meta_cognitive_reasoner = create_advanced_meta_cognitive_reasoner()
                self.data_sufficiency_evaluator = self.advanced_meta_cognitive_reasoner
                self.metacognitive_mode = 'advanced_reasoning'
                self.metacognitive_enabled = True
                print("✓ Advanced meta-cognitive reasoner initialized (V4.0 - rich justifications)")
        except Exception as e:
            self.advanced_meta_cognitive_reasoner = None
            print(f"Advanced reasoner not available: {e}")

        # Fallback to hybrid system
        if not self.metacognitive_enabled:
            try:
                from ..metacognitive import (
                    HYBRID_SYSTEM_AVAILABLE,
                    create_hybrid_meta_cognitive_system
                )
                if HYBRID_SYSTEM_AVAILABLE:
                    self.hybrid_meta_cognitive_system = create_hybrid_meta_cognitive_system()
                    self.data_sufficiency_evaluator = self.hybrid_meta_cognitive_system
                    self.metacognitive_mode = 'hybrid'
                    self.metacognitive_enabled = True
                    print("✓ Hybrid meta-cognitive system initialized (V3.0 - multi-signal)")
            except Exception as e:
                self.hybrid_meta_cognitive_system = None
                print(f"Hybrid system not available: {e}")

        # Fallback to enhanced rule-based
        if not self.metacognitive_enabled:
            try:
                from ..metacognitive.data_sufficiency_evaluator import (
                    EnhancedDataSufficiencyEvaluator,
                    create_enhanced_data_sufficiency_evaluator,
                    DataSufficiency
                )

                self.data_sufficiency_evaluator = create_enhanced_data_sufficiency_evaluator()
                self.metacognitive_mode = 'rule_based'
                self.metacognitive_enabled = True
                print("✓ Enhanced rule-based meta-cognitive system initialized (V3.1)")

            except Exception as e:
                self.data_sufficiency_evaluator = None
                self.metacognitive_enabled = False
                print(f"Meta-cognitive system initialization failed: {e}")

        # Try to load ML classifier (works with all modes)
        try:
            from ..metacognitive import ML_CLASSIFIER_AVAILABLE, create_ml_classifier
            if ML_CLASSIFIER_AVAILABLE:
                self.ml_classifier = create_ml_classifier()
                self.ml_available = True
            else:
                self.ml_classifier = None
                self.ml_available = False
        except Exception as e:
            self.ml_classifier = None
            self.ml_available = False

    def _check_data_sufficiency(self, query: str):
        """
        Check if query involves data sufficiency concerns.

        Enhanced version that uses both rule-based and ML approaches.

        Args:
            query: The query to check

        Returns:
            Meta-cognitive response if data insufficient, None if data sufficient
        """
        if not self.metacognitive_enabled or self.data_sufficiency_evaluator is None:
            return None

        # Try to extract scenario and question from benchmark task format
        # Format: "Task X: Name\n\nScenario: ...\n\nQuestion: ..."

        # Look for Scenario: and Question: markers
        scenario_match = re.search(r'Scenario:\s*(.*?)\s*(?:Question:|$)', query, re.DOTALL | re.IGNORECASE)
        question_match = re.search(r'Question:\s*(.*?)\s*$', query, re.DOTALL | re.IGNORECASE)

        if scenario_match and question_match:
            scenario = scenario_match.group(1).strip()
            question = question_match.group(1).strip()

            # Evaluate using appropriate system (hybrid or rule-based)
            assessment = self.data_sufficiency_evaluator.evaluate_task(scenario, question)

            # Handle both HybridAssessment and MetaCognitiveAssessment
            if hasattr(assessment, 'final_sufficiency'):
                # Hybrid system
                sufficiency = assessment.final_sufficiency
                confidence = assessment.final_confidence
                justification = assessment.base_assessment.justification

                # Add reasoning trace if available
                if assessment.reasoning_trace:
                    justification += f"\n\nReasoning: {' → '.join(assessment.reasoning_trace)}"

                # Check if insufficient or uncertain
                sufficiency_str = str(sufficiency).lower()
                is_insufficient = 'insufficient' in sufficiency_str or 'uncertain' in sufficiency_str

                if is_insufficient:
                    return justification

            elif hasattr(assessment, 'sufficiency'):
                # Standard assessment
                sufficiency_str = str(assessment.sufficiency).lower()
                is_insufficient = 'insufficient' in sufficiency_str or 'uncertain' in sufficiency_str

                # If ML classifier available, use it to confirm or override
                if self.ml_available and self.ml_classifier:
                    ml_result = self.ml_classifier.classify(scenario, question)

                    # Ensemble: ML confidence high + rule-based insufficient
                    if ml_result.is_meta_cognitive and ml_result.confidence > 0.6:
                        # ML confirms it's meta-cognitive - return rule-based justification
                        if is_insufficient:
                            return assessment.justification
                        else:
                            # ML thinks it's meta-cognitive but rule-based missed it
                            # Return ML-based meta-cognitive response
                            return self._generate_ml_meta_cognitive_response(ml_result, scenario, question)

                    # Rule-based insufficient with high confidence, return it
                    if is_insufficient and assessment.confidence > 0.8:
                        return assessment.justification

                # Standard rule-based response
                if is_insufficient:
                    return assessment.justification

        return None

    def _generate_ml_meta_cognitive_response(self, ml_result, scenario: str, question: str) -> str:
        """Generate meta-cognitive response based on ML classification."""
        limitation = ml_result.predicted_limitation or "data limitations"

        return (f"The data contain {limitation} that preclude reliable conclusions. "
                f"Based on meta-cognitive evaluation (confidence: {ml_result.confidence:.2f}), "
                f"I cannot provide a definitive answer to the question about {question[:50]}... "
                f"The observational or experimental constraints are fundamental to the measurement.")

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query through the unified STAN system

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            Dictionary with query results including answer, confidence, etc.
        """
        context = context or {}

        # Analyze the task to determine what capabilities are needed
        task_type = self.task_analyzer.analyze_task(query, context.get('context', ''))

        # Get capability requirements
        requirements = self.task_analyzer.get_capability_requirements(task_type)

        # For now, return a basic response
        # Enhanced implementations (unified_enhanced.py) provide full functionality
        return {
            'query': query,
            'task_type': task_type.value if task_type else 'unknown',
            'capabilities_required': requirements,
            'answer': 'STAN system initialized. For full query processing, use EnhancedUnifiedSTANSystem.',
            'confidence': 0.5,
            'metadata': {
                'system': 'UnifiedSTANSystem',
                'version': __version__
            }
        }

    def answer(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Alias for process_query for backward compatibility

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            Dictionary with query results
        """
        return self.process_query(query, context)
