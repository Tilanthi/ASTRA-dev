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
Quick installation test for STAN-CORE V4.0 Unified
"""

import sys


def test_imports():
    """Test that all main modules can be imported."""
    print("Testing STAN-CORE V4.0 Unified imports...")

    import astra_core
    assert astra_core is not None
    print("✓ astra_core")

    from astra_core.causal import StructuralCausalModel, PCAlgorithm
    assert StructuralCausalModel is not None
    assert PCAlgorithm is not None
    print("✓ Causal reasoning components")

    from astra_core.memory import EpisodicMemory, SemanticMemory
    assert EpisodicMemory is not None
    assert SemanticMemory is not None
    print("✓ Memory components")

    from astra_core.discovery import HypothesisGenerator
    assert HypothesisGenerator is not None
    print("✓ Discovery components")

    from astra_core.simulation import PhysicsSimulator
    assert PhysicsSimulator is not None
    print("✓ Simulation components")

    from astra_core.metacognitive import CognitiveMonitor
    assert CognitiveMonitor is not None
    print("✓ Meta-cognitive components")

    from astra_core.neural import MultiLayerPerceptron, Trainer
    assert MultiLayerPerceptron is not None
    assert Trainer is not None
    print("✓ Neural training components")

    from astra_core.trading import MarketCausalAnalyzer
    assert MarketCausalAnalyzer is not None
    print("✓ Trading components")

    # Test legacy imports
    from astra_core.arc_agi import Grid, EnhancedARCSolver
    assert Grid is not None
    assert EnhancedARCSolver is not None
    print("✓ ARC-AGI components (legacy)")

    from astra_core.astro_physics import AstroSwarmSystem
    assert AstroSwarmSystem is not None
    print("✓ ASTRO physics components (legacy)")

    from astra_core.scientific_discovery import autonomous_discovery
    assert autonomous_discovery is not None
    print("✓ Scientific discovery components (legacy)")

    from astra_core.reasoning import V41Orchestrator
    assert V41Orchestrator is not None
    print("✓ Reasoning components (legacy)")

    print("\nAll imports successful!")


def test_basic_functionality():
    """Test basic functionality."""
    print("\nTesting basic functionality...")

    # Test SCM creation
    from astra_core.causal.model.scm import (
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
    from astra_core.memory.episodic.memory import Experience, EpisodicMemory

    memory = EpisodicMemory()
    exp = Experience(content="Test experience")
    memory.store(exp)

    retrieved = memory.retrieve(exp.id)
    assert retrieved is not None

    print("✓ Episodic memory works")

    # Test working memory
    from astra_core.memory.working.memory import WorkingMemory

    wm = WorkingMemory()
    wm.add("item1", "content1")
    content = wm.get("item1")
    assert content == "content1"

    print("✓ Working memory works")

    # Test meta-cognitive monitoring
    from astra_core.metacognitive.monitoring.monitor import CognitiveMonitor

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
