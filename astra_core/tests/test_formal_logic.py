"""V40 FormalLogicEngine / PrologEngine restoration tests.

The two classes were imported by 7 v40 modules but never defined anywhere
(found in the 2026-08-21 audit). These tests pin the consumer contract:
FormalLogicEngine() with .z3 and .solve(question) -> (result, LogicalProof),
plus a real forward-chaining PrologEngine that only affirms derivable goals.

Run: python3 astra_core/tests/test_formal_logic.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.legacy.systems.v40.formal_logic import (  # noqa: E402
    FormalLogicEngine, PrologEngine, Z3Solver, LogicalProof, ProofStatus,
)


def test_engine_contract():
    engine = FormalLogicEngine()
    assert isinstance(engine.z3, Z3Solver)
    assert isinstance(engine.prolog, PrologEngine)


def test_solve_undecidable_is_unknown_never_fabricated():
    engine = FormalLogicEngine()
    result, proof = engine.solve("is the continuum hypothesis true")
    assert result is None
    assert isinstance(proof, LogicalProof)
    assert proof.status == ProofStatus.UNKNOWN
    assert proof.steps, "must record why no decision was made"


def test_prolog_forward_chaining_derives_goal():
    p = PrologEngine()
    p.add_fact("parent", "alice", "bob")
    p.add_fact("parent", "bob", "carol")
    p.add_rule(("grandparent", "X", "Z"), [("parent", "X", "Y"), ("parent", "Y", "Z")])
    # ground goal: proved, empty substitution (nothing to bind)
    proved, bindings = p.solve(("grandparent", "alice", "carol"))
    assert proved
    assert bindings == [{}]
    # variable goal: binding for the free variable
    proved, bindings = p.solve(("grandparent", "alice", "Z"))
    assert proved
    assert bindings == [{"Z": "carol"}]


def test_prolog_non_derivable_goal_is_false():
    p = PrologEngine()
    p.add_fact("parent", "alice", "bob")
    proved, bindings = p.solve(("parent", "carol", "dave"))
    assert not proved
    assert bindings == []


def test_engine_solve_uses_prolog_facts():
    engine = FormalLogicEngine()
    engine.prolog.add_fact("parent", "alice", "bob")
    result, proof = engine.solve("parent(alice,bob)")
    assert result is True
    assert proof.status == ProofStatus.VALID
    assert proof.verified
    assert any("parent" in s.statement for s in proof.steps)


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
