"""
Automatic Constraint Discovery Module

Addresses Limitation 3: Pre-specified constraints for novel situations

This module automatically discovers constraints from data:
- Symbolic regression to find conservation laws
- Gauge symmetry detection
- Scale-invariance analysis
- Variational principle discovery
- Lagrangian inference
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from scipy.optimize import minimize
from scipy.integrate import odeint
from scipy.stats import linregress
import warnings

try:
    from sklearn.linear_model import Ridge, Lasso
    from sklearn.preprocessing import PolynomialFeatures
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available")


@dataclass
class DiscoveredConstraint:
    """Represents a constraint discovered from data."""
    constraint_id: str
    constraint_type: str  # 'conservation', 'symmetry', 'scale_invariance', etc.
    mathematical_form: str
    parameters: Dict[str, float]
    confidence: float
    error_bounds: Dict[str, Tuple[float, float]]
    domain_of_validity: Tuple[float, float]  # Range where constraint holds
    violations: List[int] = field(default_factory=list)  # Indices where violated


@dataclass
class ConservationLaw:
    """Represents a discovered conservation law."""
    conserved_quantity: str
    expression: str
    drift_rate: float  # How much it varies (should be ~0)
    confidence: float
    time_invariance: float  # Is it conserved over time?
    symmetry: Optional[str] = None  # Associated symmetry (Noether's theorem)


class AutomaticConstraintDiscovery:
    """
    Automatically discover physical constraints from data.

    Methods:
    1. Conservation Law Discovery: Find quantities that remain constant
    2. Symmetry Detection: Identify transformation invariants
    3. Scale Analysis: Find power-law relationships
    4. Lagrangian Inference: Discover action principles
    5. Gauge Symmetry Detection: Find local symmetries
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize automatic constraint discovery engine.

        Args:
            config: Configuration dict with keys:
                - conservation_tolerance: Drift allowed for conservation (default: 1e-3)
                - symmetry_tolerance: Tolerance for symmetry detection (default: 1e-4)
                - min_confidence: Minimum confidence for reported constraints (default: 0.7)
                - max_polynomial_degree: For symbolic regression (default: 3)
        """
        config = config or {}
        self.conservation_tolerance = config.get('conservation_tolerance', 1e-3)
        self.symmetry_tolerance = config.get('symmetry_tolerance', 1e-4)
        self.min_confidence = config.get('min_confidence', 0.7)
        self.max_polynomial_degree = config.get('max_polynomial_degree', 3)

        self.discovered_constraints: List[DiscoveredConstraint] = []
        self.conservation_laws: List[ConservationLaw] = []

    def discover_constraints(
        self,
        data: np.ndarray,
        variable_names: List[str],
        time_index: Optional[int] = None,
        derivatives: Optional[np.ndarray] = None
    ) -> List[DiscoveredConstraint]:
        """
        Discover all types of constraints in the data.

        Args:
            data: Shape (n_samples, n_variables) observational data
            variable_names: Names of variables
            time_index: Which variable is time (if any)
            derivatives: Pre-computed derivatives [d/dt, d²/dt², ...]

        Returns:
            List of discovered constraints
        """
        constraints = []

        # 1. Conservation law discovery
        if time_index is not None:
            conservation_laws = self._discover_conservation_laws(
                data, variable_names, time_index
            )
            constraints.extend(conservation_laws)

        # 2. Scale-invariance discovery (power laws)
        scale_constraints = self._discover_scale_invariance(data, variable_names)
        constraints.extend(scale_constraints)

        # 3. Symmetry detection
        symmetry_constraints = self._detect_symmetries(data, variable_names)
        constraints.extend(symmetry_constraints)

        # 4. Relation discovery (correlations, functional dependencies)
        relation_constraints = self._discover_relations(data, variable_names)
        constraints.extend(relation_constraints)

        # Filter by confidence
        constraints = [c for c in constraints if c.confidence >= self.min_confidence]

        self.discovered_constraints.extend(constraints)
        return constraints

    def _discover_conservation_laws(
        self,
        data: np.ndarray,
        variable_names: List[str],
        time_index: int
    ) -> List[DiscoveredConstraint]:
        """Discover quantities that are conserved over time."""
        constraints = []

        # Time series data
        time_data = data[:, time_index]
        variable_data = np.delete(data, time_index, axis=1)
        var_names = [v for i, v in enumerate(variable_names) if i != time_index]

        # Check each variable for conservation
        for i, var_name in enumerate(var_names):
            var_values = variable_data[:, i]

            # Skip if no variation in time
            if np.std(time_data) < 1e-10:
                continue

            # Compute drift rate
            # Fit linear trend: should be flat for conserved quantity
            slope, intercept, r_value, p_value, std_err = linregress(time_data, var_values)

            # Check if drift is within tolerance
            relative_drift = abs(slope) / (np.std(var_values) + 1e-10)

            if relative_drift < self.conservation_tolerance:
                # Found conserved quantity
                confidence = 1.0 - relative_drift / self.conservation_tolerance

                constraint = DiscoveredConstraint(
                    constraint_id=f'conserved_{var_name}',
                    constraint_type='conservation',
                    mathematical_form=f'd{var_name}/dt ≈ 0',
                    parameters={'mean': float(np.mean(var_values)), 'std': float(np.std(var_values))},
                    confidence=float(confidence),
                    error_bounds={
                        'lower': float(np.mean(var_values) - 2*np.std(var_values)),
                        'upper': float(np.mean(var_values) + 2*np.std(var_values))
                    },
                    domain_of_validity=(float(np.min(time_data)), float(np.max(time_data)))
                )
                constraints.append(constraint)

        # Look for combinations of variables that are conserved
        # Simple: check linear combinations
        for i, var1_name in enumerate(var_names):
            for j, var2_name in enumerate(var_names):
                if i >= j:
                    continue

                # Check if sum or difference is conserved
                for coeff1 in [1, -1]:
                    for coeff2 in [1, -1]:
                        combination = coeff1 * variable_data[:, i] + coeff2 * variable_data[:, j]

                        slope, _, _, _, _ = linregress(time_data, combination)
                        relative_drift = abs(slope) / (np.std(combination) + 1e-10)

                        if relative_drift < self.conservation_tolerance:
                            confidence = 1.0 - relative_drift / self.conservation_tolerance

                            operation = '+' if coeff2 > 0 else '-'
                            constraint = DiscoveredConstraint(
                                constraint_id=f'conserved_{var1_name}_{operation}{var2_name}',
                                constraint_type='conservation',
                                mathematical_form=f'd({var1_name} {operation} {var2_name})/dt ≈ 0',
                                parameters={
                                    'coeff1': float(coeff1),
                                    'coeff2': float(coeff2)
                                },
                                confidence=float(confidence),
                                error_bounds={
                                    'mean': float(np.mean(combination)),
                                    'std': float(np.std(combination))
                                },
                                domain_of_validity=(float(np.min(time_data)), float(np.max(time_data)))
                            )
                            constraints.append(constraint)

        return constraints

    def _discover_scale_invariance(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[DiscoveredConstraint]:
        """Discover scale-invariant relationships (power laws)."""
        constraints = []

        # Check for power-law relationships: y ∝ x^α
        for i, var1_name in enumerate(variable_names):
            for j, var2_name in enumerate(variable_names):
                if i == j:
                    continue

                x = data[:, i] + 1e-10  # Avoid log(0)
                y = data[:, j] + 1e-10

                # Take logs
                log_x = np.log(np.abs(x))
                log_y = np.log(np.abs(y))

                # Check if points fall on line in log-log space
                mask = (np.isfinite(log_x) & np.isfinite(log_y))
                if np.sum(mask) < 10:
                    continue

                slope, intercept, r_value, p_value, std_err = linregress(log_x[mask], log_y[mask])

                # Check for good power law fit
                if abs(r_value) > 0.9 and p_value < 0.01:
                    exponent = slope
                    # Check if exponent is close to simple ratio (1/2, 2, 3, etc.)
                    simple_exponents = {0.5: '1/2', 1: '1', 2: '2', 3: '3', -1: '-1', -2: '-2'}
                    closest_exp = min(simple_exponents.keys(), key=lambda x: abs(x - exponent))

                    if abs(exponent - closest_exp) < 0.2:
                        exponent_str = simple_exponents[closest_exp]
                        confidence = abs(r_value)
                    else:
                        exponent_str = f'{exponent:.2f}'
                        confidence = abs(r_value) * 0.8

                    constraint = DiscoveredConstraint(
                        constraint_id=f'scale_invariant_{var1_name}_{var2_name}',
                        constraint_type='scale_invariance',
                        mathematical_form=f'{var2_name} ∝ {var1_name}^{exponent_str}',
                        parameters={'exponent': float(exponent), 'correlation': float(r_value)},
                        confidence=float(confidence),
                        error_bounds={
                            'exponent_lower': float(exponent - 2*std_err),
                            'exponent_upper': float(exponent + 2*std_err)
                        },
                        domain_of_validity=(float(np.min(x)), float(np.max(x)))
                    )
                    constraints.append(constraint)

        return constraints

    def _detect_symmetries(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[DiscoveredConstraint]:
        """Detect symmetries in the data."""
        constraints = []

        # Check for translational symmetry
        for i, var_name in enumerate(variable_names):
            var_data = data[:, i]

            # Check autocorrelation
            if len(var_data) > 20:
                autocorr = np.correlate(var_data - np.mean(var_data), var_data - np.mean(var_data), mode='full')
                autocorr = autocorr[len(autocorr)//2:]

                # Normalize
                autocorr = autocorr / (autocorr[0] + 1e-10)

                # Look for peaks indicating periodicity/translational symmetry
                from scipy.signal import find_peaks
                peaks, properties = find_peaks(autocorr, height=0.5, distance=5)

                if len(peaks) >= 2:
                    # Check if peaks are equally spaced
                    if len(peaks) >= 3:
                        spacings = np.diff(peaks)
                        if np.std(spacings) / np.mean(spacings) < 0.2:
                            # Found translational symmetry
                            period = float(np.mean(spacings))
                            confidence = 1.0 - np.std(spacings) / np.mean(spacings)

                            constraint = DiscoveredConstraint(
                                constraint_id=f'translational_symmetry_{var_name}',
                                constraint_type='symmetry',
                                mathematical_form=f'{var_name}(t + T) = {var_name}(t), T = {period:.1f}',
                                parameters={'period': period, 'spacings_cv': float(np.std(spacings) / np.mean(spacings))},
                                confidence=float(confidence),
                                error_bounds={'period': period},
                                domain_of_validity=(0.0, float(len(var_data)))
                            )
                            constraints.append(constraint)

        # Check for scaling symmetry (already in scale_invariance)

        return constraints

    def _discover_relations(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[DiscoveredConstraint]:
        """Discover functional relationships between variables."""
        constraints = []

        if not SKLEARN_AVAILABLE:
            return constraints

        # Use polynomial regression to discover relationships
        for i, var1_name in enumerate(variable_names):
            for j, var2_name in enumerate(variable_names):
                if i == j:
                    continue

                x = data[:, i:i+1]
                y = data[:, j]

                # Try polynomial fits
                for degree in range(1, self.max_polynomial_degree + 1):
                    poly = PolynomialFeatures(degree=degree)
                    x_poly = poly.fit_transform(x)

                    model = Ridge(alpha=1.0)
                    model.fit(x_poly, y)

                    score = model.score(x_poly, y)

                    if score > 0.9:  # Strong relationship
                        # Extract equation
                        coeffs = model.coef_
                        intercept = model.intercept_

                        # Build equation string
                        terms = []
                        for power, coeff in enumerate(coeffs):
                            if abs(coeff) > 1e-6:
                                if power == 0:
                                    terms.append(f"{coeff:.3f}")
                                elif power == 1:
                                    terms.append(f"{coeff:.3f}*{var1_name}")
                                else:
                                    terms.append(f"{coeff:.3f}*{var1_name}^{power}")

                        equation = f"{var2_name} = {' + '.join(terms)}"

                        constraint = DiscoveredConstraint(
                            constraint_id=f'relation_{var1_name}_{var2_name}_deg{degree}',
                            constraint_type='functional_relation',
                            mathematical_form=equation,
                            parameters={'r_squared': float(score), 'degree': degree},
                            confidence=float(score),
                            error_bounds={'residual_std': float(np.sqrt(1 - score))},
                            domain_of_validity=(float(np.min(x)), float(np.max(x)))
                        )
                        constraints.append(constraint)
                        break  # Use best degree

        return constraints

    def infer_lagrangian(
        self,
        coordinates: np.ndarray,
        velocities: np.ndarray,
        accelerations: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Infer Lagrangian from trajectory data.

        Uses variational principle to discover L = T - V

        Args:
            coordinates: Shape (n_timesteps, n_dof) positions
            velocities: Shape (n_timesteps, n_dof) velocities
            accelerations: Shape (n_timesteps, n_dof) accelerations

        Returns:
            Dictionary with Lagrangian components
        """
        n_dof = coordinates.shape[1]

        # Assume kinetic energy T = 0.5 * m * v^2
        # Need to discover potential V

        lagrangian_info = {
            'kinetic_energy': None,
            'potential_energy': None,
            'conserved_quantities': [],
            'equations_of_motion': []
        }

        # Estimate kinetic energy
        velocities_squared = np.sum(velocities**2, axis=1)
        # Assume unit mass for simplicity
        kinetic_energy = 0.5 * velocities_squared

        lagrangian_info['kinetic_energy'] = {
            'form': 'T = 0.5 * v^2',
            'values': kinetic_energy
        }

        # Try to discover potential energy from accelerations
        # From Euler-Lagrange: d/dt(∂L/∂v̇) - ∂L/∂x = 0
        # If L = T - V(x): a = -∂V/∂x

        if accelerations is not None:
            # Estimate potential gradient
            # a_i = -∂V/∂x_i

            # Integrate to get V (up to constant)
            potential = np.zeros(len(coordinates))

            for i in range(1, len(coordinates)):
                dx = coordinates[i] - coordinates[i-1]
                da = accelerations[i] + accelerations[i-1]

                # Work done = -F·dx = a·dx (F = ma, assume m=1)
                work = -np.sum(da * dx)

                potential[i] = potential[i-1] + work

            # Remove offset
            potential -= np.min(potential)

            lagrangian_info['potential_energy'] = {
                'form': 'V(x) inferred from trajectories',
                'values': potential
            }

        return lagrangian_info

    def detect_gauge_symmetry(
        self,
        field_data: np.ndarray,
        coordinates: np.ndarray
    ) -> List[DiscoveredConstraint]:
        """
        Detect gauge symmetries in field data.

        Gauge symmetry: physical quantities invariant under local transformations.

        Args:
            field_data: Shape (n_samples, n_components) field values
            coordinates: Shape (n_samples, n_dims) spatial coordinates

        Returns:
            List of gauge symmetry constraints
        """
        constraints = []

        # Simple check: are there transformations that leave data invariant?
        # This is complex; for now, check for phase invariance

        # For complex field data, check phase rotation invariance
        if field_data.shape[1] >= 2:  # Need at least real + imaginary
            # Compute magnitude
            magnitude = np.sqrt(field_data[:, 0]**2 + field_data[:, 1]**2)

            # Check if magnitude is conserved (gauge invariance)
            magnitude_std = np.std(magnitude) / (np.mean(magnitude) + 1e-10)

            if magnitude_std < self.conservation_tolerance:
                constraint = DiscoveredConstraint(
                    constraint_id='gauge_symmetry_phase',
                    constraint_type='gauge_symmetry',
                    mathematical_form='|ψ| = gauge_invariant',
                    parameters={'phase_invariance': True},
                    confidence=1.0 - magnitude_std,
                    error_bounds={},
                    domain_of_validity=(0.0, float(len(field_data)))
                )
                constraints.append(constraint)

        return constraints


def demo_constraint_discovery():
    """Demonstrate automatic constraint discovery."""
    print("=" * 60)
    print("Automatic Constraint Discovery Module Demo")
    print("=" * 60)

    # Create synthetic data with a conserved quantity
    np.random.seed(42)
    n_samples = 1000
    time = np.linspace(0, 10, n_samples)

    # Conserved quantity: E = T + V = constant
    position = np.sin(time) + np.random.normal(0, 0.1, n_samples)
    velocity = np.cos(time) + np.random.normal(0, 0.1, n_samples)
    energy = 0.5 * velocity**2 + 0.5 * position**2  # Should be roughly constant

    data = np.column_stack([time, position, velocity, energy])
    variable_names = ['time', 'position', 'velocity', 'energy']

    # Initialize discovery engine
    discovery = AutomaticConstraintDiscovery()

    # Discover constraints
    constraints = discovery.discover_constraints(data, variable_names, time_index=0)

    print(f"\nDiscovered {len(constraints)} constraints:")
    for constraint in constraints:
        print(f"\n  {constraint.constraint_id}")
        print(f"  Type: {constraint.constraint_type}")
        print(f"  Form: {constraint.mathematical_form}")
        print(f"  Confidence: {constraint.confidence:.2f}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    demo_constraint_discovery()
