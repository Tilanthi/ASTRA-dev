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
Uncertainty Quantification Module
==================================

This module provides Bayesian inference and uncertainty quantification
tools for robust decision-making under uncertainty.

Capabilities:
- Hierarchical Bayesian modeling
- Partial pooling (shrinkage estimators)
- Uncertainty decomposition (aleatoric vs epistemic)
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple


def bayesian_parameter_inference(prior_mean: np.ndarray,
                                  prior_cov: np.ndarray,
                                  likelihood_func: callable,
                                  data: np.ndarray,
                                  n_samples: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bayesian parameter inference using MCMC-like sampling

    Args:
        prior_mean: Prior mean of parameters
        prior_cov: Prior covariance matrix
        likelihood_func: Function that computes likelihood given parameters
        data: Observed data
        n_samples: Number of samples to generate

    Returns:
        (posterior_mean, posterior_cov)
    """
    import numpy as np

    # Simple Metropolis-Hastings sampling
    n_params = len(prior_mean)
    samples = np.zeros((n_samples, n_params))

    # Initialize from prior
    current_params = np.random.multivariate_normal(prior_mean, prior_cov)
    current_likelihood = likelihood_func(current_params, data)

    acceptance_count = 0

    for i in range(1, n_samples):
        # Propose new parameters
        proposal_cov = prior_cov * 0.1
        proposed_params = np.random.multivariate_normal(current_params, proposal_cov)

        # Compute likelihood
        proposed_likelihood = likelihood_func(proposed_params, data)

        # Compute acceptance probability
        if proposed_likelihood > 0:
            acceptance_ratio = min(1.0, proposed_likelihood / (current_likelihood + 1e-10))

            if np.random.rand() < acceptance_ratio:
                current_params = proposed_params
                current_likelihood = proposed_likelihood
                acceptance_count += 1

        samples[i] = current_params

    # Compute posterior statistics
    posterior_mean = np.mean(samples[n_samples//2:], axis=0)
    posterior_cov = np.cov(samples[n_samples//2:].T)

    return posterior_mean, posterior_cov


def causal_discovery_from_timeseries(timeseries_data: Dict[str, np.ndarray],
                                    max_lag: int = 10,
                                    significance: float = 0.05) -> Dict[str, Any]:
    """
    Discover causal relationships from timeseries data using Granger causality

    Args:
        timeseries_data: Dictionary mapping variable names to timeseries
        max_lag: Maximum lag to consider
        significance: Significance level for causality tests

    Returns:
        Causal graph as adjacency dictionary
    """
    from scipy.stats import f
    import numpy as np

    variables = list(timeseries_data.keys())
    n_vars = len(variables)

    causal_graph = {var: {'causes': [], 'effects': []} for var in variables}

    # Test Granger causality for each pair
    for i, target in enumerate(variables):
        for j, source in enumerate(variables):
            if source == target:
                continue

            # Prepare data
            y = timeseries_data[target]
            x = timeseries_data[source]

            # Test if x Granger-causes y
            f_stat, p_value = _granger_causality_test(x, y, max_lag)

            if p_value < significance:
                causal_graph[target]['causes'].append(source)
                causal_graph[source]['effects'].append(target)

    return causal_graph


def _granger_causality_test(x: np.ndarray, y: np.ndarray, max_lag: int) -> Tuple[float, float]:
    """Perform Granger causality test"""
    from scipy.stats import f
    import numpy as np

    # Ensure same length
    min_len = min(len(x), len(y))
    x = x[:min_len]
    y = y[:min_len]

    # Restricted model: y depends only on its own lags
    # Full model: y depends on lags of y and x
    n = min_len - max_lag

    if n <= 0:
        return 0.0, 1.0

    # Create lag matrices
    Y_lag = np.zeros((n, max_lag))
    X_lag = np.zeros((n, max_lag))

    for lag in range(max_lag):
        Y_lag[:, lag] = y[max_lag-lag-1:-lag-1]
        X_lag[:, lag] = x[max_lag-lag-1:-lag-1]

    # Restricted model: y_t ~ sum(y_{t-i})
    Y_restricted = y[max_lag:]
    X_restricted = Y_lag
