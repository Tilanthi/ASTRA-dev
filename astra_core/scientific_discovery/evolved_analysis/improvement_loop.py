"""improvement_loop.py — gated, MEASURED self-improvement over ASTRA's failures (#2).

Reads the failure signal in ``claim_verdicts.jsonl``, clusters recurring failure
modes, proposes concrete gated fixes (propose ONLY — never auto-applies), and — the
part most loops skip — MEASURES whether an applied fix actually reduced the failure
class it targeted (before/after recurrence). The rolled-up effectiveness feeds the
capability index's Learning sub-score (so a sub-100 measure can lower CI).

Human stays on the approval gate: a fix is recorded as "applied" (with a date) in
``rsi_applied.jsonl`` by a human decision; this module only mines, proposes, and
measures. Inspired by The Beast's RSI v0.1/v0.2 loop, adapted to ASTRA.

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.improvement_loop mine
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.improvement_loop measure
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PERSIST = Path.home() / ".astra_persistent" / "evolved_programs"
VERDICT_LOG = PERSIST / "claim_verdicts.jsonl"
PROPOSALS = PERSIST / "rsi_proposals.jsonl"
APPLIED = PERSIST / "rsi_applied.jsonl"
EFFECTIVENESS = PERSIST / "rsi_effectiveness.txt"
MIN_COUNT = 3  # a failure class recurs if it has >= this many verdicts


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


def failure_class(v: Dict[str, Any]) -> str:
    """Classify a verdict's terminal outcome (the gate where it stopped)."""
    if v.get("both_pass") is True:
        return "novel_emit"          # success, not a failure
    if (v.get("gate1") or {}).get("pass") is not True:
        return "gate1_fail"
    if v.get("holdout") is False:
        return "holdout_block"
    if v.get("triviality") is False:
        return "triviality_block"
    if v.get("consistency") is False:
        return "consistency_block"
    if v.get("circularity") is False:
        return "circularity_block"
    st = (v.get("gate2") or {}).get("status")
    if st == "known":
        return "gate2_known"
    if st == "retrieval-failed":
        return "gate2_retrieval_failed"
    return "other"


def mine_failures(verdicts: Optional[List[Dict[str, Any]]] = None,
                  min_count: int = MIN_COUNT) -> List[Dict[str, Any]]:
    """Cluster recurring failure modes by (dataset, class)."""
    verdicts = verdicts if verdicts is not None else load_verdicts()
    counts: Dict[tuple, int] = {}
    for v in verdicts:
        cls = failure_class(v)
        if cls == "novel_emit":
            continue
        key = (v.get("dataset", "?"), cls)
        counts[key] = counts.get(key, 0) + 1
    clusters = [{"dataset": ds, "failure_class": cls, "count": n}
                for (ds, cls), n in counts.items() if n >= min_count]
    return sorted(clusters, key=lambda c: -c["count"])


# Hand-authored fix templates — one per failure class. Propose only; never applied.
_FIX_TEMPLATES = {
    "holdout_block": (
        "Generated run_claim computed on df_eval (ignored df_train), so the holdout-"
        "distinct gate rejected it. Fix: enforce claim_uses_train_split + the df_train "
        "prompt rule + --propose-retries (shipped 2026-07-14). Re-check the proposer "
        "isn't regressing."),
    "gate2_retrieval_failed": (
        "Gate-2 literature retrieval returned no papers (transient arXiv rate-limit). "
        "Fix: _http_get retry/backoff + retry-on-empty + don't cache transient "
        "retrieval-failed (shipped 2026-07-15). Verify arXiv endpoint reachability."),
    "gate2_known": (
        "Many claims on this dataset are textbook-known. Fix: if the rate is very "
        "high, raise the dataset's textbook_risk, or add richer columns / a niche_hint "
        "steering away from the dominant relation family."),
    "gate1_fail": (
        "Most candidates aren't statistically significant. Fix: review EFFECT_MIN and "
        "the proposer's relation targets; consider a niche_hint toward higher-signal "
        "relations for this dataset."),
    "triviality_block": (
        "Significant but near-deterministic / few-band identities. Fix: steer the "
        "proposer toward multi-column / residual relations (higher-order priming)."),
    "consistency_block": (
        "Narrated effect contradicts the measured one. Fix: have the proposer state the "
        "measured magnitude, not an aspirational one; strengthen the consistency rule."),
    "other": ("Unclassified failure — inspect the verdict manually."),
}


def propose_fixes(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    props = []
    for i, c in enumerate(clusters, 1):
        cls = c["failure_class"]
        props.append({
            "id": f"P{i:03d}", "dataset": c["dataset"], "failure_class": cls,
            "count": c["count"],
            "proposal": _FIX_TEMPLATES.get(cls, _FIX_TEMPLATES["other"]),
            "needs_approval": True,
            "reversibility": "prompt/config change; reversible",
        })
    return props


def write_proposals(props: List[Dict[str, Any]]) -> None:
    PERSIST.mkdir(parents=True, exist_ok=True)
    with PROPOSALS.open("w") as f:
        for p in props:
            f.write(json.dumps(p) + "\n")


def _rate(verdicts: List[Dict[str, Any]], failure_class_name: str,
          dataset: Optional[str] = None) -> float:
    """Share of verdicts (optionally on a dataset) that are the given failure class."""
    vs = [v for v in verdicts if dataset is None or v.get("dataset") == dataset]
    if not vs:
        return 0.0
    n = sum(1 for v in vs if failure_class(v) == failure_class_name)
    return n / len(vs)


def measure_effectiveness() -> Optional[Dict[str, Any]]:
    """For each recorded applied fix, compare the failure-class rate before vs after
    its apply-date. Returns per-fix effectiveness + a roll-up; writes the roll-up to
    rsi_effectiveness.txt (consumed by the capability index). None if nothing applied."""
    if not APPLIED.exists():
        return None
    applied = [json.loads(l) for l in APPLIED.read_text().splitlines() if l.strip()]
    verdicts = load_verdicts()
    per_fix = []
    for a in applied:
        cls = a["failure_class"]
        ds = a.get("dataset")
        cut = _parse_ts(a.get("date_applied"))
        if cut is None:
            continue
        before = [v for v in verdicts if (_parse_ts(v.get("ts", "")) or datetime.min) < cut]
        after = [v for v in verdicts if (_parse_ts(v.get("ts", "")) or datetime.min) >= cut]
        rb, ra = _rate(before, cls, ds), _rate(after, cls, ds)
        if rb > 0:
            eff = round(100.0 * max(0.0, (rb - ra) / rb), 1)
        else:
            eff = 100.0 if ra == 0 else 0.0
        per_fix.append({"id": a.get("id"), "failure_class": cls, "dataset": ds,
                        "rate_before": round(rb, 4), "rate_after": round(ra, 4),
                        "effectiveness": eff})
    if not per_fix:
        return None
    rollup = round(sum(p["effectiveness"] for p in per_fix) / len(per_fix), 1)
    try:
        EFFECTIVENESS.write_text(str(rollup))
    except Exception:
        pass
    return {"per_fix": per_fix, "rsi_effectiveness": rollup,
            "note": "improving, not solved — sub-100 is honest"}


def _cmd_mine():
    clusters = mine_failures()
    props = propose_fixes(clusters)
    write_proposals(props)
    print(f"[rsi] mined {len(clusters)} recurring failure class(es) -> "
          f"{len(props)} proposal(s) (PROPOSE ONLY, not applied):")
    for p in props:
        print(f"  {p['id']} [{p['dataset']}/{p['failure_class']}] x{p['count']}: "
              f"{p['proposal'][:90]}")
    print(f"[rsi] proposals -> {PROPOSALS}")
    print("[rsi] to close the loop: apply a fix, append an entry to "
          f"{APPLIED} ({{id,failure_class,dataset?,date_applied}}), then run 'measure'.")


def _cmd_measure():
    res = measure_effectiveness()
    if res is None:
        print(f"[rsi] nothing to measure — record an applied fix in {APPLIED} first.")
        return
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "mine":
        _cmd_mine()
    elif cmd == "measure":
        _cmd_measure()
    else:
        clusters = mine_failures()
        print(f"[rsi] recurring failure classes: {len(clusters)}")
        for c in clusters:
            print(f"  {c['dataset']}/{c['failure_class']}: x{c['count']}")
