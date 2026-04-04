"""
Calibrated Confidence Estimation for STAN V42

Ensures that stated confidence levels match actual frequencies of correctness.
Implements multiple calibration techniques:

- Platt scaling for probability calibration
- Isotonic regression for non-parametric calibration
- Temperature scaling for neural predictions
- Bayesian calibration with proper scoring rules
- Coverage analysis for credible intervals

Properly calibrated confidence is essential for:
- Honest scientific claims
- Optimal decision making under uncertainty
- Meta-analysis and evidence combination
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
import math
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class CalibrationMethod(Enum):
    """Methods for probability calibration."""
    PLATT_SCALING = "platt"           # Logistic regression
    ISOTONIC = "isotonic"             # Non-parametric monotonic
    TEMPERATURE = "temperature"        # Single temperature parameter
    BETA = "beta"                      # Beta calibration
    HISTOGRAM = "histogram"            # Binned calibration
    BAYESIAN = "bayesian"              # Full Bayesian approach


@dataclass
class CalibrationResult:
    """Result of calibration analysis."""
    method: CalibrationMethod
    original_probabilities: List[float]
    calibrated_probabilities: List[float]
    calibration_parameters: Dict[str, float]
    reliability_diagram: Dict[str, List[float]]  # bin_centers, accuracies, counts
    expected_calibration_error: float  # ECE
    maximum_calibration_error: float   # MCE
    brier_score: float
    log_loss: float


@dataclass
class CoverageAnalysis:
    """Analysis of credible interval coverage."""
    nominal_level: float
    empirical_coverage: float
    n_samples: int
    coverage_per_parameter: Dict[str, float]
    interval_widths: Dict[str, float]
    calibration_factor: float  # Multiply intervals by this for calibration
    is_well_calibrated: bool


@dataclass
class ConfidenceScore:
    """A calibrated confidence score for a prediction."""
    raw_confidence: float
    calibrated_confidence: float
    uncertainty_type: str  # "epistemic", "aleatoric", "total"
    calibration_method: CalibrationMethod
    reliability: float  # How reliable is this calibration


# ============================================================================
# Calibration Metrics
# ============================================================================

class CalibrationMetrics:
    """
    Computes calibration metrics and diagnostics.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins

    def reliability_diagram(self,
                           probabilities: List[float],
                           outcomes: List[int]) -> Tuple[List[float], List[float], List[int]]:
        """
        Compute reliability diagram data.

        Returns: (bin_centers, accuracies, counts)
        """
        bin_boundaries = [i / self.n_bins for i in range(self.n_bins + 1)]
        bin_centers = [(bin_boundaries[i] + bin_boundaries[i + 1]) / 2
                      for i in range(self.n_bins)]

        bin_accuracies = []
        bin_counts = []

        for i in range(self.n_bins):
            low = bin_boundaries[i]
            high = bin_boundaries[i + 1]

            # Get samples in this bin
            in_bin = [(p, o) for p, o in zip(probabilities, outcomes)
                     if low <= p < high]

            if in_bin:
                accuracy = sum(o for _, o in in_bin) / len(in_bin)
                bin_accuracies.append(accuracy)
                bin_counts.append(len(in_bin))
            else:
                bin_accuracies.append(0.0)
                bin_counts.append(0)

        return bin_centers, bin_accuracies, bin_counts

    def expected_calibration_error(self,
                                   probabilities: List[float],
                                   outcomes: List[int]) -> float:
        """
        Compute Expected Calibration Error (ECE).

        ECE = Σ (n_b / N) |acc(b) - conf(b)|
        """
        n = len(probabilities)
        if n == 0:
            return 0.0

        bin_centers, bin_accuracies, bin_counts = self.reliability_diagram(
            probabilities, outcomes
        )

        ece = 0.0
        for center, acc, count in zip(bin_centers, bin_accuracies, bin_counts):
            if count > 0:
                ece += (count / n) * abs(acc - center)

        return ece

    def maximum_calibration_error(self,
                                  probabilities: List[float],
                                  outcomes: List[int]) -> float:
        """
        Compute Maximum Calibration Error (MCE).

        MCE = max_b |acc(b) - conf(b)|
        """
        bin_centers, bin_accuracies, bin_counts = self.reliability_diagram(
            probabilities, outcomes
        )

        mce = 0.0
        for center, acc, count in zip(bin_centers, bin_accuracies, bin_counts):
            if count > 0:
                mce = max(mce, abs(acc - center))

        return mce

    def brier_score(self,
                   probabilities: List[float],
                   outcomes: List[int]) -> float:
        """
        Compute Brier score (mean squared error).

        Lower is better. Range [0, 1].
        """
        if not probabilities:
            return 1.0

        return sum((p - o) ** 2 for p, o in zip(probabilities, outcomes)) / len(probabilities)

    def log_loss(self,
                probabilities: List[float],
                outcomes: List[int],
                eps: float = 1e-15) -> float:
        """
        Compute log loss (cross-entropy).

        Lower is better.
        """
        if not probabilities:
            return float('inf')

        total = 0.0
        for p, o in zip(probabilities, outcomes):
            p_clipped = max(eps, min(1 - eps, p))
            if o == 1:
                total -= math.log(p_clipped)
            else:
                total -= math.log(1 - p_clipped)

        return total / len(probabilities)


# ============================================================================
# Platt Scaling Calibrator
# ============================================================================

class PlattScalingCalibrator:
    """
    Platt scaling: fit logistic regression to map scores to probabilities.
    P(y=1|s) = 1 / (1 + exp(A*s + B))
    """

    def __init__(self):
        self.A = 0.0
        self.B = 0.0
        self.fitted = False

    def fit(self,
           scores: List[float],
           labels: List[int],
           max_iterations: int = 100,
           tolerance: float = 1e-6):
        """
        Fit Platt scaling parameters using Newton's method.
        """
        n = len(scores)
        if n == 0:
            return

        n_pos = sum(labels)
        n_neg = n - n_pos

        # Target probabilities for regularization
        t_plus = (n_pos + 1) / (n_pos + 2)
        t_minus = 1 / (n_neg + 2)
        targets = [t_plus if l == 1 else t_minus for l in labels]

        # Initialize
        self.A = 0.0
        self.B = math.log((n_neg + 1) / (n_pos + 1))

        # Newton's method
        for iteration in range(max_iterations):
            # Compute probabilities
            probs = [self._sigmoid(self.A * s + self.B) for s in scores]

            # Gradient
            grad_A = sum((t - p) * s for s, t, p in zip(scores, targets, probs))
            grad_B = sum(t - p for t, p in zip(targets, probs))

            # Hessian
            hess_AA = sum(p * (1 - p) * s * s for s, p in zip(scores, probs))
            hess_AB = sum(p * (1 - p) * s for s, p in zip(scores, probs))
            hess_BB = sum(p * (1 - p) for p in probs)

            # Regularization
            hess_AA += 1e-6
            hess_BB += 1e-6

            # Newton update
            det = hess_AA * hess_BB - hess_AB * hess_AB
            if abs(det) < 1e-10:
                break

            delta_A = (hess_BB * grad_A - hess_AB * grad_B) / det
            delta_B = (hess_AA * grad_B - hess_AB * grad_A) / det

            self.A += delta_A
            self.B += delta_B

            # Check convergence
            if abs(delta_A) < tolerance and abs(delta_B) < tolerance:
                break

        self.fitted = True

    def calibrate(self, score: float) -> float:
        """Apply Platt scaling to a score."""
        if not self.fitted:
            return self._sigmoid(score)

        return self._sigmoid(self.A * score + self.B)

    def calibrate_batch(self, scores: List[float]) -> List[float]:
        """Apply Platt scaling to multiple scores."""
        return [self.calibrate(s) for s in scores]

    def _sigmoid(self, x: float) -> float:
        """Sigmoid function with overflow protection."""
        if x >= 0:
            z = math.exp(-x)
            return 1 / (1 + z)
        else:
            z = math.exp(x)
            return z / (1 + z)


# ============================================================================
# Isotonic Regression Calibrator
# ============================================================================

class IsotonicCalibrator:
    """
    Isotonic regression: non-parametric monotonically increasing calibration.
    """

    def __init__(self):
        self.x_thresholds: List[float] = []
        self.y_values: List[float] = []
        self.fitted = False

    def fit(self, scores: List[float], labels: List[int]):
        """
        Fit isotonic regression using Pool Adjacent Violators (PAV) algorithm.
        """
        n = len(scores)
        if n == 0:
            return

        # Sort by score
        sorted_pairs = sorted(zip(scores, labels))
        x_sorted = [p[0] for p in sorted_pairs]
        y_sorted = [float(p[1]) for p in sorted_pairs]

        # PAV algorithm
        blocks = [[y_sorted[i], 1, i, i] for i in range(n)]  # [sum, count, start, end]

        i = 0
        while i < len(blocks) - 1:
            # Average of current block
            avg_current = blocks[i][0] / blocks[i][1]
            avg_next = blocks[i + 1][0] / blocks[i + 1][1]

            if avg_current > avg_next:
                # Merge blocks
                blocks[i][0] += blocks[i + 1][0]
                blocks[i][1] += blocks[i + 1][1]
                blocks[i][3] = blocks[i + 1][3]
                blocks.pop(i + 1)

                # Go back to check previous
                if i > 0:
                    i -= 1
            else:
                i += 1

        # Extract thresholds and values
        self.x_thresholds = []
        self.y_values = []

        for block in blocks:
            avg = block[0] / block[1]
            start_idx = block[2]
            end_idx = block[3]

            self.x_thresholds.append(x_sorted[start_idx])
            self.y_values.append(avg)

        self.fitted = True

    def calibrate(self, score: float) -> float:
        """Apply isotonic calibration to a score."""
        if not self.fitted or not self.x_thresholds:
            return score

        # Binary search for appropriate block
        if score <= self.x_thresholds[0]:
            return self.y_values[0]

        if score >= self.x_thresholds[-1]:
            return self.y_values[-1]

        # Find interval
        for i in range(len(self.x_thresholds) - 1):
            if self.x_thresholds[i] <= score < self.x_thresholds[i + 1]:
                # Linear interpolation
                frac = ((score - self.x_thresholds[i]) /
                       (self.x_thresholds[i + 1] - self.x_thresholds[i]))
                return self.y_values[i] + frac * (self.y_values[i + 1] - self.y_values[i])

        return self.y_values[-1]

    def calibrate_batch(self, scores: List[float]) -> List[float]:
        """Apply isotonic calibration to multiple scores."""
        return [self.calibrate(s) for s in scores]


# ============================================================================
# Temperature Scaling Calibrator
# ============================================================================

class TemperatureScalingCalibrator:
    """
    Temperature scaling: single parameter calibration.
    P_calibrated = softmax(logits / T)
    """

    def __init__(self):
        self.temperature = 1.0
        self.fitted = False

    def fit(self,
           logits: List[float],
           labels: List[int],
           max_iterations: int = 50):
        """
        Fit temperature using gradient descent on NLL.
        """
        n = len(logits)
        if n == 0:
            return

        # Grid search for good initialization
        best_nll = float('inf')
        best_temp = 1.0

        for t in [0.1, 0.5, 1.0, 2.0, 5.0]:
            nll = self._compute_nll(logits, labels, t)
            if nll < best_nll:
                best_nll = nll
                best_temp = t

        self.temperature = best_temp

        # Fine-tune with gradient descent
        learning_rate = 0.01

        for _ in range(max_iterations):
            # Compute gradient
            grad = self._compute_gradient(logits, labels)

            # Update
            self.temperature -= learning_rate * grad

            # Clamp
            self.temperature = max(0.01, min(10.0, self.temperature))

        self.fitted = True

    def _compute_nll(self, logits: List[float], labels: List[int], temp: float) -> float:
        """Compute negative log likelihood."""
        nll = 0.0
        for logit, label in zip(logits, labels):
            prob = self._sigmoid(logit / temp)
            if label == 1:
                nll -= math.log(max(1e-15, prob))
            else:
                nll -= math.log(max(1e-15, 1 - prob))
        return nll / len(logits)

    def _compute_gradient(self, logits: List[float], labels: List[int]) -> float:
        """Compute gradient of NLL with respect to temperature."""
        grad = 0.0
        t = self.temperature

        for logit, label in zip(logits, labels):
            prob = self._sigmoid(logit / t)
            dprob_dt = -logit / (t * t) * prob * (1 - prob)

            if label == 1:
                grad -= dprob_dt / max(1e-15, prob)
            else:
                grad += dprob_dt / max(1e-15, 1 - prob)

        return grad / len(logits)

    def calibrate(self, logit: float) -> float:
        """Apply temperature scaling to a logit."""
        return self._sigmoid(logit / self.temperature)

    def calibrate_batch(self, logits: List[float]) -> List[float]:
        """Apply temperature scaling to multiple logits."""
        return [self.calibrate(l) for l in logits]

    def _sigmoid(self, x: float) -> float:
        """Sigmoid function."""
        if x >= 0:
            return 1 / (1 + math.exp(-x))
        else:
            z = math.exp(x)
            return z / (1 + z)


# ============================================================================
# Coverage Calibrator for Credible Intervals
# ============================================================================

class CoverageCalibrator:
    """
    Calibrates credible intervals to achieve proper coverage.
    """

    def __init__(self):
        self.calibration_factors: Dict[float, float] = {}  # nominal -> factor
        self.coverage_history: List[CoverageAnalysis] = []

    def analyze_coverage(self,
                        predictions: List[Dict[str, float]],
                        uncertainties: List[Dict[str, float]],
                        true_values: List[Dict[str, float]],
                        nominal_level: float = 0.95) -> CoverageAnalysis:
        """
        Analyze coverage of credible intervals.

        Args:
            predictions: List of {parameter: predicted_value}
            uncertainties: List of {parameter: std_dev}
            true_values: List of {parameter: true_value}
            nominal_level: Nominal coverage level (e.g., 0.95 for 95%)
        """
        n = len(predictions)
        if n == 0:
            return CoverageAnalysis(
                nominal_level=nominal_level,
                empirical_coverage=0.0,
                n_samples=0,
                coverage_per_parameter={},
                interval_widths={},
                calibration_factor=1.0,
                is_well_calibrated=False
            )

        # Z-score for nominal level
        z = self._normal_quantile((1 + nominal_level) / 2)

        # Collect all parameters
        all_params = set()
        for pred in predictions:
            all_params.update(pred.keys())

        # Compute coverage per parameter
        coverage_counts = {p: 0 for p in all_params}
        total_counts = {p: 0 for p in all_params}
        interval_widths = {p: [] for p in all_params}

        for pred, unc, true in zip(predictions, uncertainties, true_values):
            for param in pred:
                if param not in true or param not in unc:
                    continue

                total_counts[param] += 1

                # Check if true value is within interval
                half_width = z * unc[param]
                interval_widths[param].append(2 * half_width)

                if abs(true[param] - pred[param]) <= half_width:
                    coverage_counts[param] += 1

        # Coverage per parameter
        coverage_per_param = {}
        for p in all_params:
            if total_counts[p] > 0:
                coverage_per_param[p] = coverage_counts[p] / total_counts[p]
            else:
                coverage_per_param[p] = 0.0

        # Overall coverage
        total_covered = sum(coverage_counts.values())
        total_samples = sum(total_counts.values())
        empirical_coverage = total_covered / total_samples if total_samples > 0 else 0.0

        # Mean interval widths
        mean_widths = {p: sum(w) / len(w) if w else 0.0
                      for p, w in interval_widths.items()}

        # Calibration factor to achieve nominal coverage
        calibration_factor = self._estimate_calibration_factor(
            empirical_coverage, nominal_level
        )

        # Check if well-calibrated
        is_calibrated = abs(empirical_coverage - nominal_level) < 0.05

        analysis = CoverageAnalysis(
            nominal_level=nominal_level,
            empirical_coverage=empirical_coverage,
            n_samples=n,
            coverage_per_parameter=coverage_per_param,
            interval_widths=mean_widths,
            calibration_factor=calibration_factor,
            is_well_calibrated=is_calibrated
        )

        self.coverage_history.append(analysis)
        self.calibration_factors[nominal_level] = calibration_factor

        return analysis

    def calibrate_interval(self,
                          mean: float,
                          std: float,
                          nominal_level: float = 0.95) -> Tuple[float, float]:
        """
        Return calibrated confidence interval.
        """
        z = self._normal_quantile((1 + nominal_level) / 2)

        # Apply calibration factor if available
        factor = self.calibration_factors.get(nominal_level, 1.0)
        calibrated_std = std * factor

        half_width = z * calibrated_std

        return (mean - half_width, mean + half_width)

    def _estimate_calibration_factor(self,
                                    empirical: float,
                                    nominal: float) -> float:
        """
        Estimate factor to multiply uncertainties by for calibration.
        """
        if empirical >= nominal:
            # Already overcovering, reduce intervals
            return 1.0

        if empirical < 0.01:
            return 3.0  # Major undercoverage

        # Approximate: if coverage is too low, uncertainties are too small
        # Use normal distribution assumption
        z_nominal = self._normal_quantile((1 + nominal) / 2)
        z_empirical = self._normal_quantile((1 + empirical) / 2)

        if z_empirical > 0:
            factor = z_nominal / z_empirical
        else:
            factor = 2.0

        return max(0.5, min(3.0, factor))

    def _normal_quantile(self, p: float) -> float:
        """Approximate inverse normal CDF."""
        # Abramowitz and Stegun approximation
        if p <= 0:
            return -10.0
        if p >= 1:
            return 10.0

        if p < 0.5:
            return -self._normal_quantile(1 - p)

        t = math.sqrt(-2 * math.log(1 - p))
        c0 = 2.515517
        c1 = 0.802853
        c2 = 0.010328
        d1 = 1.432788
        d2 = 0.189269
        d3 = 0.001308

        return t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)


# ============================================================================
# Main Calibrated Confidence Estimator
# ============================================================================

class CalibratedConfidenceEstimator:
    """
    Main class for calibrated confidence estimation.
    """

    def __init__(self,
                 default_method: CalibrationMethod = CalibrationMethod.ISOTONIC):
        self.default_method = default_method

        # Calibrators
        self.platt_calibrator = PlattScalingCalibrator()
        self.isotonic_calibrator = IsotonicCalibrator()
        self.temperature_calibrator = TemperatureScalingCalibrator()
        self.coverage_calibrator = CoverageCalibrator()

        # Metrics
        self.metrics = CalibrationMetrics()

        # Calibration history
        self.calibration_results: List[CalibrationResult] = []

        self._event_bus = None

    def set_event_bus(self, event_bus):
        """Set event bus for integration."""
        self._event_bus = event_bus

    def fit_calibrator(self,
                      method: CalibrationMethod,
                      scores: List[float],
                      labels: List[int]) -> CalibrationResult:
        """
        Fit a calibrator to validation data.
        """
        original_probs = scores.copy()

        if method == CalibrationMethod.PLATT_SCALING:
            self.platt_calibrator.fit(scores, labels)
            calibrated = self.platt_calibrator.calibrate_batch(scores)
            params = {"A": self.platt_calibrator.A, "B": self.platt_calibrator.B}

        elif method == CalibrationMethod.ISOTONIC:
            self.isotonic_calibrator.fit(scores, labels)
            calibrated = self.isotonic_calibrator.calibrate_batch(scores)
            params = {"n_segments": len(self.isotonic_calibrator.x_thresholds)}

        elif method == CalibrationMethod.TEMPERATURE:
            self.temperature_calibrator.fit(scores, labels)
            calibrated = self.temperature_calibrator.calibrate_batch(scores)
            params = {"temperature": self.temperature_calibrator.temperature}

        else:
            # Default to isotonic
            self.isotonic_calibrator.fit(scores, labels)
            calibrated = self.isotonic_calibrator.calibrate_batch(scores)
            params = {}

        # Compute metrics
        bin_centers, bin_accs, bin_counts = self.metrics.reliability_diagram(calibrated, labels)
        ece = self.metrics.expected_calibration_error(calibrated, labels)
        mce = self.metrics.maximum_calibration_error(calibrated, labels)
        brier = self.metrics.brier_score(calibrated, labels)
        logloss = self.metrics.log_loss(calibrated, labels)

        result = CalibrationResult(
            method=method,
            original_probabilities=original_probs,
            calibrated_probabilities=calibrated,
            calibration_parameters=params,
            reliability_diagram={
                "bin_centers": bin_centers,
                "accuracies": bin_accs,
                "counts": bin_counts
            },
            expected_calibration_error=ece,
            maximum_calibration_error=mce,
            brier_score=brier,
            log_loss=logloss
        )

        self.calibration_results.append(result)

        # Emit event
        if self._event_bus:
            self._event_bus.publish(
                "calibration_fitted",
                "calibrated_confidence",
                {
                    "method": method.value,
                    "ece": ece,
                    "mce": mce,
                    "brier": brier
                }
            )

        return result

    def calibrate_probability(self,
                             raw_probability: float,
                             method: Optional[CalibrationMethod] = None) -> ConfidenceScore:
        """
        Calibrate a raw probability score.
        """
        method = method or self.default_method

        if method == CalibrationMethod.PLATT_SCALING and self.platt_calibrator.fitted:
            calibrated = self.platt_calibrator.calibrate(raw_probability)
            reliability = 0.9 if abs(self.platt_calibrator.A) < 10 else 0.5

        elif method == CalibrationMethod.ISOTONIC and self.isotonic_calibrator.fitted:
            calibrated = self.isotonic_calibrator.calibrate(raw_probability)
            reliability = 0.85

        elif method == CalibrationMethod.TEMPERATURE and self.temperature_calibrator.fitted:
            calibrated = self.temperature_calibrator.calibrate(raw_probability)
            reliability = 0.8

        else:
            calibrated = raw_probability
            reliability = 0.5

        return ConfidenceScore(
            raw_confidence=raw_probability,
            calibrated_confidence=calibrated,
            uncertainty_type="total",
            calibration_method=method,
            reliability=reliability
        )

    def calibrate_credible_interval(self,
                                   mean: float,
                                   std: float,
                                   level: float = 0.95) -> Tuple[float, float]:
        """
        Return calibrated credible interval.
        """
        return self.coverage_calibrator.calibrate_interval(mean, std, level)

    def analyze_calibration(self,
                           probabilities: List[float],
                           outcomes: List[int]) -> Dict[str, float]:
        """
        Analyze calibration quality of given probabilities.
        """
        return {
            "ece": self.metrics.expected_calibration_error(probabilities, outcomes),
            "mce": self.metrics.maximum_calibration_error(probabilities, outcomes),
            "brier_score": self.metrics.brier_score(probabilities, outcomes),
            "log_loss": self.metrics.log_loss(probabilities, outcomes)
        }

    def select_best_method(self,
                          scores: List[float],
                          labels: List[int],
                          methods: Optional[List[CalibrationMethod]] = None) -> CalibrationMethod:
        """
        Select best calibration method based on validation data.
        """
        methods = methods or [
            CalibrationMethod.PLATT_SCALING,
            CalibrationMethod.ISOTONIC,
            CalibrationMethod.TEMPERATURE
        ]

        best_method = methods[0]
        best_ece = float('inf')

        for method in methods:
            result = self.fit_calibrator(method, scores.copy(), labels.copy())

            if result.expected_calibration_error < best_ece:
                best_ece = result.expected_calibration_error
                best_method = method

        logger.info(f"Selected {best_method.value} calibration (ECE={best_ece:.4f})")

        return best_method

    def get_calibration_summary(self) -> Dict[str, Any]:
        """Get summary of calibration performance."""
        if not self.calibration_results:
            return {"status": "No calibration performed"}

        latest = self.calibration_results[-1]

        return {
            "method": latest.method.value,
            "ece": latest.expected_calibration_error,
            "mce": latest.maximum_calibration_error,
            "brier_score": latest.brier_score,
            "log_loss": latest.log_loss,
            "parameters": latest.calibration_parameters,
            "n_calibration_runs": len(self.calibration_results),
            "coverage_analyses": len(self.coverage_calibrator.coverage_history)
        }


# ============================================================================
# Bayesian Calibration
# ============================================================================

class BayesianCalibrator:
    """
    Full Bayesian approach to probability calibration.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        self.posterior_alpha: List[float] = []
        self.posterior_beta: List[float] = []
        self.fitted = False

    def fit(self,
           probabilities: List[float],
           outcomes: List[int],
           prior_strength: float = 1.0):
        """
        Fit Bayesian calibration using Beta-Binomial model per bin.
        """
        # Initialize with uniform prior
        self.posterior_alpha = [prior_strength] * self.n_bins
        self.posterior_beta = [prior_strength] * self.n_bins

        # Bin the data
        for prob, outcome in zip(probabilities, outcomes):
            bin_idx = min(int(prob * self.n_bins), self.n_bins - 1)

            if outcome == 1:
                self.posterior_alpha[bin_idx] += 1
            else:
                self.posterior_beta[bin_idx] += 1

        self.fitted = True

    def calibrate(self, probability: float) -> Tuple[float, float]:
        """
        Return calibrated probability with uncertainty.

        Returns (mean, std) of calibrated probability.
        """
        if not self.fitted:
            return probability, 0.1

        bin_idx = min(int(probability * self.n_bins), self.n_bins - 1)

        alpha = self.posterior_alpha[bin_idx]
        beta = self.posterior_beta[bin_idx]

        # Beta distribution mean and std
        mean = alpha / (alpha + beta)
        var = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
        std = math.sqrt(var)

        return mean, std

    def sample_calibrated(self, probability: float, n_samples: int = 100) -> List[float]:
        """
        Sample from posterior of calibrated probability.
        """
        mean, std = self.calibrate(probability)

        # Simple normal approximation to Beta posterior
        samples = [max(0, min(1, random.gauss(mean, std))) for _ in range(n_samples)]

        return samples


# ============================================================================
# Singleton Access
# ============================================================================

_calibrator: Optional[CalibratedConfidenceEstimator] = None


def get_calibrated_confidence_estimator() -> CalibratedConfidenceEstimator:
    """Get singleton calibrated confidence estimator."""
    global _calibrator
    if _calibrator is None:
        _calibrator = CalibratedConfidenceEstimator()
    return _calibrator


# ============================================================================
# Integration with STAN Event Bus
# ============================================================================

def setup_calibrated_confidence_integration(event_bus) -> None:
    """Set up calibrated confidence integration with STAN event bus."""
    estimator = get_calibrated_confidence_estimator()
    estimator.set_event_bus(event_bus)

    def on_calibration_request(event):
        """Handle calibration fitting request."""
        payload = event.get("payload", {})
        scores = payload.get("scores", [])
        labels = payload.get("labels", [])
        method = payload.get("method", "isotonic")

        if scores and labels:
            method_enum = CalibrationMethod(method)
            result = estimator.fit_calibrator(method_enum, scores, labels)

            event_bus.publish(
                "calibration_result",
                "calibrated_confidence",
                {
                    "method": result.method.value,
                    "ece": result.expected_calibration_error,
                    "parameters": result.calibration_parameters
                }
            )

    def on_probability_calibration(event):
        """Handle probability calibration request."""
        payload = event.get("payload", {})
        raw_prob = payload.get("probability")

        if raw_prob is not None:
            score = estimator.calibrate_probability(raw_prob)

            event_bus.publish(
                "calibrated_probability",
                "calibrated_confidence",
                {
                    "raw": score.raw_confidence,
                    "calibrated": score.calibrated_confidence,
                    "reliability": score.reliability
                }
            )

    event_bus.subscribe("fit_calibration", on_calibration_request)
    event_bus.subscribe("calibrate_probability", on_probability_calibration)
    logger.info("Calibrated confidence integration configured")
