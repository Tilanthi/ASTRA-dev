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
Quantitative Reasoner for STAN V40

Provides statistical reasoning, probability calculations, dimensional
analysis, and numerical estimation capabilities.

This addresses the gap in quantitative reasoning for Math and Physics
problems requiring statistical interpretation and numerical analysis.

Date: 2025-12-11
"""

import re
import math
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class StatisticalTestType(Enum):
    """Types of statistical tests"""
    T_TEST_ONE_SAMPLE = "t_test_one_sample"
    T_TEST_TWO_SAMPLE = "t_test_two_sample"
    T_TEST_PAIRED = "t_test_paired"
    ANOVA_ONE_WAY = "anova_one_way"
    ANOVA_TWO_WAY = "anova_two_way"
    CHI_SQUARE_GOODNESS = "chi_square_goodness"
    CHI_SQUARE_INDEPENDENCE = "chi_square_independence"
    MANN_WHITNEY_U = "mann_whitney_u"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    KRUSKAL_WALLIS = "kruskal_wallis"
    PEARSON_CORRELATION = "pearson_correlation"
    SPEARMAN_CORRELATION = "spearman_correlation"
    LINEAR_REGRESSION = "linear_regression"
    FISHER_EXACT = "fisher_exact"
    Z_TEST = "z_test"


class DistributionType(Enum):
    """Common probability distributions"""
    NORMAL = "normal"
    BINOMIAL = "binomial"
    POISSON = "poisson"
    EXPONENTIAL = "exponential"
    UNIFORM = "uniform"
    CHI_SQUARE = "chi_square"
    T_DISTRIBUTION = "t_distribution"
    F_DISTRIBUTION = "f_distribution"
    BETA = "beta"
    GAMMA = "gamma"


class UnitDimension(Enum):
    """Fundamental physical dimensions"""
    LENGTH = "L"
    MASS = "M"
    TIME = "T"
    CURRENT = "I"
    TEMPERATURE = "Θ"
    AMOUNT = "N"
    LUMINOSITY = "J"
    DIMENSIONLESS = "1"


@dataclass
class StatisticalTestRecommendation:
    """Recommendation for which statistical test to use"""
    test_type: StatisticalTestType
    confidence: float
    rationale: str
    assumptions: List[str]
    alternatives: List[StatisticalTestType] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)


@dataclass
class StatisticalInterpretation:
    """Interpretation of a statistical result"""
    test_type: StatisticalTestType
    statistic_value: float
    p_value: float
    is_significant: bool
    significance_level: float
    interpretation: str
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    practical_significance: str = ""


@dataclass
class DimensionalAnalysisResult:
    """Result of dimensional analysis"""
    expression: str
    dimensions: Dict[UnitDimension, int]
    is_dimensionally_consistent: bool
    simplified_units: str
    issues: List[str] = field(default_factory=list)


@dataclass
class ProbabilityResult:
    """Result of probability calculation"""
    probability: float
    method: str
    steps: List[str] = field(default_factory=list)
    distribution_used: Optional[DistributionType] = None
    parameters: Dict[str, float] = field(default_factory=dict)


@dataclass
class NumericalEstimate:
    """A numerical estimate with uncertainty"""
    value: float
    uncertainty: float
    confidence_level: float
    method: str
    bounds: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))


class StatisticalTestSelector:
    """Select appropriate statistical test based on problem characteristics"""

    def __init__(self):
        self.decision_tree = self._build_decision_tree()

    def _build_decision_tree(self) -> Dict:
        """Build decision tree for test selection"""
        return {
            'comparing_means': {
                'two_groups': {
                    'independent': {
                        'normal_data': StatisticalTestType.T_TEST_TWO_SAMPLE,
                        'non_normal': StatisticalTestType.MANN_WHITNEY_U
                    },
                    'paired': {
                        'normal_data': StatisticalTestType.T_TEST_PAIRED,
                        'non_normal': StatisticalTestType.WILCOXON_SIGNED_RANK
                    }
                },
                'multiple_groups': {
                    'independent': {
                        'normal_data': StatisticalTestType.ANOVA_ONE_WAY,
                        'non_normal': StatisticalTestType.KRUSKAL_WALLIS
                    }
                },
                'one_sample': StatisticalTestType.T_TEST_ONE_SAMPLE
            },
            'comparing_proportions': {
                'two_groups': StatisticalTestType.CHI_SQUARE_INDEPENDENCE,
                'goodness_of_fit': StatisticalTestType.CHI_SQUARE_GOODNESS,
                'small_sample': StatisticalTestType.FISHER_EXACT
            },
            'correlation': {
                'linear_normal': StatisticalTestType.PEARSON_CORRELATION,
                'non_parametric': StatisticalTestType.SPEARMAN_CORRELATION
            },
            'regression': StatisticalTestType.LINEAR_REGRESSION
        }

    def select_test(self, problem_description: str,
                    data_characteristics: Optional[Dict] = None) -> StatisticalTestRecommendation:
        """
        Select appropriate statistical test based on problem description.

        Args:
            problem_description: Text describing the statistical problem
            data_characteristics: Optional dict with data properties

        Returns:
            StatisticalTestRecommendation with test type and rationale
        """
        desc_lower = problem_description.lower()
        characteristics = data_characteristics or {}

        # Analyze problem type
        is_comparing_means = any(kw in desc_lower for kw in
            ['mean', 'average', 'difference', 'compare groups', 'treatment effect'])
        is_comparing_proportions = any(kw in desc_lower for kw in
            ['proportion', 'percentage', 'frequency', 'count', 'categorical'])
        is_correlation = any(kw in desc_lower for kw in
            ['correlation', 'relationship', 'association', 'related'])
        is_regression = any(kw in desc_lower for kw in
            ['predict', 'regression', 'model', 'explain variance'])

        # Count groups
        n_groups = characteristics.get('n_groups', self._infer_n_groups(desc_lower))
        is_paired = any(kw in desc_lower for kw in
            ['paired', 'matched', 'before and after', 'repeated measure'])
        is_normal = characteristics.get('normal_distribution', True)  # Assume normal unless stated
        sample_size = characteristics.get('sample_size', 30)

        # Select test
        if is_comparing_means:
            return self._select_mean_comparison_test(n_groups, is_paired, is_normal, sample_size)
        elif is_comparing_proportions:
            return self._select_proportion_test(n_groups, sample_size)
        elif is_correlation:
            return self._select_correlation_test(is_normal)
        elif is_regression:
            return StatisticalTestRecommendation(
                test_type=StatisticalTestType.LINEAR_REGRESSION,
                confidence=0.8,
                rationale="Regression analysis for predicting outcomes",
                assumptions=["Linear relationship", "Independence of errors",
                           "Homoscedasticity", "Normality of residuals"]
            )
        else:
            # Default to t-test for unspecified comparisons
            return StatisticalTestRecommendation(
                test_type=StatisticalTestType.T_TEST_TWO_SAMPLE,
                confidence=0.5,
                rationale="Default test for comparing groups (problem type unclear)",
                assumptions=["Normal distribution", "Independent samples"],
                caveats=["Problem type could not be clearly determined"]
            )

    def _infer_n_groups(self, description: str) -> int:
        """Infer number of groups from description"""
        if any(kw in description for kw in ['three groups', 'multiple groups', 'several']):
            return 3
        elif any(kw in description for kw in ['two groups', 'compare', 'vs', 'versus']):
            return 2
        elif any(kw in description for kw in ['one sample', 'population mean']):
            return 1
        return 2

    def _select_mean_comparison_test(self, n_groups: int, is_paired: bool,
                                     is_normal: bool, sample_size: int
                                     ) -> StatisticalTestRecommendation:
        """Select test for comparing means"""
        assumptions = []
        alternatives = []

        if n_groups == 1:
            test_type = StatisticalTestType.T_TEST_ONE_SAMPLE
            rationale = "One-sample t-test for comparing sample mean to population value"
            assumptions = ["Normal distribution or large sample", "Random sampling"]

        elif n_groups == 2:
            if is_paired:
                if is_normal or sample_size >= 30:
                    test_type = StatisticalTestType.T_TEST_PAIRED
                    rationale = "Paired t-test for matched/repeated measures data"
                    assumptions = ["Normal difference scores", "Paired observations"]
                    alternatives = [StatisticalTestType.WILCOXON_SIGNED_RANK]
                else:
                    test_type = StatisticalTestType.WILCOXON_SIGNED_RANK
                    rationale = "Wilcoxon test for non-normal paired data"
                    assumptions = ["Symmetric difference distribution"]
            else:
                if is_normal or sample_size >= 30:
                    test_type = StatisticalTestType.T_TEST_TWO_SAMPLE
                    rationale = "Independent samples t-test for comparing two group means"
                    assumptions = ["Normal distributions", "Equal variances (or Welch's)",
                                 "Independent samples"]
                    alternatives = [StatisticalTestType.MANN_WHITNEY_U]
                else:
                    test_type = StatisticalTestType.MANN_WHITNEY_U
                    rationale = "Mann-Whitney U test for non-normal independent samples"
                    assumptions = ["Independent samples", "Similar distribution shapes"]

        else:  # n_groups >= 3
            if is_normal or sample_size >= 30:
                test_type = StatisticalTestType.ANOVA_ONE_WAY
                rationale = "One-way ANOVA for comparing multiple group means"
                assumptions = ["Normal distributions", "Homogeneity of variances",
                             "Independent samples"]
                alternatives = [StatisticalTestType.KRUSKAL_WALLIS]
            else:
                test_type = StatisticalTestType.KRUSKAL_WALLIS
                rationale = "Kruskal-Wallis test for non-normal multiple groups"
                assumptions = ["Independent samples", "Similar distribution shapes"]

        return StatisticalTestRecommendation(
            test_type=test_type,
            confidence=0.85 if is_normal else 0.75,
            rationale=rationale,
            assumptions=assumptions,
            alternatives=alternatives
        )

    def _select_proportion_test(self, n_groups: int,
                                sample_size: int) -> StatisticalTestRecommendation:
        """Select test for comparing proportions"""
        if sample_size < 20:
            return StatisticalTestRecommendation(
                test_type=StatisticalTestType.FISHER_EXACT,
                confidence=0.9,
                rationale="Fisher's exact test for small sample categorical data",
                assumptions=["Fixed marginal totals"],
                alternatives=[StatisticalTestType.CHI_SQUARE_INDEPENDENCE]
            )
        else:
            return StatisticalTestRecommendation(
                test_type=StatisticalTestType.CHI_SQUARE_INDEPENDENCE,
                confidence=0.85,
                rationale="Chi-square test of independence for categorical data",
                assumptions=["Expected frequencies >= 5", "Independent observations"],
                alternatives=[StatisticalTestType.FISHER_EXACT]
            )

    def _select_correlation_test(self, is_normal: bool) -> StatisticalTestRecommendation:
        """Select correlation test"""
        if is_normal:
            return StatisticalTestRecommendation(
                test_type=StatisticalTestType.PEARSON_CORRELATION,
                confidence=0.85,
                rationale="Pearson correlation for linear relationship between continuous variables",
                assumptions=["Bivariate normality", "Linear relationship", "Homoscedasticity"],
                alternatives=[StatisticalTestType.SPEARMAN_CORRELATION]
            )
        else:
            return StatisticalTestRecommendation(
                test_type=StatisticalTestType.SPEARMAN_CORRELATION,
                confidence=0.85,
                rationale="Spearman correlation for monotonic relationships or non-normal data",
                assumptions=["Monotonic relationship"],
                alternatives=[StatisticalTestType.PEARSON_CORRELATION]
            )


class StatisticalInterpreter:
    """Interpret statistical results"""

    def __init__(self):
        self.effect_size_thresholds = {
            'small': 0.2,
            'medium': 0.5,
            'large': 0.8
        }

    def interpret_p_value(self, p_value: float,
                         alpha: float = 0.05) -> StatisticalInterpretation:
        """
        Interpret a p-value result.

        Args:
            p_value: The p-value from the statistical test
            alpha: Significance level (default 0.05)

        Returns:
            StatisticalInterpretation with plain-language interpretation
        """
        is_significant = p_value < alpha

        if p_value < 0.001:
            strength = "very strong"
        elif p_value < 0.01:
            strength = "strong"
        elif p_value < 0.05:
            strength = "moderate"
        elif p_value < 0.10:
            strength = "weak"
        else:
            strength = "no"

        if is_significant:
            interpretation = (
                f"The result is statistically significant at α = {alpha} "
                f"(p = {p_value:.4f}). There is {strength} evidence against "
                f"the null hypothesis. The observed effect is unlikely to be "
                f"due to chance alone."
            )
        else:
            interpretation = (
                f"The result is not statistically significant at α = {alpha} "
                f"(p = {p_value:.4f}). We fail to reject the null hypothesis. "
                f"The data do not provide sufficient evidence of a real effect."
            )

        return StatisticalInterpretation(
            test_type=StatisticalTestType.T_TEST_TWO_SAMPLE,  # Placeholder
            statistic_value=0.0,  # Unknown
            p_value=p_value,
            is_significant=is_significant,
            significance_level=alpha,
            interpretation=interpretation
        )

    def interpret_confidence_interval(self, lower: float, upper: float,
                                      null_value: float = 0,
                                      confidence: float = 0.95) -> str:
        """Interpret a confidence interval"""
        width = upper - lower
        contains_null = lower <= null_value <= upper

        interpretation = f"The {confidence*100:.0f}% confidence interval is [{lower:.4f}, {upper:.4f}]. "

        if contains_null:
            interpretation += (
                f"Since the interval contains {null_value}, we cannot conclude "
                f"that the true parameter differs significantly from {null_value}."
            )
        else:
            direction = "above" if lower > null_value else "below"
            interpretation += (
                f"Since the entire interval is {direction} {null_value}, we can "
                f"conclude the true parameter is significantly different from {null_value}."
            )

        return interpretation

    def interpret_effect_size(self, effect_size: float,
                             effect_type: str = "cohen_d") -> str:
        """Interpret effect size magnitude"""
        abs_effect = abs(effect_size)

        if abs_effect < self.effect_size_thresholds['small']:
            magnitude = "negligible"
        elif abs_effect < self.effect_size_thresholds['medium']:
            magnitude = "small"
        elif abs_effect < self.effect_size_thresholds['large']:
            magnitude = "medium"
        else:
            magnitude = "large"

        direction = "positive" if effect_size > 0 else "negative"

        return (
            f"The effect size ({effect_type} = {effect_size:.3f}) indicates a "
            f"{magnitude} {direction} effect. "
            f"{'This may not be practically meaningful.' if magnitude in ['negligible', 'small'] else 'This suggests a practically meaningful difference.'}"
        )


class DimensionalAnalyzer:
    """Perform dimensional analysis for physics problems"""

    def __init__(self):
        # Base SI units and their dimensions
        self.base_units = {
            'm': {UnitDimension.LENGTH: 1},
            'kg': {UnitDimension.MASS: 1},
            's': {UnitDimension.TIME: 1},
            'A': {UnitDimension.CURRENT: 1},
            'K': {UnitDimension.TEMPERATURE: 1},
            'mol': {UnitDimension.AMOUNT: 1},
            'cd': {UnitDimension.LUMINOSITY: 1},
        }

        # Derived units
        self.derived_units = {
            'N': {UnitDimension.MASS: 1, UnitDimension.LENGTH: 1, UnitDimension.TIME: -2},  # Newton
            'J': {UnitDimension.MASS: 1, UnitDimension.LENGTH: 2, UnitDimension.TIME: -2},  # Joule
            'W': {UnitDimension.MASS: 1, UnitDimension.LENGTH: 2, UnitDimension.TIME: -3},  # Watt
            'Pa': {UnitDimension.MASS: 1, UnitDimension.LENGTH: -1, UnitDimension.TIME: -2},  # Pascal
            'Hz': {UnitDimension.TIME: -1},  # Hertz
            'C': {UnitDimension.CURRENT: 1, UnitDimension.TIME: 1},  # Coulomb
            'V': {UnitDimension.MASS: 1, UnitDimension.LENGTH: 2, UnitDimension.TIME: -3, UnitDimension.CURRENT: -1},  # Volt
            'Ω': {UnitDimension.MASS: 1, UnitDimension.LENGTH: 2, UnitDimension.TIME: -3, UnitDimension.CURRENT: -2},  # Ohm
            'm/s': {UnitDimension.LENGTH: 1, UnitDimension.TIME: -1},  # Velocity
            'm/s^2': {UnitDimension.LENGTH: 1, UnitDimension.TIME: -2},  # Acceleration
        }

        self.all_units = {**self.base_units, **self.derived_units}

    def analyze(self, expression: str) -> DimensionalAnalysisResult:
        """
        Perform dimensional analysis on an expression.

        Args:
            expression: Expression with units (e.g., "kg * m / s^2")

        Returns:
            DimensionalAnalysisResult with dimension breakdown
        """
        issues = []
        dimensions: Dict[UnitDimension, int] = {}

        # Parse expression
        tokens = self._tokenize_units(expression)

        current_sign = 1
        for token in tokens:
            if token == '*':
                continue
            elif token == '/':
                current_sign = -1
                continue
            elif token in ['(', ')']:
                continue
            else:
                # Parse unit with possible exponent
                unit, exponent = self._parse_unit_token(token)

                if unit in self.all_units:
                    unit_dims = self.all_units[unit]
                    for dim, power in unit_dims.items():
                        if dim not in dimensions:
                            dimensions[dim] = 0
                        dimensions[dim] += power * exponent * current_sign
                else:
                    issues.append(f"Unknown unit: {unit}")

        # Clean up zero dimensions
        dimensions = {k: v for k, v in dimensions.items() if v != 0}

        # Generate simplified unit string
        simplified = self._dimensions_to_string(dimensions)

        return DimensionalAnalysisResult(
            expression=expression,
            dimensions=dimensions,
            is_dimensionally_consistent=len(issues) == 0,
            simplified_units=simplified,
            issues=issues
        )

    def _tokenize_units(self, expression: str) -> List[str]:
        """Tokenize unit expression"""
        # Split by operators while keeping them
        tokens = re.split(r'(\*|/|\(|\))', expression)
        return [t.strip() for t in tokens if t.strip()]

    def _parse_unit_token(self, token: str) -> Tuple[str, int]:
        """Parse a unit token, extracting exponent"""
        # Match patterns like "m^2", "s^-1", "kg"
        match = re.match(r'([a-zA-ZΩ/]+)\^?(-?\d+)?', token)
        if match:
            unit = match.group(1)
            exponent = int(match.group(2)) if match.group(2) else 1
            return unit, exponent
        return token, 1

    def _dimensions_to_string(self, dimensions: Dict[UnitDimension, int]) -> str:
        """Convert dimensions dict to string representation"""
        if not dimensions:
            return "dimensionless"

        parts = []
        for dim, power in sorted(dimensions.items(), key=lambda x: -x[1]):
            if power == 1:
                parts.append(dim.value)
            else:
                parts.append(f"{dim.value}^{power}")

        return " · ".join(parts)

    def check_equation_consistency(self, lhs_units: str, rhs_units: str) -> Tuple[bool, str]:
        """Check if both sides of an equation have consistent dimensions"""
        lhs_result = self.analyze(lhs_units)
        rhs_result = self.analyze(rhs_units)

        if lhs_result.dimensions == rhs_result.dimensions:
            return True, "Equation is dimensionally consistent"
        else:
            return False, (
                f"Dimensional mismatch: LHS = {lhs_result.simplified_units}, "
                f"RHS = {rhs_result.simplified_units}"
            )

    def derive_units(self, formula: str, known_units: Dict[str, str]) -> str:
        """Derive units of result given units of inputs"""
        # This is a simplified implementation
        # Would need more sophisticated parsing for complex formulas
        result_dims: Dict[UnitDimension, int] = {}

        for var, units in known_units.items():
            var_dims = self.analyze(units).dimensions

            # Check how variable appears in formula
            # This is simplified - real implementation would parse formula properly
            if f"{var}^2" in formula or f"{var}**2" in formula:
                multiplier = 2
            elif f"1/{var}" in formula or f"/{var}" in formula:
                multiplier = -1
            else:
                multiplier = 1

            for dim, power in var_dims.items():
                if dim not in result_dims:
                    result_dims[dim] = 0
                result_dims[dim] += power * multiplier

        return self._dimensions_to_string(result_dims)


class ProbabilityCalculator:
    """Calculate probabilities for common distributions"""
