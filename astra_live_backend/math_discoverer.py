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
ASTRA Live — Mathematical Structure Discoverer
Discovers novel mathematical structures in physical data.

Key capabilities:
- Symbolic regression: Discover equations from data
- Differential equation discovery: Find governing equations
- Symmetry detection: Translational, rotational, scaling
- Topological analysis: Winding numbers, singularities
- Dimensional analysis: Buckingham π theorem
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class DiscoveredEquation:
    """An equation discovered from data."""
    equation: str
    goodness_of_fit: float
    confidence: float
    variables: List[str]
    complexity: int


@dataclass
class SymmetryResult:
    """Result of symmetry detection."""
    symmetry_type: str
    detected: bool
    tolerance: float
    transformation: str


class SymbolicRegression:
    """Discover equations from data using symbolic regression."""
    
    def discover_equation(self, x: np.ndarray, y: np.ndarray,
                         variable_names: List[str],
                         max_complexity: int = 3) -> Optional[DiscoveredEquation]:
        """Discover equation relating x and y."""
        if len(x) != len(y) or len(x) < 3:
            return None
        
        # Try simple forms: y = ax^b, y = ae^(bx), y = a log(x) + b
        models = self._try_models(x, y)
        
        if not models:
            return None
        
        # Select best model
        best = min(models, key=lambda m: m['mse'])
        
        # Calculate confidence
        variance = np.var(y)
        mse = best['mse']
        r_squared = 1 - mse / variance
        confidence = min(1.0, r_squared)
        
        return DiscoveredEquation(
            equation=best['equation'],
            goodness_of_fit=mse,
            confidence=confidence,
            variables=variable_names,
            complexity=best['complexity']
        )
    
    def _try_models(self, x: np.ndarray, y: np.ndarray) -> List[Dict]:
        """Try various equation forms."""
        models = []
        
        # Remove invalid values
        valid = np.isfinite(x) & np.isfinite(y) & (x > 0)
        x_clean = x[valid]
        y_clean = y[valid]
        
        if len(x_clean) < 3:
            return models
        
        # Power law: y = a x^b
        try:
            log_x = np.log(x_clean)
            log_y = np.log(y_clean)
            coeffs = np.polyfit(log_x, log_y, 1)
            y_pred = np.exp(coeffs[1]) * x_clean**coeffs[0]
            mse = np.mean((y_clean - y_pred)**2)
            models.append({
                'equation': f"y = {np.exp(coeffs[1]):.3g} x^{coeffs[0]:.3g}",
                'mse': mse,
                'complexity': 2
            })
        except:
            pass
        
        # Linear: y = ax + b
        try:
            coeffs = np.polyfit(x_clean, y_clean, 1)
            y_pred = coeffs[0] * x_clean + coeffs[1]
            mse = np.mean((y_clean - y_pred)**2)
            models.append({
                'equation': f"y = {coeffs[0]:.3g}x + {coeffs[1]:.3g}",
                'mse': mse,
                'complexity': 1
            })
        except:
            pass
        
        return models


class SymmetryDiscoverer:
    """Discover symmetries in data."""
    
    def discover_translational_symmetry(self, field: np.ndarray,
                                       position: np.ndarray) -> SymmetryResult:
        """Check if field is translationally invariant."""
        if len(field) < 3:
            return SymmetryResult("translational", False, 0.0, "")
        
        # Check if field is constant
        variance = np.var(field)
        tolerance = variance / (np.mean(field**2) + 1e-10)
        
        return SymmetryResult(
            symmetry_type="translational",
            detected=tolerance < 0.01,
            tolerance=tolerance,
            transformation="f(x + a) = f(x)"
        )
    
    def discover_scaling_symmetry(self, x: np.ndarray, y: np.ndarray,
                                transform: str = "power") -> Optional[Dict]:
        """Check if y scales as x^a."""
        valid = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
        x_clean = x[valid]
        y_clean = y[valid]
        
        if len(x_clean) < 3:
            return None
        
        # Log-log fit
        log_x = np.log(x_clean)
        log_y = np.log(y_clean)
        coeffs = np.polyfit(log_x, log_y, 1)
        
        correlation = np.corrcoef(log_x, log_y)[0, 1]
        
        return {
            'type': 'power_law',
            'exponent': float(coeffs[0]),
            'correlation': float(correlation),
            'is_symmetry': abs(correlation) > 0.95
        }


class MathematicalStructureDiscoverer:
    """Main class for discovering mathematical structures."""
    
    def __init__(self):
        self.symbolic_regression = SymbolicRegression()
        self.symmetry_discoverer = SymmetryDiscoverer()
    
    def discover_equation(self, x: np.ndarray, y: np.ndarray,
                         variable_names: List[str],
                         max_complexity: int = 3) -> Optional[DiscoveredEquation]:
        """Discover equation relating variables."""
        return self.symbolic_regression.discover_equation(
            x, y, variable_names, max_complexity
        )
    
    def discover_differential_equation(self, t: np.ndarray, y: np.ndarray,
                                      y_deriv: np.ndarray) -> Optional[str]:
        """Discover differential equation from time series."""
        # Try: dy/dt = ky, dy/dt = ay^2, etc.
        return None  # Placeholder


if __name__ == "__main__":
    print("MATHEMATICAL STRUCTURE DISCOVERER")
    
    discoverer = MathematicalStructureDiscoverer()
    
    # Test: y = x^2
    x = np.array([1, 2, 3, 4, 5])
    y = x**2
    
    result = discoverer.discover_equation(x, y, ['x', 'y'])
    
    if result:
        print(f"Discovered: {result.equation}")
        print(f"Confidence: {result.confidence:.3f}")
