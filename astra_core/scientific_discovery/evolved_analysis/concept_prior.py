#!/usr/bin/env python3
"""concept_prior.py — ALS concept-graph novelty prior (token-free, Path A).

AstroMLab package #1, Path A. Li/Ting et al. (arXiv 2602.14335) forecast
concept-object associations with implicit-feedback ALS; this module adapts
the same machinery as a NOVELTY PRIOR for Gate 2:

  1. Fit ALS (d=128, alpha=10, lambda=0.05, 30 iterations) on the concept-
     paper graph of the AstroMLab 5 knowledge graph (408,590 astro-ph papers,
     9,999 concepts; tingyuansen/astro-ph_knowledge_graph).
  2. For a candidate claim, match its text to concept names in the
     vocabulary and read off the pairwise affinity of the matched concepts'
     ALS factors.
  3. ``crowding`` = mean pairwise cosine affinity: well-trodden combinations
     (concepts that co-occur across the literature) score high -> prior
     toward KNOWN; unexplored combinations score low -> prior toward NOVEL.

THE PRIOR NEVER GATES. It is recorded beside verdicts as a ranking signal
only — the grounded judge (retrieval + entailment) remains the sole Gate-2
authority, per ASTRA's conservative-gate principles. Cost: zero LLM tokens.

Validation (2026-08-20, real factors): separates the extremes — an
unexplored cross-field claim (filament width x dust-temperature gradient)
scores 0.048 while crowded fields (globular-cluster pulsars, Tully-Fisher)
score 0.30-0.45. Known limitation: same-family concepts (three
'globular cluster' variants) inflate crowding — the prior measures FIELD
crowding, not whether a specific relation is studied; specific-relation
novelty inside a crowded field remains the grounded judge's job.

CLI:
    PYTHONPATH=. python3 -m astra_core.scientific_discovery.evolved_analysis.concept_prior fit
    PYTHONPATH=. python3 -m astra_core.scientific_discovery.evolved_analysis.concept_prior score "<claim>"

Data (one-time download, ~17 MB):
    ~/.astra_persistent/concept_graph/{papers_concepts_mapping.csv.gz,
                                       concepts_vocabulary.csv.gz}
Trained factors: ~/.astra_persistent/concept_graph/als_factors.npz
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

GRAPH_DIR = Path.home() / ".astra_persistent" / "concept_graph"
EDGES_PATH = GRAPH_DIR / "papers_concepts_mapping.csv.gz"
VOCAB_PATH = GRAPH_DIR / "concepts_vocabulary.csv.gz"
FACTORS_PATH = GRAPH_DIR / "als_factors.npz"

ALS_FACTORS = 128
ALS_ALPHA = 10.0
ALS_REG = 0.05
ALS_ITERS = 30

# generic tokens that cannot alone establish a concept match
_GENERIC = {
    "relation", "relations", "correlation", "correlations", "effect",
    "effects", "method", "methods", "measurement", "measurements",
    "distribution", "distributions", "model", "models", "theory",
    "analysis", "survey", "surveys", "evolution", "formation",
    "structure", "structures", "properties", "property", "physical",
    "high", "low", "general", "basic", "detailed", "study", "studies",
}


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(t) >= 4}


class ConceptPrior:
    """Ranking-only novelty prior backed by ALS concept factors."""

    def __init__(self, names: List[str], labels: List[int],
                 factors: np.ndarray, popularity: Dict[int, int]):
        self.names = list(names)
        self.labels = list(labels)
        self.factors = np.asarray(factors, dtype=np.float32)
        self.popularity = dict(popularity)
        self._by_label = {l: i for i, l in enumerate(self.labels)}
        self._unit = self.factors / np.maximum(
            np.linalg.norm(self.factors, axis=1, keepdims=True), 1e-9)
        # precompute name tokens for matching
        self._name_toks = [(_tokens(n), _distinctive(_tokens(n)))
                           for n in self.names]

    @classmethod
    def from_arrays(cls, names, labels, factors, popularity) -> "ConceptPrior":
        return cls(names, labels, factors, popularity)

    @classmethod
    def load(cls, factors_path: Path = None) -> Optional["ConceptPrior"]:
        """Load trained factors + vocabulary. None when not fitted yet."""
        path = Path(factors_path or FACTORS_PATH)
        if not path.exists() or not VOCAB_PATH.exists():
            return None
        z = np.load(path, allow_pickle=False)
        import gzip
        import csv
        names, labels = [], []
        with gzip.open(VOCAB_PATH, "rt") as f:
            for row in csv.DictReader(f):
                labels.append(int(row["label"]))
                names.append(row["concept"])
        pop = {int(k): int(v) for k, v in
               zip(z["labels"], z["popularity"])}
        by_label = {l: i for i, l in enumerate(labels)}
        popularity = {l: pop.get(l, 0) for l in labels}
        factors = z["factors"][[by_label.get(l, -1) for l in labels]] \
            if "labels" in z else z["factors"]
        return cls(names, labels, factors, popularity)

    def match_concepts(self, text: str) -> List[Dict]:
        """Concepts whose distinctive name tokens appear in ``text``.

        A concept matches when at least one DISTINCTIVE token (non-generic,
        len>=4) is present and >= 60% of its name tokens are present — so
        'relation' or 'mass' alone never matches, but 'Tully-Fisher' does.

        The vocabulary contains duplicate concept names under different
        labels (rare clusters of the same phrase); matches are deduped by
        name, keeping the highest-popularity label — rare duplicates have
        weakly-determined ALS factors and only add noise.
        """
        toks = _tokens(text)
        hits = {}
        for i, (name, (all_toks, dist)) in enumerate(zip(
                self.names, self._name_toks)):
            if not all_toks or not dist:
                continue
            if not (dist & toks):
                continue
            if len(all_toks & toks) / len(all_toks) < 0.6:
                continue
            h = {"label": self.labels[i], "concept": name,
                 "n_papers": self.popularity.get(self.labels[i], 0)}
            if name not in hits or h["n_papers"] > hits[name]["n_papers"]:
                hits[name] = h
        return list(hits.values())

    def score(self, claim: str) -> Dict:
        """Crowding of the claim's concept combination.

        crowding = mean pairwise cosine affinity of matched concepts' ALS
        factors (0..1). Single-concept claims fall back to a popularity
        percentile (crowded field -> high). No match -> crowding None.
        Prior-only: recorded for ranking, never a gate.
        """
        hits = self.match_concepts(claim)
        if not hits:
            return {"concepts": [], "n": 0, "crowding": None,
                    "role": "prior-only-ranking-signal"}
        idx = [self._by_label[h["label"]] for h in hits]
        if len(idx) == 1:
            n = hits[0]["n_papers"]
            crowd = float(min(1.0, np.log1p(n) / np.log1p(100000)))
        else:
            dots = []
            for a in range(len(idx)):
                for b in range(a + 1, len(idx)):
                    dots.append(float(np.dot(self._unit[idx[a]],
                                             self._unit[idx[b]])))
            crowd = float(np.clip(np.mean(dots), 0.0, 1.0))
        return {"concepts": hits, "n": len(hits), "crowding": round(crowd, 3),
                "role": "prior-only-ranking-signal"}


def _distinctive(toks: set) -> set:
    return {t for t in toks if t not in _GENERIC}


# process-level singleton so the factors load once per interpreter
_PRIOR: Optional["ConceptPrior"] = None
_PRIOR_TRIED = False


def score_cached(claim: str) -> Optional[Dict]:
    """score() via a process-level singleton; None when unfitted or the
    underlying data is missing. NEVER raises into the discovery loop — the
    prior is optional signal, not a dependency."""
    global _PRIOR, _PRIOR_TRIED
    if not _PRIOR_TRIED:
        _PRIOR_TRIED = True
        try:
            _PRIOR = ConceptPrior.load()
        except Exception as e:
            logger.warning("[concept-prior] load failed: %s", e)
    if _PRIOR is None:
        return None
    try:
        return _PRIOR.score(claim)
    except Exception as e:
        logger.warning("[concept-prior] score failed: %s", e)
        return None


# --------------------------------------------------------------------------- #
# offline fit (one-time)                                                       #
# --------------------------------------------------------------------------- #
def build_matrix(edges_path: Path = None, vocab_path: Path = None):
    """Concept x paper CSR confidence matrix (alpha-weighted counts)."""
    import gzip
    import csv
    import scipy.sparse as sp

    edges_path = Path(edges_path or EDGES_PATH)
    vocab_path = Path(vocab_path or VOCAB_PATH)
    with gzip.open(vocab_path, "rt") as f:
        labels = [int(row["label"]) for row in csv.DictReader(f)]
    label_index = {l: i for i, l in enumerate(labels)}

    paper_index: Dict[str, int] = {}
    rows, cols, vals = [], [], []
    popularity: Dict[int, int] = {l: 0 for l in labels}
    with gzip.open(edges_path, "rt") as f:
        for row in csv.DictReader(f):
            arxiv_id = row["arxiv_id"]
            lab = int(row["label"])
            if lab not in label_index:
                continue
            p = paper_index.setdefault(arxiv_id, len(paper_index))
            rows.append(label_index[lab])
            cols.append(p)
            vals.append(1.0)
            popularity[lab] += 1
    mat = sp.csr_matrix((vals, (rows, cols)),
                        shape=(len(labels), len(paper_index)))
    return mat, labels, popularity


def fit(factors: int = ALS_FACTORS, alpha: float = ALS_ALPHA,
        reg: float = ALS_REG, iters: int = ALS_ITERS,
        out_path: Path = None) -> Dict:
    """Fit ALS on the concept-paper graph and persist the factors."""
    import implicit
    import scipy.sparse as sp

    mat, labels, popularity = build_matrix()
    model = implicit.als.AlternatingLeastSquares(
        factors=factors, regularization=reg, iterations=iters,
        random_state=42)
    # implicit's fit() takes an item_users matrix (items x users); we want
    # concepts as the FACTORED side whose pairwise affinity we read off, so
    # pass papers-as-users, concepts-as-items: concept factors end up in
    # model.item_factors (a first version mistakenly saved user_factors —
    # paper factors — which made every concept pair score ~0).
    model.fit(sp.csr_matrix((mat * alpha).astype(np.float64)).T.tocsr())
    out = Path(out_path or FACTORS_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        factors=model.item_factors.astype(np.float32),   # concept factors
        labels=np.array(labels, dtype=np.int64),
        popularity=np.array([popularity.get(l, 0) for l in labels],
                            dtype=np.int64),
        meta=np.array([f"als d={factors} alpha={alpha} reg={reg} "
                       f"iters={iters} papers={mat.shape[1]}"], dtype=object),
    )
    info = {"n_concepts": mat.shape[0], "n_papers": mat.shape[1],
            "nnz": int(mat.nnz), "factors": factors, "out": str(out)}
    logger.info("[concept-prior] fit: %s", info)
    return info


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="ALS concept-graph novelty prior")
    ap.add_argument("cmd", choices=["fit", "score"])
    ap.add_argument("claim", nargs="?", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "fit":
        print(fit())
    else:
        p = ConceptPrior.load()
        if p is None:
            print("[concept-prior] not fitted — run 'fit' first "
                  f"(needs {EDGES_PATH})")
            return
        import json
        print(json.dumps(p.score(args.claim or ""), indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
