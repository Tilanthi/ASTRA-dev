"""calibration_lens.py — Phase 2 of the Eureka plan (2026-08-30).

"Build the calibration lens: recompute published claims touching our data
from raw data, write a plain note beside every disagreement, deliver the
notes at session start, and count how often a note changes a verdict."

The published claims are the falsification arm's model predictions (GR
perihelion precession, SIS Einstein radii, the M–T coupling) — each states
what a PUBLISHED model predicts for a quantity on a system whose data we
hold, so recomputing prediction-vs-data from the raw inputs is exactly the
lens the plan describes. The lens reuses :mod:`falsification.engine`
computation (code-only; the LLM never sets a value) and adds three things
the arm does not provide:

  1. a PLAIN note per (model, system): what is predicted, what our
     recomputation gives, agree/disagree at how many sigma — persisted to
     ``calibration_notes.json`` and the ledger (kind=calibration);
  2. delivery at session start: ``data_lake.task_system_for`` appends the
     notes head to every proposer prompt;
  3. the counter: ``verdicts_changed_by_notes`` cross-references the verdict
     log for claims whose outcome flipped AFTER a note on their dataset was
     delivered — the 90-day-review number "verdicts changed by calibration
     notes". (Mechanical approximation: it cannot see inside a session's
     reasoning, only the flip; the plan's own stop condition reads "retire
     the lens if a note never changes a verdict in a quarter".)

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.calibration_lens recompute|notes|stats
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PERSIST = Path.home() / ".astra_persistent"
EVOLVED_PROGRAMS = PERSIST / "evolved_programs"
NOTES = EVOLVED_PROGRAMS / "calibration_notes.json"
VERDICT_LOG = EVOLVED_PROGRAMS / "claim_verdicts.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def recompute(write: bool = True) -> list:
    """Recompute every published model claim against our data; write notes.

    Only a note that is NEW or CHANGED (status flip or delta moved > 0.01) is
    appended to the ledger — the clock recomputes the lens every firing, and
    an unchanged note re-fed as "new evidence" every day would both inflate
    the re-encounter metric and bury the register head under a permanent
    self-collision. The notes FILE is rewritten wholesale each time (it is
    the delivery surface); the ledger records only the changes.
    """
    from ..falsification.engine import evaluate
    from ..falsification.predictions import seed_registry, SEED_SYSTEMS
    from .evidence_ledger import safe_append

    prev = {(e.get("dataset"), e.get("model"), e.get("quantity")): e
            for e in _load_notes()}
    notes = []
    for rec in seed_registry().all():
        for system_id in SEED_SYSTEMS.get(rec.system_class, []):
            try:
                r = evaluate(rec, system_id)
            except Exception as e:  # a broken prediction never sinks the lens
                notes.append({"ts": _now(), "dataset": system_id,
                              "quantity": rec.quantity, "model": rec.model,
                              "status": "not-recomputable",
                              "note": f"recomputation failed: {type(e).__name__}: {e}"})
                continue
            agree = not r.is_anomaly
            note = (f"published {r.model} predicts {r.quantity} = "
                    f"{r.predicted:.4g} {r.units} for {system_id}; recomputed "
                    f"from our data: {r.observed:.4g} (±{r.sigma_obs:.2g}; "
                    f"{r.delta_sigma:.1f}σ from prediction; named systematics "
                    f"bound {r.systematic_bound_total:.3g}) -> "
                    f"{'AGREE' if agree else 'DISAGREE'}")
            entry = {"ts": _now(), "dataset": system_id,
                     "quantity": r.quantity, "model": r.model,
                     "status": "agree" if agree else "disagree",
                     "delta_sigma": round(r.delta_sigma, 3), "note": note}
            notes.append(entry)
            old = prev.get((system_id, r.model, rec.quantity))
            changed = (old is None
                       or old.get("status") != entry["status"]
                       or abs(float(old.get("delta_sigma") or 0)
                              - entry["delta_sigma"]) > 0.01)
            if changed:
                safe_append("calibration", entry["status"], dataset=system_id,
                            statistic=r.quantity, value=round(r.delta_sigma, 4),
                            claim=note[:400],
                            detail=None if old is None else
                            f"changed from {old.get('status')} "
                            f"({old.get('delta_sigma')})")
    if write and notes:
        EVOLVED_PROGRAMS.mkdir(parents=True, exist_ok=True)
        NOTES.write_text(json.dumps(
            {"generated": _now(), "notes": notes}, indent=2) + "\n")
    return notes


def _load_notes() -> list:
    try:
        return json.loads(NOTES.read_text()).get("notes", [])
    except Exception:
        return []


def notes_head(name: str, n: int = 3) -> list:
    """Head of the calibration notes for a proposer session on dataset
    ``name`` — this dataset's notes first, then any others. Defensive: []."""
    notes = _load_notes()
    if not notes:
        return []
    scored = []
    for i, e in enumerate(notes):
        if e.get("status") == "not-recomputable":
            continue
        rank = (0 if e.get("dataset") == name else 1, -i)
        scored.append((rank, e))
    scored.sort(key=lambda t: t[0])
    return [f'({e["status"]}) {e["note"]}' for _, e in scored[:n]]


def verdicts_changed_by_notes() -> dict:
    """The 90-day number: verdicts whose outcome flipped after a calibration
    note was delivered on their dataset.

    Reads the verdict log in order; a claim's outcome is its gate2/both_pass
    path. A flip = the same claim text later returning a DIFFERENT outcome,
    with at least one note on that dataset delivered between the two verdicts.
    """
    notes = _load_notes()
    note_ts_by_ds = {}
    for e in notes:
        ds = e.get("dataset")
        if ds:
            note_ts_by_ds.setdefault(ds, []).append(e.get("ts"))
    changed, deliveries = [], sum(len(v) for v in note_ts_by_ds.values())
    history = {}   # claim -> last (ts, outcome)
    if VERDICT_LOG.exists():
        for line in VERDICT_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            claim, ds = rec.get("claim"), rec.get("dataset")
            if not claim:
                continue
            g2 = (rec.get("gate2") or {}).get("status")
            outcome = ("novel" if rec.get("both_pass")
                       else g2 if g2 in ("known", "known-cache-only")
                       else "not-significant" if not (rec.get("gate1") or {}).get("pass")
                       else "rejected")
            prev = history.get(claim)
            history[claim] = (rec.get("ts"), outcome, ds)
            if not prev or prev[1] == outcome:
                continue
            ts_notes = note_ts_by_ds.get(ds) or note_ts_by_ds.get(prev[2]) or []
            between = [t for t in ts_notes
                       if prev[0] and t and prev[0] <= t
                       and (rec.get("ts") and t <= rec.get("ts"))]
            if between:
                changed.append({"claim": claim[:90], "dataset": ds,
                                "was": prev[1], "now": outcome,
                                "note_ts": between[0]})
    return {"notes_delivered": deliveries,
            "verdicts_changed_by_note": len(changed),
            "details": changed[:20],
            "caveat": "mechanical approximation: counts outcome flips between "
                      "retried verdicts with a note delivered in between; it "
                      "cannot attribute reasoning"}


def stats() -> dict:
    out = {"notes": len(_load_notes())}
    out.update(verdicts_changed_by_notes())
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "stats"
    if cmd == "recompute":
        notes = recompute()
        print(f"{len(notes)} calibration note(s) -> {NOTES}")
        for e in notes:
            print(f"  [{e['status']:9s}] {e['note'][:120]}")
    elif cmd == "notes":
        for line in notes_head("sdss_stars", n=10):
            print(" ", line)
    else:
        print(json.dumps(stats(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
