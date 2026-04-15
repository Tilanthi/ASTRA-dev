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
ASTRA Live — Phase 10 Test Suite
Tests degradation detection, importance-weighted memory compaction,
hypothesis lifecycle management, and exploration diversification.
"""
import sys
import time
sys.path.insert(0, ".")

import pytest
from collections import deque
from astra_live_backend.degradation import DegradationDetector
from astra_live_backend.discovery_memory import DiscoveryMemory, DiscoveryRecord, MethodOutcome
from astra_live_backend.hypotheses import Hypothesis, HypothesisStore, Phase


# ── Helpers ──────────────────────────────────────────────────────

def make_discovery(domain="Astrophysics", finding_type="correlation",
                   data_source="sdss", strength=0.6, p_value=0.01,
                   cycle=1, idx=1):
    return DiscoveryRecord(
        id=f"D{idx:04d}",
        timestamp=time.time() - (100 - idx),
        cycle=cycle,
        hypothesis_id=f"H{idx:03d}",
        domain=domain,
        finding_type=finding_type,
        variables=["var_a", "var_b"],
        statistic=2.5,
        p_value=p_value,
        description=f"Test discovery {idx}",
        data_source=data_source,
        strength=strength,
    )


def make_outcome(success=True, significant_results=2, cycle=1,
                 method="evaluate_galaxy", domain="Astrophysics"):
    return MethodOutcome(
        method_name=method,
        hypothesis_id="H001",
        domain=domain,
        timestamp=time.time(),
        cycle=cycle,
        data_points=100,
        tests_run=3,
        significant_results=significant_results,
        novelty_signals=0,
        confidence_delta=0.05 if success else -0.02,
        success=success,
    )


# ── 1. Degradation Detection Tests ──────────────────────────────

class TestDegradationDetector:
    def test_no_degradation_with_good_outcomes(self):
        """Healthy engine should not trigger degradation."""
        dd = DegradationDetector()
        mem = DiscoveryMemory.__new__(DiscoveryMemory)
        mem.discoveries = deque(maxlen=500)
        mem.method_outcomes = deque(maxlen=500)
        
        # Add 20 successful outcomes
        for i in range(20):
            mem.method_outcomes.append(make_outcome(success=True, significant_results=3))
        
        result = dd.check_after_cycle(mem, cycle=1)
        assert not result["degraded"]
        assert result["metrics"]["rolling_success_rate"] == 1.0
        assert "TRIGGER_SAFE_MODE" not in result["actions"]

    def test_safe_mode_triggered_after_streak(self):
        """5 consecutive low-success cycles should trigger SAFE_MODE."""
        dd = DegradationDetector()
        mem = DiscoveryMemory.__new__(DiscoveryMemory)
        mem.discoveries = deque(maxlen=500)
        mem.method_outcomes = deque(maxlen=500)
        
        # Add 20 failed outcomes (success rate = 0%)
        for i in range(20):
            mem.method_outcomes.append(make_outcome(success=False, significant_results=0))
        
        # Run 5 consecutive checks
        for cycle in range(1, 6):
            result = dd.check_after_cycle(mem, cycle=cycle)
        
        assert result["degraded"]
        assert "TRIGGER_SAFE_MODE" in result["actions"]
        assert dd.safe_mode_triggered

    def test_safe_mode_not_triggered_below_streak(self):
        """Under 5 consecutive bad cycles should NOT trigger SAFE_MODE."""
        dd = DegradationDetector()
        mem = DiscoveryMemory.__new__(DiscoveryMemory)
        mem.discoveries = deque(maxlen=500)
        mem.method_outcomes = deque(maxlen=500)
        
        # Bad outcomes
        for i in range(20):
            mem.method_outcomes.append(make_outcome(success=False, significant_results=0))
        
        # Only 4 consecutive checks
        for cycle in range(1, 5):
            result = dd.check_after_cycle(mem, cycle=cycle)
        
        assert "TRIGGER_SAFE_MODE" not in result["actions"]
        assert not dd.safe_mode_triggered

    def test_domain_concentration_detected(self):
        """>80% of discoveries in one domain should trigger DIVERSIFY_DOMAINS."""
        dd = DegradationDetector()
        mem = DiscoveryMemory.__new__(DiscoveryMemory)
        mem.discoveries = deque(maxlen=500)
        mem.method_outcomes = deque(maxlen=500)
        
        # Add 50 discoveries, 45 in Astrophysics (90%)
        for i in range(45):
            mem.discoveries.append(make_discovery(domain="Astrophysics", idx=i+1))
        for i in range(5):
            mem.discoveries.append(make_discovery(domain="Economics", idx=46+i))
        
        # Need outcomes too
        for i in range(5):
            mem.method_outcomes.append(make_outcome(success=True))
        
        result = dd.check_after_cycle(mem, cycle=1)
        assert "DIVERSIFY_DOMAINS" in result["actions"]
        assert result["metrics"]["dominant_domain"] == "Astrophysics"

    def test_pattern_repetition_detected(self):
        """Same finding_type+data_source repeated ≥5 times should trigger BREAK_REPETITION."""
        dd = DegradationDetector()
        mem = DiscoveryMemory.__new__(DiscoveryMemory)
        mem.discoveries = deque(maxlen=500)
        mem.method_outcomes = deque(maxlen=500)
        
        # Add 10 discoveries with same pattern
        for i in range(10):
            mem.discoveries.append(make_discovery(
                finding_type="causal", data_source="sdss", idx=i+1
            ))
        for i in range(5):
            mem.method_outcomes.append(make_outcome(success=True))
        
        result = dd.check_after_cycle(mem, cycle=1)
        assert "BREAK_REPETITION" in result["actions"]

    def test_strategy_switch_after_10_cycles(self):
        """10 consecutive cycles with low significant results should recommend strategy switch."""
        dd = DegradationDetector()
        mem = DiscoveryMemory.__new__(DiscoveryMemory)
        mem.discoveries = deque(maxlen=500)
        mem.method_outcomes = deque(maxlen=500)
        
        # Outcomes with 0 significant results
        for i in range(20):
            mem.method_outcomes.append(make_outcome(success=True, significant_results=0))
        
        # Run 10 checks
        for cycle in range(1, 11):
            result = dd.check_after_cycle(mem, cycle=cycle)
        
        assert "SWITCH_STRATEGY" in result["actions"]
        assert dd.strategy_switch_recommended

    def test_least_explored_domain(self):
        """get_least_explored_domain should return domain with fewest discoveries."""
        dd = DegradationDetector()
        mem = DiscoveryMemory.__new__(DiscoveryMemory)
        mem.discoveries = deque(maxlen=500)
        
        for i in range(30):
            mem.discoveries.append(make_discovery(domain="Astrophysics", idx=i+1))
        for i in range(5):
            mem.discoveries.append(make_discovery(domain="Economics", idx=31+i))
        
        least = dd.get_least_explored_domain(mem,
                                              ["Astrophysics", "Economics", "Climate", "Epidemiology"])
        assert least in ("Climate", "Epidemiology")  # both have 0

    def test_get_status(self):
        """get_status should return well-formed dict."""
        dd = DegradationDetector()
        status = dd.get_status()
        assert "last_check_cycle" in status
        assert "thresholds" in status
        assert "rolling_success_rates" in status


# ── 2. Importance-Weighted Compaction Tests ──────────────────────

class TestMemoryCompaction:
    def test_compaction_evicts_lowest_importance(self, tmp_path):
        """Compaction should evict lowest-importance discoveries."""
        db_path = str(tmp_path / "test.db")
        mem = DiscoveryMemory(max_records=20, db_path=db_path)

        # Add 20 discoveries: 15 weak Astrophysics, 5 strong Economics
        # Use different variables for each to avoid deduplication
        for i in range(15):
            mem.record_discovery(
                hypothesis_id=f"H{i:03d}", domain="Astrophysics",
                finding_type="correlation", variables=[f"x{i}", f"y{i}"],
                statistic=0.5, p_value=0.8,  # weak
                description=f"weak {i}", data_source="sdss",
                sample_size=10,
            )
        for i in range(5):
            mem.record_discovery(
                hypothesis_id=f"H{100+i:03d}", domain="Economics",
                finding_type="scaling", variables=[f"a{i}", f"b{i}"],
                statistic=8.0, p_value=0.001,  # strong
                description=f"strong {i}", data_source="cross",
                sample_size=5000,
            )

        assert len(mem.discoveries) == 20

        # Trigger compaction
        result = mem.compact_if_needed()
        assert result  # should have compacted

        # Verify strong discoveries (Economics) survived more than weak ones
        remaining_domains = [d.domain for d in mem.discoveries]
        econ_count = remaining_domains.count("Economics")
        assert econ_count >= 4, f"Expected ≥4 Economics discoveries to survive, got {econ_count}"

    def test_compaction_preserves_diverse_domains(self, tmp_path):
        """Discoveries from underrepresented domains should get diversity bonus."""
        db_path = str(tmp_path / "test.db")
        mem = DiscoveryMemory(max_records=20, db_path=db_path)

        # Fill with 19 Astrophysics + 1 Climate (same strength)
        # Use different variables for each to avoid deduplication
        for i in range(19):
            mem.record_discovery(
                hypothesis_id=f"H{i:03d}", domain="Astrophysics",
                finding_type="correlation", variables=[f"x{i}", f"y{i}"],
                statistic=3.0, p_value=0.01,
                description=f"astro {i}", data_source="sdss",
                sample_size=100,
            )
        mem.record_discovery(
            hypothesis_id="H100", domain="Climate",
            finding_type="trend", variables=["temp", "co2"],
            statistic=3.0, p_value=0.01,
            description="climate 1", data_source="climate",
            sample_size=100,
        )
        
        mem.compact_if_needed()
        
        # Climate discovery should survive (diversity bonus)
        climate_remaining = [d for d in mem.discoveries if d.domain == "Climate"]
        assert len(climate_remaining) >= 1, "Climate discovery should survive compaction due to diversity bonus"

    def test_no_compaction_below_cap(self, tmp_path):
        """No compaction should happen when below capacity."""
        db_path = str(tmp_path / "test.db")
        mem = DiscoveryMemory(max_records=100, db_path=db_path)

        # Use different variables for each to avoid deduplication
        for i in range(10):
            mem.record_discovery(
                hypothesis_id=f"H{i:03d}", domain="Astrophysics",
                finding_type="correlation", variables=[f"x{i}", f"y{i}"],
                statistic=2.0, p_value=0.05,
                description=f"disc {i}", data_source="sdss",
                sample_size=50,
            )

        result = mem.compact_if_needed()
        assert not result  # should NOT compact
        assert len(mem.discoveries) == 10


# ── 3. Hypothesis Lifecycle Tests ────────────────────────────────

class TestHypothesisLifecycle:
    def test_lifecycle_timestamps_exist(self):
        """Hypothesis should have lifecycle timestamp fields."""
        h = Hypothesis(id="H001", name="Test", domain="Astro",
                       description="Test hypothesis")
        assert hasattr(h, 'last_tested_at')
        assert hasattr(h, 'archived_at')
        assert h.last_tested_at == 0.0
        assert h.archived_at == 0.0

    def test_last_tested_at_set_on_pvalue_update(self):
        """update_from_pvalue should set last_tested_at."""
        h = Hypothesis(id="H001", name="Test", domain="Astro",
                       description="Test hypothesis")
        assert h.last_tested_at == 0.0
        h.update_from_pvalue(0.01)
        assert h.last_tested_at > 0

    def test_archived_at_set_on_prune(self):
        """prune_if_weak should set archived_at."""
        h = Hypothesis(id="H001", name="Test", domain="Astro",
                       description="Test hypothesis", confidence=0.1)
        h.test_results = [{"p_value": 0.5}, {"p_value": 0.6}, {"p_value": 0.7}]
        assert h.archived_at == 0.0
        h.prune_if_weak(0.2)
        assert h.phase == Phase.ARCHIVED
        assert h.archived_at > 0


# ── Run ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
