"""novelty_precheck.py — cheap deterministic features logged beside every
novelty-judge call.

Calibration against 4,103 cached LLM verdicts (2026-08-20) killed the obvious
tiered-escalation designs, so the numbers are on record here:

* claim-to-abstract MiniLM similarity: only 5/4103 calls reach 0.80 (where
  precision is 1.0); at 0.75 precision drops to 0.64 — no coverage.
* content-term containment in a retrieved abstract: ~0% of calls reach 0.6.
* reusing the verdict of a >=0.9-similar previously judged claim: 55%
  agreement — barely above the 53% coin-flip base rate, so the judge's own
  test-retest reliability on near-identical claims is ~55% (a quality fact,
  quantified prospectively by the noise-floor script, not a dedup lever).

``should_auto_known`` therefore defaults to False. Setting
``ASTRA_NOVELTY_AUTOKNOWN_TAU=<float>`` arms a similarity tier at that
threshold — only do this after checking the logged precision in
``novelty_precheck.jsonl`` justifies it.

Every judge call should log its features plus the final verdict via
``log_precheck``; the accumulated file is the standing precision/recall
measurement for any future deterministic tier.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

PRECHECK_PATH = (Path.home() / ".astra_persistent" / "evolved_programs"
                 / "novelty_precheck.jsonl")

_STOP = set(
    "the a an of in with and to is are that this for on at by be from as it we "
    "show have has than more less very between into its their was were our "
    "these those such also using used use correlated correlation correlates "
    "positively negatively significant significantly strongly weakly relation "
    "relationship associated associate sample samples result results found "
    "find report reported higher lower greater fewer increase decrease "
    "evidence indicates indicate suggests suggest".split())

_MODEL = None


def _embedder():
    """Lazy MiniLM load (CPU; the ASTRA embedding backbone)."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _terms(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9\-]+", text.lower())
            if w not in _STOP and len(w) > 2]


def precheck_features(claim: str, papers: List[dict]) -> Dict[str, float]:
    """Deterministic signals for the escalation decision.

    ``top_similarity`` — max MiniLM cosine between the claim and any
    retrieved title+abstract, with the argmax index.
    ``containment`` — fraction of claim content terms appearing in the
    best-matching abstract (the textual-entailment branch).
    """
    feats = {"top_similarity": 0.0, "top_similarity_idx": -1,
             "containment": 0.0}
    if not claim or not papers:
        return feats
    texts = [f"{p.get('title', '')} {p.get('abstract', '')[:900]}".strip()
             for p in papers]
    texts = [t for t in texts if t]
    if not texts:
        return feats
    try:
        m = _embedder()
        ce = m.encode([claim], normalize_embeddings=True)[0]
        te = m.encode(texts, normalize_embeddings=True)
        sims = (te @ ce).tolist()
        best = int(max(range(len(sims)), key=lambda i: sims[i]))
        feats["top_similarity"] = round(float(sims[best]), 4)
        feats["top_similarity_idx"] = best
        claim_terms = set(_terms(claim))
        if claim_terms:
            abstract_terms = set(_terms(texts[best]))
            feats["containment"] = round(
                len(claim_terms & abstract_terms) / len(claim_terms), 4)
    except Exception as e:  # embedding unavailable -> features stay 0, judge runs
        logger.debug("[precheck] feature computation failed: %s", e)
    return feats


def should_auto_known(features: Dict[str, float]) -> bool:
    """Only true when a threshold is explicitly armed via the environment."""
    tau = os.environ.get("ASTRA_NOVELTY_AUTOKNOWN_TAU", "").strip()
    if not tau:
        return False
    try:
        return float(features.get("top_similarity", 0.0)) >= float(tau)
    except ValueError:
        return False


def log_precheck(features: Dict[str, float], verdict: str,
                 path: Optional[Path] = None,
                 confidence: Optional[float] = None) -> None:
    """Append one features+verdict row — the standing precision/recall data."""
    target = Path(path) if path is not None else PRECHECK_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": datetime.now(timezone.utc).isoformat(),
               "verdict": verdict, **{k: features.get(k) for k in
                                      ("top_similarity", "containment")}}
        if confidence is not None:
            row["confidence"] = confidence
        with open(target, "a") as f:
            f.write(json.dumps(row) + "\n")
    except Exception as e:
        logger.debug("[precheck] log failed: %s", e)
