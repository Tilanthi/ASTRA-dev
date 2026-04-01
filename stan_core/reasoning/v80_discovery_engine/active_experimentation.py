"""
Active Experimentation Engine Module

Implements autonomous hypothesis generation and testing:
- Optimal experimental design
- Bayesian active learning
- Autonomous observation planning
- Hypothesis falsification testing
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from scipy.stats import entropy, norm
from scipy.optimize import minimize_scalar
import warnings

try:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, Matern
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available")


@dataclass
class Hypothesis:
    """Represents a testable hypothesis."""
    hypothesis_id: str
    claim: str
    predictions: Dict[str, float]
    confidence: float
    falsification_criteria: List[str]
    priority: float
    status: str = 'pending'  # pending, testing, confirmed, falsified


@dataclass
class Experiment:
    """Represents an astronomical observation/experiment."""
    experiment_id: str
    objective: str
    target_objects: List[str]
    required_instruments: List[str]
    estimated_duration: float  # in hours
    expected_information_gain: float
    cost: float
    constraints: List[str] = field(default_factory=list)


@dataclass
class ObservationResult:
    """Result from an observation."""
    experiment_id: str
    data: np.ndarray
    metadata: Dict[str, Any]
    timestamp: float


class ActiveExperimentationEngine:
    """
    Actively design and run experiments to test hypotheses.

    Methods:
    1. Optimal Experimental Design: Maximize information gain
    2. Bayesian Active Learning: Select observations to reduce uncertainty
    3. Hypothesis Ranking: Prioritize hypotheses for testing
    4. Observation Planning: Schedule observations efficiently
    5. Result Interpretation: Update beliefs based on results
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize active experimentation engine.

        Args:
            config: Configuration dict with keys:
                - information_gain_threshold: Minimum expected gain (default: 0.1)
                - max_parallel_experiments: Maximum concurrent experiments (default: 5)
                - telescope_time_budget: Total available hours (default: 100)
        """
        config = config or {}
        self.info_gain_threshold = config.get('information_gain_threshold', 0.1)
        self.max_parallel = config.get('max_parallel_experiments', 5)
        self.time_budget = config.get('telescope_time_budget', 100)

        self.pending_hypotheses: List[Hypothesis] = []
        self.completed_experiments: List[Experiment] = []
        self.observation_results: List[ObservationResult] = []

    def generate_hypotheses(
        self,
        causal_discovery: CausalGraph,
        domain_knowledge: Dict[str, Any]
    ) -> List[Hypothesis]:
        """
        Generate testable hypotheses from causal discovery.

        Args:
            causal_discovery: Discovered causal graph
            domain_knowledge: Domain-specific knowledge

        Returns:
            List of testable hypotheses
        """
        hypotheses = []

        # For each edge in causal graph, generate hypothesis
        for edge in causal_discovery.edges:
            cause, effect = edge
            confidence = causal_discovery.confidence.get(edge, 0.5)

            if confidence < 0.7:
                # Generate hypothesis to test this causal link
                hypothesis = Hypothesis(
                    hypothesis_id=f"causal_{cause}_{effect}",
                    claim=f"{cause} causes {effect}",
                    predictions={effect: confidence},
                    confidence=confidence,
                    falsification_criteria=[
                        f"If {cause} is manipulated but {effect} doesn't change, causality rejected"
                    ],
                    priority=1.0 - confidence,  # Lower confidence = higher priority
                    status='pending'
                )
                hypotheses.append(hypothesis)

        # Generate novel hypotheses from domain knowledge
        if 'known_relations' in domain_knowledge:
            for relation in domain_knowledge['known_relations']:
                if relation.get('status') == 'uncertain':
                    hypothesis = Hypothesis(
                        hypothesis_id=f"novel_{relation['id']}",
                        claim=relation['claim'],
                        predictions=relation.get('predictions', {}),
                        confidence=0.5,
                        falsification_criteria=relation.get('falsification', []),
                        priority=relation.get('priority', 0.5),
                        status='pending'
                    )
                    hypotheses.append(hypothesis)

        # Sort by priority
        hypotheses.sort(key=lambda h: h.priority, reverse=True)

        self.pending_hypotheses.extend(hypotheses)
        return hypotheses

    def design_optimal_experiment(
        self,
        hypothesis: Hypothesis,
        available_targets: List[Dict[str, Any]],
        instrument_caps: Dict[str, Any]
    ) -> Experiment:
        """
        Design optimal experiment to test hypothesis.

        Args:
            hypothesis: Hypothesis to test
            available_targets: Potential observation targets
            instrument_caps: Instrument capabilities

        Returns:
            Optimally designed experiment
        """
        # Compute expected information gain for each target
        best_target = None
        best_gain = 0

        for target in available_targets:
            # Estimate information gain
            gain = self._estimate_information_gain(hypothesis, target, instrument_caps)

            if gain > best_gain:
                best_gain = gain
                best_target = target

        if best_target is None or best_gain < self.info_gain_threshold:
            raise ValueError("No suitable target found")

        # Design experiment around best target
        experiment = Experiment(
            experiment_id=f"exp_{hypothesis.hypothesis_id}_{best_target['name']}",
            objective=f"Test hypothesis: {hypothesis.claim}",
            target_objects=[best_target['name']],
            required_instruments=self._select_instruments(best_target, instrument_caps),
            estimated_duration=self._estimate_duration(best_target, instrument_caps),
            expected_information_gain=best_gain,
            cost=self._estimate_cost(best_target, instrument_caps)
        )

        return experiment

    def _estimate_information_gain(
        self,
        hypothesis: Hypothesis,
        target: Dict[str, Any],
        instrument_caps: Dict[str, Any]
    ) -> float:
        """
        Estimate expected information gain from observing target.

        Uses mutual information and uncertainty reduction.
        """
        # Simplified: use 1 - current confidence
        base_gain = 1.0 - hypothesis.confidence

        # Adjust by target observability
        observability = target.get('observability', 1.0)

        # Adjust by instrument sensitivity
        instrument_factor = 1.0
        for instrument in target.get('suitable_instruments', []):
            sensitivity = instrument_caps.get(instrument, {}).get('sensitivity', 1.0)
            instrument_factor = max(instrument_factor, sensitivity)

        return base_gain * observability * instrument_factor

    def _select_instruments(
        self,
        target: Dict[str, Any],
        instrument_caps: Dict[str, Any]
    ) -> List[str]:
        """Select optimal instruments for target."""
        required = target.get('required_instruments', [])
        available = list(instrument_caps.keys())

        # Return intersection
        return [inst for inst in required if inst in available]

    def _estimate_duration(
        self,
        target: Dict[str, Any],
        instrument_caps: Dict[str, Any]
    ) -> float:
        """Estimate observation duration."""
        # Base duration from target
        base = target.get('base_duration', 1.0)  # hours

        # Adjust by instrument efficiency
        efficiency = 1.0
        for inst in self._select_instruments(target, instrument_caps):
            eff = instrument_caps.get(inst, {}).get('efficiency', 1.0)
            efficiency = max(efficiency, eff)

        return base / efficiency

    def _estimate_cost(
        self,
        target: Dict[str, Any],
        instrument_caps: Dict[str, Any]
    ) -> float:
        """Estimate experiment cost."""
        # Cost = time × instrument_hourly_rate
        duration = self._estimate_duration(target, instrument_caps)

        hourly_rate = 0
        for inst in self._select_instruments(target, instrument_caps):
            rate = instrument_caps.get(inst, {}).get('hourly_cost', 100)
            hourly_rate += rate

        return duration * hourly_rate

    def plan_observation_schedule(
        self,
        experiments: List[Experiment],
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[Experiment]:
        """
        Plan optimal observation schedule.

        Args:
            experiments: Candidate experiments
            constraints: Scheduling constraints

        Returns:
            Scheduled experiments in priority order
        """
        constraints = constraints or {}

        # Filter by budget
        affordable = [exp for exp in experiments if exp.cost <= self.time_budget]

        # Sort by expected information gain per unit cost
        affordable.sort(key=lambda e: e.expected_information_gain / max(e.cost, 1), reverse=True)

        # Select top experiments within parallel limit
        scheduled = affordable[:self.max_parallel]

        return scheduled

    def simulate_observation(
        self,
        experiment: Experiment,
        true_model: Optional[Callable] = None
    ) -> ObservationResult:
        """
        Simulate running an experiment (for testing/development).

        Args:
            experiment: Experiment to run
            true_model: Optional true generative model

        Returns:
            Simulated observation result
        """
        # Simulate data
        n_data_points = 100

        if true_model is not None:
            # Use true model to generate data
            data = true_model(n_data_points)
        else:
            # Generate synthetic data
            data = np.random.randn(n_data_points, 3)

        result = ObservationResult(
            experiment_id=experiment.experiment_id,
            data=data,
            metadata={
                'instrument': experiment.required_instruments[0] if experiment.required_instruments else 'unknown',
                'target': experiment.target_objects[0] if experiment.target_objects else 'unknown',
                'duration': experiment.estimated_duration
            },
            timestamp=np.random.randn() * 1e9  # Unix timestamp
        )

        self.observation_results.append(result)
        return result

    def update_hypothesis_status(
        self,
        hypothesis: Hypothesis,
        result: ObservationResult
    ) -> Hypothesis:
        """
        Update hypothesis status based on observation result.

        Args:
            hypothesis: Hypothesis being tested
            result: Observation result

        Returns:
            Updated hypothesis
        """
        # Analyze result to see if hypothesis is supported

        # Simplified: check if predictions match data
        data_mean = np.mean(result.data, axis=0)

        predictions_match = True
        for var, predicted_val in hypothesis.predictions.items():
            # Check if data is consistent with prediction
            if var in result.metadata:
                obs_val = data_mean[0]  # Simplified
                if abs(obs_val - predicted_val) > 2.0:  # 2-sigma threshold
                    predictions_match = False

        if predictions_match:
            hypothesis.status = 'confirmed'
            hypothesis.confidence = min(0.99, hypothesis.confidence * 1.2)
        else:
            hypothesis.status = 'falsified'
            hypothesis.confidence = max(0.01, hypothesis.confidence * 0.5)

        return hypothesis

    def run_autonomous_discovery_cycle(
        self,
        initial_hypotheses: List[Hypothesis],
        available_targets: List[Dict[str, Any]],
        instrument_caps: Dict[str, Any],
        max_cycles: int = 10
    ) -> Dict[str, Any]:
        """
        Run autonomous discovery cycle: generate hypotheses -> design experiments -> observe -> update.

        Args:
            initial_hypotheses: Starting hypotheses
            available_targets: Potential observation targets
            instrument_caps: Instrument capabilities
            max_cycles: Maximum discovery cycles

        Returns:
            Summary of discovery process
        """
        cycle_results = []
        current_hypotheses = initial_hypotheses.copy()

        for cycle in range(max_cycles):
            print(f"\n--- Discovery Cycle {cycle + 1} ---")

            # Select best hypothesis to test
            if not current_hypotheses:
                print("No more hypotheses to test")
                break

            hypothesis = current_hypotheses[0]

            # Design experiment
            try:
                experiment = self.design_optimal_experiment(
                    hypothesis, available_targets, instrument_caps
                )
            except ValueError as e:
                print(f"Cannot design experiment: {e}")
                break

            print(f"Testing: {hypothesis.claim}")
            print(f"Experiment: {experiment.experiment_id}")

            # Run observation (simulate)
            result = self.simulate_observation(experiment)

            # Update hypothesis
            updated = self.update_hypothesis_status(hypothesis, result)
            print(f"Result: {updated.status}")
            print(f"Updated confidence: {updated.confidence:.2f}")

            cycle_results.append({
                'cycle': cycle,
                'hypothesis': hypothesis.hypothesis_id,
                'status': updated.status,
                'confidence': updated.confidence
            })

            # Remove confirmed/falsified hypotheses
            current_hypotheses = [h for h in current_hypotheses
                                  if h.hypothesis_id != hypothesis.hypothesis_id]

            # Update budget
            self.time_budget -= experiment.estimated_duration
            if self.time_budget <= 0:
                print("Budget exhausted")
                break

        return {
            'cycles_completed': len(cycle_results),
            'hypotheses_tested': len(cycle_results),
            'results': cycle_results
        }


def demo_active_experimentation():
    """Demonstrate active experimentation engine."""
    print("=" * 60)
    print("Active Experimentation Engine Demo")
    print("=" * 60)

    # Create test hypotheses
    hypotheses = [
        Hypothesis(
            hypothesis_id="test_hyp_1",
            claim="Variable X causes Variable Y",
            predictions={'Y': 0.5},
            confidence=0.6,
            falsification_criteria=["If X changes but Y doesn't, rejected"],
            priority=0.4
        ),
        Hypothesis(
            hypothesis_id="test_hyp_2",
            claim="Temperature affects star formation rate",
            predictions={'SFR': 1.5},
            confidence=0.4,
            falsification_criteria=["No correlation with temperature"],
            priority=0.6
        )
    ]

    # Available targets
    targets = [
        {'name': 'molecular_cloud_A', 'observability': 0.8,
         'required_instruments': ['ALMA'], 'base_duration': 2.0},
        {'name': 'galaxy_cluster_B', 'observability': 0.6,
         'required_instruments': ['Chandra'], 'base_duration': 5.0}
    ]

    # Instrument capabilities
    instrument_caps = {
        'ALMA': {'sensitivity': 0.9, 'efficiency': 0.8, 'hourly_cost': 100},
        'Chandra': {'sensitivity': 0.7, 'efficiency': 0.6, 'hourly_cost': 150}
    }

    # Initialize engine
    engine = ActiveExperimentationEngine()

    # Design optimal experiment for first hypothesis
    experiment = engine.design_optimal_experiment(hypotheses[0], targets, instrument_caps)

    print(f"\nOptimal Experiment:")
    print(f"  ID: {experiment.experiment_id}")
    print(f"  Objective: {experiment.objective}")
    print(f"  Targets: {experiment.target_objects}")
    print(f"  Instruments: {experiment.required_instruments}")
    print(f"  Duration: {experiment.estimated_duration:.1f} hours")
    print(f"  Expected Info Gain: {experiment.expected_information_gain:.2f}")
    print(f"  Cost: ${experiment.cost:.0f}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    demo_active_experimentation()
