"""Tests for the structured per-candidate verdict log.

The supervisor runs ``run_claim_search`` as a subprocess with stdout/stderr ->
DEVNULL, so without an explicit file write the gate verdicts are lost. These
tests pin the observability helper: it records gate outcomes to JSONL and is
defensive (never raises), so logging cannot break the discovery loop.

Run: python3 astra_core/tests/test_verdict_logging.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import astra_core.scientific_discovery.evolved_analysis.run_claim_search as rcs  # noqa: E402


def _sample_verdict(both_pass=False, gate1_pass=True):
    return {
        "claim": "A test claim about galaxy colors and redshift.",
        "program_hash": "abc123",
        "gate1": {"pass": gate1_pass, "reason": "gate1-pass: |effect|=0.5",
                  "metrics": {"effect": 0.5, "pvalue": 1e-9},
                  "bonferroni_pmax": 1e-5, "family_size": 60},
        "triviality": {"pass": True, "reason": "ok"},
        "consistency": {"pass": True, "reason": "ok"},
        "holdout": {"pass": True, "reason": "ok"},
        "gate2": {"pass": False, "status": "known", "n_retrieved": 5,
                  "reasoning": "textbook color-redshift relation"},
        "both_pass": both_pass,
    }


def _run_on_temp_log(verdict, label=""):
    """Call _append_verdict_log with VERDICT_LOG redirected to a temp file."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    orig = rcs.VERDICT_LOG
    rcs.VERDICT_LOG = Path(path)
    try:
        rcs._append_verdict_log(verdict, label=label)
        lines = Path(path).read_text().splitlines()
    finally:
        rcs.VERDICT_LOG = orig
        try:
            Path(path).unlink()
        except OSError:
            pass
    return lines


def test_appends_one_jsonl_line_with_gate_outcomes():
    lines = _run_on_temp_log(_sample_verdict(), label="step0")
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["label"] == "step0"
    assert rec["both_pass"] is False
    assert rec["gate1"]["pass"] is True
    assert rec["gate1"]["effect"] == 0.5
    assert rec["gate2"]["status"] == "known"
    assert rec["triviality"] is True
    assert rec["holdout"] is True
    assert rec["program_hash"] == "abc123"


def test_appends_multiple_lines_in_order():
    lines = _run_on_temp_log(_sample_verdict(), label="a")
    # second append on the SAME temp log requires keeping the path; redo inline
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    orig = rcs.VERDICT_LOG
    rcs.VERDICT_LOG = Path(path)
    try:
        rcs._append_verdict_log(_sample_verdict(), label="a")
        rcs._append_verdict_log(_sample_verdict(both_pass=True), label="b")
        lines = Path(path).read_text().splitlines()
    finally:
        rcs.VERDICT_LOG = orig
        try:
            Path(path).unlink()
        except OSError:
            pass
    assert len(lines) == 2
    assert json.loads(lines[0])["label"] == "a"
    assert json.loads(lines[1])["both_pass"] is True


def test_does_not_raise_on_pathological_verdict():
    # Garbage input must degrade gracefully, not crash the loop.
    lines = _run_on_temp_log({}, label="x")
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["both_pass"] is None          # missing -> None, not a crash
    assert rec["gate1"]["pass"] is None


def test_does_not_raise_when_log_unwritable():
    # An unwritable log destination must not raise (defensive contract).
    orig = rcs.VERDICT_LOG
    rcs.VERDICT_LOG = Path("/nonexistent_root_dir_xyz/sub.jsonl")
    try:
        rcs._append_verdict_log(_sample_verdict(), label="z")  # must not raise
    finally:
        rcs.VERDICT_LOG = orig


# --------------------------------------------------------------------------- #
# Promotion-outcome projection (F1/F3(a), 2026-09-08): the log line records    #
# what actually happened at the chokepoint, not just the gate verdicts.        #
# --------------------------------------------------------------------------- #
def test_projects_emission_outcome_and_attacker():
    v = _sample_verdict(both_pass=True)
    v["emitted"] = False
    v["emit_reason"] = "attacker-killed"
    v["fresh_attacker"] = {"disposition": "killed",
                           "detail": "permutation null kills it " + "x" * 300}
    lines = _run_on_temp_log(v, label="step1")
    rec = json.loads(lines[0])
    assert rec["emitted"] is False
    assert rec["emit_reason"] == "attacker-killed"
    fa = rec["fresh_attacker"]
    assert fa["disposition"] == "killed"
    assert len(fa["detail"]) <= 160          # truncated, bounded payload


def test_projects_second_judge_outcome():
    v = _sample_verdict(both_pass=True)
    v["emitted"] = True
    v["emit_reason"] = None
    v["fresh_attacker"] = {"disposition": "survived", "detail": "ok"}
    v["second_judge"] = {"status": "not-configured", "block": False, "model": None,
                         "n_retrieved": 0, "confidence": None,
                         "reasoning": "set ASTRA_JUDGE2_* to enable"}
    lines = _run_on_temp_log(v, label="step2")
    rec = json.loads(lines[0])
    assert rec["emitted"] is True and rec["emit_reason"] is None
    sj = rec["second_judge"]
    assert sj["status"] == "not-configured"
    assert sj["model"] is None and sj["confidence"] is None


def test_projects_gate_provenance_fields():
    v = _sample_verdict(both_pass=False)
    v["gate2"]["from_cache"] = True
    lines = _run_on_temp_log(v, label="step3")
    rec = json.loads(lines[0])
    assert rec["gate1"]["pmax"] == 1e-5
    assert rec["gate1"]["family_size"] == 60
    assert rec["gate2"]["from_cache"] is True


def test_null_degradation_on_pre_emit_rows():
    """Rows from paths that never reach _emit (the seed row, log-only replays)
    carry explicit nulls, not garbage — and never crash the projection."""
    lines = _run_on_temp_log(_sample_verdict(), label="seed")
    rec = json.loads(lines[0])
    assert rec["emitted"] is None
    assert rec["emit_reason"] is None
    assert rec["fresh_attacker"] == {"disposition": None, "detail": ""}
    assert rec["second_judge"]["status"] is None


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as e:
                failed += 1
                print(f"FAIL  {name}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)
