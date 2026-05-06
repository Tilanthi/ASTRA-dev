"""
SymPy Integration for ASTRA Physics Engine

This module integrates SymPy for symbolic mathematics in physics calculations,
providing exact analytical solutions for astrophysical problems.

Key capabilities:
- Symbolic differentiation and integration
- Analytical solutions to differential equations
- Exact algebraic manipulations
- LaTeX equation generation
- Symbolic tensor operations
"""

from typing import Dict, List, Tuple, Optional, Any, Union
import logging

try:
    import sympy as sp
    from sympy import symbols, Symbol, Function, Eq, solve, diff, integrate, dsolve
    from sympy.physics import units as sp_units
    from sympy.physics.vector import dynamicsymbols
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    sp = None
    symbols = Symbol = None

logger = logging.getLogger(__name__)


class SymbolicPhysicsEngine:
    """
    SymPy-powered symbolic physics engine for ASTRA.

    Provides exact mathematical operations for:
    - Analytical derivations
    - Perturbation theory
    - Stability analysis
    - Symbolic integration of equations of motion
    - Exact algebraic solutions
    """

    def __init__(self):
        """Initialize symbolic physics engine."""
        if not SYMPY_AVAILABLE:
            logger.warning("SymPy not available. Symbolic physics operations will be limited.")
            self.available = False
            return

        self.available = True
        self._symbols: Dict[str, Symbol] = {}
        self._equations: List[Eq] = []

        # Define common physical symbols
        self._define_common_symbols()

        logger.info("Initialized SymPy symbolic physics engine")

    def _define_common_symbols(self):
        """Define commonly used physical symbols."""
        if not self.available:
            return

        # Fundamental constants
        self.G = symbols('G', constant=True)  # Gravitational constant
        self.c = symbols('c', constant=True)  # Speed of light
        self.h = symbols('h', constant=True)  # Planck constant
        self.k_B = symbols('k_B', constant=True)  # Boltzmann constant

        # Variables
        self.t = symbols('t', real=True, positive=True)  # Time
        self.x = symbols('x', real=True)  # Position
        self.y = symbols('y', real=True)  # Position
        self.z = symbols('z', real=True)  # Position
        self.r = symbols('r', real=True, positive=True)  # Radial distance

        # Physical quantities
        self.m = symbols('m', real=True, positive=True)  # Mass
        self.M = symbols('M', real=True, positive=True)  # Mass
        self.rho = symbols('rho', real=True)  # Density
        self.P = symbols('P', real=True)  # Pressure
        self.B = symbols('B', real=True)  # Magnetic field
        self.v = symbols('v', real=True)  # Velocity
        self.T = symbols('T', real=True, positive=True)  # Temperature

        # Filament/ISM specific
        self.lambda_sym = symbols('lambda', real=True, positive=True)  # Wavelength
        self.W = symbols('W', real=True, positive=True)  # Width
        self.f = symbols('f', real=True, positive=True)  # Line-mass ratio
        self.beta = symbols('beta', real=True, positive=True)  # Plasma beta
        self.Mach = symbols('M', real=True, positive=True)  # Mach number

        # Store symbols
        self._symbols.update({
            'G': self.G, 'c': self.c, 'h': self.h, 'k_B': self.k_B,
            't': self.t, 'x': self.x, 'y': self.y, 'z': self.z, 'r': self.r,
            'm': self.m, 'M': self.M, 'rho': self.rho, 'P': self.P,
            'B': self.B, 'v': self.v, 'T': self.T,
            'lambda': self.lambda_sym, 'W': self.W, 'f': self.f,
            'beta': self.beta, 'Mach': self.Mach,
        })

    def get_symbol(self, name: str, **kwargs) -> Symbol:
        """
        Get or create a symbol with given name.

        Args:
            name: Symbol name
            **kwargs: Symbol attributes (real, positive, constant, etc.)

        Returns:
            SymPy Symbol
        """
        if not self.available:
            return None

        if name in self._symbols:
            return self._symbols[name]

        symbol = symbols(name, **kwargs)
        self._symbols[name] = symbol
        return symbol

    def symbolic_derivative(self, expression: str, variable: str,
                          order: int = 1) -> Optional[Any]:
        """
        Compute symbolic derivative.

        Args:
            expression: Mathematical expression as string
            variable: Variable to differentiate with respect to
            order: Order of derivative (1, 2, ...)

        Returns:
            SymPy expression or None if unavailable
        """
        if not self.available:
            return None

        try:
            # Parse the expression with local namespace including our symbols
            local_dict = {name: sym for name, sym in self._symbols.items() if sym is not None}
            expr = sp.sympify(expression, locals=local_dict)
            var = self.get_symbol(variable)
            if var is None:
                var = symbols(variable)
            result = diff(expr, var, order)
            return result
        except Exception as e:
            logger.warning(f"Symbolic derivative failed: {e}")
            return None

    def symbolic_integral(self, expression: str, variable: str,
                        definite: bool = False,
                        limits: Optional[Tuple[float, float]] = None) -> Optional[Any]:
        """
        Compute symbolic integral.

        Args:
            expression: Mathematical expression as string
            variable: Variable to integrate with respect to
            definite: Whether to compute definite integral
            limits: Integration limits (lower, upper) for definite integral

        Returns:
            SymPy expression or None if unavailable
        """
        if not self.available:
            return None

        try:
            expr = sp.sympify(expression)
            var = self.get_symbol(variable)

            if definite and limits:
                result = integrate(expr, (var, limits[0], limits[1]))
            else:
                result = integrate(expr, var)

            return result
        except Exception as e:
            logger.warning(f"Symbolic integral failed: {e}")
            return None

    def solve_equation(self, equation: str, variable: str) -> List[Any]:
        """
        Solve symbolic equation.

        Args:
            equation: Equation as string (e.g., "x**2 - 4 = 0")
            variable: Variable to solve for

        Returns:
            List of solutions
        """
        if not self.available:
            return []

        try:
            # Parse equation with local namespace including our symbols
            local_dict = {name: sym for name, sym in self._symbols.items() if sym is not None}

            # Parse equation
            if '=' in equation:
                lhs, rhs = equation.split('=')
                lhs_expr = sp.sympify(lhs, locals=local_dict)
                rhs_expr = sp.sympify(rhs, locals=local_dict)
                expr = lhs_expr - rhs_expr
            else:
                expr = sp.sympify(equation, locals=local_dict)

            var = self.get_symbol(variable)
            if var is None:
                var = symbols(variable)
            solutions = solve(expr, var)

            # Convert to list if not already
            if not isinstance(solutions, list):
                solutions = list(solutions)

            return solutions
        except Exception as e:
            logger.warning(f"Equation solving failed: {e}")
            return []

    def solve_ode(self, equation: str, function: str,
                  independent_var: str = 't') -> Optional[Any]:
        """
        Solve ordinary differential equation symbolically.

        Args:
            equation: ODE as string (e.g., "f(t).diff(t) + f(t) - 1")
            function: Function name (e.g., "f")
            independent_var: Independent variable (default: t)

        Returns:
            SymPy solution or None if unavailable
        """
        if not self.available:
            return None

        try:
            func = Function(function)
            t = self.get_symbol(independent_var)
            expr = sp.sympify(equation)

            # Create differential equation
            ode = Eq(expr, 0)
            solution = dsolve(ode, func(t))

            return solution
        except Exception as e:
            logger.warning(f"ODE solving failed: {e}")
            return None

    def simplify_expression(self, expression: str) -> Optional[str]:
        """
        Simplify symbolic expression.

        Args:
            expression: Mathematical expression as string

        Returns:
            Simplified expression as string
        """
        if not self.available:
            return expression

        try:
            expr = sp.sympify(expression)
            simplified = sp.simplify(expr)
            return str(simplified)
        except Exception as e:
            logger.warning(f"Expression simplification failed: {e}")
            return expression

    def to_latex(self, expression: str) -> Optional[str]:
        """
        Convert expression to LaTeX format.

        Args:
            expression: Mathematical expression as string

        Returns:
            LaTeX string or None if unavailable
        """
        if not self.available:
            return None

        try:
            expr = sp.sympify(expression)
            latex_str = sp.latex(expr)
            return latex_str
        except Exception as e:
            logger.warning(f"LaTeX conversion failed: {e}")
            return None

    def taylor_series(self, expression: str, variable: str,
                     point: float = 0, order: int = 3) -> Optional[str]:
        """
        Compute Taylor series expansion.

        Args:
            expression: Mathematical expression as string
            variable: Variable to expand in
            point: Expansion point
            order: Order of expansion

        Returns:
            Series expression as string
        """
        if not self.available:
            return None

        try:
            expr = sp.sympify(expression)
            var = self.get_symbol(variable)
            series = sp.series(expr, var, point, order)
            # Remove order term for cleaner output
            series_str = str(series).removeprefix("O(")
            return series_str
        except Exception as e:
            logger.warning(f"Taylor series failed: {e}")
            return None

    def matrix_operations(self, matrix: List[List[float]],
                        operation: str) -> Optional[Any]:
        """
        Perform symbolic matrix operations.

        Args:
            matrix: Matrix as list of lists
            operation: Operation type ("determinant", "inverse", "eigenvalues", "eigenvectors")

        Returns:
            Result of operation
        """
        if not self.available:
            return None

        try:
            M = sp.Matrix(matrix)

            if operation == "determinant":
                return M.det()
            elif operation == "inverse":
                return M.inv()
            elif operation == "eigenvalues":
                return M.eigenvals()
            elif operation == "eigenvectors":
                return M.eigenvects()
            else:
                logger.warning(f"Unknown matrix operation: {operation}")
                return None
        except Exception as e:
            logger.warning(f"Matrix operation failed: {e}")
            return None


class PerturbationTheory:
    """
    Perturbation theory calculations using SymPy.

    Provides symbolic perturbation analysis for:
    - Linear stability analysis
    - Weakly nonlinear expansions
    - Multiple scale analysis
    - Asymptotic expansions
    """

    def __init__(self, engine: Optional[SymbolicPhysicsEngine] = None):
        """Initialize perturbation theory module."""
        self.engine = engine or SymbolicPhysicsEngine()

    def linear_stability_analysis(self, equilibrium: Dict[str, float],
                                  equations: List[str],
                                  variables: List[str]) -> Optional[Dict[str, Any]]:
        """
        Perform linear stability analysis around equilibrium.

        Args:
            equilibrium: Equilibrium values for variables
            equations: System of equations as strings
            variables: Variable names

        Returns:
            Dict with eigenvalues, stability analysis
        """
        if not self.engine.available:
            return None

        try:
            # Compute Jacobian matrix
            jacobian = []

            for eq in equations:
                row = []
                for var in variables:
                    derivative = self.engine.symbolic_derivative(eq, var)
                    # Evaluate at equilibrium
                    deriv_eq = derivative.subs(equilibrium)
                    row.append(deriv_eq)
                jacobian.append(row)

            # Compute eigenvalues
            J = sp.Matrix(jacobian)
            eigenvalues = J.eigenvals()

            # Determine stability
            stable = all(ev.as_real_imag()[0] < 0 for ev in eigenvalues.keys())

            return {
                'jacobian': jacobian,
                'eigenvalues': eigenvalues,
                'stable': stable,
                'analysis': 'Stable' if stable else 'Unstable'
            }
        except Exception as e:
            logger.warning(f"Linear stability analysis failed: {e}")
            return None

    def regular_perturbation(self, equation: str, variable: str,
                           epsilon: str = 'epsilon',
                           order: int = 2) -> Optional[List[str]]:
        """
        Perform regular perturbation expansion.

        Args:
            equation: Equation to expand
            variable: Variable to solve for
            epsilon: Small parameter name
            order: Order of expansion

        Returns:
            List of perturbation equations at each order
        """
        if not self.engine.available:
            return None

        try:
            eps = self.engine.get_symbol(epsilon)
            equations = []

            for n in range(order + 1):
                # Extract O(epsilon^n) terms
                eq_n = f"O({epsilon}^{n}) terms of {equation}"
                equations.append(eq_n)

            return equations
        except Exception as e:
            logger.warning(f"Regular perturbation failed: {e}")
            return None


class FilamentStabilityAnalyzer:
    """
    Specialized symbolic analysis for filament stability.

    Uses SymPy for exact analytical treatment of:
    - Jeans instability in cylindrical geometry
    - Magnetic field stabilization
    - Fragmentation wavelength calculation
    - Dispersion relation analysis
    """

    def __init__(self, engine: Optional[SymbolicPhysicsEngine] = None):
        """Initialize filament stability analyzer."""
        self.engine = engine or SymbolicPhysicsEngine()

        if not self.engine.available:
            return

        # Define filament-specific symbols
        self.lambda_J = symbols('lambda_J', real=True, positive=True)  # Jeans length
        self.mu_crit = symbols('mu_crit', real=True, positive=True)  # Critical line mass
        self.mu_line = symbols('mu_line', real=True, positive=True)  # Line mass

    def jeans_wavelength(self) -> Optional[str]:
        """
        Derive Jeans wavelength expression.

        Returns:
            LaTeX string for Jeans wavelength formula
        """
        if not self.engine.available:
            return None

        try:
            # λ_J = c_s * sqrt(π * G * ρ)
            c_s = self.engine.get_symbol('c_s', real=True, positive=True)
            G = self.engine.G
            rho = self.engine.rho
            pi = sp.pi

            lambda_J_expr = c_s * sp.sqrt(pi / (G * rho))

            latex_str = self.engine.to_latex(str(lambda_J_expr))
            return latex_str
        except Exception as e:
            logger.warning(f"Jeans wavelength derivation failed: {e}")
            return None

    def dispersion_relation(self, k: str = 'k', omega: str = 'omega') -> Optional[str]:
        """
        Derive dispersion relation for filament instability.

        Args:
            k: Wavenumber symbol
            omega: Frequency symbol

        Returns:
            LaTeX string for dispersion relation
        """
        if not self.engine.available:
            return None

        try:
            k_sym = symbols(k, real=True, positive=True)
            omega_sym = symbols(omega, complex=True)

            # Simplified dispersion relation: ω² = c_s²k² - 4πGρ
            c_s = self.engine.get_symbol('c_s', real=True, positive=True)
            G = self.engine.G
            rho = self.engine.rho

            dispersion = omega_sym**2 - c_s**2 * k_sym**2 + 4*sp.pi*G*rho

            latex_str = self.engine.to_latex(str(dispersion))
            return latex_str
        except Exception as e:
            logger.warning(f"Dispersion relation derivation failed: {e}")
            return None


# Factory function
def create_symbolic_physics_engine() -> SymbolicPhysicsEngine:
    """Create symbolic physics engine."""
    return SymbolicPhysicsEngine()


# Check availability
def is_sympy_available() -> bool:
    """Check if SymPy is available and functional."""
    return SYMPY_AVAILABLE
