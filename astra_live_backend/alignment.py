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
ASTRA Live — Alignment Checker
Computes alignment metrics from hypothesis data to monitor
whether the discovery engine operates within safe, scientific bounds.

Phase 1 of the AGI Transformation Roadmap.

Alignment Dimensions:
  1. Scientific Rigor   — fraction of hypotheses with statistical tests
  2. Domain Balance     — Shannon entropy of domain distribution / max entropy
  3. Novelty Pursuit    — new hypotheses per 10 cycles / expected rate
  4. Epistemic Humility — calibration score (confidence vs test outcomes)
  5. Resource Efficiency — validated hypotheses per 100 cycles
  6. Reproducibility    — fraction with documented methodology (≥3 tests)
"""
import math
import time
from typing import Optional


class AlignmentChecker:
    """
    Computes alignment metrics from the engine's hypothesis store.
    Returns a composite alignment score + individual dimension scores.
    """

    def __init__(self):
        self._last_cycle_count = 0
        self._hypothesis_birth_cycles: dict[str, int] = {}
        self._new_hypotheses_window: list[int] = []  # new hypotheses per cycle (rolling 50)

    def compute(self, store, engine) -> dict:
        """
        Compute all alignment metrics.

        Args:
            store: HypothesisStore instance
            engine: DiscoveryEngine instance

        Returns:
            dict with 'composite', 'dimensions', and 'metadata'
        """
        all_h = store.all()
        active_h = store.active()
        cycle_count = getattr(engine, 'cycle_count', 0)

        # Track new hypotheses per cycle
        current_ids = {h.id for h in all_h}
        known_ids = set(self._hypothesis_birth_cycles.keys())
        new_this_cycle = len(current_ids - known_ids)
        for hid in current_ids - known_ids:
            self._hypothesis_birth_cycles[hid] = cycle_count
        self._new_hypotheses_window.append(new_this_cycle)
        if len(self._new_hypotheses_window) > 50:
            self._new_hypotheses_window = self._new_hypotheses_window[-50:]
        self._last_cycle_count = cycle_count

        dims = {}

        # 1. Scientific Rigor: fraction of active hypotheses with ≥1 statistical test
        if active_h:
            with_tests = sum(1 for h in active_h if len(h.test_results) > 0)
            dims["scientific_rigor"] = with_tests / len(active_h)
        else:
            dims["scientific_rigor"] = 0.0

        # 2. Domain Balance: Shannon entropy / max entropy
        if active_h:
            domain_counts: dict[str, int] = {}
            for h in active_h:
                domain_counts[h.domain] = domain_counts.get(h.domain, 0) + 1
            total = sum(domain_counts.values())
            if total > 0 and len(domain_counts) > 1:
                probs = [c / total for c in domain_counts.values()]
                entropy = -sum(p * math.log2(p) for p in probs if p > 0)
                max_entropy = math.log2(len(domain_counts))
                dims["domain_balance"] = entropy / max_entropy if max_entropy > 0 else 0.0
            elif len(domain_counts) == 1:
                dims["domain_balance"] = 0.0  # Single domain = no balance
            else:
                dims["domain_balance"] = 0.0
        else:
            dims["domain_balance"] = 0.0

        # 3. Novelty Pursuit: new hypotheses per 10 cycles / expected rate
        # Expected rate: ~1 new hypothesis per 10 cycles (0.1 per cycle)
        expected_per_10 = 1.0
        if len(self._new_hypotheses_window) >= 10:
            recent = self._new_hypotheses_window[-10:]
            actual_per_10 = sum(recent)
        elif len(self._new_hypotheses_window) > 0:
            # Scale proportionally
            actual_per_10 = sum(self._new_hypotheses_window) * (10 / len(self._new_hypotheses_window))
        else:
            actual_per_10 = 0.0
        # Score: ratio capped at 1.0, with penalty for being too aggressive
        ratio = actual_per_10 / expected_per_10 if expected_per_10 > 0 else 0.0
        if ratio <= 1.0:
            dims["novelty_pursuit"] = ratio
        else:
            # Penalty for over-exploration: diminishing returns
            dims["novelty_pursuit"] = max(0.0, 1.0 - (ratio - 1.0) * 0.2)

        # 4. Epistemic Humility: calibration score
        # For each hypothesis with tests: how well does confidence match test outcome rate?
        calibration_errors = []
        for h in all_h:
            if len(h.test_results) >= 2:
                # Count fraction of tests that "passed"
                passed = sum(1 for t in h.test_results
                             if (isinstance(t, dict) and t.get('passed', False))
                             or (hasattr(t, 'passed') and t.passed))
                observed_rate = passed / len(h.test_results)
                # Perfect calibration: confidence ≈ observed pass rate
                calibration_errors.append(abs(h.confidence - observed_rate))
        if calibration_errors:
            mean_error = sum(calibration_errors) / len(calibration_errors)
            dims["epistemic_humility"] = max(0.0, 1.0 - mean_error)
        else:
            dims["epistemic_humility"] = 0.5  # Unknown → neutral

        # 5. Resource Efficiency: validated hypotheses per 100 cycles
        from .hypotheses import Phase
        validated_count = len(store.by_phase(Phase.VALIDATED)) + len(store.by_phase(Phase.PUBLISHED))
        if cycle_count > 0:
            rate_per_100 = (validated_count / cycle_count) * 100
            # Ideal: ~5-15 validated per 100 cycles
            if rate_per_100 <= 10:
                dims["resource_efficiency"] = min(1.0, rate_per_100 / 10.0)
            else:
                dims["resource_efficiency"] = max(0.0, 1.0 - (rate_per_100 - 10) * 0.05)
        else:
            dims["resource_efficiency"] = 0.0

        # 6. Reproducibility: fraction with documented methodology (≥3 tests)
        if all_h:
            reproducible = sum(1 for h in all_h if len(h.test_results) >= 3)
            dims["reproducibility"] = reproducible / len(all_h)
        else:
            dims["reproducibility"] = 0.0

        # Composite score: weighted average
        weights = {
            "scientific_rigor": 0.25,
            "domain_balance": 0.10,
            "novelty_pursuit": 0.15,
            "epistemic_humility": 0.25,
            "resource_efficiency": 0.10,
            "reproducibility": 0.15,
        }
        composite = sum(dims[k] * weights[k] for k in dims)

        return {
            "composite_score": round(composite, 4),
            "dimensions": {k: round(v, 4) for k, v in dims.items()},
            "weights": weights,
            "metadata": {
                "total_hypotheses": len(all_h),
                "active_hypotheses": len(active_h),
                "cycle_count": cycle_count,
                "new_hypotheses_last_10": sum(self._new_hypotheses_window[-10:]) if len(self._new_hypotheses_window) >= 10 else sum(self._new_hypotheses_window),
                "timestamp": time.time(),
            }
        }
