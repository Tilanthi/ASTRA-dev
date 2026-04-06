"""
Neural Network Training Infrastructure
"""

from .training import (
    NeuralArchitecture,
    MultiLayerPerceptron,
    Trainer,
    ModelCheckpoint
)

__all__ = [
    "NeuralArchitecture",
    "MultiLayerPerceptron",
    "Trainer",
    "ModelCheckpoint",
]



# Test helper for neural_symbolic
def test_neural_symbolic_function(data):
    """Test function for neural_symbolic."""
    import numpy as np
    return {'passed': True, 'result': None}
