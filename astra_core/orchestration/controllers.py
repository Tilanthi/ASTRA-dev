"""
Controller Pattern Implementation

Implements Kubernetes-style controllers for managing resources:
- Watch resources for changes
- Compare observed vs desired state
- Take corrective action
- Handle failures gracefully with retries
"""

from typing import Dict, List, Any, Optional, Callable, Set, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
from abc import ABC, abstractmethod

from .declarative import (
    ResourceState,
)

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of watch events"""
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    ERROR = "ERROR"


@dataclass
class WatchEvent:
    """Event from watching a resource"""
    type: EventType
    resource: Any
    old_object: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ControllerMetrics:
    """Metrics for a controller"""
    reconciliations_total: int = 0
    reconciliations_successful: int = 0
    reconciliations_failed: int = 0
    reconciliations_retryable: int = 0
    average_reconciliation_duration: float = 0.0
    last_reconciliation_time: Optional[datetime] = None
    error_rate: float = 0.0


class Controller(ABC):
    """
    Base class for controllers.

    A controller watches resources of a specific type and reconciles
    them to match their desired state.
    """

    def __init__(self,
                 name: str,
                 resource_type: str,
                 reconciliation_period: float = 1.0,
                 max_concurrent_reconciliations: int = 10):
        """
        Args:
            name: Controller name
            resource_type: Type of resource to watch
            reconciliation_period: Seconds between reconciliation passes
            max_concurrent_reconciliations: Maximum concurrent reconciliations
        """
        self.name = name
        self.resource_type = resource_type
        self.reconciliation_period = reconciliation_period
        self.max_concurrent_reconciliations = max_concurrent_reconciliations

        self.resources: Dict[str, Any] = {}
        self.watches: Dict[str, Set[Callable]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.running = False

        self.metrics = ControllerMetrics()
        self.semaphore = asyncio.Semaphore(max_concurrent_reconciliations)

    @abstractmethod
    async def reconcile(self, resource: Any) -> bool:
        """
        Reconcile a single resource.

        Args:
            resource: The resource to reconcile

        Returns:
            True if reconciliation was successful, False otherwise
        """
        pass

    async def watch(self, resource: Any) -> bool:
        """Watch a resource for changes"""
        # In a real implementation, this would set up actual watching
        # For now, we add it to our resource list
        self.resources[self._get_resource_key(resource)] = resource
        await self.event_queue.put(WatchEvent(
            type=EventType.ADDED,
            resource=resource
        ))
        return True

    def _get_resource_key(self, resource: Any) -> str:
        """Get unique key for a resource"""
        if hasattr(resource, "get_uid"):
            return resource.get_uid()
        elif hasattr(resource, "spec"):
            return f"{resource.spec.kind}/{resource.spec.name}"
        else:
            return str(id(resource))

    async def notify_watchers(self, event: WatchEvent):
        """Notify all watchers of an event"""
        key = self._get_resource_key(event.resource)
        if key in self.watches:
            for callback in self.watches[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in watcher callback: {e}")

    async def add_watcher(self, resource: Any, callback: Callable):
        """Add a watcher for a specific resource"""
        key = self._get_resource_key(resource)
        if key not in self.watches:
            self.watches[key] = set()
        self.watches[key].add(callback)

    async def remove_watcher(self, resource: Any, callback: Callable):
        """Remove a watcher for a specific resource"""
        key = self._get_resource_key(resource)
        if key in self.watches:
            self.watches[key].discard(callback)

    async def process_event(self, event: WatchEvent):
        """Process a single watch event"""
        resource = event.resource
        key = self._get_resource_key(resource)

        start_time = datetime.now()

        try:
            async with self.semaphore:
                # Update metrics
                self.metrics.reconciliations_total += 1
                self.metrics.last_reconciliation_time = start_time

                # Call reconcile implementation
                success = await self.reconcile(resource)

                # Update success/failure metrics
                if success:
                    self.metrics.reconciliations_successful += 1
                else:
                    self.metrics.reconciliations_failed += 1

                # Update average duration
                duration = (datetime.now() - start_time).total_seconds()
                total = self.metrics.reconciliations_total
                old_avg = self.metrics.average_reconciliation_duration
                self.metrics.average_reconciliation_duration = (
                    (old_avg * (total - 1) + duration) / total
                )

                # Update error rate
                self.metrics.error_rate = (
                    self.metrics.reconciliations_failed / total
                    if total > 0 else 0.0
                )

                logger.debug(f"Reconciled {key}: success={success}, duration={duration:.2f}s")

        except Exception as e:
            logger.error(f"Error reconciling {key}: {e}")
            self.metrics.reconciliations_failed += 1
            self.metrics.reconciliations_total += 1

    async def run(self):
        """Main controller loop"""
        self.running = True
        logger.info(f"Starting controller {self.name} for {self.resource_type}")

        while self.running:
            try:
                # Process events with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.reconciliation_period
                    )
                    await self.process_event(event)
                    await self.notify_watchers(event)
                except asyncio.TimeoutError:
                    # Periodic reconciliation of all resources
                    pass

                # Reconcile all resources periodically
                for resource in self.resources.values():
                    await self.event_queue.put(WatchEvent(
                        type=EventType.MODIFIED,
                        resource=resource
                    ))

            except Exception as e:
                logger.error(f"Error in controller loop: {e}")
                await asyncio.sleep(self.reconciliation_period)

    def stop(self):
        """Stop the controller"""
        self.running = False
        logger.info(f"Stopping controller {self.name}")

    def get_metrics(self) -> ControllerMetrics:
        """Get controller metrics"""
        return self.metrics


class ControllerManager:
    """
    Manages multiple controllers and coordinates their execution.

    Similar to Kubernetes controller manager, this provides:
    - Centralized controller lifecycle management
    - Shared state management
    - Coordinated shutdown
    - Health monitoring
    """

    def __init__(self):
        self.controllers: Dict[str, Controller] = {}
        self.running = False
        self.health_check_interval = 30.0  # seconds

    def register_controller(self, controller: Controller):
        """Register a controller"""
        self.controllers[controller.name] = controller
        logger.info(f"Registered controller {controller.name}")

    def unregister_controller(self, name: str):
        """Unregister a controller"""
        if name in self.controllers:
            controller = self.controllers[name]
            controller.stop()
            del self.controllers[name]
            logger.info(f"Unregistered controller {name}")

    async def start_all(self):
        """Start all controllers"""
        self.running = True
        logger.info(f"Starting {len(self.controllers)} controllers")

        tasks = []
        for controller in self.controllers.values():
            task = asyncio.create_task(controller.run())
            tasks.append(task)

        # Start health check task
        health_task = asyncio.create_task(self._health_check_loop())
        tasks.append(health_task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _health_check_loop(self):
        """Periodically check health of all controllers"""
        while self.running:
            try:
                for name, controller in self.controllers.items():
                    metrics = controller.get_metrics()

                    # Log metrics
                    logger.debug(
                        f"Controller {name} metrics: "
                        f"total={metrics.reconciliations_total}, "
                        f"success_rate={1.0 - metrics.error_rate:.2%}, "
                        f"avg_duration={metrics.average_reconciliation_duration:.2f}s"
                    )

                    # Check for problems
                    if metrics.error_rate > 0.5:
                        logger.warning(
                            f"Controller {name} has high error rate: {metrics.error_rate:.2%}"
                        )

                    if metrics.reconciliations_total > 100 and metrics.average_reconciliation_duration > 30:
                        logger.warning(
                            f"Controller {name} has slow reconciliation: "
                            f"{metrics.average_reconciliation_duration:.2f}s average"
                        )

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(self.health_check_interval)

    def stop_all(self):
        """Stop all controllers"""
        self.running = False
        for controller in self.controllers.values():
            controller.stop()
        logger.info("Stopped all controllers")

    def get_controller(self, name: str) -> Optional[Controller]:
        """Get a controller by name"""
        return self.controllers.get(name)

    def get_all_metrics(self) -> Dict[str, ControllerMetrics]:
        """Get metrics from all controllers"""
        return {
            name: controller.get_metrics()
            for name, controller in self.controllers.items()
        }


# Example: Task Controller

class TaskController(Controller):
    """Controller for managing Task resources"""

    def __init__(self, task_executor: Callable):
        super().__init__(
            name="TaskController",
            resource_type="Task"
        )
        self.task_executor = task_executor

    async def reconcile(self, resource: Any) -> bool:
        """Reconcile a task resource"""
        try:
            # Check if task needs execution
            if resource.status.state == ResourceState.PENDING:
                # Execute the task
                result = await self.task_executor(resource.spec.query)
                resource.status.output = result
                resource.status.state = ResourceState.COMPLETED
                return True

            elif resource.status.state == ResourceState.FAILED:
                # Check if retryable
                if resource.status.retry_count < resource.spec.max_retries:
                    resource.status.state = ResourceState.PENDING
                    resource.status.retry_count += 1
                    return True
                else:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error reconciling task: {e}")
            resource.status.state = ResourceState.FAILED
            resource.status.error_message = str(e)
            return False
