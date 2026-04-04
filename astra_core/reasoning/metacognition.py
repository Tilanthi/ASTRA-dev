"""
Metacognition Module for STAN V41

Implements self-reflective reasoning - the system's ability to monitor,
evaluate, and improve its own reasoning processes.

Key capabilities:
- Reasoning quality assessment: Evaluate confidence, coherence, completeness
- Uncertainty monitoring: Track what the system doesn't know
- Error detection: Identify reasoning failures and biases
- Strategy selection: Choose appropriate reasoning strategies
- Learning from mistakes: Improve future reasoning based on past errors
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from enum import Enum, auto
from datetime import datetime
import uuid
from collections import defaultdict
import math


class ReasoningQuality(Enum):
    """Quality levels for reasoning"""
    EXCELLENT = auto()
    GOOD = auto()
    ADEQUATE = auto()
    POOR = auto()
    FAILED = auto()


class UncertaintyType(Enum):
    """Types of uncertainty"""
    ALEATORIC = auto()      # Irreducible randomness
    EPISTEMIC = auto()      # Knowledge gaps (reducible)
    MODEL = auto()          # Model limitations
    MEASUREMENT = auto()    # Data quality
    COMPUTATIONAL = auto()  # Algorithm limitations


class BiasType(Enum):
    """Types of cognitive biases"""
    CONFIRMATION = auto()       # Favoring confirming evidence
    ANCHORING = auto()          # Over-relying on initial information
    AVAILABILITY = auto()       # Overweighting recent/memorable info
    OVERCONFIDENCE = auto()     # Excessive certainty
    UNDERCONFIDENCE = auto()    # Excessive doubt
    FRAMING = auto()            # Affected by problem presentation
    SUNK_COST = auto()          # Continuing due to past investment
    BASE_RATE_NEGLECT = auto()  # Ignoring prior probabilities


class ReasoningStrategy(Enum):
    """Available reasoning strategies"""
    DEDUCTIVE = auto()          # Logic-based inference
    INDUCTIVE = auto()          # Pattern generalization
    ABDUCTIVE = auto()          # Best explanation inference
    ANALOGICAL = auto()         # Cross-domain mapping
    CAUSAL = auto()             # Cause-effect analysis
    PROBABILISTIC = auto()      # Bayesian reasoning
    HEURISTIC = auto()          # Fast, approximate
    SYSTEMATIC = auto()         # Thorough, exhaustive
    COUNTERFACTUAL = auto()     # What-if analysis
    METACOGNITIVE = auto()      # Self-reflective


@dataclass
class ReasoningTrace:
    """Record of a reasoning episode"""
    trace_id: str
    task_description: str
    strategy_used: ReasoningStrategy

    # Process
    steps: List[Dict[str, Any]]        # Reasoning steps taken
    capabilities_invoked: List[str]     # Which modules were used
    time_taken_ms: float

    # Outcomes
    conclusion: Optional[str] = None
    confidence: float = 0.5
    alternatives_considered: int = 0

    # Quality metrics
    coherence: float = 0.5             # Internal consistency
    completeness: float = 0.5          # Coverage of relevant factors
    efficiency: float = 0.5            # Resource usage

    # Issues detected
    uncertainties: List[str] = field(default_factory=list)
    potential_biases: List[BiasType] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = f"TRC-{uuid.uuid4().hex[:8]}"

    @property
    def quality(self) -> ReasoningQuality:
        """Compute overall quality"""
        score = (self.coherence + self.completeness + self.confidence) / 3

        # Penalty for issues
        bias_penalty = len(self.potential_biases) * 0.1
        error_penalty = len(self.errors) * 0.2
        score = max(0, score - bias_penalty - error_penalty)

        if score >= 0.85:
            return ReasoningQuality.EXCELLENT
        elif score >= 0.7:
            return ReasoningQuality.GOOD
        elif score >= 0.5:
            return ReasoningQuality.ADEQUATE
        elif score >= 0.3:
            return ReasoningQuality.POOR
        else:
            return ReasoningQuality.FAILED


@dataclass
class UncertaintyProfile:
    """Profile of uncertainties in current knowledge state"""
    epistemic_gaps: List[str]          # What we don't know but could learn
    aleatoric_limits: List[str]        # Irreducible uncertainties
    model_limitations: List[str]       # Where our models fail

    # Quantitative
    overall_uncertainty: float = 0.5   # 0 = certain, 1 = completely uncertain
    reducible_fraction: float = 0.5    # Fraction that could be reduced

    # Prioritized gaps
    high_value_unknowns: List[str] = field(default_factory=list)  # Most valuable to learn


@dataclass
class BiasReport:
    """Report on potential biases in reasoning"""
    bias_type: BiasType
    evidence: List[str]                # Why we suspect this bias
    severity: float                    # 0-1, how much it affects reasoning
    mitigation_strategy: str           # How to counteract


@dataclass
class StrategyRecommendation:
    """Recommendation for which reasoning strategy to use"""
    strategy: ReasoningStrategy
    rationale: str
    expected_quality: float
    expected_time: str                 # "fast", "moderate", "slow"
    requirements: List[str]            # What's needed to use this strategy


@dataclass
class MetacognitiveInsight:
    """An insight about the reasoning process itself"""
    insight_id: str
    category: str                      # "pattern", "weakness", "improvement"
    description: str
    evidence: List[str]
    confidence: float

    actionable: bool = True
    suggested_action: Optional[str] = None

    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.insight_id:
            self.insight_id = f"INS-{uuid.uuid4().hex[:8]}"


class ReasoningQualityAssessor:
    """Assesses the quality of reasoning processes"""

    def __init__(self):
        self.quality_criteria = {
            "coherence": self._assess_coherence,
            "completeness": self._assess_completeness,
            "grounding": self._assess_grounding,
            "novelty": self._assess_novelty,
            "efficiency": self._assess_efficiency
        }

    def assess(self, trace: ReasoningTrace) -> Dict[str, float]:
        """Comprehensive quality assessment"""
        scores = {}
        for criterion, assessor in self.quality_criteria.items():
            scores[criterion] = assessor(trace)

        scores["overall"] = sum(scores.values()) / len(scores)
        return scores

    def _assess_coherence(self, trace: ReasoningTrace) -> float:
        """Check internal consistency of reasoning"""
        if not trace.steps:
            return 0.0

        # Check for contradictions
        conclusions = []
        for step in trace.steps:
            if "conclusion" in step:
                conclusions.append(step["conclusion"])

        # Simple heuristic: more conclusions without conflicts = more coherent
        if len(conclusions) <= 1:
            return 0.8

        # Check for obvious contradictions
        contradiction_indicators = [
            ("increase", "decrease"),
            ("true", "false"),
            ("positive", "negative"),
            ("always", "never")
        ]

        contradiction_count = 0
        for c1 in conclusions:
            c1_lower = c1.lower() if isinstance(c1, str) else str(c1).lower()
            for c2 in conclusions:
                c2_lower = c2.lower() if isinstance(c2, str) else str(c2).lower()
                for pos, neg in contradiction_indicators:
                    if pos in c1_lower and neg in c2_lower:
                        contradiction_count += 1

        coherence = max(0, 1.0 - contradiction_count * 0.2)
        return coherence

    def _assess_completeness(self, trace: ReasoningTrace) -> float:
        """Check if reasoning considered all relevant factors"""
        completeness = 0.5

        # More steps generally means more thorough
        step_bonus = min(0.3, len(trace.steps) * 0.05)
        completeness += step_bonus

        # More alternatives considered = more complete
        alt_bonus = min(0.2, trace.alternatives_considered * 0.05)
        completeness += alt_bonus

        # Penalty for unresolved uncertainties
        uncertainty_penalty = min(0.3, len(trace.uncertainties) * 0.1)
        completeness -= uncertainty_penalty

        return max(0, min(1, completeness))

    def _assess_grounding(self, trace: ReasoningTrace) -> float:
        """Check if reasoning is grounded in evidence"""
        grounding = 0.5

        # Check for evidence references in steps
        evidence_count = 0
        for step in trace.steps:
            if "evidence" in step or "data" in step or "observation" in step:
                evidence_count += 1

        if trace.steps:
            grounding = evidence_count / len(trace.steps)

        return grounding

    def _assess_novelty(self, trace: ReasoningTrace) -> float:
        """Check if reasoning produced novel insights"""
        # This is harder to assess automatically
        # Use heuristics based on strategy and alternatives
        novelty = 0.5

        if trace.strategy_used in [ReasoningStrategy.ANALOGICAL,
                                    ReasoningStrategy.ABDUCTIVE,
                                    ReasoningStrategy.COUNTERFACTUAL]:
            novelty += 0.2

        if trace.alternatives_considered >= 3:
            novelty += 0.1

        return min(1.0, novelty)

    def _assess_efficiency(self, trace: ReasoningTrace) -> float:
        """Check resource efficiency of reasoning"""
        # More quality per unit time = more efficient
        quality = (trace.coherence + trace.completeness + trace.confidence) / 3

        # Normalize time (assume 1000ms is "average")
        time_factor = 1000 / max(1, trace.time_taken_ms)
        time_factor = min(2.0, max(0.5, time_factor))

        efficiency = quality * time_factor
        return min(1.0, efficiency)


class UncertaintyMonitor:
    """Monitors and tracks uncertainties in the system's knowledge"""

    def __init__(self):
        self.known_unknowns: Dict[str, UncertaintyType] = {}
        self.uncertainty_history: List[Dict[str, Any]] = []

    def register_uncertainty(
        self,
        description: str,
        uncertainty_type: UncertaintyType,
        reducible: bool = True,
        importance: float = 0.5
    ):
        """Register a known uncertainty"""
        self.known_unknowns[description] = uncertainty_type
        self.uncertainty_history.append({
            "description": description,
            "type": uncertainty_type,
            "reducible": reducible,
            "importance": importance,
            "timestamp": datetime.now()
        })

    def get_uncertainty_profile(self) -> UncertaintyProfile:
        """Get current uncertainty profile"""
        epistemic = [d for d, t in self.known_unknowns.items()
                     if t == UncertaintyType.EPISTEMIC]
        aleatoric = [d for d, t in self.known_unknowns.items()
                     if t == UncertaintyType.ALEATORIC]
        model = [d for d, t in self.known_unknowns.items()
                 if t == UncertaintyType.MODEL]

        # Calculate overall uncertainty
        if not self.known_unknowns:
            overall = 0.3  # Some baseline uncertainty
        else:
            overall = min(1.0, len(self.known_unknowns) * 0.1)

        # Reducible fraction
        reducible_types = [UncertaintyType.EPISTEMIC, UncertaintyType.MEASUREMENT]
        reducible = sum(1 for t in self.known_unknowns.values() if t in reducible_types)
        reducible_frac = reducible / len(self.known_unknowns) if self.known_unknowns else 0.5

        # High-value unknowns
        high_value = []
        for item in self.uncertainty_history:
            if item.get("importance", 0) >= 0.7 and item.get("reducible", True):
                high_value.append(item["description"])

        return UncertaintyProfile(
            epistemic_gaps=epistemic,
            aleatoric_limits=aleatoric,
            model_limitations=model,
            overall_uncertainty=overall,
            reducible_fraction=reducible_frac,
            high_value_unknowns=high_value[:5]
        )

    def resolve_uncertainty(self, description: str):
        """Mark an uncertainty as resolved"""
        if description in self.known_unknowns:
            del self.known_unknowns[description]


class BiasDetector:
    """Detects potential cognitive biases in reasoning"""

    def __init__(self):
        self.bias_patterns = {
            BiasType.CONFIRMATION: self._detect_confirmation_bias,
            BiasType.ANCHORING: self._detect_anchoring_bias,
            BiasType.OVERCONFIDENCE: self._detect_overconfidence,
            BiasType.BASE_RATE_NEGLECT: self._detect_base_rate_neglect,
        }

    def detect_biases(self, trace: ReasoningTrace) -> List[BiasReport]:
        """Detect potential biases in reasoning trace"""
        reports = []

        for bias_type, detector in self.bias_patterns.items():
            report = detector(trace)
            if report and report.severity > 0.3:
                reports.append(report)

        return reports

    def _detect_confirmation_bias(self, trace: ReasoningTrace) -> Optional[BiasReport]:
        """Detect confirmation bias"""
        evidence = []
        severity = 0.0

        # Check if only supporting evidence was considered
        if trace.alternatives_considered == 0:
            evidence.append("No alternatives considered")
            severity += 0.3

        # Check for one-sided reasoning
        supporting = 0
        contradicting = 0
        for step in trace.steps:
            step_str = str(step).lower()
            if "supports" in step_str or "confirms" in step_str:
                supporting += 1
            if "contradicts" in step_str or "refutes" in step_str:
                contradicting += 1

        if supporting > 0 and contradicting == 0:
            evidence.append(f"Only supporting evidence ({supporting} instances)")
            severity += 0.3

        if severity > 0:
            return BiasReport(
                bias_type=BiasType.CONFIRMATION,
                evidence=evidence,
                severity=min(1.0, severity),
                mitigation_strategy="Actively seek disconfirming evidence; consider alternative hypotheses"
            )
        return None

    def _detect_anchoring_bias(self, trace: ReasoningTrace) -> Optional[BiasReport]:
        """Detect anchoring bias"""
        evidence = []
        severity = 0.0

        # Check if early values dominated
        if len(trace.steps) >= 3:
            first_step = str(trace.steps[0])
            last_step = str(trace.steps[-1])

            # If conclusion closely mirrors first step, might be anchoring
            if trace.conclusion and str(trace.conclusion)[:50] in first_step:
                evidence.append("Conclusion closely mirrors initial framing")
                severity += 0.4

        if severity > 0:
            return BiasReport(
                bias_type=BiasType.ANCHORING,
                evidence=evidence,
                severity=min(1.0, severity),
                mitigation_strategy="Consider problem from multiple starting points; defer conclusions"
            )
        return None

    def _detect_overconfidence(self, trace: ReasoningTrace) -> Optional[BiasReport]:
        """Detect overconfidence"""
        evidence = []
        severity = 0.0

        # High confidence with little evidence
        if trace.confidence > 0.8 and len(trace.steps) < 3:
            evidence.append(f"High confidence ({trace.confidence:.2f}) with few reasoning steps")
            severity += 0.4

        # High confidence with unresolved uncertainties
        if trace.confidence > 0.8 and len(trace.uncertainties) > 2:
            evidence.append("High confidence despite multiple uncertainties")
            severity += 0.3

        if severity > 0:
            return BiasReport(
                bias_type=BiasType.OVERCONFIDENCE,
                evidence=evidence,
                severity=min(1.0, severity),
                mitigation_strategy="Calibrate confidence based on evidence quality; consider unknown unknowns"
            )
        return None

    def _detect_base_rate_neglect(self, trace: ReasoningTrace) -> Optional[BiasReport]:
        """Detect base rate neglect"""
        evidence = []
        severity = 0.0

        # Check if prior probabilities were considered
        prior_mentioned = False
        for step in trace.steps:
            step_str = str(step).lower()
            if any(term in step_str for term in ["prior", "base rate", "baseline", "prevalence"]):
                prior_mentioned = True
                break

        if not prior_mentioned and trace.strategy_used == ReasoningStrategy.PROBABILISTIC:
            evidence.append("Probabilistic reasoning without explicit prior consideration")
            severity += 0.4

        if severity > 0:
            return BiasReport(
                bias_type=BiasType.BASE_RATE_NEGLECT,
                evidence=evidence,
                severity=min(1.0, severity),
                mitigation_strategy="Explicitly state and use base rates in probability estimates"
            )
        return None


class StrategySelector:
    """Selects appropriate reasoning strategies for tasks"""

    def __init__(self):
        self.strategy_profiles = {
            ReasoningStrategy.DEDUCTIVE: {
                "best_for": ["logical inference", "theorem proving", "rule application"],
                "quality": 0.9,
                "speed": "moderate",
                "requirements": ["clear premises", "logical rules"]
            },
            ReasoningStrategy.INDUCTIVE: {
                "best_for": ["pattern recognition", "generalization", "trend analysis"],
                "quality": 0.7,
                "speed": "fast",
                "requirements": ["multiple observations", "representative samples"]
            },
            ReasoningStrategy.ABDUCTIVE: {
                "best_for": ["explanation", "diagnosis", "hypothesis generation"],
                "quality": 0.75,
                "speed": "moderate",
                "requirements": ["observations to explain", "background knowledge"]
            },
            ReasoningStrategy.ANALOGICAL: {
                "best_for": ["novel domains", "creative solutions", "knowledge transfer"],
                "quality": 0.65,
                "speed": "moderate",
                "requirements": ["source domain knowledge", "structural similarity"]
            },
            ReasoningStrategy.CAUSAL: {
                "best_for": ["intervention planning", "prediction", "explanation"],
                "quality": 0.85,
                "speed": "slow",
                "requirements": ["causal model", "intervention data"]
            },
            ReasoningStrategy.PROBABILISTIC: {
                "best_for": ["uncertainty quantification", "risk assessment", "updating beliefs"],
                "quality": 0.8,
                "speed": "moderate",
                "requirements": ["prior distributions", "likelihood functions"]
            },
            ReasoningStrategy.COUNTERFACTUAL: {
                "best_for": ["alternative analysis", "responsibility attribution", "policy evaluation"],
                "quality": 0.75,
                "speed": "slow",
                "requirements": ["causal model", "factual baseline"]
            }
        }

        # Track strategy performance
        self.strategy_history: Dict[ReasoningStrategy, List[float]] = defaultdict(list)

    def recommend_strategy(
        self,
        task_description: str,
        available_resources: List[str],
        time_budget: str = "moderate"
    ) -> List[StrategyRecommendation]:
        """Recommend strategies for a task"""
        recommendations = []

        task_lower = task_description.lower()

        for strategy, profile in self.strategy_profiles.items():
            score = 0.0

            # Check if task matches strategy strengths
            for strength in profile["best_for"]:
                if any(word in task_lower for word in strength.split()):
                    score += 0.3

            # Check if requirements are met
            requirements_met = 0
            for req in profile["requirements"]:
                if any(req_word in task_lower or req_word in str(available_resources).lower()
                       for req_word in req.split()):
                    requirements_met += 1

            req_score = requirements_met / len(profile["requirements"]) if profile["requirements"] else 0.5
            score += 0.3 * req_score

            # Consider speed
            speed_match = {
                "fast": {"fast": 1.0, "moderate": 0.5, "slow": 0.2},
                "moderate": {"fast": 0.8, "moderate": 1.0, "slow": 0.6},
                "slow": {"fast": 0.6, "moderate": 0.8, "slow": 1.0}
            }
            score += 0.2 * speed_match.get(time_budget, {}).get(profile["speed"], 0.5)

            # Factor in historical performance
            if strategy in self.strategy_history and self.strategy_history[strategy]:
                avg_perf = sum(self.strategy_history[strategy]) / len(self.strategy_history[strategy])
                score += 0.2 * avg_perf

            if score > 0.3:
                recommendations.append(StrategyRecommendation(
                    strategy=strategy,
                    rationale=f"Matches: {', '.join(profile['best_for'][:2])}",
                    expected_quality=profile["quality"],
                    expected_time=profile["speed"],
                    requirements=profile["requirements"]
                ))

        # Sort by expected quality * task match
        recommendations.sort(key=lambda r: r.expected_quality, reverse=True)
        return recommendations[:3]

    def record_performance(self, strategy: ReasoningStrategy, quality: float):
        """Record strategy performance for learning"""
        self.strategy_history[strategy].append(quality)

        # Keep only recent history
        if len(self.strategy_history[strategy]) > 100:
            self.strategy_history[strategy] = self.strategy_history[strategy][-50:]


class MetacognitiveController:
    """
    Main metacognitive controller.
    Monitors reasoning, detects issues, and generates self-reflective insights.
    """

    def __init__(self):
        self.quality_assessor = ReasoningQualityAssessor()
        self.uncertainty_monitor = UncertaintyMonitor()
        self.bias_detector = BiasDetector()
        self.strategy_selector = StrategySelector()

        self.reasoning_traces: Dict[str, ReasoningTrace] = {}
        self.insights: Dict[str, MetacognitiveInsight] = {}

        # Aggregate metrics
        self.total_reasoning_episodes = 0
        self.quality_distribution: Dict[ReasoningQuality, int] = defaultdict(int)
        self.bias_frequency: Dict[BiasType, int] = defaultdict(int)

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        """Register event callback"""
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any):
        """Emit event"""
        for callback in self._callbacks[event]:
            callback(data)

    def begin_reasoning(
        self,
        task_description: str,
        strategy: ReasoningStrategy = None,
        available_resources: List[str] = None
    ) -> str:
        """Begin a reasoning episode"""
        # Select strategy if not provided
        if strategy is None:
            recommendations = self.strategy_selector.recommend_strategy(
                task_description,
                available_resources or [],
                "moderate"
            )
            strategy = recommendations[0].strategy if recommendations else ReasoningStrategy.SYSTEMATIC

        trace = ReasoningTrace(
            trace_id="",
            task_description=task_description,
            strategy_used=strategy,
            steps=[],
            capabilities_invoked=[],
            time_taken_ms=0
        )

        self.reasoning_traces[trace.trace_id] = trace
        self._emit("reasoning_started", trace)

        return trace.trace_id

    def add_reasoning_step(
        self,
        trace_id: str,
        step_type: str,
        content: Any,
        confidence: float = 0.5
    ):
        """Add a step to the reasoning trace"""
        trace = self.reasoning_traces.get(trace_id)
        if not trace:
            return

        trace.steps.append({
            "type": step_type,
            "content": content,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })

    def record_capability_invocation(self, trace_id: str, capability: str):
        """Record that a capability was invoked"""
        trace = self.reasoning_traces.get(trace_id)
        if trace:
            trace.capabilities_invoked.append(capability)

    def complete_reasoning(
        self,
        trace_id: str,
        conclusion: str,
        confidence: float,
        time_taken_ms: float
    ) -> Dict[str, Any]:
        """Complete a reasoning episode and analyze it"""
        trace = self.reasoning_traces.get(trace_id)
        if not trace:
            return {}

        trace.conclusion = conclusion
        trace.confidence = confidence
        trace.time_taken_ms = time_taken_ms

        # Assess quality
        quality_scores = self.quality_assessor.assess(trace)
        trace.coherence = quality_scores["coherence"]
        trace.completeness = quality_scores["completeness"]

        # Detect biases
        bias_reports = self.bias_detector.detect_biases(trace)
        trace.potential_biases = [r.bias_type for r in bias_reports]

        # Update aggregate metrics
        self.total_reasoning_episodes += 1
        self.quality_distribution[trace.quality] += 1
        for bias in trace.potential_biases:
            self.bias_frequency[bias] += 1

        # Record strategy performance
        self.strategy_selector.record_performance(
            trace.strategy_used,
            quality_scores["overall"]
        )

        # Generate insights if quality is poor
        if trace.quality in [ReasoningQuality.POOR, ReasoningQuality.FAILED]:
            insight = self._generate_improvement_insight(trace, quality_scores, bias_reports)
            if insight:
                self.insights[insight.insight_id] = insight
                self._emit("insight_generated", insight)

        self._emit("reasoning_completed", {
            "trace": trace,
            "quality": quality_scores,
            "biases": bias_reports
        })

        return {
            "trace_id": trace_id,
            "quality": trace.quality.name,
            "scores": quality_scores,
            "biases": [r.bias_type.name for r in bias_reports],
            "suggestions": [r.mitigation_strategy for r in bias_reports]
        }

    def _generate_improvement_insight(
        self,
        trace: ReasoningTrace,
        quality_scores: Dict[str, float],
        bias_reports: List[BiasReport]
    ) -> Optional[MetacognitiveInsight]:
        """Generate insight about how to improve reasoning"""
        # Find the weakest quality dimension
        weakest = min(quality_scores.items(), key=lambda x: x[1] if x[0] != "overall" else 1.0)

        evidence = [
            f"Task: {trace.task_description[:100]}",
            f"Strategy: {trace.strategy_used.name}",
            f"Quality: {trace.quality.name}",
            f"Weakest dimension: {weakest[0]} ({weakest[1]:.2f})"
        ]

        if bias_reports:
            evidence.append(f"Biases detected: {', '.join(b.bias_type.name for b in bias_reports)}")

        # Suggest action based on weakness
        actions = {
            "coherence": "Implement explicit consistency checking between reasoning steps",
            "completeness": "Use systematic exploration to cover all relevant factors",
            "grounding": "Require explicit evidence links for each conclusion",
            "novelty": "Try alternative reasoning strategies or cross-domain analogies",
            "efficiency": "Consider heuristic methods for initial exploration"
        }

        return MetacognitiveInsight(
            insight_id="",
            category="improvement",
            description=f"Reasoning quality issue: {weakest[0]} scored {weakest[1]:.2f}",
            evidence=evidence,
            confidence=0.7,
            actionable=True,
            suggested_action=actions.get(weakest[0], "Review reasoning process")
        )

    def register_uncertainty(
        self,
        description: str,
        uncertainty_type: UncertaintyType,
        importance: float = 0.5
    ):
        """Register an uncertainty"""
        self.uncertainty_monitor.register_uncertainty(
            description, uncertainty_type, True, importance
        )
        self._emit("uncertainty_registered", {
            "description": description,
            "type": uncertainty_type.name,
            "importance": importance
        })

    def get_uncertainty_profile(self) -> UncertaintyProfile:
        """Get current uncertainty profile"""
        return self.uncertainty_monitor.get_uncertainty_profile()

    def recommend_strategy(
        self,
        task: str,
        resources: List[str] = None,
        time_budget: str = "moderate"
    ) -> List[StrategyRecommendation]:
        """Get strategy recommendations"""
        return self.strategy_selector.recommend_strategy(
            task, resources or [], time_budget
        )

    def get_metacognitive_summary(self) -> Dict[str, Any]:
        """Get summary of metacognitive state"""
        return {
            "total_episodes": self.total_reasoning_episodes,
            "quality_distribution": {k.name: v for k, v in self.quality_distribution.items()},
            "common_biases": sorted(
                [(k.name, v) for k, v in self.bias_frequency.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "uncertainty_profile": {
                "overall": self.uncertainty_monitor.get_uncertainty_profile().overall_uncertainty,
                "reducible_fraction": self.uncertainty_monitor.get_uncertainty_profile().reducible_fraction,
                "high_value_unknowns": self.uncertainty_monitor.get_uncertainty_profile().high_value_unknowns
            },
            "recent_insights": [
                {"category": i.category, "description": i.description}
                for i in list(self.insights.values())[-5:]
            ]
        }

    def reflect_on_performance(self) -> List[MetacognitiveInsight]:
        """Generate insights from overall performance analysis"""
        insights = []

        # Check for systematic issues
        if self.total_reasoning_episodes >= 5:
            # Quality trend
            poor_count = self.quality_distribution.get(ReasoningQuality.POOR, 0)
            failed_count = self.quality_distribution.get(ReasoningQuality.FAILED, 0)
            low_quality_rate = (poor_count + failed_count) / self.total_reasoning_episodes

            if low_quality_rate > 0.3:
                insights.append(MetacognitiveInsight(
                    insight_id="",
                    category="pattern",
                    description=f"High rate of low-quality reasoning ({low_quality_rate:.0%})",
                    evidence=[
                        f"Poor: {poor_count}, Failed: {failed_count}",
                        f"Total episodes: {self.total_reasoning_episodes}"
                    ],
                    confidence=0.8,
                    actionable=True,
                    suggested_action="Review strategy selection and bias mitigation"
                ))

            # Common biases
            for bias_type, count in self.bias_frequency.items():
                if count / self.total_reasoning_episodes > 0.2:
                    insights.append(MetacognitiveInsight(
                        insight_id="",
                        category="weakness",
                        description=f"Frequent {bias_type.name} bias ({count} occurrences)",
                        evidence=[
                            f"Rate: {count/self.total_reasoning_episodes:.0%}",
                        ],
                        confidence=0.75,
                        actionable=True,
                        suggested_action=self.bias_detector.bias_patterns.get(
                            bias_type, lambda x: None
                        ).__doc__ or "Implement bias-specific mitigation"
                    ))

        # Store insights
        for insight in insights:
            self.insights[insight.insight_id] = insight

        return insights


# Singleton instance
_metacognitive_controller: Optional[MetacognitiveController] = None


def get_metacognitive_controller() -> MetacognitiveController:
    """Get or create the global metacognitive controller"""
    global _metacognitive_controller
    if _metacognitive_controller is None:
        _metacognitive_controller = MetacognitiveController()
    return _metacognitive_controller
