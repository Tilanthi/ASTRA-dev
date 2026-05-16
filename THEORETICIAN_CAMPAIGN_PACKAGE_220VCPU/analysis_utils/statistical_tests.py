#!/usr/bin/env python3
"""
Statistical tests for campaign analysis.

Provides χ² tests, bootstrap analysis, and hierarchical Bayesian methods.
"""

import numpy as np
from scipy import stats


def chi_squared_test(observed, expected, uncertainty):
    """
    Perform χ² goodness-of-fit test.

    Parameters
    ----------
    observed : array-like
        Observed values
    expected : array-like
        Expected values
    uncertainty : array-like or float
        Uncertainties (can be scalar for homoscedastic)

    Returns
    -------
    dict
        Test results with χ² statistic, p-value, and interpretation
    """
    observed = np.asarray(observed)
    expected = np.asarray(expected)

    # Compute residuals
    residuals = (observed - expected) / uncertainty

    # χ² statistic
    chi2 = np.sum(residuals**2)

    # Degrees of freedom
    dof = len(observed) - 1

    # P-value
    p_value = 1 - stats.chi2.cdf(chi2, dof)

    # Interpretation
    if p_value < 0.01:
        interpretation = "Reject null hypothesis (strong evidence)"
    elif p_value < 0.05:
        interpretation = "Reject null hypothesis (moderate evidence)"
    elif p_value < 0.10:
        interpretation = "Marginal evidence against null"
    else:
        interpretation = "Cannot reject null hypothesis"

    return {
        'chi2': chi2,
        'dof': dof,
        'p_value': p_value,
        'interpretation': interpretation
    }


def bootstrap_mean(data, n_bootstrap=10000, seed=42):
    """
    Compute bootstrap confidence interval for mean.

    Parameters
    ----------
    data : array-like
        Input data
    n_bootstrap : int
        Number of bootstrap samples
    seed : int
        Random seed

    Returns
    -------
    dict
        Bootstrap statistics
    """
    np.random.seed(seed)
    data = np.asarray(data)

    bootstrap_means = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_means[i] = sample.mean()

    return {
        'mean': data.mean(),
        'std': data.std(ddof=1),
        'bootstrap_mean': bootstrap_means.mean(),
        'bootstrap_std': bootstrap_means.std(),
        'CI_95_lower': np.percentile(bootstrap_means, 2.5),
        'CI_95_upper': np.percentile(bootstrap_means, 97.5)
    }
