"""
Stigmergy Bridge — Connects the pheromone/stigmergy subsystem to the live DiscoveryEngine.

This bridge provides:
1. Automatic pheromone deposits on hypothesis test results
2. Pheromone-guided hypothesis ranking
3. Stigmergic memory for discovery persistence
4. Gordon's biological transforms for exploration/exploitation
5. State persistence across restarts
6. A/B testing framework to validate pheromone guidance
7. Safety circuit breaker if pheromone guidance degrades performance
"""
import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import pheromone subsystem from astra_core — use importlib to bypass broken __init__.py chains
import sys
import importlib.util

_CORE_PATH = str(Path(__file__).parent.parent / 'astra_core')
if _CORE_PATH not in sys.path:
    sys.path.insert(0, _CORE_PATH)


def _import_module_from_file(name: str, filepath: str):
    """Import a module directly from file, bypassing __init__.py."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_pd = _import_module_from_file(
    'intelligence.pheromone_dynamics',
    str(Path(_CORE_PATH) / 'intelligence' / 'pheromone_dynamics.py')
)
DigitalPheromoneField = _pd.DigitalPheromoneField
PheromoneType = _pd.PheromoneType
PheromoneFieldConfig = _pd.PheromoneFieldConfig

_sm = _import_module_from_file(
    'self_teaching.stigmergic_memory',
    str(Path(_CORE_PATH) / 'self_teaching' / 'stigmergic_memory.py')
)
StigmergicMemory = _sm.StigmergicMemory
StigmergicConfig = _sm.StigmergicConfig
FieldType = _sm.FieldType

_tr = _import_module_from_file(
    'swarm.transforms',
    str(Path(_CORE_PATH) / 'swarm' / 'transforms.py')
)
PheromoneUpdater = _tr.PheromoneUpdater
CuriosityValueCalculator = _tr.CuriosityValueCalculator
GORDON_PARAMS = _tr.GORDON_PARAMS

logger = logging.getLogger('astra.stigmergy')

STATE_DIR = Path(__file__).parent.parent / 'data' / 'stigmergy'
PHEROMONE_STATE_FILE = STATE_DIR / 'pheromone_field.json'
STIGMERGY_STATE_FILE = STATE_DIR / 'stigmergic_memory.json'
METRICS_FILE = STATE_DIR / 'metrics.json'

# Domain mixture coordinates for mapping domain strings to V36 simplex
DOMAIN_MIXTURES = {
    'Astrophysics': {'CLD': 0.8, 'D1': 0.1, 'D2': 0.1},
    'astrophysics': {'CLD': 0.8, 'D1': 0.1, 'D2': 0.1},
    'Economics': {'CLD': 0.1, 'D1': 0.8, 'D2': 0.1},
    'economics': {'CLD': 0.1, 'D1': 0.8, 'D2': 0.1},
    'Climate': {'CLD': 0.3, 'D1': 0.3, 'D2': 0.4},
    'climate': {'CLD': 0.3, 'D1': 0.3, 'D2': 0.4},
    'Epidemiology': {'CLD': 0.1, 'D1': 0.1, 'D2': 0.8},
    'epidemiology': {'CLD': 0.1, 'D1': 0.1, 'D2': 0.8},
    'physics': {'CLD': 0.6, 'D1': 0.2, 'D2': 0.2},
    'biology': {'CLD': 0.2, 'D1': 0.2, 'D2': 0.6},
    'chemistry': {'CLD': 0.2, 'D1': 0.4, 'D2': 0.4},
    'materials': {'CLD': 0.4, 'D1': 0.4, 'D2': 0.2},
    'Cross-Domain': {'CLD': 0.33, 'D1': 0.33, 'D2': 0.34},
}

# Map hypothesis categories to V36 symbolic templates
CATEGORY_TEMPLATES = {
    'correlation': 'stable_autoregressive',
    'trend': 'responsive_autoregressive',
    'anomaly': 'unstable_autoregressive',
    'lag': 'delayed_response',
    'exponential': 'nonlinear_exponential',
    'interaction': 'nonlinear_multiplicative',
    'regime': 'regime_dependent',
    'hubble': 'stable_autoregressive',
    'galaxy': 'stable_autoregressive',
    'exoplanet': 'responsive_autoregressive',
    'stellar': 'stable_autoregressive',
    'crossdomain': 'nonlinear_multiplicative',
    'star_formation': 'responsive_autoregressive',
    'gravitational_waves': 'unstable_autoregressive',
    'cmb': 'stable_autoregressive',
    'transients': 'unstable_autoregressive',
    'time_domain': 'delayed_response',
}


class StigmergyBridge:
    """
    Bridges the pheromone/stigmergy subsystem with the live DiscoveryEngine.

    Hook points:
    1. on_hypothesis_tested() — after each hypothesis test, deposits pheromones
    2. rank_hypotheses() — re-ranks candidates using pheromone signals
    3. on_discovery() — records discoveries with NOVELTY pheromone
    4. get_exploration_direction() — pheromone-guided domain selection
    5. on_cross_domain_connection() — records cross-domain analogies
    """

    def __init__(self, pheromone_weight: float = 0.3):
        self.pheromone_weight = pheromone_weight
        self.pheromone_field = DigitalPheromoneField()
        self.stigmergic_memory = StigmergicMemory()
        self.gordon_updater = PheromoneUpdater()
        self.curiosity_calc = CuriosityValueCalculator()

        # Metrics tracking
        self.metrics = {
            'total_deposits': 0,
            'success_deposits': 0,
            'failure_deposits': 0,
            'analogy_deposits': 0,
            'novelty_deposits': 0,
            'queries': 0,
            'pheromone_guided_selections': 0,
            'baseline_selections': 0,
            'engine_cycles': 0,
            'last_persist': None,
            'last_success_time': time.time(),
        }

        # A/B testing: compare pheromone-guided vs baseline selections
        self.ab_test_results = {
            'pheromone_guided': {'successes': 0, 'total': 0},
            'baseline': {'successes': 0, 'total': 0},
        }

        # Recent deposit log (ring buffer)
        self._recent_deposits: List[Dict] = []
        self._max_recent = 200

        # Load persisted state
        self._load_state()
        logger.info(f'StigmergyBridge initialized (pheromone_weight={pheromone_weight})')

    # =========================================================================
    # HOOK 1: After hypothesis test
    # =========================================================================

    def on_hypothesis_tested(self, hypothesis: Dict, result: Dict) -> str:
        """
        Called after each hypothesis test — deposits pheromones based on outcome.

        Args:
            hypothesis: Dict with id, domain, confidence, category, name
            result: Dict with passed, p_value, effect_size, test_name

        Returns:
            Deposit ID
        """
        domain = hypothesis.get('domain', 'general')
        confidence = hypothesis.get('confidence', 0.5)
        category = hypothesis.get('category', 'unknown')
        h_id = hypothesis.get('id', '')
        passed = result.get('passed', False)
        p_value = result.get('p_value', 1.0)
        effect_size = result.get('effect_size', 0.0)

        domain_mixture = self._domain_to_mixture(domain)
        template = self._category_to_template(category)

        if passed and p_value < 0.05:
            # SUCCESS: hypothesis confirmed with statistical significance
            strength = 2.0 * (1 - p_value) * (1 + abs(effect_size))
            strength = min(strength, 5.0)

            deposit_id = self.pheromone_field.deposit_success(
                domain_mixture=domain_mixture,
                template=template,
                strength=strength,
                hypothesis_id=h_id,
            )
            self.stigmergic_memory.deposit_pheromone({
                'location': f'{domain}_{category}',
                'strength': strength,
                'field_type': 'aggregation',
                'domain': domain,
                'reward': abs(effect_size),
            })
            self.metrics['success_deposits'] += 1
            self.metrics['last_success_time'] = time.time()
            logger.info(f'SUCCESS pheromone: {domain}/{category} str={strength:.2f} p={p_value:.4f}')
        else:
            # FAILURE: hypothesis rejected or non-significant
            strength = 1.5 * confidence
            deposit_id = self.pheromone_field.deposit_failure(
                domain_mixture=domain_mixture,
                constraint_id=h_id,
                severity='high' if p_value > 0.5 else 'medium',
                strength=strength,
            )
            self.stigmergic_memory.deposit_pheromone({
                'location': f'{domain}_{category}',
                'strength': strength,
                'field_type': 'repulsion',
                'domain': domain,
                'reward': 0.0,
            })
            self.metrics['failure_deposits'] += 1
            logger.info(f'FAILURE pheromone: {domain}/{category} str={strength:.2f} p={p_value:.4f}')

        # Always deposit exploration trail
        self.pheromone_field.deposit_exploration(domain_mixture, strength=0.5)
        self.metrics['total_deposits'] += 1

        # Record in recent deposits
        self._record_deposit(deposit_id, domain, category, passed, strength)

        # Auto-persist every 100 deposits
        if self.metrics['total_deposits'] % 100 == 0:
            self.persist_state()

        return deposit_id

    # =========================================================================
    # HOOK 2: Hypothesis ranking
    # =========================================================================

    def rank_hypotheses(self, candidates: List[Dict],
                        original_scores: List[float]) -> List[Tuple[Dict, float]]:
        """
        Re-rank hypothesis candidates using pheromone signals.

        Blends original engine score with pheromone-based score:
            final = (1 - w) * original + w * pheromone_score

        Args:
            candidates: List of hypothesis dicts
            original_scores: Parallel list of original engine scores

        Returns:
            List of (hypothesis, blended_score) sorted descending
        """
        self.metrics['queries'] += 1
        ranked = []

        for h, orig_score in zip(candidates, original_scores):
            domain = h.get('domain', 'general')
            category = h.get('category', 'unknown')
            domain_mixture = self._domain_to_mixture(domain)
            template = self._category_to_template(category)

            # Sense pheromones at this hypothesis location
            concentrations = self.pheromone_field.sense(
                {'domain_mixture': domain_mixture, 'template': template}
            )

            # Compute pheromone score from concentration landscape
            success_signal = concentrations.get('success', 0)
            failure_signal = concentrations.get('failure', 0)
            novelty_signal = concentrations.get('novelty', 0)
            exploration_signal = concentrations.get('exploration', 0)

            # Prefer: high success, low failure, high novelty, low exploration (unexplored)
            pheromone_score = (
                0.4 * min(success_signal / 3.0, 1.0)
                + 0.2 * max(0, 1.0 - failure_signal / 3.0)
                + 0.2 * min(novelty_signal / 2.0, 1.0)
                + 0.2 * max(0, 1.0 - exploration_signal / 5.0)
            )

            # Blend original score with pheromone score
            final_score = ((1 - self.pheromone_weight) * orig_score
                           + self.pheromone_weight * pheromone_score)
            ranked.append((h, final_score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        self.metrics['pheromone_guided_selections'] += 1
        return ranked

    # =========================================================================
    # HOOK 3: Discovery recording
    # =========================================================================

    def on_discovery(self, discovery: Dict) -> str:
        """
        Record a new discovery — deposits NOVELTY pheromone and stores signature.

        Args:
            discovery: Dict with domain, category, significance, content, etc.

        Returns:
            Signature ID from stigmergic memory
        """
        domain = discovery.get('domain', 'general')
        domain_mixture = self._domain_to_mixture(domain)

        # Deposit novelty pheromone
        self.pheromone_field.deposit_novelty(
            observation_family=discovery.get('category', 'unknown'),
            domain_mixture=domain_mixture,
            strength=3.0 * discovery.get('significance', 1.0),
        )

        # Add to stigmergic memory
        sig_id = self.stigmergic_memory.add_discovery(discovery)
        self.metrics['novelty_deposits'] += 1

        logger.info(f'Discovery recorded: {domain} sig={sig_id}')
        return sig_id

    # =========================================================================
    # HOOK 4: Exploration direction
    # =========================================================================

    def get_exploration_direction(self, current_domain: str) -> Dict[str, Any]:
        """
        Get pheromone-guided exploration direction.

        Uses curiosity value (c_k) to balance explore vs exploit,
        then reads pheromone gradients to suggest direction.

        Args:
            current_domain: Current domain being explored

        Returns:
            Dict with direction, strategy, curiosity_value, knowledge_gaps,
            success_hotspots, novelty_hotspots, recommended_domain
        """
        current_mixture = self._domain_to_mixture(current_domain)

        # Calculate curiosity value from recent performance
        guided = self.ab_test_results['pheromone_guided']
        recent_successes = guided['successes']
        recent_total = max(guided['total'], 1)
        time_since = min(
            (time.time() - self.metrics.get('last_success_time', time.time())) / 3600,
            1.0,
        )
        c_k = self.curiosity_calc.calculate(recent_successes, recent_total, time_since)

        # Choose strategy based on curiosity
        if c_k > 0.7:
            strategy = 'explore'
        elif c_k < 0.3:
            strategy = 'exploit'
        else:
            strategy = 'balanced'

        direction = self.pheromone_field.suggest_exploration_direction(
            current_mixture, strategy
        )

        # Get knowledge gaps from stigmergic memory
        gaps = self.stigmergy_gaps()

        # Get hot spots
        success_spots = self.pheromone_field.get_hot_spots(PheromoneType.SUCCESS, top_k=3)
        novelty_spots = self.pheromone_field.get_hot_spots(PheromoneType.NOVELTY, top_k=3)

        # Recommend domain with largest gap
        recommended = max(gaps, key=gaps.get) if gaps else current_domain

        return {
            'direction': direction,
            'strategy': strategy,
            'curiosity_value': c_k,
            'knowledge_gaps': gaps,
            'success_hotspots': [
                {'mixture': s[0], 'concentration': s[1]} for s in success_spots
            ],
            'novelty_hotspots': [
                {'mixture': n[0], 'concentration': n[1]} for n in novelty_spots
            ],
            'recommended_domain': recommended,
        }

    # =========================================================================
    # Cross-domain analogy
    # =========================================================================

    def on_cross_domain_connection(self, domain_a: str, domain_b: str,
                                   role_a: str, role_b: str, similarity: float):
        """Record a cross-domain analogy discovery."""
        self.pheromone_field.deposit_analogy(
            domain_a, domain_b, role_a, role_b, similarity
        )
        self.metrics['analogy_deposits'] += 1
        logger.info(f'ANALOGY deposited: {domain_a}<->{domain_b} sim={similarity:.2f}')

    # =========================================================================
    # Engine cycle callback
    # =========================================================================

    def on_engine_cycle(self, cycle_count: int):
        """Called at start of each engine cycle."""
        self.metrics['engine_cycles'] = cycle_count

        # Periodic persistence
        if cycle_count % 50 == 0 and cycle_count > 0:
            self.persist_state()

        # Periodic circuit breaker check
        if cycle_count % 20 == 0 and cycle_count > 0:
            self.check_circuit_breaker()

    # =========================================================================
    # A/B Testing
    # =========================================================================

    def record_ab_result(self, guided: bool, success: bool):
        """Record A/B test result for pheromone vs baseline."""
        key = 'pheromone_guided' if guided else 'baseline'
        self.ab_test_results[key]['total'] += 1
        if success:
            self.ab_test_results[key]['successes'] += 1
            if guided:
                self.metrics['last_success_time'] = time.time()

    def get_ab_summary(self) -> Dict:
        """Get A/B test summary with success rates."""
        summary = {}
        for key in ['pheromone_guided', 'baseline']:
            total = self.ab_test_results[key]['total']
            successes = self.ab_test_results[key]['successes']
            summary[key] = {
                'total': total,
                'successes': successes,
                'rate': successes / max(total, 1),
            }
        return summary

    # =========================================================================
    # Safety Circuit Breaker
    # =========================================================================

    def check_circuit_breaker(self) -> bool:
        """
        Check if pheromone guidance should be reduced.
        Triggers if guided performance is >20% worse than baseline.

        Returns:
            True if circuit breaker triggered
        """
        guided = self.ab_test_results['pheromone_guided']
        baseline = self.ab_test_results['baseline']

        if guided['total'] < 20 or baseline['total'] < 20:
            return False  # Not enough data

        guided_rate = guided['successes'] / guided['total']
        baseline_rate = baseline['successes'] / baseline['total']

        if baseline_rate > 0 and guided_rate < baseline_rate * 0.8:
            old_weight = self.pheromone_weight
            self.pheromone_weight = max(0.05, self.pheromone_weight * 0.5)
            logger.warning(
                f'Circuit breaker: pheromone_weight {old_weight:.2f} -> '
                f'{self.pheromone_weight:.2f}'
            )
            return True
        return False

    # =========================================================================
    # Knowledge gaps
    # =========================================================================

    def stigmergy_gaps(self) -> Dict[str, float]:
        """Get knowledge gap analysis from stigmergic memory."""
        gaps = self.stigmergic_memory.analyze_gaps()
        # Extend with domains from our mixture map
        for domain in ['Astrophysics', 'Economics', 'Climate', 'Epidemiology', 'Cross-Domain']:
            if domain.lower() not in gaps and domain not in gaps:
                # Check pheromone field for this domain
                mixture = self._domain_to_mixture(domain)
                concs = self.pheromone_field.sense({'domain_mixture': mixture})
                total_signal = sum(concs.values())
                gaps[domain] = max(0.1, 1.0 - total_signal / 10.0)
        return gaps

    # =========================================================================
    # Persistence
    # =========================================================================

    def persist_state(self):
        """Save all state to disk."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)

        try:
            self.pheromone_field.save(str(PHEROMONE_STATE_FILE))
        except Exception as e:
            logger.warning(f'Could not save pheromone field: {e}')

        try:
            self.stigmergic_memory.persist(str(STIGMERGY_STATE_FILE))
        except Exception as e:
            logger.warning(f'Could not save stigmergic memory: {e}')

        try:
            with open(str(METRICS_FILE), 'w') as f:
                json.dump({
                    'metrics': self.metrics,
                    'ab_test_results': self.ab_test_results,
                    'pheromone_weight': self.pheromone_weight,
                    'timestamp': time.time(),
                }, f, indent=2)
        except Exception as e:
            logger.warning(f'Could not save metrics: {e}')

        self.metrics['last_persist'] = time.time()
        logger.info('Stigmergy state persisted to disk')

    def _load_state(self):
        """Load persisted state if available."""
        try:
            if PHEROMONE_STATE_FILE.exists():
                self.pheromone_field = DigitalPheromoneField.load(
                    str(PHEROMONE_STATE_FILE)
                )
                logger.info('Loaded pheromone field from disk')
        except Exception as e:
            logger.warning(f'Could not load pheromone field: {e}')

        try:
            if STIGMERGY_STATE_FILE.exists():
                with open(str(STIGMERGY_STATE_FILE)) as f:
                    data = json.load(f)
                # Restore trails and discoveries count
                self.stigmergic_memory.total_deposits = data.get(
                    'statistics', {}
                ).get('total_deposits', 0)
                self.stigmergic_memory.total_discoveries = data.get(
                    'statistics', {}
                ).get('total_discoveries', 0)
                logger.info('Loaded stigmergic memory from disk')
        except Exception as e:
            logger.warning(f'Could not load stigmergic memory: {e}')

        try:
            if METRICS_FILE.exists():
                with open(str(METRICS_FILE)) as f:
                    data = json.load(f)
                self.metrics.update(data.get('metrics', {}))
                self.ab_test_results.update(data.get('ab_test_results', {}))
                self.pheromone_weight = data.get(
                    'pheromone_weight', self.pheromone_weight
                )
                logger.info('Loaded metrics from disk')
        except Exception as e:
            logger.warning(f'Could not load metrics: {e}')

    # =========================================================================
    # Status & Stats
    # =========================================================================

    def get_status(self) -> Dict:
        """Get full stigmergy status for API."""
        field_stats = self.pheromone_field.stats()
        memory_state = self.stigmergic_memory.get_state()

        return {
            'pheromone_weight': self.pheromone_weight,
            'pheromone_field': field_stats,
            'stigmergic_memory': memory_state,
            'metrics': self.metrics,
            'ab_test': self.get_ab_summary(),
            'circuit_breaker_active': self.check_circuit_breaker(),
            'gordon_params': GORDON_PARAMS,
        }

    def get_field_data(self) -> Dict:
        """Get full field data for visualization."""
        return self.pheromone_field.to_dict()

    def get_recent_deposits(self, limit: int = 50) -> List[Dict]:
        """Get recent deposit history."""
        return self._recent_deposits[-limit:]

    def get_hotspots(self, pheromone_type: str = 'success',
                     top_k: int = 10) -> List[Dict]:
        """Get top-N pheromone hotspots."""
        try:
            ptype = PheromoneType(pheromone_type)
        except ValueError:
            ptype = PheromoneType.SUCCESS

        spots = self.pheromone_field.get_hot_spots(ptype, threshold=0.1, top_k=top_k)
        return [
            {'mixture': s[0], 'concentration': s[1]}
            for s in spots
        ]

    def compute_gradient(self, domain: str,
                         pheromone_type: str = 'success') -> Dict[str, float]:
        """Compute pheromone gradient at a domain location."""
        mixture = self._domain_to_mixture(domain)
        try:
            ptype = PheromoneType(pheromone_type)
        except ValueError:
            ptype = PheromoneType.SUCCESS
        return self.pheromone_field.sense_gradient(
            {'domain_mixture': mixture}, ptype
        )

    def set_weight(self, weight: float) -> float:
        """Set pheromone weight (clamped to [0.0, 1.0])."""
        self.pheromone_weight = max(0.0, min(1.0, weight))
        logger.info(f'Pheromone weight set to {self.pheromone_weight}')
        return self.pheromone_weight

    # =========================================================================
    # Helpers
    # =========================================================================

    def _domain_to_mixture(self, domain: str) -> Dict[str, float]:
        """Map domain string to V36 mixture coordinates."""
        return DOMAIN_MIXTURES.get(domain, {'CLD': 0.33, 'D1': 0.33, 'D2': 0.34})

    def _category_to_template(self, category: str) -> Optional[str]:
        """Map hypothesis category to V36 symbolic template."""
        return CATEGORY_TEMPLATES.get(category)

    def _record_deposit(self, deposit_id: str, domain: str,
                        category: str, success: bool, strength: float):
        """Record deposit in recent history ring buffer."""
        entry = {
            'deposit_id': deposit_id,
            'domain': domain,
            'category': category,
            'success': success,
            'strength': round(strength, 3),
            'timestamp': time.time(),
        }
        self._recent_deposits.append(entry)
        if len(self._recent_deposits) > self._max_recent:
            self._recent_deposits = self._recent_deposits[-self._max_recent:]


# Module-level singleton (lazily initialized)
_bridge_instance: Optional[StigmergyBridge] = None


def get_stigmergy_bridge(pheromone_weight: float = 0.3) -> StigmergyBridge:
    """Get or create the singleton StigmergyBridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = StigmergyBridge(pheromone_weight=pheromone_weight)
    return _bridge_instance
