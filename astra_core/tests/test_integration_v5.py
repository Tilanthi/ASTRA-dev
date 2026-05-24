"""
Comprehensive Integration Tests for V5.0 Library Additions

Tests NetworkX, SymPy, and DoWhy integration with ASTRA.
"""

import sys
import os
import logging
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_networkx_integration():
    """Test NetworkX graph operations integration."""
    print("\n" + "="*60)
    print("NETWORKX INTEGRATION TESTS")
    print("="*60)

    from astra_core.memory.graph_operations import (
        NetworkXMemoryGraph,
        MORKOntologyGraph,
        ContextGraphOperations,
        is_networkx_available,
    )

    # Test availability
    assert is_networkx_available(), "NetworkX should be available"
    print("✓ NetworkX is available")

    # Test basic graph operations
    graph = NetworkXMemoryGraph("directed")
    assert graph.available, "Graph should be available"
    print("✓ Created directed graph")

    # Add nodes and edges
    graph.add_node("A", type="concept")
    graph.add_node("B", type="concept")
    graph.add_edge("A", "B", relation="related_to")
    print("✓ Added nodes and edges")

    # Test shortest path
    path = graph.shortest_path("A", "B")
    assert path == ["A", "B"], f"Expected path ['A', 'B'], got {path}"
    print("✓ Shortest path computed correctly")

    # Test centrality measures
    centrality = graph.centrality_measures("A")
    assert "degree" in centrality, "Centrality should include degree"
    print(f"✓ Centrality measures: {centrality}")

    # Test MORK Ontology
    mork = MORKOntologyGraph()
    mork.add_concept("mammal")
    mork.add_concept("dog", parent="mammal")
    ancestors = mork.get_ancestors("dog")
    assert "mammal" in ancestors, "Dog should have mammal as ancestor"
    print("✓ MORK Ontology hierarchy working")

    # Test Context Graph
    context = ContextGraphOperations()
    context.add_context_link("A", "B", "semantic", strength=0.8)
    relevance = context.propagate_relevance(["A"], max_depth=2)
    assert "A" in relevance, "Relevance propagation should include seed"
    print(f"✓ Context relevance propagation: {relevance}")

    print("\n✅ All NetworkX tests passed!")
    return True


def test_sympy_integration():
    """Test SymPy symbolic physics integration."""
    print("\n" + "="*60)
    print("SYMPY INTEGRATION TESTS")
    print("="*60)

    from astra_core.physics.symbolic_physics import (
        SymbolicPhysicsEngine,
        PerturbationTheory,
        FilamentStabilityAnalyzer,
        is_sympy_available,
    )

    # Test availability
    assert is_sympy_available(), "SymPy should be available"
    print("✓ SymPy is available")

    # Test symbolic physics engine
    engine = SymbolicPhysicsEngine()
    assert engine.available, "Engine should be available"
    print("✓ Created symbolic physics engine")

    # Test symbolic derivative
    derivative = engine.symbolic_derivative("x**2", "x")
    assert derivative is not None, "Derivative should not be None"
    print(f"✓ Derivative of x^2: {derivative}")

    # Test equation solving
    solutions = engine.solve_equation("x**2 - 4 = 0", "x")
    assert len(solutions) > 0, "Should have solutions"
    print(f"✓ Solutions to x^2 - 4 = 0: {solutions}")

    # Test simplification
    simplified = engine.simplify_expression("(x**2 - 1)/(x - 1)")
    assert "x + 1" in simplified or "x+1" in simplified, "Should simplify to x+1"
    print(f"✓ Simplified (x^2-1)/(x-1): {simplified}")

    # Test LaTeX conversion
    latex = engine.to_latex("x**2 + y**2")
    assert latex is not None, "LaTeX conversion should work"
    print(f"✓ LaTeX output: {latex}")

    # Test perturbation theory
    pt = PerturbationTheory(engine)
    print("✓ Created perturbation theory module")

    # Test filament stability analyzer
    fsa = FilamentStabilityAnalyzer(engine)
    jeans_latex = fsa.jeans_wavelength()
    assert jeans_latex is not None, "Jeans wavelength derivation should work"
    print(f"✓ Jeans wavelength LaTeX: {jeans_latex}")

    print("\n✅ All SymPy tests passed!")
    return True


def test_dowhy_integration():
    """Test DoWhy causal inference integration."""
    print("\n" + "="*60)
    print("DOWHY INTEGRATION TESTS")
    print("="*60)

    from astra_core.reasoning.dowhy_causal_engine import (
        DoWhyCausalEngine,
        AstrophysicalCausalInference,
        is_dowhy_available,
    )

    # Test availability
    assert is_dowhy_available(), "DoWhy should be available"
    print("✓ DoWhy is available")

    # Test basic causal engine
    engine = DoWhyCausalEngine()
    assert engine.available, "Engine should be available"
    print("✓ Created DoWhy causal engine")

    # Test astrophysical causal inference
    astro_engine = AstrophysicalCausalInference()
    assert astro_engine.available, "Astrophysical engine should be available"
    print("✓ Created astrophysical causal inference engine")

    # Test assumption validation (without data)
    validation = astro_engine.validate_causal_assumptions("test_model")
    assert isinstance(validation, dict), "Validation should return dict"
    print(f"✓ Assumption validation: {validation}")

    # Test summary
    summary = astro_engine.get_summary("test_model")
    assert summary is not None, "Summary should not be None"
    print(f"✓ Engine summary: {summary}")

    print("\n✅ All DoWhy tests passed!")
    return True


def test_cross_module_integration():
    """Test cross-module integration and dependencies."""
    print("\n" + "="*60)
    print("CROSS-MODULE INTEGRATION TESTS")
    print("="*60)

    # Test that all three can be imported together
    from astra_core.memory import (
        NetworkXMemoryGraph,
        MORKOntologyGraph,
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

    print("✓ All three modules can be imported simultaneously")

    # Test availability checks
    assert is_networkx_available(), "NetworkX should be available"
    assert is_sympy_available(), "SymPy should be available"
    assert is_dowhy_available(), "DoWhy should be available"
    print("✓ All availability checks pass")

    # Create instances
    graph = NetworkXMemoryGraph("directed")
    physics = SymbolicPhysicsEngine()
    causal = DoWhyCausalEngine()

    print("✓ All three engines instantiated successfully")

    # Test that they don't interfere with each other
    graph.add_node("test")
    result = physics.simplify_expression("x + x")
    assert result is not None, "Physics engine should work"

    summary = causal.get_summary("test")
    assert summary is not None, "Causal engine should work"

    print("✓ All three engines work independently")

    print("\n✅ All cross-module integration tests passed!")
    return True


def test_memory_module_exports():
    """Test that memory module exports are correct."""
    print("\n" + "="*60)
    print("MEMORY MODULE EXPORT TESTS")
    print("="*60)

    from astra_core import memory

    # Check NetworkX exports
    assert hasattr(memory, 'NetworkXMemoryGraph'), "Should export NetworkXMemoryGraph"
    assert hasattr(memory, 'MORKOntologyGraph'), "Should export MORKOntologyGraph"
    assert hasattr(memory, 'ContextGraphOperations'), "Should export ContextGraphOperations"
    assert hasattr(memory, 'create_memory_graph'), "Should export create_memory_graph"
    assert hasattr(memory, 'is_networkx_available'), "Should export is_networkx_available"

    print("✓ All NetworkX exports present in memory module")

    # Test functionality
    is_avail = memory.is_networkx_available()
    assert is_avail == True, "NetworkX should be available"
    print("✓ is_networkx_available() returns True")

    print("\n✅ All memory module export tests passed!")
    return True


def test_physics_module_exports():
    """Test that physics module exports are correct."""
    print("\n" + "="*60)
    print("PHYSICS MODULE EXPORT TESTS")
    print("="*60)

    from astra_core import physics

    # Check SymPy exports
    assert hasattr(physics, 'SymbolicPhysicsEngine'), "Should export SymbolicPhysicsEngine"
    assert hasattr(physics, 'PerturbationTheory'), "Should export PerturbationTheory"
    assert hasattr(physics, 'FilamentStabilityAnalyzer'), "Should export FilamentStabilityAnalyzer"
    assert hasattr(physics, 'create_symbolic_physics_engine'), "Should export create_symbolic_physics_engine"
    assert hasattr(physics, 'is_sympy_available'), "Should export is_sympy_available"

    print("✓ All SymPy exports present in physics module")

    # Test functionality
    is_avail = physics.is_sympy_available()
    assert is_avail == True, "SymPy should be available"
    print("✓ is_sympy_available() returns True")

    print("\n✅ All physics module export tests passed!")
    return True


def test_reasoning_module_exports():
    """Test that reasoning module exports are correct."""
    print("\n" + "="*60)
    print("REASONING MODULE EXPORT TESTS")
    print("="*60)

    from astra_core import reasoning

    # Check DoWhy exports
    assert hasattr(reasoning, 'DoWhyCausalEngine'), "Should export DoWhyCausalEngine"
    assert hasattr(reasoning, 'AstrophysicalCausalInference'), "Should export AstrophysicalCausalInference"
    assert hasattr(reasoning, 'create_dowhy_engine'), "Should export create_dowhy_engine"
    assert hasattr(reasoning, 'create_astrophysical_causal_engine'), "Should export create_astrophysical_causal_engine"
    assert hasattr(reasoning, 'is_dowhy_available'), "Should export is_dowhy_available"

    print("✓ All DoWhy exports present in reasoning module")

    # Test functionality
    is_avail = reasoning.is_dowhy_available()
    assert is_avail == True, "DoWhy should be available"
    print("✓ is_dowhy_available() returns True")

    print("\n✅ All reasoning module export tests passed!")
    return True


def test_error_handling():
    """Test error handling and graceful degradation."""
    print("\n" + "="*60)
    print("ERROR HANDLING TESTS")
    print("="*60)

    from astra_core.memory.graph_operations import NetworkXMemoryGraph
    from astra_core.physics.symbolic_physics import SymbolicPhysicsEngine
    from astra_core.reasoning.dowhy_causal_engine import DoWhyCausalEngine

    # Test NetworkX error handling
    graph = NetworkXMemoryGraph("directed")
    path = graph.shortest_path("nonexistent", "also_nonexistent")
    assert path is None, "Nonexistent path should return None"
    print("✓ NetworkX handles nonexistent nodes gracefully")

    # Test SymPy error handling
    physics = SymbolicPhysicsEngine()
    invalid_expr = physics.symbolic_derivative("invalid[[[", "x")
    # Should not crash, may return None or raise specific error
    print("✓ SymPy handles invalid expressions gracefully")

    # Test DoWhy error handling
    causal = DoWhyCausalEngine()
    summary = causal.get_summary("nonexistent_model")
    assert summary is not None, "Summary for nonexistent model should return empty dict"
    print("✓ DoWhy handles nonexistent models gracefully")

    print("\n✅ All error handling tests passed!")
    return True


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("ASTRA V5.0 INTEGRATION TEST SUITE")
    print("="*60)

    tests = [
        ("NetworkX Integration", test_networkx_integration),
        ("SymPy Integration", test_sympy_integration),
        ("DoWhy Integration", test_dowhy_integration),
        ("Cross-Module Integration", test_cross_module_integration),
        ("Memory Module Exports", test_memory_module_exports),
        ("Physics Module Exports", test_physics_module_exports),
        ("Reasoning Module Exports", test_reasoning_module_exports),
        ("Error Handling", test_error_handling),
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
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Integration successful.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
