"""
Phase 1: Declarative API with Reconciliation Loops

Implements Kubernetes-style declarative resource management:
- Declarative resource specifications
- Automatic reconciliation loops
- Level-based triggering (state vs edge-based)
- Self-healing through continuous reconciliation
"""

from typing import Dict, Any, Optional, Callable, List, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ResourceState(Enum):
    """Resource lifecycle states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


class ConditionType(Enum):
    """Types of conditions for resource status"""
    READY = "Ready"
    FAILED = "Failed"
    PROGRESSING = "Progressing"
    RETRYABLE = "Retryable"
    TERMINATING = "Terminating"


@dataclass
class Condition:
    """A condition on a resource"""
    type: ConditionType
    status: str  # "True", "False", or "Unknown"
    reason: Optional[str] = None
    message: Optional[str] = None
    last_transition_time: datetime = field(default_factory=datetime.now)
    last_update_time: datetime = field(default_factory=datetime.now)


@dataclass
class ResourceSpec:
    """Desired state specification for a resource"""
    kind: str = ""
    name: str = ""
    namespace: str = "default"
    version: str = "v1"
    spec: Dict[str, Any] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "namespace": self.namespace,
            "version": self.version,
            "spec": self.spec,
            "annotations": self.annotations,
            "labels": self.labels,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceSpec":
        return cls(
            kind=data.get("kind", ""),
            name=data.get("name", ""),
            namespace=data.get("namespace", "default"),
            version=data.get("version", "v1"),
            spec=data.get("spec", {}),
            annotations=data.get("annotations", {}),
            labels=data.get("labels", {}),
        )


@dataclass
class ResourceStatus:
    """Observed state of a resource"""
    state: ResourceState = ResourceState.PENDING
    phase: str = ""
    conditions: List[Condition] = field(default_factory=list)
    observed_generation: int = 0
    last_update: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "phase": self.phase,
            "conditions": [
                {
                    "type": c.type.value,
                    "status": c.status,
                    "reason": c.reason,
                    "message": c.message,
                    "last_transition_time": c.last_transition_time.isoformat(),
                    "last_update_time": c.last_update_time.isoformat(),
                }
                for c in self.conditions
            ],
            "observed_generation": self.observed_generation,
            "last_update": self.last_update.isoformat(),
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "output": self.output,
        }

    def set_condition(self, condition_type: ConditionType, status: str,
                     reason: Optional[str] = None, message: Optional[str] = None):
        """Set or update a condition"""
        now = datetime.now()
        # Update existing condition if present
        for cond in self.conditions:
            if cond.type == condition_type:
                if cond.status != status:
                    cond.last_transition_time = now
                cond.status = status
                cond.reason = reason
                cond.message = message
                cond.last_update_time = now
                return

        # Add new condition
        self.conditions.append(Condition(
            type=condition_type,
            status=status,
            reason=reason,
            message=message,
            last_transition_time=now,
            last_update_time=now,
        ))


T = TypeVar("T", bound=ResourceSpec)


class DeclarativeResource(Generic[T]):
    """
    A declarative resource that maintains its own state through reconciliation.

    Similar to Kubernetes resources, this implements:
    - Declarative specification (desired state)
    - Automatic reconciliation (observed state -> desired state)
    - Self-healing through continuous reconciliation
    """

    def __init__(self, spec: T, generation: int = 0):
        self.spec = spec
        self.generation = generation
        self.status = ResourceStatus()
        self.creation_timestamp = datetime.now()
        self.last_reconciliation = None

    def get_uid(self) -> str:
        """Get unique identifier for this resource"""
        return f"{self.spec.namespace}/{self.spec.kind}/{self.spec.name}"

    def needs_reconciliation(self) -> bool:
        """Check if this resource needs reconciliation"""
        # Reconcile if:
        # 1. Never reconciled
        # 2. Failed and retryable
        # 3. In progress state
        # 4. Explicitly marked for reconciliation

        if self.last_reconciliation is None:
            return True

        # Check if in terminal state
        if self.status.state in [ResourceState.COMPLETED, ResourceState.TERMINATED]:
            return False

        # Check if failed but retryable
        if self.status.state == ResourceState.FAILED:
            has_retryable = any(
                c.type == ConditionType.RETRYABLE and c.status == "True"
                for c in self.status.conditions
            )
            return has_retryable and self.status.retry_count < 5

        # In progress states need reconciliation
        return self.status.state in [ResourceState.PENDING, ResourceState.RUNNING]

    def mark_for_reconciliation(self):
        """Mark this resource for immediate reconciliation"""
        self.last_reconciliation = None

    def get_age(self) -> timedelta:
        """Get age of this resource"""
        return datetime.now() - self.creation_timestamp


class ReconciliationLoop:
    """
    Continuous reconciliation loop that maintains desired state.

    Implements the control loop pattern:
    1. Observe current state
    2. Compare with desired state
    3. Take corrective action
    4. Repeat
    """

    def __init__(self,
                 reconcile_func: Callable[[DeclarativeResource], ResourceStatus],
                 interval: float = 1.0):
        """
        Args:
            reconcile_func: Function to reconcile a resource
            interval: Seconds between reconciliation passes
        """
        self.reconcile_func = reconcile_func
        self.interval = interval
        self.resources: Dict[str, DeclarativeResource] = {}
        self.running = False
        self.reconciliation_stats = {
            "total_reconciliations": 0,
            "successful_reconciliations": 0,
            "failed_reconciliations": 0,
            "average_reconciliation_time": 0.0,
        }

    def add_resource(self, resource: DeclarativeResource):
        """Add a resource to be reconciled"""
        uid = resource.get_uid()
        self.resources[uid] = resource
        logger.info(f"Added resource {uid} for reconciliation")

    def remove_resource(self, uid: str):
        """Remove a resource from reconciliation"""
        if uid in self.resources:
            del self.resources[uid]
            logger.info(f"Removed resource {uid} from reconciliation")

    def get_resource(self, uid: str) -> Optional[DeclarativeResource]:
        """Get a resource by UID"""
        return self.resources.get(uid)

    async def reconcile_resource(self, resource: DeclarativeResource) -> ResourceStatus:
        """Reconcile a single resource"""
        start_time = datetime.now()
        uid = resource.get_uid()

        try:
            logger.debug(f"Reconciling resource {uid}")

            # Call reconciliation function
            new_status = self.reconcile_func(resource)

            # Update statistics
            self.reconciliation_stats["total_reconciliations"] += 1

            if new_status.state != ResourceState.FAILED:
                self.reconciliation_stats["successful_reconciliations"] += 1
            else:
                self.reconciliation_stats["failed_reconciliations"] += 1

            # Update timing statistics
            elapsed = (datetime.now() - start_time).total_seconds()
            total = self.reconciliation_stats["total_reconciliations"]
            avg = self.reconciliation_stats["average_reconciliation_time"]
            self.reconciliation_stats["average_reconciliation_time"] = (
                (avg * (total - 1) + elapsed) / total
            )

            resource.last_reconciliation = datetime.now()
            resource.status = new_status

            logger.debug(f"Successfully reconciled {uid} in {elapsed:.2f}s")
            return new_status

        except Exception as e:
            logger.error(f"Error reconciling {uid}: {e}")
            self.reconciliation_stats["total_reconciliations"] += 1
            self.reconciliation_stats["failed_reconciliations"] += 1

            # Set failed status
            resource.status.state = ResourceState.FAILED
            resource.status.error_message = str(e)
            resource.status.retry_count += 1
            resource.status.set_condition(
                ConditionType.FAILED,
                "True",
                "ReconciliationError",
                str(e)
            )

            return resource.status

    async def run(self):
        """Main reconciliation loop"""
        self.running = True
        logger.info("Starting reconciliation loop")

        while self.running:
            try:
                # Find resources that need reconciliation
                to_reconcile = [
                    r for r in self.resources.values()
                    if r.needs_reconciliation()
                ]

                if to_reconcile:
                    logger.debug(f"Reconciling {len(to_reconcile)} resources")

                    # Reconcile in parallel
                    tasks = [
                        self.reconcile_resource(resource)
                        for resource in to_reconcile
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Sleep until next pass
                await asyncio.sleep(self.interval)

            except Exception as e:
                logger.error(f"Error in reconciliation loop: {e}")
                await asyncio.sleep(self.interval)

    def stop(self):
        """Stop the reconciliation loop"""
        self.running = False
        logger.info("Stopping reconciliation loop")

    def get_stats(self) -> Dict[str, Any]:
        """Get reconciliation statistics"""
        return {
            **self.reconciliation_stats,
            "active_resources": len(self.resources),
            "needs_reconciliation": sum(
                1 for r in self.resources.values()
                if r.needs_reconciliation()
            ),
        }


class DeclarativeAPI:
    """
    Declarative API for managing resources.

    Provides a Kubernetes-style declarative API where users specify
    desired state and the system handles the details of achieving it.
    """

    def __init__(self):
        self.reconciliation_loops: Dict[str, ReconciliationLoop] = {}
        self.resource_types: Dict[str, type] = {}

    def register_resource_type(self,
                               kind: str,
                               resource_class: type,
                               reconcile_func: Callable):
        """Register a new resource type"""
        self.resource_types[kind] = resource_class

        # Create reconciliation loop for this type
        loop = ReconciliationLoop(reconcile_func)
        self.reconciliation_loops[kind] = loop

        logger.info(f"Registered resource type {kind}")

    async def create_resource(self, spec: ResourceSpec) -> DeclarativeResource:
        """Create a new resource"""
        kind = spec.kind

        if kind not in self.resource_types:
            raise ValueError(f"Unknown resource type: {kind}")

        resource_class = self.resource_types[kind]
        resource = resource_class(spec)

        # Add to appropriate reconciliation loop
        loop = self.reconciliation_loops[kind]
        loop.add_resource(resource)

        logger.info(f"Created resource {resource.get_uid()}")
        return resource

    async def update_resource(self, uid: str, spec: ResourceSpec) -> DeclarativeResource:
        """Update an existing resource"""
        # Parse UID
        namespace, kind, name = uid.split("/")

        if kind not in self.reconciliation_loops:
            raise ValueError(f"Unknown resource type: {kind}")

        loop = self.reconciliation_loops[kind]
        resource = loop.get_resource(uid)

        if resource is None:
            raise ValueError(f"Resource not found: {uid}")

        # Update spec and increment generation
        resource.spec = spec
        resource.generation += 1
        resource.status.observed_generation = 0  # Will be updated by reconciliation
        resource.mark_for_reconciliation()

        logger.info(f"Updated resource {uid} to generation {resource.generation}")
        return resource

    async def delete_resource(self, uid: str):
        """Delete a resource"""
        # Parse UID
        namespace, kind, name = uid.split("/")

        if kind not in self.reconciliation_loops:
            raise ValueError(f"Unknown resource type: {kind}")

        loop = self.reconciliation_loops[kind]
        loop.remove_resource(uid)

        logger.info(f"Deleted resource {uid}")

    def get_resource(self, uid: str) -> Optional[DeclarativeResource]:
        """Get a resource by UID"""
        namespace, kind, name = uid.split("/")

        if kind not in self.reconciliation_loops:
            return None

        loop = self.reconciliation_loops[kind]
        return loop.get_resource(uid)

    def list_resources(self, kind: str,
                       namespace: Optional[str] = None) -> List[DeclarativeResource]:
        """List resources of a given kind"""
        if kind not in self.reconciliation_loops:
            return []

        loop = self.reconciliation_loops[kind]

        if namespace is None:
            return list(loop.resources.values())
        else:
            return [
                r for r in loop.resources.values()
                if r.spec.namespace == namespace
            ]

    async def start_all_loops(self):
        """Start all reconciliation loops"""
        tasks = []
        for kind, loop in self.reconciliation_loops.items():
            task = asyncio.create_task(loop.run())
            tasks.append(task)

        logger.info(f"Started {len(tasks)} reconciliation loops")
        await asyncio.gather(*tasks)

    def stop_all_loops(self):
        """Stop all reconciliation loops"""
        for kind, loop in self.reconciliation_loops.items():
            loop.stop()

        logger.info("Stopped all reconciliation loops")

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all reconciliation loops"""
        status = {
            "resource_types": list(self.resource_types.keys()),
            "loops": {}
        }

        for kind, loop in self.reconciliation_loops.items():
            status["loops"][kind] = loop.get_stats()

        return status


# Example: Task Resource Implementation

@dataclass
class TaskSpec(ResourceSpec):
    """Specification for a Task resource"""
    kind: str = "Task"
    query: str = ""
    priority: str = "medium"  # low, medium, high, critical
    timeout: float = 300.0  # seconds
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            self.name = f"task-{hash(self.query) % 10000:04d}"


class TaskResource(DeclarativeResource[TaskSpec]):
    """A task that executes a query using ASTRA capabilities"""

    def __init__(self, spec: TaskSpec, generation: int = 0):
        super().__init__(spec, generation)
        self.status.set_condition(ConditionType.READY, "Unknown", "Initializing",
                                "Task is being initialized")


# Example reconciliation function for tasks
async def reconcile_task(task: TaskResource) -> ResourceStatus:
    """Reconcile a TaskResource to completion"""
    spec = task.spec

    # Check if dependencies are met
    for dep_uid in spec.dependencies:
        # This would check if dependent tasks are complete
        pass

    # Execute the task based on its phase
    if task.status.state == ResourceState.PENDING:
        task.status.state = ResourceState.RUNNING
        task.status.phase = "executing"
        task.status.set_condition(ConditionType.PROGRESSING, "True",
                                "Executing", "Task is executing")

    elif task.status.state == ResourceState.RUNNING:
        try:
            # Simulate task execution
            # In real implementation, this would call ASTRA capabilities
            result = f"Result for query: {spec.query}"

            task.status.state = ResourceState.COMPLETED
            task.status.phase = "completed"
            task.status.output = {"result": result}
            task.status.set_condition(ConditionType.READY, "True",
                                    "Completed", "Task completed successfully")

        except Exception as e:
            task.status.state = ResourceState.FAILED
            task.status.error_message = str(e)
            task.status.set_condition(ConditionType.FAILED, "True",
                                    "ExecutionError", str(e))

            if task.status.retry_count < spec.max_retries:
                task.status.set_condition(ConditionType.RETRYABLE, "True",
                                        "WillRetry", f"Will retry (attempt {task.status.retry_count + 1})")
                task.status.state = ResourceState.PENDING  # Reset for retry
            else:
                task.status.set_condition(ConditionType.RETRYABLE, "False",
                                        "MaxRetriesExceeded", "Maximum retries exceeded")

    return task.status
