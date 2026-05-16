"""
Phase 3: Observability Stack

Implements comprehensive observability for the orchestrated system:
- Metrics collection and aggregation
- Health checking
- System state monitoring
- Distributed tracing
- Performance profiling
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass
class MetricData:
    """Individual metric data point"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MetricAggregate:
    """Aggregated metric data"""
    name: str
    count: int = 0
    sum: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    avg: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    recent_values: List[float] = field(default_factory=list)

    def add_value(self, value: float):
        """Add a value to the aggregate"""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.avg = self.sum / self.count

        # Keep recent values for percentile calculation
        self.recent_values.append(value)
        if len(self.recent_values) > 100:
            self.recent_values.pop(0)

        # Recalculate percentiles
        if self.recent_values:
            sorted_values = sorted(self.recent_values)
            n = len(sorted_values)
            self.p50 = sorted_values[int(n * 0.5)]
            self.p95 = sorted_values[int(n * 0.95)]
            self.p99 = sorted_values[int(n * 0.99)]


class MetricsCollector:
    """
    Collects and aggregates metrics from the system.

    Provides:
    - Metric collection from components
    - Aggregation and statistics
    - Time-series storage (in-memory)
    - Query interface
    """

    def __init__(self, retention_period: timedelta = timedelta(hours=24)):
        self.retention_period = retention_period

        # Metric storage
        self.metrics: Dict[str, List[MetricData]] = defaultdict(list)
        self.aggregates: Dict[str, MetricAggregate] = {}

        # Component registration
        self.components: Dict[str, Callable] = {}

        # Collection loop
        self.running = False
        self.collection_interval = 10.0  # seconds

        logger.info("Metrics Collector initialized")

    def register_component(self, name: str, metrics_func: Callable):
        """Register a component for metrics collection"""
        self.components[name] = metrics_func
        logger.info(f"Registered component {name} for metrics collection")

    async def collect_from_component(self, name: str) -> Dict[str, float]:
        """Collect metrics from a specific component"""
        if name not in self.components:
            return {}

        try:
            metrics = await self._call_metrics_function(self.components[name])
            return metrics
        except Exception as e:
            logger.error(f"Error collecting metrics from {name}: {e}")
            return {}

    async def _call_metrics_function(self, func: Callable) -> Dict[str, float]:
        """Call a metrics function (sync or async)"""
        if asyncio.iscoroutinefunction(func):
            return await func()
        else:
            return func()

    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric data point"""
        labels = labels or {}

        metric = MetricData(
            name=name,
            value=value,
            labels=labels
        )

        # Store metric
        key = self._make_metric_key(name, labels)
        self.metrics[key].append(metric)

        # Update aggregate
        if key not in self.aggregates:
            self.aggregates[key] = MetricAggregate(name=name)
        self.aggregates[key].add_value(value)

        # Cleanup old metrics
        self._cleanup_old_metrics()

    def _make_metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key for a metric"""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}" if label_str else name

    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.now() - self.retention_period

        for key, metric_list in self.metrics.items():
            # Keep only recent metrics
            self.metrics[key] = [
                m for m in metric_list
                if m.timestamp > cutoff
            ]

    async def collect_all_metrics(self):
        """Collect metrics from all registered components"""
        for name in self.components:
            try:
                component_metrics = await self.collect_from_component(name)

                for metric_name, value in component_metrics.items():
                    self.record_metric(
                        f"{name}.{metric_name}",
                        value,
                        {"component": name}
                    )

            except Exception as e:
                logger.error(f"Error collecting from {name}: {e}")

    def query_metric(self, name: str, labels: Optional[Dict[str, str]] = None) -> MetricAggregate:
        """Query aggregated metric data"""
        key = self._make_metric_key(name, labels or {})

        if key not in self.aggregates:
            # Return empty aggregate
            return MetricAggregate(name=name)

        return self.aggregates[key]

    def get_recent_metrics(self,
                          name: str,
                          duration: timedelta = timedelta(minutes=5),
                          labels: Optional[Dict[str, str]] = None) -> List[MetricData]:
        """Get recent metric data points"""
        cutoff = datetime.now() - duration
        key = self._make_metric_key(name, labels or {})

        if key not in self.metrics:
            return []

        return [
            m for m in self.metrics[key]
            if m.timestamp > cutoff
        ]

    async def start_collection_loop(self):
        """Start the metrics collection loop"""
        self.running = True
        logger.info("Starting metrics collection loop")

        while self.running:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(self.collection_interval)

    def stop_collection_loop(self):
        """Stop the metrics collection loop"""
        self.running = False
        logger.info("Stopping metrics collection loop")

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        return {
            "total_metrics": len(self.metrics),
            "total_aggregates": len(self.aggregates),
            "registered_components": len(self.components),
            "metrics_by_component": {
                component: len([k for k in self.metrics.keys() if k.startswith(component)])
                for component in self.components
            },
        }


class HealthCheck:
    """
    Performs health checks on system components.

    Provides:
    - Component health checking
    - Dependency health checking
    - Aggregate health status
    - Health history
    """

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.check_results: List[HealthCheckResult] = []
        self.dependencies: Dict[str, List[str]] = {}

        # Check configuration
        self.default_timeout = 10.0
        self.default_interval = 30.0

        logger.info("Health Check initialized")

    def register_check(self,
                      component: str,
                      check_func: Callable,
                      dependencies: Optional[List[str]] = None):
        """Register a health check for a component"""
        self.checks[component] = check_func
        self.dependencies[component] = dependencies or []
        logger.info(f"Registered health check for {component}")

    async def check_component(self, component: str) -> HealthCheckResult:
        """Check health of a specific component"""
        start_time = datetime.now()

        if component not in self.checks:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNKNOWN,
                message=f"No health check registered for {component}"
            )

        try:
            # Check dependencies first
            for dep in self.dependencies.get(component, []):
                dep_result = await self.check_component(dep)
                if dep_result.status != HealthStatus.HEALTHY:
                    return HealthCheckResult(
                        component=component,
                        status=HealthStatus.DEGRADED,
                        message=f"Dependency {dep} is {dep_result.status.value}",
                        details={"dependency_status": dep_result.status.value}
                    )

            # Run component check
            if asyncio.iscoroutinefunction(self.checks[component]):
                result = await asyncio.wait_for(
                    self.checks[component](),
                    timeout=self.default_timeout
                )
            else:
                result = await asyncio.to_thread(
                    self.checks[component]
                )

            # Process result
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "Health check passed" if result else "Health check failed"
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "unknown"))
                message = result.get("message", "")
            elif isinstance(result, HealthCheckResult):
                status = result.status
                message = result.message
            else:
                status = HealthStatus.HEALTHY
                message = "Health check passed"

            latency = (datetime.now() - start_time).total_seconds() * 1000

            check_result = HealthCheckResult(
                component=component,
                status=status,
                message=message,
                latency_ms=latency
            )

            # Store result
            self.check_results.append(check_result)

            return check_result

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message="Health check timed out",
                latency_ms=self.default_timeout * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def check_all_components(self) -> Dict[str, HealthCheckResult]:
        """Check health of all registered components"""
        results = {}

        for component in self.checks:
            results[component] = await self.check_component(component)

        return results

    def get_overall_health(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.check_results:
            return HealthStatus.UNKNOWN

        # Get only recent results (last 5 minutes)
        cutoff = datetime.now() - timedelta(minutes=5)
        recent_results = [
            r for r in self.check_results
            if r.timestamp > cutoff
        ]

        if not recent_results:
            return HealthStatus.UNKNOWN

        # Check if any components are unhealthy
        if any(r.status == HealthStatus.UNHEALTHY for r in recent_results):
            return HealthStatus.UNHEALTHY

        # Check if any components are degraded
        if any(r.status == HealthStatus.DEGRADED for r in recent_results):
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of health status"""
        all_results = await self.check_all_components()

        status_counts = defaultdict(int)
        for result in all_results.values():
            status_counts[result.status.value] += 1

        return {
            "overall_status": self.get_overall_health().value,
            "component_count": len(all_results),
            "status_counts": dict(status_counts),
            "components": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "latency_ms": result.latency_ms,
                }
                for name, result in all_results.items()
            },
        }


class ObservabilityStack:
    """
    Complete observability stack for the orchestrated system.

    Integrates:
    - Metrics collection
    - Health checking
    - System state monitoring
    - Performance profiling
    - Distributed tracing
    """

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthCheck()

        # System state
        self.system_state = {
            "started_at": datetime.now().isoformat(),
            "uptime_seconds": 0,
            "version": "1.0.0",
        }

        # Profiling
        self.profiling_enabled = False
        self.profile_data = []

        # Distributed tracing
        self.active_traces: Dict[str, Dict[str, Any]] = {}
        self.trace_history: List[Dict[str, Any]] = []

        # Observability loops
        self.running = False

        logger.info("Observability Stack initialized")

    async def start(self):
        """Start the observability stack"""
        logger.info("Starting Observability Stack")

        self.running = True

        # Start metrics collection
        asyncio.create_task(self.metrics_collector.start_collection_loop())

        # Start system state updates
        asyncio.create_task(self._update_system_state_loop())

        # Start trace cleanup
        asyncio.create_task(self._trace_cleanup_loop())

        logger.info("Observability Stack started")

    async def stop(self):
        """Stop the observability stack"""
        logger.info("Stopping Observability Stack")

        self.running = False

        # Stop metrics collection
        self.metrics_collector.stop_collection_loop()

        logger.info("Observability Stack stopped")

    async def _update_system_state_loop(self):
        """Periodically update system state"""
        while self.running:
            try:
                # Update uptime
                start_time = datetime.fromisoformat(self.system_state["started_at"])
                uptime = datetime.now() - start_time
                self.system_state["uptime_seconds"] = uptime.total_seconds()

                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error updating system state: {e}")
                await asyncio.sleep(60)

    async def _trace_cleanup_loop(self):
        """Clean up old traces"""
        while self.running:
            try:
                # Remove traces older than 1 hour
                cutoff = datetime.now() - timedelta(hours=1)

                # Clean active traces
                self.active_traces = {
                    trace_id: trace
                    for trace_id, trace in self.active_traces.items()
                    if datetime.fromisoformat(trace.get("start_time", "")) > cutoff
                }

                # Clean trace history
                self.trace_history = [
                    trace for trace in self.trace_history
                    if datetime.fromisoformat(trace.get("end_time", "")) > cutoff
                ]

                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logger.error(f"Error in trace cleanup: {e}")
                await asyncio.sleep(300)

    def start_trace(self, trace_id: str, operation: str, metadata: Optional[Dict] = None):
        """Start a distributed trace"""
        self.active_traces[trace_id] = {
            "trace_id": trace_id,
            "operation": operation,
            "start_time": datetime.now().isoformat(),
            "metadata": metadata or {},
            "spans": [],
        }

    def end_trace(self, trace_id: str, success: bool, error: Optional[str] = None):
        """End a distributed trace"""
        if trace_id not in self.active_traces:
            logger.warning(f"Trace {trace_id} not found")
            return

        trace = self.active_traces[trace_id]
        trace["end_time"] = datetime.now().isoformat()
        trace["success"] = success
        trace["error"] = error

        # Move to history
        self.trace_history.append(trace)
        del self.active_traces[trace_id]

    def add_span(self, trace_id: str, operation: str, duration: float, metadata: Optional[Dict] = None):
        """Add a span to a trace"""
        if trace_id not in self.active_traces:
            logger.warning(f"Trace {trace_id} not found")
            return

        span = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self.active_traces[trace_id]["spans"].append(span)

    async def get_system_observability(self) -> Dict[str, Any]:
        """Get complete system observability data"""
        return {
            "system_state": self.system_state,
            "metrics": self.metrics_collector.get_system_metrics(),
            "health": await self.health_checker.get_health_summary(),
            "traces": {
                "active": len(self.active_traces),
                "history_size": len(self.trace_history),
            },
            "profiling_enabled": self.profiling_enabled,
        }
