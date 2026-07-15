"""predictions.py — predict-before-act + scored surprise ledger (self-improvement #1).

The verdict log (``claim_verdicts.jsonl``) records OUTCOMES. This module adds the
missing PREDICTION half: before each claim-search episode a statistical-baseline
prediction (from that dataset's recent history) is written; after the episode the
actual outcome is compared and a ``surprise`` score (0-1) is appended to a ledger.
That turns the verdict log into a CALIBRATION instrument — you can measure whether
ASTRA's historical baseline predicts the next episode, which is the trust signal
for running it more unsupervised.

Predictions are STATISTICAL (rolling per-dataset history), not LLM self-confidence
— deliberately cheap (no extra LLM call) and honest. Inspired by The Beast's
predict-before-act + surprise ledger (Perni/Dey, "Unleashing the Beast," 2026),
adapted to ASTRA's single-supervisor design.

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.predictions
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PERSIST = Path.home() / ".astra_persistent" / "evolved_programs"
VERDICT_LOG = PERSIST / "claim_verdicts.jsonl"
PREDICTIONS = PERSIST / "predictions.jsonl"
SURPRISE_LEDGER = PERSIST / "surprise_ledger.jsonl"
HISTORY_WINDOW = 5  # recent episodes to base predictions on


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse_ts(s: Any):
    for f in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(s)[:26], f)
        except Exception:
            pass
    return None


def load_verdicts() -> List[Dict[str, Any]]:
    if not VERDICT_LOG.exists():
        return []
    return [json.loads(l) for l in VERDICT_LOG.read_text().splitlines() if l.strip()]


def _split_into_episodes(verdicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """A run_claim_search run emits a 'seed' verdict then 'step{i}' verdicts; a new
    episode starts at each 'seed'. Returns per-episode gate1_pass_rate + novel_emits."""
    eps: List[List[Dict[str, Any]]] = []
    cur: Optional[List[Dict[str, Any]]] = None
    for v in sorted(verdicts, key=lambda v: v.get("ts", "")):
        if (v.get("label") or "") == "seed" or cur is None:
            cur = []
            eps.append(cur)
        cur.append(v)
    out = []
    for ev in eps:
        n = len(ev)
        g1 = sum(1 for v in ev if (v.get("gate1") or {}).get("pass") is True)
        nov = sum(1 for v in ev if v.get("both_pass") is True)
        out.append({"gate1_pass_rate": (g1 / n) if n else None,
                    "novel_emits": nov, "n": n})
    return out


def historical_stats(dataset: str, verdicts: Optional[List[Dict[str, Any]]] = None):
    """Rolling per-dataset stats from prior episodes, or None if no history."""
    verdicts = verdicts if verdicts is not None else load_verdicts()
    eps = _split_into_episodes([v for v in verdicts if v.get("dataset") == dataset])
    if not eps:
        return None
    recent = eps[-HISTORY_WINDOW:]
    g1 = [e["gate1_pass_rate"] for e in recent if e["gate1_pass_rate"] is not None]
    nov = [e["novel_emits"] for e in recent if e["novel_emits"] is not None]
    return {
        "gate1_pass_rate": statistics.mean(g1) if g1 else None,
        "novel_emits": statistics.mean(nov) if nov else None,
        "n_episodes": len(recent),
    }


@dataclass
class Prediction:
    dataset: str
    ts: str
    predicted_gate1_pass_rate: Optional[float]
    predicted_novel_emits: Optional[float]
    confidence: float            # 0-1, from history depth
    key_uncertainty: str
    n_history: int


def predict_for_episode(dataset: str,
                        verdicts: Optional[List[Dict[str, Any]]] = None) -> Prediction:
    """Statistical-baseline prediction for the next episode on this dataset."""
    stats = historical_stats(dataset, verdicts)
    n = stats["n_episodes"] if stats else 0
    return Prediction(
        dataset=dataset, ts=_now_iso(),
        predicted_gate1_pass_rate=stats["gate1_pass_rate"] if stats else None,
        predicted_novel_emits=stats["novel_emits"] if stats else None,
        confidence=min(1.0, n / HISTORY_WINDOW),
        key_uncertainty=("limited history — baseline unreliable"
                         if n < HISTORY_WINDOW else "steady-state assumption"),
        n_history=n,
    )


def write_prediction(pred: Prediction) -> None:
    PERSIST.mkdir(parents=True, exist_ok=True)
    with PREDICTIONS.open("a") as f:
        f.write(json.dumps(asdict(pred)) + "\n")


def episode_actuals(dataset: str, since_ts: str,
                    verdicts: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Outcomes of the episode that ran after ``since_ts`` on ``dataset``."""
    verdicts = verdicts if verdicts is not None else load_verdicts()
    since = _parse_ts(since_ts) or datetime.min
    vs = [v for v in verdicts if v.get("dataset") == dataset
          and (_parse_ts(v.get("ts", "")) or datetime.min) >= since]
    n = len(vs)
    if n == 0:
        return {"gate1_pass_rate": None, "novel_emits": 0, "n": 0}
    g1 = sum(1 for v in vs if (v.get("gate1") or {}).get("pass") is True)
    return {"gate1_pass_rate": g1 / n,
            "novel_emits": sum(1 for v in vs if v.get("both_pass") is True), "n": n}


def score_surprise(pred: Prediction, actuals: Dict[str, Any]) -> float:
    """Surprise in [0,1]: 0.6*outcome_mismatch + 0.4*(1-confidence)."""
    pg, ag = pred.predicted_gate1_pass_rate, actuals.get("gate1_pass_rate")
    pn, an = pred.predicted_novel_emits, actuals.get("novel_emits")
    if ag is None:                       # episode produced nothing
        om = 1.0
    else:
        gm = abs((pg if pg is not None else 0.5) - ag)
        if pn is not None and (pn or an):
            nm = min(abs((pn or 0) - (an or 0)) / max(1.0, pn or 1.0, an or 1.0), 1.0)
        else:
            nm = 0.5
        om = 0.5 * gm + 0.5 * nm
    surprise = 0.6 * om + 0.4 * (1.0 - pred.confidence)
    return round(min(1.0, max(0.0, surprise)), 4)


def append_surprise(pred: Prediction, actuals: Dict[str, Any], surprise: float) -> None:
    PERSIST.mkdir(parents=True, exist_ok=True)
    entry = {"ts": _now_iso(), "dataset": pred.dataset,
             "predicted_gate1_pass_rate": pred.predicted_gate1_pass_rate,
             "actual_gate1_pass_rate": actuals.get("gate1_pass_rate"),
             "predicted_novel_emits": pred.predicted_novel_emits,
             "actual_novel_emits": actuals.get("novel_emits"),
             "confidence": pred.confidence, "surprise": surprise}
    with SURPRISE_LEDGER.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def calibration_metrics() -> Optional[Dict[str, Any]]:
    """Mean/recent surprise over the ledger — the Calibration/Learning feedstock."""
    if not SURPRISE_LEDGER.exists():
        return None
    entries = [json.loads(l) for l in SURPRISE_LEDGER.read_text().splitlines() if l.strip()]
    if not entries:
        return None
    s = [e.get("surprise", 0) for e in entries]
    return {"mean_surprise": round(statistics.mean(s), 4),
            "recent_mean": round(statistics.mean(s[-5:]), 4),
            "n": len(s)}


if __name__ == "__main__":
    cm = calibration_metrics()
    print("calibration:", cm or "(no surprise ledger yet)")
    for ds in ("sdss_galaxy_extended", "sdss_qso", "wise_midir", "gaia_variables"):
        st = historical_stats(ds)
        if st:
            print(f"  {ds}: hist gate1_pass={st['gate1_pass_rate']}, "
                  f"novel_emits={st['novel_emits']}, eps={st['n_episodes']}")
