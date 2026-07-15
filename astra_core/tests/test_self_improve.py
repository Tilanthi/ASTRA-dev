"""Tests for the self-improvement layer: predict/surprise (#1), measured RSI loop
(#2), capability index (#3). Fixture-based, no network.

Run: python3 astra_core/tests/test_self_improve.py
"""
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import (  # noqa: E402
    predictions, capability_index, improvement_loop)


def _redirect(tmpdir):
    """Point all the layer's file paths at a temp dir; return the paths set."""
    p = Path(tmpdir)
    p.mkdir(parents=True, exist_ok=True)
    preds = {
        predictions: {"VERDICT_LOG": p / "v.jsonl", "PREDICTIONS": p / "pred.jsonl",
                      "SURPRISE_LEDGER": p / "surp.jsonl"},
        capability_index: {"CI_HISTORY": p / "ci.jsonl",
                           "RSI_EFFECTIVENESS": p / "rsi_effectiveness.txt"},
        improvement_loop: {"VERDICT_LOG": p / "v.jsonl", "PROPOSALS": p / "prop.jsonl",
                           "APPLIED": p / "applied.jsonl",
                           "EFFECTIVENESS": p / "rsi_effectiveness.txt"},
    }
    saved = {}
    for mod, kv in preds.items():
        for k, v in kv.items():
            saved[(mod, k)] = getattr(mod, k)
            setattr(mod, k, v)
    return saved


def _restore(saved):
    for (mod, k), v in saved.items():
        setattr(mod, k, v)


def _v(dataset, label, ts, g1pass=True, hold=True, triv=True, cons=True,
       g2status=None, both=False, effect=0.5):
    return {"ts": ts, "dataset": dataset, "label": label, "claim": "c",
            "program_hash": "h" + ts[-5:],
            "gate1": {"pass": g1pass, "reason": "r", "metrics": {"effect": effect}},
            "triviality": triv, "consistency": cons, "holdout": hold,
            "gate2": ({"status": g2status} if g2status else None),
            "both_pass": both}


FIXTURE = [
    # before the fix (df_eval era): seed + 4 holdout_block + 1 gate2_known
    _v("sdss_galaxy_extended", "seed", "2026-07-14T11:00:00"),
    _v("sdss_galaxy_extended", "step0", "2026-07-14T11:00:10", hold=False),
    _v("sdss_galaxy_extended", "step1", "2026-07-14T11:00:20", hold=False),
    _v("sdss_galaxy_extended", "step2", "2026-07-14T11:00:30", hold=False),
    _v("sdss_galaxy_extended", "step3", "2026-07-14T11:00:40", hold=False),
    _v("sdss_galaxy_extended", "step4", "2026-07-14T11:00:50", g2status="known"),
    # after the fix: seed + 2 holdout_block + 2 novel_emit + 1 gate1_fail
    _v("sdss_galaxy_extended", "seed", "2026-07-15T10:00:00"),
    _v("sdss_galaxy_extended", "step0", "2026-07-15T10:00:10", hold=False),
    _v("sdss_galaxy_extended", "step1", "2026-07-15T10:00:20", hold=False),
    _v("sdss_galaxy_extended", "step2", "2026-07-15T10:00:30", both=True),
    _v("sdss_galaxy_extended", "step3", "2026-07-15T10:00:40", both=True),
    _v("sdss_galaxy_extended", "step4", "2026-07-15T10:00:50", g1pass=False),
]


def _write_fixture():
    predictions.VERDICT_LOG.write_text(
        "\n".join(json.dumps(v) for v in FIXTURE) + "\n")


def test_failure_class_covers_all_outcomes():
    assert improvement_loop.failure_class(_v("d", "s", "t", both=True)) == "novel_emit"
    assert improvement_loop.failure_class(_v("d", "s", "t", g1pass=False)) == "gate1_fail"
    assert improvement_loop.failure_class(_v("d", "s", "t", hold=False)) == "holdout_block"
    assert improvement_loop.failure_class(_v("d", "s", "t", triv=False)) == "triviality_block"
    assert improvement_loop.failure_class(_v("d", "s", "t", cons=False)) == "consistency_block"
    assert improvement_loop.failure_class(_v("d", "s", "t", g2status="known")) == "gate2_known"
    assert improvement_loop.failure_class(
        _v("d", "s", "t", g2status="retrieval-failed")) == "gate2_retrieval_failed"


def test_mine_and_propose():
    with tempfile.TemporaryDirectory() as td:
        saved = _redirect(td)
        try:
            _write_fixture()
            clusters = improvement_loop.mine_failures(min_count=3)
            classes = {(c["dataset"], c["failure_class"]) for c in clusters}
            assert ("sdss_galaxy_extended", "holdout_block") in classes  # 6 total
            assert all(c["count"] >= 3 for c in clusters)
            props = improvement_loop.propose_fixes(clusters)
            assert props and all("proposal" in p and p["needs_approval"] for p in props)
            assert any(p["failure_class"] == "holdout_block" for p in props)
        finally:
            _restore(saved)


def test_predict_actuals_surprise():
    with tempfile.TemporaryDirectory() as td:
        saved = _redirect(td)
        try:
            _write_fixture()
            pred = predictions.predict_for_episode("sdss_galaxy_extended")
            assert pred.dataset == "sdss_galaxy_extended"
            assert 0.0 <= pred.confidence <= 1.0
            assert 0.0 <= pred.p_novel <= 1.0   # Beta-posterior forecast
            # actuals for the post-10:00 episode
            act = predictions.episode_actuals("sdss_galaxy_extended", "2026-07-15T10:00:00")
            assert act["n"] == 6  # seed + 5 steps
            b = predictions.brier(pred.p_novel, predictions.episode_outcome(act))
            assert 0.0 <= b <= 1.0
            # a "no data" actual -> max surprise contribution
            act_empty = {"gate1_pass_rate": None, "novel_emits": 0}
            assert predictions.score_surprise(pred, act_empty) >= 0.6
            # a perfectly-matched actual (low surprise) vs confidence
            matched = {"gate1_pass_rate": pred.predicted_gate1_pass_rate,
                       "novel_emits": pred.predicted_novel_emits}
            s_match = predictions.score_surprise(pred, matched)
            assert 0.0 <= s_match <= 1.0
        finally:
            _restore(saved)


def test_measure_effectiveness_drops_after_fix():
    with tempfile.TemporaryDirectory() as td:
        saved = _redirect(td)
        try:
            _write_fixture()
            # the split-discipline fix was applied between the two episodes
            improvement_loop.APPLIED.write_text(json.dumps({
                "id": "P001", "failure_class": "holdout_block",
                "dataset": "sdss_galaxy_extended",
                "date_applied": "2026-07-14T18:00:00"}) + "\n")
            res = improvement_loop.measure_effectiveness()
            assert res is not None
            fix = res["per_fix"][0]
            assert fix["failure_class"] == "holdout_block"
            assert fix["rate_before"] > fix["rate_after"]   # fix worked
            assert fix["effectiveness"] > 0.0
            assert capability_index.RSI_EFFECTIVENESS.exists()  # roll-up written
        finally:
            _restore(saved)


def test_compute_ci_degrades_and_blends():
    with tempfile.TemporaryDirectory() as td:
        saved = _redirect(td)
        try:
            _write_fixture()
            # no surprise ledger yet -> calibration/learning absent, renormalised
            ci = capability_index.compute_ci()
            assert ci["ci"] is not None
            assert ci["calibration"] is None and ci["learning"] is None
            assert ci["execution"] is not None and ci["breadth"] is not None
            # add a surprise ledger entry + RSI effectiveness -> learning appears
            predictions.SURPRISE_LEDGER.write_text(json.dumps(
                {"ts": "2026-07-15T10:01:00", "dataset": "sdss_galaxy_extended",
                 "p_novel": 0.4, "outcome": 0, "brier": 0.16, "surprise": 0.3}) + "\n")
            capability_index.RSI_EFFECTIVENESS.write_text("72.5")
            ci2 = capability_index.compute_ci()
            assert ci2["calibration"] is not None      # Brier 0.16 -> 100*(1-0.32)=68
            assert ci2["learning"] is not None          # blended with RSI effectiveness
            assert ci2["discovery"] is not None         # outcome sub-score present
            assert ci2["rsi_effectiveness_blended"] == 72.5
        finally:
            _restore(saved)


def test_brier_and_reliability():
    with tempfile.TemporaryDirectory() as td:
        saved = _redirect(td)
        try:
            entries = [
                {"ts": "t1", "dataset": "d", "p_novel": 0.0, "outcome": 0, "brier": 0.0},
                {"ts": "t2", "dataset": "d", "p_novel": 1.0, "outcome": 1, "brier": 0.0},
                {"ts": "t3", "dataset": "d", "p_novel": 0.5, "outcome": 1, "brier": 0.25},
                {"ts": "t4", "dataset": "d", "p_novel": 0.5, "outcome": 0, "brier": 0.25},
            ]
            predictions.SURPRISE_LEDGER.write_text(
                "\n".join(json.dumps(e) for e in entries) + "\n")
            cm = predictions.calibration_metrics()
            assert cm["mean_brier"] == 0.125               # (0+0+0.25+0.25)/4
            curve = predictions.calibration_curve(bins=5)
            assert isinstance(curve, list) and len(curve) >= 1
        finally:
            _restore(saved)


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(_run())
