"""Drift canary for the novelty judge (AstroMLab package #7).

AstroMLab's cut-off/exam-date discipline: when the underlying model changes,
you must re-validate the judge, not assume behaviour carried over. The canary
freezes (claim, synthetic abstract) pairs — synthetic fixtures for judge
calibration ONLY, never discovery inputs — runs them through the exact judge
prompt+parse path, and compares verdicts against a pinned baseline. Verdict
disagreement above threshold on identical inputs = drift alarm.

Run: python3 astra_core/tests/test_drift_canary.py
"""
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import drift_canary as dc  # noqa: E402


def _stable_judge(claim, papers):
    """Deterministic stub: first fixture claim is 'known', others 'novel'."""
    if papers and "Hubble" in papers[0].title:
        return True, papers[0], "entailed", "stub match", 0.9
    return False, None, "novel", "stub no-match", 0.8


def test_canary_cases_are_frozen_and_labeled():
    cases = dc.canary_cases()
    assert len(cases) >= 5
    for c in cases:
        assert c["id"] and c["claim"] and len(c["abstracts"]) >= 2
    assert "calibration" in dc.__doc__  # fixtures labeled non-discovery


def test_run_canary_uses_injected_judge():
    verdicts = dc.run_canary(judge=_stable_judge)
    assert len(verdicts) == len(dc.canary_cases())
    assert all("known" in v and "label" in v for v in verdicts)


def test_compare_detects_drift():
    cases = dc.canary_cases()
    baseline = [{"id": c["id"], "known": False, "label": "novel",
                 "confidence": 0.9} for c in cases]
    same = [dict(b) for b in baseline]
    assert dc.compare(baseline, same)["drift"] is False
    flipped = [dict(b, known=not b["known"]) for b in baseline]
    res = dc.compare(baseline, flipped)
    assert res["drift"] is True and res["agreement"] == 0.0
    partial = [dict(b) for b in baseline]
    partial[0]["known"] = not partial[0]["known"]
    assert dc.compare(baseline, partial)["agreement"] == round(
        (len(baseline) - 1) / len(baseline), 3)


def test_pin_and_check_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "baseline.json"
        dc.pin_baseline(path, judge=_stable_judge, model="stub-m1")
        pinned = json.loads(path.read_text())
        assert pinned["model"] == "stub-m1"
        assert len(pinned["verdicts"]) == len(dc.canary_cases())
        res = dc.check_drift(path, judge=_stable_judge, model="stub-m1")
        assert res["agreement"] == 1.0 and res["drift"] is False


def test_model_swap_is_flagged():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "baseline.json"
        dc.pin_baseline(path, judge=_stable_judge, model="stub-m1")
        res = dc.check_drift(path, judge=_stable_judge, model="stub-m2")
        assert res["model_changed"] is True


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
