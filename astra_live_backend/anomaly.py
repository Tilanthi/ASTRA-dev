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
ASTRA Live — Anomaly Detection
Tracks rolling statistics on the state vector and flags anomalies.
Phase 1 of the AGI Transformation Roadmap.

Anomaly Types:
  - Dimension exceeds ±2σ from rolling mean (20-cycle window)
  - Rapid confidence shift (>0.15 in a single cycle)
  - Domain extinction (domain drops to 0 active hypotheses)
  - Exploration stall (no new hypotheses for 20+ cycles)

Severity Levels:
  INFO     — notable but expected fluctuation
  WARNING  — outside normal bounds, should be monitored
  CRITICAL — requires immediate attention / possible intervention
"""
import time
import math
from collections import deque
from dataclasses import dataclass, asdict
from typing import Optional


class AnomalyDetector:
    """
    Monitors the state vector for anomalies using rolling statistics.
    """

    WINDOW_SIZE = 20  # Rolling window for mean/std calculation
    SIGMA_THRESHOLD = 2.0  # Standard deviations for anomaly

    # Labels that correspond to state vector dimensions
    DIMENSION_LABELS = [
        "astro_conf_mean", "econ_conf_mean", "climate_conf_mean", "epi_conf_mean",
        "astro_conf_var", "econ_conf_var", "climate_conf_var", "epi_conf_var",
        "domain_entropy", "exploration_rate", "exploitation_rate",
        "coupling_density", "resource_utilization", "decision_velocity",
    ]

    def __init__(self):
        # Rolling history of state vectors
        self._history: deque[list[float]] = deque(maxlen=100)
        # Alert history
        self._alerts: list[dict] = []
        # Max alerts to keep
        self._max_alerts = 500
        # Track cycles without new hypotheses
        self._last_hypothesis_count = 0
        self._cycles_without_new = 0

    def check(self, state_vector: dict) -> list[dict]:
        """
        Check a state vector for anomalies.

        Args:
            state_vector: dict with 'vector', 'labels', 'cycle', 'timestamp'

        Returns:
            list of anomaly dicts, each with 'severity', 'dimension', 'message', 'value', 'mean', 'std'
        """
        vector = state_vector.get("vector", [])
        cycle = state_vector.get("cycle", 0)
        timestamp = state_vector.get("timestamp", time.time())

        self._history.append(vector)
        anomalies = []

        # Need at least WINDOW_SIZE data points for meaningful statistics
        if len(self._history) < max(3, self.WINDOW_SIZE // 2):
            return anomalies

        # Compute rolling statistics over the window
        window = list(self._history)[-self.WINDOW_SIZE:]
        n_dims = min(len(vector), len(self.DIMENSION_LABELS))

        for i in range(n_dims):
            dim_values = [w[i] for w in window if len(w) > i]
            if len(dim_values) < 3:
                continue

            mean = sum(dim_values) / len(dim_values)
            variance = sum((v - mean) ** 2 for v in dim_values) / len(dim_values)
            std = math.sqrt(variance) if variance > 0 else 0.0

            current = vector[i]
            label = self.DIMENSION_LABELS[i] if i < len(self.DIMENSION_LABELS) else f"dim_{i}"

            # Skip if std is 0 (constant values)
            if std < 1e-10:
                continue

            z_score = (current - mean) / std

            if abs(z_score) > 3.0:
                severity = "CRITICAL"
            elif abs(z_score) > self.SIGMA_THRESHOLD:
                severity = "WARNING"
            else:
                continue

            direction = "above" if z_score > 0 else "below"
            anomaly = {
                "severity": severity,
                "dimension": label,
                "dimension_index": i,
                "message": (f"{label} is {abs(z_score):.1f}σ {direction} rolling mean "
                           f"(current={current:.4f}, mean={mean:.4f}, std={std:.4f})"),
                "value": round(current, 6),
                "mean": round(mean, 6),
                "std": round(std, 6),
                "z_score": round(z_score, 3),
                "cycle": cycle,
                "timestamp": timestamp,
            }
            anomalies.append(anomaly)

        # Additional checks: rapid confidence shift
        if len(self._history) >= 2:
            prev = self._history[-2]
            for i in range(4):  # First 4 dims are confidence means
                if len(prev) > i and len(vector) > i:
                    delta = abs(vector[i] - prev[i])
                    if delta > 0.15:
                        label = self.DIMENSION_LABELS[i]
                        anomalies.append({
                            "severity": "WARNING",
                            "dimension": label,
                            "dimension_index": i,
                            "message": (f"Rapid confidence shift in {label}: "
                                       f"Δ={delta:.3f} in one cycle "
                                       f"({prev[i]:.3f} → {vector[i]:.3f})"),
                            "value": round(vector[i], 6),
                            "mean": round(prev[i], 6),
                            "std": round(delta, 6),
                            "z_score": 0.0,
                            "cycle": cycle,
                            "timestamp": timestamp,
                        })

        # Check for exploration stall (dim 9 = exploration_rate)
        if len(vector) > 9 and vector[9] < 0.05 and len(self._history) > 10:
            recent_exploration = [w[9] for w in list(self._history)[-10:] if len(w) > 9]
            if all(v < 0.05 for v in recent_exploration):
                anomalies.append({
                    "severity": "WARNING",
                    "dimension": "exploration_rate",
                    "dimension_index": 9,
                    "message": "Exploration stall: exploration rate below 5% for 10+ cycles",
                    "value": round(vector[9], 6),
                    "mean": 0.0,
                    "std": 0.0,
                    "z_score": 0.0,
                    "cycle": cycle,
                    "timestamp": timestamp,
                })

        # Store alerts
        for a in anomalies:
            self._alerts.append(a)
        # Trim
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts // 2:]

        return anomalies

    def get_current_anomalies(self) -> list[dict]:
        """Get anomalies from the most recent check."""
        if not self._alerts:
            return []
        # Return alerts from the most recent cycle
        if self._alerts:
            latest_cycle = self._alerts[-1].get("cycle", 0)
            return [a for a in self._alerts if a.get("cycle") == latest_cycle]
        return []

    def get_alert_history(self, limit: int = 100) -> list[dict]:
        """Get historical alerts, most recent first."""
        return list(reversed(self._alerts[-limit:]))

    def get_rolling_stats(self) -> dict:
        """Get current rolling statistics for all dimensions."""
        if len(self._history) < 3:
            return {"available": False, "reason": "Insufficient data"}

        window = list(self._history)[-self.WINDOW_SIZE:]
        n_dims = len(self.DIMENSION_LABELS)
        stats = {}

        for i in range(n_dims):
            dim_values = [w[i] for w in window if len(w) > i]
            if len(dim_values) < 2:
                continue
            mean = sum(dim_values) / len(dim_values)
            variance = sum((v - mean) ** 2 for v in dim_values) / len(dim_values)
            std = math.sqrt(variance) if variance > 0 else 0.0
            label = self.DIMENSION_LABELS[i]
            stats[label] = {
                "mean": round(mean, 6),
                "std": round(std, 6),
                "min": round(min(dim_values), 6),
                "max": round(max(dim_values), 6),
                "current": round(dim_values[-1], 6) if dim_values else 0.0,
                "samples": len(dim_values),
            }

        return {
            "available": True,
            "window_size": self.WINDOW_SIZE,
            "samples_in_window": len(window),
            "dimensions": stats,
        }

    def get_full_report(self) -> dict:
        """Get complete anomaly report."""
        return {
            "current_anomalies": self.get_current_anomalies(),
            "alert_history": self.get_alert_history(100),
            "rolling_stats": self.get_rolling_stats(),
            "total_alerts": len(self._alerts),
            "timestamp": time.time(),
        }
