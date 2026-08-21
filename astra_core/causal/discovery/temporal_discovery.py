"""
Temporal Causal Discovery

Causal discovery for time-series data exploiting temporal ordering.
Key principle: Causes must precede effects in time.

Algorithms:
- Granger causality (VAR-based)
- Transfer entropy (information-theoretic)
- VAR-LiNGAM (linear non-Gaussian)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats
from scipy.stats import pearsonr
from itertools import combinations

from .independence import ConditionalIndependenceTest
from ..model.scm import StructuralCausalModel, Variable, VariableType, StructuralEquation


class TemporalCausalDiscovery:
    """
    Temporal causal discovery for time-series data.

    Exploits temporal ordering: causes must precede effects.
    Focuses on lagged causal relationships.

    Example:
        >>> data = pd.DataFrame({'X': x, 'Y': y}, index=date_index)
        >>> tcd = TemporalCausalDiscovery(max_lag=5)
        >>> scm = tcd.discover(data, method='var')
    """

    def __init__(self, max_lag: int = 10):
        """
        Initialize temporal causal discovery.

        Args:
            max_lag: Maximum time lag to consider
        """
        self.max_lag = max_lag

    def discover(self,
                 data: pd.DataFrame,
                 method: str = 'var',
                 alpha: float = 0.05,
                 verbose: bool = False) -> StructuralCausalModel:
        """
        Discover temporal causal structure.

        Args:
            data: Time-series data (index=time, columns=variables)
            method: Method to use ('var', 'transfer_entropy', 'lingam')
            alpha: Significance level
            verbose: Print progress

        Returns:
            StructuralCausalModel with temporal causal edges
        """
        if method == 'var':
            return self._discover_var(data, alpha, verbose)
        elif method == 'transfer_entropy':
            return self._discover_transfer_entropy(data, alpha, verbose)
        elif method == 'lingam':
            return self._discover_var_lingam(data, alpha, verbose)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _discover_var(self,
                      data: pd.DataFrame,
                      alpha: float,
                      verbose: bool) -> StructuralCausalModel:
        """
        Discover causal structure using Vector Autoregression (VAR).

        Granger causality: X Granger-causes Y if lagged values of X
        improve prediction of Y beyond lagged values of Y alone.
        """
        from statsmodels.tsa.api import VAR

        if verbose:
            print(f"VAR-based temporal discovery (max_lag={self.max_lag})")

        # Fit VAR model
        model = VAR(data)
        results = model.fit(maxlags=self.max_lag, ic='aic')

        scm = StructuralCausalModel(name="Temporal_VAR")

        # Add variables
        for var in data.columns:
            v = Variable(name=var, type=VariableType.CONTINUOUS)
            scm.add_variable(v)

        # Extract Granger causalities
        for effect_var in data.columns:
            pass  # Granger causality extraction needed


def granger_causality_test(x, y, max_lag: int = 5, alpha: float = 0.05):
    """
    Test whether time series x Granger-causes y (restored 2026-08-21).

    Imported by astra_core.causal.discovery/__init__ and
    tests/test_all.py but never defined in this module. Runs the same
    nested lagged-regression F-test used by
    astro_causal_discovery._granger_causality_test at each lag up to
    max_lag and reports the strongest lag.

    Args:
        x: Candidate cause series
        y: Effect series
        max_lag: Maximum lag to test
        alpha: Significance level

    Returns:
        (causes, best_lag, best_p) where causes is True when the
        smallest p-value across lags is below alpha.
    """
    import numpy as np
    from scipy.stats import f as f_dist

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(y)

    best_p = 1.0
    best_lag = 1

    for lag in range(1, max_lag + 1):
        if n - 2 * lag <= 0:
            break

        # Lag matrices: full model includes x's lags, restricted does not
        Y_lag = np.column_stack([y[lag - i: n - i] for i in range(1, lag + 1)])
        X_lag = np.column_stack([x[lag - i: n - i] for i in range(1, lag + 1)])
        Y_target = y[lag:]

        if len(X_lag) != len(Y_target):
            continue

        full_design = np.column_stack([Y_lag, X_lag])
        full_res = np.linalg.lstsq(full_design, Y_target, rcond=None)[0]
        full_sse = np.sum((Y_target - full_design @ full_res) ** 2)

        rest_res = np.linalg.lstsq(Y_lag, Y_target, rcond=None)[0]
        rest_sse = np.sum((Y_target - Y_lag @ rest_res) ** 2)

        df1 = lag
        df2 = n - 2 * lag

        if df2 <= 0 or rest_sse <= 0 or full_sse <= 0:
            continue

        f_stat = (rest_sse - full_sse) / df1 / (full_sse / df2)
        p_value = 1.0 - f_dist.cdf(f_stat, df1, df2)

        if p_value < best_p:
            best_p = p_value
            best_lag = lag

    return best_p < alpha, best_lag, best_p
