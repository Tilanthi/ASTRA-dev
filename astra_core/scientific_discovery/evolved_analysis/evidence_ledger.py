"""evidence_ledger.py — the permanent record of everything ever flagged (Phase 0
of the Eureka plan, 2026-08-29).

One query surface over everything ever flagged: every statistic tried, every
anomaly noticed, every verdict, every near-miss. It serves four purposes:

  1. the LIFETIME count of statistical trials, standing beside every claim
     (``claim_gates.bonferroni_pmax`` corrects within one search family; this
     module corrects across the system's whole operating lifetime — the "ten
     thousand looks" no single session can see);
  2. the REGISTER of unsolved problems, enumerated from three discard streams
     rather than remembered (quarantined near-misses; statistics that passed
     but the literature gate could not judge; anomalies that survived
     falsification yet failed validation);
  3. CALIBRATION notes and other non-claim observations that had nowhere to go;
  4. the record of CONDUCT (weirdest reading first, problems held open) and of
     formal abstentions ("not enough evidence" as a first-class outcome).

Design: the claim pipeline's verdict log (``claim_verdicts.jsonl``) already
records every claim trial with its p-value — it is the historical portion of
the tally and is COUNTED IN PLACE, never copied. ``evidence_ledger.jsonl``
holds everything else, append-only. New claim trials are counted through the
verdict log; new non-claim flags go to the ledger. No store is duplicated.

Stdlib-only on purpose (same rule as ``claim_gates.py``) so the sandboxed
worker can import it cheaply.

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.evidence_ledger stats
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.evidence_ledger trials
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.evidence_ledger register
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.evidence_ledger recompute [--n 100]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PERSIST = Path.home() / ".astra_persistent"
EVOLVED_PROGRAMS = PERSIST / "evolved_programs"
LEDGER = EVOLVED_PROGRAMS / "evidence_ledger.jsonl"
VERDICT_LOG = EVOLVED_PROGRAMS / "claim_verdicts.jsonl"
CONDUCT_LOG = EVOLVED_PROGRAMS / "conduct_log.jsonl"
QUARANTINE = PERSIST / "quarantined_discoveries.json"
REGISTER = EVOLVED_PROGRAMS / "unsolved_register.json"
CORRECTION_REPORT = EVOLVED_PROGRAMS / "lifetime_correction_report.json"

CODE_VERSION = "14.18"

# The ledger rotates at this size (same policy as the verdict log) so an
# autonomous loop can never fill the disk through the ledger.
LEDGER_CAP_BYTES = 20 * 1024 * 1024

# ---------------------------------------------------------------------------
# Append-only ledger core
# ---------------------------------------------------------------------------

_KINDS = {
    "trial",            # a statistical test from a pipeline not covered by the verdict log
    "abstention",       # formal "not enough evidence" outcome
    "calibration",      # recomputed published number vs our measurement
    "anomaly",          # noticed-but-unexplained observation
    "register",         # register lifecycle: entry added / explained / refuted
    "conduct",          # conduct-rule event (mirrored into conduct_log.jsonl)
    "visual",           # flag raised by a rendered-data inspection pass
    "foreign",          # candidate originated by a different model family
    "attack",           # fresh-attacker outcome on a finding (Phase 2 hard rule)
    "clock",            # external-clock run: reopened the log, what it found
    "note",             # anything else worth keeping, with a kind of its own
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")


def append(kind: str, disposition: str, *, dataset=None, statistic=None,
           value=None, pvalue=None, claim=None, program_hash=None,
           detail=None, **extra) -> dict:
    """Append one flagged observation. Returns the entry as written.

    The lifetime count at the moment of appending is stamped onto every entry
    with a p-value, so any number quoted later can be re-corrected without
    re-reading the whole history.
    """
    if kind not in _KINDS:
        raise ValueError(f"unknown ledger kind {kind!r}; expected one of {sorted(_KINDS)}")
    entry = {
        "ts": _now(),
        "kind": kind,
        "disposition": disposition,
        "code_version": CODE_VERSION,
    }
    for k, v in (("dataset", dataset), ("statistic", statistic), ("value", value),
                 ("pvalue", pvalue), ("claim", claim), ("program_hash", program_hash),
                 ("detail", detail)):
        if v is not None:
            entry[k] = v
    entry["n_trials_lifetime"] = lifetime_trials() + (1 if kind == "trial" else 0)
    if pvalue is not None:
        entry["pvalue_lifetime"] = correct_pvalue(pvalue, entry["n_trials_lifetime"])
    if extra:
        entry.update(extra)
    EVOLVED_PROGRAMS.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def _rotate_if_needed():
    """Rotate the ledger file at the cap (kept, same policy as the verdict log)."""
    try:
        if LEDGER.exists() and LEDGER.stat().st_size > LEDGER_CAP_BYTES:
            rot = LEDGER.with_suffix(".jsonl.1")
            try:
                rot.unlink()
            except OSError:
                pass
            LEDGER.rename(rot)
    except OSError:
        pass


def safe_append(kind: str, disposition: str, **kw):
    """Pipeline-safe append: never raises, returns the entry or None.

    The supervisor runs pipelines as subprocesses with stdout/stderr -> DEVNULL
    (same contract as ``run_claim_search._append_verdict_log``), so a raising
    hook would kill an episode silently. Hooks call this, never ``append``.
    """
    try:
        _rotate_if_needed()
        return append(kind, disposition, **kw)
    except Exception as e:  # never break a discovery loop over a logging failure
        sys.stderr.write(f"[evidence_ledger] append failed: {e}\n")
        return None


def read_ledger():
    """Yield ledger entries (newest last). Malformed lines are skipped and counted."""
    bad = 0
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                bad += 1
    if bad:
        sys.stderr.write(f"[evidence_ledger] warning: skipped {bad} malformed ledger line(s)\n")


# ---------------------------------------------------------------------------
# 1. Lifetime trial count and significance correction
# ---------------------------------------------------------------------------

def _verdict_log_trials():
    """Count verdict-log lines (the historical claim trials). Counted in place."""
    if not VERDICT_LOG.exists():
        return 0, 0
    n = distinct = 0
    claims = set()
    with VERDICT_LOG.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            n += 1
            c = rec.get("claim")
            if c:
                claims.add(c)
    return n, len(claims)


def lifetime_trials() -> int:
    """Total statistical trials in the system's lifetime.

    Every claim verdict ever logged (in place, via the verdict log) plus every
    ledger trial from pipelines that do not write the verdict log. Flagged
    anomalies count as trials too: an anomalous look is still a look, and the
    lifetime correction exists precisely to price the whole search.
    """
    n_verdict, _ = _verdict_log_trials()
    n_ledger = sum(1 for e in read_ledger() if e.get("kind") in ("trial", "anomaly"))
    return n_verdict + n_ledger


def distinct_claims() -> int:
    """Distinct claim texts ever tried (the less conservative correction base)."""
    v_claims = set()
    if VERDICT_LOG.exists():
        for line in VERDICT_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line).get("claim")
            except json.JSONDecodeError:
                continue
            if c:
                v_claims.add(c)
    l_claims = {e.get("claim") for e in read_ledger()
                if e.get("kind") == "trial" and e.get("claim")}
    return len(v_claims | l_claims)


def correct_pvalue(p: float, trials: int = None) -> float:
    """Lifetime multiple-testing correction: min(1.0, p * n_lifetime).

    A Bonferroni-style bound over every trial the system has ever run. This
    never replaces the family-level correction in claim_gates; it is reported
    beside it.
    """
    if p is None:
        return None
    n = lifetime_trials() if trials is None else trials
    return min(1.0, p * max(n, 1))


def recompute_reported(n: int = 100, write: bool = True) -> dict:
    """Recompute the last ``n`` REPORTED significances (promoted claims) against
    the full lifetime tally, and publish whatever changes.

    A "reported significance" is a claim that passed both gates (gate2 status
    'novel') — i.e. a number the system actually reported as a finding.
    """
    promoted = []
    if VERDICT_LOG.exists():
        for line in VERDICT_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (rec.get("gate2") or {}).get("status") != "novel":
                continue
            # F3(a) (2026-09-08): a both-gate passer that was blocked at the
            # chokepoint (attacker-killed, second-judge-known, duplicate,
            # store-write-failed) was never REPORTED — the verdict log now
            # says so via emitted=False, and this report must not assert a
            # report that never happened. Rows without the field (historical)
            # still count, as they always did.
            if rec.get("emitted") is False:
                continue
            promoted.append(rec)
    batch = promoted[-n:]
    n_lifetime, n_distinct = lifetime_trials(), distinct_claims()
    rows, changed = [], 0
    for rec in batch:
        p = (rec.get("gate1") or {}).get("pvalue")
        if p is None:
            continue
        p_raw = min(1.0, p)
        p_life = min(1.0, p * max(n_lifetime, 1))
        still = p_life <= 1e-3  # the nominal Gate-1 bar from claim_gates
        if p_life != p_raw:
            changed += 1
        rows.append({
            "ts": rec.get("ts"),
            "claim": rec.get("claim"),
            "program_hash": rec.get("program_hash"),
            "pvalue_raw": p,
            "pvalue_lifetime": p_life,
            "still_below_1e-3_bar": still,
        })
    report = {
        "generated": _now(),
        "code_version": CODE_VERSION,
        "n_lifetime_trials": n_lifetime,
        "n_distinct_claims": n_distinct,
        "n_reported_significances_examined": len(rows),
        "n_values_changed_by_correction": changed,
        "n_still_below_nominal_bar": sum(1 for r in rows if r["still_below_1e-3_bar"]),
        "rows": rows,
    }
    if write:
        CORRECTION_REPORT.write_text(json.dumps(report, indent=2) + "\n")
    return report


# ---------------------------------------------------------------------------
# 2. Register of unsolved problems (enumerated, never remembered)
# ---------------------------------------------------------------------------

# Dispositions that make a verdict-log record a "narrow gate failure": the
# statistics all passed but the literature gate could not confirm novelty
# (retrieval or the judge failed — a machine failure, not a physics verdict),
# or the judge found it known. "known-cache-only" (Phase 2, 2026-08-30): a
# cached known-verdict whose live-source check could not be completed — the
# dismissal is NOT accepted, so the claim stays an open problem here.
# "gate2-error" (2026-09-08): the check raised outright — same standing, it
# used to vanish without a register trace.
_NARROW_GATE2 = {"retrieval-failed", "judge-failed", "known-cache-only",
                 "gate2-error"}


def _stream_attacks():
    """Stream (d), F3 (2026-09-08): claims that WON the statistics and were
    then blocked at the promotion threshold by an empty-context adversarial
    check — fresh-attacker killed/not-runnable, or a second-family judge's
    abstract-entailed 'known'.

    These are the strongest dead lanes in the record (a real effect that
    failed re-attack), which is why build_register puts this stream FIRST:
    a claim blocked at promotion wins the claim-key dedup over a narrower
    reading and leads the proposer head. Recurrence prevention, not
    punishment — entries leave by explanation or refutation like any other,
    and the clock's re-encounter cross-match is the resurrection path when
    genuinely new evidence arrives."""
    out = []
    for e in read_ledger():
        if e.get("kind") != "attack":
            continue
        if e.get("disposition") not in ("killed", "not-runnable",
                                        "second-judge-known"):
            continue  # survived/suspect are markings, not blocks
        key = e.get("claim")
        if not key or key in _resolved_keys():
            continue
        out.append({
            "stream": "blocked-at-promotion",
            "gate_failed": f"attack:{e.get('disposition')}",
            "reason": e.get("detail") or e.get("disposition"),
            "quarantined_at": e.get("ts"),
            "context": {k: e.get(k) for k in ("claim", "dataset",
                                              "program_hash", "value",
                                              "disposition") if e.get(k) is not None},
        })
    return out


def _stream_quarantine():
    """Stream (b): quarantined near-misses, full original record attached."""
    out = []
    if QUARANTINE.exists():
        try:
            for rec in json.loads(QUARANTINE.read_text() or "[]"):
                out.append({
                    "stream": "quarantined-near-miss",
                    "gate_failed": rec.get("gate_failed"),
                    "reason": rec.get("reason"),
                    "quarantined_at": rec.get("quarantined_at"),
                    "context": rec.get("original_record"),
                })
        except (json.JSONDecodeError, TypeError):
            pass
    return out


def _stream_narrow_gate2():
    """Stream (c): statistics passed every check but the literature gate could
    not be judged (machine failure) — exactly the claims worth a second look."""
    out, seen = [], set()
    if VERDICT_LOG.exists():
        for line in VERDICT_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            g2 = rec.get("gate2") or {}
            if g2.get("status") not in _NARROW_GATE2:
                continue
            g1 = rec.get("gate1") or {}
            if not (g1.get("pass") and rec.get("triviality") and rec.get("consistency")
                    and rec.get("holdout")):
                continue
            key = rec.get("claim")
            if not key or key in seen:
                continue
            seen.add(key)
            out.append({
                "stream": "narrow-gate-failure",
                "gate_failed": f"gate2:{g2.get('status')}",
                "reason": g2.get("reasoning") or g2.get("status"),
                "quarantined_at": rec.get("ts"),
                "context": {
                    "claim": key,
                    "program_hash": rec.get("program_hash"),
                    "dataset": rec.get("dataset"),
                    "effect": g1.get("effect"),
                    "pvalue": g1.get("pvalue"),
                    "gate1_reason": g1.get("reason"),
                },
            })
    return out


def _stream_anomalies():
    """Stream (a): anomalies noticed and left unexplained (ledger kind=anomaly
    or kind=visual with no later explained/refuted entry), plus falsification-
    arm survivors that failed validation."""
    out = []
    for e in read_ledger():
        if e.get("kind") in ("anomaly", "visual") and e.get("disposition") not in ("explained", "refuted"):
            key = e.get("claim") or e.get("detail")
            if key in _resolved_keys():
                continue
            out.append({
                "stream": "unexplained-anomaly",
                "gate_failed": None,
                "reason": e.get("detail") or e.get("disposition"),
                "quarantined_at": e.get("ts"),
                "context": {k: e.get(k) for k in ("claim", "dataset", "statistic",
                                                  "value", "pvalue", "pvalue_lifetime") if e.get(k) is not None},
            })
    return out


def _resolved_keys() -> set:
    """Claims/details an explicit ledger entry has explained or refuted."""
    resolved = set()
    for e in read_ledger():
        if e.get("kind") == "register" and e.get("disposition") in ("explained", "refuted"):
            key = e.get("claim") or e.get("detail")
            if key:
                resolved.add(key)
    return resolved


def _reencounter_index() -> dict:
    """claim-key -> {count, last} over register/re-encountered ledger entries.

    The external clock writes a ``register``/``re-encountered`` entry each time
    NEW evidence collides with an OLD unsolved problem; this index surfaces
    those collisions beside the register entry so the next proposer session
    leads with the pairing (the arranged collision), not the bare claim.
    """
    idx: dict = {}
    for e in read_ledger():
        if e.get("kind") == "register" and e.get("disposition") == "re-encountered":
            k = e.get("claim") or e.get("bears_on")
            if not k:
                continue
            rec = idx.setdefault(k, {"count": 0, "last": None})
            rec["count"] += 1
            if e.get("ts"):
                rec["last"] = e.get("ts")
    return idx


def build_register(write: bool = True) -> list:
    """Materialise the register of unsolved problems from the four streams.

    Nothing leaves the register except by explanation or refutation (recorded
    as a ledger ``register`` entry), and only through the existing gates.
    Each entry carries its re-encounter count from the clock so collisions
    stay visible until the problem itself is resolved.
    """
    resolved = _resolved_keys()
    reenc = _reencounter_index()
    # attacks first (F3): a claim that passed the statistics AND failed an
    # adversarial check at the promotion threshold is the strongest open
    # problem, so it wins the context.claim dedup and leads the head.
    entries = (_stream_attacks() + _stream_quarantine() + _stream_narrow_gate2()
               + _stream_anomalies())
    dedup, seen = [], set()
    for e in entries:
        key = (e.get("context") or {}).get("claim") or e.get("reason")
        if key in resolved:
            continue
        if key and key in seen:
            continue
        seen.add(key)
        e["added_ts"] = _now()
        if key in reenc:
            e["reencounters"] = reenc[key]["count"]
            e["last_reencounter"] = reenc[key]["last"]
        dedup.append(e)
    if write:
        EVOLVED_PROGRAMS.mkdir(parents=True, exist_ok=True)
        REGISTER.write_text(json.dumps({"generated": _now(), "entries": dedup}, indent=2) + "\n")
    return dedup


def resolve_register(claim: str, disposition: str, detail: str = None):
    """Mark a register entry explained or refuted (append-only; the register is
    regenerated on next build without it)."""
    if disposition not in ("explained", "refuted"):
        raise ValueError("disposition must be 'explained' or 'refuted'")
    return append("register", disposition, claim=claim, detail=detail)


# ---------------------------------------------------------------------------
# 3. Formal abstention + rule-based confidence labels
# ---------------------------------------------------------------------------

# The escalation template: escalating past an abstention requires positive
# justification against THIS template, never a judgement call in the moment.
ESCALATION_TEMPLATE = {
    "abstained_because": "<which check could not be run or which evidence was absent>",
    "evidence_that_would_change_it": "<the concrete observation or query that would flip this to a verdict>",
    "cost_to_obtain": "<what it takes to get that evidence: query, compute, or data>",
    "who_can_obtain_it": "<model | operator>",
    "escalating_anyway_because": "<why this cannot wait for that evidence>",
}

ABSTAIN = "not-enough-evidence"


def abstain(what: str, template_fill: dict, *, dataset=None, claim=None) -> dict:
    """Record a formal abstention. The template must be filled — an abstention
    without a stated path to evidence is itself evidence-free."""
    missing = [k for k in ESCALATION_TEMPLATE if k not in template_fill]
    if missing:
        raise ValueError(f"escalation template incomplete: missing {missing}")
    return append("abstention", ABSTAIN, dataset=dataset, claim=claim,
                  detail=what, escalation=template_fill)


# Rule-based confidence labels: computed from which checks a finding actually
# passed, never composed freehand. Ordered weakest -> strongest; the label is
# the strongest class whose required checks all passed.
LABEL_RULES = [
    ("routine",                {"gate1"}),
    ("flagged",                {"gate1", "triviality", "consistency", "holdout"}),
    ("independently-reviewed", {"gate1", "triviality", "consistency", "holdout", "gate2"}),
    ("escalated",              {"gate1", "triviality", "consistency", "holdout", "gate2",
                                "fresh-attacker"}),
]


def confidence_label(passed_checks) -> str:
    """Assign the label by rule. ``passed_checks`` is any iterable of check
    names from LABEL_RULES (unknown names are ignored)."""
    passed = set(passed_checks)
    label = None
    for name, required in LABEL_RULES:
        if required <= passed:
            label = name
    if label is None:
        return "unverified"
    return label


def verdict_checks(rec: dict) -> set:
    """Extract the check names a verdict-log record actually passed."""
    checks = set()
    g1, g2 = rec.get("gate1") or {}, rec.get("gate2") or {}
    if g1.get("pass"):
        checks.add("gate1")
    for k in ("triviality", "consistency", "holdout"):
        if rec.get(k):
            checks.add(k)
    if (g2.get("status") == "novel") and g2.get("pass"):
        checks.add("gate2")
    return checks


# ---------------------------------------------------------------------------
# 4. Conduct log
# ---------------------------------------------------------------------------

CONDUCT_RULES = (
    "weirdest-reading-first",
    "one-problem-held-open",
    "nothing-closed-while-unexplained",
    "conduct-not-pipeline-surfaced-it",
)


def conduct(rule: str, detail: str, **extra) -> dict:
    """Record a conduct event. The rule must be one of CONDUCT_RULES."""
    if rule not in CONDUCT_RULES:
        raise ValueError(f"unknown conduct rule {rule!r}; expected one of {CONDUCT_RULES}")
    entry = {"ts": _now(), "rule": rule, "detail": detail, "code_version": CODE_VERSION}
    entry.update(extra)
    EVOLVED_PROGRAMS.mkdir(parents=True, exist_ok=True)
    with CONDUCT_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    # mirror into the ledger so conduct events are queryable with everything else
    return append("conduct", rule, detail=detail)


def read_conduct():
    if not CONDUCT_LOG.exists():
        return
    for line in CONDUCT_LOG.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def stats() -> dict:
    kinds = Counter(e.get("kind") for e in read_ledger())
    return {
        "lifetime_trials": lifetime_trials(),
        "distinct_claims": distinct_claims(),
        "ledger_entries": dict(kinds),
        "register_entries": len(build_register(write=False)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["stats", "trials", "register", "recompute"])
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args(argv)
    if a.cmd == "stats":
        print(json.dumps(stats(), indent=2))
    elif a.cmd == "trials":
        print(f"lifetime trials: {lifetime_trials()}  (distinct claims: {distinct_claims()})")
    elif a.cmd == "register":
        entries = build_register()
        print(f"register: {len(entries)} unsolved problems -> {REGISTER}")
        for e in entries[:10]:
            ctx = e.get("context") or {}
            print(f"  [{e['stream']}] {str(ctx.get('claim') or e.get('reason'))[:100]}")
        if len(entries) > 10:
            print(f"  ... and {len(entries) - 10} more")
    elif a.cmd == "recompute":
        r = recompute_reported(a.n)
        print(f"examined {r['n_reported_significances_examined']} reported significances "
              f"against {r['n_lifetime_trials']} lifetime trials")
        print(f"values changed by correction: {r['n_values_changed_by_correction']}; "
              f"still below the 1e-3 nominal bar: {r['n_still_below_nominal_bar']}")
        print(f"report -> {CORRECTION_REPORT}")


if __name__ == "__main__":
    main()
