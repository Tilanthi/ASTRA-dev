"""V40 missing-engine restoration tests (Group C, 2026-08-21 audit).

NeuralTheoremProver, EnhancedKnowledgeRetrieval (+StackExchangeAPI/
KnowledgeFusion/SourceRanker), AnswerVerifier (+UnitConsistencyChecker/
ConstraintValidator) were imported by v40 modules but never defined;
meta_cognitive.py is a baselined syntax-broken file whose names must come
from a fallback. These tests pin the contracts v40_system.py consumes —
and the honesty rule: no fabricated PROVED/VERIFIED results.

Run: python3 astra_core/tests/test_v40_missing_engines.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.legacy.systems.v40.theorem_prover import (  # noqa: E402
    NeuralTheoremProver, TheoremStatus, ProofSketch, Counterexample,
)
from astra_core.legacy.systems.v40.enhanced_knowledge import (  # noqa: E402
    EnhancedKnowledgeRetrieval, StackExchangeAPI, KnowledgeFusion, SourceRanker,
    GoogleScholarAPI, KnowledgeResult, KnowledgeSourceType,
)
from astra_core.legacy.systems.v40.answer_verification import (  # noqa: E402
    AnswerVerifier, UnitConsistencyChecker, ConstraintValidator,
    Unit, VerificationStatus,
)


# ---------------------------------------------------------------- theorem
def test_prover_arithmetic_true_is_proved():
    prover = NeuralTheoremProver()
    status, result = prover.prove("2 + 2 = 4")
    assert status == TheoremStatus.PROVED
    assert isinstance(result, ProofSketch)
    assert result.complete and result.confidence >= 0.9
    assert all(s.verified for s in result.steps)


def test_prover_arithmetic_false_is_disproved_with_counterexample():
    prover = NeuralTheoremProver()
    status, result = prover.prove("2 + 2 = 5")
    assert status == TheoremStatus.DISPROVED
    assert isinstance(result, Counterexample)
    assert result.variable_assignment  # records the witness values


def test_prover_undecidable_is_unknown_never_fabricated():
    prover = NeuralTheoremProver()
    status, result = prover.prove("every even number > 2 is the sum of two primes")
    assert status == TheoremStatus.UNKNOWN
    assert result is None


def test_prover_stats_count_all_outcomes():
    prover = NeuralTheoremProver()
    prover.prove("1 + 1 = 2")
    prover.prove("1 + 1 = 3")
    prover.prove("the riemann hypothesis holds")
    stats = prover.get_stats()
    assert stats["theorems_attempted"] == 3
    assert stats["proved"] == 1
    assert stats["disproved"] == 1
    assert stats["undecided"] == 1


# ------------------------------------------------------- knowledge
def test_scholar_search_without_key_returns_empty_not_mock():
    api = GoogleScholarAPI()
    assert api.search("black hole thermodynamics") == []


def test_retrieval_without_keys_reports_no_sources():
    retrieval = EnhancedKnowledgeRetrieval()
    result = retrieval.query("what is a pulsar", "Astronomy")
    assert result["success"] is False
    assert result["results_count"] == 0
    assert result["content"] == ""
    assert result["results"] == []
    assert "reason" in result  # must explain why nothing was retrieved


def test_retrieval_stats_track_queries():
    retrieval = EnhancedKnowledgeRetrieval()
    retrieval.query("pulsar")
    assert retrieval.get_stats()["queries_made"] == 1


def test_fusion_dedupes_and_ranker_orders():
    a = KnowledgeResult(source=KnowledgeSourceType.GOOGLE_SCHOLAR,
                        title="Same paper", content="x", relevance=0.9)
    b = KnowledgeResult(source=KnowledgeSourceType.GOOGLE_SCHOLAR,
                        title="Same paper", content="x", relevance=0.9)
    c = KnowledgeResult(source=KnowledgeSourceType.STACK_EXCHANGE,
                        title="Other", content="y", relevance=0.2)
    assert len(KnowledgeFusion().fuse([a, b, c])) == 2
    ranked = SourceRanker().rank([c, a])
    assert ranked[0].title == "Same paper"  # higher combined score first


def test_stackexchange_api_without_key_returns_empty():
    api = StackExchangeAPI()
    assert api.search("python list comprehension") == []


# ---------------------------------------------------- verification
def test_verifier_empty_answer_is_unknown_never_verified():
    verifier = AnswerVerifier()
    result = verifier.verify("", "what is 2+2?", ["computed 4"])
    assert result["status"] == "unknown"
    assert result["verified"] is False


def test_verifier_returns_structured_result_and_tracks_stats():
    verifier = AnswerVerifier()
    result = verifier.verify("4", "what is 2+2?", ["added 2 and 2", "therefore 4"])
    assert "confidence" in result and "checks" in result and "issues" in result
    assert verifier.get_stats()["total_verifications"] == 1


def test_unit_checker_converts_to_si_before_comparing():
    checker = UnitConsistencyChecker()
    km = Unit(name="kilometre", dimension="length", symbol="km", si_conversion=1000.0)
    m = Unit(name="metre", dimension="length", symbol="m", si_conversion=1.0)
    ok = checker.check_consistency(3.0, km, 3000.0, m)
    assert ok.status == VerificationStatus.VERIFIED
    bad = checker.check_consistency(3.0, km, 4000.0, m)
    assert bad.status == VerificationStatus.FAILED
    s = Unit(name="second", dimension="time", symbol="s", si_conversion=1.0)
    mixed = checker.check_consistency(3.0, km, 3000.0, s)
    assert mixed.status == VerificationStatus.FAILED  # dimension mismatch


def test_constraint_validator_enforces_bounds():
    validator = ConstraintValidator()
    ok = validator.validate(0.5, {"min": 0.0, "max": 1.0})
    assert ok.status == VerificationStatus.VERIFIED
    bad = validator.validate(1.5, {"min": 0.0, "max": 1.0})
    assert bad.status == VerificationStatus.FAILED
    enum_ok = validator.validate("b", {"allowed": ["a", "b"]})
    assert enum_ok.status == VerificationStatus.VERIFIED


# ------------------------------------------------ meta-cognitive fallback
def test_meta_cognitive_fallback_importable_from_package():
    import astra_core.legacy.systems.v40 as v40
    # the five names the package __init__ re-exports
    for name in ("MetaCognitiveController", "ReasoningStrategy",
                 "ResourceBudget", "ConfidenceEstimator",
                 "StrategySelector"):
        assert getattr(v40, name, None) is not None, name
    # StrategyResult/ProblemCharacteristics come via v40_system's own
    # fallback import (not package-level exports, as originally designed)
    from astra_core.legacy.systems.v40.v40_system import (
        StrategyResult, ProblemCharacteristics,
    )
    assert StrategyResult is not None and ProblemCharacteristics is not None


def test_fallback_controller_delegates_to_registered_executor():
    from astra_core.legacy.systems.v40 import (
        MetaCognitiveController, ReasoningStrategy, ResourceBudget,
    )
    controller = MetaCognitiveController()
    calls = []

    def fake_executor(question, budget):
        calls.append((question, type(budget).__name__))
        return "42", ["added two numbers", "therefore 42"]

    controller.register_executor(ReasoningStrategy.DIRECT, fake_executor)
    result = controller.solve("what is 40 + 2?", "", ResourceBudget())
    assert calls, "executor must actually run"
    assert result.answer == "42"
    assert result.strategy in list(ReasoningStrategy)
    assert 0.0 <= result.confidence <= 1.0
    assert result.reasoning_trace


def test_fallback_controller_honest_with_no_executors():
    from astra_core.legacy.systems.v40 import MetaCognitiveController
    result = MetaCognitiveController().solve("any question")
    assert result.answer is None
    assert result.confidence == 0.0
    assert any("no" in s.lower() for s in result.reasoning_trace)


def test_fallback_budget_and_analysis():
    from astra_core.legacy.systems.v40 import (
        MetaCognitiveController, ResourceBudget,
    )
    budget = ResourceBudget(max_llm_calls=5)
    assert budget.remaining_llm_calls() == 5
    chars = MetaCognitiveController().analyze_problem("why do stars fuse hydrogen?", "Astronomy")
    assert chars.is_causal
    assert chars.domain == "Astronomy"


def test_v40_system_module_imports():
    from astra_core.legacy.systems.v40 import v40_system  # noqa: F401
    assert v40_system.V40CompleteSystem is not None


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
