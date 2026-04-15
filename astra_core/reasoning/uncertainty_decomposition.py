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
Uncertainty Decomposition for STAN V42

Separates uncertainty into distinct, actionable components:
- Aleatoric uncertainty: Irreducible noise in data
- Epistemic uncertainty: Model uncertainty (reducible with more data)
- Model form uncertainty: Uncertainty from model choice
- Numerical uncertainty: Computational/discretization errors

This decomposition enables:
- Targeted data collection (reduce epistemic uncertainty)
- Model improvement prioritization
- Honest confidence reporting
- Scientific discovery guidance
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

class UncertaintyType(Enum):
    """Types of uncertainty."""
    ALEATORIC = "aleatoric"       # Data noise (irreducible)
    EPISTEMIC = "epistemic"       # Model uncertainty (reducible)
    MODEL_FORM = "model_form"     # Model misspecification
    NUMERICAL = "numerical"       # Computational errors
    TOTAL = "total"              # Combined uncertainty


@dataclass
class UncertaintyComponent:
    """A single uncertainty component."""
    type: UncertaintyType
    variance: float
    std_dev: float
    fraction: float  # Fraction of total variance
    description: str
    reducible: bool
    reduction_strategy: Optional[str] = None


@dataclass
class DecomposedUncertainty:
    """Complete uncertainty decomposition for a quantity."""
    parameter: str
    total_variance: float
    total_std: float
    components: List[UncertaintyComponent]
    dominant_type: UncertaintyType
    confidence_interval_68: Tuple[float, float]
    confidence_interval_95: Tuple[float, float]
    actionable_insights: List[str]


@dataclass
class ModelEnsemblePrediction:
    """Prediction from ensemble of models."""
    mean: float
    std: float
    model_predictions: Dict[str, float]
    model_weights: Dict[str, float]
    disagreement: float  # Inter-model variance


@dataclass
class BootstrapResult:
    """Result from bootstrap analysis."""
    original_estimate: float
    bootstrap_mean: float
    bootstrap_std: float
    bootstrap_bias: float
    percentiles: Dict[int, float]
    n_resamples: int


# ============================================================================
# Aleatoric Uncertainty Estimator
# ============================================================================

class AleatoricEstimator:
    """
    Estimates irreducible uncertainty from data noise.

    Methods:
    - Repeated measurements analysis
    - Residual variance estimation
    - Heteroscedastic noise modeling
    """

    def __init__(self):
        self._noise_models: Dict[str, Callable] = {}

    def estimate_from_residuals(self,
                                residuals: List[float],
                                model_complexity: int = 1) -> float:
        """
        Estimate aleatoric variance from model residuals.

        Uses unbiased variance estimator with degrees of freedom correction.
        """
        n = len(residuals)
        if n <= model_complexity:
            return float('inf')

        # Degrees of freedom
        dof = n - model_complexity

        # Sum of squared residuals
        ss_residuals = sum(r * r for r in residuals)

        # Unbiased variance estimate
        variance = ss_residuals / dof

        return variance

    def estimate_from_repeated_measurements(self,
                                           measurements: Dict[str, List[float]]) -> Dict[str, float]:
        """
        Estimate aleatoric variance from repeated measurements.

        Args:
            measurements: Dict mapping condition to list of repeated values

        Returns:
            Dict with pooled variance estimate and per-condition variances
        """
        result = {}

        total_ss = 0.0
        total_dof = 0

        for condition, values in measurements.items():
            n = len(values)
            if n < 2:
                continue

            mean = sum(values) / n
            ss = sum((v - mean) ** 2 for v in values)

            result[f"variance_{condition}"] = ss / (n - 1)

            total_ss += ss
            total_dof += n - 1

        if total_dof > 0:
            result["pooled_variance"] = total_ss / total_dof
            result["pooled_std"] = math.sqrt(result["pooled_variance"])
        else:
            result["pooled_variance"] = 0.0
            result["pooled_std"] = 0.0

        return result

    def estimate_heteroscedastic(self,
                                x_values: List[float],
                                residuals: List[float],
                                n_bins: int = 10) -> Dict[str, float]:
        """
        Estimate non-constant (heteroscedastic) noise.

        Returns variance as function of predictor values.
        """
        if len(x_values) != len(residuals):
            raise ValueError("x_values and residuals must have same length")

        n = len(x_values)
        if n < n_bins * 2:
            n_bins = max(2, n // 2)

        # Sort by x
        sorted_pairs = sorted(zip(x_values, residuals))

        # Compute variance in each bin
        bin_size = n // n_bins
        variances = {}

        for i in range(n_bins):
            start = i * bin_size
            end = start + bin_size if i < n_bins - 1 else n

            bin_residuals = [sorted_pairs[j][1] for j in range(start, end)]
            bin_x = [sorted_pairs[j][0] for j in range(start, end)]

            if len(bin_residuals) >= 2:
                mean_x = sum(bin_x) / len(bin_x)
                mean_r = sum(bin_residuals) / len(bin_residuals)
                var = sum((r - mean_r) ** 2 for r in bin_residuals) / (len(bin_residuals) - 1)
                variances[f"bin_{i}_x={mean_x:.3f}"] = var

        return variances


# ============================================================================
# Epistemic Uncertainty Estimator
# ============================================================================

class EpistemicEstimator:
    """
    Estimates reducible uncertainty from limited data/knowledge.

    Methods:
    - Bootstrap resampling
    - Bayesian posterior analysis
    - Model ensemble disagreement
    """

    def __init__(self):
        self.bootstrap_cache: Dict[str, BootstrapResult] = {}

    def bootstrap_variance(self,
                          data: List[float],
                          estimator: Callable[[List[float]], float],
                          n_resamples: int = 1000,
                          confidence_levels: List[int] = [5, 25, 50, 75, 95]) -> BootstrapResult:
        """
        Estimate epistemic uncertainty via bootstrap resampling.
        """
        n = len(data)
        if n == 0:
            return BootstrapResult(
                original_estimate=0.0,
                bootstrap_mean=0.0,
                bootstrap_std=0.0,
                bootstrap_bias=0.0,
                percentiles={},
                n_resamples=0
            )

        # Original estimate
        original = estimator(data)

        # Bootstrap resamples
        bootstrap_estimates = []
        for _ in range(n_resamples):
            resample = [random.choice(data) for _ in range(n)]
            bootstrap_estimates.append(estimator(resample))

        # Statistics
        mean = sum(bootstrap_estimates) / n_resamples
        var = sum((e - mean) ** 2 for e in bootstrap_estimates) / (n_resamples - 1)
        std = math.sqrt(var)
        bias = mean - original

        # Percentiles
        sorted_estimates = sorted(bootstrap_estimates)
        percentiles = {}
        for level in confidence_levels:
            idx = int(level * n_resamples / 100)
            idx = min(idx, n_resamples - 1)
            percentiles[level] = sorted_estimates[idx]

        return BootstrapResult(
            original_estimate=original,
            bootstrap_mean=mean,
            bootstrap_std=std,
            bootstrap_bias=bias,
            percentiles=percentiles,
            n_resamples=n_resamples
        )

    def bayesian_posterior_variance(self,
                                   prior_mean: float,
                                   prior_var: float,
                                   likelihood_var: float,
                                   data: List[float]) -> Tuple[float, float]:
        """
        Compute posterior variance under Gaussian assumptions.

        Returns (posterior_mean, posterior_variance)
        """
        n = len(data)
        if n == 0:
            return prior_mean, prior_var

        data_mean = sum(data) / n

        # Precision-weighted combination
        prior_precision = 1.0 / prior_var if prior_var > 0 else 0.0
        data_precision = n / likelihood_var if likelihood_var > 0 else 0.0

        total_precision = prior_precision + data_precision

        if total_precision == 0:
            return data_mean, float('inf')

        posterior_var = 1.0 / total_precision
        posterior_mean = (prior_precision * prior_mean +
                         data_precision * data_mean) / total_precision

        return posterior_mean, posterior_var

    def ensemble_disagreement(self,
                             predictions: Dict[str, float],
                             weights: Optional[Dict[str, float]] = None) -> ModelEnsemblePrediction:
        """
        Estimate epistemic uncertainty from model ensemble disagreement.
        """
        if not predictions:
            return ModelEnsemblePrediction(
                mean=0.0,
                std=0.0,
                model_predictions={},
                model_weights={},
                disagreement=0.0
            )

        n_models = len(predictions)

        # Default equal weights
        if weights is None:
            weights = {name: 1.0 / n_models for name in predictions}

        # Normalize weights
        total_weight = sum(weights.values())
        weights = {name: w / total_weight for name, w in weights.items()}

        # Weighted mean
        mean = sum(weights[name] * pred for name, pred in predictions.items())

        # Weighted variance (inter-model disagreement)
        var = sum(weights[name] * (pred - mean) ** 2
                 for name, pred in predictions.items())
        std = math.sqrt(var)

        return ModelEnsemblePrediction(
            mean=mean,
            std=std,
            model_predictions=predictions.copy(),
            model_weights=weights.copy(),
            disagreement=var
        )


# ============================================================================
# Model Form Uncertainty Estimator
# ============================================================================

class ModelFormEstimator:
    """
    Estimates uncertainty from model misspecification.

    Methods:
    - Multi-model comparison
    - Systematic residual patterns
    - Complexity-accuracy tradeoff
    """

    def __init__(self):
        self._model_scores: Dict[str, Dict[str, float]] = {}

    def compare_models(self,
                      models: Dict[str, Callable[[Dict], float]],
                      data: List[Dict[str, float]],
                      target_key: str) -> Dict[str, float]:
        """
        Compare multiple models to estimate model form uncertainty.

        Returns dict with:
        - Model-specific RMSEs
        - Inter-model variance
        - Best model selection
        """
        if not models or not data:
            return {}

        predictions = {name: [] for name in models}
