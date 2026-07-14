"""Tests for the literature action-space miner (Sub-project C). No network —
tests the rule-based extractor, the suggester, and a mocked LLM pass.

Run: python3 astra_core/tests/test_action_space_miner.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis.action_space_miner import (  # noqa: E402
    extract_dataset_mentions, suggest_datasets, extract_via_llm,
)


def test_extract_mentions_counts_known_surveys():
    abstracts = [
        "We use SDSS and Gaia data to study stars. The SDSS sample is large.",
        "TESS light curves reveal exoplanets. LSST will follow up shortly.",
        "An abstract about a topic with no survey mentioned at all.",
    ]
    mentions = {m["dataset"]: m["count"] for m in extract_dataset_mentions(abstracts)}
    assert mentions.get("SDSS") == 2
    assert mentions.get("Gaia") == 1
    assert mentions.get("TESS") == 1
    assert mentions.get("LSST/Rubin") == 1


def test_suggest_excludes_already_registered():
    mentions = [{"dataset": "SDSS", "count": 5}, {"dataset": "Euclid", "count": 2}]
    suggestions = suggest_datasets(mentions, have=["sdss", "gaia_nearby"])
    assert "Euclid" in suggestions
    assert "SDSS" not in suggestions  # already registered (case-insensitive)


def test_extract_via_llm_parses_json_list():
    def fake_complete(system, user):
        return ' [{"dataset":"DESI","analysis":"BAO","method":"clustering"}] '
    items = extract_via_llm(["some abstract"], llm_complete=fake_complete)
    assert items == [{"dataset": "DESI", "analysis": "BAO", "method": "clustering"}]


def test_extract_via_llm_no_callable_returns_empty():
    assert extract_via_llm(["abs"], llm_complete=None) == []


def test_extract_via_llm_bad_response_returns_empty():
    def bad(system, user):
        return "this response has no JSON list"
    assert extract_via_llm(["abs"], llm_complete=bad) == []


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
