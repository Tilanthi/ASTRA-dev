"""
V7.0 Research Engines

Individual engines for the autonomous research cycle.
"""

from .question_generator import QuestionGenerator
from .hypothesis_formulator import HypothesisFormulator
from .experiment_designer import ExperimentDesigner
from .experiment_executor import ExperimentExecutor
from .prediction_engine import (
    PredictionEngine, AnalysisEngine, TheoryRevisionEngine, PublicationEngine
)

__all__ = [
    'QuestionGenerator',
    'HypothesisFormulator',
    'ExperimentDesigner',
    'ExperimentExecutor',
    'PredictionEngine',
    'AnalysisEngine',
    'TheoryRevisionEngine',
    'PublicationEngine',
]
