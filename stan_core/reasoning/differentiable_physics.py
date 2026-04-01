"""
Differentiable Physics Engine for STAN V42

Implements automatic differentiation through physics forward models,
enabling gradient-based optimization for astrophysical inference.

Key capabilities:
- Automatic differentiation through any physics model
- Gradient computation for parameter sensitivity analysis
- Hessian approximation for uncertainty estimation
- Integration with gradient-based samplers (HMC, NUTS)
- Physics-informed neural network components

All physics in CGS units following STAN conventions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple, Union
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Physical Constants (CGS)
# ============================================================================

G_GRAV = 6.674e-8       # Gravitational constant [cm³/g/s²]
C_LIGHT = 2.998e10      # Speed of light [cm/s]
H_PLANCK = 6.626e-27    # Planck constant [erg·s]
K_BOLTZMANN = 1.381e-16 # Boltzmann constant [erg/K]
M_SUN = 1.989e33        # Solar mass [g]
R_SUN = 6.957e10        # Solar radius [cm]
L_SUN = 3.828e33        # Solar luminosity [erg/s]
PC = 3.086e18           # Parsec [cm]
AU = 1.496e13           # Astronomical unit [cm]
SIGMA_SB = 5.670e-5     # Stefan-Boltzmann constant [erg/cm²/s/K⁴]


# ============================================================================
# Dual Numbers for Automatic Differentiation
# ============================================================================

class DualNumber:
    """
    Dual number for forward-mode automatic differentiation.
    Represents value + epsilon * derivative
    """

    def __init__(self, value: float, derivative: float = 0.0):
        self.value = value
        self.derivative = derivative

    def __repr__(self) -> str:
        return f"Dual({self.value}, {self.derivative})"

    def __add__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            return DualNumber(self.value + other.value,
                            self.derivative + other.derivative)
        return DualNumber(self.value + other, self.derivative)

    def __radd__(self, other: float) -> 'DualNumber':
        return self + other

    def __sub__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            return DualNumber(self.value - other.value,
                            self.derivative - other.derivative)
        return DualNumber(self.value - other, self.derivative)

    def __rsub__(self, other: float) -> 'DualNumber':
        return DualNumber(other - self.value, -self.derivative)

    def __mul__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            # Product rule: (f*g)' = f'*g + f*g'
            return DualNumber(self.value * other.value,
                            self.derivative * other.value + self.value * other.derivative)
        return DualNumber(self.value * other, self.derivative * other)

    def __rmul__(self, other: float) -> 'DualNumber':
        return self * other

    def __truediv__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            # Quotient rule: (f/g)' = (f'*g - f*g') / g²
            return DualNumber(
                self.value / other.value,
                (self.derivative * other.value - self.value * other.derivative) / (other.value ** 2)
            )
        return DualNumber(self.value / other, self.derivative / other)

    def __rtruediv__(self, other: float) -> 'DualNumber':
        return DualNumber(other / self.value, -other * self.derivative / (self.value ** 2))

    def __pow__(self, n: Union[int, float, 'DualNumber']) -> 'DualNumber':
        if isinstance(n, DualNumber):
            # (f^g)' = f^g * (g' * ln(f) + g * f'/f)
            if self.value <= 0:
                return DualNumber(0.0, 0.0)
            val = self.value ** n.value
            deriv = val * (n.derivative * math.log(self.value) +
                          n.value * self.derivative / self.value)
            return DualNumber(val, deriv)
        # f^n: (f^n)' = n * f^(n-1) * f'
        return DualNumber(self.value ** n, n * (self.value ** (n - 1)) * self.derivative)

    def __neg__(self) -> 'DualNumber':
        return DualNumber(-self.value, -self.derivative)

    def __abs__(self) -> 'DualNumber':
        if self.value >= 0:
            return DualNumber(self.value, self.derivative)
        return DualNumber(-self.value, -self.derivative)

    def __lt__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value >= other.value
        return self.value >= other


# Differentiable math functions
def dual_sqrt(x: DualNumber) -> DualNumber:
    """Square root for dual numbers."""
    val = math.sqrt(x.value)
    return DualNumber(val, x.derivative / (2 * val) if val != 0 else 0.0)


def dual_exp(x: DualNumber) -> DualNumber:
    """Exponential for dual numbers."""
    val = math.exp(x.value)
    return DualNumber(val, val * x.derivative)


def dual_log(x: DualNumber) -> DualNumber:
    """Natural log for dual numbers."""
    return DualNumber(math.log(x.value), x.derivative / x.value)


def dual_sin(x: DualNumber) -> DualNumber:
    """Sine for dual numbers."""
    return DualNumber(math.sin(x.value), math.cos(x.value) * x.derivative)


def dual_cos(x: DualNumber) -> DualNumber:
    """Cosine for dual numbers."""
    return DualNumber(math.cos(x.value), -math.sin(x.value) * x.derivative)


def dual_atan2(y: DualNumber, x: DualNumber) -> DualNumber:
    """Arctangent for dual numbers."""
    denom = x.value ** 2 + y.value ** 2
    return DualNumber(
        math.atan2(y.value, x.value),
        (x.value * y.derivative - y.value * x.derivative) / denom if denom != 0 else 0.0
    )


# ============================================================================
# Gradient Tape for Reverse-Mode AD
# ============================================================================

class GradientTape:
    """
    Gradient tape for reverse-mode automatic differentiation.
    Records operations for backward pass.
    """

    def __init__(self):
        self.operations: List[Tuple[str, Any, Any, Any]] = []
        self.values: Dict[int, float] = {}
        self.adjoints: Dict[int, float] = {}
        self._watching: Dict[str, int] = {}

    def watch(self, name: str, value: float) -> int:
        """Watch a variable for gradient computation."""
        var_id = id(value) if isinstance(value, object) else hash((name, value))
        self.values[var_id] = value
        self._watching[name] = var_id
        return var_id

    def record_op(self, op: str, inputs: List[int], output_id: int, output_val: float):
        """Record an operation."""
        self.operations.append((op, inputs, output_id, output_val))
        self.values[output_id] = output_val

    def gradient(self, output_id: int, var_names: List[str]) -> Dict[str, float]:
        """Compute gradients via reverse-mode AD."""
        # Initialize adjoints
        self.adjoints = {vid: 0.0 for vid in self.values}
        self.adjoints[output_id] = 1.0

        # Backward pass
        for op, inputs, out_id, out_val in reversed(self.operations):
            adj = self.adjoints.get(out_id, 0.0)

            if op == "add":
                for inp_id in inputs:
                    self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj
            elif op == "mul":
                # d(a*b) = a*db + b*da
                a_id, b_id = inputs
                a_val = self.values[a_id]
                b_val = self.values[b_id]
                self.adjoints[a_id] = self.adjoints.get(a_id, 0.0) + adj * b_val
                self.adjoints[b_id] = self.adjoints.get(b_id, 0.0) + adj * a_val
            elif op == "div":
                a_id, b_id = inputs
                a_val = self.values[a_id]
                b_val = self.values[b_id]
                self.adjoints[a_id] = self.adjoints.get(a_id, 0.0) + adj / b_val
                self.adjoints[b_id] = self.adjoints.get(b_id, 0.0) - adj * a_val / (b_val ** 2)
            elif op == "pow":
                base_id, exp_id = inputs
                base = self.values[base_id]
                exp = self.values[exp_id]
                if base > 0:
                    self.adjoints[base_id] = self.adjoints.get(base_id, 0.0) + adj * exp * (base ** (exp - 1))
                    self.adjoints[exp_id] = self.adjoints.get(exp_id, 0.0) + adj * out_val * math.log(base)
            elif op == "sqrt":
                inp_id = inputs[0]
                if out_val != 0:
                    self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj / (2 * out_val)
            elif op == "exp":
                inp_id = inputs[0]
                self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj * out_val
            elif op == "log":
                inp_id = inputs[0]
                inp_val = self.values[inp_id]
                if inp_val != 0:
                    self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj / inp_val

        # Extract requested gradients
        result = {}
        for name in var_names:
            var_id = self._watching.get(name)
            if var_id is not None:
                result[name] = self.adjoints.get(var_id, 0.0)
            else:
                result[name] = 0.0

        return result


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class GradientResult:
    """Result of gradient computation."""
    value: float
    gradients: Dict[str, float]
    parameters: Dict[str, float]


@dataclass
class HessianResult:
    """Result of Hessian computation."""
    value: float
    gradients: Dict[str, float]
    hessian: Dict[str, Dict[str, float]]
    parameters: Dict[str, float]


@dataclass
class SensitivityAnalysis:
    """Sensitivity analysis result."""
    parameter: str
    sensitivity: float  # |∂output/∂param| * param/output (elasticity)
    gradient: float
    relative_importance: float


# ============================================================================
# Differentiable Physics Models
# ============================================================================

class DifferentiablePhysicsEngine:
    """
    Main engine for differentiable physics computations.
    Supports both forward-mode and reverse-mode AD.
    """

    def __init__(self):
        self.models: Dict[str, Callable] = {}
        self._register_builtin_models()
        self._event_bus = None

    def _register_builtin_models(self):
        """Register built-in astrophysics models."""
        self.models["planck"] = self._planck_function
        self.models["sie_lens"] = self._sie_lens_deflection
        self.models["nfw_profile"] = self._nfw_density_profile
        self.models["stellar_luminosity"] = self._stellar_luminosity
        self.models["kepler_velocity"] = self._kepler_orbital_velocity
        self.models["hydrostatic"] = self._hydrostatic_equilibrium
        self.models["synchrotron"] = self._synchrotron_emission
        self.models["bremsstrahlung"] = self._bremsstrahlung_emission
        self.models["friedmann"] = self._friedmann_equation
        self.models["sersic"] = self._sersic_profile

    def set_event_bus(self, event_bus):
        """Set event bus for integration."""
        self._event_bus = event_bus

    def register_model(self, name: str, model_fn: Callable):
        """Register a custom physics model."""
        self.models[name] = model_fn

    def compute_gradient(self,
                         model_name: str,
                         parameters: Dict[str, float],
                         diff_params: Optional[List[str]] = None) -> GradientResult:
        """
        Compute gradient of model output with respect to parameters.

        Uses forward-mode AD (efficient for few parameters).
        """
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model = self.models[model_name]
        diff_params = diff_params or list(parameters.keys())

        gradients = {}

        # Compute gradient for each parameter
        for param_name in diff_params:
            # Create dual numbers with derivative wrt this parameter
            dual_params = {}
            for name, val in parameters.items():
                if name == param_name:
                    dual_params[name] = DualNumber(val, 1.0)
                else:
                    dual_params[name] = DualNumber(val, 0.0)

            # Evaluate model with dual numbers
            result = model(dual_params)

            if isinstance(result, DualNumber):
                gradients[param_name] = result.derivative
            else:
                gradients[param_name] = 0.0

        # Get scalar value
        scalar_params = {name: DualNumber(val, 0.0) for name, val in parameters.items()}
        result = model(scalar_params)
        value = result.value if isinstance(result, DualNumber) else result

        return GradientResult(
            value=value,
            gradients=gradients,
            parameters=parameters.copy()
        )

    def compute_hessian(self,
                        model_name: str,
                        parameters: Dict[str, float],
                        diff_params: Optional[List[str]] = None) -> HessianResult:
        """
        Compute Hessian matrix using finite differences on gradients.
        """
        diff_params = diff_params or list(parameters.keys())

        # Get gradient at current point
        grad_result = self.compute_gradient(model_name, parameters, diff_params)

        # Compute Hessian via finite differences
        epsilon = 1e-6
        hessian = {p1: {p2: 0.0 for p2 in diff_params} for p1 in diff_params}

        for p1 in diff_params:
            # Perturb parameter
            params_plus = parameters.copy()
            params_plus[p1] = parameters[p1] + epsilon

            grad_plus = self.compute_gradient(model_name, params_plus, diff_params)

            for p2 in diff_params:
                hessian[p1][p2] = (grad_plus.gradients[p2] - grad_result.gradients[p2]) / epsilon

        return HessianResult(
            value=grad_result.value,
            gradients=grad_result.gradients,
            hessian=hessian,
            parameters=parameters.copy()
        )

    def sensitivity_analysis(self,
                             model_name: str,
                             parameters: Dict[str, float]) -> List[SensitivityAnalysis]:
        """
        Perform sensitivity analysis on model parameters.
        """
        grad_result = self.compute_gradient(model_name, parameters)

        sensitivities = []
        total_sensitivity = 0.0

        for param, grad in grad_result.gradients.items():
            # Elasticity: percent change in output per percent change in input
            param_val = parameters[param]
            if grad_result.value != 0 and param_val != 0:
                elasticity = abs(grad * param_val / grad_result.value)
            else:
                elasticity = 0.0

            sensitivities.append(SensitivityAnalysis(
                parameter=param,
                sensitivity=elasticity,
                gradient=grad,
                relative_importance=0.0  # Computed below
            ))
            total_sensitivity += elasticity

        # Compute relative importance
        if total_sensitivity > 0:
            for s in sensitivities:
                s.relative_importance = s.sensitivity / total_sensitivity

        # Sort by importance
        sensitivities.sort(key=lambda s: s.relative_importance, reverse=True)

        return sensitivities

    # ========================================================================
    # Built-in Differentiable Physics Models
    # ========================================================================

    def _planck_function(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Planck function for blackbody radiation.
        B_ν(T) = 2hν³/c² * 1/(exp(hν/kT) - 1)

        Parameters: nu (frequency Hz), T (temperature K)
        Returns: specific intensity [erg/s/cm²/Hz/sr]
        """
        nu = params.get("nu", DualNumber(1e14, 0.0))
        T = params.get("T", DualNumber(5778.0, 0.0))

        two = DualNumber(2.0, 0.0)
        h = DualNumber(H_PLANCK, 0.0)
        c = DualNumber(C_LIGHT, 0.0)
        k = DualNumber(K_BOLTZMANN, 0.0)

        # Numerator: 2hν³/c²
        numerator = two * h * nu * nu * nu / (c * c)

        # Exponent: hν/kT
        x = h * nu / (k * T)

        # Avoid overflow
        if x.value > 100:
            return DualNumber(0.0, 0.0)

        # exp(x) - 1
        denominator = dual_exp(x) - DualNumber(1.0, 0.0)

        if denominator.value < 1e-10:
            return DualNumber(0.0, 0.0)

        return numerator / denominator

    def _sie_lens_deflection(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Singular Isothermal Ellipsoid lens deflection magnitude.

        Parameters:
            theta_E: Einstein radius [arcsec]
            q: axis ratio (b/a)
            x, y: position [arcsec]
        Returns: deflection magnitude [arcsec]
        """
        theta_E = params.get("theta_E", DualNumber(1.0, 0.0))
        q = params.get("q", DualNumber(0.8, 0.0))
        x = params.get("x", DualNumber(0.5, 0.0))
        y = params.get("y", DualNumber(0.5, 0.0))

        # Elliptical radius
        q_sq = q * q
        r_ell = dual_sqrt(x * x + y * y / q_sq)

        if r_ell.value < 1e-10:
            return DualNumber(0.0, 0.0)

        # SIE deflection (simplified)
        deflection = theta_E * dual_sqrt(q) / r_ell

        return deflection

    def _nfw_density_profile(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Navarro-Frenk-White density profile.
        ρ(r) = ρ_s / [(r/r_s)(1 + r/r_s)²]

        Parameters:
            r: radius [kpc]
            r_s: scale radius [kpc]
            rho_s: scale density [M_sun/kpc³]
        Returns: density [M_sun/kpc³]
        """
        r = params.get("r", DualNumber(10.0, 0.0))
        r_s = params.get("r_s", DualNumber(20.0, 0.0))
        rho_s = params.get("rho_s", DualNumber(1e7, 0.0))

        x = r / r_s

        if x.value < 1e-10:
            return rho_s  # Core density

        one = DualNumber(1.0, 0.0)
        denom = x * (one + x) * (one + x)

        return rho_s / denom

    def _stellar_luminosity(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Stefan-Boltzmann law: L = 4πR²σT⁴

        Parameters:
            R: radius [cm]
            T: effective temperature [K]
        Returns: luminosity [erg/s]
        """
        R = params.get("R", DualNumber(R_SUN, 0.0))
        T = params.get("T", DualNumber(5778.0, 0.0))

        four_pi = DualNumber(4.0 * math.pi, 0.0)
        sigma = DualNumber(SIGMA_SB, 0.0)

        return four_pi * R * R * sigma * T * T * T * T

    def _kepler_orbital_velocity(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Keplerian orbital velocity: v = sqrt(GM/r)

        Parameters:
            M: central mass [g]
            r: orbital radius [cm]
        Returns: velocity [cm/s]
        """
        M = params.get("M", DualNumber(M_SUN, 0.0))
        r = params.get("r", DualNumber(AU, 0.0))

        G = DualNumber(G_GRAV, 0.0)

        return dual_sqrt(G * M / r)

    def _hydrostatic_equilibrium(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Hydrostatic pressure: dP/dr = -ρGM(r)/r²

        Computes pressure gradient for given conditions.

        Parameters:
            rho: density [g/cm³]
            M_r: enclosed mass [g]
            r: radius [cm]
        Returns: pressure gradient [dyn/cm³]
        """
        rho = params.get("rho", DualNumber(1.0, 0.0))
        M_r = params.get("M_r", DualNumber(M_SUN, 0.0))
        r = params.get("r", DualNumber(R_SUN, 0.0))

        G = DualNumber(G_GRAV, 0.0)

        return DualNumber(-1.0, 0.0) * rho * G * M_r / (r * r)

    def _synchrotron_emission(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Synchrotron power: P ∝ B² γ² (simplified)

        Parameters:
            B: magnetic field [G]
            gamma: Lorentz factor
        Returns: power [erg/s]
        """
        B = params.get("B", DualNumber(1e-6, 0.0))
        gamma = params.get("gamma", DualNumber(1000.0, 0.0))

        # Thomson cross section
        sigma_T = DualNumber(6.652e-25, 0.0)
        c = DualNumber(C_LIGHT, 0.0)

        # Magnetic energy density
        U_B = B * B / (DualNumber(8.0 * math.pi, 0.0))

        # Power ∝ σ_T c U_B γ²
        return sigma_T * c * U_B * gamma * gamma

    def _bremsstrahlung_emission(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Free-free emission: ε_ff ∝ n_e² T^(1/2) (simplified)

        Parameters:
            n_e: electron density [cm⁻³]
            T: temperature [K]
        Returns: emissivity [erg/s/cm³]
        """
        n_e = params.get("n_e", DualNumber(1.0, 0.0))
        T = params.get("T", DualNumber(1e6, 0.0))

        # Gaunt factor approximation
        g_ff = DualNumber(1.2, 0.0)

        # Constant factor
        const = DualNumber(1.4e-27, 0.0)  # [erg cm³/s/K^0.5]

        return const * g_ff * n_e * n_e * dual_sqrt(T)

    def _friedmann_equation(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Friedmann equation for Hubble parameter.
        H(z) = H0 * sqrt(Ω_m(1+z)³ + Ω_Λ)

        Parameters:
            H0: Hubble constant [km/s/Mpc]
            Omega_m: matter density parameter
            Omega_Lambda: dark energy density parameter
            z: redshift
        Returns: H(z) [km/s/Mpc]
        """
        H0 = params.get("H0", DualNumber(70.0, 0.0))
        Omega_m = params.get("Omega_m", DualNumber(0.3, 0.0))
        Omega_L = params.get("Omega_Lambda", DualNumber(0.7, 0.0))
        z = params.get("z", DualNumber(0.5, 0.0))

        one = DualNumber(1.0, 0.0)
        one_plus_z = one + z
        z_term = one_plus_z * one_plus_z * one_plus_z

        return H0 * dual_sqrt(Omega_m * z_term + Omega_L)

    def _sersic_profile(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Sersic surface brightness profile.
        I(r) = I_e * exp(-b_n * [(r/r_e)^(1/n) - 1])

        Parameters:
            r: radius [arcsec]
            r_e: effective radius [arcsec]
            n: Sersic index
            I_e: intensity at r_e
        Returns: surface brightness
        """
        r = params.get("r", DualNumber(1.0, 0.0))
        r_e = params.get("r_e", DualNumber(2.0, 0.0))
        n = params.get("n", DualNumber(4.0, 0.0))  # de Vaucouleurs
        I_e = params.get("I_e", DualNumber(1.0, 0.0))

        # Approximate b_n ≈ 2n - 1/3
        one_third = DualNumber(1.0 / 3.0, 0.0)
        two = DualNumber(2.0, 0.0)
        b_n = two * n - one_third

        # (r/r_e)^(1/n)
        x = r / r_e
        one_over_n = DualNumber(1.0, 0.0) / n
        x_pow = x ** one_over_n

        # exp(-b_n * [x^(1/n) - 1])
        one = DualNumber(1.0, 0.0)
        exponent = DualNumber(-1.0, 0.0) * b_n * (x_pow - one)

        return I_e * dual_exp(exponent)


# ============================================================================
# Gradient-Based Optimization
# ============================================================================

class GradientOptimizer:
    """
    Gradient-based optimizer for physics models.
    """

    def __init__(self, engine: DifferentiablePhysicsEngine):
        self.engine = engine

    def optimize(self,
                 model_name: str,
                 initial_params: Dict[str, float],
                 target_value: float,
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None,
                 learning_rate: float = 0.01,
                 max_iterations: int = 1000,
                 tolerance: float = 1e-6) -> Tuple[Dict[str, float], List[float]]:
        """
        Optimize parameters to match target value using gradient descent.
        """
        params = initial_params.copy()
        losses = []

        for i in range(max_iterations):
            # Compute gradient
            result = self.engine.compute_gradient(model_name, params)

            # Loss = (value - target)²
            diff = result.value - target_value
            loss = diff * diff
            losses.append(loss)

            if loss < tolerance:
                break

            # Update parameters
            for name in params:
                grad = result.gradients.get(name, 0.0)
                # Gradient of loss wrt param: 2 * diff * dvalue/dparam
                grad_loss = 2 * diff * grad

                params[name] -= learning_rate * grad_loss

                # Apply bounds
                if bounds and name in bounds:
                    low, high = bounds[name]
                    params[name] = max(low, min(high, params[name]))

        return params, losses


# ============================================================================
# Fisher Information Matrix
# ============================================================================

class FisherInformationEstimator:
    """
    Estimates Fisher information matrix for parameter uncertainty.
    """

    def __init__(self, engine: DifferentiablePhysicsEngine):
        self.engine = engine

    def compute_fisher_matrix(self,
                              model_name: str,
                              parameters: Dict[str, float],
                              data_points: List[Dict[str, float]],
                              noise_variance: float) -> Dict[str, Dict[str, float]]:
        """
        Compute Fisher information matrix.
        F_ij = (1/σ²) Σ (∂μ/∂θ_i)(∂μ/∂θ_j)
        """
        param_names = list(parameters.keys())
        n_params = len(param_names)

        # Initialize Fisher matrix
        fisher = {p1: {p2: 0.0 for p2 in param_names} for p1 in param_names}

        # Sum over data points
        for data in data_points:
            # Merge data with parameters
            full_params = parameters.copy()
            full_params.update(data)

            # Compute gradient
            result = self.engine.compute_gradient(model_name, full_params, param_names)

            # Outer product of gradients
            for p1 in param_names:
                for p2 in param_names:
                    fisher[p1][p2] += (result.gradients[p1] * result.gradients[p2] /
                                      noise_variance)

        return fisher

    def parameter_uncertainties(self,
                                fisher_matrix: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Compute parameter uncertainties from Fisher matrix.
        σ_i = sqrt((F^-1)_ii)
        """
        param_names = list(fisher_matrix.keys())
        n = len(param_names)

        # Convert to list of lists for inversion
        matrix = [[fisher_matrix[p1][p2] for p2 in param_names] for p1 in param_names]

        # Simple matrix inversion (Gauss-Jordan)
        inv = self._invert_matrix(matrix)

        # Extract diagonal uncertainties
        uncertainties = {}
        for i, name in enumerate(param_names):
            if inv[i][i] > 0:
                uncertainties[name] = math.sqrt(inv[i][i])
            else:
                uncertainties[name] = float('inf')

        return uncertainties

    def _invert_matrix(self, matrix: List[List[float]]) -> List[List[float]]:
        """Gauss-Jordan matrix inversion."""
        n = len(matrix)

        # Augment with identity
        aug = [row + [1.0 if i == j else 0.0 for j in range(n)]
               for i, row in enumerate(matrix)]

        # Forward elimination
        for i in range(n):
            # Find pivot
            max_row = max(range(i, n), key=lambda r: abs(aug[r][i]))
            aug[i], aug[max_row] = aug[max_row], aug[i]

            if abs(aug[i][i]) < 1e-10:
                continue

            # Scale row
            scale = aug[i][i]
            aug[i] = [x / scale for x in aug[i]]

            # Eliminate column
            for j in range(n):
                if i != j:
                    factor = aug[j][i]
                    aug[j] = [aug[j][k] - factor * aug[i][k] for k in range(2 * n)]

        # Extract inverse
        return [row[n:] for row in aug]


# ============================================================================
# Singleton Access
# ============================================================================

_physics_engine: Optional[DifferentiablePhysicsEngine] = None


def get_differentiable_physics_engine() -> DifferentiablePhysicsEngine:
    """Get singleton physics engine instance."""
    global _physics_engine
    if _physics_engine is None:
        _physics_engine = DifferentiablePhysicsEngine()
    return _physics_engine


# ============================================================================
# Integration with STAN Event Bus
# ============================================================================

def setup_differentiable_physics_integration(event_bus) -> None:
    """Set up differentiable physics integration with STAN event bus."""
    engine = get_differentiable_physics_engine()
    engine.set_event_bus(event_bus)

    def on_gradient_request(event):
        """Handle gradient computation requests."""
        payload = event.get("payload", {})
        model_name = payload.get("model")
        parameters = payload.get("parameters", {})

        if model_name and parameters:
            result = engine.compute_gradient(model_name, parameters)

            event_bus.publish(
                "gradient_result",
                "differentiable_physics",
                {
                    "model": model_name,
                    "value": result.value,
                    "gradients": result.gradients
                }
            )

    def on_sensitivity_request(event):
        """Handle sensitivity analysis requests."""
        payload = event.get("payload", {})
        model_name = payload.get("model")
        parameters = payload.get("parameters", {})

        if model_name and parameters:
            sensitivities = engine.sensitivity_analysis(model_name, parameters)

            event_bus.publish(
                "sensitivity_result",
                "differentiable_physics",
                {
                    "model": model_name,
                    "sensitivities": [
                        {
                            "parameter": s.parameter,
                            "elasticity": s.sensitivity,
                            "gradient": s.gradient,
                            "importance": s.relative_importance
                        }
                        for s in sensitivities
                    ]
                }
            )

    event_bus.subscribe("gradient_request", on_gradient_request)
    event_bus.subscribe("sensitivity_request", on_sensitivity_request)
    logger.info("Differentiable physics integration configured")
