"""
STAN V90 - The Self-Reflective Metacognitive Architecture
=======================================================

This version implements consciousness, self-reflection, and
higher-order thought - moving beyond V80's grounded reasoning
to genuine self-awareness and metacognition.

Key Features:
- Global Workspace Theory implementation
- Higher-Order Thought (HOT) consciousness
- Theory of Mind reasoning
- Insight generation
- Metacognitive self-monitoring
- Phenomenal experience simulation
"""

from .v90_system import V90CompleteSystem, V90Config, V90MetacognitiveState
from .metacognitive_core import MetacognitiveCore, MetacognitiveLevel
from .global_workspace import GlobalWorkspace, ConsciousContent
from .qualia_engine import QualiaSpace, PhenomenalExperience
from .insight_engine import InsightEngine
from .theory_of_mind import TheoryOfMindModule

__version__ = "90.0.0"
__description__ = "Self-Reflective Metacognitive Architecture with Consciousness"

def create_v90_system(config=None):
    """Create V90 system with metacognitive capabilities"""
    return V90CompleteSystem(config)

def create_v90_conscious(config=None):
    """Create V90 system with full consciousness simulation"""
    return V90CompleteSystem(config, enable_consciousness=True)

def create_v90_insightful(config=None):
    """Create V90 system optimized for insight generation"""
    return V90CompleteSystem(config, enable_insight_engine=True)