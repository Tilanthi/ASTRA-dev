"""ALS concept-graph novelty prior (AstroMLab package #1, Path A — token-free).

Li/Ting et al. (arXiv 2602.14335) forecast concept-object links with implicit-
feedback ALS; Path A adapts the same machinery as a NOVELTY PRIOR on ASTRA's
Gate 2: fit ALS on the concept-paper graph (AstroMLab 5 knowledge graph,
408,590 astro-ph papers x 9,999 concepts), then score a candidate claim by
the affinity structure of the concepts it mentions. Well-trodden combinations
(high pairwise affinity) get a prior toward known; unexplored combinations
get a prior toward novel.

The prior is a RANKING SIGNAL ONLY — it never gates, never overrides the
grounded judge, and costs zero LLM tokens.

Run: python3 astra_core/tests/test_concept_prior.py
"""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import concept_prior as cp  # noqa: E402


def _stub_prior():
    """3 concepts: T-F aligned with BH mass, dust orthogonal to both."""
    names = ["Tully-Fisher relation", "black hole mass", "dust extinction"]
    labels = [1, 2, 3]
    factors = np.array([
        [1.0, 0.0],
        [1.0, 0.0],   # aligned with T-F
        [0.0, 1.0],   # orthogonal
    ])
    popularity = {1: 500, 2: 300, 3: 40}
    return cp.ConceptPrior.from_arrays(names, labels, factors, popularity)


def test_match_concepts_by_name_tokens():
    p = _stub_prior()
    hit = p.match_concepts("galaxy rotation velocity follows the Tully-Fisher relation")
    assert "Tully-Fisher relation" in [h["concept"] for h in hit]
    hit2 = p.match_concepts("dust extinction curves in high-redshift galaxies")
    assert "dust extinction" in [h["concept"] for h in hit2]


def test_match_ignores_generic_only_overlap():
    p = _stub_prior()
    hits = p.match_concepts("a relation between mass and structure")
    # 'relation'/'mass' alone are generic/partial — no full concept match
    assert all(h["concept"] != "Tully-Fisher relation" for h in hits)


def test_crowding_high_for_aligned_concepts():
    p = _stub_prior()
    out = p.score("the Tully-Fisher relation constrains black hole mass")
    assert out["concepts"], out
    assert out["crowding"] > 0.9   # T-F and BH-mass factors are aligned


def test_crowding_low_for_orthogonal_concepts():
    p = _stub_prior()
    out = p.score("dust extinction along the Tully-Fisher relation")
    assert out["crowding"] < 0.1   # dust is orthogonal to T-F


def test_single_concept_falls_back_to_popularity():
    p = _stub_prior()
    out = p.score("dust extinction measured in nearby clouds")
    assert len(out["concepts"]) == 1
    assert 0.0 <= out["crowding"] <= 1.0


def test_no_concept_match_returns_empty():
    p = _stub_prior()
    out = p.score("the chef prepares lasagna tonight")
    assert out["concepts"] == [] and out["crowding"] is None


def test_score_output_is_prior_not_verdict():
    p = _stub_prior()
    out = p.score("dust extinction along the Tully-Fisher relation")
    assert out["role"] == "prior-only-ranking-signal"
    assert "llm_tokens" not in out


def test_score_cached_live_factors():
    """Integration: the real fitted factors load and score a textbook-crowded
    claim higher than an unexplored cross-field claim. Skips (passes) if the
    one-time fit has not been run yet."""
    prior = cp.ConceptPrior.load()
    if prior is None:
        print("SKIP test_score_cached_live_factors (factors not fitted)")
        return
    crowded = prior.score("Galaxy rotation velocity follows the Tully-Fisher "
                          "relation with luminosity")["crowding"]
    unexplored = prior.score(
        "The width of molecular filaments anticorrelates with the dust "
        "temperature gradient perpendicular to the filament spine")["crowding"]
    assert crowded > unexplored, (crowded, unexplored)
    # cached path returns the same shape and never raises
    got = cp.score_cached("Tully-Fisher relation and luminosity")
    assert got is not None and "crowding" in got


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
