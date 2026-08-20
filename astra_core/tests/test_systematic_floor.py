"""Systematic-floor gate + judge confidence elicitation (AstroMLab package #6).

Egent (arXiv 2512.01270) measured propagated uncertainties under-calibrated by
2-3x in the low-sigma regime and recommended a systematic floor in quadrature.
ASTRA's gate-1 is an absolute-effect + p-value gate; the floor lands as a
per-dataset additive effect floor (a spurious-correlation level the effect must
clear), with a registry so floors are named and revisable, never invented.

Run: python3 astra_core/tests/test_systematic_floor.py
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis.systematic_floor import (  # noqa: E402
    effect_floor, SYSTEMATIC_FLOORS,
)
from astra_core.scientific_discovery.evolved_analysis.claim_task import (  # noqa: E402
    gate1_significant,
)


def test_registry_names_datasets_and_reasons():
    for dataset, spec in SYSTEMATIC_FLOORS.items():
        assert isinstance(spec["floor"], float) and spec["floor"] >= 0
        assert spec["reason"], dataset


def test_known_dataset_has_floor():
    assert effect_floor("legacy") > 0.0


def test_unknown_dataset_defaults_to_no_floor():
    assert effect_floor("never-heard-of") == 0.0


def test_gate1_respects_floor():
    # effect 0.305 clears the raw bar (0.30) but sits below the legacy bar
    # (0.30 + 0.01 floor)
    ok, reason = gate1_significant({"effect": 0.305, "pvalue": 1e-9},
                                   dataset="legacy")
    assert not ok and "systematic floor" in reason


def test_gate1_floor_absent_passes():
    ok, reason = gate1_significant({"effect": 0.305, "pvalue": 1e-9},
                                   dataset="clean-sim")
    assert ok, reason


def test_judge_confidence_parsed_from_verdict():
    from astra_core.scientific_discovery.evolved_analysis.novelty_gate import (
        _parse_judge_text)
    conf, verdict = _parse_judge_text(
        '{"known": true, "reason": "entailed", "by_abstract": 0, '
        '"confidence": 0.85, "reasoning": "direct"}')
    assert verdict["known"] is True and conf == 0.85


def test_judge_confidence_missing_is_none():
    from astra_core.scientific_discovery.evolved_analysis.novelty_gate import (
        _parse_judge_text)
    conf, verdict = _parse_judge_text('{"known": false, "reason": "novel"}')
    assert conf is None and verdict["known"] is False


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
