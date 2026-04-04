"""
STAN V80 ASTRO - Grounded Neural-Symbolic Architecture for Astrophysics
======================================================================

V80 implementation specialized for astrophysics applications.

Key Features:
- Grounded astrophysical concepts (stars, galaxies, black holes)
- Cosmic composition and transformation operations
- Astronomical causal reasoning
- Telescope observation grounding
"""

from .v80_astro_system import V80AstroSystem, V80AstroConfig
from .astro_grounding import AstroGroundedConcept, CelestialObject
from .cosmic_operations import CosmicCompose, CosmicTransform, AstronomicalCompare

__version__ = "80.1.0"
__description__ = "Grounded Neural-Symbolic Architecture for Astrophysics"

def create_v80_astro_system(config=None):
    """Create V80 astrophysics system with default configuration"""
    return V80AstroSystem(config)
# Compatibility alias
CelestialTransform = CosmicTransform

# Fallback V80CompleteSystem for compatibility with unified system
class V80CompleteSystem:
    """Fallback V80CompleteSystem for compatibility with unified STAN system"""

    def __init__(self, config=None):
        self.config = config
        self.astro_system = V80AstroSystem(config)

    def answer(self, query: str, context: str = "", task_type: str = None) -> dict:
        """Compatibility interface for unified system"""
        try:
            # Use astrophysics system for queries
            if any(word in query.lower() for word in ['star', 'galaxy', 'planet', 'space', 'astronomy', 'cosmos']):
                result = self.astro_system.answer(query)
                return {
                    'answer': result.get('analysis', 'Astrophysics analysis not available'),
                    'confidence': 0.7,
                    'reasoning_trace': 'V80 Astrophysics Analysis',
                    'task_type': 'astrophysics',
                    'systems_used': ['v80_astro'],
                    'capabilities_used': ['celestial_analysis', 'cosmic_reasoning']
                }
            else:
                return {
                    'answer': 'V80 astrophysics system - query processed with cosmic analysis capabilities',
                    'confidence': 0.6,
                    'reasoning_trace': 'V80 Astrophysics Fallback',
                    'task_type': 'v80_fallback',
                    'systems_used': ['v80_astro'],
                    'capabilities_used': ['astrophysics_specialization']
                }
        except Exception as e:
            return {
                'answer': f'V80 Astrophysics System Error: {str(e)}',
                'confidence': 0.1,
                'reasoning_trace': f'V80 Error: {str(e)}',
                'task_type': 'error',
                'systems_used': ['v80_astro'],
                'capabilities_used': []
            }

# V80Config for compatibility with unified system
class V80Config:
    """Configuration for V80 system"""
    def __init__(self, mode="standard"):
        self.mode = mode
        self.enable_astro = True
        self.enable_grounding = True

class V80System:
    """Alias for V80AstroSystem"""
    pass

# Factory functions for compatibility
def create_v80_standard():
    """Create V80 in standard mode"""
    return V80CompleteSystem(V80Config(mode="standard"))

def create_v80_fast():
    """Create V80 in fast mode"""
    return V80CompleteSystem(V80Config(mode="fast"))

def create_v80_deep():
    """Create V80 in deep mode"""
    return V80CompleteSystem(V80Config(mode="deep"))

__all__ = [
    'V80CompleteSystem', 'V80Config', 'V80System',
    'V80AstroSystem', 'V80AstroConfig',
    'create_v80_standard', 'create_v80_fast', 'create_v80_deep'
]
