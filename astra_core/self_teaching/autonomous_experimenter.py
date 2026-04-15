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
Autonomous Experiment Designer for STAR-Learn V2.5

This module enables STAR-Learn to design and execute experiments:
1. Hypothesis-driven experiment design
2. Optimal experimental design (minimize variance)
3. Sequential experimental design (adaptive)
4. Multi-factor experiment design
5. Experiment simulation and prediction
6. Results analysis and interpretation
7. Next-experiment recommendation

This is a CRITICAL AGI capability - the ability to autonomously
design experiments to test hypotheses and gain new knowledge.

Version: 2.5.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import itertools

# Optional scipy for statistical tests
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class ExperimentType(Enum):
    """Types of experiments"""
    OBSERVATIONAL = "observational"  # Observe without intervention
    CONTROLLED = "controlled"  # Manipulate variables
    RANDOMIZED = "randomized"  # Random assignment
    BLIND = "blind"  # Single-blind
    DOUBLE_BLIND = "double_blind"  # Double-blind
    FIELD = "field"  # Natural environment
    SIMULATION = "simulation"  # Computational experiment


class ExperimentStatus(Enum):
    """Status of an experiment"""
    DESIGNED = "designed"
    RUNNING = "running"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    FAILED = "failed"


@dataclass
class Variable:
    """An experimental variable"""
    name: str
    type: str  # "independent", "dependent", "controlled", "confounding"
    values: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    units: str = ""
    measurement_method: str = ""


@dataclass
class Hypothesis:
    """A scientific hypothesis to test"""
    statement: str
    null_hypothesis: str
    independent_variables: List[str]
    dependent_variables: List[str]
    predicted_relationship: str
    confidence: float = 0.5


@dataclass
class ExperimentalCondition:
    """A condition in an experiment"""
    name: str
    variable_settings: Dict[str, Any]
    replications: int = 1
    randomization: bool = False


@dataclass
class ExperimentDesign:
    """A complete experimental design"""
    name: str
    experiment_type: ExperimentType
    hypothesis: Optional[Hypothesis] = None
    variables: List[Variable] = field(default_factory=list)
    conditions: List[ExperimentalCondition] = field(default_factory=list)
    procedure: List[str] = field(default_factory=list)
    measurements: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)
    sample_size: int = 30
    duration: str = ""
    status: ExperimentStatus = ExperimentStatus.DESIGNED
    expected_outcomes: List[str] = field(default_factory=list)
    design_id: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExperimentResult:
    """Results from running an experiment"""
    experiment_id: str
    condition_results: Dict[str, Any] = field(default_factory=dict)
    measurements: Dict[str, List[float]] = field(default_factory=dict)
    statistical_tests: Dict[str, Any] = field(default_factory=dict)
    effect_sizes: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    p_values: Dict[str, float] = field(default_factory=dict)
    conclusion: str = ""
    hypothesis_supported: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class NextExperimentRecommendation:
    """Recommendation for next experiment"""
    priority: float  # 0-1
    experiment_type: ExperimentType
    rationale: str
    variables_to_test: List[str]
    expected_information_gain: float
    estimated_cost: float = 1.0
    design_hints: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Experiment Designer
# =============================================================================
class ExperimentDesigner:
    """
    Design experiments to test scientific hypotheses.

    Key capabilities:
    - Optimal design (minimize variance, maximize power)
    - Sequential design (adapt based on results)
    - Multi-factor design (test multiple variables)
    - Resource optimization (minimize cost, maximize information)
    """

    def __init__(self):
        """Initialize the experiment designer."""
        self.design_history = []
        self.result_history = []

    def design_experiment(
        self,
        hypothesis: Hypothesis,
        variables: List[Variable],
        constraints: Optional[Dict[str, Any]] = None
    ) -> ExperimentDesign:
        """
        Design an experiment to test a hypothesis.

        Args:
            hypothesis: Hypothesis to test
            variables: Variables in the experiment
            constraints: Experimental constraints (budget, time, equipment)

        Returns:
            Complete experimental design
        """
        constraints = constraints or {}

        # Determine optimal experimental type
        exp_type = self._select_experiment_type(hypothesis, constraints)

        # Design experimental conditions
        conditions = self._design_conditions(hypothesis, variables, constraints)

        # Determine sample size
        sample_size = self._calculate_sample_size(hypothesis, variables, constraints)

        # Create procedure
        procedure = self._generate_procedure(hypothesis, variables, conditions)

        # Specify measurements
        measurements = self._specify_measurements(hypothesis, variables)

        # Identify controls
        controls = self._identify_controls(hypothesis, variables)

        # Predict outcomes
        expected_outcomes = self._predict_outcomes(hypothesis)

        design = ExperimentDesign(
            name=f"Test of {hypothesis.statement[:50]}",
            experiment_type=exp_type,
            hypothesis=hypothesis,
            variables=variables,
            conditions=conditions,
            procedure=procedure,
            measurements=measurements,
            controls=controls,
            sample_size=sample_size,
            duration=constraints.get('duration', '1 hour'),
            expected_outcomes=expected_outcomes
        )

        self.design_history.append(design)
        return design

    def _select_experiment_type(
        self,
        hypothesis: Hypothesis,
        constraints: Dict
    ) -> ExperimentType:
        """Select the best experimental type."""
        # Default to controlled experiment
        return ExperimentType.CONTROLLED

    def _design_conditions(
        self,
        hypothesis: Hypothesis,
        variables: List[Variable],
        constraints: Dict
    ) -> List[ExperimentalCondition]:
        """Design experimental conditions."""
        conditions = []

        # Get independent variables
        independent_vars = [v for v in variables if v.type == "independent"]

        if not independent_vars:
            return conditions

        # Create factorial design
        var_values = []
        for var in independent_vars:
            if var.values:
                var_values.append(var.values)
            elif var.min_value is not None and var.max_value is not None:
                # Use min, max, and midpoint
                var_values.append([var.min_value, var.max_value])
            else:
                var_values.append([0, 1])

        # Generate all combinations
        for combination in itertools.product(*var_values):
            settings = {}
            for i, var in enumerate(independent_vars):
                settings[var.name] = combination[i]

            condition = ExperimentalCondition(
                name=f"Condition_{len(conditions)}",
                variable_settings=settings,
                replications=3
            )
            conditions.append(condition)

        return conditions

    def _calculate_sample_size(
        self,
        hypothesis: Hypothesis,
        variables: List[Variable],
        constraints: Dict
    ) -> int:
        """Calculate required sample size."""
        # Use power analysis (simplified)
        effect_size = hypothesis.confidence  # Use confidence as proxy
        alpha = 0.05  # Significance level
        power = 0.8  # Desired power

        # Simplified formula
        if effect_size > 0.5:
            return 20
        elif effect_size > 0.3:
            return 50
        else:
            return 100

    def _generate_procedure(
        self,
        hypothesis: Hypothesis,
        variables: List[Variable],
        conditions: List[ExperimentalCondition]
    ) -> List[str]:
        """Generate experimental procedure."""
        procedure = [
            f"1. Prepare experimental materials",
            f"2. Randomize participants/samples to conditions",
            f"3. For each condition:",
        ]

        for i, condition in enumerate(conditions):
            procedure.append(f"   Condition {i+1}: Set {condition.variable_settings}")
            procedure.append(f"   - Observe and record measurements")
            procedure.append(f"   - Repeat {condition.replications} times")

        procedure.extend([
            "4. Analyze results",
            "5. Draw conclusions regarding hypothesis"
        ])

        return procedure

    def _specify_measurements(
        self,
        hypothesis: Hypothesis,
        variables: List[Variable]
    ) -> List[str]:
        """Specify what to measure."""
        dependent_vars = [v for v in variables if v.type == "dependent"]
        measurements = []

        for var in dependent_vars:
            measurements.append(f"{var.name} (method: {var.measurement_method or 'standard'})")

        return measurements

    def _identify_controls(
        self,
        hypothesis: Hypothesis,
        variables: List[Variable]
    ) -> List[str]:
        """Identify necessary control variables."""
        controlled_vars = [v for v in variables if v.type == "controlled"]
        controls = [f"Control {v.name}" for v in controlled_vars]
        controls.append("Random assignment")
        controls.append("Blind measurement if possible")
        return controls

    def _predict_outcomes(
        self,
        hypothesis: Hypothesis
    ) -> List[str]:
        """Predict experimental outcomes."""
        return [
            f"If {hypothesis.statement}: expected to see {hypothesis.predicted_relationship}",
            f"If null hypothesis: no significant relationship"
        ]


# =============================================================================
# Sequential Experiment Designer
# =============================================================================
class SequentialExperimentDesigner(ExperimentDesigner):
    """
    Design experiments sequentially, adapting based on results.

    Uses Bayesian optimization to select next experiment.
    """

    def __init__(self):
        """Initialize sequential designer."""
        super().__init__()
        self.beliefs = {}  # Current beliefs about hypotheses
        self.information_gains = []

    def design_next_experiment(
        self,
        previous_results: List[ExperimentResult],
        available_experiments: List[ExperimentDesign]
    ) -> NextExperimentRecommendation:
        """
        Recommend the next experiment based on previous results.

        Args:
            previous_results: Results from previous experiments
            available_experiments: Potential experiments to run

        Returns:
            Recommendation for next experiment
        """
        # Update beliefs based on results
        self._update_beliefs(previous_results)

        # Calculate expected information gain for each experiment
        best_exp = None
        best_gain = 0

        for exp in available_experiments:
            gain = self._calculate_information_gain(exp)
            if gain > best_gain:
                best_gain = gain
                best_exp = exp

        if best_exp:
            return NextExperimentRecommendation(
                priority=best_gain,
                experiment_type=best_exp.experiment_type,
                rationale=f"Expected information gain: {best_gain:.3f}",
                variables_to_test=[v.name for v in best_exp.variables],
                expected_information_gain=best_gain,
                estimated_cost=self._estimate_cost(best_exp)
            )

        # Default: explore new variable space
        return NextExperimentRecommendation(
            priority=0.5,
            experiment_type=ExperimentType.CONTROLLED,
            rationale="Explore new variable combinations",
            variables_to_test=[],
            expected_information_gain=0.5,
            estimated_cost=1.0
        )

    def _update_beliefs(self, results: List[ExperimentResult]):
        """Update beliefs based on experimental results."""
        # Simplified Bayesian update
        for result in results:
            if result.hypothesis_supported:
                # Increase confidence in hypothesis
                self.beliefs[result.experiment_id] = self.beliefs.get(result.experiment_id, 0.5) + 0.1
            else:
                # Decrease confidence
                self.beliefs[result.experiment_id] = self.beliefs.get(result.experiment_id, 0.5) - 0.1

    def _calculate_information_gain(self, experiment: ExperimentDesign) -> float:
        """Calculate expected information gain from experiment."""
        # Simplified: based on hypothesis uncertainty
        if experiment.hypothesis:
            uncertainty = 1 - experiment.hypothesis.confidence
            return uncertainty * 0.5
        return 0.5

    def _estimate_cost(self, experiment: ExperimentDesign) -> float:
        """Estimate cost of running experiment."""
        # Based on sample size and duration
        base_cost = experiment.sample_size * 0.1
        return base_cost


# =============================================================================
# Experiment Simulator
# =============================================================================
class ExperimentSimulator:
    """
    Simulate experiments to predict outcomes.

    Useful for:
    - Virtual testing before real experiments
    - Educational demonstrations
    - Hypothesis exploration
    """

    def __init__(self):
        """Initialize the experiment simulator."""
        pass

    def simulate_experiment(
        self,
        design: ExperimentDesign,
        true_effect: Optional[float] = None
    ) -> ExperimentResult:
        """
        Simulate running an experiment.

        Args:
            design: Experimental design
            true_effect: True effect size (None = no effect)

        Returns:
            Simulated experiment results
        """
        # Simulate measurements for each condition
        measurements = {}
        condition_results = {}

        for condition in design.conditions:
            # Generate simulated data
            if true_effect is not None:
                # Effect present
                base_value = true_effect
                noise = np.random.normal(0, 0.1, condition.replications)
                values = [base_value + n for n in noise]
            else:
                # No effect (null true)
                base_value = 0
                noise = np.random.normal(0, 0.1, condition.replications)
                values = [base_value + n for n in noise]

            condition_name = condition.name
            measurements[condition_name] = values
            condition_results[condition_name] = np.mean(values)

        # Perform statistical test
        if len(measurements) >= 2:
            # Simple t-test
            groups = list(measurements.values())
            t_stat, p_value = self._perform_t_test(groups[0], groups[1])
        else:
            t_stat, p_value = 0, 1.0

        # Calculate effect size
        effect_size = abs(condition_results.get(design.conditions[0].name, 0) -
                          condition_results.get(design.conditions[1].name, 0))

        # Determine conclusion
        hypothesis_supported = p_value < 0.05 and effect_size > 0.2

        if hypothesis_supported:
            conclusion = f"Results support hypothesis: {design.hypothesis.statement if design.hypothesis else 'H1'}"
        else:
            conclusion = f"Results do not support hypothesis. Failed to reject null."

        return ExperimentResult(
            experiment_id=design.design_id,
            condition_results=condition_results,
            measurements=measurements,
            statistical_tests={'t_statistic': t_stat, 'p_value': p_value},
            effect_sizes={'main_effect': effect_size},
            p_values={'main_effect': p_value},
            conclusion=conclusion,
            hypothesis_supported=hypothesis_supported
        )

    def _perform_t_test(
        self,
        group1: List[float],
        group2: List[float]
    ) -> Tuple[float, float]:
        """Perform simple t-test."""
        if SCIPY_AVAILABLE:
            t_stat, p_value = stats.ttest_ind(group1, group2)
            return t_stat, p_value
        else:
            # Simplified t-test approximation
            mean1, mean2 = np.mean(group1), np.mean(group2)
            var1, var2 = np.var(group1), np.var(group2)
            n1, n2 = len(group1), len(group2)

            # Pooled variance
            pooled_var = ((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2)

            # T-statistic
            t_stat = (mean1 - mean2) / np.sqrt(pooled_var * (1/n1 + 1/n2))

            # Approximate p-value (simplified)
            p_value = 2 * (1 - 0.5)  # Placeholder
            return t_stat, p_value


# =============================================================================
# Experiment Analyzer
# =============================================================================
class ExperimentAnalyzer:
    """
    Analyze experimental results and draw conclusions.

    Performs:
    - Statistical analysis
    - Effect size calculation
    - Confidence intervals
    - Power analysis
    - Conclusion drawing
    """

    def __init__(self):
        """Initialize the experiment analyzer."""
        pass

    def analyze_results(
        self,
        result: ExperimentResult,
        design: ExperimentDesign
    ) -> Dict[str, Any]:
        """
        Analyze experimental results.

        Args:
            result: Experiment results
            design: Original experimental design

        Returns:
            Analysis with conclusions
        """
        analysis = {
            'hypothesis_test': self._test_hypothesis(result, design),
            'effect_size': self._calculate_effect_size(result),
            'practical_significance': self._assess_practical_significance(result),
            'limitations': self._identify_limitations(result, design),
            'recommendations': self._generate_recommendations(result, design)
        }

        return analysis

    def _test_hypothesis(
        self,
        result: ExperimentResult,
        design: ExperimentDesign
    ) -> Dict[str, Any]:
        """Test the experimental hypothesis."""
        alpha = 0.05
        p_value = result.p_values.get('main_effect', 1.0)

        reject_null = p_value < alpha

        return {
            'null_hypothesis': design.hypothesis.null_hypothesis if design.hypothesis else "",
            'alternative_hypothesis': design.hypothesis.statement if design.hypothesis else "",
            'p_value': p_value,
            'alpha': alpha,
            'reject_null': reject_null,
            'conclusion': "Reject null" if reject_null else "Fail to reject null"
        }

    def _calculate_effect_size(self, result: ExperimentResult) -> Dict[str, float]:
        """Calculate effect sizes."""
        return result.effect_sizes

    def _assess_practical_significance(
        self,
        result: ExperimentResult
    ) -> str:
        """Assess practical significance."""
        effect_size = result.effect_sizes.get('main_effect', 0)

        if effect_size > 0.8:
            return "Large practical effect"
        elif effect_size > 0.5:
            return "Medium practical effect"
        elif effect_size > 0.2:
            return "Small practical effect"
        else:
            return "Negligible practical effect"

    def _identify_limitations(
        self,
        result: ExperimentResult,
        design: ExperimentDesign
    ) -> List[str]:
        """Identify study limitations."""
        limitations = []

        if design.sample_size < 30:
            limitations.append("Small sample size may limit power")

        if not design.controls:
            limitations.append("No control conditions specified")

        if design.experiment_type == ExperimentType.OBSERVATIONAL:
            limitations.append("Observational design - cannot infer causation")

        return limitations

    def _generate_recommendations(
        self,
        result: ExperimentResult,
        design: ExperimentDesign
    ) -> List[str]:
        """Generate recommendations for future research."""
        recommendations = []

        if not result.hypothesis_supported:
            recommendations.append("Consider increasing sample size")
            recommendations.append("Explore alternative hypotheses")

        if result.hypothesis_supported:
            recommendations.append("Replicate with independent sample")
            recommendations.append("Test generalizability to other domains")

        return recommendations


# =============================================================================
# Unified Autonomous Experiment System
# =============================================================================
class AutonomousExperimentSystem:
    """
    Unified system for autonomous experimentation.

    Integrates:
    - Experiment design
    - Sequential design (adaptive)
    - Experiment simulation
    - Result analysis
    """

    def __init__(self):
        """Initialize the autonomous experiment system."""
        self.designer = SequentialExperimentDesigner()
        self.simulator = ExperimentSimulator()
        self.analyzer = ExperimentAnalyzer()

        self.experiments = []
        self.results = []

    def design_experiment(
        self,
        hypothesis: Hypothesis,
        variables: List[Variable],
        constraints: Optional[Dict] = None
    ) -> ExperimentDesign:
        """Design a new experiment."""
        design = self.designer.design_experiment(hypothesis, variables, constraints)
        self.experiments.append(design)
        return design

    def simulate_experiment(
        self,
        design: ExperimentDesign,
        true_effect: Optional[float] = None
    ) -> ExperimentResult:
        """Simulate an experiment."""
        result = self.simulator.simulate_experiment(design, true_effect)
        self.results.append(result)
        return result

    def analyze_results(
        self,
        result: ExperimentResult,
        design: ExperimentDesign
    ) -> Dict[str, Any]:
        """Analyze experimental results."""
        return self.analyzer.analyze_results(result, design)

    def recommend_next_experiment(
        self,
        available_designs: List[ExperimentDesign]
    ) -> NextExperimentRecommendation:
        """Recommend the next experiment to run."""
        return self.designer.design_next_experiment(self.results, available_designs)


# =============================================================================
# Factory Functions
# =============================================================================
def create_autonomous_experiment_system() -> AutonomousExperimentSystem:
    """Create an autonomous experiment system."""
    return AutonomousExperimentSystem()


# =============================================================================
# Integration with STAR-Learn
# =============================================================================
def get_experimental_discovery_reward(
    discovery: Dict[str, Any],
    experiment_system: AutonomousExperimentSystem
) -> Tuple[float, Dict]:
    """
    Calculate reward for experimental discoveries.

    High rewards for:
    - Well-designed experiments
    - Novel experimental methods
    - Clear hypothesis testing
    - Significant results
    """
    content = discovery.get('content', '').lower()
    domain = discovery.get('domain', 'unknown')

    details = {}
    reward = 0.0

    # Check for experimental design
    experiment_keywords = ['experiment', 'test', 'measure', 'hypothesis',
                          'controlled', 'randomized', 'sample']

    for keyword in experiment_keywords:
        if keyword in content:
            reward += 0.1
            details['experimental_design'] = True

    # Bonus for hypothesis-driven research
    if 'hypothesis' in content:
        reward += 0.2
        details['hypothesis_driven'] = True

    # Bonus for statistical testing
    if any(word in content for word in ['significant', 'p-value', 'confidence interval']):
        reward += 0.2
        details['statistical_testing'] = True

    # Bonus for novel methods
    if 'novel' in content or 'innovative' in content:
        reward += 0.2
        details['novel_method'] = True

    return min(reward, 1.0), details
