"""Pre-check feature logging for the novelty judge (tiered-escalation arm).

Calibration on 4,103 cached verdicts (2026-08-20) showed NO safe deterministic
auto-known tier: claim-to-abstract similarity covers 0.1% of calls at tau=0.80;
token containment covers ~0%; reusing a >=0.9-similar prior claim's verdict is
only 55% accurate. The auto-known tier therefore defaults OFF and what ships is
the measurement: every judge call logs its cheap-signal features alongside the
verdict, so any future tier's precision/recall is measured, not assumed.

Run: python3 astra_core/tests/test_novelty_precheck.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import novelty_precheck  # noqa: E402


def _papers():
    return [
        {"title": "Tully-Fisher in local galaxies", "abstract": "We measure the "
         "Tully-Fisher relation for rotation and velocity in nearby galaxies "
         "using HI line widths across a sample of spiral disks."},
        {"title": "Unrelated quasar study", "abstract": "Quasar variability at "
         "high redshift over ten years of monitoring."},
    ]


def test_similarity_features_rank_matching_paper_first():
    f = novelty_precheck.precheck_features(
        "The Tully-Fisher relation links rotation velocity to luminosity in "
        "spiral galaxies", _papers())
    assert 0.0 < f["top_similarity"] <= 1.0
    assert f["top_similarity_idx"] == 0


def test_containment_fraction_bounds():
    f = novelty_precheck.precheck_features(
        "quasar variability monitoring", _papers())
    assert 0.0 <= f["containment"] <= 1.0


def test_auto_known_disabled_by_default():
    assert not novelty_precheck.should_auto_known({"top_similarity": 0.99,
                                                   "containment": 1.0})


def test_auto_known_only_when_tau_configured():
    os.environ["ASTRA_NOVELTY_AUTOKNOWN_TAU"] = "0.80"
    try:
        assert novelty_precheck.should_auto_known({"top_similarity": 0.99,
                                                   "containment": 0.1})
        assert not novelty_precheck.should_auto_known({"top_similarity": 0.5,
                                                       "containment": 0.1})
    finally:
        del os.environ["ASTRA_NOVELTY_AUTOKNOWN_TAU"]


def test_log_precheck_appends_verdict_row():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "precheck.jsonl"
        novelty_precheck.log_precheck({"top_similarity": 0.61, "containment": 0.2},
                                      "known", path=path)
        novelty_precheck.log_precheck({"top_similarity": 0.42, "containment": 0.05},
                                      "novel", path=path)
        rows = [json.loads(x) for x in path.read_text().splitlines()]
        assert rows[0]["verdict"] == "known" and rows[0]["top_similarity"] == 0.61
        assert rows[1]["verdict"] == "novel"


def test_check_novelty_logs_precheck_and_honors_armed_tier():
    """Integration: check_novelty computes features, logs them with the
    verdict, and (only when a tau is armed) skips the LLM on high similarity."""
    from astra_core.scientific_discovery.evolved_analysis import novelty_gate as ng

    papers = [ng.Paper(source="arxiv", title="Tully-Fisher in local galaxies",
                       abstract="We measure the Tully-Fisher relation for "
                       "rotation velocity and luminosity in spiral galaxies.",
                       identifier="x", year="2019")]
    with tempfile.TemporaryDirectory() as d:
        log_path = Path(d) / "precheck.jsonl"
        ng.CACHE_PATH = Path(d) / "novelty_cache.json"
        ng._retrieve_papers = lambda q, s2, max_results=5: papers
        calls = []
        ng._judge_known = lambda c, ps: (calls.append(c) or
                                         (True, ps[0], "entailed", "match", 0.9))
        import astra_core.scientific_discovery.evolved_analysis.novelty_precheck as pc
        pc.PRECHECK_PATH = log_path
        # unarmed: LLM judge runs, row logged with verdict
        r1 = ng.check_novelty("rotation velocity predicts luminosity in spiral "
                              "galaxies", force=True)
        assert r1.status == "known" and len(calls) == 1
        rows = [json.loads(x) for x in log_path.read_text().splitlines()]
        assert rows[-1]["verdict"] == "known" and rows[-1]["top_similarity"] > 0
        # armed at a trivial tau: same claim short-circuits without the LLM
        os.environ["ASTRA_NOVELTY_AUTOKNOWN_TAU"] = "0.05"
        try:
            ng.check_novelty("rotation velocity predicts luminosity in spiral "
                             "galaxies", force=True)
            assert len(calls) == 1  # no second judge call
            rows = [json.loads(x) for x in log_path.read_text().splitlines()]
            assert rows[-1]["verdict"] == "known-auto"
        finally:
            del os.environ["ASTRA_NOVELTY_AUTOKNOWN_TAU"]


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")


