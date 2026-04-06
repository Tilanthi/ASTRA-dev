"""
Swarm Agents for ASTRA Discovery Engine

Five biologically-inspired agent types that operate on the pheromone field:

1. ExplorerAgent  — Seeks low-EXPLORATION regions, deposits EXPLORATION
2. ExploiterAgent — Follows SUCCESS trails, deposits SUCCESS
3. FalsifierAgent — Tests high-C_K theories, deposits FAILURE
4. AnalogistAgent — Cross-domain pattern matching, deposits ANALOGY
5. ScoutAgent     — Random walk with NOVELTY sensing

Each agent implements Gordon's contact rate protocol (2-10 contacts/min).
"""
import time
import random
import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from .stigmergy_bridge import (
    StigmergyBridge, DOMAIN_MIXTURES, CATEGORY_TEMPLATES,
    PheromoneType, DigitalPheromoneField,
    PheromoneUpdater, CuriosityValueCalculator, GORDON_PARAMS,
)

logger = logging.getLogger('astra.swarm')

# All domains the agents can operate in
ALL_DOMAINS = ['Astrophysics', 'Economics', 'Climate', 'Epidemiology', 'Cross-Domain']


@dataclass
class AgentAction:
    """Result of an agent's decide() step."""
    action_type: str       # 'explore', 'exploit', 'test', 'analogize', 'scout'
    target_domain: str     # Domain to act in
    target_category: str   # Category within domain
    confidence: float      # How confident in this action (0-1)
    reasoning: str         # Why this action was chosen
    metadata: Dict = field(default_factory=dict)


class SwarmAgentBase:
    """
    Base class for all swarm agents.

    Implements Gordon's contact rate protocol: each agent interacts
    at 2-10 contacts/minute, with task switching at 15% probability.
    """

    agent_type: str = 'base'

    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f'{self.agent_type}_{id(self):08x}'
        self.contacts = 0
        self.last_contact_time = time.time()
        self.contact_rate = GORDON_PARAMS['contact_rate_min']  # Start conservative
        self.actions_taken = 0
        self.successes = 0
        self._updater = PheromoneUpdater()

    def sense(self, bridge: StigmergyBridge, domain: str) -> Dict[str, float]:
        """
        Read pheromone concentrations at a domain location.

        Returns dict of pheromone_type -> concentration.
        """
        mixture = bridge._domain_to_mixture(domain)
        return bridge.pheromone_field.sense({'domain_mixture': mixture})

    def decide(self, bridge: StigmergyBridge,
               available_domains: List[str] = None) -> AgentAction:
        """
        Choose action based on pheromone landscape. Override in subclasses.
        """
        raise NotImplementedError

    def deposit(self, bridge: StigmergyBridge, action: AgentAction,
                result: Dict) -> str:
        """
        Leave pheromone trail based on outcome. Override in subclasses.
        """
        raise NotImplementedError

    def should_act(self) -> bool:
        """
        Gordon's contact rate protocol: only act if enough time has passed.
        """
        now = time.time()
        elapsed = now - self.last_contact_time
        # Contact rate is contacts per second
        min_interval = 1.0 / max(self.contact_rate, 0.001)

        if elapsed >= min_interval:
            self.last_contact_time = now
            self.contacts += 1

            # Task switching: 15% chance to skip (switch to idle)
            if random.random() < GORDON_PARAMS['switch_probability']:
                return False
            return True
        return False

    def adjust_contact_rate(self, success: bool):
        """
        Adjust contact rate based on outcome (anternet principle).
        More success → higher rate. Less → lower.
        """
        if success:
            self.contact_rate = min(
                self.contact_rate * 1.1,
                GORDON_PARAMS['contact_rate_max']
            )
        else:
            self.contact_rate = max(
                self.contact_rate * 0.95,
                GORDON_PARAMS['contact_rate_min']
            )

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'contacts': self.contacts,
            'contact_rate': round(self.contact_rate, 4),
            'actions_taken': self.actions_taken,
            'successes': self.successes,
            'success_rate': self.successes / max(self.actions_taken, 1),
        }


class ExplorerAgent(SwarmAgentBase):
    """
    Seeks low-EXPLORATION regions to maximize coverage.
    Deposits EXPLORATION pheromone after visiting.
    """
    agent_type = 'explorer'

    def decide(self, bridge: StigmergyBridge,
               available_domains: List[str] = None) -> AgentAction:
        domains = available_domains or ALL_DOMAINS

        # Sense exploration levels across domains
        exploration_levels = {}
        for domain in domains:
            concs = self.sense(bridge, domain)
            exploration_levels[domain] = concs.get('exploration', 0)

        # Pick domain with LOWEST exploration (most unexplored)
        target = min(exploration_levels, key=exploration_levels.get)
        level = exploration_levels[target]

        return AgentAction(
            action_type='explore',
            target_domain=target,
            target_category='general',
            confidence=max(0.1, 1.0 - level / 5.0),
            reasoning=f'Least explored domain (exploration={level:.2f})',
        )

    def deposit(self, bridge: StigmergyBridge, action: AgentAction,
                result: Dict) -> str:
        """Deposit EXPLORATION pheromone at visited location."""
        mixture = bridge._domain_to_mixture(action.target_domain)
        deposit_id = bridge.pheromone_field.deposit_exploration(
            domain_mixture=mixture, strength=1.0
        )
        self.actions_taken += 1
        bridge.metrics['total_deposits'] += 1
        return deposit_id


class ExploiterAgent(SwarmAgentBase):
    """
    Follows SUCCESS pheromone trails — exploits known productive regions.
    Deposits SUCCESS when confirmation is achieved.
    """
    agent_type = 'exploiter'

    def decide(self, bridge: StigmergyBridge,
               available_domains: List[str] = None) -> AgentAction:
        domains = available_domains or ALL_DOMAINS

        # Sense success levels across domains
        success_levels = {}
        for domain in domains:
            concs = self.sense(bridge, domain)
            success_levels[domain] = concs.get('success', 0)

        # Pick domain with HIGHEST success (most productive)
        target = max(success_levels, key=success_levels.get)
        level = success_levels[target]

        return AgentAction(
            action_type='exploit',
            target_domain=target,
            target_category='correlation',
            confidence=min(level / 3.0, 1.0),
            reasoning=f'Highest success domain (success={level:.2f})',
        )

    def deposit(self, bridge: StigmergyBridge, action: AgentAction,
                result: Dict) -> str:
        """Deposit SUCCESS pheromone if test passed."""
        mixture = bridge._domain_to_mixture(action.target_domain)
        passed = result.get('passed', False)

        if passed:
            deposit_id = bridge.pheromone_field.deposit_success(
                domain_mixture=mixture,
                strength=2.0 * (1 + result.get('effect_size', 0)),
                hypothesis_id=result.get('hypothesis_id', ''),
            )
            self.successes += 1
        else:
            deposit_id = bridge.pheromone_field.deposit_exploration(
                domain_mixture=mixture, strength=0.3
            )

        self.actions_taken += 1
        self.adjust_contact_rate(passed)
        bridge.metrics['total_deposits'] += 1
        return deposit_id


class FalsifierAgent(SwarmAgentBase):
    """
    Tests well-established theories (high C_K) to find weaknesses.
    Deposits FAILURE pheromone when a theory fails.
    """
    agent_type = 'falsifier'

    def decide(self, bridge: StigmergyBridge,
               available_domains: List[str] = None) -> AgentAction:
        domains = available_domains or ALL_DOMAINS

        # Use stigmergic memory to find high-C_K (well-established) locations
        recommendations = bridge.stigmergic_memory.get_swarm_recommendations(
            current_location=domains[0].lower(),
            agent_type='falsifier',
        )

        if recommendations and recommendations[0].get('target'):
            target_loc = recommendations[0]['target']
            target_domain = target_loc.split('_')[0].title()
            if target_domain not in domains:
                target_domain = domains[0]
            confidence = recommendations[0].get('confidence', 0.5)
            reason = recommendations[0].get('reason', 'high C_K theory')
        else:
            # Fallback: pick domain with highest success (most to falsify)
            success_levels = {}
            for domain in domains:
                concs = self.sense(bridge, domain)
                success_levels[domain] = concs.get('success', 0)
            target_domain = max(success_levels, key=success_levels.get)
            confidence = 0.5
            reason = 'targeting highest-success domain for falsification'

        return AgentAction(
            action_type='test',
            target_domain=target_domain,
            target_category='anomaly',
            confidence=confidence,
            reasoning=reason,
        )

    def deposit(self, bridge: StigmergyBridge, action: AgentAction,
                result: Dict) -> str:
        """Deposit FAILURE pheromone when theory is falsified."""
        mixture = bridge._domain_to_mixture(action.target_domain)
        falsified = result.get('falsified', False)

        if falsified:
            deposit_id = bridge.pheromone_field.deposit_failure(
                domain_mixture=mixture,
                constraint_id=result.get('hypothesis_id', ''),
                severity='high',
                strength=2.5,
            )
            self.successes += 1  # "success" for a falsifier means finding a flaw
        else:
            # Theory survived: reinforce it
            deposit_id = bridge.pheromone_field.deposit_success(
                domain_mixture=mixture, strength=0.5,
            )

        self.actions_taken += 1
        self.adjust_contact_rate(falsified)
        bridge.metrics['total_deposits'] += 1
        return deposit_id


class AnalogistAgent(SwarmAgentBase):
    """
    Cross-domain pattern matching — finds structural similarities
    between different domains and deposits ANALOGY pheromone.
    """
    agent_type = 'analogist'

    def decide(self, bridge: StigmergyBridge,
               available_domains: List[str] = None) -> AgentAction:
        domains = available_domains or ALL_DOMAINS

        # Find pairs of domains with similar pheromone profiles
        profiles = {}
        for domain in domains:
            concs = self.sense(bridge, domain)
            profiles[domain] = concs

        # Find most similar pair (excluding self-comparisons)
        best_sim = -1
        best_pair = (domains[0], domains[1] if len(domains) > 1 else domains[0])

        for i, d1 in enumerate(domains):
            for d2 in domains[i + 1:]:
                p1 = profiles[d1]
                p2 = profiles[d2]
                # Cosine similarity of pheromone profiles
                keys = set(p1.keys()) | set(p2.keys())
                dot = sum(p1.get(k, 0) * p2.get(k, 0) for k in keys)
                mag1 = math.sqrt(sum(v ** 2 for v in p1.values())) or 1
                mag2 = math.sqrt(sum(v ** 2 for v in p2.values())) or 1
                sim = dot / (mag1 * mag2)
                if sim > best_sim:
                    best_sim = sim
                    best_pair = (d1, d2)

        return AgentAction(
            action_type='analogize',
            target_domain=best_pair[0],
            target_category='interaction',
            confidence=best_sim,
            reasoning=f'Analog pair: {best_pair[0]}<->{best_pair[1]} sim={best_sim:.3f}',
            metadata={'domain_b': best_pair[1], 'similarity': best_sim},
        )

    def deposit(self, bridge: StigmergyBridge, action: AgentAction,
                result: Dict) -> str:
        """Deposit ANALOGY pheromone for cross-domain connection."""
        domain_a = action.target_domain
        domain_b = action.metadata.get('domain_b', 'general')
        similarity = action.metadata.get('similarity', 0.5)

        bridge.on_cross_domain_connection(
            domain_a=domain_a,
            domain_b=domain_b,
            role_a=result.get('role_a', 'pattern'),
            role_b=result.get('role_b', 'pattern'),
            similarity=similarity,
        )
        self.actions_taken += 1
        self.successes += 1 if similarity > 0.5 else 0
        return f'analogy_{domain_a}_{domain_b}'


class ScoutAgent(SwarmAgentBase):
    """
    Random walk with NOVELTY sensing — finds unexpected signals.
    Deposits NOVELTY when unusual patterns are detected.
    """
    agent_type = 'scout'

    def decide(self, bridge: StigmergyBridge,
               available_domains: List[str] = None) -> AgentAction:
        domains = available_domains or ALL_DOMAINS

        # Random walk — pick a domain randomly
        target = random.choice(domains)
        concs = self.sense(bridge, target)
        novelty_level = concs.get('novelty', 0)

        return AgentAction(
            action_type='scout',
            target_domain=target,
            target_category='unknown',
            confidence=0.5,
            reasoning=f'Random walk to {target} (novelty={novelty_level:.2f})',
            metadata={'novelty_level': novelty_level},
        )

    def deposit(self, bridge: StigmergyBridge, action: AgentAction,
                result: Dict) -> str:
        """Deposit NOVELTY pheromone if something unexpected is found."""
        mixture = bridge._domain_to_mixture(action.target_domain)
        is_novel = result.get('is_novel', False)

        if is_novel:
            deposit_id = bridge.pheromone_field.deposit_novelty(
                observation_family=action.target_category,
                domain_mixture=mixture,
                strength=3.0 * result.get('significance', 1.0),
            )
            self.successes += 1
        else:
            deposit_id = bridge.pheromone_field.deposit_exploration(
                domain_mixture=mixture, strength=0.2
            )

        self.actions_taken += 1
        bridge.metrics['total_deposits'] += 1
        return deposit_id


class SwarmCoordinator:
    """
    Coordinates the 5 swarm agent types during engine cycles.

    Called from the DiscoveryEngine at each OODA phase:
    - ORIENT: ScoutAgent scans for novelty
    - SELECT: ExploiterAgent + ExplorerAgent rank candidates
    - INVESTIGATE: FalsifierAgent validates
    - UPDATE: All agents deposit pheromones, AnalogistAgent finds links
    """

    def __init__(self, bridge: StigmergyBridge):
        self.bridge = bridge
        self.explorer = ExplorerAgent()
        self.exploiter = ExploiterAgent()
        self.falsifier = FalsifierAgent()
        self.analogist = AnalogistAgent()
        self.scout = ScoutAgent()
        self._agents = [
            self.explorer, self.exploiter, self.falsifier,
            self.analogist, self.scout,
        ]

    def run_orient_phase(self) -> Optional[AgentAction]:
        """ScoutAgent scans for novelty during ORIENT."""
        if not self.scout.should_act():
            return None
        action = self.scout.decide(self.bridge)
        return action

    def run_select_phase(self, candidates: List[Dict],
                         scores: List[float]) -> List[Tuple[Dict, float]]:
        """
        ExploiterAgent and ExplorerAgent influence hypothesis ranking.
        Returns re-ranked candidates.
        """
        # Get exploration direction
        direction = self.bridge.get_exploration_direction(
            candidates[0].get('domain', 'Astrophysics') if candidates else 'Astrophysics'
        )

        # Use bridge's ranking (combines pheromone signals)
        return self.bridge.rank_hypotheses(candidates, scores)

    def run_investigate_phase(self, hypothesis: Dict) -> Optional[AgentAction]:
        """FalsifierAgent targets hypothesis for testing."""
        if not self.falsifier.should_act():
            return None
        action = self.falsifier.decide(self.bridge)
        return action

    def run_update_phase(self, results: List[Dict]):
        """All agents deposit pheromones based on cycle results."""
        for result in results:
            domain = result.get('domain', 'general')

            # Explorer always deposits exploration
            if self.explorer.should_act():
                action = self.explorer.decide(self.bridge)
                self.explorer.deposit(self.bridge, action, result)

            # Exploiter deposits on success
            if self.exploiter.should_act():
                action = self.exploiter.decide(self.bridge)
                self.exploiter.deposit(self.bridge, action, result)

            # Analogist looks for cross-domain connections
            if self.analogist.should_act() and len(results) > 1:
                action = self.analogist.decide(self.bridge)
                self.analogist.deposit(self.bridge, action, result)

    def get_all_status(self) -> List[Dict]:
        """Get status of all swarm agents."""
        return [agent.get_status() for agent in self._agents]

    def get_swarm_summary(self) -> Dict:
        """Get swarm summary statistics."""
        statuses = self.get_all_status()
        total_actions = sum(s['actions_taken'] for s in statuses)
        total_successes = sum(s['successes'] for s in statuses)
        return {
            'agent_count': len(self._agents),
            'agents': statuses,
            'total_actions': total_actions,
            'total_successes': total_successes,
            'overall_success_rate': total_successes / max(total_actions, 1),
            'gordon_params': GORDON_PARAMS,
        }
