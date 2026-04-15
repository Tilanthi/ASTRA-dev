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
ASTRA Live — Bayesian Model Selection
Evidence computation, Bayes factors, and hypothesis competition scoring.

As described in White & Dey (2026), Sections 6 and 8.4.3.
"""
import numpy as np
from scipy import stats
from scipy.special import gammaln
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ModelEvidence:
    model_name: str
    log_evidence: float
    n_parameters: int
    r_squared: float
    residuals_std: float
    aic: float
    bic: float

    def to_dict(self):
        return asdict(self)


@dataclass
class ModelComparison:
    models: List[ModelEvidence]
    best_model: str
    bayes_factors: Dict[str, float]  # model_name → BF vs best
    ranking: List[str]

    def to_dict(self):
        return {
            "models": [m.to_dict() for m in self.models],
            "best_model": self.best_model,
            "bayes_factors": self.bayes_factors,
            "ranking": self.ranking,
        }


def compute_log_evidence(y: np.ndarray, y_pred: np.ndarray, n_params: int,
                          prior_width: float = 1.0) -> float:
    """
    Compute log Bayesian evidence (marginal likelihood) using BIC approximation.

    log P(D|M) ≈ -BIC/2 = -χ²/2 - k·log(n)/2 + const

    For more precise computation, use nested sampling (not implemented here).
    """
    n = len(y)
    resid = y - y_pred
    chi2 = np.sum(resid**2)
    sigma2 = np.var(resid)

    if sigma2 <= 0:
        return -1e10

    # Log-likelihood (Gaussian)
    log_lik = -0.5 * n * np.log(2 * np.pi * sigma2) - 0.5 * chi2 / sigma2

    # Log-prior (Gaussian with width prior_width)
    log_prior = -n_params * np.log(prior_width)

    # BIC approximation to log evidence
    log_evidence = log_lik - 0.5 * n_params * np.log(n)

    return log_evidence


def fit_model(x: np.ndarray, y: np.ndarray, model_type: str) -> Dict:
    """Fit a model and return predictions, parameters, and metrics."""
    n = len(x)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    n_valid = len(x)

    if n_valid < 3:
        return {"y_pred": y, "n_params": 0, "r_squared": 0, "residuals_std": 1, "params": []}

    if model_type == "linear":
        X = np.column_stack([np.ones(n_valid), x])
        params = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ params
        n_params = 2

    elif model_type == "power_law":
        # y = a * x^b → log(y) = log(a) + b*log(x)
        pos = (x > 0) & (y > 0)
        if np.sum(pos) < 3:
            return {"y_pred": y, "n_params": 2, "r_squared": 0, "residuals_std": 1, "params": [0, 0]}
        log_x = np.log10(x[pos])
        log_y = np.log10(y[pos])
        X = np.column_stack([np.ones(len(log_x)), log_x])
        beta = np.linalg.lstsq(X, log_y, rcond=None)[0]
        y_pred_log = X @ beta
        y_pred = np.zeros_like(y)
        y_pred[pos] = 10 ** y_pred_log
        y_pred[~pos] = np.mean(y[pos])
        n_params = 2
        params = [10**beta[0], beta[1]]  # a, b

    elif model_type == "logarithmic":
        pos = x > 0
        if np.sum(pos) < 3:
            return {"y_pred": y, "n_params": 2, "r_squared": 0, "residuals_std": 1, "params": [0, 0]}
        log_x = np.log(x[pos])
        X = np.column_stack([np.ones(len(log_x)), log_x])
        params = np.linalg.lstsq(X, y[pos], rcond=None)[0]
        y_pred = np.zeros_like(y)
        y_pred[pos] = X @ params
        y_pred[~pos] = params[0]
        n_params = 2

    elif model_type == "quadratic":
        X = np.column_stack([np.ones(n_valid), x, x**2])
        params = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ params
        n_params = 3

    elif model_type == "broken_power_law":
        # y = a * x^b1 for x < x_break, a * x_break^(b1-b2) * x^b2 for x > x_break
        # Approximate: find best breakpoint
        best_chi2 = np.inf
        best_pred = y.copy()
        x_sorted = np.sort(x)
        for break_pct in [0.3, 0.5, 0.7]:
            x_break = np.percentile(x[x > 0], break_pct * 100) if np.any(x > 0) else np.median(x)
            left = x <= x_break
            right = x > x_break
            if np.sum(left) < 3 or np.sum(right) < 3:
                continue
            # Fit left
            X_l = np.column_stack([np.ones(np.sum(left)), np.log10(x[left] + 1e-10)])
            y_l = np.log10(y[left] + 1e-10)
            beta_l = np.linalg.lstsq(X_l, y_l, rcond=None)[0]
            # Fit right
            X_r = np.column_stack([np.ones(np.sum(right)), np.log10(x[right] + 1e-10)])
            y_r = np.log10(y[right] + 1e-10)
            beta_r = np.linalg.lstsq(X_r, y_r, rcond=None)[0]
            # Predict
            y_pred = np.zeros_like(y, dtype=float)
            y_pred[left] = 10**(X_l @ beta_l)
            y_pred[right] = 10**(X_r @ beta_r)
            chi2 = np.sum((y - y_pred)**2)
            if chi2 < best_chi2:
                best_chi2 = chi2
                best_pred = y_pred.copy()
        y_pred = best_pred
        n_params = 4  # 2 slopes + break + normalization
        params = [n_params]

    else:
        y_pred = np.full_like(y, np.mean(y))
        n_params = 1
        params = [np.mean(y)]

    # R²
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    resid_std = np.std(y - y_pred)

    return {
        "y_pred": y_pred,
        "n_params": n_params,
        "r_squared": r_sq,
        "residuals_std": resid_std,
        "params": list(params) if hasattr(params, '__iter__') else [params],
    }


def compare_models(x: np.ndarray, y: np.ndarray,
                    model_types: List[str] = None,
                    prior_width: float = 1.0) -> ModelComparison:
    """
    Compare multiple models using Bayesian evidence and Bayes factors.

    Models tested: linear, power_law, logarithmic, quadratic, broken_power_law
    """
    if model_types is None:
        model_types = ["linear", "power_law", "logarithmic", "quadratic", "broken_power_law"]

    evidences = []
    for mtype in model_types:
        result = fit_model(x, y, mtype)
        log_ev = compute_log_evidence(y, result["y_pred"], result["n_params"], prior_width)
        n = len(y)
        aic = -2 * log_ev + 2 * result["n_params"]
        bic = -2 * log_ev + result["n_params"] * np.log(max(n, 1))

        evidences.append(ModelEvidence(
            model_name=mtype,
            log_evidence=log_ev,
            n_parameters=result["n_params"],
            r_squared=result["r_squared"],
            residuals_std=result["residuals_std"],
            aic=aic,
            bic=bic,
        ))

    # Sort by evidence (highest = best)
    evidences.sort(key=lambda m: m.log_evidence, reverse=True)
    best = evidences[0]

    # Bayes factors relative to best model
    bf = {}
    for m in evidences:
        bf[m.model_name] = np.exp(m.log_evidence - best.log_evidence)

    ranking = [m.model_name for m in evidences]

    return ModelComparison(
        models=evidences,
        best_model=best.model_name,
        bayes_factors=bf,
        ranking=ranking,
    )


def score_hypothesis(evidence_fit: float, plausibility: float,
                      predictive_power: float, simplicity: float) -> float:
    """
    Score a hypothesis using the weighted formula from the paper:

    Score(H) = 0.35 × evidence_fit + 0.30 × plausibility
             + 0.25 × predictive_power + 0.10 × simplicity

    All inputs should be in [0, 1].
    """
    return (0.35 * evidence_fit +
            0.30 * plausibility +
            0.25 * predictive_power +
            0.10 * simplicity)


def rank_hypotheses(hypotheses: List[Dict]) -> List[Dict]:
    """
    Rank competing hypotheses using the scoring formula.

    Each hypothesis dict should have:
    - name: hypothesis name
    - evidence_fit: 0-1 (how well it fits the data)
    - plausibility: 0-1 (physical plausibility)
    - predictive_power: 0-1 (ability to make testable predictions)
    - simplicity: 0-1 (Occam's razor)
    """
    scored = []
    for h in hypotheses:
        score = score_hypothesis(
            h.get("evidence_fit", 0.5),
            h.get("plausibility", 0.5),
            h.get("predictive_power", 0.5),
            h.get("simplicity", 0.5),
        )
        scored.append({**h, "score": score})

    scored.sort(key=lambda h: h["score"], reverse=True)
    return scored


def compute_posterior_intervals(data: np.ndarray, model_func, param_bounds: dict,
                                 n_samples: int = 1000) -> dict:
    """
    Compute posterior parameter intervals using Laplace approximation.
    
    1. Find MAP estimate via differential_evolution
    2. Compute Hessian at MAP for approximate posterior covariance
    3. Return MAP params, uncertainties, and 95% credible intervals
    """
    from scipy import optimize
    import numpy as np
    
    param_names = list(param_bounds.keys())
    bounds_list = [param_bounds[k] for k in param_names]
    
    def neg_log_posterior(params):
        try:
            pred = model_func(params)
            residuals = data - pred
            sigma = np.std(residuals) if np.std(residuals) > 0 else 1.0
            log_lik = -0.5 * np.sum((residuals / sigma)**2)
            # Flat prior within bounds
            return -log_lik
        except Exception:
            return 1e10
    
    # MAP via differential evolution
    result = optimize.differential_evolution(neg_log_posterior, bounds_list,
                                              maxiter=200, seed=42, tol=1e-6)
    map_params = result.x
    
    # Laplace approximation: Hessian at MAP
    try:
        hess = np.zeros((len(map_params), len(map_params)))
        eps = 1e-5
        f0 = neg_log_posterior(map_params)
        for i in range(len(map_params)):
            for j in range(i, len(map_params)):
                params_pp = map_params.copy()
                params_pm = map_params.copy()
                params_mp = map_params.copy()
                params_mm = map_params.copy()
                params_pp[i] += eps; params_pp[j] += eps
                params_pm[i] += eps; params_pm[j] -= eps
                params_mp[i] -= eps; params_mp[j] += eps
                params_mm[i] -= eps; params_mm[j] -= eps
                hess[i, j] = (neg_log_posterior(params_pp) - neg_log_posterior(params_pm) -
                              neg_log_posterior(params_mp) + neg_log_posterior(params_mm)) / (4 * eps**2)
                hess[j, i] = hess[i, j]
        
        # Covariance = inverse Hessian
        try:
            cov = np.linalg.inv(hess)
            # Ensure positive diagonal
            uncertainties = np.sqrt(np.abs(np.diag(cov)))
        except np.linalg.LinAlgError:
            uncertainties = np.full(len(map_params), np.nan)
    except Exception:
        uncertainties = np.full(len(map_params), np.nan)
    
    # Build result
    param_dict = {}
    unc_dict = {}
    ci_dict = {}
    for i, name in enumerate(param_names):
        param_dict[name] = round(float(map_params[i]), 6)
        unc_dict[name] = round(float(uncertainties[i]), 6)
        ci_dict[name] = {
            "lower": round(float(map_params[i] - 1.96 * uncertainties[i]), 6),
            "upper": round(float(map_params[i] + 1.96 * uncertainties[i]), 6),
        }
    
    return {
        "map_params": param_dict,
        "param_uncertainties": unc_dict,
        "credible_intervals": ci_dict,
        "convergence": result.success,
        "n_evaluations": result.nfev,
    }
