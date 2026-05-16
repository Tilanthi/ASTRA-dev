#!/usr/bin/env python3
"""
Test suite for ASTRA orchestration layer.

Verifies that all three phases of orchestration improvements work correctly.
"""

import asyncio
import unittest
import logging
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)

from astra_core.orchestration.declarative import (
    TaskSpec, TaskResource, ResourceState, DeclarativeAPI,
    reconcile_task
)
from astra_core.orchestration.controllers import Controller, ControllerManager
from astra_core.orchestration.service_mesh import ServiceMesh, MindServiceMesh, ServiceEndpoint
from astra_core.orchestration.observability import (
    MetricsCollector, HealthCheck, ObservabilityStack
)
from astra_core.orchestration.crd import (
    CRDRegistry, CustomResourceDefinition, CRDSchema, create_standard_crds
)
from astra_core.orchestration.integrated_system import (
    OrchestratedASTRASystem, create_orchestrated_astra_system
)


class TestDeclarativeAPI(unittest.IsolatedAsyncioTestCase):
    """Test declarative API and reconciliation loops"""

    def test_task_spec_creation(self):
        """Test creating a task specification"""
        spec = TaskSpec(
            kind="Task",
            name="test-task",
            query="Test query",
            priority="high",
            timeout=300.0
        )

        self.assertEqual(spec.kind, "Task")
        self.assertEqual(spec.name, "test-task")
        self.assertEqual(spec.priority, "high")
        self.assertEqual(spec.timeout, 300.0)

    def test_task_resource_creation(self):
        """Test creating a task resource"""
        spec = TaskSpec(
            kind="Task",
            name="test-task",
            query="Test query"
        )

        resource = TaskResource(spec)

        self.assertEqual(resource.get_uid(), "default/Task/test-task")
        self.assertEqual(resource.status.state, ResourceState.PENDING)
        self.assertTrue(resource.needs_reconciliation())

    async def test_reconcile_task(self):
        """Test task reconciliation"""
        spec = TaskSpec(
            kind="Task",
            name="test-task",
            query="Test query"
        )

        resource = TaskResource(spec)
        resource.status.state = ResourceState.RUNNING

        # Reconcile
        new_status = await reconcile_task(resource)

        self.assertIsNotNone(new_status)
        self.assertIn(new_status.state, [ResourceState.RUNNING, ResourceState.COMPLETED])


class TestControllers(unittest.IsolatedAsyncioTestCase):
    """Test controller pattern implementation"""

    async def test_controller_registration(self):
        """Test controller registration"""
        manager = ControllerManager()

        # Mock controller
        controller = Mock(spec=Controller)
        controller.name = "TestController"
        controller.resource_type = "TestResource"

        manager.register_controller(controller)
        self.assertIn("TestController", manager.controllers)

    async def test_controller_metrics(self):
        """Test controller metrics"""
        # Create a simple concrete controller implementation
        from astra_core.orchestration.controllers import Controller

        class TestController(Controller):
            async def reconcile(self, resource):
                return resource.status

        controller = TestController(
            name="TestController",
            resource_type="TestResource",
            reconciliation_period=0.1
        )

        metrics = controller.get_metrics()
        self.assertEqual(metrics.reconciliations_total, 0)


class TestServiceMesh(unittest.TestCase):
    """Test service mesh implementation"""

    def test_service_registration(self):
        """Test service registration"""
        mesh = ServiceMesh()

        endpoint = ServiceEndpoint(
            name="test-service",
            address="localhost",
            port=8080
        )

        mesh.register_service(endpoint)
        self.assertIn("test-service", mesh.service_registry)

    def test_traffic_policy(self):
        """Test traffic policy management"""
        mesh = ServiceMesh()

        from astra_core.orchestration.service_mesh import TrafficPolicy

        policy = TrafficPolicy(
            source_service="client",
            destination_service="backend",
            rate_limit=100.0,
            timeout=30.0
        )

        mesh.add_traffic_policy(policy)

        retrieved = mesh.get_traffic_policy("client", "backend")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.rate_limit, 100.0)


class TestObservability(unittest.IsolatedAsyncioTestCase):
    """Test observability stack"""

    def test_metrics_collection(self):
        """Test metrics collection"""
        collector = MetricsCollector()

        # Record some metrics
        collector.record_metric("test_metric", 10.5)
        collector.record_metric("test_metric", 15.2)
        collector.record_metric("test_metric", 12.1)

        # Query metric
        aggregate = collector.query_metric("test_metric")

        self.assertEqual(aggregate.count, 3)
        self.assertEqual(aggregate.avg, 12.6)  # (10.5 + 15.2 + 12.1) / 3

    async def test_health_check(self):
        """Test health checking"""
        health_checker = HealthCheck()

        # Register a health check
        async def always_healthy():
            return True

        health_checker.register_check("test_component", always_healthy)

        # Run health check
        result = await health_checker.check_component("test_component")

        self.assertEqual(result.status.value, "healthy")


class TestCRDSystem(unittest.TestCase):
    """Test CRD system"""

    def test_crd_registration(self):
        """Test CRD registration"""
        registry = CRDRegistry()

        schema = CRDSchema(
            kind="TestResource",
            version="v1",
            group="test.ai",
            plural="testresources",
            singular="testresource",
            properties={}
        )

        crd = CustomResourceDefinition(schema)
        registry.register_crd(crd)

        self.assertIn("TestResource", registry.crds)

    def test_resource_validation(self):
        """Test resource validation"""
        registry = CRDRegistry()

        # Create standard CRDs
        create_standard_crds(registry)

        # Validate a resource
        resource = {
            "kind": "AnalysisTask",
            "name": "test-analysis",
            "spec": {
                "domain": "filaments",
                "analysis_type": "spacing",
                "data_source": "/data/test.fits"
            }
        }

        validation = registry.validate_resource("AnalysisTask", resource)
        self.assertTrue(validation.valid)


class TestIntegratedSystem(unittest.IsolatedAsyncioTestCase):
    """Test complete orchestrated system"""

    async def test_system_creation(self):
        """Test system creation"""
        system = OrchestratedASTRASystem()

        self.assertIsNotNone(system.control_plane)
        self.assertIsNotNone(system.data_plane)
        self.assertIsNotNone(system.service_mesh)
        self.assertIsNotNone(system.observability)
        self.assertIsNotNone(system.crd_registry)

    async def test_system_lifecycle(self):
        """Test system start/stop lifecycle"""
        system = OrchestratedASTRASystem()

        # Start system
        await system.start()
        self.assertTrue(system.running)

        # Check status
        status = system.get_system_status()
        self.assertTrue(status["running"])

        # Stop system
        await system.stop()
        self.assertFalse(system.running)

    async def test_query_processing(self):
        """Test query processing through orchestrated system"""
        system = OrchestratedASTRASystem()
        await system.start()

        # Process query
        result = await system.process_query("Test query")

        self.assertIsNotNone(result)

        await system.stop()

    async def test_task_creation(self):
        """Test creating tasks through orchestrated system"""
        system = OrchestratedASTRASystem()
        await system.start()

        # Create task
        spec = TaskSpec(
            kind="Task",
            name="test-task",
            query="Test query"
        )

        task = await system.create_task(spec)
        self.assertIsNotNone(task)

        await system.stop()


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for orchestration layer"""

    async def test_end_to_end_task_execution(self):
        """Test complete task execution flow"""
        system = create_orchestrated_astra_system()
        await system.start()

        # Create task
        spec = TaskSpec(
            kind="Task",
            name="integration-test",
            query="Analyze filament spacing",
            priority="medium"
        )

        task = await system.create_task(spec)

        # Verify task was created
        self.assertIsNotNone(task)

        # Get task status
        status = await system.get_task_status(task.get_uid())
        self.assertIsNotNone(status)

        await system.stop()

    async def test_system_status_completeness(self):
        """Test that system status includes all components"""
        system = create_orchestrated_astra_system()
        await system.start()

        status = system.get_system_status()

        # Verify all components are present
        self.assertIn("running", status)
        self.assertIn("control_plane", status)
        self.assertIn("data_plane", status)
        self.assertIn("service_mesh", status)
        self.assertIn("observability", status)
        self.assertIn("crds", status)

        await system.stop()


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDeclarativeAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestControllers))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceMesh))
    suite.addTests(loader.loadTestsFromTestCase(TestObservability))
    suite.addTests(loader.loadTestsFromTestCase(TestCRDSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()

    if success:
        print("\n" + "="*60)
        print("ALL TESTS PASSED")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("SOME TESTS FAILED")
        print("="*60)

    exit(0 if success else 1)
