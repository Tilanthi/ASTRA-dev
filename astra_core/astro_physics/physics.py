"""
Physics Engine for Astronomical Inference

This module provides the PHYSICS LAYER for astronomical inference. It implements:

1. Fundamental physical constants and unit conversions
2. Astrophysical forward models (the actual equations)
3. Conservation laws and constraints
4. Dimensional analysis validation

The key insight: Swarm intelligence is powerful for EXPLORATION, and
astronomical inference requires PHYSICS-BASED FITNESS FUNCTIONS to guide it.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from scipy.integrate import quad, odeint
from scipy.special import gamma as gamma_func
from scipy.interpolate import interp1d


# =============================================================================
# PHYSICAL CONSTANTS (CODATA 2018)
# =============================================================================

class PhysicalConstants:
    """Fundamental physical constants in SI units"""

    # Fundamental
    c = 299792458.0  # Speed of light [m/s]
    G = 6.67430e-11  # Gravitational constant [m³/kg/s²]
    h = 6.62607015e-34  # Planck constant [J·s]
    hbar = 1.054571817e-34  # Reduced Planck constant [J·s]
    k_B = 1.380649e-23  # Boltzmann constant [J/K]
    e = 1.602176634e-19  # Elementary charge [C]
    m_e = 9.1093837015e-31  # Electron mass [kg]
    m_p = 1.67262192369e-27  # Proton mass [kg]
    sigma_SB = 5.670374419e-8  # Stefan-Boltzmann constant [W/m²/K⁴]
    sigma_T = 6.6524587321e-29  # Thomson cross-section [m²]

    # Astronomical
    M_sun = 1.98841e30  # Solar mass [kg]
    L_sun = 3.828e26  # Solar luminosity [W]
    R_sun = 6.9634e8  # Solar radius [m]
    AU = 1.495978707e11  # Astronomical unit [m]
    pc = 3.0856775814913673e16  # Parsec [m]
    Mpc = 3.0856775814913673e22  # Megaparsec [m]
    ly = 9.4607304725808e15  # Light year [m]

    # Cosmological (Planck 2018)
    H0 = 67.4  # Hubble constant [km/s/Mpc]
    Omega_m = 0.315  # Matter density parameter
    Omega_L = 0.685  # Dark energy density parameter
    Omega_b = 0.0493  # Baryon density parameter
    Omega_k = 0.0  # Curvature (flat universe)
    T_CMB = 2.7255  # CMB temperature [K]

    @classmethod
    def H0_SI(cls) -> float:
        """Hubble constant in SI units [1/s]"""
        return cls.H0 * 1000 / cls.Mpc


# =============================================================================
# ASTROPHYSICAL CONSTRAINTS
# =============================================================================

class ConstraintType(Enum):
    """Types of physical constraints"""
    CONSERVATION = "conservation"  # Energy, momentum, mass conservation
    BOUND = "bound"  # Physical bounds (mass > 0, T > 0)
    CAUSALITY = "causality"  # No superluminal, no negative time
    STABILITY = "stability"  # Virial, Jeans, etc.
    OBSERVATIONAL = "observational"  # Must match observations within errors


@dataclass
class PhysicalConstraint:
    """A physical constraint that must be satisfied"""
    name: str
    constraint_type: ConstraintType
    check_function: Callable[[Dict], Tuple[bool, float]]  # Returns (satisfied, violation_magnitude)
    description: str
    severity: str = "hard"  # "hard" = must satisfy, "soft" = penalize violations


class AstrophysicalConstraints:
    """
    Collection of astrophysical constraints

    These constraints are IMMUTABLE physical laws, analogous to
    Gordon's biological parameters but for physics.
    """

    def __init__(self):
        self.constraints: List[PhysicalConstraint] = []
        self._build_fundamental_constraints()

    def _build_fundamental_constraints(self):
        """Build fundamental physical constraints"""

        # Mass positivity
        self.constraints.append(PhysicalConstraint(
            name="mass_positive",
            constraint_type=ConstraintType.BOUND,
            check_function=lambda p: (p.get('mass', 1) > 0, max(0, -p.get('mass', 1))),
            description="Mass must be positive",
            severity="hard"
        ))

        # Temperature positivity
        self.constraints.append(PhysicalConstraint(
            name="temperature_positive",
            constraint_type=ConstraintType.BOUND,
            check_function=lambda p: (p.get('temperature', 1) > 0, max(0, -p.get('temperature', 1))),
            description="Temperature must be positive (T > 0 K)",
            severity="hard"
        ))

        # Luminosity positivity
        self.constraints.append(PhysicalConstraint(
            name="luminosity_positive",
            constraint_type=ConstraintType.BOUND,
            check_function=lambda p: (p.get('luminosity', 1) > 0, max(0, -p.get('luminosity', 1))),
            description="Luminosity must be positive",
            severity="hard"
        ))

        # Velocity < c
        self.constraints.append(PhysicalConstraint(
            name="subluminal_velocity",
            constraint_type=ConstraintType.CAUSALITY,
            check_function=lambda p: (
                p.get('velocity', 0) < PhysicalConstants.c,
                max(0, p.get('velocity', 0) - PhysicalConstants.c)
            ),
            description="Velocity must be less than speed of light",
            severity="hard"
        ))

        # Redshift >= -1 (no blueshift beyond source frame)
        self.constraints.append(PhysicalConstraint(
            name="redshift_physical",
            constraint_type=ConstraintType.BOUND,
            check_function=lambda p: (p.get('redshift', 0) >= -1, max(0, -1 - p.get('redshift', 0))),
            description="Redshift must be >= -1",
            severity="hard"
        ))

        # Schwarzschild radius constraint (object larger than its event horizon)
        def schwarzschild_check(p):
            if 'mass' not in p or 'radius' not in p:
                return True, 0.0
            r_s = 2 * PhysicalConstants.G * p['mass'] / PhysicalConstants.c**2
            return p['radius'] > r_s, max(0, r_s - p['radius'])

        self.constraints.append(PhysicalConstraint(
            name="not_black_hole",
            constraint_type=ConstraintType.STABILITY,
            check_function=schwarzschild_check,
            description="Non-BH object must be larger than Schwarzschild radius",
            severity="soft"  # BHs are valid, just a different regime
        ))

    def add_constraint(self, constraint: PhysicalConstraint):
        """Add a custom constraint"""
        self.constraints.append(constraint)

    def check_all(self, parameters: Dict) -> Dict:
        """Check all constraints against parameters"""
        results = {
            'satisfied': True,
            'violations': [],
            'total_violation': 0.0
        }

        for constraint in self.constraints:
            satisfied, violation = constraint.check_function(parameters)

            if not satisfied:
                results['violations'].append({
                    'name': constraint.name,
                    'type': constraint.constraint_type.value,
                    'severity': constraint.severity,
                    'violation_magnitude': violation,
                    'description': constraint.description
                })
                results['total_violation'] += violation

                if constraint.severity == "hard":
                    results['satisfied'] = False

        return results


# =============================================================================
# FORWARD MODELS (THE ACTUAL PHYSICS)
# =============================================================================

class ForwardModel(ABC):
    """
    Abstract base class for astrophysical forward models

    A forward model takes physical parameters and predicts observables.
    This is what was MISSING from the V36-Swarm lens implementation.
    """

    @abstractmethod
    def predict(self, parameters: Dict) -> Dict:
        """Predict observables from parameters"""
        pass

    @abstractmethod
    def parameter_names(self) -> List[str]:
        """List of parameter names"""
        pass

    @abstractmethod
    def observable_names(self) -> List[str]:
        """List of observable names"""
        pass


class GravitationalLensModel(ForwardModel):
    """
    Singular Isothermal Ellipsoid (SIE) + External Shear lens model

    This implements the ACTUAL lens equation that was missing from V36-Swarm.
    """

    def __init__(self):
        self.pc = PhysicalConstants

    def parameter_names(self) -> List[str]:
        return ['einstein_radius', 'ellipticity', 'position_angle',
                'lens_x', 'lens_y', 'source_x', 'source_y',
                'shear_magnitude', 'shear_angle', 'z_lens', 'z_source']

    def observable_names(self) -> List[str]:
        return ['image_positions', 'image_fluxes', 'time_delays', 'magnifications']

    def deflection_angle(self, theta_x: np.ndarray, theta_y: np.ndarray,
                         theta_E: float, e: float, phi: float,
                         lens_x: float = 0, lens_y: float = 0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate SIE deflection angles

        Parameters:
        -----------
        theta_x, theta_y : Image positions relative to origin [arcsec]
        theta_E : Einstein radius [arcsec]
        e : Ellipticity (1 - b/a)
        phi : Position angle [radians]
        lens_x, lens_y : Lens center position [arcsec]

        Returns:
        --------
        alpha_x, alpha_y : Deflection angles [arcsec]
        """
        # Transform to lens-centered coordinates
        dx = np.atleast_1d(theta_x) - lens_x
        dy = np.atleast_1d(theta_y) - lens_y

        # Rotate to align with ellipse axes
        cos_phi = np.cos(phi)
        sin_phi = np.sin(phi)

        x_rot = dx * cos_phi + dy * sin_phi
        y_rot = -dx * sin_phi + dy * cos_phi

        # Axis ratio
        q = max(0.1, 1 - e)  # Prevent extreme ellipticities

        if e < 0.01:
            # Nearly circular - use SIS
            r = np.sqrt(x_rot**2 + y_rot**2)
            r = np.maximum(r, 1e-10)
            alpha_x_rot = theta_E * x_rot / r
            alpha_y_rot = theta_E * y_rot / r
        else:
            # Full SIE calculation
            psi = np.sqrt(q**2 * x_rot**2 + y_rot**2)
            psi = np.maximum(psi, 1e-10)

            sqrt_1_q2 = np.sqrt(1 - q**2)

            alpha_x_rot = theta_E * np.sqrt(q) / sqrt_1_q2 * np.arctan(sqrt_1_q2 * x_rot / psi)
            alpha_y_rot = theta_E * np.sqrt(q) / sqrt_1_q2 * np.arctanh(
                np.clip(sqrt_1_q2 * y_rot / psi, -0.9999, 0.9999)
            )

        # Rotate back
        alpha_x = alpha_x_rot * cos_phi - alpha_y_rot * sin_phi
        alpha_y = alpha_x_rot * sin_phi + alpha_y_rot * cos_phi

        return alpha_x, alpha_y

    def external_shear(self, theta_x: np.ndarray, theta_y: np.ndarray,
                       gamma: float, phi_gamma: float) -> Tuple[np.ndarray, np.ndarray]:
        """Add external shear contribution"""
        cos_2phi = np.cos(2 * phi_gamma)
        sin_2phi = np.sin(2 * phi_gamma)

        alpha_x = gamma * (theta_x * cos_2phi + theta_y * sin_2phi)
        alpha_y = gamma * (theta_x * sin_2phi - theta_y * cos_2phi)

        return alpha_x, alpha_y

    def lens_equation(self, theta_x: np.ndarray, theta_y: np.ndarray,
                      params: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply lens equation: β = θ - α(θ)

        Maps image positions to source positions.
        """
        # Main lens deflection
        alpha_x, alpha_y = self.deflection_angle(
            theta_x, theta_y,
            params['einstein_radius'],
            params['ellipticity'],
            params['position_angle'],
            params.get('lens_x', 0),
            params.get('lens_y', 0)
        )

        # External shear
        if params.get('shear_magnitude', 0) > 0:
            shear_x, shear_y = self.external_shear(
                np.atleast_1d(theta_x) - params.get('lens_x', 0),
                np.atleast_1d(theta_y) - params.get('lens_y', 0),
                params['shear_magnitude'],
                params['shear_angle']
            )
            alpha_x = alpha_x + shear_x
            alpha_y = alpha_y + shear_y

        # Source position
        beta_x = np.atleast_1d(theta_x) - alpha_x
        beta_y = np.atleast_1d(theta_y) - alpha_y

        return beta_x, beta_y

    def magnification(self, theta_x: np.ndarray, theta_y: np.ndarray,
                      params: Dict, delta: float = 1e-5) -> np.ndarray:
        """
        Calculate magnification μ = 1/det(A)

        Where A = ∂β/∂θ is the Jacobian of the lens mapping.
        """
        theta_x = np.atleast_1d(theta_x)
        theta_y = np.atleast_1d(theta_y)

        # Numerical Jacobian
        beta_x0, beta_y0 = self.lens_equation(theta_x, theta_y, params)
        beta_x1, _ = self.lens_equation(theta_x + delta, theta_y, params)
        beta_x2, _ = self.lens_equation(theta_x, theta_y + delta, params)
        _, beta_y1 = self.lens_equation(theta_x + delta, theta_y, params)
        _, beta_y2 = self.lens_equation(theta_x, theta_y + delta, params)

        # Jacobian elements
        a11 = (beta_x1 - beta_x0) / delta
        a12 = (beta_x2 - beta_x0) / delta
        a21 = (beta_y1 - beta_y0) / delta
        a22 = (beta_y2 - beta_y0) / delta

        det_A = a11 * a22 - a12 * a21

        return 1 / np.abs(det_A)

    def predict(self, parameters: Dict) -> Dict:
        """
        Predict observables from lens parameters

        Given lens parameters, find image positions for a point source.
        """
        # This would involve solving the lens equation numerically
        # For now, return structure showing what would be computed
        return {
            'image_positions': None,  # Would be computed
            'image_fluxes': None,
            'time_delays': None,
            'magnifications': None
        }

    def chi_squared(self, parameters: Dict, observations: Dict) -> float:
        """
        Compute chi-squared between model and observations

        THIS IS THE PROPER FITNESS FUNCTION for gravitational lensing.
        """
        image_positions = observations['image_positions']

        # Apply lens equation to observed image positions
        beta_x, beta_y = self.lens_equation(
            image_positions[:, 0],
            image_positions[:, 1],
            parameters
        )

        # Source position from parameters
        source_x = parameters['source_x'] + parameters.get('lens_x', 0)
        source_y = parameters['source_y'] + parameters.get('lens_y', 0)

        # Chi-squared: All images should map to same source
        chi2_pos = np.sum((beta_x - source_x)**2 + (beta_y - source_y)**2)

        # Weight by uncertainties
        sigma = observations.get('position_uncertainty', 0.01)
        chi2_pos /= sigma**2

        # Flux constraint
        if 'image_fluxes' in observations and observations['image_fluxes'] is not None:
            pred_mags = self.magnification(
                image_positions[:, 0],
                image_positions[:, 1],
                parameters
            )
            pred_flux = pred_mags / np.max(pred_mags)
            obs_flux = observations['image_fluxes']
            chi2_flux = np.sum((pred_flux - obs_flux)**2) * 100
        else:
            chi2_flux = 0

        return chi2_pos + chi2_flux


class StellarStructureModel(ForwardModel):
    """
    Stellar structure model for inferring stellar parameters

    Uses scaling relations and stellar physics.
    """

    def __init__(self):
        self.pc = PhysicalConstants

    def parameter_names(self) -> List[str]:
        return ['mass', 'radius', 'temperature', 'luminosity', 'metallicity', 'age']

    def observable_names(self) -> List[str]:
        return ['apparent_magnitude', 'color', 'parallax', 'spectrum']

    def stefan_boltzmann(self, radius: float, temperature: float) -> float:
        """L = 4πR²σT⁴"""
        return 4 * np.pi * radius**2 * self.pc.sigma_SB * temperature**4

    def main_sequence_mass_luminosity(self, mass: float) -> float:
        """
        Mass-luminosity relation for main sequence stars

        L/L_sun ≈ (M/M_sun)^α where α depends on mass range
        """
        m = mass / self.pc.M_sun

        if m < 0.43:
            alpha = 2.3
        elif m < 2:
            alpha = 4.0
        elif m < 55:
            alpha = 3.5
        else:
            alpha = 1.0

        return self.pc.L_sun * m**alpha

    def predict(self, parameters: Dict) -> Dict:
        """Predict observables from stellar parameters"""
        L = self.stefan_boltzmann(parameters['radius'], parameters['temperature'])

        return {
            'luminosity': L,
            'absolute_magnitude': -2.5 * np.log10(L / self.pc.L_sun) + 4.83,
        }


class CosmologicalModel(ForwardModel):
    """
    Cosmological distance and expansion model

    Implements ΛCDM cosmology for distance calculations.
    """

    def __init__(self, H0: float = None, Omega_m: float = None, Omega_L: float = None):
        self.pc = PhysicalConstants
        self.H0 = H0 or self.pc.H0
        self.Omega_m = Omega_m or self.pc.Omega_m
        self.Omega_L = Omega_L or self.pc.Omega_L

    def parameter_names(self) -> List[str]:
        return ['redshift', 'H0', 'Omega_m', 'Omega_L']

    def observable_names(self) -> List[str]:
        return ['luminosity_distance', 'angular_diameter_distance', 'comoving_distance',
                'lookback_time', 'age_at_redshift']

    def E(self, z: float) -> float:
        """Dimensionless Hubble parameter E(z) = H(z)/H0"""
        return np.sqrt(self.Omega_m * (1 + z)**3 + self.Omega_L)

    def comoving_distance(self, z: float) -> float:
        """Comoving distance in Mpc"""
        def integrand(z_prime):
            return 1 / self.E(z_prime)

        result, _ = quad(integrand, 0, z)
        return (self.pc.c / 1000) / self.H0 * result  # Convert to Mpc

    def luminosity_distance(self, z: float) -> float:
        """Luminosity distance in Mpc"""
        return (1 + z) * self.comoving_distance(z)

    def angular_diameter_distance(self, z: float) -> float:
        """Angular diameter distance in Mpc"""
        return self.comoving_distance(z) / (1 + z)

    def angular_diameter_distance_between(self, z1: float, z2: float) -> float:
        """Angular diameter distance between two redshifts (for lensing)"""
        if z2 <= z1:
            raise ValueError("z2 must be greater than z1")

        D_1 = self.comoving_distance(z1)
        D_2 = self.comoving_distance(z2)

        return (D_2 - D_1) / (1 + z2)

    def lookback_time(self, z: float) -> float:
        """Lookback time in Gyr"""
        def integrand(z_prime):
            return 1 / ((1 + z_prime) * self.E(z_prime))

        result, _ = quad(integrand, 0, z)
        H0_per_Gyr = self.H0 * 1.022e-3  # Convert km/s/Mpc to 1/Gyr
        return result / H0_per_Gyr

    def predict(self, parameters: Dict) -> Dict:
        """Predict distances and times from redshift"""
        z = parameters['redshift']

        return {
            'comoving_distance': self.comoving_distance(z),
            'luminosity_distance': self.luminosity_distance(z),
            'angular_diameter_distance': self.angular_diameter_distance(z),
            'lookback_time': self.lookback_time(z)
        }


class GalaxyDynamicsModel(ForwardModel):
    """
    Galaxy dynamics model for rotation curves, velocity dispersions

    Implements dark matter halo models and Jeans equations.
    """

    def __init__(self):
        self.pc = PhysicalConstants

    def parameter_names(self) -> List[str]:
        return ['halo_mass', 'scale_radius', 'concentration',
                'stellar_mass', 'effective_radius', 'inclination']

    def observable_names(self) -> List[str]:
        return ['rotation_curve', 'velocity_dispersion', 'mass_profile']

    def nfw_density(self, r: float, rho_s: float, r_s: float) -> float:
        """NFW dark matter halo density profile"""
        x = r / r_s
        return rho_s / (x * (1 + x)**2)

    def nfw_mass(self, r: float, M_200: float, c: float, r_200: float) -> float:
        """Enclosed mass for NFW profile"""
        r_s = r_200 / c
        x = r / r_s

        # NFW mass formula
        f_c = np.log(1 + c) - c / (1 + c)
        f_x = np.log(1 + x) - x / (1 + x)

        return M_200 * f_x / f_c

    def circular_velocity(self, r: float, M_enclosed: float) -> float:
        """Circular velocity from enclosed mass"""
        return np.sqrt(self.pc.G * M_enclosed / r)

    def predict(self, parameters: Dict) -> Dict:
        """Predict rotation curve from halo parameters"""
        # Would compute full rotation curve
        return {
            'rotation_curve': None,
            'velocity_dispersion': None
        }


# =============================================================================
# PHYSICS ENGINE (COORDINATOR)
# =============================================================================

class PhysicsEngine:
    """
    Central physics engine for astronomical inference

    Coordinates:
    - Forward models (predicting observables from parameters)
    - Constraints (physical laws that must be satisfied)
    - Unit conversions
    - Dimensional analysis
    """

    def __init__(self):
        self.constants = PhysicalConstants()
        self.constraints = AstrophysicalConstraints()
        self.models: Dict[str, ForwardModel] = {}

        # Register default models
        self._register_default_models()

    def _register_default_models(self):
        """Register built-in forward models"""
        self.models['gravitational_lens'] = GravitationalLensModel()
        self.models['stellar_structure'] = StellarStructureModel()
        self.models['cosmology'] = CosmologicalModel()
        self.models['galaxy_dynamics'] = GalaxyDynamicsModel()

    def register_model(self, name: str, model: ForwardModel):
        """Register a custom forward model"""
        self.models[name] = model

    def get_model(self, name: str) -> ForwardModel:
        """Get a registered model"""
        if name not in self.models:
            raise ValueError(f"Unknown model: {name}. Available: {list(self.models.keys())}")
        return self.models[name]

    def compute_chi_squared(self, model_name: str, parameters: Dict,
                            observations: Dict) -> float:
        """
        Compute chi-squared for a model

        This is the PROPER fitness function for astronomical inference.
        """
        model = self.get_model(model_name)

        # Check physical constraints first
        constraint_check = self.constraints.check_all(parameters)
        if not constraint_check['satisfied']:
            # Return large chi-squared for unphysical parameters
            return 1e10 + constraint_check['total_violation'] * 1e6

        # Compute model-specific chi-squared
        if hasattr(model, 'chi_squared'):
            return model.chi_squared(parameters, observations)
        else:
            # Generic chi-squared from predictions
            predictions = model.predict(parameters)
            chi2 = 0
            for key in predictions:
                if key in observations and predictions[key] is not None:
                    chi2 += np.sum((predictions[key] - observations[key])**2)
            return chi2

    def validate_parameters(self, parameters: Dict) -> Dict:
        """Validate parameters against physical constraints"""
        return self.constraints.check_all(parameters)
