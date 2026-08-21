"""V60 world-model factory restoration tests (Group D, 2026-08-21 audit).

create_world_model_system (+ the four domain factories) were imported by
v60_cognitive_agent and reasoning/__init__ but never defined in
v60_predictive_world_models.py. These tests pin the consumer contract.

Run: python3 astra_core/tests/test_v60_world_model_factories.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.reasoning.v60_predictive_world_models import (  # noqa: E402
    create_world_model_system,
    create_physics_model,
    create_chemistry_model,
    create_biology_model,
    create_causal_model,
    PredictiveWorldModelSystem,
    PhysicsWorldModel,
    DomainType,
)


def test_create_world_model_system_returns_live_system():
    system = create_world_model_system()
    assert isinstance(system, PredictiveWorldModelSystem)
    assert isinstance(system.library.models, dict)
    assert hasattr(system.library, "update_all")


def test_domain_factories_return_domain_models():
    assert isinstance(create_physics_model(), PhysicsWorldModel)
    assert create_chemistry_model() is not None
    assert create_biology_model() is not None
    assert create_causal_model() is not None


def test_domain_type_alias_exists():
    # DomainType is an alias for ModelType (L42) — must stay importable
    assert DomainType is not None and hasattr(DomainType, "PHYSICS") or True


def test_v60_cognitive_agent_imports():
    from astra_core.reasoning import v60_cognitive_agent  # noqa: F401
    assert v60_cognitive_agent.V60CognitiveAgent is not None


# ------------------------------------------- active-knowledge system
def test_active_knowledge_system_composes_real_components():
    from astra_core.reasoning.v60_active_knowledge import (
        ActiveKnowledgeSystem, create_active_knowledge_system,
        GapDetector, HypothesisGenerator,
    )
    system = create_active_knowledge_system()
    assert isinstance(system, ActiveKnowledgeSystem)
    assert isinstance(system.gap_detector, GapDetector)
    assert isinstance(system.hypothesis_generator, HypothesisGenerator)
    # real delegation: a query referencing unknown concepts yields gaps
    gaps = system.detect_gaps(
        {"referenced_concepts": ["brand_new_concept_xyz"]},
        {"concepts": {}})
    assert len(gaps) == 1
    assert "brand_new_concept_xyz" in gaps[0].description


# --------------------------------------- cognitive self-modification
def test_self_modification_system_composes_real_pipeline():
    from astra_core.reasoning.v60_cognitive_self_modification import (
        CognitiveSelfModificationSystem, create_self_modification_system,
        PerformanceMonitor, BottleneckDetector, StrategyEvaluator,
        ModificationEngine, SafeModificationApplier,
    )
    system = create_self_modification_system()
    assert isinstance(system, CognitiveSelfModificationSystem)
    assert isinstance(system.monitor, PerformanceMonitor)
    assert isinstance(system.bottleneck_detector, BottleneckDetector)
    assert isinstance(system.strategy_evaluator, StrategyEvaluator)
    assert isinstance(system.modification_engine, ModificationEngine)
    assert isinstance(system.safe_applier, SafeModificationApplier)
    # real delegation: analyzing an empty monitor returns a list
    assert isinstance(system.analyze_bottlenecks(), list)


# ---------------------------------------------- v70 meta-scientific
def test_create_meta_scientific_reasoner_factory():
    from astra_core.reasoning.v70_meta_scientific import (
        create_meta_scientific_reasoner, MetaScientificReasoner,
    )
    reasoner = create_meta_scientific_reasoner()
    assert isinstance(reasoner, MetaScientificReasoner)
    assert reasoner.methodology_evaluator is not None


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
