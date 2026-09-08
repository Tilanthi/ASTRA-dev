"""eureka_clock.py — the external clock (Phase 1 completion, Eureka plan
2026-08-30).

"A scheduled fresh session whose only job is to reopen the log and ask
whether anything new bears on anything old. The model cannot wake itself."

The clock runs as its own LaunchAgent (``com.astra.eureka-clock``, daily
09:41) in a FRESH process that starts from the record — not from any
session's memory. Each firing:

  1. reopens the ledger, the verdict log and the register (rebuilt live);
  2. takes everything NEW since the last firing (bounded by line offsets
     stamped into the previous clock entry, not by trusting timestamps);
  3. asks the one question — does anything new bear on anything old? —
     mechanically: new evidence (new verdicts, new anomalies, new attacks,
     new calibration notes) is cross-matched against the register's unsolved
     problems and past calibration notes on shared datasets, statistics and
     claim content;
  4. every genuine collision is written as a ledger ``register`` /
     ``re-encountered`` entry, which (a) counts toward the 90-day
     "re-encounters per week" number and (b) bumps that register entry to
     the head of the next proposer session's injection with the pairing
     spelled out — the arranged collision, made explicit;
  5. refreshes the lifetime significance correction and the register file.

Never raises, always exits 0 (a clock that crash-loops is worse than a clock
that misses a day: every failure is recorded as a ``clock`` entry instead).

Run:
    python3 -m astra_core.scientific_discovery.evolved_analysis.eureka_clock          # fire once
    python3 -m astra_core.scientific_discovery.evolved_analysis.eureka_clock --status # show past firings
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .evidence_ledger import (LEDGER, VERDICT_LOG, REGISTER,
                              read_ledger, build_register, recompute_reported,
                              safe_append)

# Bounds: the cross-match must stay cheap and the write volume capped even if
# a very long gap leaves a huge "new" pool.
MAX_NEW_VERDICTS = 5000
MAX_REENCOUNTERS_PER_RUN = 25

_STOP = {"with", "that", "this", "from", "have", "than", "then", "when", "where",
         "which", "their", "there", "these", "those", "into", "over", "under",
         "between", "among", "higher", "lower", "greater", "smaller", "sample",
         "using", "based", "data", "dataset", "value", "values", "relation",
         "correlation", "effect", "shows", "show", "strong", "weak"}


def _tokens(text) -> set:
    """Content tokens for claim comparison: words ≥4 chars plus numbers."""
    if not text:
        return set()
    words = {w for w in re.findall(r"[a-z][a-z0-9_]{3,}", str(text).lower())
             if w not in _STOP}
    numbers = set(re.findall(r"\d+\.?\d*", str(text)))
    return words | numbers


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _count_lines(path: Path) -> int:
    try:
        with path.open() as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _tail_records(path: Path, offset: int, cap: int) -> list:
    """Parsed JSON records beyond ``offset`` lines. On the first firing
    (offset 0) the newest ``cap`` records are taken, not the oldest; if a
    rotation shrank the file below the stored offset, the whole current file
    counts as new."""
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return []
    if offset > len(lines):          # rotated: treat current file as new
        offset = 0
    if offset == 0:                  # first firing: newest, bounded
        offset = max(0, len(lines) - cap)
    if offset >= len(lines):
        return []
    out = []
    for line in lines[offset:offset + cap]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def last_clock() -> dict | None:
    """The most recent clock entry (kind=clock), or None."""
    last = None
    for e in read_ledger():
        if e.get("kind") == "clock":
            last = e
    return last


# --------------------------------------------------------------------------- #
# the one question: does anything new bear on anything old?                    #
# --------------------------------------------------------------------------- #

def _old_pool() -> list:
    """Everything OLD worth colliding against: register entries + past
    calibration notes (a note is a standing claim about a dataset)."""
    old = []
    for e in build_register(write=False):
        ctx = e.get("context") or {}
        old.append({"key": ctx.get("claim") or e.get("reason"),
                    "dataset": ctx.get("dataset"),
                    "statistic": ctx.get("statistic"),
                    "kind": f"register:{e.get('stream')}"})
    for e in read_ledger():
        if e.get("kind") == "calibration":
            old.append({"key": e.get("claim") or e.get("statistic"),
                        "dataset": e.get("dataset"),
                        "statistic": e.get("statistic"),
                        "kind": "calibration-note"})
    seen, dedup = set(), []
    for o in old:
        if o["key"] and o["key"] not in seen:
            seen.add(o["key"])
            dedup.append(o)
    return dedup


def _new_pool() -> list:
    """Everything NEW since the last firing (by stamped line offsets)."""
    new = []
    prev = last_clock() or {}
    lo = int(prev.get("ledger_lines_seen", 0) or 0)
    lv = int(prev.get("verdict_lines_seen", 0) or 0)
    for e in _tail_records(LEDGER, lo, MAX_NEW_VERDICTS):
        if e.get("kind") in ("clock", "register", "conduct"):
            continue          # bookkeeping is not evidence
        claim = e.get("claim")
        if not claim:
            continue
        new.append({"claim": claim, "dataset": e.get("dataset"),
                    "statistic": e.get("statistic"), "kind": e.get("kind")})
    for rec in _tail_records(VERDICT_LOG, lv, MAX_NEW_VERDICTS):
        claim = rec.get("claim")
        if not claim:
            continue
        new.append({"claim": claim, "dataset": rec.get("dataset"),
                    "statistic": None, "kind": "verdict"})
    return new


def _matches(new: dict, old: dict) -> str | None:
    """Why the pair collides, or None. Mechanical and explainable."""
    if str(new.get("claim")) == str(old.get("key")):
        return None          # identity is not a collision (first-run self-match)
    if (new.get("dataset") and old.get("dataset")
            and new["dataset"] == old["dataset"]
            and new.get("statistic") and old.get("statistic")
            and new["statistic"] == old["statistic"]):
        return (f"same dataset ({new['dataset']}) and statistic "
                f"({new['statistic']})")
    tn, to = _tokens(new.get("claim")), _tokens(old.get("key"))
    j = _jaccard(tn, to)
    same_ds = bool(new.get("dataset") and old.get("dataset")
                   and new["dataset"] == old["dataset"])
    if same_ds and (j >= 0.25 or len(tn & to) >= 3):
        return f"same dataset ({new['dataset']}); overlapping claim content"
    if j >= 0.45:
        return "strong claim-content overlap across datasets"
    return None


def run_clock() -> dict:
    """One firing. Never raises."""
    try:
        return _run_clock()
    except Exception as e:  # a broken clock still records that it broke
        try:
            safe_append("clock", "clock-failed",
                        detail=f"{type(e).__name__}: {str(e)[:200]}")
        except Exception:
            pass
        return {"disposition": "clock-failed",
                "error": f"{type(e).__name__}: {str(e)[:200]}"}


def _run_clock() -> dict:
    # calibration lens first: freshly recomputed published numbers join the
    # old pool this same firing can collide new evidence against
    lens = 0
    try:
        from .calibration_lens import recompute as lens_recompute
        lens = len(lens_recompute(write=True) or [])
    except Exception as e:
        try:
            safe_append("note", "calibration-lens-failed",
                        detail=f"{type(e).__name__}: {str(e)[:160]}")
        except Exception:
            pass
    register = build_register(write=True)          # reopen the register
    old = _old_pool()
    new = _new_pool()

    pairs, seen_pairs = [], set()
    for o in old:
        for n in new:
            if not o.get("key"):
                continue
            why = _matches(n, o)
            if not why:
                continue
            pk = (o["key"], n.get("claim"))
            if pk in seen_pairs:
                continue
            seen_pairs.add(pk)
            pairs.append((o, n, why))
            if len(pairs) >= MAX_REENCOUNTERS_PER_RUN:
                break
        if len(pairs) >= MAX_REENCOUNTERS_PER_RUN:
            break

    for o, n, why in pairs:
        safe_append("register", "re-encountered",
                    claim=o["key"], dataset=o.get("dataset"),
                    bears_on=o["key"],
                    new_evidence=str(n.get("claim"))[:200],
                    new_kind=n.get("kind"),
                    detail=f"new {n.get('kind')} evidence "
                           f"'{str(n.get('claim'))[:90]}...' bears on this: "
                           f"{why} — what do they share?")

    # rebuild so the re-encounter counts are stamped into the register file
    register = build_register(write=True)

    correction = {}
    try:
        r = recompute_reported(write=True)
        correction = {"examined": r["n_reported_significances_examined"],
                      "lifetime_trials": r["n_lifetime_trials"],
                      "still_below_bar": r["n_still_below_nominal_bar"]}
    except Exception as e:
        correction = {"error": f"{type(e).__name__}: {str(e)[:120]}"}

    summary = {
        "disposition": "clock-ran",
        "n_new_evidence": len(new),
        "n_calibration_notes": lens,
        "register_entries": len(register),
        "n_reencounters": len(pairs),
        "reencounters": [{"old": str(o.get("key"))[:90],
                          "new": str(n.get("claim"))[:90], "why": why}
                         for o, n, why in pairs[:10]],
        "correction": correction,
        "ledger_lines_seen": _count_lines(LEDGER),   # stamped AFTER appends
        "verdict_lines_seen": _count_lines(VERDICT_LOG),
    }
    safe_append("clock", "clock-ran", detail=json.dumps(summary)[:1500],
                **{k: summary[k] for k in
                   ("n_new_evidence", "register_entries", "n_reencounters",
                    "ledger_lines_seen", "verdict_lines_seen")})
    return summary


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--status":
        c = last_clock()
        print(json.dumps(c, indent=2) if c else "no clock firing recorded yet")
        return 0
    summary = run_clock()
    print(json.dumps(summary, indent=2)[:2500])
    return 0                      # a clock never fails the agent


if __name__ == "__main__":
    sys.exit(main())
