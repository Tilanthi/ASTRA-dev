"""Noise-aware effectiveness verdicts + negative-impact flagging for the RSI
improvement loop (Mephisto lesson).

measure_effectiveness() used a raw before/after rate ratio clamped at zero —
a fix that made its failure class WORSE scored 0, indistinguishable from no
data, and nothing flagged it for retirement. Mephisto's lifecycle rule: only
keep knowledge that demonstrably helps on held-out data; drop (flag for
human removal) what measures negative.

Run: python3 astra_core/tests/test_knowledge_lifecycle.py
"""
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import improvement_loop as il  # noqa: E402


def _setup(tmp, applied, verdicts):
    il.APPLIED = Path(tmp) / "rsi_applied.jsonl"
    il.EFFECTIVENESS = Path(tmp) / "rsi_effectiveness.txt"
    il.VERDICT_LOG = Path(tmp) / "claim_verdicts.jsonl"
    il.APPLIED.write_text("".join(json.dumps(a) + "\n" for a in applied))
    il.VERDICT_LOG.write_text("".join(json.dumps(v) + "\n" for v in verdicts))


def _verdicts(rate_by_half, n=100, cls="gate1_fail"):
    """n verdicts; first half before cut, second half after; per-half rate."""
    out = []
    for half, rate in enumerate(rate_by_half):
        n_fail = int(rate * n // 2)
        for i in range(n // 2):
            v = {"ts": f"2026-08-{1 + half:02d}T12:00:00",
                 "dataset": "ds", "gate1": {"pass": i >= n_fail}}
            out.append(v)
    return out


def test_improved_fix_gets_improved_verdict():
    with tempfile.TemporaryDirectory() as d:
        _setup(d, [{"id": "F1", "failure_class": "gate1_fail",
                    "date_applied": "2026-08-01T18:00:00"}],
               _verdicts([0.8, 0.2]))
        res = il.measure_effectiveness()
        v = res["per_fix"][0]
        assert v["verdict"] == "improved", v
        assert "negative_impact" not in json.loads(
            il.APPLIED.read_text().splitlines()[0])


def test_worsened_fix_flagged_negative_impact():
    with tempfile.TemporaryDirectory() as d:
        _setup(d, [{"id": "F2", "failure_class": "gate1_fail",
                    "date_applied": "2026-08-01T18:00:00"}],
               _verdicts([0.2, 0.8]))
        res = il.measure_effectiveness()
        assert res["per_fix"][0]["verdict"] == "worsened"
        entry = json.loads(il.APPLIED.read_text().splitlines()[0])
        assert entry.get("negative_impact") is True


def test_tiny_sample_is_underpowered_not_worsened():
    with tempfile.TemporaryDirectory() as d:
        _setup(d, [{"id": "F3", "failure_class": "gate1_fail",
                    "date_applied": "2026-08-01T18:00:00"}],
               _verdicts([0.2, 0.8], n=20))
        res = il.measure_effectiveness()
        assert res["per_fix"][0]["verdict"] == "underpowered"


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
