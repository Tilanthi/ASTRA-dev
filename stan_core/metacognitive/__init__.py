"""
Meta-Cognitive Package for ASTRA
==================================

This package provides meta-cognitive capabilities for ASTRA,
including data sufficiency evaluation, ML classification, fine-tuning,
context management, and self-monitoring.

Key Modules:
    - EnhancedDataSufficiencyEvaluator: Evaluates whether data are sufficient
      to support requested scientific conclusions (enhanced patterns v3.1)
    - HybridMetaCognitiveSystem: Advanced hybrid system combining
      rule-based, causal, Bayesian, and domain knowledge approaches
    - AdvancedMetaCognitiveReasoner: Generates high-quality quantitative
      justifications using V42-V94 reasoning capabilities
    - MetaCognitiveClassifier: ML-based meta-cognitive task detection
    - EnsembleMetaCognitiveEvaluator: Combines rule-based and ML approaches
    - MetaCognitiveFinetuner: Fine-tuning system for meta-cognitive prompts
    - MetaContextEngine: Manages multi-layered context awareness
    - CognitiveMonitor: Monitors cognitive processes

Author: ASTRA Project
Date: 2026-03-31
Version: 4.0 (Advanced Reasoning with Rich Justifications)
"""

from .monitoring.monitor import CognitiveMonitor, ProcessState
from .data_sufficiency_evaluator import (
    DataSufficiency,
    LimitationType,
    MetaCognitiveAssessment,
    DataSufficiencyEvaluator,
    EnhancedDataSufficiencyEvaluator,
    create_data_sufficiency_evaluator,
    create_enhanced_data_sufficiency_evaluator
)

try:
    from .hybrid_meta_cognitive_system import (
        HybridMetaCognitiveSystem,
        HybridAssessment,
        ConfidenceLevel,
        create_hybrid_meta_cognitive_system
    )
    HYBRID_SYSTEM_AVAILABLE = True
except ImportError:
    HYBRID_SYSTEM_AVAILABLE = False
    HybridMetaCognitiveSystem = None
    HybridAssessment = None
    ConfidenceLevel = None
    create_hybrid_meta_cognitive_system = None

try:
    from .ml_classifier import (
        MetaCognitiveClassifier,
        ClassificationResult,
        EnsembleMetaCognitiveEvaluator,
        create_ml_classifier,
        create_ensemble_evaluator
    )
    ML_CLASSIFIER_AVAILABLE = True
except ImportError:
    ML_CLASSIFIER_AVAILABLE = False
    # Create dummy classes for graceful degradation
    MetaCognitiveClassifier = None
    ClassificationResult = None
    EnsembleMetaCognitiveEvaluator = None
    create_ml_classifier = None
    create_ensemble_evaluator = None

try:
    from .finetuning import (
        MetaCognitivePrompt,
        TrainingExample,
        MetaCognitiveFinetuner,
        create_metacognitive_finetuner
    )
    FINETUNING_AVAILABLE = True
except ImportError:
    FINETUNING_AVAILABLE = False
    MetaCognitivePrompt = None
    TrainingExample = None
    MetaCognitiveFinetuner = None
    create_metacognitive_finetuner = None

try:
    from .advanced_reasoner import (
        AdvancedMetaCognitiveReasoner,
        QuantitativeAnalysis,
        MultiPerspectiveAnalysis,
        create_advanced_meta_cognitive_reasoner
    )
    ADVANCED_REASONER_AVAILABLE = True
except ImportError:
    ADVANCED_REASONER_AVAILABLE = False
    AdvancedMetaCognitiveReasoner = None
    QuantitativeAnalysis = None
    MultiPerspectiveAnalysis = None
    create_advanced_meta_cognitive_reasoner = None

__all__ = [
    # Monitoring
    "CognitiveMonitor",
    "ProcessState",

    # Data Sufficiency Evaluation
    "DataSufficiency",
    "LimitationType",
    "MetaCognitiveAssessment",
    "DataSufficiencyEvaluator",
    "EnhancedDataSufficiencyEvaluator",
    "create_data_sufficiency_evaluator",
    "create_enhanced_data_sufficiency_evaluator",

    # Hybrid System (NEW in v3.0)
    "HybridMetaCognitiveSystem",
    "HybridAssessment",
    "ConfidenceLevel",
    "create_hybrid_meta_cognitive_system",

    # Advanced Reasoner (NEW in v4.0)
    "AdvancedMetaCognitiveReasoner",
    "QuantitativeAnalysis",
    "MultiPerspectiveAnalysis",
    "create_advanced_meta_cognitive_reasoner",

    # ML Classification
    "MetaCognitiveClassifier",
    "ClassificationResult",
    "EnsembleMetaCognitiveEvaluator",
    "create_ml_classifier",
    "create_ensemble_evaluator",

    # Fine-Tuning
    "MetaCognitivePrompt",
    "TrainingExample",
    "MetaCognitiveFinetuner",
    "create_metacognitive_finetuner",
]
