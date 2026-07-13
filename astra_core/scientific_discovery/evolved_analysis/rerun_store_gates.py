"""rerun_store_gates.py — retroactively re-run the genuine discovery store through
the corrected claim gates (Fixes 2-5) and quarantine the failures/unverifiables.

WHY
  The 2026-07-12 record-8 audit showed stored claims had *in-sample-only*,
  *un-Bonferroni-corrected* statistics, and some were trivial colour identities.
  The fixes exist (``claim_gates.py``: Fix 3 triviality, Fix 4 narrated-vs-measured
  consistency, Fix 5 Bonferroni; Fix 2 holdout-on-test lives in
  ``claim_eval_worker.py``) but until now NO stored record had been checked against
  them. This tool does that batch check:

    * every record whose program source is recoverable is RE-EXECUTED on the real
      SDSS split (the same one the search used) and re-gated with the CURRENT gates;
    * survivors are kept with a refreshed ``verification`` block (and, Fix 1, their
      source is propagated into the genuine record so future re-runs need no join);
    * records that fail any gate, and records whose source cannot be recovered, are
      moved to ``quarantined_discoveries.json`` with a machine reason.

Source recovery
  Genuine store records do NOT carry ``program_source`` (the consumer only recently
  began forwarding it). The ``evolved_discoveries.json`` staging file DOES (Fix 1),
  so we join by ``program_hash``. Records with no recoverable source (the early
  in-sample-only claims) are quarantined as unverifiable — they cannot be
  re-checked and their headline statistics are known-inflated.

This re-run is READ-ONLY by default (prints the classification + would-be outcome);
pass ``--apply`` to rewrite the stores. It never calls ``bump_family_counter`` — the
live search's multiple-testing accounting is not disturbed; the Bonferroni threshold
uses the current read-only ``family_size()``.

Run (decoupled, like run_claim_search):
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.rerun_store_gates [--apply]
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .claim_task import parse_claim, gate1_significant, PMAX
from .claim_gates import (triviality_check, consistency_check,
                          holdout_distinct_check, family_size)
from .run_claim_search import gate1_run, _program_hash

logger = logging.getLogger(__name__)

# Load discovery_store by file path so we do NOT trigger astra_core's heavy
# __init__ chain (deadlock history, CLAUDE.md v5-v7). discovery_store is stdlib-only.
_DS_PATH = Path(__file__).resolve().parent.parent / "discovery_store.py"
_spec = importlib.util.spec_from_file_location("astra_discovery_store", _DS_PATH)
discovery_store = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(discovery_store)  # type: ignore[union-attr]

PERSIST_DIR = discovery_store.PERSIST_DIR
GENUINE_PATH = PERSIST_DIR / "genuine_discoveries.json"
EVOLVED_PATH = PERSIST_DIR / "evolved_discoveries.json"
QUARANTINE_PATH = PERSIST_DIR / "quarantined_discoveries.json"

# Buckets returned by classify_record.
KEEP = "keep"            # Phase-1 pipeline (out-of-sample) — not a claim
SURVIVES = "survives"    # source-bearing claim that passes every current gate
QUARANTINE = "quarantine"  # fails a gate, or source unrecoverable


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().isoformat()


def _verification_hash(rec: Dict[str, Any]) -> Optional[str]:
    return (rec.get("verification") or {}).get("program_hash")


def _refresh_verification(rec: Dict[str, Any], metrics: Dict[str, Any],
                          verdict: Dict[str, Any], source: Optional[str]) -> Dict[str, Any]:
    """Return a copy of *rec* with a refreshed ``verification`` block reflecting the
    re-run, plus (Fix 1) the persisted ``program_source`` so the record is
    independently reproducible."""
    new = copy.deepcopy(rec)
    v = dict(new.get("verification") or {})
    v["effect"] = metrics.get("effect")
    v["pvalue"] = metrics.get("pvalue")
    v["effect_insample"] = metrics.get("effect_insample")
    v["pvalue_insample"] = metrics.get("pvalue_insample")
    v["held_out_split"] = "test"
    prev_gate = v.get("gate") or {}
    v["gate"] = {
        "gate1_real_data": "pass",
        "gate2_novelty": prev_gate.get("gate2_novelty", "novel"),
        "triviality": "pass",
        "consistency": "pass",
        "holdout": "pass",
        "bonferroni_pmax": verdict["bonferroni_pmax"],
        "family_size": verdict["family_size"],
    }
    v["rerun"] = {
        "at": _now_iso(),
        "gate1": verdict["g1_reason"],
        "holdout": verdict["hold_reason"],
        "triviality": verdict["triv_reason"],
        "consistency": verdict["cons_reason"],
        "metrics": {k: metrics.get(k) for k in
                    ("effect", "pvalue", "effect_insample", "pvalue_insample")},
    }
    new["verification"] = v
    if source:
        new["program_source"] = source  # Fix 1: persist source in the genuine record
    return new


def classify_record(rec: Dict[str, Any],
                    source_map: Dict[str, str],
                    evolved_by_hash: Dict[str, Dict[str, Any]],
                    family: int,
                    corrected_pmax: float,
                    gate1_runner: Callable[[str, int], Dict[str, Any]],
                    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]],
                               str, Optional[str]]:
    """Classify one genuine-store record against the current gates.

    Returns ``(bucket, genuine_rec, evolved_rec, reason, gate_failed)``:
      * KEEP      — genuine_rec is the original record; evolved_rec is its evolved
                    twin (unchanged) if present; not re-gated.
      * SURVIVES  — genuine_rec + evolved_rec are refreshed with the re-run verdict.
      * QUARANTINE— genuine_rec/evolved_rec are None; reason/gate_failed explain why.
    """
    v = rec.get("verification") or {}
    metric = v.get("metric_name")
    h = v.get("program_hash")

    # Phase-1 pipeline (photo-z): out-of-sample, not a (CLAIM, run_claim) artifact.
    # Keep without re-running the claim gates (gate1_run requires `def run_claim`).
    if metric == "sigma_NMAD":
        return KEEP, rec, evolved_by_hash.get(h), "phase-1 pipeline (out-of-sample)", None

    src = source_map.get(h)
    if not src:
        return (QUARANTINE, None, None,
                "no persisted program_source (in-sample-only claim); unverifiable",
                "no_source")

    # Re-execute on the identical real split the search used.
    metrics = gate1_runner(src, 42)
    if not isinstance(metrics, dict):
        metrics = {"effect": 0.0, "pvalue": 1.0, "error": "runner returned non-dict"}
    effect = metrics.get("effect", 0.0)
    try:
        effect = float(effect)
    except (TypeError, ValueError):
        effect = 0.0

    g1_ok, g1_reason = gate1_significant(metrics, pmax=corrected_pmax)
    hold_ok, hold_reason = holdout_distinct_check(metrics)  # Fix 6
    triv_ok, triv_reason = triviality_check(src, effect)
    claim = parse_claim(src) or v.get("claim") or rec.get("abstract") or ""
    cons_ok, cons_reason = consistency_check(claim, metrics)

    verdict = {
        "bonferroni_pmax": corrected_pmax,
        "family_size": family,
        "g1_reason": g1_reason,
        "hold_reason": hold_reason,
        "triv_reason": triv_reason,
        "cons_reason": cons_reason,
    }

    if not g1_ok:
        return QUARANTINE, None, None, g1_reason, "gate1"
    if not hold_ok:
        return QUARANTINE, None, None, hold_reason, "holdout"
    if not triv_ok:
        return QUARANTINE, None, None, triv_reason, "triviality"
    if not cons_ok:
        return QUARANTINE, None, None, cons_reason, "consistency"

    genuine_rec = _refresh_verification(rec, metrics, verdict, src)
    evolved_twin = evolved_by_hash.get(h)
    evolved_rec = (_refresh_verification(evolved_twin, metrics, verdict, src)
                   if evolved_twin else None)
    return SURVIVES, genuine_rec, evolved_rec, (
        f"survives re-run: {g1_reason} | {hold_reason} | {triv_reason} | "
        f"{cons_reason}"), None


def rerun_all(apply: bool = False,
              gate1_runner: Callable[[str, int], Dict[str, Any]] = gate1_run,
              ) -> Dict[str, Any]:
    """Re-gate every record in the genuine store. Returns a summary dict.

    When *apply* is False (default) nothing is written — this is a dry run."""
    genuine_recs = discovery_store.load_records(GENUINE_PATH)
    evolved_recs = discovery_store.load_records(EVOLVED_PATH)
    source_map = {}
    evolved_by_hash: Dict[str, Dict[str, Any]] = {}
    for r in evolved_recs:
        h = _verification_hash(r)
        if h:
            evolved_by_hash[h] = r
            if r.get("program_source"):
                source_map[h] = r["program_source"]

    family = family_size()
    corrected_pmax = max(PMAX / family, 1e-300)

    kept_genuine = []
    kept_evolved = []
    quarantined = []
    counts = {"keep": 0, "survives": 0, "quarantine": 0,
              "quarantine_by_gate": {}}

    print("=" * 92)
    print(f"RE-RUN THROUGH CORRECTED GATES  (family_size={family}, "
          f"bonferroni_pmax={corrected_pmax:.2e}, apply={apply})")
    print("=" * 92)
    print(f"{'#':>3} {'bucket':<10} {'gate':<13} {'metric':<14} {'|eff|':>7} "
          f"{'p':>10}  claim")
    print("-" * 92)

    for i, rec in enumerate(genuine_recs):
        bucket, g_rec, e_rec, reason, gate_failed = classify_record(
            rec, source_map, evolved_by_hash, family, corrected_pmax, gate1_runner)
        counts[bucket] += 1
        v = (g_rec or rec).get("verification") or {}
        eff = v.get("effect")
        pv = v.get("pvalue")
        claim = (v.get("claim") or rec.get("abstract") or "")
        eff_s = f"{abs(float(eff)):.3f}" if isinstance(eff, (int, float)) else "—"
        pv_s = f"{float(pv):.1e}" if isinstance(pv, (int, float)) else "—"
        gate_s = gate_failed or "—"
        print(f"{i:>3} {bucket:<10} {gate_s:<13} {str(v.get('metric_name')):<14} "
              f"{eff_s:>7} {pv_s:>10}  {claim[:46]}")
        if bucket == QUARANTINE:
            counts["quarantine_by_gate"][gate_failed] = (
                counts["quarantine_by_gate"].get(gate_failed, 0) + 1)
            quarantined.append({
                "quarantined_at": _now_iso(),
                "gate_failed": gate_failed,
                "reason": reason,
                "program_hash": _verification_hash(rec),
                "original_record": rec,
            })
        else:
            kept_genuine.append(g_rec)
            if e_rec is not None:
                kept_evolved.append(e_rec)
            elif bucket == KEEP:
                # keep the evolved twin unchanged if it exists
                twin = evolved_by_hash.get(_verification_hash(rec))
                if twin:
                    kept_evolved.append(twin)

    print("-" * 92)
    print(f"keep={counts['keep']}  survives={counts['survives']}  "
          f"quarantine={counts['quarantine']}  "
          f"(by gate: {counts['quarantine_by_gate']})")

    if not apply:
        print("\n(dry run — no files written. Re-run with --apply to rewrite the stores.)")
        return {**counts, "apply": False,
                "kept": len(kept_genuine), "quarantined": len(quarantined)}

    # Validate every kept record still satisfies the chokepoint invariant.
    bad = [r for r in kept_genuine if not discovery_store.has_machine_verification(r)]
    if bad:
        raise RuntimeError(
            f"{len(bad)} kept record(s) fail has_machine_verification — refusing to write")

    discovery_store.save_bucket(GENUINE_PATH, kept_genuine)
    discovery_store.save_list(EVOLVED_PATH, kept_evolved)
    QUARANTINE_PATH.write_text(json.dumps(quarantined, indent=2, default=str))
    print(f"\n[applied] genuine={len(kept_genuine)} evolved={len(kept_evolved)} "
          f"quarantined={len(quarantined)} -> {QUARANTINE_PATH.name}")
    return {**counts, "apply": True,
            "kept": len(kept_genuine), "quarantined": len(quarantined)}


def main():
    ap = argparse.ArgumentParser(
        description="Re-run the genuine discovery store through the corrected claim gates.")
    ap.add_argument("--apply", action="store_true",
                    help="actually rewrite the stores (default: dry run)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    rerun_all(apply=args.apply)


if __name__ == "__main__":
    main()
