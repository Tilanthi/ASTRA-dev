"""
Deep Dependency and Cross-Link Tests for V5.0 Integration

Tests for:
1. Import chain integrity
2. Circular dependency detection
3. Module accessibility
4. Function availability
5. Cross-module compatibility
"""

import sys
import os
import logging
import importlib
from typing import Dict, List, Set, Any

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_import_chains():
    """Test that all import chains are valid."""
    print("\n" + "="*60)
    print("IMPORT CHAIN INTEGRITY TESTS")
    print("="*60)

    import_chains = [
        # NetworkX chain
        ("astra_core.memory.graph_operations", [
            "networkx",
        ]),
        # SymPy chain
        ("astra_core.physics.symbolic_physics", [
            "sympy",
        ]),
        # DoWhy chain
        ("astra_core.reasoning.dowhy_causal_engine", [
            "dowhy",
            "networkx",  # DoWhy depends on NetworkX
        ]),
    ]

    passed = 0
    total = 0

    for module_name, expected_deps in import_chains:
        total += 1
        try:
            module = importlib.import_module(module_name)
            print(f"✓ Imported {module_name}")

            # Check if expected dependencies are accessible
            for dep in expected_deps:
                try:
                    importlib.import_module(dep)
                    print(f"  ✓ Dependency {dep} is accessible")
                except ImportError:
                    print(f"  ✗ Dependency {dep} is NOT accessible")
                    raise

            passed += 1
        except Exception as e:
            print(f"✗ Failed to import {module_name}: {e}")

    print(f"\nImport chains: {passed}/{total} passed")
    return passed == total


def test_circular_dependencies():
    """Test for circular dependencies."""
    print("\n" + "="*60)
    print("CIRCULAR DEPENDENCY TESTS")
    print("="*60)

    # Modules to check for circular dependencies
    modules_to_check = [
        "astra_core.memory",
        "astra_core.memory.graph_operations",
        "astra_core.physics",
        "astra_core.physics.symbolic_physics",
        "astra_core.reasoning",
        "astra_core.reasoning.dowhy_causal_engine",
    ]

    passed = 0
    total = 0

    for module_name in modules_to_check:
        total += 1
        try:
            # Import module
            module = importlib.import_module(module_name)

            # Get module's file
            module_file = getattr(module, '__file__', None)
            if module_file:
                # Simple check: if we got here without circular import error, we're good
                print(f"✓ {module_name} - no circular dependency detected")
                passed += 1
            else:
                print(f"⚠ {module_name} - no file attribute (namespace package)")
                passed += 1

        except ImportError as e:
            if "circular" in str(e).lower():
                print(f"✗ {module_name} - CIRCULAR IMPORT DETECTED: {e}")
            else:
                print(f"✗ {module_name} - import error: {e}")

    print(f"\nCircular dependency checks: {passed}/{total} passed")
    return passed == total


def test_module_exports():
    """Test that all expected exports are available."""
    print("\n" + "="*60)
    print("MODULE EXPORTS TESTS")
    print("="*60)

    # Expected exports from each module
    expected_exports = {
        "astra_core.memory": [
            "NetworkXMemoryGraph",
            "MORKOntologyGraph",
            "ContextGraphOperations",
            "create_memory_graph",
            "is_networkx_available",
        ],
        "astra_core.physics": [
            "SymbolicPhysicsEngine",
            "PerturbationTheory",
            "FilamentStabilityAnalyzer",
            "create_symbolic_physics_engine",
            "is_sympy_available",
        ],
        "astra_core.reasoning": [
            "DoWhyCausalEngine",
            "AstrophysicalCausalInference",
            "create_dowhy_engine",
            "create_astrophysical_causal_engine",
            "is_dowhy_available",
        ],
    }

    passed = 0
    total = 0

    for module_name, exports in expected_exports.items():
        try:
            module = importlib.import_module(module_name)
            print(f"\nChecking {module_name}:")

            module_passed = 0
            for export_name in exports:
                total += 1
                if hasattr(module, export_name):
                    print(f"  ✓ {export_name} is exported")
                    module_passed += 1
                    passed += 1
                else:
                    print(f"  ✗ {export_name} is NOT exported")

            if module_passed == len(exports):
                print(f"✓ {module_name} - all exports present")

        except Exception as e:
            print(f"✗ {module_name} - error: {e}")

    print(f"\nModule exports: {passed}/{total} exports found")
    return passed == total


def test_function_availability():
    """Test that key functions are callable."""
    print("\n" + "="*60)
    print("FUNCTION AVAILABILITY TESTS")
    print("="*60)

    functions_to_test = [
        ("astra_core.memory.graph_operations", "NetworkXMemoryGraph", []),
        ("astra_core.memory.graph_operations", "MORKOntologyGraph", []),
        ("astra_core.memory.graph_operations", "ContextGraphOperations", []),
        ("astra_core.memory.graph_operations", "create_memory_graph", []),
        ("astra_core.memory.graph_operations", "is_networkx_available", []),
        ("astra_core.physics.symbolic_physics", "SymbolicPhysicsEngine", []),
        ("astra_core.physics.symbolic_physics", "PerturbationTheory", []),
        ("astra_core.physics.symbolic_physics", "FilamentStabilityAnalyzer", []),
        ("astra_core.physics.symbolic_physics", "create_symbolic_physics_engine", []),
        ("astra_core.physics.symbolic_physics", "is_sympy_available", []),
        ("astra_core.reasoning.dowhy_causal_engine", "DoWhyCausalEngine", []),
        ("astra_core.reasoning.dowhy_causal_engine", "AstrophysicalCausalInference", []),
        ("astra_core.reasoning.dowhy_causal_engine", "create_dowhy_engine", []),
        ("astra_core.reasoning.dowhy_causal_engine", "create_astrophysical_causal_engine", []),
        ("astra_core.reasoning.dowhy_causal_engine", "is_dowhy_available", []),
    ]

    passed = 0
    total = 0

    for module_name, func_name, args in functions_to_test:
        total += 1
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)

            # Test if callable or class
            if callable(func) or isinstance(func, type):
                print(f"✓ {module_name}.{func_name} is callable")
                passed += 1
            else:
                print(f"✗ {module_name}.{func_name} is NOT callable")

        except Exception as e:
            print(f"✗ {module_name}.{func_name} - error: {e}")

    print(f"\nFunction availability: {passed}/{total} passed")
    return passed == total


def test_cross_module_compatibility():
    """Test that modules work together without conflicts."""
    print("\n" + "="*60)
    print("CROSS-MODULE COMPATIBILITY TESTS")
    print("="*60)

    try:
        # Import all three modules
        from astra_core.memory import (
            NetworkXMemoryGraph,
            is_networkx_available,
        )
        from astra_core.physics import (
            SymbolicPhysicsEngine,
            is_sympy_available,
        )
        from astra_core.reasoning import (
            DoWhyCausalEngine,
            is_dowhy_available,
        )

        print("✓ All modules imported successfully")

        # Check availability
        assert is_networkx_available(), "NetworkX should be available"
        assert is_sympy_available(), "SymPy should be available"
        assert is_dowhy_available(), "DoWhy should be available"
        print("✓ All libraries available")

        # Create instances
        graph = NetworkXMemoryGraph("directed")
        physics = SymbolicPhysicsEngine()
        causal = DoWhyCausalEngine()
        print("✓ All engines instantiated")

        # Test basic operations
        graph.add_node("test")
        result = physics.simplify_expression("x + x")
        summary = causal.get_summary("test")

        assert result is not None, "Physics should return result"
        assert summary is not None, "Causal should return summary"
        print("✓ All engines functional")

        print("\n✅ Cross-module compatibility verified!")
        return True

    except Exception as e:
        print(f"\n✗ Cross-module compatibility test failed: {e}")
        return False


def test_backward_compatibility():
    """Test backward compatibility with existing ASTRA code."""
    print("\n" + "="*60)
    print("BACKWARD COMPATIBILITY TESTS")
    print("="*60)

    try:
        # Test that existing imports still work
        from astra_core.memory import MORKOntology, MemoryGraph
        from astra_core.physics import UnifiedPhysicsEngine
        from astra_core.reasoning import CausalGraph

        print("✓ Legacy imports still work")

        # Test that new imports don't break old ones
        from astra_core import memory, physics, reasoning
        assert hasattr(memory, 'MORKOntology'), "Legacy MORKOntology should still be available"
        assert hasattr(physics, 'UnifiedPhysicsEngine'), "Legacy UnifiedPhysicsEngine should still be available"
        assert hasattr(reasoning, 'CausalGraph'), "Legacy CausalGraph should still be available"

        print("✓ Legacy and new exports coexist")

        print("\n✅ Backward compatibility verified!")
        return True

    except Exception as e:
        print(f"\n✗ Backward compatibility test failed: {e}")
        return False


def test_no_conflicts():
    """Test that new integrations don't create conflicts."""
    print("\n" + "="*60)
    print("CONFLICT DETECTION TESTS")
    print("="*60)

    # Check for duplicate names
    from astra_core import memory, physics, reasoning

    def get_all_exports(module):
        """Get all public exports from a module."""
        if hasattr(module, '__all__'):
            return set(module.__all__)
        return {
            name for name in dir(module)
            if not name.startswith('_')
        }

    memory_exports = get_all_exports(memory)
    physics_exports = get_all_exports(physics)
    reasoning_exports = get_all_exports(reasoning)

    # Check for overlapping exports
    memory_physics_overlap = memory_exports & physics_exports
    memory_reasoning_overlap = memory_exports & reasoning_exports
    physics_reasoning_overlap = physics_exports & reasoning_exports

    conflicts_found = False

    if memory_physics_overlap:
        print(f"⚠ Memory/Physics overlap: {memory_physics_overlap}")
        conflicts_found = True

    if memory_reasoning_overlap:
        print(f"⚠ Memory/Reasoning overlap: {memory_reasoning_overlap}")
        conflicts_found = True

    if physics_reasoning_overlap:
        print(f"⚠ Physics/Reasoning overlap: {physics_reasoning_overlap}")
        conflicts_found = True

    if not conflicts_found:
        print("✓ No export name conflicts detected")

    print("\n✅ Conflict detection complete!")
    return not conflicts_found


def run_deep_tests():
    """Run all deep dependency tests."""
    print("\n" + "="*60)
    print("ASTRA V5.0 DEEP DEPENDENCY TEST SUITE")
    print("="*60)

    tests = [
        ("Import Chains", test_import_chains),
        ("Circular Dependencies", test_circular_dependencies),
        ("Module Exports", test_module_exports),
        ("Function Availability", test_function_availability),
        ("Cross-Module Compatibility", test_cross_module_compatibility),
        ("Backward Compatibility", test_backward_compatibility),
        ("Conflict Detection", test_no_conflicts),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test '{name}' failed with exception: {e}")
            results[name] = False

    # Summary
    print("\n" + "="*60)
    print("DEEP TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} test categories passed")

    if passed == total:
        print("\n🎉 ALL DEEP TESTS PASSED! Integration is solid.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test categor(ies) failed. Review above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_deep_tests())
