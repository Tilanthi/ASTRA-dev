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
Tests for Stigmergy Integration — Phase 4

Covers:
- Pheromone deposit and sense round-trip
- Evaporation over time
- Gradient computation
- StigmergyBridge hooks
- Hypothesis ranking with pheromones
- A/B testing framework
- Circuit breaker logic
- Persistence save/load
- Swarm agent behaviors
- Gordon parameter validation
- API endpoint smoke tests
"""
import os
import sys
import json
import time
import tempfile
import pytest

# Add paths — use direct subpackage imports to avoid astra_core.__init__ cascading errors
_base = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, _base)
_core = os.path.join(_base, 'astra_core')
sys.path.insert(0, _core)

# Direct file imports — bypass all __init__.py to avoid cascading import errors
import importlib.util

def _import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_pd = _import_from_file(
    'intelligence.pheromone_dynamics',
    os.path.join(_core, 'intelligence', 'pheromone_dynamics.py')
)
DigitalPheromoneField = _pd.DigitalPheromoneField
PheromoneType = _pd.PheromoneType
PheromoneFieldConfig = _pd.PheromoneFieldConfig
PheromoneDeposit = _pd.PheromoneDeposit

_sm = _import_from_file(
    'self_teaching.stigmergic_memory',
    os.path.join(_core, 'self_teaching', 'stigmergic_memory.py')
)
StigmergicMemory = _sm.StigmergicMemory
StigmergicConfig = _sm.StigmergicConfig
FieldType = _sm.FieldType

_tr = _import_from_file(
    'swarm.transforms',
    os.path.join(_core, 'swarm', 'transforms.py')
)
PheromoneUpdater = _tr.PheromoneUpdater
CuriosityValueCalculator = _tr.CuriosityValueCalculator
GORDON_PARAMS = _tr.GORDON_PARAMS
GordonTransforms = _tr.GordonTransforms

# Now stigmergy_bridge can import these modules from sys.modules
from astra_live_backend.stigmergy_bridge import StigmergyBridge, DOMAIN_MIXTURES
from astra_live_backend.swarm_agents import (
    ExplorerAgent, ExploiterAgent, FalsifierAgent, AnalogistAgent, ScoutAgent,
    SwarmCoordinator,
)


# =========================================================================
# Pheromone Field Tests
# =========================================================================

class TestPheromoneField:
    """Test DigitalPheromoneField deposit/sense round-trip."""

    def test_deposit_and_sense(self):
        field = DigitalPheromoneField()
        mixture = {'CLD': 0.8, 'D1': 0.1, 'D2': 0.1}
        field.deposit_success(domain_mixture=mixture, strength=3.0)
        concs = field.sense({'domain_mixture': mixture}, radius=0)
        assert concs['success'] >= 2.0, f"Expected success >= 2.0, got {concs['success']}"

    def test_exploration_deposit(self):
        field = DigitalPheromoneField()
        mixture = {'CLD': 0.5, 'D1': 0.3, 'D2': 0.2}
        field.deposit_exploration(domain_mixture=mixture, strength=2.0)
        concs = field.sense({'domain_mixture': mixture}, radius=0)
        assert concs['exploration'] > 0

    def test_failure_deposit(self):
        field = DigitalPheromoneField()
        mixture = {'CLD': 0.3, 'D1': 0.3, 'D2': 0.4}
        field.deposit_failure(domain_mixture=mixture, strength=1.5)
        concs = field.sense({'domain_mixture': mixture}, radius=0)
        assert concs['failure'] > 0

    def test_novelty_deposit(self):
        field = DigitalPheromoneField()
        mixture = {'CLD': 0.1, 'D1': 0.1, 'D2': 0.8}
        field.deposit_novelty('test_family', domain_mixture=mixture, strength=3.0)
        concs = field.sense({'domain_mixture': mixture}, radius=0)
        assert concs['novelty'] > 0

    def test_evaporation(self):
        field = DigitalPheromoneField()
        mixture = {'CLD': 0.5, 'D1': 0.3, 'D2': 0.2}
        field.deposit_success(domain_mixture=mixture, strength=5.0)

        # Force evaporation by manipulating timestamp
        field._last_evaporation = time.time() - 100
        concs_after = field.sense({'domain_mixture': mixture}, radius=0)
        # After 100 seconds with rate 0.02, decay = exp(-0.02*100) ≈ 0.135
        assert concs_after['success'] < 5.0, "Evaporation should reduce concentration"

    def test_gradient_computation(self):
        field = DigitalPheromoneField()
        # Deposit at a specific location
        field.deposit_success(
            domain_mixture={'CLD': 0.8, 'D1': 0.1, 'D2': 0.1}, strength=5.0
        )
        # Check gradient at nearby location
        grad = field.sense_gradient(
            {'domain_mixture': {'CLD': 0.5, 'D1': 0.3, 'D2': 0.2}},
            PheromoneType.SUCCESS
        )
        assert 'CLD' in grad and 'D1' in grad and 'D2' in grad

    def test_hot_spots(self):
        field = DigitalPheromoneField()
        field.deposit_success(
            domain_mixture={'CLD': 0.8, 'D1': 0.1, 'D2': 0.1}, strength=5.0
        )
        spots = field.get_hot_spots(PheromoneType.SUCCESS, threshold=0.1)
        assert len(spots) >= 1
        assert spots[0][1] > 0

    def test_serialization(self):
        field = DigitalPheromoneField()
        field.deposit_success(
            domain_mixture={'CLD': 0.5, 'D1': 0.3, 'D2': 0.2}, strength=3.0
        )
        field.deposit_exploration(
            domain_mixture={'CLD': 0.1, 'D1': 0.8, 'D2': 0.1}, strength=1.0
        )

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            field.save(f.name)
            loaded = DigitalPheromoneField.load(f.name)
            os.unlink(f.name)

        orig_stats = field.stats()
        loaded_stats = loaded.stats()
        assert orig_stats['total_deposits'] == loaded_stats['total_deposits']

    def test_stats(self):
        field = DigitalPheromoneField()
        field.deposit_success(
            domain_mixture={'CLD': 0.5, 'D1': 0.3, 'D2': 0.2}, strength=2.0
        )
        stats = field.stats()
        assert 'total_deposits' in stats
        assert 'deposits_by_type' in stats
        assert 'field_stats' in stats
        assert stats['total_deposits'] >= 1

    def test_suggest_exploration_direction(self):
        field = DigitalPheromoneField()
        field.deposit_success(
            domain_mixture={'CLD': 0.8, 'D1': 0.1, 'D2': 0.1}, strength=5.0
        )
        direction = field.suggest_exploration_direction(
            {'CLD': 0.5, 'D1': 0.3, 'D2': 0.2}, strategy='balanced'
        )
        assert 'CLD' in direction
        # Strategies
        for s in ['explore', 'exploit', 'avoid_failure']:
            d = field.suggest_exploration_direction(
                {'CLD': 0.5, 'D1': 0.3, 'D2': 0.2}, strategy=s
            )
            assert isinstance(d, dict)


# =========================================================================
# Stigmergic Memory Tests
# =========================================================================

class TestStigmergicMemory:
    """Test StigmergicMemory deposit and query."""

    def test_deposit_pheromone(self):
        mem = StigmergicMemory()
        trail_id = mem.deposit_pheromone({
            'location': 'astrophysics_correlation',
            'strength': 2.0,
            'field_type': 'aggregation',
            'domain': 'astrophysics',
            'reward': 0.5,
        })
        assert trail_id.startswith('trail_')
        assert mem.total_deposits == 1

    def test_add_discovery(self):
        mem = StigmergicMemory()
        sig_id = mem.add_discovery({
            'content': 'Galaxy bimodality confirmed with u-g color peaks',
            'domain': 'astrophysics',
            'reward': 0.8,
            'novelty': 0.5,
        })
        assert sig_id.startswith('sig_')
        assert mem.total_discoveries == 1

    def test_analyze_gaps(self):
        mem = StigmergicMemory()
        gaps = mem.analyze_gaps()
        assert isinstance(gaps, dict)
        # Empty memory should show gaps
        for domain, gap in gaps.items():
            assert 0 <= gap <= 1.0

    def test_get_state(self):
        mem = StigmergicMemory()
        state = mem.get_state()
        assert 'n_fields' in state
        assert 'integration_score' in state

    def test_swarm_recommendations(self):
        mem = StigmergicMemory()
        mem.deposit_pheromone({
            'location': 'astrophysics_correlation',
            'strength': 3.0,
            'field_type': 'aggregation',
            'domain': 'astrophysics',
            'reward': 0.8,
        })
        recs = mem.get_swarm_recommendations('astrophysics', 'explorer')
        assert isinstance(recs, list)

    def test_persistence(self):
        mem = StigmergicMemory()
        mem.deposit_pheromone({
            'location': 'test_location',
            'strength': 1.0,
            'field_type': 'aggregation',
            'domain': 'test',
        })
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            mem.persist(f.name)
            with open(f.name) as rf:
                data = json.load(rf)
            os.unlink(f.name)
        assert data['statistics']['total_deposits'] == 1


# =========================================================================
# StigmergyBridge Tests
# =========================================================================

class TestStigmergyBridge:
    """Test the StigmergyBridge integration layer."""

    def setup_method(self):
        self.bridge = StigmergyBridge(pheromone_weight=0.3)

    def test_on_hypothesis_tested_success(self):
        h = {'id': 'H1', 'domain': 'Astrophysics', 'confidence': 0.8,
             'category': 'correlation', 'name': 'Galaxy Bimodality'}
        result = {'passed': True, 'p_value': 0.001, 'effect_size': 1.5}
        dep_id = self.bridge.on_hypothesis_tested(h, result)
        assert dep_id is not None
        assert self.bridge.metrics['success_deposits'] == 1

    def test_on_hypothesis_tested_failure(self):
        h = {'id': 'H2', 'domain': 'Economics', 'confidence': 0.5,
             'category': 'trend', 'name': 'Phillips Curve'}
        result = {'passed': False, 'p_value': 0.8, 'effect_size': 0.1}
        dep_id = self.bridge.on_hypothesis_tested(h, result)
        assert dep_id is not None
        assert self.bridge.metrics['failure_deposits'] == 1

    def test_rank_hypotheses(self):
        candidates = [
            {'id': 'H1', 'domain': 'Astrophysics', 'category': 'correlation'},
            {'id': 'H2', 'domain': 'Economics', 'category': 'trend'},
            {'id': 'H3', 'domain': 'Climate', 'category': 'anomaly'},
        ]
        scores = [0.8, 0.6, 0.7]
        ranked = self.bridge.rank_hypotheses(candidates, scores)
        assert len(ranked) == 3
        # Should be sorted by score descending
        for i in range(len(ranked) - 1):
            assert ranked[i][1] >= ranked[i + 1][1]

    def test_on_discovery(self):
        discovery = {
            'domain': 'Astrophysics',
            'category': 'correlation',
            'significance': 0.9,
            'content': 'Galaxy color bimodality confirmed',
        }
        sig_id = self.bridge.on_discovery(discovery)
        assert sig_id is not None
        assert self.bridge.metrics['novelty_deposits'] == 1

    def test_get_exploration_direction(self):
        direction = self.bridge.get_exploration_direction('Astrophysics')
        assert 'strategy' in direction
        assert 'curiosity_value' in direction
        assert 'knowledge_gaps' in direction
        assert direction['strategy'] in ('explore', 'exploit', 'balanced')

    def test_ab_testing(self):
        for _ in range(10):
            self.bridge.record_ab_result(guided=True, success=True)
        for _ in range(10):
            self.bridge.record_ab_result(guided=False, success=False)
        summary = self.bridge.get_ab_summary()
        assert summary['pheromone_guided']['rate'] == 1.0
        assert summary['baseline']['rate'] == 0.0

    def test_circuit_breaker_not_triggered(self):
        # Not enough data → should not trigger
        assert self.bridge.check_circuit_breaker() is False

    def test_circuit_breaker_triggered(self):
        # Simulate bad pheromone performance
        for _ in range(25):
            self.bridge.record_ab_result(guided=True, success=False)
        for _ in range(25):
            self.bridge.record_ab_result(guided=False, success=True)
        old_weight = self.bridge.pheromone_weight
        triggered = self.bridge.check_circuit_breaker()
        assert triggered is True
        assert self.bridge.pheromone_weight < old_weight

    def test_persistence_roundtrip(self):
        # Make some deposits
        self.bridge.on_hypothesis_tested(
            {'id': 'H1', 'domain': 'Astrophysics', 'confidence': 0.9, 'category': 'hubble'},
            {'passed': True, 'p_value': 0.001, 'effect_size': 2.0}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            import astra_live_backend.stigmergy_bridge as sb
            old_dir = sb.STATE_DIR
            sb.STATE_DIR = type(old_dir)(tmpdir)
            sb.PHEROMONE_STATE_FILE = sb.STATE_DIR / 'pheromone_field.json'
            sb.STIGMERGY_STATE_FILE = sb.STATE_DIR / 'stigmergic_memory.json'
            sb.METRICS_FILE = sb.STATE_DIR / 'metrics.json'

            self.bridge.persist_state()
            assert (sb.STATE_DIR / 'pheromone_field.json').exists()
            assert (sb.STATE_DIR / 'metrics.json').exists()

            # Restore paths
            sb.STATE_DIR = old_dir
            sb.PHEROMONE_STATE_FILE = old_dir / 'pheromone_field.json'
            sb.STIGMERGY_STATE_FILE = old_dir / 'stigmergic_memory.json'
            sb.METRICS_FILE = old_dir / 'metrics.json'

    def test_set_weight(self):
        w = self.bridge.set_weight(0.7)
        assert w == 0.7
        w = self.bridge.set_weight(1.5)  # Should clamp
        assert w == 1.0
        w = self.bridge.set_weight(-0.5)  # Should clamp
        assert w == 0.0

    def test_get_status(self):
        status = self.bridge.get_status()
        assert 'pheromone_weight' in status
        assert 'pheromone_field' in status
        assert 'stigmergic_memory' in status
        assert 'metrics' in status
        assert 'ab_test' in status
        assert 'gordon_params' in status

    def test_domain_to_mixture(self):
        for domain in ['Astrophysics', 'Economics', 'Climate', 'Epidemiology']:
            m = self.bridge._domain_to_mixture(domain)
            total = m['CLD'] + m['D1'] + m['D2']
            assert abs(total - 1.0) < 0.01, f"{domain} mixture doesn't sum to 1"

    def test_recent_deposits(self):
        self.bridge.on_hypothesis_tested(
            {'id': 'H1', 'domain': 'Astrophysics', 'confidence': 0.9, 'category': 'hubble'},
            {'passed': True, 'p_value': 0.01, 'effect_size': 1.0}
        )
        deposits = self.bridge.get_recent_deposits()
        assert len(deposits) >= 1


# =========================================================================
# Swarm Agent Tests
# =========================================================================

class TestSwarmAgents:
    """Test swarm agent behavior."""

    def setup_method(self):
        self.bridge = StigmergyBridge(pheromone_weight=0.3)

    def test_explorer_decide(self):
        agent = ExplorerAgent()
        action = agent.decide(self.bridge)
        assert action.action_type == 'explore'
        assert action.target_domain in ['Astrophysics', 'Economics', 'Climate',
                                         'Epidemiology', 'Cross-Domain']

    def test_exploiter_decide(self):
        # Deposit some success first
        self.bridge.pheromone_field.deposit_success(
            domain_mixture={'CLD': 0.8, 'D1': 0.1, 'D2': 0.1}, strength=5.0
        )
        agent = ExploiterAgent()
        action = agent.decide(self.bridge)
        assert action.action_type == 'exploit'

    def test_falsifier_decide(self):
        agent = FalsifierAgent()
        action = agent.decide(self.bridge)
        assert action.action_type == 'test'

    def test_analogist_decide(self):
        agent = AnalogistAgent()
        action = agent.decide(self.bridge)
        assert action.action_type == 'analogize'
        assert 'domain_b' in action.metadata

    def test_scout_decide(self):
        agent = ScoutAgent()
        action = agent.decide(self.bridge)
        assert action.action_type == 'scout'

    def test_explorer_deposit(self):
        agent = ExplorerAgent()
        action = agent.decide(self.bridge)
        dep_id = agent.deposit(self.bridge, action, {})
        assert dep_id is not None
        assert agent.actions_taken == 1

    def test_contact_rate_protocol(self):
        agent = ExplorerAgent()
        # First call should act (enough time elapsed)
        agent.last_contact_time = time.time() - 100  # Force elapsed time
        assert agent.should_act() is True

    def test_contact_rate_adjustment(self):
        agent = ExploiterAgent()
        initial_rate = agent.contact_rate
        agent.adjust_contact_rate(success=True)
        assert agent.contact_rate > initial_rate
        agent.adjust_contact_rate(success=False)
        # Should decrease but not below min
        assert agent.contact_rate >= GORDON_PARAMS['contact_rate_min']

    def test_swarm_coordinator(self):
        coord = SwarmCoordinator(self.bridge)
        summary = coord.get_swarm_summary()
        assert summary['agent_count'] == 5
        assert len(summary['agents']) == 5

    def test_coordinator_orient(self):
        coord = SwarmCoordinator(self.bridge)
        coord.scout.last_contact_time = time.time() - 100
        action = coord.run_orient_phase()
        # May return None due to task switching
        if action:
            assert action.action_type == 'scout'

    def test_coordinator_select(self):
        coord = SwarmCoordinator(self.bridge)
        candidates = [
            {'id': 'H1', 'domain': 'Astrophysics', 'category': 'correlation'},
            {'id': 'H2', 'domain': 'Economics', 'category': 'trend'},
        ]
        ranked = coord.run_select_phase(candidates, [0.8, 0.6])
        assert len(ranked) == 2


# =========================================================================
# Gordon Parameter Tests
# =========================================================================

class TestGordonParams:
    """Test Gordon's immutable biological parameters."""

    def test_evaporation_rate(self):
        assert GORDON_PARAMS['evaporation_rate'] == 0.05

    def test_reinforcement_rate(self):
        assert GORDON_PARAMS['reinforcement_rate'] == 0.1

    def test_anternet_weight(self):
        assert GORDON_PARAMS['anternet_weight'] == 0.6

    def test_restraint_weight(self):
        assert GORDON_PARAMS['restraint_weight'] == 0.4

    def test_switch_probability(self):
        assert GORDON_PARAMS['switch_probability'] == 0.15

    def test_contact_rate_range(self):
        assert GORDON_PARAMS['contact_rate_min'] < GORDON_PARAMS['contact_rate_max']
        assert GORDON_PARAMS['contact_rate_min'] == 0.033
        assert GORDON_PARAMS['contact_rate_max'] == 0.167

    def test_pheromone_updater(self):
        updater = PheromoneUpdater()
        # Evaporation
        tau = updater.evaporate(1.0)
        assert tau == 0.95  # 1.0 * (1 - 0.05)
        # Reinforcement
        tau = updater.reinforce(0.5, 1.0)
        assert abs(tau - 0.6) < 0.001  # 0.5 + 0.1 * 1.0
        # Combined update
        tau = updater.update(0.5, 1.0)
        assert 0.1 <= tau <= 1.0

    def test_curiosity_calculator(self):
        calc = CuriosityValueCalculator()
        # No data → high exploration
        c_k = calc.calculate(0, 0, 0.5)
        assert c_k == 0.8
        # All success → low exploration
        c_k = calc.calculate(10, 10, 0.0)
        assert c_k <= 0.3
        # All failure → high exploration
        c_k = calc.calculate(0, 10, 1.0)
        assert c_k >= 0.7

    def test_gordon_transforms(self):
        rule = GordonTransforms.trail_evaporation()
        assert 'evaporation' in rule.description.lower()
        rule = GordonTransforms.trail_reinforcement()
        assert 'reinforcement' in rule.description.lower()
        rule = GordonTransforms.anternet_feedback()
        assert 'anternet' in rule.description.lower()
        rule = GordonTransforms.collective_restraint()
        assert 'restraint' in rule.description.lower()


# =========================================================================
# Integration Test
# =========================================================================

class TestEndToEnd:
    """End-to-end integration test."""

    def test_full_cycle(self):
        """Simulate a full research cycle through the bridge."""
        bridge = StigmergyBridge(pheromone_weight=0.4)

        # 1. Start cycle
        bridge.on_engine_cycle(1)

        # 2. Get exploration direction
        direction = bridge.get_exploration_direction('Astrophysics')
        assert direction['strategy'] in ('explore', 'exploit', 'balanced')

        # 3. Test a hypothesis (success)
        dep1 = bridge.on_hypothesis_tested(
            {'id': 'H1', 'domain': 'Astrophysics', 'confidence': 0.8,
             'category': 'correlation'},
            {'passed': True, 'p_value': 0.001, 'effect_size': 2.0}
        )

        # 4. Test a hypothesis (failure)
        dep2 = bridge.on_hypothesis_tested(
            {'id': 'H2', 'domain': 'Economics', 'confidence': 0.4,
             'category': 'trend'},
            {'passed': False, 'p_value': 0.7, 'effect_size': 0.1}
        )

        # 5. Record discovery
        sig = bridge.on_discovery({
            'domain': 'Astrophysics',
            'category': 'correlation',
            'significance': 0.95,
            'content': 'Test discovery',
        })

        # 6. Rank hypotheses
        ranked = bridge.rank_hypotheses(
            [{'id': 'H1', 'domain': 'Astrophysics', 'category': 'correlation'},
             {'id': 'H2', 'domain': 'Economics', 'category': 'trend'}],
            [0.8, 0.6]
        )

        # 7. Check metrics
        assert bridge.metrics['total_deposits'] >= 2
        assert bridge.metrics['success_deposits'] >= 1
        assert bridge.metrics['failure_deposits'] >= 1

        # 8. Run swarm
        coord = SwarmCoordinator(bridge)
        coord.run_update_phase([
            {'domain': 'Astrophysics', 'passed': True, 'hypothesis_id': 'H1',
             'effect_size': 2.0},
        ])

        # 9. Get status
        status = bridge.get_status()
        assert status['metrics']['total_deposits'] >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
