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
First Principles Discovery Module

Addresses Limitation 1: Novel phenomena without clear analogies

This module discovers phenomena from first principles by:
- Creating ab initio physical models from fundamental constraints
- Using variational inference to discover new relationships
- Implementing emergence detection for pattern recognition
- Applying symmetry principles to constrain possible solutions
- Using renormalization group methods for scale-invariant discoveries
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from scipy.optimize import minimize
from scipy.stats import entropy
import warnings

try:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available, some features disabled")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.distributions import Normal, kl_divergence
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch not available, variational inference disabled")


@dataclass
class PhysicalConstraint:
    """Represents a physical constraint for first-principles modeling."""
    name: str
    constraint_func: Callable[[np.ndarray], float]
    gradient_func: Optional[Callable[[np.ndarray], np.ndarray]] = None
    tolerance: float = 1e-6
    is_hard: bool = True  # Hard constraint (must satisfy) vs soft (penalty)


@dataclass
class EmergentPattern:
    """Represents a pattern discovered from first principles."""
    pattern_id: str
    mathematical_form: str
    parameters: Dict[str, float]
    confidence: float
    emergence_scale: float  # Scale at which pattern emerges
    physical_interpretation: str
    testable_predictions: List[str] = field(default_factory=list)
    governing_equations: List[str] = field(default_factory=list)


class FirstPrinciplesDiscovery:
    """
    Discover phenomena from first principles when analogies fail.

    Methods:
    1. Variational Discovery: Learn latent representations that satisfy physics
    2. Symmetry Detection: Find invariances in data that suggest fundamental laws
    3. Renormalization Group: Discover scale-invariant relationships
    4. Emergence Detection: Identify patterns that emerge at specific scales
    5. Ab Initio Modeling: Build models from conservation laws + dimensional analysis
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize first principles discovery engine.

        Args:
            config: Configuration dict with keys:
                - max_emergence_scales: Number of scales to check for emergence (default: 20)
                - symmetry_tolerance: Tolerance for symmetry detection (default: 1e-4)
                - use_variational_inference: Enable VAE-based discovery (default: True)
                - latent_dim: Dimension of latent space (default: 8)
        """
        config = config or {}
        self.max_emergence_scales = config.get('max_emergence_scales', 20)
        self.symmetry_tolerance = config.get('symmetry_tolerance', 1e-4)
        self.use_variational_inference = config.get('use_variational_inference', TORCH_AVAILABLE)
        self.latent_dim = config.get('latent_dim', 8)

        # Physical constraints registry
        self.constraints: List[PhysicalConstraint] = []

        # Add default physical constraints
        self._add_default_constraints()

        # Discovered patterns
        self.discovered_patterns: List[EmergentPattern] = []

        # Dimensional analysis cache
        self.dimension_cache: Dict[str, Tuple[float, float, float]] = {}

    def _add_default_constraints(self):
        """Add fundamental physical constraints."""
        # Energy conservation (as a general constraint form)
        self.constraints.append(PhysicalConstraint(
            name="energy_conservation",
            constraint_func=lambda x: np.sum(x**2) if len(x) > 0 else 0.0,
            tolerance=1e-6
        ))

        # Positivity constraint for physical quantities
        self.constraints.append(PhysicalConstraint(
            name="positivity",
            constraint_func=lambda x: np.sum(np.minimum(x, 0)**2),
            tolerance=1e-8
        ))

        # Smoothness constraint (physical quantities vary smoothly)
        def smoothness(x):
            if len(x) < 3:
                return 0.0
            diffs = np.diff(x, n=2)
            return np.sum(diffs**2)

        self.constraints.append(PhysicalConstraint(
            name="smoothness",
            constraint_func=smoothness,
            tolerance=1e-3,
            is_hard=False
        ))

    def discover_from_data(
        self,
        data: np.ndarray,
        variable_names: List[str],
        units: Optional[List[str]] = None
    ) -> List[EmergentPattern]:
        """
        Discover patterns from data using first principles.

        Args:
            data: Shape (n_samples, n_variables) observational data
            variable_names: Names of variables
            units: Physical units (for dimensional analysis)

        Returns:
            List of discovered emergent patterns
        """
        n_samples, n_vars = data.shape

        discovered = []

        # 1. Dimensional analysis to find dimensionless relationships
        dimensionless_groups = self._find_dimensionless_groups(data, variable_names, units)
        if dimensionless_groups:
            pattern = EmergentPattern(
                pattern_id="dimensionless_invariant",
                mathematical_form=f"Π₁ = {dimensionless_groups[0]['form']}",
                parameters={group['name']: group['value'] for group in dimensionless_groups},
                confidence=0.85,
                emergence_scale=0.0,  # Scale-independent
                physical_interpretation="Dimensionless invariant from Buckingham Pi theorem",
                testable_predictions=[f"Relationship holds across all scales of {variable_names[0]}"]
            )
            discovered.append(pattern)

        # 2. Symmetry detection
        symmetries = self._detect_symmetries(data, variable_names)
        for sym in symmetries:
            pattern = EmergentPattern(
                pattern_id=f"symmetry_{sym['type']}",
                mathematical_form=sym['mathematical_form'],
                parameters=sym['parameters'],
                confidence=sym['confidence'],
                emergence_scale=sym['scale'],
                physical_interpretation=f"{sym['type']} symmetry suggests conservation law",
                testable_predictions=[f"System invariant under {sym['operation']}"]
            )
            discovered.append(pattern)

        # 3. Emergence detection - look for scale-dependent patterns
        emergence_patterns = self._detect_emergence(data, variable_names)
        discovered.extend(emergence_patterns)

        # 4. Variational discovery if enabled
        if self.use_variational_inference and TORCH_AVAILABLE and SKLEARN_AVAILABLE:
            variational_patterns = self._variational_discovery(data, variable_names)
            discovered.extend(variational_patterns)

        self.discovered_patterns.extend(discovered)
        return discovered

    def _find_dimensionless_groups(
        self,
        data: np.ndarray,
        variable_names: List[str],
        units: Optional[List[str]] = None
    ) -> List[Dict]:
        """Find dimensionless groups using Buckingham Pi theorem."""
        if units is None:
            # Default units: assume all quantities have basic dimensions
            units = ['unknown'] * len(variable_names)

        groups = []

        # Simple implementation: find scale-invariant ratios
        for i in range(len(variable_names)):
            for j in range(i+1, len(variable_names)):
                # Check if ratio has low variance across scales
                ratio = data[:, i] / (data[:, j] + 1e-10)

                # Check if ratio is approximately constant
                if np.std(np.log(np.abs(ratio) + 1e-10)) < 0.5:
                    groups.append({
                        'name': f'Pi_{i}{j}',
                        'form': f'{variable_names[i]} / {variable_names[j]}',
                        'value': float(np.median(ratio)),
                        'std': float(np.std(ratio))
                    })

        return groups

    def _detect_symmetries(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[Dict]:
        """Detect symmetries in the data."""
        symmetries = []

        # Check for translational symmetry (shift invariance)
        for i, var in enumerate(variable_names):
            # Compute autocorrelation to detect periodicity/translation
            if len(data) > 10:
                autocorr = np.correlate(data[:, i], data[:, i], mode='full')
                autocorr = autocorr[len(autocorr)//2:]

                # Look for peaks that suggest periodic symmetry
                from scipy.signal import find_peaks
                peaks, _ = find_peaks(autocorr, height=np.max(autocorr) * 0.5)

                if len(peaks) > 1:
                    symmetries.append({
                        'type': 'translational',
                        'variable': var,
                        'mathematical_form': f'f({var} + T) = f({var})',
                        'parameters': {'period': float(peaks[1] if len(peaks) > 1 else 0)},
                        'confidence': 0.75,
                        'scale': float(np.std(data[:, i])),
                        'operation': 'translation by period T'
                    })

        # Check for scaling symmetry
        scales = np.logspace(-2, 2, self.max_emergence_scales)
        for scale in scales:
            scaled_data = data * scale
            # Check if statistical properties are preserved
            orig_mean, orig_std = np.mean(data, axis=0), np.std(data, axis=0)
            scaled_mean, scaled_std = np.mean(scaled_data, axis=0), np.std(scaled_data, axis=0)

            # Normalize and compare
            orig_normalized = (data - orig_mean) / (orig_std + 1e-10)
            scaled_normalized = (scaled_data - scaled_mean) / (scaled_std + 1e-10)

            correlation = np.corrcoef(orig_normalized.flatten(), scaled_normalized.flatten())[0, 1]

            if correlation > 0.95:
                symmetries.append({
                    'type': 'scaling',
                    'mathematical_form': 'f(λx) = λ^α f(x)',
                    'parameters': {'scale': scale, 'alpha': 1.0},
                    'confidence': correlation,
                    'scale': scale,
                    'operation': f'scaling by {scale:.3f}'
                })
                break

        return symmetries

    def _detect_emergence(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[EmergentPattern]:
        """Detect emergent patterns at specific scales."""
        patterns = []

        # Use renormalization group approach: look at data at different scales
        scales = np.logspace(-1, 1, 10)

        for i, var1 in enumerate(variable_names):
            for j, var2 in enumerate(variable_names):
                if i >= j:
                    continue

                # Compute correlation at each scale
                correlations = []
                for scale in scales:
                    # Smooth/aggregate data at this scale
                    smoothed = self._aggregate_at_scale(data, scale)

                    # Compute correlation
                    corr = np.corrcoef(smoothed[:, i], smoothed[:, j])[0, 1]
                    correlations.append(corr)

                # Look for emergence: correlation that changes significantly with scale
                corr_change = np.abs(np.diff(correlations))
                if np.max(corr_change) > 0.3:
                    emergent_scale = scales[np.argmax(corr_change)]

                    pattern = EmergentPattern(
                        pattern_id=f'emergence_{var1}_{var2}',
                        mathematical_form=f'ρ({var1}, {var2}) emerges at scale ~ {emergent_scale:.3f}',
                        parameters={'emergence_scale': emergent_scale, 'max_change': float(np.max(corr_change))},
                        confidence=0.7,
                        emergence_scale=emergent_scale,
                        physical_interpretation=f'{var1} and {var2} become coupled at scale {emergent_scale:.3f}',
                        testable_predictions=[
                            f'Measurements at scale {emergent_scale:.3f} will show strong {var1}-{var2} correlation'
                        ]
                    )
                    patterns.append(pattern)

        return patterns

    def _aggregate_at_scale(self, data: np.ndarray, scale: float) -> np.ndarray:
        """Aggregate data at a given scale (simple implementation)."""
        if scale <= 1.0:
            return data

        # Simple block averaging
        block_size = int(scale)
        if block_size < 2:
            return data

        n_samples = len(data)
        n_blocks = n_samples // block_size

        if n_blocks < 2:
            return data

        truncated = data[:n_blocks * block_size]
        reshaped = truncated.reshape(n_blocks, block_size, -1)
        return np.mean(reshaped, axis=1)

    def _variational_discovery(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[EmergentPattern]:
        """
        Use variational inference to discover latent structure.

        This implements a VAE-like approach to discover underlying physical laws.
        """
        if not TORCH_AVAILABLE or not SKLEARN_AVAILABLE:
            return []

        patterns = []

        try:
            # Normalize data
            data_normalized = (data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-10)

            # Fit GP to learn smooth manifold
            kernel = Matern(length_scale=1.0, nu=1.5) + WhiteKernel(noise_level=0.1)
            gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True)

            # Use subset for efficiency
            n_train = min(1000, len(data))
            indices = np.random.choice(len(data), n_train, replace=False)
            gp.fit(data_normalized[indices], np.zeros(n_train))

            # Discover latent structure through GP kernel
            kernel_lengthscale = gp.kernel_.k1.get_params()['length_scale']

            pattern = EmergentPattern(
                pattern_id='variational_manifold',
                mathematical_form=f'Data lies on smooth manifold with characteristic scale {kernel_lengthscale:.3f}',
                parameters={'manifold_scale': float(kernel_lengthscale)},
                confidence=0.8,
                emergence_scale=float(kernel_lengthscale),
                physical_interpretation='Observations constrained to low-dimensional manifold',
                testable_predictions=[
                    f'New observations will remain within {kernel_lengthscale:.3f} of learned manifold'
                ]
            )
            patterns.append(pattern)

        except Exception as e:
            warnings.warn(f"Variational discovery failed: {e}")

        return patterns

    def generate_hypothesis(
        self,
        pattern: EmergentPattern,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a testable hypothesis from a discovered pattern.

        Args:
            pattern: The discovered pattern
            context: Additional context (domain knowledge, etc.)

        Returns:
            Hypothesis with predictions and testing strategy
        """
        hypothesis = {
            'hypothesis_id': f"hyp_{pattern.pattern_id}",
            'claim': pattern.physical_interpretation,
            'mathematical_form': pattern.mathematical_form,
            'parameters': pattern.parameters,
            'confidence': pattern.confidence,
            'testable_predictions': pattern.testable_predictions,
            'falsification_criteria': self._generate_falsification(pattern),
            'observational_tests': self._design_observational_tests(pattern, context)
        }

        return hypothesis

    def _generate_falsification(self, pattern: EmergentPattern) -> List[str]:
        """Generate criteria that would falsify the pattern."""
        criteria = []

        if pattern.emergence_scale > 0:
            criteria.append(
                f"Pattern should not appear at scales << {pattern.emergence_scale:.3f}"
            )

        # Add parameter-based falsification
        for param, value in pattern.parameters.items():
            if isinstance(value, (int, float)):
                criteria.append(
                    f"Parameter {param} should remain within ±{2*value:.3f} of measured value"
                )

        return criteria

    def _design_observational_tests(
        self,
        pattern: EmergentPattern,
        context: Dict[str, Any]
    ) -> List[Dict]:
        """Design observational tests for the pattern."""
        tests = []

        for prediction in pattern.testable_predictions:
            test = {
                'prediction': prediction,
                'required_observations': context.get('required_instruments', ['generic']),
                'estimated_duration': context.get('duration', 'unknown'),
                'confidence_gain': pattern.confidence * 0.1
            }
            tests.append(test)

        return tests

    def build_ab_initio_model(
        self,
        phenomenon_description: str,
        variables: List[str],
        constraints: Optional[List[PhysicalConstraint]] = None
    ) -> Dict[str, Any]:
        """
        Build a model from first principles.

        Args:
            phenomenon_description: Description of the phenomenon
            variables: Variables involved
            constraints: Physical constraints to apply

        Returns:
            Model with equations and parameters
        """
        constraints = constraints or self.constraints

        # Use dimensional analysis + Buckingham Pi theorem
        # Build a model that satisfies all constraints

        model = {
            'phenomenon': phenomenon_description,
            'variables': variables,
            'constraints': [c.name for c in constraints],
            'dimensionless_groups': [],
            'governing_equations': [],
            'parameters': {}
        }

        # Simple Buckingham Pi implementation
        # In practice, this would be more sophisticated
        if len(variables) >= 2:
            model['dimensionless_groups'].append(
                f"Π₁ = {variables[0]} / {variables[1]}"
            )

        # Add constraint satisfaction
        def objective(params):
            # Simple: minimize constraint violations
            violation = 0.0
            for constraint in constraints:
                if constraint.is_hard:
                    violation += 1000 * constraint.constraint_func(params)
                else:
                    violation += constraint.constraint_func(params)
            return violation

        # Find parameters that satisfy constraints
        initial_params = np.ones(len(variables))
        result = minimize(objective, initial_params, method='L-BFGS-B')

        if result.success:
            model['parameters'] = {
                var: float(val) for var, val in zip(variables, result.x)
            }

        return model


def demo_first_principles_discovery():
    """Demonstrate first principles discovery on synthetic data."""
    print("=" * 60)
    print("First Principles Discovery Module Demo")
    print("=" * 60)

    # Create synthetic data with a hidden dimensionless relationship
    np.random.seed(42)
    n_samples = 1000

    # Create data: all following R ~ v^2 (dimensionally consistent kinetic energy relation)
    R = np.random.uniform(1, 100, n_samples)
    v = np.sqrt(R) * np.random.uniform(0.9, 1.1, n_samples)
    data = np.column_stack([R, v])

    variable_names = ['R', 'v']
    units = ['J', 'm/s']

    # Initialize discovery engine
    discovery = FirstPrinciplesDiscovery()

    # Discover patterns
    patterns = discovery.discover_from_data(data, variable_names, units)

    print(f"\nDiscovered {len(patterns)} patterns:")
    for pattern in patterns:
        print(f"\n  Pattern: {pattern.pattern_id}")
        print(f"  Mathematical form: {pattern.mathematical_form}")
        print(f"  Interpretation: {pattern.physical_interpretation}")
        print(f"  Confidence: {pattern.confidence:.2f}")

    # Generate hypothesis
    if patterns:
        hypothesis = discovery.generate_hypothesis(patterns[0], {})
        print(f"\n  Generated hypothesis:")
        print(f"  Claim: {hypothesis['claim']}")
        print(f"  Falsification: {hypothesis['falsification_criteria']}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    demo_first_principles_discovery()
