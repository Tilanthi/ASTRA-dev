"""
Uncertainty Planning: Planning Under Belief Uncertainty

This module implements planning under uncertainty using POMDP-lite
approaches - making decisions when the world state is not fully known.

Key Features:
- Belief state representation and updating
- Information-seeking action planning
- Contingency planning for uncertain outcomes
- Risk-aware policy generation
- V40: Question-aware answer commitment decisions

Why This Matters for AGI:
- Real-world problems involve uncertainty
- Enables proactive information gathering
- Supports robust decision-making under partial observability

Date: 2025-12-11
Version: 40.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import heapq


class ActionType(Enum):
    """Types of actions"""
    OBSERVE = "observe"           # Gather information
    INTERVENE = "intervene"       # Change world state
    QUERY = "query"               # Ask for information
    COMMIT = "commit"             # Commit to decision
    WAIT = "wait"                 # Wait for more information


class RiskAttitude(Enum):
    """Risk attitudes for planning"""
    RISK_NEUTRAL = "risk_neutral"
    RISK_AVERSE = "risk_averse"
    RISK_SEEKING = "risk_seeking"


@dataclass
class State:
    """A possible world state"""
    state_id: str
    features: Dict[str, Any]
    is_terminal: bool = False
    reward: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'state_id': self.state_id,
            'features': self.features,
            'is_terminal': self.is_terminal,
            'reward': self.reward
        }


@dataclass
class Action:
    """An action that can be taken"""
    action_id: str
    action_type: ActionType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Costs
    execution_cost: float = 1.0
    time_cost: float = 1.0

    # Information value (for observation actions)
    expected_information_gain: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'action_id': self.action_id,
            'type': self.action_type.value,
            'description': self.description,
            'parameters': self.parameters,
            'cost': self.execution_cost,
            'info_gain': self.expected_information_gain
        }


@dataclass
class Observation:
    """An observation received from the environment"""
    observation_id: str
    content: Dict[str, Any]
    source_action: Optional[str] = None
    reliability: float = 1.0

    def to_dict(self) -> Dict:
        return {
            'observation_id': self.observation_id,
            'content': self.content,
            'source': self.source_action,
            'reliability': self.reliability
        }


@dataclass
class BeliefState:
    """Probability distribution over world states"""
    states: List[State]
    probabilities: np.ndarray
    entropy: float = 0.0

    def __post_init__(self):
        # Normalize probabilities
        self.probabilities = np.array(self.probabilities)
        total = self.probabilities.sum()
        if total > 0:
            self.probabilities = self.probabilities / total
        self.entropy = self._compute_entropy()

    def _compute_entropy(self) -> float:
        """Compute Shannon entropy"""
        p = self.probabilities[self.probabilities > 0]
        return -np.sum(p * np.log2(p)) if len(p) > 0 else 0.0

    def get_most_likely_state(self) -> State:
        """Get most likely state"""
        idx = np.argmax(self.probabilities)
        return self.states[idx]

    def get_state_probability(self, state_id: str) -> float:
        """Get probability of specific state"""
        for s, p in zip(self.states, self.probabilities):
            if s.state_id == state_id:
                return p
        return 0.0

    def update(self, observation: Observation,
               observation_model: 'ObservationModel') -> 'BeliefState':
        """Bayesian belief update given observation"""
        likelihoods = np.array([
            observation_model.likelihood(observation, state)
            for state in self.states
        ])

        # Bayesian update
        posterior = self.probabilities * likelihoods
        total = posterior.sum()
        if total > 0:
            posterior = posterior / total
        else:
            posterior = self.probabilities  # No update if all likelihoods zero

        return BeliefState(self.states, posterior)

    def predict(self, action: Action,
                transition_model: 'TransitionModel') -> 'BeliefState':
        """Predict belief after action"""
        # Compute expected transition
        new_probs = np.zeros(len(self.states))

        for i, s in enumerate(self.states):
            transition_probs = transition_model.transition(s, action)
            for j, s_prime in enumerate(self.states):
                prob = transition_probs.get(s_prime.state_id, 0.0)
                new_probs[j] += self.probabilities[i] * prob

        return BeliefState(self.states, new_probs)

    def to_dict(self) -> Dict:
        return {
            'n_states': len(self.states),
            'entropy': self.entropy,
            'most_likely': self.get_most_likely_state().state_id,
            'max_probability': float(np.max(self.probabilities))
        }


class ObservationModel(ABC):
    """Model P(observation | state)"""

    @abstractmethod
    def likelihood(self, observation: Observation, state: State) -> float:
        """Compute likelihood of observation given state"""
        pass

    @abstractmethod
    def sample(self, state: State) -> Observation:
        """Sample observation from state"""
        pass


class TransitionModel(ABC):
    """Model P(state' | state, action)"""

    @abstractmethod
    def transition(self, state: State, action: Action) -> Dict[str, float]:
        """Return probability distribution over next states"""
        pass


class RewardModel(ABC):
    """Model R(state, action)"""

    @abstractmethod
    def reward(self, state: State, action: Action) -> float:
        """Compute reward for state-action pair"""
        pass


class DefaultObservationModel(ObservationModel):
    """Default observation model with configurable noise"""

    def __init__(self, noise_level: float = 0.1):
        self.noise_level = noise_level

    def likelihood(self, observation: Observation, state: State) -> float:
        """Compute likelihood based on feature matching"""
        matching = 0
        total = 0

        for key, obs_value in observation.content.items():
            if key in state.features:
                state_value = state.features[key]
                if obs_value == state_value:
                    matching += 1
                total += 1

        if total == 0:
            return 0.5

        match_rate = matching / total
        # Add noise
        return (1 - self.noise_level) * match_rate + self.noise_level * 0.5

    def sample(self, state: State) -> Observation:
        """Sample observation from state"""
        content = {}
        for key, value in state.features.items():
            # Add noise
            if np.random.rand() < (1 - self.noise_level):
                content[key] = value
            else:
                content[key] = f"noisy_{value}"

        return Observation(
            observation_id=f"obs_{np.random.randint(10000)}",
            content=content,
            reliability=1 - self.noise_level
        )


class DefaultTransitionModel(TransitionModel):
    """Default transition model"""

    def __init__(self, transitions: Dict[str, Dict[str, float]] = None):
        """
        Args:
            transitions: Dict mapping (state_id, action_id) -> {next_state_id: prob}
        """
        self.transitions = transitions or {}

    def transition(self, state: State, action: Action) -> Dict[str, float]:
        """Return transition probabilities"""
        key = f"{state.state_id}_{action.action_id}"

        if key in self.transitions:
            return self.transitions[key]

        # Default: mostly stay in same state
        return {state.state_id: 0.9}

    def add_transition(self, state_id: str, action_id: str,
                       next_state_probs: Dict[str, float]):
        """Add transition"""
        key = f"{state_id}_{action_id}"
        self.transitions[key] = next_state_probs


class DefaultRewardModel(RewardModel):
    """Default reward model"""

    def __init__(self, goal_states: List[str] = None,
                 goal_reward: float = 10.0,
                 action_costs: Dict[str, float] = None):
        self.goal_states = set(goal_states) if goal_states else set()
        self.goal_reward = goal_reward
        self.action_costs = action_costs or {}

    def reward(self, state: State, action: Action) -> float:
        """Compute reward"""
        r = 0.0

        # Goal reward
        if state.state_id in self.goal_states:
            r += self.goal_reward

        # State reward
        r += state.reward

        # Action cost
        r -= self.action_costs.get(action.action_id, action.execution_cost)

        return r


@dataclass
class Policy:
    """A policy mapping beliefs to actions"""
    policy_type: str  # 'deterministic', 'stochastic'
    belief_action_map: Dict[str, Action]  # Mapping from belief hash to action
    default_action: Optional[Action] = None

    # Performance
    expected_value: float = 0.0
    risk_measure: float = 0.0

    def get_action(self, belief: BeliefState) -> Action:
        """Get action for belief state"""
        # Use most likely state as belief key (simplification)
        belief_key = belief.get_most_likely_state().state_id

        if belief_key in self.belief_action_map:
            return self.belief_action_map[belief_key]

        return self.default_action

    def to_dict(self) -> Dict:
        return {
            'type': self.policy_type,
            'n_mappings': len(self.belief_action_map),
            'expected_value': self.expected_value,
            'risk_measure': self.risk_measure
        }


class POMDPLite:
    """
    Lightweight POMDP solver.

    Uses belief-space value iteration with approximations.
    """

    def __init__(self,
                 observation_model: ObservationModel = None,
                 transition_model: TransitionModel = None,
                 reward_model: RewardModel = None,
                 discount: float = 0.95,
                 horizon: int = 10):
        """
        Args:
            observation_model: P(o|s)
            transition_model: P(s'|s,a)
            reward_model: R(s,a)
            discount: Discount factor
            horizon: Planning horizon
        """
        self.obs_model = observation_model or DefaultObservationModel()
        self.trans_model = transition_model or DefaultTransitionModel()
        self.reward_model = reward_model or DefaultRewardModel()
        self.discount = discount
        self.horizon = horizon

    def solve(self, initial_belief: BeliefState,
              actions: List[Action]) -> Policy:
        """
        Solve POMDP from initial belief.

        Uses point-based value iteration approximation.
        """
        # Sample belief points
        belief_points = self._sample_belief_points(initial_belief, n_points=20)

        # Value function represented at belief points
        values = {i: 0.0 for i in range(len(belief_points))}

        # Value iteration
        for _ in range(self.horizon):
            new_values = {}

            for i, belief in enumerate(belief_points):
                best_value = float('-inf')
                best_action = None

                for action in actions:
                    # Compute Q-value
                    q_value = self._compute_q_value(belief, action, belief_points, values)

                    if q_value > best_value:
                        best_value = q_value
                        best_action = action

                new_values[i] = best_value

            values = new_values

        # Extract policy
        policy_map = {}
        for i, belief in enumerate(belief_points):
            best_action = None
            best_value = float('-inf')

            for action in actions:
                q_value = self._compute_q_value(belief, action, belief_points, values)
                if q_value > best_value:
                    best_value = q_value
                    best_action = action

            policy_map[belief.get_most_likely_state().state_id] = best_action

        return Policy(
            policy_type='deterministic',
            belief_action_map=policy_map,
            default_action=actions[0] if actions else None,
            expected_value=values.get(0, 0.0)
        )

    def _sample_belief_points(self, initial_belief: BeliefState,
                               n_points: int) -> List[BeliefState]:
        """Sample belief points for approximation"""
        points = [initial_belief]

        # Add perturbations
        for _ in range(n_points - 1):
            noise = np.random.dirichlet(np.ones(len(initial_belief.states)))
            perturbed = initial_belief.probabilities * 0.7 + noise * 0.3
            points.append(BeliefState(initial_belief.states, perturbed))

        return points

    def _compute_q_value(self, belief: BeliefState, action: Action,
                         belief_points: List[BeliefState],
                         values: Dict[int, float]) -> float:
        """Compute Q(b, a)"""
        # Immediate reward
        immediate = sum(
            belief.probabilities[i] * self.reward_model.reward(state, action)
            for i, state in enumerate(belief.states)
        )

        # Future value (simplified)
        next_belief = belief.predict(action, self.trans_model)

        # Find closest belief point
        closest_idx = self._find_closest_belief(next_belief, belief_points)
        future_value = values.get(closest_idx, 0.0)

        return immediate + self.discount * future_value

    def _find_closest_belief(self, belief: BeliefState,
                              belief_points: List[BeliefState]) -> int:
        """Find index of closest belief point"""
        min_dist = float('inf')
        min_idx = 0

        for i, point in enumerate(belief_points):
            dist = np.sum(np.abs(belief.probabilities - point.probabilities))
            if dist < min_dist:
                min_dist = dist
                min_idx = i

        return min_idx


class InformationSeekingPlanner:
    """Plan to reduce uncertainty through information gathering"""

    def __init__(self, base_planner: POMDPLite = None):
        self.base_planner = base_planner or POMDPLite()

    def plan_information_seeking(self, belief: BeliefState,
                                  observation_actions: List[Action],
                                  info_value: float = 1.0) -> Action:
        """
        Plan to gather information that maximally reduces uncertainty.

        Args:
            belief: Current belief state
            observation_actions: Available observation actions
            info_value: Weight on information gain vs cost

        Returns:
            Best observation action
        """
        best_action = None
        best_value = float('-inf')

        for action in observation_actions:
            if action.action_type != ActionType.OBSERVE:
                continue

            # Compute expected information gain
            eig = self._expected_information_gain(belief, action)

            # Compute value = info_gain - cost
            value = info_value * eig - action.execution_cost

            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def _expected_information_gain(self, belief: BeliefState,
                                    action: Action) -> float:
        """Compute expected information gain from observation action"""
        prior_entropy = belief.entropy

        # Sample possible observations and compute expected posterior entropy
        n_samples = 20
        expected_posterior_entropy = 0.0

        for _ in range(n_samples):
            # Sample a state
            state_idx = np.random.choice(len(belief.states), p=belief.probabilities)
            state = belief.states[state_idx]

            # Sample observation from that state
            obs = self.base_planner.obs_model.sample(state)

            # Compute posterior
            posterior = belief.update(obs, self.base_planner.obs_model)
            expected_posterior_entropy += posterior.entropy / n_samples

        return prior_entropy - expected_posterior_entropy


class ContingencyPlanner:
    """Plan with contingencies for uncertain outcomes"""

    def __init__(self):
        self.contingency_threshold = 0.2  # Create contingency if prob > this

    def plan_with_contingencies(self, belief: BeliefState,
                                 actions: List[Action],
                                 goal_checker: Callable[[State], bool]) -> Dict[str, Any]:
        """
        Create plan with contingency branches.

        Returns plan tree with branches for different outcomes.
        """
        plan = {
            'primary_action': None,
            'contingencies': [],
            'expected_value': 0.0
        }

        # Evaluate primary actions
        best_action = None
        best_value = float('-inf')

        for action in actions:
            value = self._evaluate_action(belief, action, goal_checker)
            if value > best_value:
                best_value = value
                best_action = action

        plan['primary_action'] = best_action
        plan['expected_value'] = best_value

        # Create contingencies for uncertain outcomes
        if best_action is not None:
            contingencies = self._create_contingencies(
                belief, best_action, actions, goal_checker
            )
            plan['contingencies'] = contingencies

        return plan

    def _evaluate_action(self, belief: BeliefState, action: Action,
                          goal_checker: Callable[[State], bool]) -> float:
        """Evaluate action under belief"""
        value = 0.0

        for i, state in enumerate(belief.states):
            prob = belief.probabilities[i]

            # Check if action leads to goal
            if goal_checker(state):
                value += prob * 10.0

            # Subtract cost
            value -= prob * action.execution_cost

        return value

    def _create_contingencies(self, belief: BeliefState, primary_action: Action,
                               all_actions: List[Action],
                               goal_checker: Callable[[State], bool]) -> List[Dict]:
        """Create contingency plans for different outcomes"""
        contingencies = []

        # For each possible state with significant probability
        for i, state in enumerate(belief.states):
            prob = belief.probabilities[i]

            if prob > self.contingency_threshold:
                # Create contingency for this state
                contingency = {
                    'condition': f"state = {state.state_id}",
                    'probability': prob,
                    'recommended_action': primary_action
                }

                # Check if different action is better for this state
                best_action = primary_action
                best_value = self._state_action_value(state, primary_action, goal_checker)

                for action in all_actions:
                    value = self._state_action_value(state, action, goal_checker)
                    if value > best_value:
                        best_value = value
                        best_action = action

                contingency['recommended_action'] = best_action
                contingency['expected_value'] = best_value

                contingencies.append(contingency)

        return contingencies

    def _state_action_value(self, state: State, action: Action,
                            goal_checker: Callable[[State], bool]) -> float:
        """Compute value of action in specific state"""
        value = -action.execution_cost

        if goal_checker(state):
            value += 10.0

        return value


class UncertaintyPlanner:
    """
    Main Uncertainty Planning system.

    Provides unified interface for planning under belief uncertainty.
    """

    def __init__(self,
                 observation_model: ObservationModel = None,
                 transition_model: TransitionModel = None,
                 reward_model: RewardModel = None,
                 risk_attitude: RiskAttitude = RiskAttitude.RISK_NEUTRAL):
        """
        Args:
            observation_model: P(o|s)
            transition_model: P(s'|s,a)
            reward_model: R(s,a)
            risk_attitude: Risk attitude for planning
        """
        self.obs_model = observation_model or DefaultObservationModel()
        self.trans_model = transition_model or DefaultTransitionModel()
        self.reward_model = reward_model or DefaultRewardModel()
        self.risk_attitude = risk_attitude

        # Planners
        self.pomdp = POMDPLite(self.obs_model, self.trans_model, self.reward_model)
        self.info_seeker = InformationSeekingPlanner(self.pomdp)
        self.contingency = ContingencyPlanner()

        # State
        self.current_belief: Optional[BeliefState] = None
        self.action_history: List[Tuple[Action, Observation]] = []

    def build_belief_state(self, states: List[State],
                           prior: np.ndarray = None) -> BeliefState:
        """
        Build initial belief state.

        Args:
            states: Possible states
            prior: Prior probabilities (uniform if not provided)

        Returns:
            BeliefState
        """
        if prior is None:
            prior = np.ones(len(states)) / len(states)

        belief = BeliefState(states, prior)
        self.current_belief = belief
        return belief

    def plan_with_uncertainty(self, actions: List[Action],
                               goal: Callable[[State], bool] = None) -> Dict[str, Any]:
        """
        Plan considering belief uncertainty.

        Args:
            actions: Available actions
            goal: Goal checking function

        Returns:
            Plan with policy, contingencies, and information-seeking recommendations
        """
        if self.current_belief is None:
            raise ValueError("Must build belief state first")

        result = {
            'policy': None,
            'contingencies': None,
            'information_seeking': None,
            'should_gather_info': False,
            'confidence': 0.0
        }

        # Compute policy
        result['policy'] = self.pomdp.solve(self.current_belief, actions)

        # Create contingency plan
        if goal:
            result['contingencies'] = self.contingency.plan_with_contingencies(
                self.current_belief, actions, goal
            )

        # Check if we should gather more information
        observation_actions = [a for a in actions if a.action_type == ActionType.OBSERVE]
        if observation_actions and self.current_belief.entropy > 0.5:
            best_info_action = self.info_seeker.plan_information_seeking(
                self.current_belief, observation_actions
            )
            result['information_seeking'] = best_info_action
            result['should_gather_info'] = best_info_action is not None

        # Confidence based on belief entropy
        result['confidence'] = 1.0 - min(1.0, self.current_belief.entropy / np.log2(len(self.current_belief.states)))

        return result

    def update_belief(self, observation: Observation) -> BeliefState:
        """Update belief state with new observation"""
        if self.current_belief is None:
            raise ValueError("No current belief to update")

        self.current_belief = self.current_belief.update(observation, self.obs_model)
        return self.current_belief

    def predict_belief_after_action(self, action: Action) -> BeliefState:
        """Predict belief state after taking action"""
        if self.current_belief is None:
            raise ValueError("No current belief")

        return self.current_belief.predict(action, self.trans_model)

    def execute_action(self, action: Action, observation: Observation = None):
        """Execute action and update state"""
        if observation:
            self.update_belief(observation)

        self.action_history.append((action, observation))

    def should_stop_planning(self, confidence_threshold: float = 0.8) -> bool:
        """Determine if planning can stop"""
        if self.current_belief is None:
            return False

        # Stop if confident enough
        max_prob = np.max(self.current_belief.probabilities)
        return max_prob > confidence_threshold

    def replan_on_surprise(self, observation: Observation,
                            expected_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Replan if observation is surprising.

        Args:
            observation: New observation
            expected_threshold: Threshold for surprise

        Returns:
            Replan result with surprise measure and new plan
        """
        if self.current_belief is None:
            return {'error': 'No current belief'}

        # Compute surprise
        surprise = self._compute_surprise(observation)

        result = {
            'surprise': surprise,
            'is_surprising': surprise > expected_threshold,
            'replan_needed': False,
            'new_plan': None
        }

        if result['is_surprising']:
            result['replan_needed'] = True
            # Update belief and replan
            self.update_belief(observation)
            # Replan would need actions - return flag for now
            result['belief_updated'] = True

        return result

    def _compute_surprise(self, observation: Observation) -> float:
        """Compute surprise of observation given current belief"""
        # P(o) = sum_s P(o|s) P(s)
        p_o = sum(
            self.obs_model.likelihood(observation, state) * prob
            for state, prob in zip(self.current_belief.states, self.current_belief.probabilities)
        )

        # Surprise = -log(P(o))
        if p_o < 1e-10:
            return 10.0  # Very surprising

        return -np.log(p_o)

    def get_stats(self) -> Dict[str, Any]:
        """Get planner statistics"""
        return {
            'has_belief': self.current_belief is not None,
            'belief_entropy': self.current_belief.entropy if self.current_belief else None,
            'n_states': len(self.current_belief.states) if self.current_belief else 0,
            'n_actions_taken': len(self.action_history),
            'risk_attitude': self.risk_attitude.value
        }


# =============================================================================
# V40: QUESTION-AWARE ANSWER PLANNER
# =============================================================================

class QuestionAnswerPlanner:
    """
    V40: Plan for question-answering with confidence-aware decisions.

    Extends uncertainty planning to handle multiple-choice and
    exact-match question answering scenarios.
    """

    def __init__(self, uncertainty_planner: Optional[UncertaintyPlanner] = None):
        self.planner = uncertainty_planner or UncertaintyPlanner()
        self.answer_history: List[Dict] = []

        # Configurable thresholds
        self.high_confidence_threshold = 0.8
        self.medium_confidence_threshold = 0.5
        self.low_confidence_threshold = 0.3

    def plan_for_multiple_choice(self, question: str,
                                  options: List[str],
                                  option_confidences: List[float]
                                  ) -> Dict[str, Any]:
        """
        Plan answer strategy for multiple choice question.

        Args:
            question: The question text
            options: List of answer options
            option_confidences: Confidence in each option

        Returns:
            Dict with decision and rationale
        """
        # Build belief state over options
        states = [State(opt, {'selected': opt}, reward=0) for opt in options]

        # Normalize confidences to probabilities
        total_conf = sum(option_confidences) + 1e-10
        probs = np.array(option_confidences) / total_conf

        belief = BeliefState(
            states=states,
            probabilities=probs
        )

        # Get best option
        best_idx = np.argmax(probs)
        best_option = options[best_idx]
        best_confidence = probs[best_idx]

        # Compute entropy and margin
        entropy = belief.entropy
        sorted_probs = sorted(probs, reverse=True)
        margin = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else sorted_probs[0]

        # Decision logic
        decision = self._make_decision(best_confidence, entropy, margin)

        return {
            'best_option': best_option,
            'confidence': float(best_confidence),
            'entropy': float(entropy),
            'margin': float(margin),
            'decision': decision['action'],
            'rationale': decision['rationale'],
            'should_commit': decision['should_commit'],
            'alternative_options': [
                {'option': opt, 'confidence': float(conf)}
                for opt, conf in sorted(zip(options, probs), key=lambda x: -x[1])[:3]
            ]
        }

    def plan_for_exact_match(self, question: str,
                             answer_candidates: List[str],
                             candidate_confidences: List[float]
                             ) -> Dict[str, Any]:
        """
        Plan answer strategy for exact match question.

        Args:
            question: The question text
            answer_candidates: Candidate answers generated
            candidate_confidences: Confidence in each candidate

        Returns:
            Dict with decision and rationale
        """
        if not answer_candidates:
            return {
                'best_answer': None,
                'confidence': 0.0,
                'decision': 'give_up',
                'rationale': 'No answer candidates generated',
                'should_commit': False
            }

        # Normalize and find best
        total_conf = sum(candidate_confidences) + 1e-10
        probs = np.array(candidate_confidences) / total_conf

        best_idx = np.argmax(probs)
        best_answer = answer_candidates[best_idx]
        best_confidence = probs[best_idx]

        # For exact match, require higher confidence
        adjusted_threshold = self.high_confidence_threshold + 0.1

        if best_confidence >= adjusted_threshold:
            decision = {
                'action': 'commit',
                'rationale': f'High confidence ({best_confidence:.2f}) in exact answer',
                'should_commit': True
            }
        elif best_confidence >= self.medium_confidence_threshold:
            decision = {
                'action': 'commit_with_caution',
                'rationale': f'Moderate confidence ({best_confidence:.2f}), committing as best available',
                'should_commit': True
            }
        else:
            decision = {
                'action': 'low_confidence_guess',
                'rationale': f'Low confidence ({best_confidence:.2f}), answer may be incorrect',
                'should_commit': True  # Still commit, but flag uncertainty
            }

        return {
            'best_answer': best_answer,
            'confidence': float(best_confidence),
            'decision': decision['action'],
            'rationale': decision['rationale'],
            'should_commit': decision['should_commit'],
            'alternative_candidates': answer_candidates[:5]
        }

    def _make_decision(self, confidence: float, entropy: float,
                       margin: float) -> Dict[str, Any]:
        """Make decision based on uncertainty metrics"""
        # High confidence, low entropy - commit
        if confidence >= self.high_confidence_threshold and entropy < 1.0:
            return {
                'action': 'commit',
                'rationale': f'High confidence ({confidence:.2f}) with low uncertainty',
                'should_commit': True
            }

        # Large margin between top options - commit
        if margin > 0.3:
            return {
                'action': 'commit',
                'rationale': f'Clear winner with margin {margin:.2f}',
                'should_commit': True
            }

        # Medium confidence - might want more info
        if confidence >= self.medium_confidence_threshold:
            return {
                'action': 'commit_with_verification',
                'rationale': f'Moderate confidence ({confidence:.2f}), verification recommended',
                'should_commit': True
            }

        # Low confidence, high entropy - uncertain
        if confidence < self.low_confidence_threshold:
            return {
                'action': 'strategic_guess',
                'rationale': f'Low confidence ({confidence:.2f}), making strategic guess',
                'should_commit': True  # Still have to answer
            }

        # Default - commit with caution
        return {
            'action': 'commit_with_caution',
            'rationale': f'Committing with confidence {confidence:.2f}',
            'should_commit': True
        }

    def should_seek_more_info(self, current_confidence: float,
                              time_remaining: Optional[float] = None,
                              info_cost: float = 0.1) -> Dict[str, Any]:
        """
        Decide whether to seek more information before committing.

        Args:
            current_confidence: Current confidence in best answer
            time_remaining: Time available (if applicable)
            info_cost: Cost of seeking more information

        Returns:
            Dict with decision and expected value
        """
        # Expected value of committing now
        ev_commit = current_confidence

        # Expected value of seeking info (rough estimate)
        # Assume info might increase confidence by 10-20%
        expected_improvement = 0.15
        ev_seek = (current_confidence + expected_improvement) * (1 - info_cost)

        seek_info = ev_seek > ev_commit and current_confidence < self.high_confidence_threshold

        # Override if no time
        if time_remaining is not None and time_remaining < 1.0:
            seek_info = False

        return {
            'should_seek_info': seek_info,
            'ev_commit_now': ev_commit,
            'ev_seek_info': ev_seek,
            'rationale': (
                'Seeking info may improve answer' if seek_info
                else 'Better to commit now'
            )
        }

    def multi_attempt_strategy(self, attempts_remaining: int,
                               current_confidence: float,
                               option_distribution: List[float]
                               ) -> Dict[str, Any]:
        """
        Strategy for when multiple attempts are allowed.

        Args:
            attempts_remaining: Number of attempts left
            current_confidence: Confidence in best answer
            option_distribution: Probability distribution over options

        Returns:
            Strategy recommendation
        """
        sorted_dist = sorted(enumerate(option_distribution),
                            key=lambda x: x[1], reverse=True)

        if attempts_remaining == 1:
            # Last attempt - go with best option
            return {
                'strategy': 'commit_best',
                'recommended_option': sorted_dist[0][0],
                'rationale': 'Last attempt - committing to highest probability option'
            }

        elif attempts_remaining == 2:
            # Two attempts - go with best, have backup
            return {
                'strategy': 'best_then_second',
                'recommended_option': sorted_dist[0][0],
                'backup_option': sorted_dist[1][0] if len(sorted_dist) > 1 else None,
                'rationale': 'Try best option first, second-best as backup'
            }

        else:
            # Multiple attempts - can explore
            if current_confidence > self.high_confidence_threshold:
                return {
                    'strategy': 'commit_best',
                    'recommended_option': sorted_dist[0][0],
                    'rationale': 'High confidence - commit to best option'
                }
            else:
                # Could consider more exploratory approach
                return {
                    'strategy': 'explore_then_exploit',
                    'recommended_option': sorted_dist[0][0],
                    'explore_options': [idx for idx, _ in sorted_dist[1:3]],
                    'rationale': 'Multiple attempts available - can verify top choices'
                }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'UncertaintyPlanner',
    'BeliefState',
    'State',
    'Action',
    'ActionType',
    'Observation',
    'Policy',
    'POMDPLite',
    'ObservationModel',
    'TransitionModel',
    'RewardModel',
    'DefaultObservationModel',
    'DefaultTransitionModel',
    'DefaultRewardModel',
    'InformationSeekingPlanner',
    'ContingencyPlanner',
    'RiskAttitude',
    'QuestionAnswerPlanner'  # V40
]

# =============================================================================
# MISSING CLASSES FOR COMPATIBILITY
# =============================================================================

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class PlanStatus(Enum):
    """Status of a plan"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PlanNode:
    """A node in a plan"""
    node_id: str
    action: Action
    parent_node_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    actual_outcome: Optional[Dict[str, Any]] = None


@dataclass
class Plan:
    """A plan with sequence of actions"""
    plan_id: str
    nodes: List[PlanNode]
    root_node_id: str
    status: PlanStatus = PlanStatus.PENDING
    expected_value: float = 0.0
    actual_value: float = 0.0

    def get_root_node(self) -> Optional[PlanNode]:
        """Get root node of plan"""
        for node in self.nodes:
            if node.node_id == self.root_node_id:
                return node
        return None


class ValueEstimator:
    """Base class for value estimation"""

    def estimate(self, state: State, action: Action) -> float:
        """Estimate value of action in state"""
        return 0.0


class InformationValueEstimator(InformationSeekingPlanner):
    """Estimate information value of observations"""
    pass


class GoalBasedEstimator(ValueEstimator):
    """Estimate value based on goal proximity"""

    def __init__(self, goal_state: State):
        self.goal_state = goal_state

    def estimate(self, state: State, action: Action) -> float:
        """Estimate value based on distance to goal"""
        # Simplified: inverse of distance
        return 1.0 / (1.0 + self._distance_to_goal(state))

    def _distance_to_goal(self, state: State) -> float:
        """Compute distance to goal"""
        # Placeholder - actual implementation depends on state representation
        return 0.5


# Aliases for compatibility
BayesianPlanner = POMDPLite

