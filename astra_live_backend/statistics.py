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
