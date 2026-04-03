"""
V7.0 Autonomous Research Scientist

The next transformative leap in ASTRA's evolution - an autonomous research
system capable of conducting the entire scientific research cycle:

Question → Hypothesis → Design → Experiment → Analysis → Theory → Publication

This represents a paradigm shift from tool to autonomous scientist.
"""

from .v7_autonomous_scientist import (
    V7AutonomousScientist,
    create_v7_scientist,
    ResearchCycle,
    ResearchQuestion,
    Hypothesis,
    Experiment,
    ResearchResult,
    Publication
)

from .engines.question_generator import (
    QuestionGenerator,
    QuestionType,
    QuestionImportance
)

from .engines.hypothesis_formulator import (
    HypothesisFormulator,
    HypothesisType,
    HypothesisStatus
)

from .engines.experiment_designer import (
    ExperimentDesigner,
    ExperimentType,
    DesignParameters
)

from .engines.experiment_executor import (
    ExperimentExecutor,
    ExecutionResult,
    DataSource
)

from .engines.prediction_engine import (
    PredictionEngine,
    PredictionType,
    PredictionConfidence
)

from .engines.prediction_engine import (
    PredictionEngine, AnalysisEngine, TheoryRevisionEngine, PublicationEngine,
    PredictionType, PredictionConfidence, AnalysisType,
    CausalInferenceResult, RevisionType, TheoryStatus,
    PaperStructure, FigureType
)

__all__ = [
    # Main system
    'V7AutonomousScientist',
    'create_v7_scientist',
    'ResearchCycle',
    'ResearchQuestion',
    'Hypothesis',
    'Experiment',
    'ResearchResult',
    'Publication',

    # Engines
    'QuestionGenerator',
    'QuestionType',
    'QuestionImportance',
    'HypothesisFormulator',
    'HypothesisType',
    'HypothesisStatus',
    'ExperimentDesigner',
    'ExperimentType',
    'DesignParameters',
    'ExperimentExecutor',
    'ExecutionResult',
    'DataSource',
    'PredictionEngine',
    'PredictionType',
    'PredictionConfidence',
    'AnalysisEngine',
    'AnalysisType',
    'CausalInferenceResult',
    'TheoryRevisionEngine',
    'RevisionType',
    'TheoryStatus',
    'PublicationEngine',
    'PaperStructure',
    'FigureType',
]
