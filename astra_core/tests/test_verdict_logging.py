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
