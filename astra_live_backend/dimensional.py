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
ASTRA Live — Dimensional Analysis Engine
Implements Buckingham π theorem for discovering dimensionless parameters
and validating physical relationships.

As described in White & Dey (2026), Section 2.3 and Test Case 1.
"""
import numpy as np
from itertools import combinations
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


# Fundamental dimensions: M, L, T, Θ, I (mass, length, time, temperature, current)
DIMENSION_MAP = {
    'mass': [1, 0, 0, 0, 0],
    'length': [0, 1, 0, 0, 0],
    'time': [0, 0, 1, 0, 0],
    'temperature': [0, 0, 0, 1, 0],
    'current': [0, 0, 0, 0, 1],
    'velocity': [0, 1, -1, 0, 0],  # L/T
    'acceleration': [0, 1, -2, 0, 0],  # L/T²
    'force': [1, 1, -2, 0, 0],  # ML/T²
    'energy': [1, 2, -2, 0, 0],  # ML²/T²
    'power': [1, 2, -3, 0, 0],  # ML²/T³
    'density': [1, -3, 0, 0, 0],  # M/L³
    'pressure': [1, -1, -2, 0, 0],  # M/(LT²)
    'frequency': [0, 0, -1, 0, 0],  # 1/T
    'angular_momentum': [1, 2, -1, 0, 0],  # ML²/T
    'flux': [1, 0, -3, 0, 0],  # M/T³ (energy flux)
    'luminosity': [1, 2, -3, 0, 0],  # ML²/T³
    'column_density': [1, -2, 0, 0, 0],  # M/L²
    'mass_per_length': [1, -1, 0, 0, 0],  # M/L
    'dimensionless': [0, 0, 0, 0, 0],
}

# Common astronomical quantities with their dimensions
ASTRO_DIMENSIONS = {
    'mass': 'mass',
    'length': 'length',
    'radius': 'length',
    'distance': 'length',
    'velocity': 'velocity',
    'velocity_dispersion': 'velocity',
    'sigma_v': 'velocity',
    'time': 'time',
    'period': 'time',
    'density': 'density',
    'temperature': 'temperature',
    'luminosity': 'luminosity',
    'flux': 'flux',
    'force': 'force',
    'energy': 'energy',
    'mass_per_length': 'mass_per_length',
    'column_density': 'column_density',
    'pressure': 'pressure',
    'frequency': 'frequency',
    'acceleration': 'acceleration',
}


@dataclass
class DimensionlessGroup:
    """A dimensionless π group discovered by Buckingham π theorem."""
    name: str
    variables: List[str]
    exponents: List[float]
    formula: str
    physical_interpretation: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ScalingRelation:
    """A discovered power-law scaling relation y ∝ x^α."""
    y_variable: str
    x_variable: str
    exponent: float
    exponent_error: float
    intercept: float
    r_squared: float
    p_value: float
    n_points: int
    dimensionless: bool = False

    def to_dict(self):
        return asdict(self)


def buckingham_pi(variables: Dict[str, str]) -> List[DimensionlessGroup]:
    """
    Apply Buckingham π theorem to find dimensionless groups.

    Args:
        variables: dict mapping variable names to their dimension types
                   e.g., {'mass': 'mass', 'velocity': 'velocity', 'length': 'length'}

    Returns list of dimensionless π groups.
    """
    # Build dimension matrix
    var_names = list(variables.keys())
    dim_matrix = []
    for var in var_names:
        dim_type = variables[var]
        if dim_type in DIMENSION_MAP:
            dim_matrix.append(DIMENSION_MAP[dim_type])
        elif dim_type in ASTRO_DIMENSIONS:
            dim_matrix.append(DIMENSION_MAP[ASTRO_DIMENSIONS[dim_type]])
        else:
            dim_matrix.append([0, 0, 0, 0, 0])  # assume dimensionless

    dim_matrix = np.array(dim_matrix, dtype=float)  # shape: (n_vars, 5)

    if dim_matrix.shape[0] == 0:
        return []

    # Find null space of dimension matrix to get dimensionless combinations
    # π = v₁^a₁ * v₂^a₂ * ... where dim_matrix.T @ [a₁, a₂, ...] = 0
    U, S, Vt = np.linalg.svd(dim_matrix.T, full_matrices=True)

    # Null space vectors are rows of Vt corresponding to zero (or near-zero) singular values
    rank = np.sum(S > 1e-10)
    null_dim = dim_matrix.shape[1] - rank  # number of fundamental dimensions used

    if null_dim == 0:
        return []  # No dimensionless groups possible

    null_vectors = Vt[rank:]  # Each row is a dimensionless combination

    groups = []
    for i, vec in enumerate(null_vectors):
        # Round exponents to simple fractions
        exponents = [round(v, 3) for v in vec]
        if all(abs(e) < 0.01 for e in exponents):
            continue

        # Build formula string
        parts = []
        for var, exp in zip(var_names, exponents):
            if abs(exp) > 0.01:
                if abs(exp - 1.0) < 0.01:
                    parts.append(var)
                else:
                    parts.append(f"{var}^{exp:.3f}")

        formula = " × ".join(parts) if parts else "1"

        # Physical interpretation heuristics
        interpretation = _interpret_pi_group(var_names, exponents)

        groups.append(DimensionlessGroup(
            name=f"π{i+1}",
            variables=var_names,
            exponents=exponents,
            formula=formula,
            physical_interpretation=interpretation,
        ))

    return groups


def _interpret_pi_group(var_names: List[str], exponents: List[float]) -> str:
    """Try to interpret a dimensionless group physically."""
    var_exp = {v: e for v, e in zip(var_names, exponents) if abs(e) > 0.01}

    # Virial parameter: σ²L/(GM) or σ²/(GM/L)
    if 'velocity' in var_exp or 'sigma_v' in var_exp or 'velocity_dispersion' in var_exp:
        if 'mass' in var_exp and ('length' in var_exp or 'radius' in var_exp):
            return "Virial parameter (gravitational binding ratio)"

    # Mach number: v/c_sound
    if 'velocity' in var_exp and len(var_exp) == 1:
        return "Velocity ratio (Mach-like)"

    # Reynolds number: ρvL/μ
    if 'density' in var_exp and 'velocity' in var_exp and 'length' in var_exp:
        return "Reynolds-like number (inertial/viscous)"

    return "Dimensionless parameter"


def discover_scaling_relations(x_data: np.ndarray, y_data: np.ndarray,
                                x_name: str = "x", y_name: str = "y",
                                x_dim: str = "", y_dim: str = "") -> ScalingRelation:
    """
    Discover power-law scaling relation y ∝ x^α using log-log regression.

    Also checks dimensional consistency if dimensions are provided.
    """
    # Filter positive values
    valid = (x_data > 0) & (y_data > 0) & np.isfinite(x_data) & np.isfinite(y_data)
    x = x_data[valid]
    y = y_data[valid]

    if len(x) < 3:
        return ScalingRelation(y_name, x_name, 0, 0, 0, 0, 1, len(x))

    # Log-log regression
    log_x = np.log10(x)
    log_y = np.log10(y)

    # OLS in log space
    n = len(log_x)
    X = np.column_stack([np.ones(n), log_x])
    beta = np.linalg.lstsq(X, log_y, rcond=None)[0]
    intercept, slope = beta

    # R²
    y_pred = X @ beta
    ss_res = np.sum((log_y - y_pred)**2)
    ss_tot = np.sum((log_y - np.mean(log_y))**2)
    r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    # Bootstrap uncertainty on slope
    n_boot = 1000
    slopes = []
    for _ in range(n_boot):
        idx = np.random.choice(n, n, replace=True)
        X_b = X[idx]
        y_b = log_y[idx]
        try:
            b = np.linalg.lstsq(X_b, y_b, rcond=None)[0]
            slopes.append(b[1])
        except:
            pass
    slope_err = np.std(slopes) if slopes else 0.1

    # p-value for slope (H0: slope = 0)
    t_stat = slope / slope_err if slope_err > 0 else 0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=max(n-2, 1)))

    return ScalingRelation(
        y_variable=y_name,
        x_variable=x_name,
        exponent=float(slope),
        exponent_error=float(slope_err),
        intercept=float(intercept),
        r_squared=float(r_sq),
        p_value=float(p_value),
        n_points=len(x),
        dimensionless=False,
    )


def check_dimensional_consistency(exponent: float, y_dim: str, x_dim: str) -> Dict:
    """
    Check if a discovered power-law exponent is dimensionally consistent.

    If y ∝ x^α, then [y] = [x]^α must hold dimensionally.
    """
    y_dims = DIMENSION_MAP.get(y_dim, DIMENSION_MAP.get(ASTRO_DIMENSIONS.get(y_dim, 'dimensionless'), [0]*5))
    x_dims = DIMENSION_MAP.get(x_dim, DIMENSION_MAP.get(ASTRO_DIMENSIONS.get(x_dim, 'dimensionless'), [0]*5))

    expected_dims = [d * exponent for d in x_dims]
    dim_match = np.allclose(y_dims, expected_dims, atol=0.1)

    return {
        "consistent": dim_match,
        "y_dimensions": y_dims,
        "expected_dimensions": expected_dims,
        "exponent": exponent,
        "dimension_residual": [y - e for y, e in zip(y_dims, expected_dims)],
    }
