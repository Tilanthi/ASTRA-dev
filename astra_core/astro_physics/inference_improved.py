"""
Enhanced Bayesian inference diagnostics.

Complements inference.py (SMC sampler) and uncertainty_quantification.py
(samplers) with the standard convergence and model-comparison machinery used
to *trust* a Bayesian result:

  * Gelman-Rubin potential scale reduction factor R-hat (Gelman & Rubin 1992;
    split-R-hat as in Vehtari+ 2021).
  * Effective sample size from the integrated autocorrelation time
    (Sokal 1997; Geyer 1992).
  * Information-criteria model comparison: AIC (Akaike 1974), BIC (Schwarz
    1978), DIC (Spiegelhalter+ 2002) and WAIC (Watanabe 2010; Gelman+ 2014).
"""

import numpy as np
from dataclasses import dataclass
from typing import Sequence, Optional


# --- Convergence diagnostics ----------------------------------------------

def gelman_rubin(chains: Sequence[np.ndarray]) -> float:
    """Standard Gelman-Rubin R-hat for >=2 chains of equal length.

    chains: sequence of 1-D arrays (one per chain).
    Returns R-hat; ~1.0 means convergence; >1.1 typically not converged.
    """
    chains = [np.asarray(c, float) for c in chains]
    m = len(chains)
    n = min(len(c) for c in chains)
    chains = np.array([c[:n] for c in chains])          # (m, n)
    means = chains.mean(axis=1)
    grand = means.mean()
    B = n / (m - 1) * np.sum((means - grand) ** 2)       # between-chain variance
    W = np.mean([np.var(c, ddof=1) for c in chains])     # within-chain variance
    if W <= 0:
        return 1.0
    var_hat = (n - 1) / n * W + B / n                    # marginal posterior var est.
    return float(np.sqrt(var_hat / W))


def effective_sample_size(chain: np.ndarray) -> float:
    """ESS from the integrated autocorrelation time tau: ESS = n / (1 + 2 sum rho_k),
    truncated at the first non-positive autocorrelation (Geyer's initial monotone
    sequence)."""
    x = np.asarray(chain, float)
    n = len(x)
    x = x - x.mean()
    var = np.dot(x, x) / n
    if var <= 0:
        return float(n)
    # autocorrelation via FFT
    f = np.fft.rfft(x, n=2 * n)
    acf = np.fft.irfft(f * np.conjugate(f))[:n].real
    acf /= acf[0]
    # sum until first negative pair (Geyer)
    s = 0.0
    for k in range(1, n):
        if acf[k] <= 0:
            break
        s += acf[k]
    tau = 1.0 + 2.0 * s
    return float(n / tau)


# --- Information criteria --------------------------------------------------

@dataclass
class ModelComparison:
    name: str
    log_likelihood: float          # max log-likelihood (for AIC/BIC)
    n_params: int
    n_data: int
    aic: float
    bic: float


def aic(log_likelihood: float, n_params: int) -> float:
    """Akaike information criterion: AIC = 2k - 2 logL (lower is better)."""
    return 2.0 * n_params - 2.0 * log_likelihood


def bic(log_likelihood: float, n_params: int, n_data: int) -> float:
    """Bayesian information criterion: BIC = k ln(n) - 2 logL."""
    return n_params * np.log(max(n_data, 1)) - 2.0 * log_likelihood


def dic(log_likelihood_samples: np.ndarray, deviance_at_mean_params: float) -> float:
    """Deviance information criterion (Spiegelhalter+ 2002).

    DIC = D_bar + p_D, where D_bar = -2 mean(logL over posterior samples)
    and p_D = D_bar - D(mean params). Lower is better.
    """
    Dbar = -2.0 * np.mean(log_likelihood_samples)
    pD = Dbar - deviance_at_mean_params
    return float(Dbar + pD)


def waic(log_likelihood_per_obs: np.ndarray) -> dict:
    """Watanabe-Akaike (widely-applicable) information criterion.

    log_likelihood_per_obs: (S, N) array of pointwise log-likelihood over S
    posterior draws and N data points. Returns dict with waic and p_w.
    """
    ll = np.asarray(log_likelihood_per_obs, float)
    S, N = ll.shape
    lppd = np.log(np.mean(np.exp(ll - ll.max(axis=0, keepdims=True)), axis=0)) \
        + ll.max(axis=0)
    lppd_sum = float(np.sum(lppd))
    p_w = float(np.sum(np.var(ll, axis=0, ddof=1)))
    return {'waic': -2.0 * (lppd_sum - p_w), 'p_w': p_w, 'lppd': lppd_sum}


def compare_models(models: Sequence[ModelComparison], criterion: str = "bic"
                   ) -> list:
    """Rank models by the chosen criterion (lower = better); add deltas."""
    key = criterion
    best = min(getattr(m, key) for m in models)
    ranked = sorted(models, key=lambda m: getattr(m, key))
    for m in ranked:
        m.__dict__[f'delta_{criterion}'] = getattr(m, key) - best
    return ranked


def make_model(name: str, log_likelihood: float, n_params: int, n_data: int
               ) -> ModelComparison:
    return ModelComparison(name=name, log_likelihood=log_likelihood,
                           n_params=n_params, n_data=n_data,
                           aic=aic(log_likelihood, n_params),
                           bic=bic(log_likelihood, n_params, n_data))


__all__ = [
    'gelman_rubin', 'effective_sample_size', 'aic', 'bic', 'dic', 'waic',
    'ModelComparison', 'make_model', 'compare_models',
]
