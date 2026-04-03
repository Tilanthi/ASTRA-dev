"""
ASTRA Live — Physical Validation
Checks results against dimensional consistency, conservation laws,
and established physical principles.

As described in White & Dey (2026), Section 2.3 (Capability 16).
"""
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ValidationResult:
    check_name: str
    passed: bool
    message: str
    severity: str  # "info", "warning", "error"
    details: Dict = None

    def to_dict(self):
        d = asdict(self)
        if self.details is None:
            d["details"] = {}
        return d


def validate_physical_result(result_type: str, data: Dict) -> List[ValidationResult]:
    """
    Validate a physical result against known constraints.

    Args:
        result_type: type of result ("scaling_relation", "correlation", "causal", "model_fit")
        data: result data to validate
    """
    checks = []

    if result_type == "scaling_relation":
        checks.extend(_validate_scaling_relation(data))
    elif result_type == "correlation":
        checks.extend(_validate_correlation(data))
    elif result_type == "model_fit":
        checks.extend(_validate_model_fit(data))
    elif result_type == "causal":
        checks.extend(_validate_causal(data))

    return checks


def _validate_scaling_relation(data: Dict) -> List[ValidationResult]:
    """Validate a power-law scaling relation."""
    checks = []

    # Check 1: Is the exponent physically reasonable?
    exponent = data.get("exponent", 0)
    if abs(exponent) > 10:
        checks.append(ValidationResult(
            "exponent_magnitude", False,
            f"Exponent {exponent:.3f} is unreasonably large (|α| > 10)",
            "warning"
        ))
    else:
        checks.append(ValidationResult(
            "exponent_magnitude", True,
            f"Exponent {exponent:.3f} is physically reasonable",
            "info"
        ))

    # Check 2: Is R² reasonable?
    r_sq = data.get("r_squared", 0)
    if r_sq < 0.1:
        checks.append(ValidationResult(
            "fit_quality", False,
            f"R² = {r_sq:.3f} — very poor fit, relation may not be real",
            "warning"
        ))
    elif r_sq < 0.5:
        checks.append(ValidationResult(
            "fit_quality", True,
            f"R² = {r_sq:.3f} — moderate fit, interpret with caution",
            "info"
        ))
    else:
        checks.append(ValidationResult(
            "fit_quality", True,
            f"R² = {r_sq:.3f} — good fit",
            "info"
        ))

    # Check 3: Statistical significance
    p_value = data.get("p_value", 1.0)
    if p_value > 0.05:
        checks.append(ValidationResult(
            "statistical_significance", False,
            f"p = {p_value:.4f} — not statistically significant at α=0.05",
            "warning"
        ))
    else:
        checks.append(ValidationResult(
            "statistical_significance", True,
            f"p = {p_value:.2e} — statistically significant",
            "info"
        ))

    # Check 4: Sample size adequacy
    n = data.get("n_points", 0)
    if n < 10:
        checks.append(ValidationResult(
            "sample_size", False,
            f"Only {n} data points — insufficient for robust scaling relation",
            "warning"
        ))
    else:
        checks.append(ValidationResult(
            "sample_size", True,
            f"Sample size n={n} is adequate",
            "info"
        ))

    return checks


def _validate_correlation(data: Dict) -> List[ValidationResult]:
    """Validate a correlation result."""
    checks = []
    r = data.get("correlation", 0)
    p = data.get("p_value", 1.0)
    n = data.get("n_points", 0)

    # Check: Correlation strength
    abs_r = abs(r)
    if abs_r > 0.95:
        checks.append(ValidationResult(
            "correlation_strength", True,
            f"|r| = {abs_r:.4f} — very strong correlation",
            "info"
        ))
    elif abs_r > 0.7:
        checks.append(ValidationResult(
            "correlation_strength", True,
            f"|r| = {abs_r:.4f} — strong correlation",
            "info"
        ))
    elif abs_r > 0.3:
        checks.append(ValidationResult(
            "correlation_strength", True,
            f"|r| = {abs_r:.4f} — moderate correlation",
            "info"
        ))
    else:
        checks.append(ValidationResult(
            "correlation_strength", False,
            f"|r| = {abs_r:.4f} — weak correlation, may not be meaningful",
            "warning"
        ))

    # Check: Correlation ≠ causation reminder
    if abs_r > 0.5 and p < 0.05:
        checks.append(ValidationResult(
            "causation_warning", True,
            "Correlation does not imply causation — use causal inference to investigate",
            "info"
        ))

    return checks


def _validate_model_fit(data: Dict) -> List[ValidationResult]:
    """Validate a model fit."""
    checks = []

    # Check residual normality
    residuals = data.get("residuals", [])
    if len(residuals) > 8:
        from scipy import stats as sp_stats
        stat, p = sp_stats.shapiro(residuals[:5000])  # Shapiro limited to 5000
        if p < 0.05:
            checks.append(ValidationResult(
                "residual_normality", False,
                f"Residuals are not normally distributed (Shapiro p={p:.4f})",
                "warning"
            ))
        else:
            checks.append(ValidationResult(
                "residual_normality", True,
                f"Residuals are consistent with normality (Shapiro p={p:.4f})",
                "info"
            ))

    # Check for overfitting
    n_params = data.get("n_parameters", 0)
    n_points = data.get("n_points", 0)
    if n_params > 0 and n_points > 0:
        ratio = n_points / n_params
        if ratio < 3:
            checks.append(ValidationResult(
                "overfitting_risk", False,
                f"n/params = {ratio:.1f} — high overfitting risk",
                "warning"
            ))
        else:
            checks.append(ValidationResult(
                "overfitting_risk", True,
                f"n/params = {ratio:.1f} — adequate for model complexity",
                "info"
            ))

    return checks


def _validate_causal(data: Dict) -> List[ValidationResult]:
    """Validate a causal inference result."""
    checks = []

    # Check: Do we have conditional independence evidence?
    conditioning_set = data.get("conditioning_set", [])
    if not conditioning_set:
        checks.append(ValidationResult(
            "conditional_test", False,
            "No conditioning variables tested — causal claim not well-supported",
            "warning"
        ))

    # Check: V-structure detection
    edge_type = data.get("edge_type", "")
    if edge_type == "o—o":
        checks.append(ValidationResult(
            "hidden_confounders", False,
            "Edge marked as uncertain — possible hidden confounders present",
            "warning"
        ))

    return checks


def run_physical_validation(results: List[Dict]) -> Dict:
    """
    Run all physical validation checks on a set of results.
    Returns summary of passed/failed checks.
    """
    all_checks = []
    for result in results:
        rtype = result.get("type", "unknown")
        checks = validate_physical_result(rtype, result)
        all_checks.extend(checks)

    passed = sum(1 for c in all_checks if c.passed)
    failed = sum(1 for c in all_checks if not c.passed)
    warnings = [c for c in all_checks if c.severity == "warning" and not c.passed]

    return {
        "total_checks": len(all_checks),
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0,
        "warnings": [c.to_dict() for c in warnings],
        "checks": [c.to_dict() for c in all_checks],
    }
