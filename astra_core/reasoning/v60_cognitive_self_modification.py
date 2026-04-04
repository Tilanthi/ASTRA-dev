"""
V60 Cognitive Self-Modification

Recursive self-improvement system enabling the agent to:
- Monitor its own cognitive performance
- Identify bottlenecks and failure modes
- Propose and evaluate modifications
- Safely apply improvements with rollback

Key innovations:
1. Performance introspection with detailed metrics
2. Strategy evaluation comparing alternatives
3. Safe modification with sandboxed testing
4. Rollback capabilities for failed modifications
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, TypeVar
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict
import copy
import time
import hashlib
import json


T = TypeVar('T')


class ModificationType(Enum):
    """Types of self-modifications"""
    PARAMETER_TUNING = "parameter_tuning"
    STRATEGY_SELECTION = "strategy_selection"
    COMPONENT_REPLACEMENT = "component_replacement"
    ARCHITECTURE_CHANGE = "architecture_change"
    KNOWLEDGE_RESTRUCTURE = "knowledge_restructure"
    ATTENTION_REWEIGHTING = "attention_reweighting"


class PerformanceMetric(Enum):
    """Performance metrics to monitor"""
    ACCURACY = "accuracy"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    GENERALIZATION = "generalization"
    ROBUSTNESS = "robustness"


class ModificationStatus(Enum):
    """Status of a modification"""
    PROPOSED = "proposed"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


class SafetyLevel(Enum):
    """Safety levels for modifications"""
    SAFE = "safe"           # Reversible, low impact
    MODERATE = "moderate"   # Reversible, medium impact
    RISKY = "risky"        # Potentially irreversible, high impact
    CRITICAL = "critical"   # Major architectural change


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance at a point in time"""
    timestamp: float
    metrics: Dict[PerformanceMetric, float]
    context: Dict[str, Any]
    task_distribution: Dict[str, float]
    component_performance: Dict[str, Dict[str, float]]

    def compare(self, other: 'PerformanceSnapshot') -> Dict[str, float]:
        """Compare with another snapshot"""
        deltas = {}
        for metric, value in self.metrics.items():
            if metric in other.metrics:
                deltas[metric.value] = value - other.metrics[metric]
        return deltas


@dataclass
class BottleneckAnalysis:
    """Analysis of a performance bottleneck"""
    id: str
    location: str
    metric_affected: PerformanceMetric
    severity: float
    diagnosis: str
    potential_fixes: List[str]
    evidence: Dict[str, Any]


@dataclass
class ModificationProposal:
    """Proposed self-modification"""
    id: str
    modification_type: ModificationType
    description: str
    target_component: str
    changes: Dict[str, Any]
    expected_improvement: Dict[PerformanceMetric, float]
    safety_level: SafetyLevel
    status: ModificationStatus = ModificationStatus.PROPOSED
    evaluation_results: Optional[Dict[str, Any]] = None
    applied_at: Optional[float] = None
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class Strategy:
    """A cognitive strategy"""
    id: str
    name: str
    description: str
    applicability: Dict[str, float]  # context -> applicability score
    parameters: Dict[str, Any]
    performance_history: List[Dict[str, Any]] = field(default_factory=list)

    def get_average_performance(self, metric: str) -> float:
        """Get average performance for a metric"""
        if not self.performance_history:
            return 0.5
        values = [h.get(metric, 0.5) for h in self.performance_history]
        return np.mean(values)


class PerformanceMonitor:
    """
    Monitors cognitive performance across components.
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metric_history: Dict[PerformanceMetric, List[float]] = defaultdict(list)
        self.component_metrics: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.task_history: List[Dict[str, Any]] = []
        self.anomaly_threshold: float = 2.0  # Standard deviations

    def record(
        self,
        metric: PerformanceMetric,
        value: float,
        component: Optional[str] = None,
        task: Optional[Dict[str, Any]] = None
    ):
        """Record a performance measurement"""
        self.metric_history[metric].append(value)

        # Trim to window size
        if len(self.metric_history[metric]) > self.window_size:
            self.metric_history[metric] = self.metric_history[metric][-self.window_size:]

        if component:
            self.component_metrics[component][metric.value].append(value)
            if len(self.component_metrics[component][metric.value]) > self.window_size:
                self.component_metrics[component][metric.value] = \
                    self.component_metrics[component][metric.value][-self.window_size:]

        if task:
            self.task_history.append({
                'task': task,
                'metric': metric.value,
                'value': value,
                'timestamp': time.time()
            })
            if len(self.task_history) > self.window_size * 10:
                self.task_history = self.task_history[-self.window_size * 10:]

    def get_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        metrics = {}
        for metric, values in self.metric_history.items():
            if values:
                metrics[metric] = np.mean(values[-self.window_size:])

        component_perf = {}
        for component, comp_metrics in self.component_metrics.items():
            component_perf[component] = {
                k: np.mean(v[-self.window_size:]) if v else 0.0
                for k, v in comp_metrics.items()
            }

        task_dist = self._compute_task_distribution()

        return PerformanceSnapshot(
            timestamp=time.time(),
            metrics=metrics,
            context={'window_size': self.window_size},
            task_distribution=task_dist,
            component_performance=component_perf
        )

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect performance anomalies"""
        anomalies = []

        for metric, values in self.metric_history.items():
            if len(values) < 10:
                continue

            mean = np.mean(values)
            std = np.std(values)

            if std > 0:
                recent = values[-5:]
                for i, v in enumerate(recent):
                    z_score = abs(v - mean) / std
                    if z_score > self.anomaly_threshold:
                        anomalies.append({
                            'metric': metric.value,
                            'value': v,
                            'z_score': z_score,
                            'direction': 'high' if v > mean else 'low',
                            'severity': min(1.0, z_score / 5.0)
                        })

        return anomalies

    def _compute_task_distribution(self) -> Dict[str, float]:
        """Compute distribution of task types"""
        if not self.task_history:
            return {}

        type_counts = defaultdict(int)
        for entry in self.task_history[-100:]:
            task_type = entry.get('task', {}).get('type', 'unknown')
            type_counts[task_type] += 1

        total = sum(type_counts.values())
        return {k: v/total for k, v in type_counts.items()}


class BottleneckDetector:
    """
    Detects performance bottlenecks through analysis.
    """

    def __init__(self, performance_monitor: PerformanceMonitor):
        self.monitor = performance_monitor
        self.bottleneck_patterns = {
            'latency_spike': self._check_latency_spike,
            'accuracy_degradation': self._check_accuracy_degradation,
            'memory_pressure': self._check_memory_pressure,
            'confidence_miscalibration': self._check_calibration
        }

    def analyze(self) -> List[BottleneckAnalysis]:
        """Analyze for bottlenecks"""
        bottlenecks = []

        for pattern_name, check_fn in self.bottleneck_patterns.items():
            result = check_fn()
            if result:
                bottlenecks.append(result)

        # Analyze component-specific bottlenecks
        component_bottlenecks = self._analyze_components()
        bottlenecks.extend(component_bottlenecks)

        return sorted(bottlenecks, key=lambda b: b.severity, reverse=True)

    def _check_latency_spike(self) -> Optional[BottleneckAnalysis]:
        """Check for latency spikes"""
        latency_values = self.monitor.metric_history.get(PerformanceMetric.LATENCY, [])

        if len(latency_values) < 10:
            return None

        recent_mean = np.mean(latency_values[-10:])
        historical_mean = np.mean(latency_values[:-10]) if len(latency_values) > 10 else recent_mean

        if recent_mean > historical_mean * 1.5:
            return BottleneckAnalysis(
                id=f"bottleneck_latency_{time.time()}",
                location="system_wide",
                metric_affected=PerformanceMetric.LATENCY,
                severity=(recent_mean - historical_mean) / historical_mean,
                diagnosis=f"Latency increased by {(recent_mean/historical_mean - 1)*100:.1f}%",
                potential_fixes=[
                    "Optimize slow components",
                    "Enable caching",
                    "Reduce computational complexity"
                ],
                evidence={
                    'recent_mean': recent_mean,
                    'historical_mean': historical_mean
                }
            )
        return None

    def _check_accuracy_degradation(self) -> Optional[BottleneckAnalysis]:
        """Check for accuracy degradation"""
        accuracy_values = self.monitor.metric_history.get(PerformanceMetric.ACCURACY, [])

        if len(accuracy_values) < 20:
            return None

        # Check for trend
        first_half = np.mean(accuracy_values[:len(accuracy_values)//2])
        second_half = np.mean(accuracy_values[len(accuracy_values)//2:])

        if second_half < first_half * 0.95:
            return BottleneckAnalysis(
                id=f"bottleneck_accuracy_{time.time()}",
                location="reasoning_pipeline",
                metric_affected=PerformanceMetric.ACCURACY,
                severity=(first_half - second_half) / first_half,
                diagnosis=f"Accuracy degraded from {first_half:.2f} to {second_half:.2f}",
                potential_fixes=[
                    "Retrain models",
                    "Update knowledge base",
                    "Adjust confidence thresholds"
                ],
                evidence={
                    'first_half_accuracy': first_half,
                    'second_half_accuracy': second_half
                }
            )
        return None

    def _check_memory_pressure(self) -> Optional[BottleneckAnalysis]:
        """Check for memory pressure"""
        memory_values = self.monitor.metric_history.get(PerformanceMetric.MEMORY_USAGE, [])

        if len(memory_values) < 5:
            return None

        current = memory_values[-1]
        if current > 0.9:  # >90% memory usage
            return BottleneckAnalysis(
                id=f"bottleneck_memory_{time.time()}",
                location="memory_system",
                metric_affected=PerformanceMetric.MEMORY_USAGE,
                severity=current - 0.9,
                diagnosis=f"Memory usage at {current*100:.1f}%",
                potential_fixes=[
                    "Clear episodic memory cache",
                    "Consolidate semantic memory",
                    "Reduce working memory size"
                ],
                evidence={'current_usage': current}
            )
        return None

    def _check_calibration(self) -> Optional[BottleneckAnalysis]:
        """Check for confidence miscalibration"""
        calibration = self.monitor.metric_history.get(
            PerformanceMetric.CONFIDENCE_CALIBRATION, []
        )

        if len(calibration) < 10:
            return None

        recent_cal = np.mean(calibration[-10:])
        if abs(recent_cal - 1.0) > 0.2:  # Miscalibrated by >20%
            return BottleneckAnalysis(
                id=f"bottleneck_calibration_{time.time()}",
                location="confidence_system",
                metric_affected=PerformanceMetric.CONFIDENCE_CALIBRATION,
                severity=abs(recent_cal - 1.0),
                diagnosis=f"Confidence {'over' if recent_cal > 1 else 'under'}calibrated: {recent_cal:.2f}",
                potential_fixes=[
                    "Adjust confidence scaling",
                    "Recalibrate on validation set",
                    "Use temperature scaling"
                ],
                evidence={'calibration_ratio': recent_cal}
            )
        return None

    def _analyze_components(self) -> List[BottleneckAnalysis]:
        """Analyze component-specific bottlenecks"""
        bottlenecks = []

        for component, metrics in self.monitor.component_metrics.items():
            for metric_name, values in metrics.items():
                if len(values) < 10:
                    continue

                # Check if this component is underperforming
                mean = np.mean(values)
                std = np.std(values)

                # Compare to other components
                all_means = [
                    np.mean(m.get(metric_name, [0])) if m.get(metric_name) else 0
                    for m in self.monitor.component_metrics.values()
                ]
                if all_means:
                    overall_mean = np.mean(all_means)
                    if mean < overall_mean * 0.8:
                        bottlenecks.append(BottleneckAnalysis(
                            id=f"bottleneck_{component}_{metric_name}_{time.time()}",
                            location=component,
                            metric_affected=PerformanceMetric.ACCURACY,
                            severity=(overall_mean - mean) / overall_mean,
                            diagnosis=f"{component} underperforming on {metric_name}",
                            potential_fixes=[
                                f"Optimize {component}",
                                f"Replace {component} strategy",
                                f"Add caching for {component}"
                            ],
                            evidence={
                                'component_mean': mean,
                                'overall_mean': overall_mean
                            }
                        ))

        return bottlenecks


class StrategyEvaluator:
    """
    Evaluates and selects cognitive strategies.
    """

    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.evaluation_history: List[Dict[str, Any]] = []

    def register_strategy(self, strategy: Strategy):
        """Register a strategy"""
        self.strategies[strategy.id] = strategy

    def evaluate(
        self,
        strategy: Strategy,
        context: Dict[str, Any],
        trials: int = 10
    ) -> Dict[str, float]:
        """Evaluate strategy performance"""
        # Get applicability for context
        applicability = self._compute_applicability(strategy, context)

        # Simulate trials (in real system, would run actual trials)
        results = {
            'applicability': applicability,
            'expected_accuracy': strategy.get_average_performance('accuracy'),
            'expected_latency': strategy.get_average_performance('latency'),
            'confidence': min(1.0, len(strategy.performance_history) / 20)
        }

        self.evaluation_history.append({
            'strategy_id': strategy.id,
            'context': context,
            'results': results,
            'timestamp': time.time()
        })

        return results

    def select_best(
        self,
        context: Dict[str, Any],
        metric_weights: Optional[Dict[str, float]] = None
    ) -> Optional[Strategy]:
        """Select best strategy for context"""
        metric_weights = metric_weights or {
            'applicability': 0.3,
            'expected_accuracy': 0.5,
            'expected_latency': -0.2  # Lower is better
        }

        best_score = float('-inf')
        best_strategy = None

        for strategy in self.strategies.values():
            evaluation = self.evaluate(strategy, context)

            score = sum(
                evaluation.get(metric, 0) * weight
                for metric, weight in metric_weights.items()
            )

            if score > best_score:
                best_score = score
                best_strategy = strategy

        return best_strategy

    def compare_strategies(
        self,
        strategy_ids: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Compare multiple strategies"""
        results = {}
        for sid in strategy_ids:
            if sid in self.strategies:
                results[sid] = self.evaluate(self.strategies[sid], context)
        return results

    def _compute_applicability(
        self,
        strategy: Strategy,
        context: Dict[str, Any]
    ) -> float:
        """Compute how applicable a strategy is to context"""
        if not strategy.applicability:
            return 0.5

        score = 0
        count = 0

        for key, base_score in strategy.applicability.items():
            if key in context:
                # Exact match
                score += base_score
                count += 1
            elif any(key in str(v) for v in context.values()):
                # Partial match
                score += base_score * 0.5
                count += 1

        return score / max(count, 1)


class ModificationEngine:
    """
    Proposes and applies self-modifications.
    """

    def __init__(
        self,
        bottleneck_detector: BottleneckDetector,
        strategy_evaluator: StrategyEvaluator
    ):
        self.bottleneck_detector = bottleneck_detector
        self.strategy_evaluator = strategy_evaluator
        self.modification_templates: Dict[ModificationType, List[Dict[str, Any]]] = {
            ModificationType.PARAMETER_TUNING: [
                {'param': 'learning_rate', 'range': (0.001, 0.1)},
                {'param': 'temperature', 'range': (0.1, 2.0)},
                {'param': 'threshold', 'range': (0.1, 0.9)}
            ],
            ModificationType.STRATEGY_SELECTION: [
                {'strategy': 'depth_first', 'applicability': 'complex'},
                {'strategy': 'breadth_first', 'applicability': 'simple'},
                {'strategy': 'beam_search', 'applicability': 'uncertain'}
            ],
            ModificationType.ATTENTION_REWEIGHTING: [
                {'component': 'memory', 'weight_delta': 0.1},
                {'component': 'reasoning', 'weight_delta': 0.1},
                {'component': 'world_model', 'weight_delta': 0.1}
            ]
        }
        self.active_proposals: Dict[str, ModificationProposal] = {}

    def propose_modifications(
        self,
        bottlenecks: List[BottleneckAnalysis],
        max_proposals: int = 5
    ) -> List[ModificationProposal]:
        """Generate modification proposals for bottlenecks"""
        proposals = []

        for bottleneck in bottlenecks[:max_proposals]:
            modification = self._create_proposal_for_bottleneck(bottleneck)
            if modification:
                proposals.append(modification)
                self.active_proposals[modification.id] = modification

        return proposals

    def _create_proposal_for_bottleneck(
        self,
        bottleneck: BottleneckAnalysis
    ) -> Optional[ModificationProposal]:
        """Create a modification proposal for a bottleneck"""
        # Select modification type based on bottleneck
        if bottleneck.metric_affected == PerformanceMetric.LATENCY:
            mod_type = ModificationType.PARAMETER_TUNING
        elif bottleneck.metric_affected == PerformanceMetric.ACCURACY:
            mod_type = ModificationType.STRATEGY_SELECTION
        elif bottleneck.metric_affected == PerformanceMetric.MEMORY_USAGE:
            mod_type = ModificationType.ATTENTION_REWEIGHTING
        else:
            mod_type = ModificationType.PARAMETER_TUNING

        # Get template
        templates = self.modification_templates.get(mod_type, [])
        if not templates:
            return None

        template = np.random.choice(templates)

        # Create proposal
        proposal = ModificationProposal(
            id=f"mod_{bottleneck.id}_{time.time()}",
            modification_type=mod_type,
            description=f"Address {bottleneck.diagnosis} via {mod_type.value}",
            target_component=bottleneck.location,
            changes=template,
            expected_improvement={
                bottleneck.metric_affected: bottleneck.severity * 0.5
            },
            safety_level=self._assess_safety(mod_type, template)
        )

        return proposal

    def _assess_safety(
        self,
        mod_type: ModificationType,
        changes: Dict[str, Any]
    ) -> SafetyLevel:
        """Assess safety level of modification"""
        safety_map = {
            ModificationType.PARAMETER_TUNING: SafetyLevel.SAFE,
            ModificationType.ATTENTION_REWEIGHTING: SafetyLevel.SAFE,
            ModificationType.STRATEGY_SELECTION: SafetyLevel.MODERATE,
            ModificationType.KNOWLEDGE_RESTRUCTURE: SafetyLevel.MODERATE,
            ModificationType.COMPONENT_REPLACEMENT: SafetyLevel.RISKY,
            ModificationType.ARCHITECTURE_CHANGE: SafetyLevel.CRITICAL
        }
        return safety_map.get(mod_type, SafetyLevel.MODERATE)


class SafeModificationApplier:
    """
    Safely applies modifications with rollback capability.
    """

    def __init__(self):
        self.state_snapshots: Dict[str, Dict[str, Any]] = {}
        self.applied_modifications: List[ModificationProposal] = []
        self.rollback_stack: List[str] = []

    def apply(
        self,
        proposal: ModificationProposal,
        target_state: Dict[str, Any],
        sandbox_test: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """Apply modification with safety checks"""
        # Create rollback point
        snapshot_id = self._create_snapshot(target_state, proposal.id)
        proposal.rollback_data = {'snapshot_id': snapshot_id}

        # Sandbox test if enabled
        if sandbox_test:
            test_success = self._sandbox_test(proposal, target_state)
