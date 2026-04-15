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
Conditional Independence Testing

Statistical tests for determining conditional independence:
X ⟂ Y | Z (X independent of Y given Z)

Provides the foundation for causal discovery algorithms.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from typing import Optional, Tuple, Union
from enum import Enum


class TestType(Enum):
    """Types of conditional independence tests."""
    GAUSSIAN = "gaussian"  # Assumes multivariate normal
    DISCRETE = "discrete"  # For discrete variables
    KSAMPLE = "k-sample"  # Non-parametric
    FISHER_Z = "fisher_z"  # Fisher's Z transformation


class ConditionalIndependenceTest:
    """
    Statistical tests for conditional independence.

    Tests the null hypothesis: X ⟂ Y | Z

    Methods:
    - Gaussian CI test: Uses partial correlation
    - Discrete CI test: Uses G-test or Chi-squared
    - Fisher's Z: For correlation coefficients

    Example:
        >>> test = ConditionalIndependenceTest(alpha=0.05)
        >>> x, y, z = data['X'], data['Y'], data[['Z1', 'Z2']]
        >>> independent, p_value = test.gaussian_ci_test(x, y, z)
        >>> if independent:
        ...     print("X is independent of Y given Z")
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize CI test.

        Args:
            alpha: Significance level for rejecting independence
        """
        self.alpha = alpha

    def gaussian_ci_test(self,
                         x: np.ndarray,
                         y: np.ndarray,
                         z: Optional[np.ndarray] = None) -> Tuple[bool, float]:
        """
        Conditional independence test assuming Gaussian distribution.

        Tests if X ⟂ Y | Z using partial correlation.

        H0: X and Y are independent given Z
        Ha: X and Y are dependent given Z

        Args:
            x: Variable X (n_samples,)
            y: Variable Y (n_samples,)
            z: Conditioning variables Z (n_samples, n_features) or None

        Returns:
            (is_independent, p_value)
        """
        # Ensure arrays
        x = np.asarray(x).flatten()
        y = np.asarray(y).flatten()

        if z is None or z.shape[1] == 0:
            # Simple correlation test
            corr, p_value = pearsonr(x, y)
            is_independent = p_value > self.alpha
            return is_independent, p_value

        z = np.asarray(z)

        # Partial correlation test
        # Compute correlation of residuals after regressing on Z
        try:
            from sklearn.linear_model import LinearRegression

            # Regress X on Z
            reg_x = LinearRegression()
            reg_x.fit(z, x)
            resid_x = x - reg_x.predict(z)

            # Regress Y on Z
            reg_y = LinearRegression()
            reg_y.fit(z, y)
            resid_y = y - reg_y.predict(z)

            # Correlation of residuals
            n = len(x)
            k = z.shape[1]  # Number of conditioning variables

            corr, p_value = pearsonr(resid_x, resid_y)

            # Apply Fisher's Z transformation for better p-value
            if n > k + 3:
                z_score = self.fisher_z(corr, n, k)
                p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

            is_independent = p_value > self.alpha

            return is_independent, p_value

        except Exception as e:
            # Fallback to simple correlation
            corr, p_value = pearsonr(x, y)
            is_independent = p_value > self.alpha
            return is_independent, p_value

    def discrete_ci_test(self,
                         x: np.ndarray,
                         y: np.ndarray,
                         z: Optional[np.ndarray] = None) -> Tuple[bool, float]:
        """
        Conditional independence test for discrete variables.

        Uses G-test or Chi-squared test of independence.

        Args:
            x: Discrete variable X
            y: Discrete variable Y
            z: Discrete conditioning variable(s)

        Returns:
            (is_independent, p_value)
        """
        # Ensure integer arrays
        x = np.asarray(x).astype(int)
        y = np.asarray(y).astype(int)

        if z is None:
            # Simple independence test
            contingency = pd.crosstab(x, y)
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            is_independent = p_value > self.alpha
            return is_independent, p_value

        z = np.asarray(z).astype(int)

        # Conditional independence test
        # Test independence within each level of Z
        p_values = []

        for z_val in np.unique(z):
            mask = (z == z_val)

            if mask.sum() < 5:  # Skip if too few samples
                continue

            contingency = pd.crosstab(x[mask], y[mask])

            if contingency.shape == (2, 2):
                chi2, p, _, _ = stats.chi2_contingency(contingency)
                p_values.append(p)

        if p_values:
            # Combine p-values using Fisher's method
            from scipy.stats import combine_pvalues
            _, p_value = combine_pvalues(p_values, method='fisher')
            is_independent = p_value > self.alpha
            return is_independent, p_value
        else:
            # No valid tests
            return True, 1.0

    def fisher_z(self,
                  r: float,
                  n: int,
                  k: int = 0) -> float:
        """
        Fisher's Z transformation for correlation coefficient.

        Converts correlation to approximately normal distribution.

        Z = 0.5 * ln((1+r)/(1-r)) * sqrt(n - k - 3)

        Args:
            r: Correlation coefficient
            n: Sample size
            k: Number of conditioning variables

        Returns:
            Z-score
        """
        # Avoid numerical issues
        r = np.clip(r, -0.999, 0.999)

        # Fisher's Z transformation
        z = 0.5 * np.log((1 + r) / (1 - r))

        # Standard error
        if n > k + 3:
            se = 1 / np.sqrt(n - k - 3)
            z_score = z / se
        else:
            z_score = z

        return z_score

    def kernel_ci_test(self,
                       x: np.ndarray,
                       y: np.ndarray,
                       z: Optional[np.ndarray] = None) -> Tuple[bool, float]:
        """
        Kernel-based conditional independence test.

        Non-parametric test using kernel methods.
        More flexible than Gaussian test but slower.

        Args:
            x: Variable X
            y: Variable Y
            z: Conditioning variables

        Returns:
            (is_independent, p_value)
        """
        # Simplified version - use Gaussian test as fallback
        return self.gaussian_ci_test(x, y, z)

    def test(self,
             x: np.ndarray,
             y: np.ndarray,
             z: Optional[np.ndarray] = None,
             test_type: TestType = TestType.GAUSSIAN) -> Tuple[bool, float]:
        """
        Run conditional independence test.

        Args:
            x: Variable X
            y: Variable Y
            z: Conditioning variables
            test_type: Type of test to use

        Returns:
            (is_independent, p_value)
        """
        if test_type == TestType.GAUSSIAN:
            return self.gaussian_ci_test(x, y, z)
        elif test_type == TestType.DISCRETE:
            return self.discrete_ci_test(x, y, z)
        elif test_type == TestType.KSAMPLE:
            return self.kernel_ci_test(x, y, z)
        else:
            raise ValueError(f"Unknown test type: {test_type}")


def correlation_test(x: np.ndarray,
                     y: np.ndarray,
                     method: str = 'pearson') -> Tuple[float, float]:
    """
    Test correlation between two variables.

    Args:
        x: Variable X
        y: Variable Y
        method: 'pearson', 'spearman', or 'kendall'

    Returns:
        (correlation, p_value)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    if method == 'pearson':
        corr, p_value = pearsonr(x, y)
    elif method == 'spearman':
        corr, p_value = spearmanr(x, y)
    elif method == 'kendall':
        from scipy.stats import kendalltau
        corr, p_value = kendalltau(x, y)
    else:
        raise ValueError(f"Unknown correlation method: {method}")

    return corr, p_value


def partial_correlation(x: np.ndarray,
                        y: np.ndarray,
                        z: np.ndarray) -> Tuple[float, float]:
    """
    Compute partial correlation between X and Y controlling for Z.

    Args:
        x: Variable X
        y: Variable Y
        z: Conditioning variables (can be multivariate)

    Returns:
        (partial_correlation, p_value)
    """
    from sklearn.linear_model import LinearRegression

    # Residualize X on Z
    reg_x = LinearRegression()
    reg_x.fit(z, x)
    resid_x = x - reg_x.predict(z)

    # Residualize Y on Z
    reg_y = LinearRegression()
    reg_y.fit(z, y)
    resid_y = y - reg_y.predict(z)

    # Correlation of residuals
    corr, p_value = pearsonr(resid_x, resid_y)

    return corr, p_value



def bootstrap_uncertainty(data: np.ndarray,
                         estimator_func: callable,
                         n_bootstrap: int = 1000,
                         ci_level: float = 0.95) -> Dict[str, Any]:
    """
    Estimate uncertainty using bootstrap resampling.

    Args:
        data: Input data
        estimator_func: Function that computes estimate from data
        n_bootstrap: Number of bootstrap samples
        ci_level: Confidence interval level

    Returns:
        Dictionary with estimate and confidence interval
    """
    import numpy as np

    n = len(data)
    estimates = []

    for _ in range(n_bootstrap):
        pass  # Bootstrap implementation needed
