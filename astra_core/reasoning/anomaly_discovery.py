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
Anomaly-Driven Discovery Loop for STAN V42

Implements a systematic framework for turning anomalies into discoveries:
1. Anomaly Detection: Statistical outlier identification
2. Anomaly Characterization: Feature extraction and clustering
3. Hypothesis Generation: Automated explanation synthesis
4. Falsification: Testing explanations against data
5. Knowledge Integration: Updating world models with validated discoveries

This creates a closed loop where anomalies drive scientific progress.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
from enum import Enum
import math
import random
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class AnomalyType(Enum):
    """Classification of anomaly types."""
    STATISTICAL_OUTLIER = "statistical_outlier"     # >3σ from expected
    MODEL_RESIDUAL = "model_residual"               # Poor model fit
    TEMPORAL = "temporal"                           # Unusual time evolution
    SPATIAL = "spatial"                             # Unusual spatial pattern
    SPECTRAL = "spectral"                           # Unusual spectral features
    CORRELATION = "correlation"                     # Unexpected correlation
    ABSENCE = "absence"                             # Missing expected signal
    NOVELTY = "novelty"                             # Never-before-seen pattern


class AnomalyStatus(Enum):
    """Status in the discovery pipeline."""
    DETECTED = "detected"
    CHARACTERIZED = "characterized"
    HYPOTHESIZED = "hypothesized"
    TESTING = "testing"
    VALIDATED = "validated"
    REJECTED = "rejected"
    INTEGRATED = "integrated"


class HypothesisType(Enum):
    """Types of explanatory hypotheses."""
    INSTRUMENTAL = "instrumental"       # Artifact/instrument error
    SYSTEMATIC = "systematic"           # Systematic bias
    STATISTICAL_FLUKE = "statistical"   # Random fluctuation
    KNOWN_PHYSICS = "known_physics"     # Explained by known physics
    NEW_PHYSICS = "new_physics"         # Requires new physics
    NEW_OBJECT = "new_object"           # New class of astronomical object
    CALIBRATION = "calibration"         # Calibration issue


@dataclass
class Anomaly:
    """A detected anomaly."""
    anomaly_id: str
    type: AnomalyType
    status: AnomalyStatus
    detection_time: float
    source_location: Optional[Dict[str, float]]  # RA, Dec, etc.
    data_context: Dict[str, Any]
    observed_value: float
    expected_value: float
    significance: float  # sigma
    features: Dict[str, float] = field(default_factory=dict)
    cluster_id: Optional[int] = None
    hypotheses: List['Hypothesis'] = field(default_factory=list)
    discovery_potential: float = 0.0


@dataclass
class Hypothesis:
    """An explanatory hypothesis for an anomaly."""
    hypothesis_id: str
    type: HypothesisType
    description: str
    prior_probability: float
    posterior_probability: float
    predictions: List[Dict[str, Any]]  # Testable predictions
    tests_passed: int = 0
    tests_failed: int = 0
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)


@dataclass
class DiscoveryCandidate:
    """A candidate discovery ready for validation."""
    anomaly: Anomaly
    best_hypothesis: Hypothesis
    confidence: float
    supporting_evidence: List[str]
    required_observations: List[Dict[str, Any]]
    astrophysical_implications: List[str]


@dataclass
class ValidatedDiscovery:
    """A validated scientific discovery."""
    discovery_id: str
    anomaly_id: str
    hypothesis: Hypothesis
    validation_level: str  # "preliminary", "confirmed", "robust"
    confidence: float
    implications: List[str]
    follow_up_recommendations: List[str]


# ============================================================================
# Anomaly Detector
# ============================================================================

class AnomalyDetector:
    """
    Multi-method anomaly detection system.
    """

    def __init__(self,
                 sigma_threshold: float = 3.0,
                 min_significance: float = 2.0):
        self.sigma_threshold = sigma_threshold
        self.min_significance = min_significance
        self._anomaly_counter = 0

    def detect_statistical_outliers(self,
                                   values: List[float],
                                   expected: Optional[List[float]] = None,
                                   uncertainties: Optional[List[float]] = None) -> List[Anomaly]:
        """
        Detect statistical outliers using robust statistics.
        """
        anomalies = []
        n = len(values)

        if n < 5:
            return anomalies

        if expected is None:
            # Use median and MAD for robust estimation
            sorted_vals = sorted(values)
            median = sorted_vals[n // 2]
            mad = sorted(abs(v - median) for v in values)[n // 2]
            sigma = mad * 1.4826  # MAD to sigma conversion

            expected = [median] * n
            uncertainties = uncertainties or [sigma] * n

        for i, (obs, exp) in enumerate(zip(values, expected)):
            unc = uncertainties[i] if uncertainties else 1.0

            if unc <= 0:
                continue

            significance = abs(obs - exp) / unc

            if significance > self.sigma_threshold:
                anomaly = Anomaly(
                    anomaly_id=self._generate_id(),
                    type=AnomalyType.STATISTICAL_OUTLIER,
                    status=AnomalyStatus.DETECTED,
                    detection_time=0.0,
                    source_location={"index": i},
                    data_context={"array_position": i, "n_total": n},
                    observed_value=obs,
                    expected_value=exp,
                    significance=significance
                )
                anomalies.append(anomaly)

        return anomalies

    def detect_model_residuals(self,
                              residuals: List[float],
                              model_uncertainties: List[float],
                              positions: Optional[List[Dict[str, float]]] = None) -> List[Anomaly]:
        """
        Detect anomalies in model residuals.
        """
        anomalies = []

        for i, (res, unc) in enumerate(zip(residuals, model_uncertainties)):
            if unc <= 0:
                continue

            significance = abs(res) / unc

            if significance > self.sigma_threshold:
                location = positions[i] if positions else {"index": i}

                anomaly = Anomaly(
                    anomaly_id=self._generate_id(),
                    type=AnomalyType.MODEL_RESIDUAL,
                    status=AnomalyStatus.DETECTED,
                    detection_time=0.0,
                    source_location=location,
                    data_context={"residual": res, "uncertainty": unc},
                    observed_value=res,
                    expected_value=0.0,
                    significance=significance
                )
                anomalies.append(anomaly)

        return anomalies

    def detect_temporal_anomalies(self,
                                  times: List[float],
                                  values: List[float],
                                  window_size: int = 10) -> List[Anomaly]:
        """
        Detect anomalies in time series data.
        """
        anomalies = []
        n = len(values)

        if n < window_size * 2:
            return anomalies

        for i in range(window_size, n - window_size):
            # Local context
            context = values[i - window_size:i + window_size + 1]
            context_without_center = context[:window_size] + context[window_size + 1:]

            local_mean = sum(context_without_center) / len(context_without_center)
            local_std = math.sqrt(
                sum((v - local_mean) ** 2 for v in context_without_center) /
                len(context_without_center)
            )

            if local_std > 0:
                significance = abs(values[i] - local_mean) / local_std

                if significance > self.sigma_threshold:
                    anomaly = Anomaly(
                        anomaly_id=self._generate_id(),
                        type=AnomalyType.TEMPORAL,
                        status=AnomalyStatus.DETECTED,
                        detection_time=times[i],
                        source_location={"time": times[i], "index": i},
                        data_context={"window_size": window_size},
                        observed_value=values[i],
                        expected_value=local_mean,
                        significance=significance
                    )
                    anomalies.append(anomaly)

        return anomalies

    def detect_correlation_anomalies(self,
                                    x_values: List[float],
                                    y_values: List[float],
                                    expected_correlation: float = 0.0) -> List[Anomaly]:
        """
        Detect anomalous correlations between variables.
        """
        n = len(x_values)
        if n != len(y_values) or n < 10:
            return []

        # Compute correlation
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n

        cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values)) / n
        std_x = math.sqrt(sum((x - mean_x) ** 2 for x in x_values) / n)
        std_y = math.sqrt(sum((y - mean_y) ** 2 for y in y_values) / n)

        if std_x > 0 and std_y > 0:
            correlation = cov / (std_x * std_y)
        else:
            return []

        # Fisher z-transformation for significance
        z = 0.5 * math.log((1 + correlation) / (1 - correlation)) if abs(correlation) < 1 else 0
        z_expected = 0.5 * math.log((1 + expected_correlation) / (1 - expected_correlation)) if abs(expected_correlation) < 1 else 0

        sigma_z = 1.0 / math.sqrt(n - 3) if n > 3 else 1.0
        significance = abs(z - z_expected) / sigma_z

        if significance > self.min_significance:
            return [Anomaly(
                anomaly_id=self._generate_id(),
                type=AnomalyType.CORRELATION,
                status=AnomalyStatus.DETECTED,
                detection_time=0.0,
                source_location=None,
                data_context={
                    "n_points": n,
                    "expected_correlation": expected_correlation
                },
                observed_value=correlation,
                expected_value=expected_correlation,
                significance=significance
            )]

        return []

    def detect_absence_anomalies(self,
                                expected_signals: List[Dict[str, Any]],
                                observed_signals: List[Dict[str, Any]],
                                matching_tolerance: float = 0.1) -> List[Anomaly]:
        """
        Detect absence of expected signals (non-detections).
        """
        anomalies = []

        for expected in expected_signals:
            # Check if expected signal is present in observations
            found = False
            for observed in observed_signals:
                # Simple matching based on position
                if all(abs(expected.get(k, 0) - observed.get(k, 0)) < matching_tolerance
                      for k in expected if k not in ['expected_value', 'uncertainty']):
                    found = True
                    break

            if not found:
                exp_val = expected.get('expected_value', 1.0)
                unc = expected.get('uncertainty', 0.1)

                anomaly = Anomaly(
                    anomaly_id=self._generate_id(),
                    type=AnomalyType.ABSENCE,
                    status=AnomalyStatus.DETECTED,
                    detection_time=0.0,
                    source_location={k: v for k, v in expected.items()
                                    if k not in ['expected_value', 'uncertainty']},
                    data_context={"expected_signal": expected},
                    observed_value=0.0,
                    expected_value=exp_val,
                    significance=exp_val / unc if unc > 0 else 0.0
                )
                anomalies.append(anomaly)

        return anomalies

    def _generate_id(self) -> str:
        """Generate unique anomaly ID."""
        self._anomaly_counter += 1
        return f"ANOM_{self._anomaly_counter:06d}"


# ============================================================================
# Anomaly Characterizer
# ============================================================================

class AnomalyCharacterizer:
    """
    Extracts features and clusters similar anomalies.
    """

    def __init__(self):
        self._feature_extractors: Dict[str, Callable] = {}
        self._register_default_extractors()

    def _register_default_extractors(self):
        """Register default feature extractors."""
        self._feature_extractors["significance_level"] = lambda a: a.significance
        self._feature_extractors["deviation_direction"] = lambda a: 1.0 if a.observed_value > a.expected_value else -1.0
        self._feature_extractors["relative_deviation"] = lambda a: (a.observed_value - a.expected_value) / a.expected_value if a.expected_value != 0 else 0.0

    def register_feature_extractor(self, name: str, extractor: Callable[[Anomaly], float]):
        """Register custom feature extractor."""
        self._feature_extractors[name] = extractor
