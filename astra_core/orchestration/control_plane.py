"""
Phase 2: Control Plane and Data Plane Separation

Implements clean separation between control and data planes:
- Control Plane: Manages system state, policies, and orchestration
- Data Plane: Handles actual computation and I/O
- Clear API boundaries between planes
- Independent scaling and deployment
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio
from abc import ABC, abstractmethod

from .controllers import Controller, ControllerManager
from .operators import OperatorFactory, Operator
from .declarative import DeclarativeAPI, DeclarativeResource, ResourceSpec

logger = logging.getLogger(__name__)


@dataclass
class Policy:
    """A policy that governs system behavior"""
    name: str
    rules: Dict[str, Any]
    priority: int = 0
    enabled: bool = True


@dataclass
class ControlPolicy:
    """Policy for control plane behavior"""
    max_concurrent_operations: int = 10
    default_timeout: float = 300.0
    retry_policy: str = "exponential_backoff"
    retry_limit: int = 3
    resource_limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPolicy:
    """Policy for data plane execution"""
    enable_caching: bool = True
    cache_ttl: int = 3600  # seconds
    enable_parallel_execution: bool = True
    max_parallel_tasks: int = 5
    memory_limit_mb: int = 8192
    enable_profiling: bool = False


class ControlPlane:
    """
    Control Plane manages system state and policies.

    Responsibilities:
    - Manage resources and their desired state
    - Enforce policies and constraints
    - Coordinate controllers and operators
    - Monitor system health
    - Handle failures and recovery
    """

    def __init__(self, config: Optional[ControlPolicy] = None):
        self.config = config or ControlPolicy()
        self.api_server = DeclarativeAPI()
        self.controller_manager = ControllerManager()
        self.operator_factory = OperatorFactory()

        # Policy management
        self.policies: Dict[str, Policy] = {}
        self.policy_history: List[Dict[str, Any]] = []

        # State management
        self.system_state = {}
        self.health_status = {}

        # Event bus for control plane events
        self.event_bus = asyncio.Queue()

        logger.info("Control Plane initialized")

    async def start(self):
        """Start the control plane"""
        logger.info("Starting Control Plane")

        # Start all controllers
        await self.controller_manager.start_all()

        # Start event processing loop
        asyncio.create_task(self._event_loop())

        logger.info("Control Plane started")

    async def stop(self):
        """Stop the control plane"""
        logger.info("Stopping Control Plane")

        # Stop all controllers
        self.controller_manager.stop_all()

        logger.info("Control Plane stopped")

    async def _event_loop(self):
        """Process control plane events"""
        while True:
            try:
                event = await self.event_bus.get()
                await self._handle_event(event)
            except Exception as e:
                logger.error(f"Error handling control plane event: {e}")

    async def _handle_event(self, event: Dict[str, Any]):
        """Handle a control plane event"""
        event_type = event.get("type")

        if event_type == "resource_created":
            await self._on_resource_created(event)
        elif event_type == "resource_updated":
            await self._on_resource_updated(event)
        elif event_type == "resource_deleted":
            await self._on_resource_deleted(event)
        elif event_type == "policy_changed":
            await self._on_policy_changed(event)
        elif event_type == "health_check":
            await self._on_health_check(event)

    async def _on_resource_created(self, event: Dict[str, Any]):
        """Handle resource creation"""
        resource = event["resource"]
        logger.debug(f"Resource created: {resource.get_uid()}")

    async def _on_resource_updated(self, event: Dict[str, Any]):
        """Handle resource update"""
        resource = event["resource"]
        logger.debug(f"Resource updated: {resource.get_uid()}")

    async def _on_resource_deleted(self, event: Dict[str, Any]):
        """Handle resource deletion"""
        uid = event["uid"]
        logger.debug(f"Resource deleted: {uid}")

    async def _on_policy_changed(self, event: Dict[str, Any]):
        """Handle policy change"""
        policy_name = event["policy_name"]
        logger.info(f"Policy changed: {policy_name}")

    async def _on_health_check(self, event: Dict[str, Any]):
        """Handle health check"""
        # Update health status
        metrics = self.get_metrics()
        self.health_status = {
            "timestamp": datetime.now().isoformat(),
            "controllers_healthy": all(
                m.error_rate < 0.5
                for m in metrics["controllers"].values()
            ),
            "active_resources": sum(
                loop_stats.get("active_resources", 0)
                for loop_stats in metrics.get("loops", {}).values()
            ),
        }

    def register_controller(self, controller: Controller):
        """Register a controller with the control plane"""
        self.controller_manager.register_controller(controller)
        logger.info(f"Registered controller {controller.name}")

    def register_operator(self, domain: str, operator_class: type):
        """Register a domain operator"""
        self.operator_factory.register_operator(domain, operator_class)
        logger.info(f"Registered operator for domain {domain}")

    def add_policy(self, policy: Policy):
        """Add a policy"""
        self.policies[policy.name] = policy

        # Record in history
        self.policy_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "added",
            "policy": policy.name,
        })

        logger.info(f"Added policy {policy.name}")

    def remove_policy(self, policy_name: str):
        """Remove a policy"""
        if policy_name in self.policies:
            del self.policies[policy_name]

            # Record in history
            self.policy_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "removed",
                "policy": policy_name,
            })

            logger.info(f"Removed policy {policy_name}")

    def get_policies(self) -> Dict[str, Policy]:
        """Get all active policies"""
        return {
            name: policy
            for name, policy in self.policies.items()
            if policy.enabled
        }

    def apply_policies(self, resource: DeclarativeResource) -> bool:
        """Apply policies to a resource"""
        allowed = True

        for policy in self.get_policies().values():
            # Check if resource matches policy rules
            if not self._check_policy_compliance(resource, policy):
                allowed = False
                logger.warning(
                    f"Resource {resource.get_uid()} violates policy {policy.name}"
                )

        return allowed

    def _check_policy_compliance(self,
                                resource: DeclarativeResource,
                                policy: Policy) -> bool:
        """Check if a resource complies with a policy"""
        # Implement policy checking logic
        # For now, always return True
        return True

    async def create_resource(self, spec: ResourceSpec) -> DeclarativeResource:
        """Create a resource through the control plane"""
        # Check policies
        resource = await self.api_server.create_resource(spec)

        if not self.apply_policies(resource):
            # Reject resource if policies not satisfied
            await self.api_server.delete_resource(resource.get_uid())
            raise ValueError(f"Resource violates policies: {resource.get_uid()}")

        # Emit event
        await self.event_bus.put({
            "type": "resource_created",
            "resource": resource,
        })

        return resource

    async def update_resource(self, uid: str, spec: ResourceSpec) -> DeclarativeResource:
        """Update a resource through the control plane"""
        resource = await self.api_server.update_resource(uid, spec)

        if not self.apply_policies(resource):
            # Rollback update if policies not satisfied
            raise ValueError(f"Update violates policies: {uid}")

        # Emit event
        await self.event_bus.put({
            "type": "resource_updated",
            "resource": resource,
        })

        return resource

    async def delete_resource(self, uid: str):
        """Delete a resource through the control plane"""
        await self.api_server.delete_resource(uid)

        # Emit event
        await self.event_bus.put({
            "type": "resource_deleted",
            "uid": uid,
        })

    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        return {
            "api_status": self.api_server.get_system_status(),
            "controllers": self.controller_manager.get_all_metrics(),
            "policies": len(self.policies),
            "health": self.health_status,
            "timestamp": datetime.now().isoformat(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get control plane metrics"""
        return {
            "controllers": self.controller_manager.get_all_metrics(),
            "loops": self.api_server.get_system_status().get("loops", {}),
            "policies": {
                name: {
                    "enabled": policy.enabled,
                    "priority": policy.priority,
                }
                for name, policy in self.policies.items()
            },
        }


class DataPlane:
    """
    Data Plane handles actual computation and I/O.

    Responsibilities:
    - Execute queries and computations
    - Apply control plane policies
    - Manage resources (memory, compute)
    - Handle caching and optimization
    - Provide observability
    """

    def __init__(self,
                 control_plane: ControlPlane,
                 config: Optional[ExecutionPolicy] = None):
        self.control_plane = control_plane
        self.config = config or ExecutionPolicy()

        # Capability registry
        self.capabilities: Dict[str, Callable] = {}

        # Cache management
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}

        # Execution state
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_history: List[Dict[str, Any]] = []

        # Metrics
        self.execution_metrics = {
            "total_executions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_execution_time": 0.0,
            "failed_executions": 0,
        }

        logger.info("Data Plane initialized")

    def register_capability(self, name: str, handler: Callable):
        """Register a capability with the data plane"""
        self.capabilities[name] = handler
        logger.info(f"Registered capability {name}")

    async def execute_query(self,
                           query: str,
                           context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a query through the data plane"""
        start_time = datetime.now()
        execution_id = f"exec-{hash(query) % 100000:05d}"

        try:
            # Check cache
            if self.config.enable_caching:
                cached_result = self._get_cached_result(query)
                if cached_result is not None:
                    self.execution_metrics["cache_hits"] += 1
                    logger.debug(f"Cache hit for query: {query[:50]}...")
                    return cached_result
                else:
                    self.execution_metrics["cache_misses"] += 1

            # Apply control plane policies
            policies = self.control_plane.get_policies()
            execution_context = {
                "query": query,
                "context": context or {},
                "policies": policies,
                "config": self.config,
            }

            # Select and execute capability
            result = await self._execute_with_capabilities(execution_context)

            # Cache result
            if self.config.enable_caching:
                self._cache_result(query, result)

            # Update metrics
            elapsed = (datetime.now() - start_time).total_seconds()
            self._update_execution_metrics(elapsed, success=True)

            # Record in history
            self.execution_history.append({
                "id": execution_id,
                "query": query,
                "start_time": start_time.isoformat(),
                "elapsed_seconds": elapsed,
                "success": True,
            })

            return result

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            self._update_execution_metrics(elapsed, success=False)

            # Record in history
            self.execution_history.append({
                "id": execution_id,
                "query": query,
                "start_time": start_time.isoformat(),
                "elapsed_seconds": elapsed,
                "success": False,
                "error": str(e),
            })

            logger.error(f"Error executing query: {e}")
            raise

    async def _execute_with_capabilities(self, context: Dict[str, Any]) -> Any:
        """Execute query using appropriate capabilities"""
        query = context["query"]
        policies = context["policies"]

        # Select capability based on query analysis
        capability_name = self._select_capability(query)

        if capability_name not in self.capabilities:
            raise ValueError(f"Capability not found: {capability_name}")

        capability = self.capabilities[capability_name]

        # Execute with policy checks
        if not self._check_execution_policies(context, capability_name):
            raise PermissionError(f"Execution denied by policies: {capability_name}")

        # Execute capability
        result = await capability(query, context)

        return result

    def _select_capability(self, query: str) -> str:
        """Select appropriate capability for a query"""
        # Simple keyword-based selection
        # In real implementation, would use more sophisticated routing

        query_lower = query.lower()

        if any(word in query_lower for word in ["filament", "core", "spacing"]):
            return "filament_analysis"
        elif any(word in query_lower for word in ["simulate", "mhd", "hydro"]):
            return "simulation"
        elif any(word in query_lower for word in ["physics", "equation", "calculate"]):
            return "physics"
        elif any(word in query_lower for word in ["discover", "hypothesis", "experiment"]):
            return "discovery"
        else:
            return "general"

    def _check_execution_policies(self,
                                 context: Dict[str, Any],
                                 capability_name: str) -> bool:
        """Check if execution complies with policies"""
        # Implement policy checking
        # For now, always allow
        return True

    def _get_cached_result(self, query: str) -> Optional[Any]:
        """Get cached result if available and not expired"""
        if query not in self.cache:
            return None

        timestamp = self.cache_timestamps.get(query)
        if timestamp is None:
            return None

        age = (datetime.now() - timestamp).total_seconds()
        if age > self.config.cache_ttl:
            # Cache expired
            del self.cache[query]
            del self.cache_timestamps[query]
            return None

        return self.cache[query]

    def _cache_result(self, query: str, result: Any):
        """Cache a result"""
        self.cache[query] = result
        self.cache_timestamps[query] = datetime.now()

        # Clean old cache entries if needed
        if len(self.cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove old cache entries"""
        now = datetime.now()

        # Remove entries older than TTL
        to_remove = [
            query for query, timestamp in self.cache_timestamps.items()
            if (now - timestamp).total_seconds() > self.config.cache_ttl
        ]

        for query in to_remove:
            del self.cache[query]
            del self.cache_timestamps[query]

        logger.debug(f"Cleaned up {len(to_remove)} cache entries")

    def _update_execution_metrics(self, elapsed: float, success: bool):
        """Update execution metrics"""
        self.execution_metrics["total_executions"] += 1

        if not success:
            self.execution_metrics["failed_executions"] += 1

        # Update average execution time
        total = self.execution_metrics["total_executions"]
        old_avg = self.execution_metrics["average_execution_time"]
        self.execution_metrics["average_execution_time"] = (
            (old_avg * (total - 1) + elapsed) / total
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get data plane metrics"""
        return {
            **self.execution_metrics,
            "cache_size": len(self.cache),
            "cache_hit_rate": (
                self.execution_metrics["cache_hits"] /
                (self.execution_metrics["cache_hits"] + self.execution_metrics["cache_misses"])
                if (self.execution_metrics["cache_hits"] + self.execution_metrics["cache_misses"]) > 0
                else 0.0
            ),
            "active_executions": len(self.active_executions),
            "registered_capabilities": len(self.capabilities),
        }

    def clear_cache(self):
        """Clear all cached results"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Cache cleared")


class OrchestratedSystem:
    """
    Complete system with separated control and data planes.

    This provides the main entry point for the orchestrated ASTRA system,
    managing both control plane (orchestration) and data plane (execution).
    """

    def __init__(self,
                 control_config: Optional[ControlPolicy] = None,
                 data_config: Optional[ExecutionPolicy] = None):
        # Create control plane
        self.control_plane = ControlPlane(control_config)

        # Create data plane with reference to control plane
        self.data_plane = DataPlane(self.control_plane, data_config)

        # System state
        self.running = False

        logger.info("Orchestrated System initialized")

    async def start(self):
        """Start the orchestrated system"""
        logger.info("Starting Orchestrated System")

        # Start control plane (which starts controllers)
        await self.control_plane.start()

        self.running = True
        logger.info("Orchestrated System started")

    async def stop(self):
        """Stop the orchestrated system"""
        logger.info("Stopping Orchestrated System")

        # Stop control plane
        await self.control_plane.stop()

        self.running = False
        logger.info("Orchestrated System stopped")

    async def process_query(self,
                           query: str,
                           context: Optional[Dict[str, Any]] = None) -> Any:
        """Process a query through the orchestrated system"""
        if not self.running:
            raise RuntimeError("System not running. Call start() first.")

        # Route through data plane
        result = await self.data_plane.execute_query(query, context)

        return result

    def register_capability(self, name: str, handler: Callable):
        """Register a capability with the data plane"""
        self.data_plane.register_capability(name, handler)

    def add_policy(self, policy: Policy):
        """Add a policy to the control plane"""
        self.control_plane.add_policy(policy)

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            "running": self.running,
            "control_plane": self.control_plane.get_system_state(),
            "data_plane": self.data_plane.get_metrics(),
            "timestamp": datetime.now().isoformat(),
        }
