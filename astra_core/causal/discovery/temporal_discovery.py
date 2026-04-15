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
