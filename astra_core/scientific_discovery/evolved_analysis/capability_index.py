"""capability_index.py — a dated, reproducible capability index (self-improvement #3).

A single CI-score (0-100) computed entirely from artifacts ASTRA already produces
(verdict log, surprise ledger, data breadth, RSI effectiveness). The defining
design property, borrowed from The Beast's instrument: **it ingests inputs that can
LOWER its own headline number** — e.g. a sub-100 RSI-effectiveness measure is
blended into the Learning sub-score, and rising surprise lowers Calibration. A
vanity metric never does that.

The TREND is the signal, not the level; 100 means "saturates this formula," not
"finished." Sub-scores degrade gracefully (renormalised over whichever inputs
exist), so the first run on sparse data is honest rather than padded.

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.capability_index
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from . import predictions

PERSIST = Path.home() / ".astra_persistent" / "evolved_programs"
CI_HISTORY = PERSIST / "ci_history.jsonl"
RSI_EFFECTIVENESS = PERSIST / "rsi_effectiveness.txt"
BREADTH_HORIZON = 6  # distinct datasets that would "saturate" the breadth score


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _execution_score(verdicts) -> Optional[float]:
    """Fraction of episodes that ran beyond the seed sanity check (i.e. produced
    >=1 evaluated candidate). A seed-only episode means the search errored before
    mining (no token, proposer unavailable, etc.) — the live-ness/execution signal."""
    eps = predictions._split_into_episodes(verdicts)
    if not eps:
        return None
    executed = sum(1 for ep in eps if ep["n"] >= 2)
    return round(100.0 * executed / len(eps), 1)


def _breadth_score(verdicts) -> Optional[float]:
    distinct = {v.get("dataset") for v in verdicts if v.get("dataset")}
    distinct.discard(None)
    if not distinct:
        return None
    return round(100.0 * min(1.0, len(distinct) / BREADTH_HORIZON), 1)


def _read_rsi_effectiveness() -> Optional[float]:
    if not RSI_EFFECTIVENESS.exists():
        return None
    try:
        return float(RSI_EFFECTIVENESS.read_text().strip())
    except Exception:
        return None


def compute_ci() -> Dict[str, Any]:
    """Compute the capability index from live artifacts. Never raises."""
    verdicts = predictions.load_verdicts()
    cm = predictions.calibration_metrics()

    # Calibration: low mean surprise => high calibration.
    calibration = None
    if cm:
        calibration = round(100.0 * (1.0 - cm["mean_surprise"]), 1)

    # Learning: recent surprise level + trend, blended with RSI effectiveness.
    learning = None
    if cm:
        level = 100.0 * (1.0 - cm["recent_mean"])
        trend = 0.0
        if cm["mean_surprise"] is not None and cm["n"] >= 2:
            # declining surprise (recent < overall) is a positive trend
            trend = 100.0 * max(0.0, cm["mean_surprise"] - cm["recent_mean"])
        learning = round(min(100.0, level + trend), 1)
    rsi_eff = _read_rsi_effectiveness()
    if learning is not None and rsi_eff is not None:
        learning = round(0.5 * learning + 0.5 * rsi_eff, 1)   # can LOWER it
    elif learning is None and rsi_eff is not None:
        learning = round(rsi_eff, 1)

    execution = _execution_score(verdicts)
    breadth = _breadth_score(verdicts)

    weighted = [("calibration", 0.30, calibration), ("learning", 0.25, learning),
                ("execution", 0.25, execution), ("breadth", 0.20, breadth)]
    avail = [(w, v) for _, w, v in weighted if v is not None]
    ci = round(sum(w * v for w, v in avail) / sum(w for w, _ in avail), 1) if avail else None

    result = {"ts": _now_iso(), "ci": ci,
              "calibration": calibration, "learning": learning,
              "execution": execution, "breadth": breadth,
              "rsi_effectiveness_blended": rsi_eff,
              "subscores_available": [k for k, _, v in weighted if v is not None],
              "note": "trend not level; 100 = formula saturation, not completion"}
    # append to history (never crash the run on a write failure)
    try:
        PERSIST.mkdir(parents=True, exist_ok=True)
        with CI_HISTORY.open("a") as f:
            f.write(json.dumps(result) + "\n")
    except Exception:
        pass
    return result


if __name__ == "__main__":
    ci = compute_ci()
    print(json.dumps(ci, indent=2))
