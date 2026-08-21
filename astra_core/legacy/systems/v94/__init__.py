"""
STAN V94: Embodied Learning and Grounded Cognition Architecture (ASTRO Version)

This module implements the paradigm shift from simulated intelligence to experienced intelligence
through embodied learning, sensorimotor integration, and grounded cognition.
Enhanced for astrophysics applications with cosmic-scale embodied understanding.
"""

from .embodied_learning_engine import EmbodiedLearningEngine
from .developmental_learning import DevelopmentalLearning, PlayfulExplorer
from .common_sense_engine import CommonSenseEngine, PhysicsIntuitionModule
from .v94_complete import V94CompleteSystem, V94Config
from .astro_embodied_integration import AstroEmbodiedIntegrator

# sensorimotor_system.py and language_grounding.py have baselined syntax errors
# (tests/known_broken_syntax.txt); quarantined so the rest of v94 stays importable.
try:
    from .sensorimotor_system import SensorimotorInterface, WorldAction, Experience
except (ImportError, SyntaxError):
    SensorimotorInterface = None
    WorldAction = None
    Experience = None

try:
    from .language_grounding import LanguageGroundingEngine, ConceptGroundingEngine
except (ImportError, SyntaxError):
    LanguageGroundingEngine = None
    ConceptGroundingEngine = None

__all__ = [
    'EmbodiedLearningEngine',
    'SensorimotorInterface',
    'WorldAction',
    'Experience',
    'DevelopmentalLearning',
    'PlayfulExplorer',
    'CommonSenseEngine',
    'PhysicsIntuitionModule',
    'LanguageGroundingEngine',
    'ConceptGroundingEngine',
    'V94CompleteSystem',
    'V94Config',
    'AstroEmbodiedIntegrator'
]