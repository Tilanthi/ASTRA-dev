"""contamination_guards.py — holdout + temporal contamination guards (#7).

AstroMLab lesson (EAIRA / IOAA): a benchmark whose answers the model has seen
measures nothing. ASTRA's falsification arm has the same exposure:

1. **Holdout split** — a deterministic 30% of registry prediction IDs are
   holdout (``is_holdout``). They are excluded from every LLM-visible context
   (``llm_visible``), so if a narration ever *matches* a holdout entry
   (``holdout_alarm``) the LLM is confabulating or the pipeline leaked — either
   way the emission is quarantined, not promoted.

2. **Temporal check** — a "prediction" that postdates the data release it is
   tested against could have been fit to that data. ``temporal_check`` fails
   such pairings; archival data predating the prediction is the strongest test.

The split is hash-based, not random, so it is stable across runs and identical
for every consumer — no seed drift, no accidental un-holding.
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable, List, Optional

# ids forced into the holdout set (tests / explicit quarantine)
_FORCE_HOLDOUT: set = set()

_STOP = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
    "were", "has", "have", "had", "its", "per", "into", "given", "under",
    "predicts", "predicted", "predicting", "predict", "advance", "value",
    "expected", "measured", "observe", "observed", "using", "used",
}


def is_holdout(prediction_id: str) -> bool:
    """Deterministic 30% holdout membership: sha1(id) % 10 < 3."""
    if prediction_id in _FORCE_HOLDOUT:
        return True
    h = hashlib.sha1(prediction_id.encode()).hexdigest()
    return int(h, 16) % 10 < 3


def llm_visible(records: Iterable) -> List:
    """Filter an iterable of registry-like records down to non-holdout entries.

    Use this wherever prediction metadata is rendered into an LLM context
    (selection, narration, summarisation). Holdout entries stay code-only.
    """
    return [r for r in records if not is_holdout(getattr(r, "id", ""))]


def _terms(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(w) >= 3 and w not in _STOP}


def holdout_alarm(narration: str, records: Iterable,
                  threshold: float = 0.5) -> Optional[dict]:
    """Return an alarm dict if ``narration`` overlaps a holdout record's
    distinctive content terms at >= ``threshold`` (fraction of the record's
    terms present in the narration). None when clean.

    Overlap here means the narration restates what a holdout entry predicts —
    impossible if holdout entries truly never entered the LLM context.
    """
    text_terms = _terms(narration)
    best = None
    for r in records:
        rid = getattr(r, "id", "")
        if not is_holdout(rid):
            continue
        rec_terms = _terms(" ".join([
            getattr(r, "quantity", "") or "",
            getattr(r, "formula_doc", "") or ""]))
        if not rec_terms:
            continue
        overlap = len(rec_terms & text_terms) / len(rec_terms)
        if overlap >= threshold and (best is None or overlap > best["overlap"]):
            best = {"matched_id": rid, "overlap": round(overlap, 3),
                    "n_terms": len(rec_terms)}
    return best


def temporal_check(prediction_year: Optional[int],
                   data_release_year: Optional[int]) -> tuple:
    """(ok, reason): a prediction made AFTER the data was public could have
    been fit to it — fail. Unknown years defer (ok=True, 'unknown ...')."""
    if prediction_year is None:
        return True, "unknown prediction year; temporal check deferred"
    if data_release_year is None:
        return True, "unknown data release year; temporal check deferred"
    if prediction_year > data_release_year:
        return False, (f"prediction ({prediction_year}) postdates data release "
                       f"({data_release_year}) — it could have been fit to the data")
    return True, (f"prediction ({prediction_year}) predates or is contemporaneous "
                  f"with data release ({data_release_year})")
