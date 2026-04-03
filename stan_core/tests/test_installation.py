"""
Quick installation test for STAN-CORE V4.0 Unified
"""

import sys


def test_imports():
    """Test that all main modules can be imported."""
    print("Testing STAN-CORE V4.0 Unified imports...")

    import stan_core
    assert stan_core is not None
    print("✓ stan_core")

    from stan_core.causal import StructuralCausalModel, PCAlgorithm
    assert StructuralCausalModel is not None
    assert PCAlgorithm is not None
    print("✓ Causal reasoning components")

    from stan_core.memory import EpisodicMemory, SemanticMemory
    assert EpisodicMemory is not None
    assert SemanticMemory is not None
    print("✓ Memory components")

    from stan_core.discovery import HypothesisGenerator
    assert HypothesisGenerator is not None
    print("✓ Discovery components")

    from stan_core.simulation import PhysicsSimulator
    assert PhysicsSimulator is not None
    print("✓ Simulation components")

    from stan_core.metacognitive import CognitiveMonitor
    assert CognitiveMonitor is not None
    print("✓ Meta-cognitive components")

    from stan_core.neural import MultiLayerPerceptron, Trainer
    assert MultiLayerPerceptron is not None
    assert Trainer is not None
    print("✓ Neural training components")

    from stan_core.trading import MarketCausalAnalyzer
    assert MarketCausalAnalyzer is not None
    print("✓ Trading components")

    # Test legacy imports
    from stan_core.arc_agi import Grid, EnhancedARCSolver
    assert Grid is not None
    assert EnhancedARCSolver is not None
    print("✓ ARC-AGI components (legacy)")

    from stan_core.astro_physics import AstroSwarmSystem
    assert AstroSwarmSystem is not None
    print("✓ ASTRO physics components (legacy)")

    from stan_core.scientific_discovery import autonomous_discovery
    assert autonomous_discovery is not None
    print("✓ Scientific discovery components (legacy)")

    from stan_core.reasoning import V41Orchestrator
    assert V41Orchestrator is not None
    print("✓ Reasoning components (legacy)")

    print("\nAll imports successful!")


def test_basic_functionality():
    """Test basic functionality."""
    print("\nTesting basic functionality...")

    # Test SCM creation
    from stan_core.causal.model.scm import (
        StructuralCausalModel,
        Variable,
        VariableType,
        StructuralEquation
    )

    scm = StructuralCausalModel(name="test")
    scm.add_variable(Variable("X", VariableType.CONTINUOUS))
    scm.add_variable(Variable("Y", VariableType.CONTINUOUS))

    def eq(parents):
        return 0.5 * parents.get("X", 0)

    scm.add_edge("X", "Y", StructuralEquation(eq), confidence=0.9)

    print("✓ Created Structural Causal Model")

    # Test episodic memory
    from stan_core.memory.episodic.memory import Experience, EpisodicMemory

    memory = EpisodicMemory()
    exp = Experience(content="Test experience")
    memory.store(exp)

    retrieved = memory.retrieve(exp.id)
    assert retrieved is not None

    print("✓ Episodic memory works")

    # Test working memory
    from stan_core.memory.working.memory import WorkingMemory

    wm = WorkingMemory()
    wm.add("item1", "content1")
    content = wm.get("item1")
    assert content == "content1"

    print("✓ Working memory works")

    # Test meta-cognitive monitoring
    from stan_core.metacognitive.monitoring.monitor import CognitiveMonitor

    monitor = CognitiveMonitor()
    pid = monitor.start_process("test")
    monitor.end_process(pid)

    print("✓ Meta-cognitive monitoring works")

    print("\nAll basic functionality tests passed!")


def main():
    """Run all tests."""
    print("=" * 50)
    print("STAN-CORE V4.0 Unified Installation Test")
    print("=" * 50)
    print()

    success = True

    if not test_imports():
        success = False

    if not test_basic_functionality():
        success = False

    print()
    print("=" * 50)
    if success:
        print("ALL TESTS PASSED ✓")
        print("STAN-CORE V4.0 Unified is ready to use!")
    else:
        print("SOME TESTS FAILED ✗")
        print("Please check the errors above.")
    print("=" * 50)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
