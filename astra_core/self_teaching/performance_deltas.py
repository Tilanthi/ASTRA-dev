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
Performance Delta Analyzer for Autocatalytic Self-Compiler

Analyzes performance differences between simulation and real-world
execution to identify bottlenecks and improvement opportunities.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import time


class MetricType(Enum):
    """Types of performance metrics"""
    LATENCY = "latency"           # Response time
    ACCURACY = "accuracy"         # Answer quality
    THROUGHPUT = "throughput"     # Requests per second
    MEMORY = "memory"             # Memory usage
    CPU = "cpu"                   # CPU usage
    CONFIDENCE = "confidence"     # Prediction confidence
    USER_SATISFACTION = "satisfaction"  # User feedback


@dataclass
class PerformanceMetric:
    """A single performance metric"""
    metric_type: MetricType
    value: float
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceDelta:
    """Difference in performance between two states"""
    metric_type: MetricType
    simulation_value: float
    real_world_value: float
    delta: float  # real_world - simulation
    percent_change: float
    magnitude: str  # "negligible", "minor", "moderate", "significant"
    timestamp: float


@dataclass
class Bottleneck:
    """Identified performance bottleneck"""
    component: str
    severity: float  # 0.0 to 1.0
    metric_type: MetricType
    description: str
    suggested_mutations: List[str]
    estimated_improvement: float


@dataclass
class PerformanceProfile:
    """Overall performance profile"""
    version_id: str
    metrics: Dict[MetricType, float]
    timestamp: float
    test_queries: List[str]
    scores: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceDeltaAnalyzer:
    """
    Analyzes performance deltas between simulation and real-world execution.

    Uses delta analysis to identify:
    - Bottlenecks in cognitive architecture
    - Opportunities for optimization
    - Areas where simulation diverges from reality
    """

    def __init__(self):
        self.simulation_metrics: List[PerformanceMetric] = []
        self.real_world_metrics: List[PerformanceMetric] = []
        self.deltas: List[PerformanceDelta] = []
        self.bottlenecks: List[Bottleneck] = []
        self.profiles: Dict[str, PerformanceProfile] = {}

    def record_simulation_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric from simulation."""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=time.time(),
            context=context or {}
        )
        self.simulation_metrics.append(metric)

    def record_real_world_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric from real-world execution."""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=time.time(),
            context=context or {}
        )
        self.real_world_metrics.append(metric)

    def analyze_delta(
        self,
        metric_type: MetricType,
        time_window: float = 300.0
    ) -> Optional[PerformanceDelta]:
        """Analyze delta for a specific metric type."""
        current_time = time.time()
        start_time = current_time - time_window

        # Get recent metrics
        sim_values = [
            m.value for m in self.simulation_metrics
            if m.metric_type == metric_type and m.timestamp >= start_time
        ]
        real_values = [
            m.value for m in self.real_world_metrics
            if m.metric_type == metric_type and m.timestamp >= start_time
        ]

        if not sim_values or not real_values:
            return None

        # Calculate averages
        sim_avg = sum(sim_values) / len(sim_values)
        real_avg = sum(real_values) / len(real_values)

        delta = real_avg - sim_avg
        percent_change = (delta / sim_avg * 100) if sim_avg != 0 else 0

        # Determine magnitude
        if abs(percent_change) < 5:
            magnitude = "negligible"
        elif abs(percent_change) < 15:
            magnitude = "minor"
        elif abs(percent_change) < 30:
            magnitude = "moderate"
        else:
            magnitude = "significant"

        perf_delta = PerformanceDelta(
            metric_type=metric_type,
            simulation_value=sim_avg,
            real_world_value=real_avg,
            delta=delta,
            percent_change=percent_change,
            magnitude=magnitude,
            timestamp=current_time
        )

        self.deltas.append(perf_delta)
        return perf_delta

    def analyze_all_deltas(self, time_window: float = 300.0) -> List[PerformanceDelta]:
        """Analyze deltas for all metric types."""
        deltas = []

        for metric_type in MetricType:
            delta = self.analyze_delta(metric_type, time_window)
            if delta:
                deltas.append(delta)

        return deltas

    def identify_bottlenecks(
        self,
        threshold: float = 0.3
    ) -> List[Bottleneck]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        component_metrics = defaultdict(list)

        # Group metrics by component
        for metric in self.real_world_metrics:
            component = metric.context.get("component", "unknown")
            component_metrics[component].append(metric)

        # Analyze each component
        for component, metrics in component_metrics.items():
            for metric_type in MetricType:
                values = [m.value for m in metrics if m.metric_type == metric_type]

                if values:
                    avg_value = sum(values) / len(values)

                    # Check if this is a bottleneck (lower is worse for most metrics)
                    is_bottleneck = False
                    severity = 0.0

                    if metric_type in [MetricType.LATENCY, MetricType.MEMORY, MetricType.CPU]:
                        # Lower is better
                        if avg_value > threshold:
                            is_bottleneck = True
                            severity = min(1.0, avg_value / threshold)
                    elif metric_type in [MetricType.ACCURACY, MetricType.CONFIDENCE, MetricType.USER_SATISFACTION]:
                        # Higher is better
                        if avg_value < (1.0 - threshold):
                            is_bottleneck = True
                            severity = min(1.0, (1.0 - avg_value) / threshold)

                    if is_bottleneck and severity > 0.3:
                        bottleneck = Bottleneck(
                            component=component,
                            severity=severity,
                            metric_type=metric_type,
                            description=f"Poor {metric_type.value} in {component}: {avg_value:.3f}",
                            suggested_mutations=self._generate_suggestions(component, metric_type, severity),
                            estimated_improvement=severity * 0.5
                        )
                        bottlenecks.append(bottleneck)

        # Sort by severity
        bottlenecks.sort(key=lambda b: b.severity, reverse=True)
        self.bottlenecks = bottlenecks

        return bottlenecks

    def _generate_suggestions(
        self,
        component: str,
        metric_type: MetricType,
        severity: float
    ) -> List[str]:
        """Generate mutation suggestions for a bottleneck."""
        suggestions = []

        if metric_type == MetricType.LATENCY:
            suggestions = [
                f"Add caching to {component}",
                f"Optimize algorithm in {component}",
                f"Parallelize operations in {component}"
            ]
        elif metric_type == MetricType.ACCURACY:
            suggestions = [
                f"Enhance knowledge base for {component}",
                f"Adjust confidence thresholds in {component}",
                f"Add ensemble methods to {component}"
            ]
        elif metric_type == MetricType.MEMORY:
            suggestions = [
                f"Implement streaming in {component}",
                f"Add lazy loading to {component}",
                f"Optimize data structures in {component}"
            ]
        elif metric_type == MetricType.CPU:
            suggestions = [
                f"Add batching to {component}",
                f"Implement memoization in {component}",
                f"Reduce redundant calculations in {component}"
            ]
        else:
            suggestions = [
                f"Review and optimize {component}",
                f"Add monitoring to {component}"
            ]

        return suggestions

    def create_profile(
        self,
        version_id: str,
        metrics: Dict[MetricType, float],
        test_queries: List[str],
        scores: Optional[Dict[str, float]] = None
    ) -> PerformanceProfile:
        """Create a performance profile for a version."""
        profile = PerformanceProfile(
            version_id=version_id,
            metrics=metrics,
            timestamp=time.time(),
            test_queries=test_queries,
            scores=scores or {}
        )
        self.profiles[version_id] = profile
        return profile

    def compare_profiles(
        self,
        version_1: str,
        version_2: str
    ) -> Dict[str, Any]:
        """Compare two performance profiles."""
        if version_1 not in self.profiles or version_2 not in self.profiles:
            return {"error": "One or both versions not found"}

        profile_1 = self.profiles[version_1]
        profile_2 = self.profiles[version_2]

        comparison = {
            "version_1": version_1,
            "version_2": version_2,
            "timestamp_1": profile_1.timestamp,
            "timestamp_2": profile_2.timestamp,
            "metric_deltas": {},
            "score_deltas": {}
        }

        # Compare metrics
        for metric_type in profile_1.metrics:
            if metric_type in profile_2.metrics:
                value_1 = profile_1.metrics[metric_type]
                value_2 = profile_2.metrics[metric_type]
                delta = value_2 - value_1
                percent = (delta / value_1 * 100) if value_1 != 0 else 0

                comparison["metric_deltas"][metric_type.value] = {
                    "value_1": value_1,
                    "value_2": value_2,
                    "delta": delta,
                    "percent_change": percent
                }

        # Compare scores
        for score_name in profile_1.scores:
            if score_name in profile_2.scores:
                score_1 = profile_1.scores[score_name]
                score_2 = profile_2.scores[score_name]
                delta = score_2 - score_1

                comparison["score_deltas"][score_name] = {
                    "score_1": score_1,
                    "score_2": score_2,
                    "delta": delta
                }

        # Determine overall improvement
        metric_improvements = sum(
            1 for d in comparison["metric_deltas"].values()
            if self._is_improvement(d["delta"], d.get("value_1", 0))
        )

        comparison["overall_improvement"] = (
            metric_improvements / len(comparison["metric_deltas"])
            if comparison["metric_deltas"] else 0
        )

        return comparison

    def _is_improvement(self, delta: float, baseline: float) -> bool:
        """Determine if a delta represents improvement."""
        # For most metrics, positive delta is improvement
        # For latency, memory, CPU: negative is improvement
        return delta > 0

    def get_trend(
        self,
        metric_type: MetricType,
        window_size: int = 10
    ) -> Optional[str]:
        """Get trend direction for a metric."""
        relevant_deltas = [
            d for d in self.deltas
            if d.metric_type == metric_type
        ]

        if len(relevant_deltas) < window_size:
            return "insufficient_data"

        recent_deltas = relevant_deltas[-window_size:]
        avg_delta = sum(d.delta for d in recent_deltas) / len(recent_deltas)

        if abs(avg_delta) < 0.05:
            return "stable"
        elif avg_delta > 0:
            return "improving"
        else:
            return "degrading"

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of performance analysis."""
        recent_deltas = self.analyze_all_deltas()

        return {
            "total_simulation_metrics": len(self.simulation_metrics),
            "total_real_world_metrics": len(self.real_world_metrics),
            "total_deltas": len(self.deltas),
            "recent_deltas": [
                {
                    "type": d.metric_type.value,
                    "delta": d.delta,
                    "percent": d.percent_change,
                    "magnitude": d.magnitude
                }
                for d in recent_deltas
            ],
            "bottlenecks": [
                {
                    "component": b.component,
                    "severity": b.severity,
                    "metric": b.metric_type.value,
                    "description": b.description
                }
                for b in self.bottlenecks[:5]
            ],
            "profiles": list(self.profiles.keys())
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_performance_delta_analyzer() -> PerformanceDeltaAnalyzer:
    """Create a performance delta analyzer."""
    return PerformanceDeltaAnalyzer()
