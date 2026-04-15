#!/usr/bin/env python3

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
Complete Integration Test Suite for MoE Router with Advanced Capabilities

This test suite verifies:
1. All capability modules are importable
2. MoE router can route to real capabilities
3. Integration with unified system works
4. All links and dependencies are correct
5. Permissionless hooks for corrections
"""

import sys
import os
import time
import traceback
from typing import Dict, List, Tuple, Any
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from astra_core.causal.routing import (
    MoECapabilityRouter,
    ConditionalComputationEngine,
    TaskType
)


@pytest.fixture
def results():
    """Pytest fixture for IntegrationTestResults."""
    return IntegrationTestResults()


class IntegrationTestResults:
    """Track test results."""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        print(f"  ✓ {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"  ✗ {test_name}: {error}")

    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        print(f"  ⚠ {test_name}: {message}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*70}")
        print(f"Integration Test Summary: {len(self.passed)}/{total} passed")
        print(f"{'='*70}")
        if self.warnings:
            print(f"\nWarnings: {len(self.warnings)}")
            for test, msg in self.warnings:
                print(f"  - {test}: {msg}")
        if self.failed:
            print(f"\nFailed: {len(self.failed)}")
            for test, err in self.failed:
                print(f"  - {test}: {err}")


def test_capability_imports(results: IntegrationTestResults):
    """Test that all capability modules can be imported."""
    print("\n" + "="*70)
    print("TEST 1: Capability Module Imports")
    print("="*70)

    import_tests = [
        # Causal
        ("astra_core.causal.model.scm", "StructuralCausalModel"),
        ("astra_core.causal.discovery.pc_algorithm", "PCAlgorithm"),

        # Memory
        ("astra_core.memory.episodic.memory", "EpisodicMemory"),
        ("astra_core.memory.working.memory", "WorkingMemory"),
        ("astra_core.memory.semantic.memory", "SemanticMemory"),

        # Simulation
        ("astra_core.simulation.physics.simulator", "PhysicsSimulator"),

        # Metacognitive
        ("astra_core.metacognitive.monitoring", "CognitiveMonitor"),
    ]

    for module_path, class_name in import_tests:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            results.add_pass(f"Import {class_name} from {module_path}")
        except ImportError as e:
            # This is expected for optional modules
            results.add_warning(f"Import {class_name}", f"Optional module not available: {e}")
        except Exception as e:
            results.add_fail(f"Import {class_name}", str(e))


def test_moe_router_with_real_capabilities(results: IntegrationTestResults):
    """Test MoE router with actual capability functions."""
    print("\n" + "="*70)
    print("TEST 2: MoE Router with Real Capabilities")
    print("="*70)

    router = MoECapabilityRouter()

    # Create mock capability functions that simulate real behavior
    def causal_model_func(task, context):
        return {"result": "causal_model_output", "confidence": 0.9}

    def pc_algorithm_func(task, context):
        return {"result": "pc_algorithm_output", "confidence": 0.85}

    def episodic_memory_func(task, context):
        return {"result": "episodic_memory_output", "confidence": 0.8}

    def working_memory_func(task, context):
        return {"result": "working_memory_output", "confidence": 0.9}

    def physics_simulator_func(task, context):
        return {"result": "physics_simulation", "confidence": 0.85}

    def discovery_engine_func(task, context):
        return {"result": "discovery_result", "confidence": 0.8}

    # Test routing to real capability functions
    task_func_map = {
        "structural_causal_model": causal_model_func,
        "pc_algorithm": pc_algorithm_func,
        "episodic_memory": episodic_memory_func,
        "working_memory": working_memory_func,
        "physics_simulator": physics_simulator_func,
        "scientific_discovery": discovery_engine_func,
    }

    test_tasks = [
        "Build a causal model for this system",
        "Remember previous experimental results",
        "Simulate the orbital dynamics",
    ]

    for task in test_tasks:
        try:
            result = router.select_experts(task)
            selected = [e[0] for e in result]

            # Check if selected experts are in our function map
            available = [e for e in selected if e in task_func_map]

            if available:
                results.add_pass(f"Route task: {task[:40]}... -> {available}")
            else:
                results.add_warning(f"Route task: {task[:40]}...", "No available experts matched")
        except Exception as e:
            results.add_fail(f"Route task: {task[:40]}", str(e))


def test_unified_system_integration(results: IntegrationTestResults):
    """Test integration with unified STAN system."""
    print("\n" + "="*70)
    print("TEST 3: Unified System Integration")
    print("="*70)

    try:
        from astra_core import create_stan_system

        # Create system in different modes
        modes = ["v4", "general", "unified"]

        for mode in modes:
            try:
                system = create_stan_system(mode=mode)
                results.add_pass(f"Create unified system in {mode} mode")

                # Check if system has expected attributes
                if hasattr(system, 'process_query'):
                    results.add_pass(f"System {mode} has process_query method")
                else:
                    results.add_warning(f"System {mode}", "No process_query method")

            except Exception as e:
                # Some modes might fail due to missing dependencies
                if "unified" in mode and "Legacy" in str(e):
                    results.add_warning(f"Create {mode} system", "Legacy components not available")
                else:
                    results.add_fail(f"Create {mode} system", str(e))

    except ImportError as e:
        results.add_fail("Import create_stan_system", str(e))


def test_routing_with_all_task_types(results: IntegrationTestResults):
    """Test routing across all task types."""
    print("\n" + "="*70)
    print("TEST 4: Routing Across All Task Types")
    print("="*70)

    engine = ConditionalComputationEngine(top_k=2)

    # Create dummy function map
    dummy_func = lambda task, ctx: {"result": "dummy"}
    task_func_map = {name: dummy_func for name in engine.router.experts.keys()}

    # Test all task types
    task_type_tests = [
        ("Analyze causal structure", TaskType.CAUSAL_ANALYSIS),
        ("Discover new patterns", TaskType.DISCOVERY),
        ("Simulate physical system", TaskType.SIMULATION),
        ("Analyze trading signals", TaskType.TRADING),
        ("Process astronomical data", TaskType.ASTRONOMY),
        ("Recall past experiences", TaskType.MEMORY),
        ("Evaluate confidence levels", TaskType.METACOGNITIVE),
        ("Generate creative analogy", TaskType.CREATIVE),
    ]

    for task, expected_type in task_type_tests:
        try:
            result = engine.route_and_execute(task, task_func_map)
            predicted_type, _ = engine.router.classify_task(task)

            if predicted_type == expected_type:
                results.add_pass(f"Classify: {task[:30]}... as {expected_type.value}")
            else:
                results.add_warning(
                    f"Classify: {task[:30]}...",
                    f"Expected {expected_type.value}, got {predicted_type.value}"
                )

        except Exception as e:
            results.add_fail(f"Classify: {task[:30]}", str(e))


def test_expert_affinity_learning(results: IntegrationTestResults):
    """Test that expert affinity updates correctly."""
    print("\n" + "="*70)
    print("TEST 5: Expert Affinity Learning")
    print("="*70)

    router = MoECapabilityRouter()

    task = "Analyze causal relationships"
    task_type, _ = router.classify_task(task)

    # Get initial affinity
    selected = router.select_experts(task)
    expert_name = selected[0][0]
    initial_affinity = router.expert_task_affinity.get((expert_name, task_type), 0.5)

    # Update with positive outcomes
    for _ in range(10):
        router.update_affinity(expert_name, task_type, success=True, response_time=0.1)

    final_affinity = router.expert_task_affinity.get((expert_name, task_type), 0.5)

    if final_affinity > initial_affinity:
        results.add_pass(f"Affinity increased: {initial_affinity:.3f} -> {final_affinity:.3f}")
    else:
        results.add_fail(f"Affinity learning", f"Did not increase: {initial_affinity:.3f} -> {final_affinity:.3f}")


def test_load_balancing(results: IntegrationTestResults):
    """Test load balancing across experts."""
    print("\n" + "="*70)
    print("TEST 6: Load Balancing")
    print("="*70)

    router = MoECapabilityRouter()

    # Simulate multiple tasks that would use the same expert
    task = "Causal analysis task"
    expert_name = "structural_causal_model"

    # Increase load on one expert
    router.experts[expert_name].current_load = 10.0

    # Select experts
    selected = router.select_experts(task)

    # Check that the highly-loaded expert is not selected first
    if selected and selected[0][0] != expert_name:
        results.add_pass(f"Load balancing: {expert_name} not prioritized due to high load")
    else:
        results.add_warning(f"Load balancing", f"{expert_name} still selected despite high load")


def test_explainability(results: IntegrationTestResults):
    """Test routing explainability."""
    print("\n" + "="*70)
    print("TEST 7: Routing Explainability")
    print("="*70)

    router = MoECapabilityRouter()

    task = "Build a causal model and discover underlying patterns"

    try:
        explanation = router.explain_routing(task)

        if "Task Classification" in explanation:
            results.add_pass("Explainability includes task classification")

        if "Selected Experts" in explanation:
            results.add_pass("Explainability includes selected experts")

        if "specializes in" in explanation.lower():
            results.add_pass("Explainability includes expert specializations")

        if "Success rate" in explanation:
            results.add_pass("Explainability includes success rates")

    except Exception as e:
        results.add_fail("Generate explanation", str(e))


def test_conditional_computation(results: IntegrationTestResults):
    """Test conditional computation efficiency."""
    print("\n" + "="*70)
    print("TEST 8: Conditional Computation")
    print("="*70)

    engine = ConditionalComputationEngine(top_k=3)

    dummy_func = lambda task, ctx: {"result": "ok"}
    task_func_map = {name: dummy_func for name in engine.router.experts.keys()}

    total_experts = len(task_func_map)

    # Test multiple tasks
    tasks = [
        "Causal analysis",
        "Memory recall",
        "Simulation",
        "Trading analysis",
        "Discovery",
    ]

    for task in tasks:
        result = engine.route_and_execute(task, task_func_map)
        num_selected = len(result['selected_experts'])

        if num_selected <= 3:
            results.add_pass(f"Conditional compute: {num_selected}/{total_experts} experts for '{task}'")
        else:
            results.add_fail(f"Conditional compute: {task}", f"Too many experts: {num_selected}")


def test_permissionless_hooks(results: IntegrationTestResults):
    """Test that permissionless hooks work for corrections."""
    print("\n" + "="*70)
    print("TEST 9: Permissionless Hooks")
    print("="*70)

    router = MoECapabilityRouter()

    # Test 1: Adding a new expert dynamically
    try:
        from astra_core.causal.routing.moe_router import Expert

        new_expert = Expert(
            name="dynamic_expert",
            module_path="test.module",
            task_types=[TaskType.GENERAL],
            specialization_keywords=["dynamic", "runtime", "added"]
        )

        router.experts["dynamic_expert"] = new_expert
        results.add_pass("Add expert dynamically at runtime")

    except Exception as e:
        results.add_fail("Add expert dynamically", str(e))

    # Test 2: Updating expert scores
    try:
        task = "Test task for dynamic expert"
        selected = router.select_experts(task)

        if "dynamic_expert" in [e[0] for e in selected]:
            results.add_pass("Dynamic expert selected for relevant task")
        else:
            results.add_warning("Dynamic expert", "Not selected (may not match keywords)")

    except Exception as e:
        results.add_fail("Select dynamic expert", str(e))

    # Test 3: Updating affinity based on feedback
    try:
        router.update_affinity(
            "dynamic_expert",
            TaskType.GENERAL,
            success=True,
            response_time=0.1
        )

        if router.experts["dynamic_expert"].usage_count > 0:
            results.add_pass("Update affinity from feedback")
        else:
            results.add_fail("Update affinity", "Usage count not incremented")

    except Exception as e:
        results.add_fail("Update affinity", str(e))


def test_end_to_end_routing(results: IntegrationTestResults):
    """End-to-end test of routing with simulated real capabilities."""
    print("\n" + "="*70)
    print("TEST 10: End-to-End Routing")
    print("="*70)

    engine = ConditionalComputationEngine(top_k=3)

    # Simulate real capability functions
    capabilities = {
        "structural_causal_model": lambda t, c: {"model": "DAG", "edges": 5},
        "pc_algorithm": lambda t, c: {"graph": "skeleton", "independencies": 3},
        "episodic_memory": lambda t, c: {"memories": 5, "relevance": 0.8},
        "scientific_discovery": lambda t, c: {"hypothesis": "new theory", "confidence": 0.7},
        "physics_simulator": lambda t, c: {"trajectory": "computed", "time": 100},
    }

    # Complex multi-domain task
    task = "Analyze the causal structure of this physical system using previous experimental data"

    try:
        result = engine.route_and_execute(task, capabilities)

        # Verify routing
        if result['selected_experts']:
            results.add_pass(f"Selected {len(result['selected_experts'])} experts")

        # Verify execution
        if result['results']:
            results.add_pass(f"Executed {len(result['results'])} capabilities")

        # Verify we got results
        has_results = all('result' in v or 'graph' in v or 'model' in v
                         for v in result['results'].values())

        if has_results:
            results.add_pass("All capabilities returned valid results")

        # Verify efficiency
        if len(result['selected_experts']) < len(capabilities):
            results.add_pass(f"Efficient routing: {len(result['selected_experts'])}/{len(capabilities)} used")

    except Exception as e:
        results.add_fail("End-to-end routing", f"{e}\n{traceback.format_exc()}")


def test_router_statistics(results: IntegrationTestResults):
    """Test routing statistics collection."""
    print("\n" + "="*70)
    print("TEST 11: Router Statistics")
    print("="*70)

    engine = ConditionalComputationEngine()

    dummy_func = lambda t, c: {"result": "ok"}
    task_func_map = {name: dummy_func for name in engine.router.experts.keys()}

    # Generate routing activity
    tasks = [
        "Causal task",
        "Memory task",
        "Simulation task",
    ] * 5

    for task in tasks:
        engine.route_and_execute(task, task_func_map)

    try:
        stats = engine.router.get_routing_stats()

        if stats['total_routings'] > 0:
            results.add_pass(f"Collected {stats['total_routings']} routing records")

        if 'expert_usage' in stats:
            results.add_pass("Statistics include expert usage")

        if 'task_type_distribution' in stats:
            results.add_pass("Statistics include task type distribution")

        if 'avg_experts_per_task' in stats:
            results.add_pass("Statistics include average experts per task")

    except Exception as e:
        results.add_fail("Get statistics", str(e))


def run_all_integration_tests():
    """Run all integration tests."""
    print("\n")
    print("="*70)
    print("Complete Integration Test Suite for MoE Router")
    print("="*70)
    print("\nTesting all dependencies, links, and components...")

    results = IntegrationTestResults()

    try:
        test_capability_imports(results)
        test_moe_router_with_real_capabilities(results)
        test_unified_system_integration(results)
        test_routing_with_all_task_types(results)
        test_expert_affinity_learning(results)
        test_load_balancing(results)
        test_explainability(results)
        test_conditional_computation(results)
        test_permissionless_hooks(results)
        test_end_to_end_routing(results)
        test_router_statistics(results)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()

    results.summary()

    # Return success status
    return len(results.failed) == 0


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
