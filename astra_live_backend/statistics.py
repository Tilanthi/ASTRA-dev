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
ASTRA Live — Real Statistical Tests
Wraps scipy.stats for actual hypothesis testing.
"""
import numpy as np
from scipy import stats
from dataclasses import dataclass


@dataclass
class StatTestResult:
    test_name: str
    statistic: float
    p_value: float
    passed: bool
    details: str
    alpha: float = 0.05

    def __post_init__(self):
        # Ensure all values are Python native types, not numpy
        self.statistic = float(self.statistic)
        self.p_value = float(self.p_value)
        self.passed = bool(self.passed)
        self.alpha = float(self.alpha)


def chi_squared_test(observed: np.ndarray, expected: np.ndarray = None,
                     alpha: float = 0.05) -> StatTestResult:
    """Chi-squared goodness of fit test."""
    observed = np.asarray(observed, dtype=float)
    if expected is None:
        expected = np.full_like(observed, np.mean(observed))
    else:
        expected = np.asarray(expected, dtype=float)
        # Scale expected to match observed sum
        obs_sum = observed.sum()
        exp_sum = expected.sum()
        if exp_sum > 0:
            expected = expected * (obs_sum / exp_sum)
        else:
            expected = np.full_like(observed, obs_sum / len(observed))
    stat, p = stats.chisquare(observed, f_exp=expected)
    dof = len(observed) - 1
    return StatTestResult(
        test_name="Chi-squared",
        statistic=float(stat),
        p_value=float(p),
        passed=p > alpha,
        details=f"χ² = {stat:.4f}, dof = {dof}, χ²/dof = {stat/dof:.2f}"
    )


def kolmogorov_smirnov_test(sample1: np.ndarray, sample2: np.ndarray = None,
                            dist_name: str = "norm", alpha: float = 0.05) -> StatTestResult:
    """Kolmogorov-Smirnov test against a distribution or between two samples."""
    if sample2 is not None:
        stat, p = stats.ks_2samp(sample1, sample2)
        details = f"D = {stat:.4f} (two-sample)"
    else:
        stat, p = stats.kstest(sample1, dist_name)
        details = f"D = {stat:.4f} (vs {dist_name})"
    return StatTestResult(
        test_name="Kolmogorov-Smirnov",
        statistic=float(stat),
        p_value=float(p),
        passed=p > alpha,
        details=details
    )


def bayesian_t_test(sample1: np.ndarray, sample2: np.ndarray = None,
                    popmean: float = 0.0, alpha: float = 0.05) -> StatTestResult:
    """One-sample or two-sample t-test with Bayesian interpretation."""
    if sample2 is not None:
        stat, p = stats.ttest_ind(sample1, sample2)
        details = f"t = {stat:.4f} (two-sample), n1={len(sample1)}, n2={len(sample2)}"
    else:
        stat, p = stats.ttest_1samp(sample1, popmean)
        details = f"t = {stat:.4f} (one-sample vs μ={popmean}), n={len(sample1)}"
    return StatTestResult(
        test_name="Bayesian t-test",
        statistic=float(stat),
        p_value=float(p),
        passed=p < alpha,
        details=details
    )


def anderson_darling_test(sample: np.ndarray, dist: str = "norm",
                          alpha: float = 0.05) -> StatTestResult:
    """Anderson-Darling normality test."""
    result = stats.anderson(sample, dist=dist)
    # Use 5% significance level (index 2)
    critical = result.critical_values[2]
    passed = result.statistic < critical
    return StatTestResult(
        test_name="Anderson-Darling",
        statistic=float(result.statistic),
        p_value=0.05,  # AD doesn't give p-value directly
        passed=passed,
        details=f"A² = {result.statistic:.4f}, critical(5%) = {critical:.4f}"
    )


def mann_whitney_test(sample1: np.ndarray, sample2: np.ndarray,
                      alpha: float = 0.05) -> StatTestResult:
    """Mann-Whitney U test (non-parametric)."""
    stat, p = stats.mannwhitneyu(sample1, sample2, alternative='two-sided')
    return StatTestResult(
        test_name="Mann-Whitney U",
        statistic=float(stat),
        p_value=float(p),
        passed=p > alpha,
        details=f"U = {stat:.1f}, n1={len(sample1)}, n2={len(sample2)}"
    )


def pearson_correlation(x: np.ndarray, y: np.ndarray,
                        alpha: float = 0.05) -> StatTestResult:
    """Pearson correlation with significance test."""
    r, p = stats.pearsonr(x, y)
    return StatTestResult(
        test_name="Pearson correlation",
        statistic=float(r),
        p_value=float(p),
        passed=p < alpha,
        details=f"r = {r:.4f}, r² = {r**2:.4f}"
    )


def granger_causality_simple(x: np.ndarray, y: np.ndarray,
                             lag: int = 3, alpha: float = 0.05) -> StatTestResult:
    """Simplified Granger causality test using F-test on lagged regression."""
    n = len(x)
    if n < lag + 10:
        return StatTestResult("Granger causality", 0, 1.0, False, "Insufficient data")

    # Restricted model: y_t = c + Σ a_i * y_{t-i} + e
    Y = y[lag:]
    X_restricted = np.column_stack([y[lag - i - 1: n - i - 1] for i in range(lag)])
    X_restricted = np.column_stack([np.ones(len(Y)), X_restricted])

    # Unrestricted: add lagged x
    X_unrestricted = np.column_stack([
        X_restricted,
        *[x[lag - i - 1: n - i - 1] for i in range(lag)]
    ])

    # OLS
    beta_r = np.linalg.lstsq(X_restricted, Y, rcond=None)[0]
    beta_u = np.linalg.lstsq(X_unrestricted, Y, rcond=None)[0]

    resid_r = Y - X_restricted @ beta_r
    resid_u = Y - X_unrestricted @ beta_u

    ssr_r = np.sum(resid_r ** 2)
    ssr_u = np.sum(resid_u ** 2)

    df1 = lag
    df2 = len(Y) - X_unrestricted.shape[1]

    if ssr_u == 0 or df2 <= 0:
        return StatTestResult("Granger causality", 0, 1.0, False, "Degenerate case")

    f_stat = ((ssr_r - ssr_u) / df1) / (ssr_u / df2)
    p_value = 1 - stats.f.cdf(f_stat, df1, df2)

    return StatTestResult(
        test_name="Granger causality",
        statistic=float(f_stat),
        p_value=float(p_value),
        passed=p_value < alpha,
        details=f"F({df1},{df2}) = {f_stat:.4f}, lag = {lag}"
    )


# === Advanced Statistical Methods (Phase 7) ===

def fdr_correction(p_values: list, alpha: float = 0.05) -> dict:
    """Benjamini-Hochberg FDR correction for multiple comparisons."""
    import numpy as np
    p = np.array(p_values, dtype=float)
    n = len(p)
    if n == 0:
        return {"corrected_alpha": alpha, "rejected_mask": [], "adjusted_p_values": [], "n_significant": 0}
    
    sorted_idx = np.argsort(p)
    sorted_p = p[sorted_idx]
    
    # BH adjusted p-values
    adjusted = np.zeros(n)
    adjusted[sorted_idx[-1]] = sorted_p[-1]
    for i in range(n - 2, -1, -1):
        adjusted[sorted_idx[i]] = min(adjusted[sorted_idx[i + 1]], sorted_p[i] * n / (i + 1))
    
    # Corrected alpha (threshold for the last rejected hypothesis)
    rejected_mask = adjusted <= alpha
    n_significant = int(np.sum(rejected_mask))
    
    # Corrected alpha = max p-value that's still rejected
    if n_significant > 0:
        corrected_alpha = float(np.max(p[rejected_mask]))
    else:
        corrected_alpha = 0.0
    
    return {
        "corrected_alpha": corrected_alpha,
        "rejected_mask": rejected_mask.tolist(),
        "adjusted_p_values": [round(float(v), 8) for v in adjusted],
        "n_significant": n_significant,
    }


def cohen_d(group1, group2) -> float:
    """Cohen's d effect size for two groups."""
    import numpy as np
    g1, g2 = np.asarray(group1, dtype=float), np.asarray(group2, dtype=float)
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return 0.0
    pooled_std = np.sqrt(((n1 - 1) * np.var(g1, ddof=1) + (n2 - 1) * np.var(g2, ddof=1)) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((np.mean(g1) - np.mean(g2)) / pooled_std)


def cramers_v(contingency_table) -> float:
    """Cramér's V effect size for categorical data."""
    import numpy as np
    from scipy.stats import chi2_contingency
    table = np.asarray(contingency_table, dtype=float)
    if table.size == 0 or table.sum() == 0:
        return 0.0
    chi2, _, _, _ = chi2_contingency(table)
    n = table.sum()
    min_dim = min(table.shape[0], table.shape[1]) - 1
    if min_dim == 0 or n == 0:
        return 0.0
    return float(np.sqrt(chi2 / (n * min_dim)))


def eta_squared(groups: list) -> float:
    """η² effect size for one-way ANOVA."""
    import numpy as np
    all_data = np.concatenate([np.asarray(g, dtype=float) for g in groups])
    grand_mean = np.mean(all_data)
    ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in groups)
    ss_total = np.sum((all_data - grand_mean)**2)
    if ss_total == 0:
        return 0.0
    return float(ss_between / ss_total)


def effect_size_report(data1, data2, test_type="continuous") -> dict:
    """Auto-select appropriate effect size measure."""
    import numpy as np
    d1, d2 = np.asarray(data1, dtype=float), np.asarray(data2, dtype=float)
    
    if test_type == "continuous":
        d = cohen_d(d1, d2)
        interpretation = "large" if abs(d) >= 0.8 else ("medium" if abs(d) >= 0.5 else ("small" if abs(d) >= 0.2 else "negligible"))
        return {"measure": "cohen_d", "value": round(d, 4), "interpretation": interpretation}
    elif test_type == "categorical":
        # Treat as 2x2 contingency
        table = np.array([[np.sum(d1 > 0), np.sum(d1 <= 0)],
                          [np.sum(d2 > 0), np.sum(d2 <= 0)]])
        v = cramers_v(table)
        interpretation = "large" if v >= 0.5 else ("medium" if v >= 0.3 else ("small" if v >= 0.1 else "negligible"))
        return {"measure": "cramers_v", "value": round(v, 4), "interpretation": interpretation}
    else:
        return {"measure": "none", "value": 0.0, "interpretation": "unknown"}


def detect_autocorrelation(series: list, max_lag: int = 10) -> dict:
    """Detect autocorrelation in a time series using Ljung-Box test."""
    import numpy as np
    from scipy import stats as sp_stats
    
    s = np.asarray(series, dtype=float)
    n = len(s)
    if n < max_lag + 5:
        return {"autocorrelations": {}, "ar1_significant": False, "ljung_box_p": 1.0}
    
    s_centered = s - np.mean(s)
    var = np.var(s)
    if var == 0:
        return {"autocorrelations": {}, "ar1_significant": False, "ljung_box_p": 1.0}
    
    acf = {}
    for lag in range(1, max_lag + 1):
        c = np.mean(s_centered[lag:] * s_centered[:-lag]) / var
        acf[lag] = round(float(c), 6)
    
    # Ljung-Box statistic for AR(1) test
    Q = n * (n + 2) * sum((acf[k]**2) / (n - k) for k in range(1, min(max_lag + 1, n)))
    lb_p = 1.0 - sp_stats.chi2.cdf(Q, max_lag)
    
    return {
        "autocorrelations": acf,
        "ar1_significant": acf.get(1, 0) > 2.0 / np.sqrt(n) or lb_p < 0.05,
        "ljung_box_statistic": round(float(Q), 4),
        "ljung_box_p": round(float(lb_p), 8),
        "n": n,
    }


def change_point_detection(series: list) -> dict:
    """Simple CUSUM change point detection."""
    import numpy as np
    
    s = np.asarray(series, dtype=float)
    n = len(s)
    if n < 10:
        return {"change_points": [], "n_changes": 0}
    
    mean = np.mean(s)
    std = np.std(s)
    if std == 0:
        return {"change_points": [], "n_changes": 0}
    
    # CUSUM
    cusum_pos = np.zeros(n)
    cusum_neg = np.zeros(n)
    threshold = 4.0 * std  # Detection threshold
    
    change_points = []
    for i in range(1, n):
        cusum_pos[i] = max(0, cusum_pos[i-1] + (s[i] - mean) - 0.5 * std)
        cusum_neg[i] = min(0, cusum_neg[i-1] + (s[i] - mean) + 0.5 * std)
        
        if cusum_pos[i] > threshold:
            change_points.append(int(i))
            cusum_pos[i] = 0
        elif cusum_neg[i] < -threshold:
            change_points.append(int(i))
            cusum_neg[i] = 0
    
    return {
        "change_points": change_points,
        "n_changes": len(change_points),
        "method": "CUSUM",
        "threshold": round(float(threshold), 4),
    }


# === Astronomical data generators with REAL distributions ===

def generate_hubble_constant_measurements(n: int = 100, method: str = "BAO") -> np.ndarray:
    """Generate H0 measurements following real observational distributions."""
    if method == "BAO":
        return np.random.normal(67.4, 0.5, n)  # Planck 2018
    elif method == "SNeIa":
        return np.random.normal(73.04, 1.04, n)  # SH0ES 2022
    elif method == "CMB":
        return np.random.normal(67.36, 0.54, n)  # Planck 2018
    elif method == "GW":
        return np.random.normal(68.3, 4.0, n)  # LIGO constraints
    else:
        return np.random.normal(70.0, 2.0, n)


def generate_galaxy_luminosity_function(n: int = 1000) -> np.ndarray:
    """Schechter luminosity function: real distribution."""
    phi_star = 1.5e-3  # Mpc^-3
    M_star = -20.83 + 5 * np.log10(0.7)  # Absolute magnitude
    alpha = -1.07

    M = np.linspace(-24, -16, n)
    phi = 0.4 * np.log(10) * phi_star * (10 ** (0.4 * (M_star - M))) ** (alpha + 1) * \
          np.exp(-10 ** (0.4 * (M_star - M)))
    return phi


def generate_rotation_curve(r: np.ndarray, v_flat: float = 220,
                            r_scale: float = 2.0) -> np.ndarray:
    """Realistic rotation curve (NFW-like profile)."""
    return v_flat * (1 - np.exp(-r / r_scale))


def generate_mcmc_chain(n_steps: int = 1000, h0_true: float = 68.5,
                        sigma: float = 0.8) -> np.ndarray:
    """Simple Metropolis-Hastings MCMC for H0 estimation."""
    chain = np.zeros(n_steps)
    chain[0] = 70.0
    for i in range(1, n_steps):
        proposal = chain[i-1] + np.random.normal(0, 0.5)
        # Likelihood: exp(-(h-h0)^2 / 2σ^2)
        log_lik_current = -0.5 * ((chain[i-1] - h0_true) / sigma) ** 2
        log_lik_proposal = -0.5 * ((proposal - h0_true) / sigma) ** 2
        log_alpha = log_lik_proposal - log_lik_current
        if np.log(np.random.random()) < log_alpha:
            chain[i] = proposal
        else:
            chain[i] = chain[i-1]
    return chain


# ============================================================
#   Phase 7.2 — Confounder Detection (Backdoor Criterion Proxy)
# ============================================================

def backdoor_criterion_test(data: 'pd.DataFrame', cause: str, effect: str,
                            potential_confounders: list, alpha: float = 0.05) -> dict:
    """
    Test for confounders using a proxy for the backdoor criterion.
    For each potential confounder Z:
      1. Regress cause ~ Z → get residuals
      2. Regress effect ~ Z → get residuals
      3. Correlate residuals (confounder-adjusted effect)
      4. Compare adjusted vs unadjusted effect size
    Returns dict with confounders_detected, adjusted/unadjusted effect, confounding bias.
    """
    import pandas as pd

    cause_data = data[cause].values.astype(float)
    effect_data = data[effect].values.astype(float)

    # Unadjusted correlation
    valid = np.isfinite(cause_data) & np.isfinite(effect_data)
    if valid.sum() < 10:
        return {
            "confounders_detected": [],
            "adjusted_effect": 0.0,
            "unadjusted_effect": 0.0,
            "confounding_bias": 0.0,
            "error": "Insufficient valid data points",
        }

    unadj_r, unadj_p = stats.pearsonr(cause_data[valid], effect_data[valid])
    unadj_effect = float(unadj_r)

    confounders_detected = []

    for z_name in potential_confounders:
        if z_name in (cause, effect):
            continue
        z_data = data[z_name].values.astype(float)
        mask = valid & np.isfinite(z_data)
        if mask.sum() < 10:
            continue

        c, e, z = cause_data[mask], effect_data[mask], z_data[mask]

        # Regress cause ~ Z
        z_mean = z - z.mean()
        z_var = np.dot(z_mean, z_mean)
        if z_var < 1e-12:
            continue
        beta_cz = np.dot(z_mean, c - c.mean()) / z_var
        residual_c = c - (c.mean() + beta_cz * z_mean)

        # Regress effect ~ Z
        beta_ez = np.dot(z_mean, e - e.mean()) / z_var
        residual_e = e - (e.mean() + beta_ez * z_mean)

        # Adjusted correlation (partial correlation)
        if np.std(residual_c) < 1e-12 or np.std(residual_e) < 1e-12:
            continue
        adj_r, adj_p = stats.pearsonr(residual_c, residual_e)

        # Bias = |unadjusted| - |adjusted|: positive means Z inflated the association
        bias = abs(unadj_r) - abs(adj_r)

        # Is Z associated with both cause and effect?
        _, p_zc = stats.pearsonr(z, c)
        _, p_ze = stats.pearsonr(z, e)

        confounders_detected.append({
            "variable": z_name,
            "unadjusted_r": round(float(unadj_r), 5),
            "adjusted_r": round(float(adj_r), 5),
            "bias_magnitude": round(float(bias), 5),
            "p_cause_z": round(float(p_zc), 6),
            "p_effect_z": round(float(p_ze), 6),
            "adj_p_value": round(float(adj_p), 6),
            "is_confounder": bool(p_zc < alpha and p_ze < alpha and abs(bias) > 0.02),
        })

    # Sort by bias magnitude (largest first)
    confounders_detected.sort(key=lambda x: abs(x["bias_magnitude"]), reverse=True)

    # Best adjusted effect = effect after conditioning on strongest confounder
    if confounders_detected and confounders_detected[0]["is_confounder"]:
        adj_effect = confounders_detected[0]["adjusted_r"]
    else:
        adj_effect = unadj_effect

    return {
        "confounders_detected": confounders_detected,
        "adjusted_effect": round(float(adj_effect), 5),
        "unadjusted_effect": round(float(unadj_effect), 5),
        "confounding_bias": round(float(unadj_effect - adj_effect), 5),
    }


def detect_confounders(df: 'pd.DataFrame', cause: str, effect: str,
                       alpha: float = 0.05) -> dict:
    """
    High-level confounder detection:
      1. Identifies potential confounders as all other numeric columns
      2. Runs backdoor_criterion_test for each
      3. Applies FDR correction to the confounder significance tests
      4. Returns ranked list of confirmed confounders with bias magnitude
    """
    import pandas as pd

    # Identify numeric columns (potential confounders)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    potential = [c for c in numeric_cols if c not in (cause, effect)]

    if not potential:
        return {
            "cause": cause,
            "effect": effect,
            "n_candidates": 0,
            "confirmed_confounders": [],
            "fdr_corrected": False,
            "summary": f"No numeric confounders to test for {cause} → {effect}",
        }

    # Run backdoor criterion test
    result = backdoor_criterion_test(df, cause, effect, potential, alpha)

    detected = result.get("confounders_detected", [])

    # FDR correction on p-values for Z→cause and Z→effect associations
    if detected:
        # Use the product of p_cause_z and p_effect_z as joint significance
        p_values = [max(d["p_cause_z"], d["p_effect_z"]) for d in detected]
        fdr_result = fdr_correction(p_values, alpha)

        for i, d in enumerate(detected):
            d["fdr_significant"] = fdr_result["rejected_mask"][i] if i < len(fdr_result["rejected_mask"]) else False
            d["fdr_adjusted_p"] = fdr_result["adjusted_p_values"][i] if i < len(fdr_result["adjusted_p_values"]) else 1.0

        confirmed = [d for d in detected if d.get("fdr_significant") and d["is_confounder"]]
    else:
        confirmed = []
        fdr_result = None

    return {
        "cause": cause,
        "effect": effect,
        "n_candidates": len(potential),
        "n_tested": len(detected),
        "confirmed_confounders": confirmed,
        "all_candidates": detected,
        "unadjusted_effect": result.get("unadjusted_effect", 0),
        "adjusted_effect": result.get("adjusted_effect", 0),
        "confounding_bias": result.get("confounding_bias", 0),
        "fdr_corrected": fdr_result is not None,
        "summary": (
            f"Tested {len(potential)} candidates for {cause} → {effect}: "
            f"{len(confirmed)} confirmed confounders "
            f"(bias: {result.get('confounding_bias', 0):.4f})"
        ),
    }
