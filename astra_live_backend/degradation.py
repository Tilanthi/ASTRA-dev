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
ASTRA Live — Degradation Detection (Phase 10.3)
Monitors engine health metrics and triggers protective actions when quality degrades.
"""
import time
from collections import Counter, deque
from typing import Optional, Dict, List


class DegradationDetector:
    """
    Monitors rolling engine metrics and triggers safety actions on degradation.

    Checks after each cycle's UPDATE phase:
    - Rolling success rate (last 20 outcomes)
    - Rolling significant results per cycle
    - Domain concentration
    - Pattern repetition
    """

    def __init__(self, window: int = 20):
        self.window = window
        # Rolling metrics
        self._cycle_success_rates: deque = deque(maxlen=50)
        self._cycle_sig_results: deque = deque(maxlen=50)
        self._low_success_streak = 0
        self._low_sig_streak = 0
        self._last_check_cycle = 0

        # Pattern detection
        self._recent_patterns: deque = deque(maxlen=100)

        # Thresholds
        self.success_rate_threshold = 0.50
        self.success_streak_limit = 5
        self.sig_results_threshold = 1.0
        self.sig_streak_limit = 10
        self.domain_concentration_threshold = 0.80

        # State
        self.safe_mode_triggered = False
        self.strategy_switch_recommended = False
        self._recommendations: list = []

    def check_after_cycle(self, discovery_memory, cycle: int) -> Dict:
        """
        Run all degradation checks after each cycle's UPDATE phase.

        Returns dict with:
        - degraded: bool
        - metrics: current health metrics
        - actions: list of triggered/recommended actions
        """
        self._last_check_cycle = cycle
        actions = []
        self._recommendations = []

        # 1. Rolling success rate from last N method outcomes
        outcomes = list(discovery_memory.method_outcomes)
        recent_outcomes = outcomes[-self.window:] if outcomes else []

        if recent_outcomes:
            success_count = sum(1 for o in recent_outcomes if o.success)
            success_rate = success_count / len(recent_outcomes)
        else:
            success_rate = 1.0  # no data yet = assume ok

        self._cycle_success_rates.append(success_rate)

        # 2. Significant results per evaluation (recent window)
        if recent_outcomes:
            avg_sig = sum(o.significant_results for o in recent_outcomes) / len(recent_outcomes)
        else:
            avg_sig = 0.0
        self._cycle_sig_results.append(avg_sig)

        # 3. Success rate streak check
        if success_rate < self.success_rate_threshold:
            self._low_success_streak += 1
        else:
            self._low_success_streak = 0
            self.safe_mode_triggered = False  # reset on recovery

        trigger_safe_mode = (
            self._low_success_streak >= self.success_streak_limit
            and not self.safe_mode_triggered
        )
        if trigger_safe_mode:
            self.safe_mode_triggered = True
            actions.append("TRIGGER_SAFE_MODE")
            self._recommendations.append(
                f"Success rate {success_rate:.1%} below {self.success_rate_threshold:.0%} "
                f"for {self._low_success_streak} consecutive cycles — triggering SAFE_MODE"
            )

        # 4. Significant results streak check
        if avg_sig < self.sig_results_threshold:
            self._low_sig_streak += 1
        else:
            self._low_sig_streak = 0
            self.strategy_switch_recommended = False

        if self._low_sig_streak >= self.sig_streak_limit and not self.strategy_switch_recommended:
            self.strategy_switch_recommended = True
            actions.append("SWITCH_STRATEGY")
            self._recommendations.append(
                f"Avg significant results {avg_sig:.2f} below {self.sig_results_threshold:.1f} "
                f"for {self._low_sig_streak} cycles — recommending exploration strategy switch"
            )

        # 5. Domain concentration
        discoveries = list(discovery_memory.discoveries)
        recent_disc = discoveries[-50:] if len(discoveries) >= 50 else discoveries
        domain_counts = Counter(d.domain for d in recent_disc)
        total_recent = len(recent_disc)
        domain_concentration = {}
        dominant_domain = None
        if total_recent > 0:
            for domain, count in domain_counts.items():
                frac = count / total_recent
                domain_concentration[domain] = round(frac, 3)
                if frac > self.domain_concentration_threshold:
                    dominant_domain = domain
                    actions.append("DIVERSIFY_DOMAINS")
                    self._recommendations.append(
                        f"Domain '{domain}' has {frac:.0%} of recent {total_recent} "
                        f"discoveries — force-switching to underrepresented domains"
                    )

        # 6. Pattern repetition detection
        recent_patterns = []
        for d in recent_disc[-20:]:
            pattern = f"{d.finding_type}|{d.data_source}"
            recent_patterns.append(pattern)

        pattern_counts = Counter(recent_patterns)
        repetitive_patterns = {p: c for p, c in pattern_counts.items() if c >= 5}
        if repetitive_patterns:
            actions.append("BREAK_REPETITION")
            for p, c in repetitive_patterns.items():
                self._recommendations.append(
                    f"Pattern '{p}' repeated {c} times in last 20 discoveries — stuck in loop"
                )

        degraded = bool(actions)

        return {
            "degraded": degraded,
            "cycle": cycle,
            "metrics": {
                "rolling_success_rate": round(success_rate, 3),
                "rolling_avg_significant": round(avg_sig, 3),
                "low_success_streak": self._low_success_streak,
                "low_sig_streak": self._low_sig_streak,
                "domain_concentration": domain_concentration,
                "dominant_domain": dominant_domain,
                "repetitive_patterns": dict(repetitive_patterns),
                "total_discoveries": len(discoveries),
                "total_outcomes": len(outcomes),
            },
            "actions": actions,
            "recommendations": self._recommendations,
            "safe_mode_triggered": self.safe_mode_triggered,
            "strategy_switch_recommended": self.strategy_switch_recommended,
        }

    def get_status(self) -> Dict:
        """Return current degradation status for API."""
        return {
            "last_check_cycle": self._last_check_cycle,
            "rolling_success_rates": list(self._cycle_success_rates),
            "rolling_sig_results": list(self._cycle_sig_results),
            "low_success_streak": self._low_success_streak,
            "low_sig_streak": self._low_sig_streak,
            "safe_mode_triggered": self.safe_mode_triggered,
            "strategy_switch_recommended": self.strategy_switch_recommended,
            "recommendations": self._recommendations,
            "thresholds": {
                "success_rate": self.success_rate_threshold,
                "success_streak_limit": self.success_streak_limit,
                "sig_results": self.sig_results_threshold,
                "sig_streak_limit": self.sig_streak_limit,
                "domain_concentration": self.domain_concentration_threshold,
            },
        }

    def get_least_explored_domain(self, discovery_memory,
                                   canonical_domains: list = None) -> Optional[str]:
        """Find the domain with fewest recent discoveries — for forced exploration."""
        if not canonical_domains:
            canonical_domains = ["Astrophysics", "Economics", "Climate", "Epidemiology"]

        discoveries = list(discovery_memory.discoveries)
        recent = discoveries[-50:] if len(discoveries) >= 50 else discoveries
        domain_counts = Counter(d.domain for d in recent)

        least = None
        least_count = float('inf')
        for domain in canonical_domains:
            count = domain_counts.get(domain, 0)
            if count < least_count:
                least_count = count
                least = domain

        return least
