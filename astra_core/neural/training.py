# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Neural Network Training Infrastructure

Training utilities for neural network models on M1 Max.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from abc import ABC, abstractmethod


class NeuralArchitecture(ABC):
    """Base class for neural architectures."""

    @abstractmethod
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        pass

    @abstractmethod
    def backward(self, grad: np.ndarray) -> Dict[str, np.ndarray]:
        """Backward pass, return gradients."""
        pass

    @abstractmethod
    def get_params(self) -> Dict[str, np.ndarray]:
        """Get model parameters."""
        pass

    @abstractmethod
    def set_params(self, params: Dict[str, np.ndarray]) -> None:
        """Set model parameters."""
        pass


class MultiLayerPerceptron(NeuralArchitecture):
    """
    Simple multi-layer perceptron for M1.

    Uses Metal Accelerate for matrix operations when available.
    """

    def __init__(self,
                 layer_sizes: List[int],
                 activation: str = 'relu'):
        """
        Initialize MLP.

        Args:
            layer_sizes: List of layer sizes (including input and output)
            activation: Activation function ('relu', 'sigmoid', 'tanh')
        """
        self.layer_sizes = layer_sizes
        self.activation = activation

        # Initialize parameters
        self.params = {}
        for i in range(len(layer_sizes) - 1):
            self.params[f'W{i}'] = np.random.randn(
                layer_sizes[i], layer_sizes[i+1]
            ) * 0.01
            self.params[f'b{i}'] = np.zeros(layer_sizes[i+1])

        # Cache for backward pass
        self.cache = {}

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        a = x
        self.cache['a0'] = a

        for i in range(len(self.layer_sizes) - 1):
            W = self.params[f'W{i}']
            b = self.params[f'b{i}']

            z = np.dot(a, W) + b
            self.cache[f'z{i}'] = z

            # Activation
            if i < len(self.layer_sizes) - 2:  # Hidden layers
                if self.activation == 'relu':
                    a = np.maximum(0, z)
                elif self.activation == 'sigmoid':
                    a = 1 / (1 + np.exp(-z))
                elif self.activation == 'tanh':
                    a = np.tanh(z)
            else:  # Output layer (linear for regression)
                a = z

            self.cache[f'a{i+1}'] = a

        return a

    def backward(self, grad: np.ndarray) -> Dict[str, np.ndarray]:
        """Backward pass."""
        gradients = {}

        n_layers = len(self.layer_sizes) - 1

        # Output layer
        i = n_layers - 1
        a_prev = self.cache[f'a{i}']
        z = self.cache[f'z{i}']

        # Gradient of loss w.r.t. z
        dz = grad  # Assuming linear output

        # Gradients
        gradients[f'W{i}'] = np.dot(a_prev.T, dz)
        gradients[f'b{i}'] = np.sum(dz, axis=0)

        # Backpropagate
        da = np.dot(dz, self.params[f'W{i}'].T)

        # Hidden layers
        for i in range(n_layers - 2, -1, -1):
            a_prev = self.cache[f'a{i}']
            z = self.cache[f'z{i}']

            # Activation gradient
            if self.activation == 'relu':
                dz = da * (z > 0)
            elif self.activation == 'sigmoid':
                sig = 1 / (1 + np.exp(-z))
                dz = da * sig * (1 - sig)
            elif self.activation == 'tanh':
                tanh = np.tanh(z)
                dz = da * (1 - tanh**2)

            # Gradients
            gradients[f'W{i}'] = np.dot(a_prev.T, dz)
            gradients[f'b{i}'] = np.sum(dz, axis=0)

            # Backpropagate
            da = np.dot(dz, self.params[f'W{i}'].T)

        return gradients

    def get_params(self) -> Dict[str, np.ndarray]:
        """Get model parameters."""
        return self.params.copy()

    def set_params(self, params: Dict[str, np.ndarray]) -> None:
        """Set model parameters."""
        self.params = params.copy()


class Trainer:
    """
    Neural network trainer.

    Supports:
    - SGD and Adam optimizers
    - Loss functions (MSE, cross-entropy)
    - Training loop with validation
    """

    def __init__(self,
                 model: NeuralArchitecture,
                 optimizer: str = 'adam',
                 learning_rate: float = 0.001):
        self.model = model
        self.optimizer = optimizer
        self.learning_rate = learning_rate

        # Adam optimizer state
        self.m = {}  # First moment
        self.v = {}  # Second moment
        self.t = 0  # Timestep

    def compute_loss(self,
                     y_pred: np.ndarray,
                     y_true: np.ndarray,
                     loss_type: str = 'mse') -> float:
        """Compute loss."""
        if loss_type == 'mse':
            return np.mean((y_pred - y_true)**2)
        elif loss_type == 'mae':
            return np.mean(np.abs(y_pred - y_true))
        elif loss_type == 'binary_crossentropy':
            # Avoid log(0)
            y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
            return -np.mean(y_true * np.log(y_pred) +
                          (1 - y_true) * np.log(1 - y_pred))
        else:
            raise ValueError(f"Unknown loss type: {loss_type}")

    def compute_gradient(self,
                        y_pred: np.ndarray,
                        y_true: np.ndarray,
                        loss_type: str = 'mse') -> np.ndarray:
        """Compute gradient of loss w.r.t. predictions."""
        if loss_type == 'mse':
            return 2 * (y_pred - y_true) / y_pred.size
        elif loss_type == 'binary_crossentropy':
            y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
            return (y_pred - y_true) / y_pred.size
        else:
            raise ValueError(f"Unknown loss type: {loss_type}")

    def train_step(self,
                   x: np.ndarray,
                   y: np.ndarray,
                   loss_type: str = 'mse') -> Dict[str, float]:
        """
        Single training step.

        Args:
            x: Input data
            y: Target data
            loss_type: Type of loss function

        Returns:
            Dict with loss and metrics
        """
        # Forward pass
        y_pred = self.model.forward(x)

        # Compute loss
        loss = self.compute_loss(y_pred, y, loss_type)

        # Backward pass
        grad = self.compute_gradient(y_pred, y, loss_type)
        gradients = self.model.backward(grad)

        # Update parameters
        self._update_params(gradients)

        return {'loss': loss}

    def _update_params(self, gradients: Dict[str, np.ndarray]) -> None:
        """Update model parameters."""
        if self.optimizer == 'sgd':
            for key, grad in gradients.items():
                if key in self.model.params:
                    self.model.params[key] -= self.learning_rate * grad

        elif self.optimizer == 'adam':
            # Adam optimizer
            beta1 = 0.9
            beta2 = 0.999
            epsilon = 1e-8

            self.t += 1

            for key, grad in gradients.items():
                if key not in self.model.params:
                    continue

                if key not in self.m:
                    self.m[key] = np.zeros_like(grad)
                    self.v[key] = np.zeros_like(grad)

                # Update biased first and second moment estimates
                self.m[key] = beta1 * self.m[key] + (1 - beta1) * grad
                self.v[key] = beta2 * self.v[key] + (1 - beta2) * (grad**2)

                # Compute bias-corrected estimates
                m_hat = self.m[key] / (1 - beta1**self.t)
                v_hat = self.v[key] / (1 - beta2**self.t)

                # Update parameters
                self.model.params[key] -= self.learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)

    def train(self,
             x_train: np.ndarray,
             y_train: np.ndarray,
             x_val: Optional[np.ndarray] = None,
             y_val: Optional[np.ndarray] = None,
             epochs: int = 100,
             batch_size: int = 32,
             loss_type: str = 'mse',
             verbose: bool = True) -> Dict[str, List[float]]:
        """
        Training loop.

        Args:
            x_train: Training inputs
            y_train: Training targets
            x_val: Validation inputs
            y_val: Validation targets
            epochs: Number of epochs
            batch_size: Batch size
            loss_type: Loss function type
            verbose: Print progress

        Returns:
            Training history
        """
        history = {'train_loss': [], 'val_loss': []}

        n_samples = len(x_train)

        for epoch in range(epochs):
            # Shuffle training data
            indices = np.random.permutation(n_samples)

            epoch_loss = 0
            n_batches = 0

            # Mini-batch training
            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch_indices = indices[start:end]

                x_batch = x_train[batch_indices]
                y_batch = y_train[batch_indices]

                result = self.train_step(x_batch, y_batch, loss_type)
                epoch_loss += result['loss']
                n_batches += 1

            epoch_loss /= n_batches
            history['train_loss'].append(epoch_loss)

            # Validation
            if x_val is not None and y_val is not None:
                y_pred = self.model.forward(x_val)
                val_loss = self.compute_loss(y_pred, y_val, loss_type)
                history['val_loss'].append(val_loss)

                if verbose and epoch % 10 == 0:
                    print(f"Epoch {epoch}: train_loss={epoch_loss:.4f}, "
                          f"val_loss={val_loss:.4f}")
            else:
                if verbose and epoch % 10 == 0:
                    print(f"Epoch {epoch}: train_loss={epoch_loss:.4f}")

        return history


class ModelCheckpoint:
    """Save and load model checkpoints."""

    @staticmethod
    def save(model: NeuralArchitecture,
             filepath: str,
             metadata: Optional[Dict] = None) -> None:
        """Save model checkpoint."""
        checkpoint = {
            'params': model.get_params(),
            'architecture': model.__class__.__name__,
            'config': {
                'layer_sizes': model.layer_sizes,
                'activation': model.activation
            },
            'metadata': metadata or {}
        }

        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)

    @staticmethod
    def load(filepath: str) -> Tuple[NeuralArchitecture, Dict]:
        """Load model checkpoint."""
        import pickle

        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)

        # Recreate model
        config = checkpoint['config']
        model = MultiLayerPerceptron(
            layer_sizes=config['layer_sizes'],
            activation=config['activation']
        )
        model.set_params(checkpoint['params'])

        return model, checkpoint.get('metadata', {})



def bridge_neural_symbolic(neural_output: Dict[str, Any],
                          symbolic_knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bridge neural network outputs with symbolic knowledge.

    Args:
        neural_output: Raw neural network predictions
        symbolic_knowledge: Symbolic rules and constraints

    Returns:
        Bridged prediction with symbolic consistency
    """
    import numpy as np

    prediction = neural_output.get('prediction')
    confidence = neural_output.get('confidence', 0.5)

    # Apply symbolic constraints
    constraints = symbolic_knowledge.get('constraints', [])

    adjusted_prediction = prediction
    constraint_violations = []

    for constraint in constraints:
        constraint_type = constraint.get('type')

        if constraint_type == 'monotonic':
            x = neural_output.get('input_value', 0)
            if constraint.get('direction') == 'increasing':
                expected = constraint.get('reference', 0)
                if prediction < expected and x > expected:
                    adjusted_prediction = expected
                    constraint_violations.append('monotonic')

        elif constraint_type == 'bounds':
            lower = constraint.get('lower', -float('inf'))
            upper = constraint.get('upper', float('inf'))

            if prediction < lower:
                adjusted_prediction = lower
                constraint_violations.append('lower_bound')
            elif prediction > upper:
                adjusted_prediction = upper
                constraint_violations.append('upper_bound')

    # Adjust confidence based on violations
    if constraint_violations:
        confidence *= 0.8

    return {
        'prediction': adjusted_prediction,
        'confidence': confidence,
        'constraint_violations': constraint_violations,
        'original_prediction': prediction
    }



def pc_algorithm_discover(data: Dict[str, np.ndarray],
                         alpha: float = 0.05,
                         max_depth: int = 3) -> Dict[str, Any]:
    """
    Discover causal graph using PC algorithm (constraint-based).

    Builds skeleton graph by testing conditional independence.

    Args:
        data: Dictionary mapping variable names to data arrays
        alpha: Significance level for independence tests
        max_depth: Maximum depth for conditional independence tests

    Returns:
        Dictionary with adjacency matrix and separation sets
    """
    import numpy as np
    from scipy.stats import pearsonr

    variables = list(data.keys())
    n_vars = len(variables)

    # Initialize fully connected graph
    adjacency = np.ones((n_vars, n_vars), dtype=int) - np.eye(n_vars, dtype=int)

    # Separation sets
    sep_sets = {frozenset({i, j}): set() for i in range(n_vars) for j in range(n_vars) if i != j}

    # Phase 1: Skeleton discovery
    for depth in range(max_depth + 1):
        for i in range(n_vars):
            for j in range(adjacency[i]):
                if i >= j:
                    continue

                # Find neighbors of i (excluding j)
                neighbors_i = [k for k in range(n_vars) if adjacency[i, k] and k != j]

                if len(neighbors_i) >= depth:
                    # Test all subsets of size depth
                    from itertools import combinations

                    for subset in combinations(neighbors_i, depth):
                        # Test if i independent of j given subset
                        x = data[variables[i]]
                        y = data[variables[j]]

                        # Partial correlation
                        if len(subset) == 0:
                            corr, p_val = pearsonr(x, y)
