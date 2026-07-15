"""predictions.py — probabilistic forecast + Brier-scored calibration (#1, upgraded).

Before each claim-search episode, emit a PROBABILISTIC forecast of the outcome that
matters — P(>=1 novel emit) — as a Beta-posterior from the dataset's episode history
(Beta(1,1) prior => 0.5 under no history, i.e. honest max-uncertainty). After the
episode, score it with the Brier score ((p - outcome)^2) and append to a ledger.

This is REAL calibration in the forecasting sense: a calibrated forecaster is one
whose predicted probabilities match observed frequencies. We compute the mean Brier
score and a reliability curve (forecast-probability bins vs observed frequency) over
the ledger. This is strictly stronger than (a) a rolling point average (which only
measures stationarity) and (b) an LLM-authored confidence number (itself usually
miscalibrated, and it costs an extra call per episode). It also detects regime
shifts directly: when the base rate moves, the Beta forecast lags and Brier rises.

A mismatch-based ``surprise`` is kept for backward-compat / the Learning trend.

Run: PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.predictions
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PERSIST = Path.home() / ".astra_persistent" / "evolved_programs"
VERDICT_LOG = PERSIST / "claim_verdicts.jsonl"
PREDICTIONS = PERSIST / "predictions.jsonl"
SURPRISE_LEDGER = PERSIST / "surprise_ledger.jsonl"
HISTORY_WINDOW = 5


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


def _episodes_for(dataset: str, verdicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _split_into_episodes([v for v in verdicts if v.get("dataset") == dataset])


def historical_stats(dataset: str, verdicts: Optional[List[Dict[str, Any]]] = None):
    verdicts = verdicts if verdicts is not None else load_verdicts()
    eps = _episodes_for(dataset, verdicts)
    if not eps:
        return None
    recent = eps[-HISTORY_WINDOW:]
    g1 = [e["gate1_pass_rate"] for e in recent if e["gate1_pass_rate"] is not None]
    nov = [e["novel_emits"] for e in recent if e["novel_emits"] is not None]
    return {"gate1_pass_rate": statistics.mean(g1) if g1 else None,
            "novel_emits": statistics.mean(nov) if nov else None,
            "n_episodes": len(recent)}


def _episode_outcomes(dataset: str, verdicts: List[Dict[str, Any]]) -> List[int]:
    """1 if an episode emitted >=1 novel claim, else 0 — the binary outcome the
    forecast predicts."""
    return [1 if (e["novel_emits"] or 0) > 0 else 0 for e in _episodes_for(dataset, verdicts)]


@dataclass
class Prediction:
    dataset: str
    ts: str
    predicted_gate1_pass_rate: Optional[float]   # point context
    predicted_novel_emits: Optional[float]       # point context
    p_novel: float                               # Beta-posterior P(>=1 novel emit)
    confidence: float                            # 0-1, history depth (legacy)
    key_uncertainty: str
    n_history: int


def predict_for_episode(dataset: str,
                        verdicts: Optional[List[Dict[str, Any]]] = None) -> Prediction:
    """Probabilistic forecast for the next episode on this dataset."""
    verdicts = verdicts if verdicts is not None else load_verdicts()
    stats = historical_stats(dataset, verdicts)
    outcomes = _episode_outcomes(dataset, verdicts)
    n_eps = len(outcomes)
    # Beta(1,1) posterior mean over binary episode outcomes: honest, regresses to
    # 0.5 with no history (max uncertainty), converges to the base rate as data grows.
    p_novel = (sum(outcomes) + 1) / (n_eps + 2)
    return Prediction(
        dataset=dataset, ts=_now_iso(),
        predicted_gate1_pass_rate=stats["gate1_pass_rate"] if stats else None,
        predicted_novel_emits=stats["novel_emits"] if stats else None,
        p_novel=round(p_novel, 4),
        confidence=min(1.0, n_eps / HISTORY_WINDOW),
        key_uncertainty=("limited history — forecast regresses to 0.5"
                         if n_eps < HISTORY_WINDOW else "base-rate assumption"),
        n_history=n_eps,
    )


def write_prediction(pred: Prediction) -> None:
    PERSIST.mkdir(parents=True, exist_ok=True)
    with PREDICTIONS.open("a") as f:
        f.write(json.dumps(asdict(pred)) + "\n")


def episode_actuals(dataset: str, since_ts: str,
                    verdicts: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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


def episode_outcome(actuals: Dict[str, Any]) -> int:
    """Binary outcome the forecast predicts: 1 if the episode emitted >=1 novel."""
    return 1 if (actuals.get("novel_emits") or 0) > 0 else 0


def brier(p_novel: float, outcome: int) -> float:
    """Brier score for the binary forecast: (p - outcome)^2 in [0,1]; 0 = perfect,
    0.25 = a constant-0.5 / climatological forecast."""
    return round((p_novel - outcome) ** 2, 4)


def score_surprise(pred: Prediction, actuals: Dict[str, Any]) -> float:
    """Legacy mismatch-based surprise (0-1); kept for the Learning trend."""
    pg, ag = pred.predicted_gate1_pass_rate, actuals.get("gate1_pass_rate")
    pn, an = pred.predicted_novel_emits, actuals.get("novel_emits")
    if ag is None:
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


def append_surprise(pred: Prediction, actuals: Dict[str, Any],
                    surprise: float) -> None:
    """Record the forecast, outcome, Brier, and legacy surprise for this episode."""
    outcome = episode_outcome(actuals)
    entry = {"ts": _now_iso(), "dataset": pred.dataset,
             "p_novel": pred.p_novel, "outcome": outcome,
             "brier": brier(pred.p_novel, outcome),
             "predicted_gate1_pass_rate": pred.predicted_gate1_pass_rate,
             "actual_gate1_pass_rate": actuals.get("gate1_pass_rate"),
             "predicted_novel_emits": pred.predicted_novel_emits,
             "actual_novel_emits": actuals.get("novel_emits"),
             "confidence": pred.confidence, "surprise": surprise}
    PERSIST.mkdir(parents=True, exist_ok=True)
    with SURPRISE_LEDGER.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def _load_ledger() -> List[Dict[str, Any]]:
    if not SURPRISE_LEDGER.exists():
        return []
    return [json.loads(l) for l in SURPRISE_LEDGER.read_text().splitlines() if l.strip()]


def calibration_metrics() -> Optional[Dict[str, Any]]:
    """Mean/recent Brier (primary calibration) + legacy surprise, over the ledger."""
    entries = _load_ledger()
    if not entries:
        return None
    out: Dict[str, Any] = {"n": len(entries)}
    briers = [e["brier"] for e in entries if "brier" in e]
    if briers:
        out["mean_brier"] = round(statistics.mean(briers), 4)
        out["recent_brier"] = round(statistics.mean(briers[-5:]), 4)
    surprises = [e["surprise"] for e in entries if "surprise" in e]
    if surprises:
        out["mean_surprise"] = round(statistics.mean(surprises), 4)
        out["recent_mean"] = round(statistics.mean(surprises[-5:]), 4)
    return out


def calibration_curve(bins: int = 5) -> List[Tuple[float, float, float, int]]:
    """Reliability curve: (bin_center, mean_forecast_p, observed_frequency, n) per
    forecast-probability bin. A calibrated forecaster has mean_forecast ~= observed."""
    entries = [e for e in _load_ledger() if "p_novel" in e and "outcome" in e]
    if not entries:
        return []
    edges = [i / bins for i in range(bins + 1)]
    out = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        members = [e for e in entries if lo <= e["p_novel"] < hi or (i == bins - 1 and e["p_novel"] == hi)]
        if not members:
            continue
        mf = statistics.mean(e["p_novel"] for e in members)
        of = statistics.mean(e["outcome"] for e in members)
        out.append((round((lo + hi) / 2, 3), round(mf, 3), round(of, 3), len(members)))
    return out


if __name__ == "__main__":
    cm = calibration_metrics()
    print("calibration:", cm or "(no surprise ledger yet)")
    if cm:
        print("reliability curve (bin, mean_forecast, observed_freq, n):")
        for row in calibration_curve():
            print("  ", row)
    for ds in ("sdss_galaxy_extended", "sdss_qso", "wise_midir", "gaia_variables"):
        oc = _episode_outcomes(ds, load_verdicts())
        if oc:
            print(f"  {ds}: episode outcomes {oc} -> base rate "
                  f"{sum(oc)/len(oc):.2f}, Beta p_novel={(sum(oc)+1)/(len(oc)+2):.3f}")
