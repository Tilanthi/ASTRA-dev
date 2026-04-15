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
ASTRA Live — Novelty Detector
Identifies potentially novel findings by comparing results against
known science, detecting statistical anomalies, and cross-referencing
with literature.

This is the component that turns "confirming known science" into
"possibly discovering something new."
"""
import time
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class NoveltySignal:
    """A potentially novel finding."""
    timestamp: float
    hypothesis_id: str
    hypothesis_name: str
    signal_type: str  # "outlier", "unexpected_correlation", "distribution_shift", "literature_gap"
    description: str
    novelty_score: float  # 0.0 = known, 1.0 = completely unexpected
    evidence: Dict[str, Any] = field(default_factory=dict)
    literature_check: Optional[Dict] = None
    investigated: bool = False
    follow_up: str = ""

    def to_dict(self):
        return asdict(self)


# ── Known Science Baselines ───────────────────────────────────────
# These are reference values the engine compares against.
# If results deviate significantly, it flags novelty.

KNOWN_BASELINES = {
    "hubble_constant": {
        "planck_2018": {"value": 67.4, "uncertainty": 0.5, "method": "CMB"},
        "shoes_2022": {"value": 73.04, "uncertainty": 1.04, "method": "SNe Ia"},
        "tension_sigma": 5.0,  # The Hubble tension is ~5σ
        "description": "Hubble constant: Planck vs SH0ES tension at ~5σ",
    },
    "galaxy_bimodality": {
        "green_valley_g_r": 0.7,  # Approximate g-r color of green valley
        "red_sequence_g_r": 0.9,
        "blue_cloud_g_r": 0.5,
        "bimodal_fraction": 0.8,  # ~80% of galaxies are clearly red or blue
        "description": "Galaxy color bimodality (red sequence + blue cloud)",
    },
    "exoplanet_period_valley": {
        "valley_center_days": 10.0,
        "valley_width_days": 3.0,
        "description": "Exoplanet period valley near 10 days (Fulton gap)",
    },
    "hr_diagram": {
        "ms_slope": 0.1,  # Main sequence has positive BP-RP vs M_G slope
        "giant_branch_tip_gmag": -3.0,
        "wd_sequence_bp_rp": 0.0,  # White dwarfs are blue
        "description": "HR diagram structure: MS, giant branch, WD sequence",
    },
}


class NoveltyDetector:
    """
    Compares engine results against known science to identify
    potentially novel findings.
    """

    def __init__(self):
        self._signals: List[NoveltySignal] = []
        self._baselines_checked: Dict[str, float] = {}  # hypothesis -> last check time

    def evaluate_result(self, hypothesis_id: str, hypothesis_name: str,
                        test_name: str, statistic: float, p_value: float,
                        data_summary: Dict[str, Any]) -> Optional[NoveltySignal]:
        """
        Evaluate a test result for novelty. Returns a NoveltySignal if
        something unexpected is found, None if it matches known science.
        """
        # Check against known baselines
        signal = None

        if "hubble" in hypothesis_name.lower() or "h0" in hypothesis_name.lower():
            signal = self._check_hubble_novelty(
                hypothesis_id, hypothesis_name, test_name, statistic, p_value, data_summary)
        elif "galaxy" in hypothesis_name.lower() or "color" in hypothesis_name.lower():
            signal = self._check_galaxy_novelty(
                hypothesis_id, hypothesis_name, test_name, statistic, p_value, data_summary)
        elif "exoplanet" in hypothesis_name.lower() or "period" in hypothesis_name.lower():
            signal = self._check_exoplanet_novelty(
                hypothesis_id, hypothesis_name, test_name, statistic, p_value, data_summary)
        elif "hr" in hypothesis_name.lower() or "gaia" in hypothesis_name.lower():
            signal = self._check_hr_novelty(
                hypothesis_id, hypothesis_name, test_name, statistic, p_value, data_summary)

        if signal:
            self._signals.append(signal)

        return signal

    def _check_hubble_novelty(self, hid, name, test, stat, p, data) -> Optional[NoveltySignal]:
        """Check if Hubble diagram results deviate from known cosmology."""

        # Check 1: Is the linearity unexpected?
        if test == "Pearson correlation":
            r = abs(stat)
            if r < 0.95:
                # Hubble diagram should be highly linear (r > 0.99)
                # Lower linearity could indicate new physics
                return NoveltySignal(
                    timestamp=time.time(),
                    hypothesis_id=hid,
                    hypothesis_name=name,
                    signal_type="outlier",
                    description=f"Unexpectedly low Hubble diagram linearity: r={r:.4f} (expected >0.99)",
                    novelty_score=min(1.0, (0.99 - r) * 20),
                    evidence={"r_value": r, "expected_min": 0.99, "test": test},
                    follow_up="Investigate: outliers? Selection effects? Modified gravity?",
                )

        # Check 2: Are residuals systematically offset?
        if test == "Bayesian t-test" and data.get("context") == "residual":
            t_stat = abs(stat)
            if t_stat > 100:
                return NoveltySignal(
                    timestamp=time.time(),
                    hypothesis_id=hid,
                    hypothesis_name=name,
                    signal_type="distribution_shift",
                    description=f"Hubble law residuals significant: |t|={t_stat:.1f} (p={p:.2e}) — may indicate model tension",
                    novelty_score=min(0.5, t_stat / 2000),
                    evidence={"t_statistic": t_stat, "p_value": p, "test": test},
                    follow_up="Compare χ² with Planck vs SH0ES models to assess Hubble tension",
                )

        # Check 3: Planck vs SH0ES χ² comparison (via KS test on residuals)
        if test == "Kolmogorov-Smirnov" and 'chi2_planck' in data and 'chi2_shoes' in data:
            delta_chi2 = abs(data['chi2_planck'] - data['chi2_shoes'])
            if delta_chi2 > 100:
                return NoveltySignal(
                    timestamp=time.time(),
                    hypothesis_id=hid,
                    hypothesis_name=name,
                    signal_type="distribution_shift",
                    description=f"Hubble tension: Δχ²(Planck vs SH0ES) = {delta_chi2:.0f} — model preference detected",
                    novelty_score=min(0.4, delta_chi2 / 5000),
                    evidence={"delta_chi2": delta_chi2},
                    follow_up="This confirms the known Hubble tension (~5σ) — well-established result",
                )

        return None

    def _check_galaxy_novelty(self, hid, name, test, stat, p, data) -> Optional[NoveltySignal]:
        """Check if galaxy color distribution has unexpected features."""

        if "g_r_mean" in data:
            mean_gr = data["g_r_mean"]
            # Green valley is at g-r ~ 0.7. Excess population there is interesting
            if 0.6 < mean_gr < 0.8:
                return NoveltySignal(
                    timestamp=time.time(),
                    hypothesis_id=hid,
                    hypothesis_name=name,
                    signal_type="distribution_shift",
                    description=f"Galaxy sample centered in green valley (g-r={mean_gr:.2f}) — transitional population",
                    novelty_score=0.4,
                    evidence={"mean_g_r": mean_gr, "green_valley_range": [0.6, 0.8]},
                    follow_up="Is this a selection effect or genuine green valley excess?",
                )

        return None

    def _check_exoplanet_novelty(self, hid, name, test, stat, p, data) -> Optional[NoveltySignal]:
        """Check if exoplanet demographics show unexpected features."""

        if test == "Kolmogorov-Smirnov" and "log" in name.lower():
            # KS test on log-period distribution
            if p > 0.1:
                # If log(P) passes normality test, that's actually interesting
                # Real period distributions are NOT log-normal
                return NoveltySignal(
                    timestamp=time.time(),
                    hypothesis_id=hid,
                    hypothesis_name=name,
                    signal_type="unexpected_correlation",
                    description=f"Exoplanet log-period distribution passes KS test (p={p:.4f}) — unexpectedly smooth",
                    novelty_score=0.3,
                    evidence={"p_value": p, "test": test},
                    follow_up="Check if selection effects create artificial smoothness",
                )

        return None

    def _check_hr_novelty(self, hid, name, test, stat, p, data) -> Optional[NoveltySignal]:
        """Check if HR diagram shows unexpected features."""

        if "bp_rp_range" in data:
            bp_rp_range = data["bp_rp_range"]
            # If the sample is missing the blue end (< -0.5) or red end (> 3.5),
            # or has an unusual gap
            if bp_rp_range < 1.0:
                return NoveltySignal(
                    timestamp=time.time(),
                    hypothesis_id=hid,
                    hypothesis_name=name,
                    signal_type="outlier",
                    description=f"Narrow HR diagram color range (BP-RP span = {bp_rp_range:.1f})",
                    novelty_score=0.2,
                    evidence={"bp_rp_range": bp_rp_range},
                    follow_up="Check if sample selection is too restrictive",
                )

        return None

    def detect_pattern_anomaly(self, hypothesis_id: str, hypothesis_name: str,
                               current_values: Dict[str, float],
                               historical_values: List[Dict[str, float]]) -> Optional[NoveltySignal]:
        """
        Detect if current results are anomalous compared to historical results
        from the same hypothesis. This catches drift or sudden changes.
        """
        if len(historical_values) < 3:
            return None

        for key, current_val in current_values.items():
            if not isinstance(current_val, (int, float)):
                continue

            hist_vals = [h.get(key) for h in historical_values if key in h]
            hist_vals = [v for v in hist_vals if isinstance(v, (int, float))]

            if len(hist_vals) < 3:
                continue

            mean = np.mean(hist_vals)
            std = np.std(hist_vals)

            if std > 0 and abs(current_val - mean) > 3 * std:
                signal = NoveltySignal(
                    timestamp=time.time(),
                    hypothesis_id=hypothesis_id,
                    hypothesis_name=hypothesis_name,
                    signal_type="distribution_shift",
                    description=f"{key} drifted: {current_val:.4f} vs historical {mean:.4f}±{std:.4f} ({abs(current_val-mean)/std:.1f}σ)",
                    novelty_score=min(1.0, abs(current_val - mean) / (5 * std)),
                    evidence={
                        "metric": key, "current": current_val,
                        "historical_mean": mean, "historical_std": std,
                        "sigma_deviation": abs(current_val - mean) / std,
                    },
                    follow_up="Investigate what changed between cycles",
                )
                self._signals.append(signal)
                return signal

        return None

    def get_signals(self, limit: int = 20, min_score: float = 0.0) -> List[Dict]:
        """Return novelty signals, optionally filtered by minimum score."""
        filtered = [s for s in self._signals if s.novelty_score >= min_score]
        return [s.to_dict() for s in filtered[-limit:]]

    def get_unexplored(self) -> List[Dict]:
        """Return high-novelty signals that haven't been investigated."""
        return [s.to_dict() for s in self._signals
                if not s.investigated and s.novelty_score >= 0.3]

    def get_status(self) -> Dict:
        return {
            "total_signals": len(self._signals),
            "uninvestigated": sum(1 for s in self._signals if not s.investigated),
            "high_novelty": sum(1 for s in self._signals if s.novelty_score >= 0.5),
            "by_type": {
                t: sum(1 for s in self._signals if s.signal_type == t)
                for t in set(s.signal_type for s in self._signals)
            },
            "recent": self.get_signals(5),
        }
