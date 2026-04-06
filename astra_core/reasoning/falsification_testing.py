"""
Falsification-First Hypothesis Testing for STAN V42

Implements rigorous hypothesis testing following Popperian falsificationist principles:
- Actively seeks to disprove hypotheses rather than confirm
- Generates severe tests with high diagnostic power
- Distinguishes genuine confirmation from mere consistency
- Tracks surviving hypotheses through multiple tests

This approach prevents confirmation bias and ensures
scientific rigor in astrophysical inference.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
from enum import Enum
import math
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class TestOutcome(Enum):
    """Outcomes of hypothesis tests."""
    FALSIFIED = "falsified"           # Strong evidence against
    WEAKENED = "weakened"             # Moderate evidence against
    INCONCLUSIVE = "inconclusive"     # No diagnostic power
    CONSISTENT = "consistent"         # Passed test, not falsified
    CORROBORATED = "corroborated"     # Passed severe test


class TestSeverity(Enum):
    """Severity levels of tests."""
    TRIVIAL = "trivial"       # Passes easily, low diagnostic power
    STANDARD = "standard"     # Normal scientific test
    SEVERE = "severe"         # High chance of failure if false
    CRITICAL = "critical"     # Would be remarkable to pass if false


class HypothesisStatus(Enum):
    """Current status of a hypothesis."""
    PROVISIONAL = "provisional"   # Not yet tested
    TESTING = "testing"           # Currently under test
    SURVIVING = "surviving"       # Passed multiple tests
    FALSIFIED = "falsified"       # Definitively rejected
    DISCARDED = "discarded"       # Rejected by severe tests


@dataclass
class TestPrediction:
    """A testable prediction from a hypothesis."""
    prediction_id: str
    description: str
    observable: str  # What to measure
    predicted_value: float
    predicted_uncertainty: float
    auxiliary_assumptions: List[str]
    severity: TestSeverity


@dataclass
class TestResult:
    """Result of a single hypothesis test."""
    test_id: str
    prediction_id: str
    observed_value: float
    observed_uncertainty: float
    predicted_value: float
    predicted_uncertainty: float
    deviation_sigma: float  # |obs - pred| / sqrt(σ_obs² + σ_pred²)
    outcome: TestOutcome
    severity: TestSeverity
    p_value: float
    diagnostic_power: float  # How informative was this test


@dataclass
class Hypothesis:
    """A scientific hypothesis under test."""
    hypothesis_id: str
    name: str
    description: str
    status: HypothesisStatus
    predictions: List[TestPrediction]
    test_history: List[TestResult]
    n_tests_passed: int
    n_tests_failed: int
    n_severe_tests_passed: int
    corroboration_degree: float  # Cumulative evidence strength
    prior_plausibility: float
    current_plausibility: float
    auxiliary_assumptions: List[str]


@dataclass
class SeverityAnalysis:
    """Analysis of test severity."""
    test_id: str
    probability_pass_if_true: float   # P(pass|H true)
    probability_pass_if_false: float  # P(pass|H false)
    severity_score: float  # 1 - P(pass|H false)
    diagnostic_ratio: float  # P(pass|true) / P(pass|false)
    recommendation: str


@dataclass
class FalsificationReport:
    """Complete report on falsification attempts."""
    hypothesis: Hypothesis
    tests_conducted: int
    tests_passed: int
    tests_failed: int
    severe_tests_passed: int
    overall_outcome: TestOutcome
    confidence_level: float
    surviving_predictions: List[TestPrediction]
    critical_failures: List[TestResult]
    recommendations: List[str]


# ============================================================================
# Severity Calculator
# ============================================================================

class SeverityCalculator:
    """
    Calculates test severity following Mayo's error-statistical approach.
    """

    def __init__(self):
        self._test_counter = 0

    def compute_severity(self,
                        prediction: TestPrediction,
                        alternative_hypotheses: Optional[List[Dict[str, float]]] = None) -> SeverityAnalysis:
        """
        Compute severity of a test.

        Severity = probability test would have detected departure from H if it existed.
        """
        test_id = self._generate_test_id()

        # Probability of passing if hypothesis is true
        # (based on prediction uncertainty)
        p_pass_if_true = 0.95  # Default for 2σ prediction

        # Probability of passing if false
        if alternative_hypotheses:
            # Average over alternative hypotheses
            p_pass_if_false = self._compute_false_pass_probability(
                prediction, alternative_hypotheses
            )
        else:
            # Default based on prediction precision
            relative_precision = prediction.predicted_uncertainty / abs(prediction.predicted_value + 1e-10)
            p_pass_if_false = min(0.9, 0.1 + 0.8 * relative_precision)

        # Severity score: high when test is likely to fail if hypothesis is false
        severity_score = 1 - p_pass_if_false

        # Diagnostic ratio
        if p_pass_if_false > 0:
            diagnostic_ratio = p_pass_if_true / p_pass_if_false
        else:
            diagnostic_ratio = float('inf')

        # Generate recommendation
        if severity_score > 0.8:
            recommendation = "Highly severe test - strong evidence if passed"
        elif severity_score > 0.5:
            recommendation = "Moderately severe - meaningful test"
        elif severity_score > 0.2:
            recommendation = "Low severity - consider alternatives"
        else:
            recommendation = "Trivial test - does not discriminate hypotheses"

        return SeverityAnalysis(
            test_id=test_id,
            probability_pass_if_true=p_pass_if_true,
            probability_pass_if_false=p_pass_if_false,
            severity_score=severity_score,
            diagnostic_ratio=diagnostic_ratio,
            recommendation=recommendation
        )

    def _compute_false_pass_probability(self,
                                        prediction: TestPrediction,
                                        alternatives: List[Dict[str, float]]) -> float:
        """
        Compute probability of passing test under alternative hypotheses.
        """
        pass_probs = []

        for alt in alternatives:
            alt_value = alt.get("predicted_value", prediction.predicted_value)
            alt_uncertainty = alt.get("uncertainty", prediction.predicted_uncertainty)

            # Distance between predictions
            diff = abs(alt_value - prediction.predicted_value)
            combined_unc = math.sqrt(alt_uncertainty ** 2 + prediction.predicted_uncertainty ** 2)

            if combined_unc > 0:
                # Probability of overlapping at 2σ
                z = diff / combined_unc
                p_pass = 1 - self._normal_cdf(z - 2) + self._normal_cdf(-z - 2)
            else:
                p_pass = 1.0 if diff < 1e-10 else 0.0

            weight = alt.get("plausibility", 1.0)
            pass_probs.append(p_pass * weight)

        total_weight = sum(alt.get("plausibility", 1.0) for alt in alternatives)
        if total_weight > 0:
            return sum(pass_probs) / total_weight
        return 0.5

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _generate_test_id(self) -> str:
        """Generate unique test ID."""
        self._test_counter += 1
        return f"TEST_{self._test_counter:06d}"


# ============================================================================
# Falsification Engine
# ============================================================================

class FalsificationEngine:
    """
    Main engine for falsification-first hypothesis testing.
    """

    def __init__(self,
                 sigma_threshold: float = 3.0,
                 severe_threshold: float = 5.0):
        """
        Args:
            sigma_threshold: Sigma level for falsification
            severe_threshold: Sigma level for severe falsification
        """
        self.sigma_threshold = sigma_threshold
        self.severe_threshold = severe_threshold

        self.severity_calculator = SeverityCalculator()
        self._hypothesis_counter = 0
        self._result_counter = 0

    def create_hypothesis(self,
                         name: str,
                         description: str,
                         predictions: List[Dict[str, Any]],
                         prior_plausibility: float = 0.5,
                         auxiliary_assumptions: Optional[List[str]] = None) -> Hypothesis:
        """
        Create a new hypothesis for testing.
        """
        hypothesis_id = self._generate_hypothesis_id()

        test_predictions = []
        for i, pred in enumerate(predictions):
            test_pred = TestPrediction(
                prediction_id=f"{hypothesis_id}_P{i:03d}",
                description=pred.get("description", f"Prediction {i}"),
                observable=pred.get("observable", "value"),
                predicted_value=pred["predicted_value"],
                predicted_uncertainty=pred.get("uncertainty", 0.1 * abs(pred["predicted_value"])),
                auxiliary_assumptions=pred.get("auxiliary", []),
                severity=TestSeverity(pred.get("severity", "standard"))
            )
            test_predictions.append(test_pred)

        return Hypothesis(
            hypothesis_id=hypothesis_id,
            name=name,
            description=description,
            status=HypothesisStatus.PROVISIONAL,
            predictions=test_predictions,
            test_history=[],
            n_tests_passed=0,
            n_tests_failed=0,
            n_severe_tests_passed=0,
            corroboration_degree=0.0,
            prior_plausibility=prior_plausibility,
            current_plausibility=prior_plausibility,
            auxiliary_assumptions=auxiliary_assumptions or []
        )

    def test_prediction(self,
                       hypothesis: Hypothesis,
                       prediction_id: str,
                       observed_value: float,
                       observed_uncertainty: float,
                       alternative_predictions: Optional[List[Dict]] = None) -> TestResult:
        """
        Test a specific prediction against observation.
        """
        # Find prediction
        prediction = next((p for p in hypothesis.predictions
                          if p.prediction_id == prediction_id), None)

        if prediction is None:
            raise ValueError(f"Prediction {prediction_id} not found")

        # Compute deviation
        combined_uncertainty = math.sqrt(
            observed_uncertainty ** 2 + prediction.predicted_uncertainty ** 2
        )
        deviation = abs(observed_value - prediction.predicted_value)
        deviation_sigma = deviation / combined_uncertainty if combined_uncertainty > 0 else 0.0

        # Compute p-value (two-tailed)
        p_value = 2 * (1 - self._normal_cdf(deviation_sigma))

        # Determine outcome
        if deviation_sigma >= self.severe_threshold:
            outcome = TestOutcome.FALSIFIED
        elif deviation_sigma >= self.sigma_threshold:
            outcome = TestOutcome.WEAKENED
        elif deviation_sigma >= 2.0:
            outcome = TestOutcome.INCONCLUSIVE
        else:
            # Passed - check severity
            severity_analysis = self.severity_calculator.compute_severity(
                prediction, alternative_predictions
            )

            if severity_analysis.severity_score > 0.7:
                outcome = TestOutcome.CORROBORATED
            else:
                outcome = TestOutcome.CONSISTENT

        # Compute diagnostic power
        diagnostic_power = 1 - p_value if deviation_sigma < 2 else min(1.0, deviation_sigma / 5)

        result = TestResult(
            test_id=self._generate_result_id(),
            prediction_id=prediction_id,
            observed_value=observed_value,
            observed_uncertainty=observed_uncertainty,
            predicted_value=prediction.predicted_value,
            predicted_uncertainty=prediction.predicted_uncertainty,
            deviation_sigma=deviation_sigma,
            outcome=outcome,
            severity=prediction.severity,
            p_value=p_value,
            diagnostic_power=diagnostic_power
        )

        # Update hypothesis
        self._update_hypothesis(hypothesis, result)

        return result

    def _update_hypothesis(self, hypothesis: Hypothesis, result: TestResult):
        """Update hypothesis based on test result."""
        hypothesis.test_history.append(result)
        hypothesis.status = HypothesisStatus.TESTING

        if result.outcome in [TestOutcome.CONSISTENT, TestOutcome.CORROBORATED]:
            hypothesis.n_tests_passed += 1

            if result.severity in [TestSeverity.SEVERE, TestSeverity.CRITICAL]:
                hypothesis.n_severe_tests_passed += 1

            # Update corroboration
            if result.outcome == TestOutcome.CORROBORATED:
                hypothesis.corroboration_degree += result.diagnostic_power

        elif result.outcome in [TestOutcome.FALSIFIED, TestOutcome.WEAKENED]:
            hypothesis.n_tests_failed += 1

            if result.outcome == TestOutcome.FALSIFIED:
                if result.severity in [TestSeverity.SEVERE, TestSeverity.CRITICAL]:
                    hypothesis.status = HypothesisStatus.FALSIFIED
                else:
                    hypothesis.status = HypothesisStatus.DISCARDED

        # Update plausibility
        self._update_plausibility(hypothesis, result)

        # Check if surviving
        if (hypothesis.n_tests_passed > 3 and
            hypothesis.n_tests_failed == 0 and
            hypothesis.n_severe_tests_passed > 0):
            hypothesis.status = HypothesisStatus.SURVIVING

    def _update_plausibility(self, hypothesis: Hypothesis, result: TestResult):
        """Update hypothesis plausibility using likelihood ratio."""
        # Simplified Bayesian update
        prior = hypothesis.current_plausibility

        if result.outcome == TestOutcome.FALSIFIED:
            # Strong evidence against
            likelihood_ratio = 0.01
        elif result.outcome == TestOutcome.WEAKENED:
            likelihood_ratio = 0.1
        elif result.outcome == TestOutcome.CORROBORATED:
            # Severity-weighted evidence for
            likelihood_ratio = 1 + result.diagnostic_power
        elif result.outcome == TestOutcome.CONSISTENT:
            likelihood_ratio = 1.0 + 0.1 * result.diagnostic_power
        else:
            likelihood_ratio = 1.0

        # Bayes update (simplified with implicit alternative)
        posterior = prior * likelihood_ratio / (prior * likelihood_ratio + (1 - prior))
        hypothesis.current_plausibility = max(0.001, min(0.999, posterior))

    def design_severe_test(self,
                          hypothesis: Hypothesis,
                          available_observables: List[str],
                          precision_budget: Dict[str, float]) -> Optional[TestPrediction]:
        """
        Design the most severe test possible given constraints.
        """
        best_prediction = None
        best_severity = 0.0

        for prediction in hypothesis.predictions:
            # Check if observable is available
            if prediction.observable not in available_observables:
                continue

            # Check if already tested
            already_tested = any(r.prediction_id == prediction.prediction_id
                               for r in hypothesis.test_history)
            if already_tested:
                continue

            # Check precision requirement
            required_precision = prediction.predicted_uncertainty / 2
            available_precision = precision_budget.get(prediction.observable, float('inf'))

            if available_precision > required_precision:
                continue  # Can't achieve required precision

            # Compute severity
            severity_analysis = self.severity_calculator.compute_severity(prediction)

            if severity_analysis.severity_score > best_severity:
                best_severity = severity_analysis.severity_score
                best_prediction = prediction

        return best_prediction

    def generate_falsification_report(self, hypothesis: Hypothesis) -> FalsificationReport:
        """
        Generate comprehensive falsification report.
        """
        # Count outcomes
        tests_conducted = len(hypothesis.test_history)
        tests_passed = hypothesis.n_tests_passed
        tests_failed = hypothesis.n_tests_failed

        # Find critical failures
        critical_failures = [r for r in hypothesis.test_history
                           if r.outcome == TestOutcome.FALSIFIED]

        # Find untested predictions
        tested_ids = {r.prediction_id for r in hypothesis.test_history}
        surviving_predictions = [p for p in hypothesis.predictions
                               if p.prediction_id not in tested_ids]

        # Determine overall outcome
        if hypothesis.status == HypothesisStatus.FALSIFIED:
            overall_outcome = TestOutcome.FALSIFIED
        elif hypothesis.status == HypothesisStatus.SURVIVING:
            overall_outcome = TestOutcome.CORROBORATED
        elif tests_failed > 0:
            overall_outcome = TestOutcome.WEAKENED
        elif tests_passed > 0:
            overall_outcome = TestOutcome.CONSISTENT
        else:
            overall_outcome = TestOutcome.INCONCLUSIVE

        # Confidence level
        if tests_conducted > 0:
            confidence = hypothesis.current_plausibility
        else:
            confidence = hypothesis.prior_plausibility

        # Recommendations
        recommendations = self._generate_recommendations(hypothesis)

        return FalsificationReport(
            hypothesis=hypothesis,
            tests_conducted=tests_conducted,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            severe_tests_passed=hypothesis.n_severe_tests_passed,
            overall_outcome=overall_outcome,
            confidence_level=confidence,
            surviving_predictions=surviving_predictions,
            critical_failures=critical_failures,
            recommendations=recommendations
        )

    def _generate_recommendations(self, hypothesis: Hypothesis) -> List[str]:
        """Generate recommendations for further testing."""
        recommendations = []

        if hypothesis.status == HypothesisStatus.FALSIFIED:
            recommendations.append("Hypothesis has been falsified by severe test")
            recommendations.append("Consider modifying auxiliary assumptions")
            recommendations.append("Develop alternative hypotheses")

        elif hypothesis.status == HypothesisStatus.SURVIVING:
            recommendations.append("Hypothesis has survived multiple severe tests")
            recommendations.append("Seek even more demanding predictions to test")
            recommendations.append("Compare quantitatively with competing hypotheses")

        elif hypothesis.n_tests_failed > 0:
            recommendations.append("Hypothesis shows tension with some observations")
            recommendations.append("Examine auxiliary assumptions carefully")
            recommendations.append("Consider whether failures indicate systematic issues")

        else:
            if hypothesis.n_severe_tests_passed == 0:
                recommendations.append("No severe tests passed yet - design more demanding tests")
            if len(hypothesis.test_history) < 3:
                recommendations.append("Insufficient testing - more tests needed")

        # Untested predictions
        tested_ids = {r.prediction_id for r in hypothesis.test_history}
        untested = [p for p in hypothesis.predictions if p.prediction_id not in tested_ids]

        if untested:
            severe_untested = [p for p in untested
                             if p.severity in [TestSeverity.SEVERE, TestSeverity.CRITICAL]]
            if severe_untested:
                recommendations.append(f"Test {len(severe_untested)} remaining severe predictions")

        return recommendations

    def compare_hypotheses(self,
                          hypotheses: List[Hypothesis]) -> Dict[str, Any]:
        """
        Compare multiple hypotheses based on test performance.
        """
        comparison = {
            "ranking": [],
            "decisive_tests": [],
            "recommendations": []
        }

        # Rank by current plausibility
        ranked = sorted(hypotheses,
                       key=lambda h: h.current_plausibility,
                       reverse=True)

        for rank, h in enumerate(ranked):
            comparison["ranking"].append({
                "rank": rank + 1,
                "hypothesis_id": h.hypothesis_id,
                "name": h.name,
                "plausibility": h.current_plausibility,
                "tests_passed": h.n_tests_passed,
                "tests_failed": h.n_tests_failed,
                "severe_passes": h.n_severe_tests_passed,
                "status": h.status.value
            })

        # Find decisive tests
        if len(hypotheses) > 1:
            for h1 in hypotheses:
                for h2 in hypotheses:
                    if h1.hypothesis_id >= h2.hypothesis_id:
                        continue

                    decisive = self._find_decisive_test(h1, h2)
                    if decisive:
                        comparison["decisive_tests"].append({
                            "between": [h1.name, h2.name],
                            "test": decisive
                        })

        # Recommendations
        if len(ranked) > 1 and ranked[0].current_plausibility < 0.9:
            comparison["recommendations"].append(
                "No hypothesis strongly favored - more testing needed"
            )
        elif ranked[0].n_severe_tests_passed < 2:
            comparison["recommendations"].append(
                "Leading hypothesis needs more severe testing"
            )

        return comparison

    def _find_decisive_test(self,
                           h1: Hypothesis,
                           h2: Hypothesis) -> Optional[Dict]:
        """Find test that would distinguish two hypotheses."""
        # Look for predictions that differ significantly
        for p1 in h1.predictions:
            for p2 in h2.predictions:
                if p1.observable != p2.observable:
                    continue

                diff = abs(p1.predicted_value - p2.predicted_value)
                combined_unc = math.sqrt(
                    p1.predicted_uncertainty ** 2 + p2.predicted_uncertainty ** 2
                )

                if combined_unc > 0 and diff / combined_unc > 3:
                    return {
                        "observable": p1.observable,
                        "h1_prediction": p1.predicted_value,
                        "h2_prediction": p2.predicted_value,
                        "discrimination_sigma": diff / combined_unc
                    }

        return None

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _generate_hypothesis_id(self) -> str:
        """Generate unique hypothesis ID."""
        self._hypothesis_counter += 1
        return f"HYP_{self._hypothesis_counter:06d}"

    def _generate_result_id(self) -> str:
        """Generate unique result ID."""
        self._result_counter += 1
        return f"RES_{self._result_counter:06d}"


# ============================================================================
# Test Design Generator
# ============================================================================

class TestDesignGenerator:
    """
    Generates optimal test designs for hypothesis falsification.
    """

    def __init__(self, falsification_engine: FalsificationEngine):
        self.engine = falsification_engine

    def design_test_sequence(self,
                            hypothesis: Hypothesis,
                            max_tests: int = 5,
                            optimization_criterion: str = "severity") -> List[TestPrediction]:
        """
        Design optimal sequence of tests.

        Args:
            hypothesis: Hypothesis to test
            max_tests: Maximum number of tests
            optimization_criterion: "severity", "information", or "cost"
        """
        untested = [p for p in hypothesis.predictions
                   if not any(r.prediction_id == p.prediction_id
                             for r in hypothesis.test_history)]

        if not untested:
            return []

        # Score predictions
        scored = []
        for pred in untested:
            severity_analysis = self.engine.severity_calculator.compute_severity(pred)

            if optimization_criterion == "severity":
                score = severity_analysis.severity_score
            elif optimization_criterion == "information":
                score = severity_analysis.diagnostic_ratio if severity_analysis.diagnostic_ratio < float('inf') else 10.0
            else:
                score = 1.0

            # Bonus for severe/critical predictions
            if pred.severity == TestSeverity.CRITICAL:
                score *= 2
            elif pred.severity == TestSeverity.SEVERE:
                score *= 1.5

            scored.append((pred, score))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in scored[:max_tests]]

    def suggest_novel_test(self,
                          hypothesis: Hypothesis,
                          domain_knowledge: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Suggest a novel test not in current predictions.
        """
        suggestion = {
            "type": "novel_test",
            "rationale": "",
            "observable": "",
            "expected_precision": 0.0
        }

        # Analyze existing predictions
        observables = {p.observable for p in hypothesis.predictions}
        tested_observables = {r.prediction_id.split("_")[0]
                            for r in hypothesis.test_history}

        # Look for gaps
        if domain_knowledge:
            possible_observables = domain_knowledge.get("observables", [])
            untested = [o for o in possible_observables if o not in observables]

            if untested:
                suggestion["observable"] = untested[0]
                suggestion["rationale"] = f"Observable '{untested[0]}' not yet tested"

        # Check for high-risk auxiliary assumptions
        if hypothesis.auxiliary_assumptions:
            risky = [a for a in hypothesis.auxiliary_assumptions
                    if "assumed" in a.lower() or "approximation" in a.lower()]
            if risky:
                suggestion["rationale"] += f"; Test auxiliary assumption: {risky[0]}"

        return suggestion


# ============================================================================
# Singleton Access
# ============================================================================

_falsification_engine: Optional[FalsificationEngine] = None


def get_falsification_engine() -> FalsificationEngine:
    """Get singleton falsification engine."""
    global _falsification_engine
    if _falsification_engine is None:
        _falsification_engine = FalsificationEngine()
    return _falsification_engine


# ============================================================================
# Integration with STAN Event Bus
# ============================================================================

def setup_falsification_testing_integration(event_bus) -> None:
    """Set up falsification testing integration with STAN event bus."""
    engine = get_falsification_engine()

    active_hypotheses: Dict[str, Hypothesis] = {}

    def on_hypothesis_created(event):
        """Handle new hypothesis creation."""
        payload = event.get("payload", {})
        name = payload.get("name", "Unnamed")
        description = payload.get("description", "")
        predictions = payload.get("predictions", [])

        if predictions:
            hypothesis = engine.create_hypothesis(
                name=name,
                description=description,
                predictions=predictions,
                prior_plausibility=payload.get("prior", 0.5)
            )
            active_hypotheses[hypothesis.hypothesis_id] = hypothesis

            event_bus.publish(
                "hypothesis_registered",
                "falsification_testing",
                {
                    "hypothesis_id": hypothesis.hypothesis_id,
                    "name": name,
                    "n_predictions": len(predictions)
                }
            )

    def on_test_observation(event):
        """Handle new observation for testing."""
        payload = event.get("payload", {})
        hypothesis_id = payload.get("hypothesis_id")
        prediction_id = payload.get("prediction_id")
        observed = payload.get("observed_value")
        uncertainty = payload.get("uncertainty")

        if hypothesis_id in active_hypotheses and observed is not None:
            hypothesis = active_hypotheses[hypothesis_id]

            result = engine.test_prediction(
                hypothesis=hypothesis,
                prediction_id=prediction_id,
                observed_value=observed,
                observed_uncertainty=uncertainty or 0.0
            )

            event_bus.publish(
                "test_result",
                "falsification_testing",
                {
                    "hypothesis_id": hypothesis_id,
                    "test_id": result.test_id,
                    "outcome": result.outcome.value,
                    "deviation_sigma": result.deviation_sigma,
                    "hypothesis_status": hypothesis.status.value,
                    "plausibility": hypothesis.current_plausibility
                }
            )

    def on_report_request(event):
        """Handle request for falsification report."""
        payload = event.get("payload", {})
        hypothesis_id = payload.get("hypothesis_id")

        if hypothesis_id in active_hypotheses:
            hypothesis = active_hypotheses[hypothesis_id]
            report = engine.generate_falsification_report(hypothesis)

            event_bus.publish(
                "falsification_report",
                "falsification_testing",
                {
                    "hypothesis_id": hypothesis_id,
                    "tests_conducted": report.tests_conducted,
                    "tests_passed": report.tests_passed,
                    "tests_failed": report.tests_failed,
                    "outcome": report.overall_outcome.value,
                    "confidence": report.confidence_level,
                    "recommendations": report.recommendations
                }
            )

    event_bus.subscribe("create_hypothesis", on_hypothesis_created)
    event_bus.subscribe("test_observation", on_test_observation)
    event_bus.subscribe("falsification_report_request", on_report_request)
    logger.info("Falsification testing integration configured")
