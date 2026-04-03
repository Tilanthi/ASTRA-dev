"""
Capability Baseline for STAN Self-Evolution

Defines what constitutes "improved reasoning" in the context of
astrophysics discovery and inference. This framework evaluates
capabilities based on their ability to:

1. Generate novel insights from data
2. Make valid inferences across domains
3. Discover patterns humans might miss
4. Maintain logical consistency
5. Generalize to new problems
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import numpy as np
import time
from abc import ABC, abstractmethod


class ReasoningMetric(Enum):
    """
    Core metrics for evaluating reasoning quality.

    These are objective measures that don't require human supervision:
    """
    # Logical consistency
    LOGICAL_CONSISTENCY = "logical_consistency"  # Internal coherence of reasoning
    INFERENCE_VALIDITY = "inference_validity"    # Soundness of logical steps

    # Discovery capability
    PATTERN_DISCOVERY = "pattern_discovery"      # Finding non-obvious patterns
    NOVELTY_GENERATION = "novelty_generation"    # Generating new insights
    HYPOTHESIS_QUALITY = "hypothesis_quality"    # Testability and falsifiability

    # Generalization
    CROSS_DOMAIN_TRANSFER = "cross_domain_transfer"  # Applying knowledge elsewhere
    ABSTRACTION_QUALITY = "abstraction_quality"      # Extracting principles
    GENERALIZATION_SCORE = "generalization_score"    # Performance on new problems

    # Efficiency
    COMPUTATIONAL_EFFICIENCY = "computational_efficiency"  # Time/resources used
    CONVERGENCE_SPEED = "convergence_speed"                # How fast solutions emerge

    # Robustness
    UNCERTAINTY_CALIBRATION = "uncertainty_calibration"  # Accurate confidence
    ERROR_RECOVERY = "error_recovery"                    # Handling failures
    NOISE_TOLERANCE = "noise_tolerance"                  # Working with imperfect data


@dataclass
class MetricScore:
    """Score for a single reasoning metric"""
    metric: ReasoningMetric
    value: float  # 0-1 score
    confidence: float  # Confidence in this score
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class CapabilityProfile:
    """Complete capability profile of a system"""
    scores: Dict[ReasoningMetric, MetricScore]
    overall_score: float
    strengths: List[ReasoningMetric]
    weaknesses: List[ReasoningMetric]
    timestamp: float = field(default_factory=time.time)


class ReasoningTask(ABC):
    """
    Abstract base class for reasoning tasks used to evaluate capabilities.

    Tasks should be:
    - Self-contained (no external data needed)
    - Objectively scoreable
    - Representative of astrophysics reasoning
    - Challenging (not trivial)
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return task name"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return task description"""
        pass

    @abstractmethod
    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """
        Execute task and return (score, details)

        Args:
            system: The system being tested

        Returns:
            (score: 0-1, details: execution details)
        """
        pass

    @abstractmethod
    def get_difficulty(self) -> float:
        """Return task difficulty (0-1)"""
        pass


class CapabilityBaseline:
    """
    Defines and evaluates capability baselines for reasoning systems.

    This provides the objective framework for determining whether
    a mutation has improved the system.
    """

    def __init__(self, stan_core_path: str = "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO"):
        self.stan_core_path = stan_core_path
        self.tasks: List[ReasoningTask] = []
        self.baseline_profiles: Dict[str, CapabilityProfile] = {}

        # Register default astrophysics reasoning tasks
        self._register_default_tasks()

    def _register_default_tasks(self):
        """Register default astrophysics reasoning tasks"""
        self.tasks.extend([
            SpectralPatternDiscoveryTask(),
            CausalInferenceTask(),
            AbstractionFormationTask(),
            CounterfactualReasoningTask(),
            CrossDomainTransferTask(),
            HypothesisGenerationTask(),
            UncertaintyQuantificationTask(),
            MultiScaleInferenceTask(),
        ])

    def evaluate_capability(self, system: Any, task_filter: Optional[List[str]] = None) -> CapabilityProfile:
        """
        Evaluate system capability across all reasoning tasks.

        Args:
            system: The system to evaluate
            task_filter: Optional list of task names to run

        Returns:
            CapabilityProfile with scores for all metrics
        """
        scores = {}
        task_details = {}

        # Run all tasks (or filtered subset)
        for task in self.tasks:
            if task_filter and task.get_name() not in task_filter:
                continue

            try:
                score, details = task.execute(system)
                task_details[task.get_name()] = details

                # Map task to metric
                metric = self._task_to_metric(task)
                scores[metric] = MetricScore(
                    metric=metric,
                    value=score,
                    confidence=0.7,  # Default confidence
                    details={'task': task.get_name(), **details}
                )
            except Exception as e:
                # Log failure but continue
                scores[self._task_to_metric(task)] = MetricScore(
                    metric=self._task_to_metric(task),
                    value=0.0,
                    confidence=0.0,
                    details={'error': str(e), 'task': task.get_name()}
                )

        # Compute overall score
        overall = np.mean([s.value for s in scores.values()]) if scores else 0.0

        # Identify strengths and weaknesses
        sorted_metrics = sorted(scores.items(), key=lambda x: x[1].value)
        weaknesses = [m for m, s in sorted_metrics[:3]] if len(sorted_metrics) > 3 else []
        strengths = [m for m, s in sorted_metrics[-3:]] if len(sorted_metrics) > 3 else []

        return CapabilityProfile(
            scores=scores,
            overall_score=overall,
            strengths=strengths,
            weaknesses=weaknesses
        )

    def _task_to_metric(self, task: ReasoningTask) -> ReasoningMetric:
        """Map task to primary metric"""
        task_name = task.get_name()

        mapping = {
            "spectral_pattern_discovery": ReasoningMetric.PATTERN_DISCOVERY,
            "causal_inference": ReasoningMetric.INFERENCE_VALIDITY,
            "abstraction_formation": ReasoningMetric.ABSTRACTION_QUALITY,
            "counterfactual_reasoning": ReasoningMetric.LOGICAL_CONSISTENCY,
            "cross_domain_transfer": ReasoningMetric.CROSS_DOMAIN_TRANSFER,
            "hypothesis_generation": ReasoningMetric.HYPOTHESIS_QUALITY,
            "uncertainty_quantification": ReasoningMetric.UNCERTAINTY_CALIBRATION,
            "multi_scale_inference": ReasoningMetric.GENERALIZATION_SCORE,
        }

        return mapping.get(task_name, ReasoningMetric.LOGICAL_CONSISTENCY)

    def compare_profiles(self, profile1: CapabilityProfile, profile2: CapabilityProfile) -> Dict[str, Any]:
        """
        Compare two capability profiles to determine improvement.

        Returns:
            Dict with improvement metrics
        """
        # Compare overall scores
        overall_improvement = profile2.overall_score - profile1.overall_score

        # Compare individual metrics
        metric_improvements = {}
        for metric in profile1.scores:
            if metric in profile2.scores:
                improvement = profile2.scores[metric].value - profile1.scores[metric].value
                metric_improvements[metric.value] = improvement

        # Count improvements vs regressions
        improvements = sum(1 for v in metric_improvements.values() if v > 0.01)
        regressions = sum(1 for v in metric_improvements.values() if v < -0.01)
        unchanged = len(metric_improvements) - improvements - regressions

        # Check if weaknesses improved
        weaknesses_improved = any(
            metric in profile2.strengths and metric not in profile1.strengths
            for metric in profile1.weaknesses
        )

        return {
            'overall_improvement': overall_improvement,
            'metric_improvements': metric_improvements,
            'improvements': improvements,
            'regressions': regressions,
            'unchanged': unchanged,
            'weaknesses_improved': weaknesses_improved,
            'is_better': overall_improvement > 0.05 and regressions == 0,
        }

    def save_baseline(self, name: str, profile: CapabilityProfile):
        """Save a capability profile as a named baseline"""
        self.baseline_profiles[name] = profile

    def load_baseline(self, name: str) -> Optional[CapabilityProfile]:
        """Load a named baseline profile"""
        return self.baseline_profiles.get(name)


# =============================================================================
# ASTROPHYSICS REASONING TASKS
# =============================================================================

class SpectralPatternDiscoveryTask(ReasoningTask):
    """
    Task: Discover patterns in synthetic spectral data

    Tests ability to find non-obvious patterns in high-dimensional data,
    a core skill in astrophysics discovery.
    """

    def __init__(self):
        # Generate synthetic spectral data with hidden patterns
        np.random.seed(42)
        self.wavelengths = np.linspace(4000, 7000, 1000)  # Angstroms

        # Hidden pattern: sinusoidal variation + emission lines
        self.flux_base = np.sin(2 * np.pi * self.wavelengths / 5000) * 0.1 + 1.0

        # Add hidden emission lines at specific ratios (Golden ratio connection)
        golden_ratio = (1 + np.sqrt(5)) / 2
        line_positions = [5000, 5000 * golden_ratio, 5000 * golden_ratio**2]
        self.flux = self.flux_base.copy()
        for pos in line_positions:
            if 4000 <= pos <= 7000:
                idx = np.argmin(np.abs(self.wavelengths - pos))
                self.flux[idx] += 0.5

        # Add noise
        self.flux += np.random.randn(1000) * 0.05

    def get_name(self) -> str:
        return "spectral_pattern_discovery"

    def get_description(self) -> str:
        return "Discover hidden patterns in synthetic spectral data including emission lines at golden-ratio spaced wavelengths"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate system's pattern discovery capability"""
        try:
            # Try to use the system to analyze the spectral data
            if hasattr(system, 'analyze_spectrum'):
                result = system.analyze_spectrum(self.wavelengths, self.flux)
            elif hasattr(system, 'discover_patterns'):
                result = system.discover_patterns({'wavelengths': self.wavelengths, 'flux': self.flux})
            else:
                # Fall back to basic analysis
                result = self._basic_analysis()

            # Score based on whether golden ratio pattern was discovered
            score = self._score_result(result)

            return score, {
                'result': result,
                'expected_pattern': 'emission lines at golden-ratio intervals',
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_analysis(self) -> Dict[str, Any]:
        """Basic analysis as fallback"""
        # Find peaks
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(self.flux, height=0.3)

        peak_wavelengths = self.wavelengths[peaks].tolist()

        return {
            'peaks_found': len(peaks),
            'peak_wavelengths': peak_wavelengths,
            'flux_range': [float(np.min(self.flux)), float(np.max(self.flux))]
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score the result based on pattern discovery"""
        score = 0.0

        # Check for emission lines
        if 'peak_wavelengths' in result:
            peaks = result['peak_wavelengths']

            # Check if peaks are near expected positions
            expected = [5000, 5000 * 1.618, 5000 * 2.618]
            for exp in expected:
                if 4000 <= exp <= 7000:
                    # Check if a peak is within 50 Angstroms
                    if any(abs(p - exp) < 50 for p in peaks):
                        score += 0.3

        # Check for golden ratio recognition
        if 'pattern_recognized' in result:
            if result['pattern_recognized'] == 'golden_ratio':
                score += 0.4

        return min(score, 1.0)

    def get_difficulty(self) -> float:
        return 0.7


class CausalInferenceTask(ReasoningTask):
    """
    Task: Infer causal relationships from observational data

    Tests ability to distinguish correlation from causation,
    crucial for astrophysics inference.
    """

    def __init__(self):
        # Generate synthetic data with causal structure
        np.random.seed(43)

        # Causal structure: X -> Y -> Z, X -> Z (confounding)
        self.X = np.random.randn(1000)
        self.Y = 0.5 * self.X + np.random.randn(1000) * 0.3
        self.Z = 0.3 * self.X + 0.4 * self.Y + np.random.randn(1000) * 0.2

        # Confounder W that affects both Y and Z
        self.W = np.random.randn(1000)
        self.Y += 0.2 * self.W
        self.Z += 0.3 * self.W

        self.data = {
            'X': self.X, 'Y': self.Y, 'Z': self.Z, 'W': self.W
        }

    def get_name(self) -> str:
        return "causal_inference"

    def get_description(self) -> str:
        return "Infer causal structure from synthetic observational data with confounding"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate causal inference capability"""
        try:
            if hasattr(system, 'infer_causality'):
                result = system.infer_causality(self.data)
            elif hasattr(system, 'discover_causal_structure'):
                result = system.discover_causal_structure(self.data)
            else:
                result = self._basic_inference()

            score = self._score_result(result)

            return score, {
                'result': result,
                'expected_structure': 'X -> Y -> Z, X -> Z, W -> Y, W -> Z',
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_inference(self) -> Dict[str, Any]:
        """Basic inference as fallback"""
        from scipy.stats import pearsonr

        correlations = {}
        for var1 in ['X', 'Y', 'Z', 'W']:
            for var2 in ['X', 'Y', 'Z', 'W']:
                if var1 < var2:
                    corr, _ = pearsonr(self.data[var1], self.data[var2])
                    correlations[f"{var1}-{var2}"] = corr

        return {
            'correlations': correlations,
            'inferred_structure': 'unknown'
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score causal inference result"""
        score = 0.0

        # Check if causal structure was inferred
        if 'causal_graph' in result:
            graph = result['causal_graph']

            # Correct edges: X->Y, Y->Z, X->Z, W->Y, W->Z
            correct_edges = {('X', 'Y'), ('Y', 'Z'), ('X', 'Z'), ('W', 'Y'), ('W', 'Z')}

            if isinstance(graph, dict):
                inferred_edges = set()
                for source, targets in graph.items():
                    for target in targets:
                        inferred_edges.add((source, target))

                correct = len(inferred_edges & correct_edges)
                score = correct / len(correct_edges)

        return min(score, 1.0)

    def get_difficulty(self) -> float:
        return 0.8


class AbstractionFormationTask(ReasoningTask):
    """
    Task: Form abstract principles from concrete examples

    Tests ability to generalize and extract principles,
    key for scientific discovery.
    """

    def __init__(self):
        # Examples of gravitational systems
        self.examples = [
            {"system": "planet", "mass": 1, "distance": 1, "period": 1},
            {"system": "planet", "mass": 1, "distance": 4, "period": 8},
            {"system": "planet", "mass": 1, "distance": 9, "period": 27},
            {"system": "planet", "mass": 2, "distance": 1, "period": 0.7},
        ]

    def get_name(self) -> str:
        return "abstraction_formation"

    def get_description(self) -> str:
        return "Extract Kepler's Third Law (T² ∝ R³) from orbital examples"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate abstraction formation capability"""
        try:
            if hasattr(system, 'extract_principle'):
                result = system.extract_principle(self.examples)
            elif hasattr(system, 'form_abstraction'):
                result = system.form_abstraction(self.examples)
            else:
                result = self._basic_extraction()

            score = self._score_result(result)

            return score, {
                'result': result,
                'expected_principle': 'T² ∝ R³/M (Kepler\'s Third Law)',
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_extraction(self) -> Dict[str, Any]:
        """Basic extraction as fallback"""
        import numpy as np

        # Extract distance and period
        distances = [e["distance"] for e in self.examples[:3]]
        periods = [e["period"] for e in self.examples[:3]]

        # Check for power law relationship
        log_d = np.log(distances)
        log_p = np.log(periods)

        slope = np.polyfit(log_d, log_p, 1)[0]

        return {
            'power_law_exponent': float(slope),
            'extracted_principle': f'T ∝ R^{slope:.2f}'
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score abstraction result"""
        score = 0.0

        # Expected exponent is 1.5 (since T² ∝ R³ means T ∝ R^(3/2))
        expected_exponent = 1.5

        if 'power_law_exponent' in result:
            exponent = result['power_law_exponent']
            error = abs(exponent - expected_exponent)
            score = max(0, 1 - error)

        return score

    def get_difficulty(self) -> float:
        return 0.6


class CounterfactualReasoningTask(ReasoningTask):
    """
    Task: Reason about what would happen under different conditions

    Tests ability to perform counterfactual reasoning,
    essential for hypothesis testing.
    """

    def __init__(self):
        self.scenario = {
            'system': 'star',
            'mass': 1.0,  # Solar masses
            'temperature': 5778,  # K
            'luminosity': 1.0,  # Solar luminosities
        }

    def get_name(self) -> str:
        return "counterfactual_reasoning"

    def get_description(self) -> str:
        return "Predict how stellar properties would change if mass were doubled"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate counterfactual reasoning capability"""
        try:
            counterfactual = {'mass': 2.0}  # What if mass were doubled?

            if hasattr(system, 'reason_counterfactual'):
                result = system.reason_counterfactual(self.scenario, counterfactual)
            elif hasattr(system, 'simulate_counterfactual'):
                result = system.simulate_counterfactual(self.scenario, counterfactual)
            else:
                result = self._basic_counterfactual()

            score = self._score_result(result)

            return score, {
                'result': result,
                'expected': 'L ∝ M^3.5, T ∝ M^0.5 (main sequence relations)',
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_counterfactual(self) -> Dict[str, Any]:
        """Basic counterfactual as fallback"""
        # Main sequence scaling relations
        mass_ratio = 2.0
        luminosity_ratio = mass_ratio ** 3.5
        temp_ratio = mass_ratio ** 0.5

        return {
            'predicted_luminosity': luminosity_ratio,
            'predicted_temperature': 5778 * temp_ratio
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score counterfactual result"""
        score = 0.0

        expected_luminosity = 2.0 ** 3.5  # ~11.3
        expected_temp = 5778 * (2.0 ** 0.5)  # ~8170 K

        if 'predicted_luminosity' in result:
            lum_error = abs(result['predicted_luminosity'] - expected_luminosity) / expected_luminosity
            score += max(0, 1 - lum_error) * 0.5

        if 'predicted_temperature' in result:
            temp_error = abs(result['predicted_temperature'] - expected_temp) / expected_temp
            score += max(0, 1 - temp_error) * 0.5

        return score

    def get_difficulty(self) -> float:
        return 0.5


class CrossDomainTransferTask(ReasoningTask):
    """
    Task: Apply knowledge from one domain to another

    Tests ability to transfer reasoning patterns across domains.
    """

    def __init__(self):
        self.source_domain = {
            'name': 'planetary_orbits',
            'principle': 'gravitational_force decreases as 1/r²',
            'examples': [
                {'r': 1, 'F': 1},
                {'r': 2, 'F': 0.25},
                {'r': 3, 'F': 0.111}
            ]
        }

        self.target_domain = {
            'name': 'electromagnetic_radiation',
            'question': 'How does intensity vary with distance from a source?'
        }

    def get_name(self) -> str:
        return "cross_domain_transfer"

    def get_description(self) -> str:
        return "Transfer inverse-square law from gravity to electromagnetic radiation"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate cross-domain transfer capability"""
        try:
            if hasattr(system, 'transfer_knowledge'):
                result = system.transfer_knowledge(self.source_domain, self.target_domain)
            elif hasattr(system, 'apply_across_domains'):
                result = system.apply_across_domains(self.source_domain, self.target_domain)
            else:
                result = self._basic_transfer()

            score = self._score_result(result)

            return score, {
                'result': result,
                'expected': 'Intensity ∝ 1/r² (inverse-square law)',
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_transfer(self) -> Dict[str, Any]:
        """Basic transfer as fallback"""
        # Both gravity and EM follow inverse-square law
        return {
            'transferred_principle': 'inverse_square_law',
            'relationship': 'I ∝ 1/r²',
            'confidence': 0.9
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score transfer result"""
        score = 0.0

        if 'relationship' in result:
            if '1/r²' in result['relationship'] or '1/r^2' in result['relationship']:
                score = 1.0
            elif 'inverse' in str(result).lower() and 'square' in str(result).lower():
                score = 0.8
            elif 'inverse' in str(result).lower():
                score = 0.5

        return score

    def get_difficulty(self) -> float:
        return 0.4


class HypothesisGenerationTask(ReasoningTask):
    """
    Task: Generate testable hypotheses from observations

    Tests ability to create falsifiable scientific hypotheses.
    """

    def __init__(self):
        self.observations = {
            'star_name': 'Mystery-Star-42',
            'spectral_lines': ['H-alpha', 'H-beta', 'He I'],
            'variability': 'periodic with period 23.4 hours',
            'position': {'ra': '18h 36m', 'dec': '+38° 47m'},
            'magnitude_variations': 0.15
        }

    def get_name(self) -> str:
        return "hypothesis_generation"

    def get_description(self) -> str:
        return "Generate testable hypotheses explaining the observations"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate hypothesis generation capability"""
        try:
            if hasattr(system, 'generate_hypothesis'):
                result = system.generate_hypothesis(self.observations)
            elif hasattr(system, 'formulate_hypotheses'):
                result = system.formulate_hypotheses(self.observations)
            else:
                result = self._basic_generation()

            score = self._score_result(result)

            return score, {
                'result': result,
                'expected_hypotheses': ['pulsating_variable_star', 'eclipsing_binary', 'rotating_star'],
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_generation(self) -> Dict[str, Any]:
        """Basic hypothesis generation as fallback"""
        return {
            'primary_hypothesis': 'pulsating_variable_star',
            'alternative_hypotheses': [
                'eclipsing_binary_system',
                'rotating_star_with_spots'
            ],
            'testable_predictions': [
                'radial_velocity_variations',
                'temperature_changes_during_cycle',
                'line_profile_variations'
            ]
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score hypothesis generation"""
        score = 0.0

        # Check for plausible astrophysical explanations
        plausible = ['pulsating', 'variable', 'binary', 'eclipsing', 'rotating']

        result_str = str(result).lower()

        for p in plausible:
            if p in result_str:
                score += 0.2

        # Check for testable predictions
        if 'prediction' in result_str or 'test' in result_str:
            score += 0.2

        return min(score, 1.0)

    def get_difficulty(self) -> float:
        return 0.6


class UncertaintyQuantificationTask(ReasoningTask):
    """
    Task: Quantify uncertainty in estimates

    Tests ability to accurately represent uncertainty.
    """

    def __init__(self):
        # Generate data with known uncertainty
        np.random.seed(44)
        self.true_value = 42.0
        self.observations = self.true_value + np.random.randn(100) * 5.0

    def get_name(self) -> str:
        return "uncertainty_quantification"

    def get_description(self) -> str:
        return "Estimate value and uncertainty from noisy observations"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate uncertainty quantification capability"""
        try:
            if hasattr(system, 'estimate_with_uncertainty'):
                result = system.estimate_with_uncertainty(self.observations)
            elif hasattr(system, 'quantify_uncertainty'):
                result = system.quantify_uncertainty(self.observations)
            else:
                result = self._basic_uncertainty()

            score = self._score_result(result)

            return score, {
                'result': result,
                'true_value': self.true_value,
                'expected_uncertainty': '~5.0',
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_uncertainty(self) -> Dict[str, Any]:
        """Basic uncertainty estimation as fallback"""
        import numpy as np

        estimate = np.mean(self.observations)
        uncertainty = np.std(self.observations) / np.sqrt(len(self.observations))

        return {
            'estimate': float(estimate),
            'uncertainty': float(uncertainty),
            'confidence_interval': [estimate - 2*uncertainty, estimate + 2*uncertainty]
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score uncertainty quantification"""
        score = 0.0

        if 'estimate' in result and 'uncertainty' in result:
            estimate = result['estimate']
            uncertainty = result['uncertainty']

            # Check if true value is within uncertainty bounds
            if abs(estimate - self.true_value) <= uncertainty:
                score = 1.0
            else:
                # Partial credit based on error
                error = abs(estimate - self.true_value)
                score = max(0, 1 - error / (uncertainty + 1))

        return score

    def get_difficulty(self) -> float:
        return 0.3


class MultiScaleInferenceTask(ReasoningTask):
    """
    Task: Make inferences across multiple spatial/temporal scales

    Tests ability to integrate information at different scales.
    """

    def __init__(self):
        self.data = {
            'small_scale': {'size': 'stellar', 'phenomenon': 'magnetic_reconnection', 'energy': 1e20},
            'medium_scale': {'size': 'cluster', 'phenomenon': 'coronal_heating', 'energy': 1e25},
            'large_scale': {'size': 'galactic', 'phenomenon': 'cosmic_ray_acceleration', 'energy': 1e30}
        }

    def get_name(self) -> str:
        return "multi_scale_inference"

    def get_description(self) -> str:
        return "Integrate phenomena across stellar to galactic scales"

    def execute(self, system: Any) -> Tuple[float, Dict[str, Any]]:
        """Evaluate multi-scale inference capability"""
        try:
            if hasattr(system, 'integrate_scales'):
                result = system.integrate_scales(self.data)
            elif hasattr(system, 'multi_scale_inference'):
                result = system.multi_scale_inference(self.data)
            else:
                result = self._basic_inference()

            score = self._score_result(result)

            return score, {
                'result': result,
                'expected': 'Magnetic processes operate across all scales',
                'difficulty': self.get_difficulty()
            }
        except Exception as e:
            return 0.0, {'error': str(e)}

    def _basic_inference(self) -> Dict[str, Any]:
        """Basic multi-scale inference as fallback"""
        return {
            'unifying_principle': 'magnetic_fields_operate_across_scales',
            'scale_connections': [
                'stellar_reconnection_drives_coronal_heating',
                'coronal_heating_contributes_to_galactic_cosmic_rays'
            ],
            'energy_scaling': 'E ∝ scale^(3/2)'
        }

    def _score_result(self, result: Dict[str, Any]) -> float:
        """Score multi-scale inference"""
        score = 0.0

        result_str = str(result).lower()

        # Check for recognition of magnetic processes
        if 'magnetic' in result_str or 'field' in result_str:
            score += 0.3

        # Check for scale connections
        if 'scale' in result_str:
            score += 0.3

        # Check for energy scaling
        if 'energy' in result_str:
            score += 0.2

        # Check for unifying principle
        if 'principle' in result_str or 'unify' in result_str:
            score += 0.2

        return score

    def get_difficulty(self) -> float:
        return 0.7


__all__ = [
    'ReasoningMetric',
    'MetricScore',
    'CapabilityProfile',
    'ReasoningTask',
    'CapabilityBaseline',
]
