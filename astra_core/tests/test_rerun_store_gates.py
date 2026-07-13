"""Tests for rerun_store_gates.classify_record — the retroactive re-gating logic.

Exercises the three classification buckets (KEEP / SURVIVES / QUARANTINE) and each
gate-failure path, with an injected ``gate1_runner`` so no real data or subprocess
is needed. Run: python3 astra_core/tests/test_rerun_store_gates.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis.rerun_store_gates import (  # noqa: E402
    classify_record, KEEP, SURVIVES, QUARANTINE)
from astra_core.scientific_discovery.evolved_analysis.claim_task import PMAX  # noqa: E402

FAMILY = 50
CPMAX = PMAX / FAMILY  # ~2e-5

# A multi-band source whose CLAIM states no correlation magnitude. With a moderate
# injected effect it passes gate1 + triviality + consistency.
SRC_OK = '''CLAIM = "A novel multi-band SDSS photometric relationship predicts redshift."


def run_claim(df_train, df_eval):
    from scipy.stats import spearmanr
    import numpy as np
    df = df_train
    x = df["u"].to_numpy(float) - df["g"].to_numpy(float) - df["r"].to_numpy(float)
    y = df["z_spec"].to_numpy(float)
    r, p = spearmanr(x, y)
    return {"effect": float(r), "pvalue": float(p), "effect_insample": 0.4,
            "pvalue_insample": 1e-8}
'''

# A multi-band source whose CLAIM states rho ~ 0.15 — contradicts a measured 0.5.
SRC_INCONSISTENT = '''CLAIM = "The colour combination shows a weak correlation (rho ~ 0.15) with redshift."


def run_claim(df_train, df_eval):
    from scipy.stats import spearmanr
    df = df_train
    x = df["u"] - df["g"] - df["r"] + df["i"]
    r, p = spearmanr(x, df["z_spec"])
    return {"effect": float(r), "pvalue": float(p)}
'''


def _claim_rec(metric="two_gate_claim", src_hash="h_ok", effect=0.55):
    return {
        "title": "t",
        "abstract": "a",
        "verification": {
            "program_hash": src_hash,
            "metric_name": metric,
            "claim": "placeholder",
            "effect": effect,
            "pvalue": 1e-10,
        },
    }


def _runner(metrics_by_hash):
    """Return a fake gate1_runner that picks metrics by the source's hash."""
    def _run(src, seed):
        # identify which source it is by a marker in the CLAIM text
        if "rho ~ 0.15" in src:
            return metrics_by_hash["inconsistent"]
        return metrics_by_hash["ok"]
    return _run


# --------------------------------------------------------------------------- #
# KEEP — Phase-1 pipeline, out-of-sample, not a claim                          #
# --------------------------------------------------------------------------- #
def test_keep_phase1_pipeline():
    rec = _claim_rec(metric="sigma_NMAD")
    bucket, g, e, reason, gate = classify_record(
        rec, source_map={}, evolved_by_hash={}, family=FAMILY,
        corrected_pmax=CPMAX, gate1_runner=lambda s, n: {})
    assert bucket == KEEP
    assert g is rec                      # unchanged
    assert gate is None
    assert "out-of-sample" in reason


# --------------------------------------------------------------------------- #
# SURVIVES — source present, every gate passes; verification refreshed        #
# --------------------------------------------------------------------------- #
def test_survives_all_gates_pass():
    rec = _claim_rec(src_hash="h_ok")
    source_map = {"h_ok": SRC_OK}
    runner = _runner({"ok": {"effect": 0.55, "pvalue": 1e-12,
                             "effect_insample": 0.6, "pvalue_insample": 1e-9}})
    bucket, g, e, reason, gate = classify_record(
        rec, source_map, evolved_by_hash={}, family=FAMILY,
        corrected_pmax=CPMAX, gate1_runner=runner)
    assert bucket == SURVIVES
    assert gate is None
    v = g["verification"]
    assert v["effect"] == 0.55                                # refreshed from re-run
    assert v["effect_insample"] == 0.6
    assert v["held_out_split"] == "test"
    assert v["gate"]["triviality"] == "pass"
    assert v["gate"]["consistency"] == "pass"
    assert v["gate"]["bonferroni_pmax"] == CPMAX
    assert v["gate"]["family_size"] == FAMILY
    assert "rerun" in v and v["rerun"]["metrics"]["effect"] == 0.55
    assert g["program_source"] == SRC_OK                      # Fix 1: source persisted


# --------------------------------------------------------------------------- #
# QUARANTINE — no recoverable source (the early in-sample-only claims)        #
# --------------------------------------------------------------------------- #
def test_quarantine_no_source():
    rec = _claim_rec()                  # hash "h_ok" absent from source_map
    bucket, g, e, reason, gate = classify_record(
        rec, source_map={}, evolved_by_hash={}, family=FAMILY,
        corrected_pmax=CPMAX, gate1_runner=lambda s, n: {})
    assert bucket == QUARANTINE
    assert gate == "no_source"
    assert g is None and e is None
    assert "unverifiable" in reason


# --------------------------------------------------------------------------- #
# QUARANTINE — triviality failure (near-deterministic |rho|)                  #
# --------------------------------------------------------------------------- #
def test_quarantine_triviality():
    rec = _claim_rec(src_hash="h_ok")
    runner = _runner({"ok": {"effect": 0.991, "pvalue": 1e-30}})
    bucket, g, e, reason, gate = classify_record(
        rec, {"h_ok": SRC_OK}, {}, FAMILY, CPMAX, runner)
    assert bucket == QUARANTINE
    assert gate == "triviality"
    assert "near-deterministic" in reason or "trivial" in reason


# --------------------------------------------------------------------------- #
# QUARANTINE — consistency failure (narrated rho contradicts measured)        #
# --------------------------------------------------------------------------- #
def test_quarantine_consistency():
    rec = _claim_rec(src_hash="h_inc")
    runner = _runner({"inconsistent": {"effect": 0.5, "pvalue": 1e-10}})
    bucket, g, e, reason, gate = classify_record(
        rec, {"h_inc": SRC_INCONSISTENT}, {}, FAMILY, CPMAX, runner)
    assert bucket == QUARANTINE
    assert gate == "consistency"
    assert "contradict" in reason or "consistency" in reason


# --------------------------------------------------------------------------- #
# QUARANTINE — Gate-1 failure (weak / non-significant effect)                 #
# --------------------------------------------------------------------------- #
def test_quarantine_gate1_weak():
    rec = _claim_rec(src_hash="h_ok")
    runner = _runner({"ok": {"effect": 0.10, "pvalue": 0.5}})
    bucket, g, e, reason, gate = classify_record(
        rec, {"h_ok": SRC_OK}, {}, FAMILY, CPMAX, runner)
    assert bucket == QUARANTINE
    assert gate == "gate1"
    assert "gate1-failed" in reason


# --------------------------------------------------------------------------- #
# QUARANTINE — holdout not distinct (run_claim ignored df_train)  [Fix 6]     #
# --------------------------------------------------------------------------- #
def test_quarantine_holdout_indistinguishable():
    """effect == effect_insample to float precision means run_claim computed on
    df_eval for both calls — the 'test' split was never used. Must quarantine."""
    rec = _claim_rec(src_hash="h_ok")

    def runner(src, seed):
        return {"effect": 0.55, "pvalue": 1e-12,
                "effect_insample": 0.55, "pvalue_insample": 1e-12}

    bucket, g, e, reason, gate = classify_record(
        rec, {"h_ok": SRC_OK}, {}, FAMILY, CPMAX, runner)
    assert bucket == QUARANTINE
    assert gate == "holdout"
    assert "ignores df_train" in reason or "not genuine" in reason


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
