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
Experimental Design Simulator for V92
======================================

Automated experimental design and simulation capabilities.
This module allows V92 to design optimal experiments to test hypotheses
and simulate their outcomes before real-world execution.

Capabilities:
- Generate experimental designs to test hypotheses
- Power analysis and sample size calculation
- Control group and treatment assignment
- Factorial and response surface designs
- Experimental confound control
- Outcome variable selection
- Experimental cost optimization
- Simulation of experimental outcomes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from collections import defaultdict
import itertools
import math
from abc import ABC, abstractmethod
from scipy import stats


class ExperimentalType(Enum):
    """Types of experimental designs"""
    RANDOMIZED_CONTROLLED = "randomized_controlled"      # RCT design
    FACTORIAL = "factorial"                              # Factorial design
    REPEATED_MEASURES = "repeated_measures"             # Within-subjects
    QUASI_EXPERIMENTAL = "quasi_experimental"            # Natural experiments
    RESPONSE_SURFACE = "response_surface"                # RSM designs
    OPTIMAL_DESIGN = "optimal_design"                    # Optimal designs
    ADAPTIVE = "adaptive"                                # Adaptive trials
    OBSERVATIONAL = "observational"                      # Observational studies


class RandomizationType(Enum):
    """Randomization strategies"""
    SIMPLE = "simple"                                    # Simple randomization
    BLOCK = "block"                                      # Block randomization
    STRATIFIED = "stratified"                            # Stratified randomization
    CLUSTER = "cluster"                                  # Cluster randomization
    MINIMIZATION = "minimization"                        # Minimization
    ADAPTIVE = "adaptive"                                # Adaptive randomization


class HypothesisType(Enum):
    """Types of hypotheses to test"""
    CAUSAL = "causal"                                    # X causes Y
    ASSOCIATION = "association"                          # X associated with Y
    DIFFERENCE = "difference"                            # Group differences
    INTERACTION = "interaction"                          # Interaction effects
    DOSE_RESPONSE = "dose_response"                      # Dose-response relationship
    NON_INFERIORITY = "non_inferiority"                  # Non-inferiority tests


@dataclass
class ExperimentalVariable:
    """An experimental variable (factor or outcome)"""
    name: str
    variable_type: str  # 'independent', 'dependent', 'covariate', 'control'
    data_type: str  # 'continuous', 'categorical', 'binary', 'count'
    levels: List[Any] = field(default_factory=list)  # For categorical variables
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    expected_effect_size: Optional[float] = None
    cost_per_measurement: float = 0.0
    measurement_error: float = 0.0
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Treatment:
    """A treatment condition in an experiment"""
    name: str
    description: str
    level_values: Dict[str, Any] = field(default_factory=dict)
    expected_effect: Dict[str, float] = field(default_factory=dict)
    cost_per_subject: float = 0.0
    risk_level: float = 0.0


@dataclass
class ExperimentalCondition:
    """A condition in the experiment"""
    treatment: Treatment
    sample_size: int
    allocation_ratio: float = 1.0
    stratification_factors: List[str] = field(default_factory=list)


@dataclass
class ExperimentalDesign:
    """Complete experimental design"""
    name: str
    hypothesis: str
    design_type: ExperimentalType
    independent_variables: List[ExperimentalVariable] = field(default_factory=list)
    dependent_variables: List[ExperimentalVariable] = field(default_factory=list)
    covariates: List[ExperimentalVariable] = field(default_factory=list)
    conditions: List[ExperimentalCondition] = field(default_factory=list)
    sample_size: int = 0
    randomization_type: RandomizationType = RandomizationType.SIMPLE
    blocking_factors: List[str] = field(default_factory=list)
    stratification_factors: List[str] = field(default_factory=list)
    control_confounders: List[str] = field(default_factory=list)
    statistical_power: float = 0.8
    significance_level: float = 0.05
    expected_duration: float = 0.0  # in time units
    estimated_cost: float = 0.0
    ethical_considerations: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class SimulationResult:
    """Result of experimental simulation"""
    design: ExperimentalDesign
    simulated_data: pd.DataFrame
    treatment_effects: Dict[str, float]
    statistical_tests: Dict[str, Dict[str, Any]]
    power_analysis: Dict[str, float]
    cost_benefit: Dict[str, float]
    recommendations: List[str] = field(default_factory=list)
    success_probability: float = 0.0


class ExperimentalDesignEngine:
    """
    Automated experimental design and simulation.

    This module creates optimal experimental designs to test
    hypotheses and simulates their likely outcomes.
    """

    def __init__(self):
        self.design_generators = {
            ExperimentalType.RANDOMIZED_CONTROLLED: self._generate_rct_design,
            ExperimentalType.FACTORIAL: self._generate_factorial_design,
            ExperimentalType.REPEATED_MEASURES: self._generate_repeated_measures_design,
            ExperimentalType.RESPONSE_SURFACE: self._generate_rsm_design,
            ExperimentalType.OPTIMAL_DESIGN: self._generate_optimal_design
        }

        self.simulation_engines = {
            'monte_carlo': MonteCarloSimulator(),
            'bootstrap': BootstrapSimulator(),
            'analytical': AnalyticalSimulator()
        }

        self.power_calculators = {
            't_test': TTestPowerCalculator(),
            'anova': ANOVAPowerCalculator(),
            'regression': RegressionPowerCalculator(),
            'chi2': ChiSquarePowerCalculator()
        }

    def design_experiment(self,
                         hypothesis: str,
                         variables: List[ExperimentalVariable],
                         design_type: ExperimentalType = ExperimentalType.RANDOMIZED_CONTROLLED,
                         constraints: Optional[Dict[str, Any]] = None) -> ExperimentalDesign:
        """Generate optimal experimental design for hypothesis testing"""
        print(f"Designing {design_type.value} experiment to test: {hypothesis}")

        # Categorize variables
        independent_vars = [v for v in variables if v.variable_type == 'independent']
        dependent_vars = [v for v in variables if v.variable_type == 'dependent']
        covariates = [v for v in variables if v.variable_type == 'covariate']

        # Generate design using appropriate generator
        design = self.design_generators[design_type](
            hypothesis, independent_vars, dependent_vars, covariates, constraints
        )

        # Optimize design
        design = self._optimize_design(design, constraints)

        return design

    def calculate_sample_size(self,
                            design: ExperimentalDesign,
                            effect_size: float,
                            power: float = 0.8,
                            alpha: float = 0.05) -> int:
        """Calculate required sample size"""
        if len(design.independent_variables) == 1 and len(design.dependent_variables) == 1:
            # Simple t-test
            iv = design.independent_variables[0]
            dv = design.dependent_variables[0]

            if iv.data_type == 'categorical' and len(iv.levels) == 2:
                # Two-sample t-test
                n_per_group = self._calculate_ttest_sample_size(effect_size, power, alpha)
                return n_per_group * len(design.conditions)
            elif iv.data_type == 'continuous':
                # Correlation or regression
                return self._calculate_correlation_sample_size(effect_size, power, alpha)

        # For more complex designs, use simulation or approximation
        return self._estimate_complex_sample_size(design, effect_size, power, alpha)

    def simulate_experiment(self,
                          design: ExperimentalDesign,
                          true_effects: Optional[Dict[str, float]] = None,
                          n_simulations: int = 1000) -> SimulationResult:
        """Simulate experimental outcomes"""
        print(f"Simulating {n_simulations} runs of experiment...")

        # Choose simulation engine
        if design.design_type in [ExperimentalType.RANDOMIZED_CONTROLLED, ExperimentalType.FACTORIAL]:
            simulator = self.simulation_engines['monte_carlo']
        else:
            simulator = self.simulation_engines['analytical']

        # Run simulation
        result = simulator.simulate(design, true_effects, n_simulations)

        # Add recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def optimize_design(self,
                       initial_design: ExperimentalDesign,
                       objectives: List[str] = ['power', 'cost', 'feasibility']) -> ExperimentalDesign:
        """Optimize experimental design"""
        design = initial_design.copy() if hasattr(initial_design, 'copy') else initial_design

        # Multi-objective optimization
        for objective in objectives:
            if objective == 'power':
                design = self._optimize_for_power(design)
            elif objective == 'cost':
                design = self._optimize_for_cost(design)
            elif objective == 'feasibility':
                design = self._optimize_for_feasibility(design)

        return design

    def _generate_rct_design(self,
                           hypothesis: str,
                           independent_vars: List[ExperimentalVariable],
                           dependent_vars: List[ExperimentalVariable],
                           covariates: List[ExperimentalVariable],
                           constraints: Optional[Dict[str, Any]] = None) -> ExperimentalDesign:
        """Generate Randomized Controlled Trial design"""
        # Default RCT with one treatment and one control
        if not independent_vars:
            iv = ExperimentalVariable(
                name="treatment",
                variable_type="independent",
                data_type="categorical",
                levels=["control", "treatment"]
            )
            independent_vars = [iv]

        # Create treatments
        treatments = []
        iv = independent_vars[0]
        for level in iv.levels:
            treatment = Treatment(
                name=f"treatment_{level}",
                description=f"Condition: {level}",
                level_values={iv.name: level}
            )
            treatments.append(treatment)

        # Create conditions
        conditions = []
        for treatment in treatments:
            condition = ExperimentalCondition(
                treatment=treatment,
                sample_size=50,  # Default
                allocation_ratio=1.0
            )
            conditions.append(condition)

        return ExperimentalDesign(
            name=f"RCT_for_{hypothesis[:30]}",
            hypothesis=hypothesis,
            design_type=ExperimentalType.RANDOMIZED_CONTROLLED,
            independent_variables=independent_vars,
            dependent_variables=dependent_vars,
            covariates=covariates,
            conditions=conditions,
            randomization_type=RandomizationType.SIMPLE,
            statistical_power=0.8,
            significance_level=0.05
        )

    def _generate_factorial_design(self,
                                 hypothesis: str,
                                 independent_vars: List[ExperimentalVariable],
                                 dependent_vars: List[ExperimentalVariable],
                                 covariates: List[ExperimentalVariable],
                                 constraints: Optional[Dict[str, Any]] = None) -> ExperimentalDesign:
        """Generate factorial experimental design"""
        # Create all combinations of factor levels
        factor_levels = [var.levels for var in independent_vars]
        level_combinations = list(itertools.product(*factor_levels))

        # Create treatments for each combination
        treatments = []
        for i, combination in enumerate(level_combinations):
            treatment = Treatment(
                name=f"treatment_{i}",
                description=f"Combination: {dict(zip([v.name for v in independent_vars], combination))}",
                level_values=dict(zip([v.name for v in independent_vars], combination))
            )
            treatments.append(treatment)

        # Create conditions
        conditions = []
        for treatment in treatments:
            condition = ExperimentalCondition(
                treatment=treatment,
                sample_size=30,  # Per cell
                allocation_ratio=1.0
            )
            conditions.append(condition)

        return ExperimentalDesign(
            name=f"Factorial_for_{hypothesis[:30]}",
            hypothesis=hypothesis,
            design_type=ExperimentalType.FACTORIAL,
            independent_variables=independent_vars,
            dependent_variables=dependent_vars,
            covariates=covariates,
            conditions=conditions,
            randomization_type=RandomizationType.SIMPLE,
            statistical_power=0.8,
            significance_level=0.05
        )

    def _generate_repeated_measures_design(self,
                                         hypothesis: str,
                                         independent_vars: List[ExperimentalVariable],
                                         dependent_vars: List[ExperimentalVariable],
                                         covariates: List[ExperimentalVariable],
                                         constraints: Optional[Dict[str, Any]] = None) -> ExperimentalDesign:
        """Generate repeated measures design"""
        # Within-subjects design
        conditions = []
        iv = independent_vars[0] if independent_vars else \
            ExperimentalVariable("time", "independent", "categorical", levels=["pre", "post"])

        for level in iv.levels:
            treatment = Treatment(
                name=f"condition_{level}",
                description=f"Time point: {level}",
                level_values={iv.name: level}
            )
            condition = ExperimentalCondition(
                treatment=treatment,
                sample_size=50,  # Number of subjects
                allocation_ratio=1.0
            )
            conditions.append(condition)

        return ExperimentalDesign(
            name=f"RepeatedMeasures_for_{hypothesis[:30]}",
            hypothesis=hypothesis,
            design_type=ExperimentalType.REPEATED_MEASURES,
            independent_variables=[iv],
            dependent_variables=dependent_vars,
            covariates=covariates,
            conditions=conditions,
            randomization_type=RandomizationType.SIMPLE,
            statistical_power=0.8,
            significance_level=0.05
        )

    def _generate_rsm_design(self,
                           hypothesis: str,
                           independent_vars: List[ExperimentalVariable],
                           dependent_vars: List[ExperimentalVariable],
                           covariates: List[ExperimentalVariable],
                           constraints: Optional[Dict[str, Any]] = None) -> ExperimentalDesign:
        """Generate Response Surface Methodology design"""
        # Central Composite Design for two factors
        if len(independent_vars) >= 2:
            # Create factorial points
            factorial_points = list(itertools.product([-1, 1], repeat=len(independent_vars)))

            # Create axial points
            axial_points = []
            for i in range(len(independent_vars)):
                for alpha in [-1.414, 1.414]:  # Alpha for rotatability
                    point = [0] * len(independent_vars)
                    point[i] = alpha
                    axial_points.append(tuple(point))

            # Combine all points
            all_points = factorial_points + axial_points + [(0,) * len(independent_vars)]  # Center point

            treatments = []
            for i, point in enumerate(all_points):
                level_values = {}
                for j, var in enumerate(independent_vars):
                    if var.data_type == 'continuous':
                        value = var.min_value + (point[j] + 1) * (var.max_value - var.min_value) / 2
                        level_values[var.name] = value

                treatment = Treatment(
                    name=f"rsm_point_{i}",
                    description=f"RSM point: {point}",
                    level_values=level_values
                )
                treatments.append(treatment)

            conditions = []
            for treatment in treatments:
                condition = ExperimentalCondition(
                    treatment=treatment,
                    sample_size=5,  # Replicates per point
                    allocation_ratio=1.0
                )
                conditions.append(condition)

            return ExperimentalDesign(
                name=f"RSM_for_{hypothesis[:30]}",
                hypothesis=hypothesis,
                design_type=ExperimentalType.RESPONSE_SURFACE,
                independent_variables=independent_vars,
                dependent_variables=dependent_vars,
                covariates=covariates,
                conditions=conditions,
                randomization_type=RandomizationType.SIMPLE,
                statistical_power=0.8,
                significance_level=0.05
            )

        # Fallback to RCT
        return self._generate_rct_design(hypothesis, independent_vars, dependent_vars, covariates, constraints)

    def _generate_optimal_design(self,
                               hypothesis: str,
                               independent_vars: List[ExperimentalVariable],
                               dependent_vars: List[ExperimentalVariable],
                               covariates: List[ExperimentalVariable],
                               constraints: Optional[Dict[str, Any]] = None) -> ExperimentalDesign:
        """Generate optimal experimental design"""
        # D-optimal design (simplified)
        # Generate candidate points
        candidate_points = []
        if independent_vars:
            # For continuous variables, use extreme values and center
            for var in independent_vars:
                if var.data_type == 'continuous':
                    candidate_points.append(var.min_value)
                    candidate_points.append(var.max_value)
                    candidate_points.append((var.min_value + var.max_value) / 2)

        # Select optimal subset (simplified - would use optimization)
        optimal_points = candidate_points[:min(len(candidate_points), 5)]

        treatments = []
        for i, point in enumerate(optimal_points):
            treatment = Treatment(
                name=f"optimal_{i}",
                description=f"Optimal design point {i}",
                level_values={independent_vars[0].name: point} if independent_vars else {}
            )
            treatments.append(treatment)

        conditions = []
        for treatment in treatments:
            condition = ExperimentalCondition(
                treatment=treatment,
                sample_size=20,
                allocation_ratio=1.0
            )
            conditions.append(condition)

        return ExperimentalDesign(
            name=f"Optimal_for_{hypothesis[:30]}",
            hypothesis=hypothesis,
            design_type=ExperimentalType.OPTIMAL_DESIGN,
            independent_variables=independent_vars,
            dependent_variables=dependent_vars,
            covariates=covariates,
            conditions=conditions,
            randomization_type=RandomizationType.SIMPLE,
            statistical_power=0.8,
            significance_level=0.05
        )

    def _optimize_design(self, design: ExperimentalDesign, constraints: Optional[Dict[str, Any]]) -> ExperimentalDesign:
        """Optimize experimental design"""
        if constraints:
            # Apply constraints
            if 'max_sample_size' in constraints:
                total_n = sum(c.sample_size for c in design.conditions)
                if total_n > constraints['max_sample_size']:
                    # Scale down proportionally
                    scale_factor = constraints['max_sample_size'] / total_n
                    for condition in design.conditions:
                        condition.sample_size = int(condition.sample_size * scale_factor)

            if 'max_cost' in constraints:
                total_cost = self._calculate_total_cost(design)
                if total_cost > constraints['max_cost']:
                    # Adjust sample size to meet cost constraint
                    scale_factor = constraints['max_cost'] / total_cost
                    for condition in design.conditions:
                        condition.sample_size = int(condition.sample_size * scale_factor)

        # Calculate total sample size
        design.sample_size = sum(c.sample_size for c in design.conditions)

        # Calculate estimated cost and duration
        design.estimated_cost = self._calculate_total_cost(design)
        design.expected_duration = self._estimate_duration(design)

        return design

    def _calculate_total_cost(self, design: ExperimentalDesign) -> float:
        """Calculate total experimental cost"""
        total_cost = 0.0

        # Variable measurement costs
        all_vars = design.independent_variables + design.dependent_variables + design.covariates
        for var in all_vars:
            total_cost += var.cost_per_measurement * design.sample_size

        # Treatment costs
        for condition in design.conditions:
            total_cost += condition.treatment.cost_per_subject * condition.sample_size

        # Add overhead
        total_cost *= 1.2  # 20% overhead

        return total_cost

    def _estimate_duration(self, design: ExperimentalDesign) -> float:
        """Estimate experimental duration"""
        # Simplified duration calculation
        base_duration = 1.0  # Base duration in time units

        # More conditions take longer
        if len(design.conditions) > 2:
            base_duration *= 1.5

        # Repeated measures may take longer
        if design.design_type == ExperimentalType.REPEATED_MEASURES:
            base_duration *= 2.0

        return base_duration

    def _calculate_ttest_sample_size(self, effect_size: float, power: float, alpha: float) -> int:
        """Calculate sample size for t-test"""
        from scipy.stats import norm

        # Two-sided test
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)

        # Pooled standard deviation assumed to be 1
        n = 2 * (z_alpha + z_beta)**2 / effect_size**2

        return int(np.ceil(n))

    def _calculate_correlation_sample_size(self, effect_size: float, power: float, alpha: float) -> int:
        """Calculate sample size for correlation test"""
        from scipy.stats import norm

        # Fisher's z transformation
        z_effect = 0.5 * np.log((1 + effect_size) / (1 - effect_size))
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)

        n = (z_alpha + z_beta)**2 / z_effect**2 + 3

        return int(np.ceil(n))

    def _estimate_complex_sample_size(self, design: ExperimentalDesign, effect_size: float,
                                    power: float, alpha: float) -> int:
        """Estimate sample size for complex designs"""
        # Rule of thumb for complex designs
        base_n = self._calculate_ttest_sample_size(effect_size, power, alpha)

        # Adjust for design complexity
        if len(design.independent_variables) > 1:
            base_n *= len(design.independent_variables)

        if len(design.conditions) > 2:
            base_n *= np.sqrt(len(design.conditions))

        return int(np.ceil(base_n))

    def _optimize_for_power(self, design: ExperimentalDesign) -> ExperimentalDesign:
        """Optimize design for statistical power"""
        # Increase sample size if power is below target
        if design.statistical_power < 0.8:
            scale_factor = 0.8 / design.statistical_power
            for condition in design.conditions:
                condition.sample_size = int(condition.sample_size * scale_factor)

        return design

    def _optimize_for_cost(self, design: ExperimentalDesign) -> ExperimentalDesign:
        """Optimize design for cost efficiency"""
        # Remove expensive measurements if possible
        expensive_vars = [v for v in design.dependent_variables if v.cost_per_measurement > 100]
        for var in expensive_vars:
            if len(design.dependent_variables) > 1:
                design.dependent_variables.remove(var)

        return design

    def _optimize_for_feasibility(self, design: ExperimentalDesign) -> ExperimentalDesign:
        """Optimize design for practical feasibility"""
        # Limit number of conditions for practicality
        if len(design.conditions) > 10:
            # Merge similar conditions
            merged_conditions = design.conditions[:5]  # Keep first 5
            design.conditions = merged_conditions

        return design

    def _generate_recommendations(self, simulation_result: SimulationResult) -> List[str]:
        """Generate recommendations based on simulation results"""
        recommendations = []

        # Power recommendations
        if simulation_result.power_analysis.get('average_power', 0) < 0.8:
            recommendations.append("Consider increasing sample size to achieve adequate power")

        # Cost recommendations
        if simulation_result.cost_benefit.get('cost_per_effect', float('inf')) > 1000:
            recommendations.append("Experimental cost per effect size is high - consider design simplification")

        # Effect size recommendations
        avg_effect = np.mean(list(simulation_result.treatment_effects.values())) if simulation_result.treatment_effects else 0
        if abs(avg_effect) < 0.2:
            recommendations.append("Expected effect size is small - consider increasing precision or focusing on larger effects")

        # Design recommendations
        design = simulation_result.design
        if len(design.conditions) > 5:
            recommendations.append("Consider reducing number of experimental conditions for better feasibility")

        return recommendations

    def get_design_statistics(self) -> Dict[str, Any]:
        """Get statistics about experimental design capabilities"""
        return {
            'available_designs': list(self.design_generators.keys()),
            'simulation_engines': list(self.simulation_engines.keys()),
            'power_calculators': list(self.power_calculators.keys())
        }


# Simulation Engines

class MonteCarloSimulator:
    """Monte Carlo simulation engine"""

    def simulate(self, design: ExperimentalDesign, true_effects: Optional[Dict[str, float]],
                n_simulations: int) -> SimulationResult:
        """Run Monte Carlo simulation"""
        simulated_data = []
        treatment_effects = {}
        statistical_tests = {}
        power_analysis = {}

        # Simulate each run
        p_values = []
        for sim in range(n_simulations):
            # Generate data for this simulation
            data = self._generate_single_simulation(design, true_effects, sim)
            simulated_data.append(data)

            # Analyze results
            test_result = self._analyze_simulation(data, design)
            p_values.append(test_result.get('p_value', 1.0))

        # Calculate power
        power = np.mean(np.array(p_values) < 0.05) if p_values else 0
        power_analysis['average_power'] = power

        # Combine all simulated data
        all_data = pd.concat(simulated_data, ignore_index=True)

        # Estimate treatment effects
        for condition in design.conditions:
            condition_data = all_data[all_data['treatment'] == condition.treatment.name]
            if len(condition_data) > 0 and len(design.dependent_variables) > 0:
                dv = design.dependent_variables[0]
                if dv.name in condition_data.columns:
                    treatment_effects[condition.treatment.name] = condition_data[dv.name].mean()

        return SimulationResult(
            design=design,
            simulated_data=all_data,
            treatment_effects=treatment_effects,
            statistical_tests=statistical_tests,
            power_analysis=power_analysis,
            cost_benefit={'cost_per_effect': design.estimated_cost / max(0.1, np.mean(list(treatment_effects.values())) if treatment_effects else 1)},
            success_probability=power
        )

    def _generate_single_simulation(self, design: ExperimentalDesign,
                                   true_effects: Optional[Dict[str, float]], seed: int) -> pd.DataFrame:
        """Generate single simulation run"""
        np.random.seed(seed)
        data = []

        for condition in design.conditions:
            for subject in range(condition.sample_size):
                row = {'subject_id': f"sub_{condition.treatment.name}_{subject}",
                       'treatment': condition.treatment.name}

                # Add independent variables
                for var in design.independent_variables:
                    if var.name in condition.treatment.level_values:
                        row[var.name] = condition.treatment.level_values[var.name]
                    else:
                        # Random value within range
                        if var.data_type == 'continuous':
                            row[var.name] = np.random.uniform(var.min_value or 0, var.max_value or 1)
                        elif var.data_type == 'categorical':
                            row[var.name] = np.random.choice(var.levels)

                # Add dependent variables (with treatment effects)
                for var in design.dependent_variables:
                    base_value = 0.0

                    # Add treatment effect
                    effect_key = condition.treatment.name
                    if true_effects and effect_key in true_effects:
                        base_value += true_effects[effect_key]

                    # Add noise
                    noise = np.random.normal(0, 1)  # Standard normal noise
                    row[var.name] = base_value + noise

                data.append(row)

        return pd.DataFrame(data)

    def _analyze_simulation(self, data: pd.DataFrame, design: ExperimentalDesign) -> Dict[str, Any]:
        """Analyze single simulation results"""
        # Simplified analysis - would use appropriate statistical tests
        if len(design.conditions) == 2 and len(design.dependent_variables) == 1:
            # Two-group comparison
            dv_name = design.dependent_variables[0].name
            group1 = data[data['treatment'] == design.conditions[0].treatment.name][dv_name]
            group2 = data[data['treatment'] == design.conditions[1].treatment.name][dv_name]

            if len(group1) > 0 and len(group2) > 0:
                from scipy.stats import ttest_ind
                t_stat, p_value = ttest_ind(group1, group2)
                return {'t_statistic': t_stat, 'p_value': p_value}

        return {'p_value': 1.0}


class BootstrapSimulator:
    """Bootstrap simulation engine"""

    def simulate(self, design: ExperimentalDesign, true_effects: Optional[Dict[str, float]],
                n_simulations: int) -> SimulationResult:
        """Run bootstrap simulation"""
        # Simplified bootstrap implementation
        return MonteCarloSimulator().simulate(design, true_effects, n_simulations)


class AnalyticalSimulator:
    """Analytical simulation engine"""

    def simulate(self, design: ExperimentalDesign, true_effects: Optional[Dict[str, float]],
                n_simulations: int) -> SimulationResult:
        """Run analytical simulation"""
        # Calculate expected values analytically
        treatment_effects = true_effects or {}

        # Generate expected data
        data = self._generate_expected_data(design, treatment_effects)

        return SimulationResult(
            design=design,
            simulated_data=data,
            treatment_effects=treatment_effects,
            statistical_tests={},
            power_analysis={'analytical_power': design.statistical_power},
            cost_benefit={'cost_per_effect': design.estimated_cost / max(0.1, np.mean(list(treatment_effects.values())) if treatment_effects else 1)},
            success_probability=design.statistical_power
        )

    def _generate_expected_data(self, design: ExperimentalDesign, true_effects: Dict[str, float]) -> pd.DataFrame:
        """Generate expected data based on design"""
        data = []

        for condition in design.conditions:
            for subject in range(condition.sample_size):
                row = {'subject_id': f"sub_{condition.treatment.name}_{subject}",
                       'treatment': condition.treatment.name}

                # Add variables
                for var in design.independent_variables:
                    if var.name in condition.treatment.level_values:
                        row[var.name] = condition.treatment.level_values[var.name]

                for var in design.dependent_variables:
                    base_value = true_effects.get(condition.treatment.name, 0)
                    row[var.name] = base_value

                data.append(row)

        return pd.DataFrame(data)


# Power Calculators

class TTestPowerCalculator:
    """Power calculator for t-tests"""

    def calculate(self, effect_size: float, n: int, alpha: float = 0.05) -> float:
        """Calculate statistical power"""
        from scipy.stats import norm, t

        df = n - 1
        t_crit = t.ppf(1 - alpha/2, df)
        ncp = effect_size * np.sqrt(n/2)  # Non-centrality parameter

        # Power calculation
        power = 1 - t.cdf(t_crit, df, ncp) + t.cdf(-t_crit, df, ncp)

        return power


class ANOVAPowerCalculator:
    """Power calculator for ANOVA"""

    def calculate(self, effect_size: float, n: int, groups: int, alpha: float = 0.05) -> float:
        """Calculate statistical power for ANOVA"""
        from scipy.stats import f

        df_between = groups - 1
        df_within = groups * (n - 1)
        f_crit = f.ppf(1 - alpha, df_between, df_within)

        # Non-centrality parameter
        ncp = groups * n * effect_size**2 / 2

        # Power calculation
        power = 1 - f.cdf(f_crit, df_between, df_within, ncp)

        return power


class RegressionPowerCalculator:
    """Power calculator for regression"""

    def calculate(self, effect_size: float, n: int, predictors: int, alpha: float = 0.05) -> float:
        """Calculate statistical power for regression"""
        from scipy.stats import f

        df_model = predictors
        df_error = n - predictors - 1
        f_crit = f.ppf(1 - alpha, df_model, df_error)

        # Effect size as R²
        r_squared = effect_size**2
        ncp = r_squared * df_error / (1 - r_squared)

        # Power calculation
        power = 1 - f.cdf(f_crit, df_model, df_error, ncp)

        return power


class ChiSquarePowerCalculator:
    """Power calculator for chi-square tests"""

    def calculate(self, effect_size: float, n: int, df: int, alpha: float = 0.05) -> float:
        """Calculate statistical power for chi-square test"""
        from scipy.stats import chi2

        chi2_crit = chi2.ppf(1 - alpha, df)
        ncp = n * effect_size**2  # Non-centrality parameter

        # Power calculation
        power = 1 - chi2.cdf(chi2_crit, df, ncp)

        return power