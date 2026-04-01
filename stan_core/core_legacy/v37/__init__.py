"""
V37 Enhanced System: V36 with Swarm Intelligence & Memory

This package provides the integrated V37CompleteSystem that extends
V36 with swarm intelligence and memory capabilities.

Version: 37.0
"""

from .v37_system import V37CompleteSystem

# Alias for backward compatibility
V37EnhancedSystem = V37CompleteSystem

__version__ = "37.0"

__all__ = ['V37CompleteSystem', 'V37EnhancedSystem']
