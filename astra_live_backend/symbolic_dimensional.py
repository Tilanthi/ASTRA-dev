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
ASTRA Live — Symbolic Dimensional Analysis Generator
Extends ASTRA's existing dimensional analysis (dimensional.py) from a
validator into a generator of candidate physical equations.

Uses SymPy for symbolic algebra when available; falls back gracefully
to numpy-only operations otherwise.

New capabilities
-----------------
1. BuckinghamPiGenerator  — Enumerates ALL valid π groups via null-space
                            computation of the dimension matrix (not just
                            the SVD-based subset in dimensional.py).
2. ScalingRelationGenerator — Derives candidate power-law scaling relations
                              as SymPy expressions from π groups.
3. UniversalExponentMatcher — Tests whether an observed exponent α is close
                              to a known universal value and provides physical
                              interpretation.
4. CandidateEquationSet    — Collects candidate equations with provenance.

Compatibility
-------------
The existing `discover_scaling_relations` and `buckingham_pi` functions in
dimensional.py are NOT modified. This module imports and wraps them, adding
new generator-level functionality on top.

As described in White & Dey (2026), Section 3.3: Symbolic Dimensional Engine.
"""
from __future__ import annotations

import subprocess
import sys
import time
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# ---------------------------------------------------------------------------
# SymPy availability — try to import; auto-install if missing
# ---------------------------------------------------------------------------

def _ensure_sympy() -> bool:
    """Attempt to import sympy; install via pip if absent. Returns True on success."""
    try:
        import sympy  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "sympy"],
            timeout=120,
        )
        import sympy  # noqa: F401
        return True
    except Exception:
        return False


SYMPY_AVAILABLE = _ensure_sympy()

if SYMPY_AVAILABLE:
    import sympy as sp
    from sympy import symbols, Rational, simplify, latex, nsimplify
    from sympy.matrices import Matrix
else:
    sp = None  # type: ignore

# ---------------------------------------------------------------------------
# Import existing dimensional analysis tools (non-breaking)
# ---------------------------------------------------------------------------

try:
    from .dimensional import (
        DIMENSION_MAP,
        ASTRO_DIMENSIONS,
        DimensionlessGroup,
        ScalingRelation,
        buckingham_pi as _legacy_buckingham_pi,
        discover_scaling_relations,
        check_dimensional_consistency,
    )
    _DIMENSIONAL_AVAILABLE = True
except ImportError:
    # Standalone usage: replicate minimal DIMENSION_MAP
    _DIMENSIONAL_AVAILABLE = False
    DIMENSION_MAP = {
        'mass':          [1, 0, 0, 0, 0],
        'length':        [0, 1, 0, 0, 0],
        'time':          [0, 0, 1, 0, 0],
        'temperature':   [0, 0, 0, 1, 0],
        'current':       [0, 0, 0, 0, 1],
        'velocity':      [0, 1, -1, 0, 0],
        'acceleration':  [0, 1, -2, 0, 0],
        'force':         [1, 1, -2, 0, 0],
        'energy':        [1, 2, -2, 0, 0],
        'power':         [1, 2, -3, 0, 0],
        'density':       [1, -3, 0, 0, 0],
        'pressure':      [1, -1, -2, 0, 0],
        'frequency':     [0, 0, -1, 0, 0],
        'angular_momentum': [1, 2, -1, 0, 0],
        'flux':          [1, 0, -3, 0, 0],
        'luminosity':    [1, 2, -3, 0, 0],
        'column_density': [1, -2, 0, 0, 0],
        'mass_per_length': [1, -1, 0, 0, 0],
        'dimensionless': [0, 0, 0, 0, 0],
    }
    ASTRO_DIMENSIONS = {
        'mass': 'mass', 'length': 'length', 'radius': 'length',
        'distance': 'length', 'velocity': 'velocity',
        'velocity_dispersion': 'velocity', 'sigma_v': 'velocity',
        'time': 'time', 'period': 'time', 'density': 'density',
        'temperature': 'temperature', 'luminosity': 'luminosity',
        'flux': 'flux', 'force': 'force', 'energy': 'energy',
        'mass_per_length': 'mass_per_length',
        'column_density': 'column_density', 'pressure': 'pressure',
        'frequency': 'frequency', 'acceleration': 'acceleration',
    }

    @dataclass
    class DimensionlessGroup:  # type: ignore[no-redef]
        name: str
        variables: List[str]
        exponents: List[float]
        formula: str
        physical_interpretation: str

    @dataclass
    class ScalingRelation:  # type: ignore[no-redef]
        y_variable: str
        x_variable: str
        exponent: float
        exponent_error: float
        intercept: float
        r_squared: float
        p_value: float
        n_points: int
        dimensionless: bool = False

    def _legacy_buckingham_pi(variables):
        return []


# ---------------------------------------------------------------------------
# Universal exponents catalogue
# ---------------------------------------------------------------------------

#: (value, rational_repr, physical_interpretation)
UNIVERSAL_EXPONENTS: List[Tuple[float, str, str]] = [
    (1/3,    "1/3",  "Jeans/Kolmogorov 1/3 — turbulent energy cascade or Jeans fragmentation"),
    (1/2,    "1/2",  "Square-root scaling — diffusion, virial equilibrium (σ ∝ R^1/2)"),
    (2/3,    "2/3",  "Larson 2/3 — velocity dispersion–size relation in molecular clouds"),
    (3/4,    "3/4",  "Kleiber's law — metabolic rate ∝ mass^3/4"),
    (1.0,    "1",    "Linear — direct proportionality"),
    (4/3,    "4/3",  "Adiabatic index — polytropic EOS, radiation pressure"),
    (3/2,    "3/2",  "Kepler's third law — T ∝ a^3/2"),
    (2.0,    "2",    "Quadratic — area, kinetic energy ∝ v^2, Jeans mass ∝ T^2"),
    (3.0,    "3",    "Cubic — volume, density contrast"),
    (5/2,    "5/2",  "Salpeter IMF power-law index (Γ = 2.35 ≈ 7/3)"),
    (-1.0,   "-1",   "Inverse — gravitational potential, 1/r"),
    (-2.0,   "-2",   "Inverse square — flux, gravity, Coulomb"),
    (-1/3,   "-1/3", "Negative Kolmogorov — density power spectrum"),
    (-1/2,   "-1/2", "Inverse square-root — diffusion time, reciprocal virial"),
    (-3/2,   "-3/2", "Kepler velocity — orbital velocity ∝ r^{-1/2} (energy ∝ r^{-1})"),
    (-2/3,   "-2/3", "Inverse Larson — specific angular momentum scaling"),
    (5/3,    "5/3",  "Kolmogorov energy spectrum E(k) ∝ k^{-5/3}"),
    (-5/3,   "-5/3", "Kolmogorov power spectrum (negative)"),
    (7/3,    "7/3",  "Salpeter IMF slope ≈ 7/3"),
    (0.0,    "0",    "Constant — no dependence"),
]


# ---------------------------------------------------------------------------
# UniversalExponentMatcher
# ---------------------------------------------------------------------------

class UniversalExponentMatcher:
    """
    Given an observed power-law exponent α, find the closest known
    universal value and return its physical interpretation.

    Examples
    --------
    >>> m = UniversalExponentMatcher()
    >>> result = m.match(0.667)
    >>> result['rational']
    '2/3'
    >>> result['interpretation']
    'Larson 2/3 — velocity dispersion–size relation in molecular clouds'
    """

    def __init__(self, tolerance: float = 0.05):
        """
        Parameters
        ----------
        tolerance : float
            Maximum absolute difference to call a match "close".
        """
        self.tolerance = tolerance

    def match(self, alpha: float) -> Dict[str, Any]:
        """
        Match α to the nearest universal exponent.

        Returns
        -------
        Dict with keys:
            'observed'       : float, the input exponent
            'closest_value'  : float, best-matching universal exponent
            'rational'       : str, e.g. "2/3"
            'delta'          : float, |observed - closest|
            'is_close'       : bool, within tolerance
            'interpretation' : str
            'all_matches'    : list of (value, rational, interp, delta) sorted by delta
        """
        scored = sorted(
            [(abs(alpha - v), v, r, i) for v, r, i in UNIVERSAL_EXPONENTS],
            key=lambda x: x[0],
        )
        best_delta, best_val, best_rat, best_interp = scored[0]
        return {
            "observed":      alpha,
            "closest_value": best_val,
            "rational":      best_rat,
            "delta":         best_delta,
            "is_close":      best_delta <= self.tolerance,
            "interpretation": best_interp,
            "all_matches":   [(v, r, i, d) for d, v, r, i in scored[:5]],
        }

    def match_many(self, alphas: List[float]) -> List[Dict[str, Any]]:
        """Match a list of exponents."""
        return [self.match(a) for a in alphas]


# ---------------------------------------------------------------------------
# BuckinghamPiGenerator
# ---------------------------------------------------------------------------

class BuckinghamPiGenerator:
    """
    Enumerate ALL valid dimensionless π groups for a given set of variables
    using explicit null-space computation of the dimension matrix.

    This is more rigorous than the SVD-based approach in dimensional.py:
    it uses SymPy's exact rational arithmetic (when available) to avoid
    floating-point truncation errors, and returns a complete basis.

    Parameters
    ----------
    variables : Dict[str, str]
        Mapping of variable name → dimension type string.
        Dimension types must be keys in DIMENSION_MAP or ASTRO_DIMENSIONS.

    Examples
    --------
    >>> gen = BuckinghamPiGenerator({'velocity': 'velocity',
    ...                              'length': 'length',
    ...                              'time': 'time'})
    >>> groups = gen.generate()
    """

    def __init__(self, variables: Dict[str, str]):
        self.variables = variables
        self._groups: Optional[List[DimensionlessGroup]] = None

    def _build_dim_matrix(self) -> np.ndarray:
        """Build the (n_vars × 5) dimension matrix."""
        rows = []
        for var, dim_type in self.variables.items():
            dim_type_resolved = ASTRO_DIMENSIONS.get(dim_type, dim_type)
            row = DIMENSION_MAP.get(dim_type_resolved, [0, 0, 0, 0, 0])
            rows.append(row)
        return np.array(rows, dtype=float)  # (n_vars, 5)

    def _null_space_numpy(self, mat: np.ndarray) -> np.ndarray:
        """Compute null space of mat.T using numpy SVD."""
        U, S, Vt = np.linalg.svd(mat.T, full_matrices=True)
        rank = int(np.sum(S > 1e-10))
        if rank >= Vt.shape[0]:
            return np.zeros((0, mat.shape[0]))
        return Vt[rank:]  # rows are null-space basis vectors

    def _null_space_sympy(self, mat: np.ndarray) -> np.ndarray:
        """Compute exact null space via SymPy integer arithmetic."""
        if not SYMPY_AVAILABLE:
            return self._null_space_numpy(mat)
        # Convert to SymPy rational matrix
        rows, cols = mat.shape
        sp_mat = Matrix([[Rational(int(round(mat[r, c] * 6)), 6)
                          for c in range(cols)]
                         for r in range(rows)])
        null = sp_mat.T.nullspace()
        if not null:
            return np.zeros((0, cols))
        result = np.array([[float(v) for v in vec] for vec in null], dtype=float)
        return result

    def generate(self, use_sympy: bool = True) -> List[DimensionlessGroup]:
        """
        Generate all dimensionless π groups.

        Parameters
        ----------
        use_sympy : bool
            Use SymPy for exact rational arithmetic if available.
        """
        if self._groups is not None:
            return self._groups

        var_names = list(self.variables.keys())
        dim_mat = self._build_dim_matrix()

        if use_sympy and SYMPY_AVAILABLE:
            null_vecs = self._null_space_sympy(dim_mat)
        else:
            null_vecs = self._null_space_numpy(dim_mat)

        groups: List[DimensionlessGroup] = []
        for i, vec in enumerate(null_vecs):
            exponents = [float(round(v, 4)) for v in vec]
            if all(abs(e) < 1e-9 for e in exponents):
                continue
            # Normalise so the largest |exponent| = 1
            max_abs = max(abs(e) for e in exponents)
            if max_abs > 1e-9:
                exponents = [e / max_abs for e in exponents]
                exponents = [float(round(e, 4)) for e in exponents]

            parts = []
            for var, exp in zip(var_names, exponents):
                if abs(exp) > 1e-3:
                    if abs(exp - 1.0) < 1e-3:
                        parts.append(var)
                    else:
                        parts.append(f"{var}^{exp:.4g}")

            formula = " × ".join(parts) if parts else "1"
            interpretation = self._interpret(var_names, exponents)

            groups.append(DimensionlessGroup(
                name=f"π{i+1}",
                variables=var_names,
                exponents=exponents,
                formula=formula,
                physical_interpretation=interpretation,
            ))

        self._groups = groups
        return groups

    @staticmethod
    def _interpret(var_names: List[str], exponents: List[float]) -> str:
        """Heuristic physical interpretation of a π group."""
        ve = {v: e for v, e in zip(var_names, exponents) if abs(e) > 1e-3}
        vel_vars = {'velocity', 'sigma_v', 'velocity_dispersion'}
        if vel_vars & set(ve) and 'mass' in ve and \
           ('length' in ve or 'radius' in ve or 'distance' in ve):
            return "Virial parameter (kinetic/gravitational energy ratio)"
        if vel_vars & set(ve) and len(ve) == 1:
            return "Velocity ratio (Mach-like)"
        if 'density' in ve and vel_vars & set(ve) and \
           ('length' in ve or 'radius' in ve):
            return "Reynolds-like number (inertial/viscous forces)"
        if 'pressure' in ve and 'density' in ve and vel_vars & set(ve):
            return "Bernoulli-like parameter (dynamic vs static pressure)"
        if 'luminosity' in ve and 'mass' in ve:
            return "Mass-to-light ratio (stellar population)"
        if 'time' in ve or 'period' in ve:
            return "Dimensionless time / frequency ratio"
        return "Dimensionless combination"


# ---------------------------------------------------------------------------
# ScalingRelationGenerator
# ---------------------------------------------------------------------------

@dataclass
class SymbolicScalingRelation:
    """A candidate power-law scaling relation derived from π groups."""
    y_variable: str
    x_variable: str
    exponent: float
    exponent_rational: str          # e.g. "2/3"
    sympy_expr: Optional[str]       # LaTeX string if SymPy available
    provenance: str                 # Which π groups this came from
    universal_match: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "y_variable":        self.y_variable,
            "x_variable":        self.x_variable,
            "exponent":          self.exponent,
            "exponent_rational": self.exponent_rational,
            "sympy_expr":        self.sympy_expr,
            "provenance":        self.provenance,
            "universal_match":   self.universal_match,
        }


class ScalingRelationGenerator:
    """
    Derive candidate power-law scaling relations from π groups.

    Given a set of dimensionless groups, construct equations of the form
    π₁ = f(π₂, π₃, …) and solve for individual variable exponents.

    Parameters
    ----------
    variables : Dict[str, str]
        Variable name → dimension type mapping.
    """

    def __init__(self, variables: Dict[str, str]):
        self.gen = BuckinghamPiGenerator(variables)
        self._matcher = UniversalExponentMatcher()

    def generate(self) -> List[SymbolicScalingRelation]:
        """Generate all candidate scaling relations from π groups."""
        groups = self.gen.generate()
        relations: List[SymbolicScalingRelation] = []
        var_names = list(self.gen.variables.keys())

        for group in groups:
            # For each variable with a non-zero exponent, attempt to solve
            # for it in terms of the others: y ∝ x^α
            ve = [(v, e) for v, e in zip(group.variables, group.exponents)
                  if abs(e) > 1e-3]
            if len(ve) < 2:
                continue

            for k, (y_var, y_exp) in enumerate(ve):
                for x_var, x_exp in ve:
                    if x_var == y_var:
                        continue
                    if abs(y_exp) < 1e-9:
                        continue
                    # From π: y^y_exp × x^x_exp × … = const
                    # Isolate y: y ∝ x^(-x_exp / y_exp)
                    raw_exp = -x_exp / y_exp
                    match = self._matcher.match(raw_exp)
                    # Build rational string
                    rational_str = match["rational"] if match["is_close"] else f"{raw_exp:.4g}"
                    # Build SymPy expression if available
                    sympy_expr = None
                    if SYMPY_AVAILABLE:
                        try:
                            y_sym = sp.Symbol(y_var)
                            x_sym = sp.Symbol(x_var)
                            exp_rat = nsimplify(raw_exp, rational=True, tolerance=0.05)
                            expr = sp.Eq(y_sym, x_sym ** exp_rat)
                            sympy_expr = latex(expr)
                        except Exception:
                            sympy_expr = f"{y_var} ∝ {x_var}^{raw_exp:.4g}"

                    relations.append(SymbolicScalingRelation(
                        y_variable=y_var,
                        x_variable=x_var,
                        exponent=raw_exp,
                        exponent_rational=rational_str,
                        sympy_expr=sympy_expr,
                        provenance=f"Derived from {group.name}: {group.formula}",
                        universal_match=match if match["is_close"] else None,
                    ))

        return relations


# ---------------------------------------------------------------------------
# CandidateEquationSet
# ---------------------------------------------------------------------------

@dataclass
class CandidateEquation:
    """A candidate physical equation with dimensional derivation provenance."""
    id: str
    equation_str: str           # Human-readable, e.g. "sigma_v ∝ R^(2/3)"
    sympy_expr: Optional[str]   # LaTeX or None
    variables: List[str]
    exponent: float
    exponent_rational: str
    pi_group_provenance: str    # Which π group it came from
    universal_match: Optional[Dict]
    confidence: float = 0.5     # Prior; updated by data comparison
    tested: bool = False
    test_r_squared: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        d = {
            "id":                   self.id,
            "equation_str":         self.equation_str,
            "sympy_expr":           self.sympy_expr,
            "variables":            self.variables,
            "exponent":             self.exponent,
            "exponent_rational":    self.exponent_rational,
            "pi_group_provenance":  self.pi_group_provenance,
            "universal_match":      self.universal_match,
            "confidence":           self.confidence,
            "tested":               self.tested,
            "test_r_squared":       self.test_r_squared,
            "created_at":           self.created_at,
        }
        return d


class CandidateEquationSet:
    """
    Collection of candidate equations generated from dimensional analysis,
    with their dimensional derivation provenance.

    Wraps BuckinghamPiGenerator and ScalingRelationGenerator to provide a
    clean interface for the ASTRA engine.
    """

    def __init__(self):
        self._equations: Dict[str, CandidateEquation] = {}
        self._next_id: int = 1

    def generate_from_variables(self, variables: Dict[str, str]) -> List[CandidateEquation]:
        """
        Generate candidate equations from a set of variables.

        Parameters
        ----------
        variables : Dict[str, str]
            Variable name → dimension type (same format as buckingham_pi).

        Returns
        -------
        List[CandidateEquation]
        """
        gen = ScalingRelationGenerator(variables)
        relations = gen.generate()
        new_eqs: List[CandidateEquation] = []
        for rel in relations:
            eid = f"CE{self._next_id:04d}"
            self._next_id += 1
            eq_str = (f"{rel.y_variable} ∝ {rel.x_variable}"
                      f"^({rel.exponent_rational})")
            eq = CandidateEquation(
                id=eid,
                equation_str=eq_str,
                sympy_expr=rel.sympy_expr,
                variables=[rel.y_variable, rel.x_variable],
                exponent=rel.exponent,
                exponent_rational=rel.exponent_rational,
                pi_group_provenance=rel.provenance,
                universal_match=rel.universal_match,
                confidence=0.3 + 0.2 * (1.0 if rel.universal_match else 0.0),
            )
            self._equations[eid] = eq
            new_eqs.append(eq)
        return new_eqs

    def all(self) -> List[CandidateEquation]:
        return list(self._equations.values())

    def by_variable_pair(self, y: str, x: str) -> List[CandidateEquation]:
        return [eq for eq in self._equations.values()
                if eq.variables[0] == y and eq.variables[1] == x]

    def to_json(self) -> str:
        return json.dumps([eq.to_dict() for eq in self._equations.values()], indent=2)


# ---------------------------------------------------------------------------
# Convenience re-exports for compatibility with existing callers
# ---------------------------------------------------------------------------

__all__ = [
    # New generator classes
    "BuckinghamPiGenerator",
    "ScalingRelationGenerator",
    "UniversalExponentMatcher",
    "CandidateEquationSet",
    "CandidateEquation",
    "SymbolicScalingRelation",
    "UNIVERSAL_EXPONENTS",
    "SYMPY_AVAILABLE",
    # Re-exported from dimensional.py (if available)
    "DIMENSION_MAP",
    "ASTRO_DIMENSIONS",
    "DimensionlessGroup",
    "ScalingRelation",
]

# Only re-export legacy functions if they were successfully imported
if _DIMENSIONAL_AVAILABLE:
    __all__ += [
        "discover_scaling_relations",
        "check_dimensional_consistency",
    ]
