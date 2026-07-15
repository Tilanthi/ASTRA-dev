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


def _discovery_score(verdicts) -> Optional[float]:
    """OUTCOME metric (#2): recent genuine novel-yield (both-gate survivors /
    evaluated candidates) vs an aspirational target, plus an improvement trend.
    This is what makes the CI track DISCOVERY quality, not just pipeline health —
    and it goes DOWN when the system is process-healthy but textbook-dominated
    (ASTRA's actual situation). TARGET and the trend weight are tunable."""
    nonseed = [v for v in verdicts if (v.get("label") or "") != "seed"]
    if len(nonseed) < 4:
        return None
    sv = sorted(nonseed, key=lambda v: v.get("ts", ""))
    mid = len(sv) // 2
    older, recent = sv[:mid], sv[mid:]

    def yrate(vs):
        return (sum(1 for v in vs if v.get("both_pass") is True) / len(vs)) if vs else 0.0

    yr_recent, yr_older = yrate(recent), yrate(older)
    TARGET = 0.15  # aspirational novel-yield (~1 in 7 candidates -> both-gate novel); tunable
    level = min(1.0, yr_recent / TARGET)
    trend = max(0.0, yr_recent - yr_older) / TARGET     # bonus if improving
    return round(100.0 * min(1.0, level + 0.5 * trend), 1)


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

    # Calibration: Brier-scored forecast calibration (primary); surprise fallback.
    # Brier in [0,1]: 0 => perfect, 0.25 => constant-0.5/climatological. Map so
    # brier 0 -> 100, 0.25 -> 50, 0.5 -> 0.
    calibration = None
    if cm and cm.get("mean_brier") is not None:
        calibration = round(max(0.0, min(100.0, 100.0 * (1.0 - 2.0 * cm["mean_brier"]))), 1)
    elif cm and cm.get("mean_surprise") is not None:
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
    discovery = _discovery_score(verdicts)   # OUTCOME sub-score (#2)

    weighted = [("calibration", 0.25, calibration), ("learning", 0.20, learning),
                ("execution", 0.15, execution), ("breadth", 0.15, breadth),
                ("discovery", 0.25, discovery)]
    avail = [(w, v) for _, w, v in weighted if v is not None]
    ci = round(sum(w * v for w, v in avail) / sum(w for w, _ in avail), 1) if avail else None

    # Phase 3b: human-confirmation rate over reviewed novel claims (a real outcome
    # metric once a human reviews via discovery_review). None until reviews exist.
    try:
        from . import discovery_review
        confirmation = discovery_review.confirmation_rate()
    except Exception:
        confirmation = None

    result = {"ts": _now_iso(), "ci": ci,
              "calibration": calibration, "learning": learning,
              "execution": execution, "breadth": breadth, "discovery": discovery,
              "discovery_confirmation": confirmation,
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
