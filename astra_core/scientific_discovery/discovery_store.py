"""discovery_store.py — the single trust boundary for the genuine-discovery store.

Why this module exists
----------------------
ASTRA's idle-time discovery loop historically wrote *anything* it generated into
the persistent discovery store — including canned/template text (the
"STAN system initialized…" string) and textbook restatements. That violated the
project's prime directive ("NO FICTIONAL/SYNTHETIC DISCOVERIES").

The structural fix (see docs/superpowers/specs/2026-07-11-astra-autonomous-
discovery-rearchitecture-design.md) is a **single write chokepoint**: no record
enters any discovery store unless it carries a non-empty machine `verification`
block — i.e. an objective result produced by executing code on real data (an
AlphaEvolve-style EVALUATE), never free LLM text or a hardcoded constant.

Everything that writes a discovery — the evolved-discovery consumer, any future
emitter, the supervisor — must go through :func:`append_verified`.

This module is deliberately self-contained (stdlib only, no ``astra_core``
imports) so it can be used from contexts that must not trigger ASTRA's heavy
``__init__`` (deadlock history, CLAUDE.md v5–v7).
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

PERSIST_DIR: Path = Path.home() / ".astra_persistent"

# Every quality-segregated bucket file written by the legacy loop. The purge
# must touch all of them — fiction was scattered across incremental/textbook.
BUCKET_FILES: Dict[str, str] = {
    "genuine": "genuine_discoveries.json",
    "incremental": "incremental_advances.json",
    "textbook": "textbook_knowledge.json",
    "synthesis": "literature_synthesis.json",
    "unknown": "unknown_quality.json",
}
GENUINE_FILE = BUCKET_FILES["genuine"]
EVOLVED_FILE = "evolved_discoveries.json"


# --------------------------------------------------------------------------- #
# Verification check — the heart of the "fiction is impossible" invariant.    #
# --------------------------------------------------------------------------- #
def has_machine_verification(record: Any) -> bool:
    """True iff *record* carries a non-empty machine ``verification`` block.

    A machine verification is an objective result from executing code on real
    data (e.g. a held-out σ_NMAD, a balanced accuracy, a false-alarm
    probability) — NOT an LLM's self-judgement, a regex classifier score, or a
    hardcoded constant. Concretely we require a dict that contains at least one
    of the recognised evidence keys.

    The legacy fictional records have *no* ``verification`` key at all, so even
    the weakest check cleanly separates them from real ones; the key-list makes
    the intent explicit and survives schema drift.
    """
    if not isinstance(record, dict):
        return False
    v = record.get("verification")
    if not isinstance(v, dict) or not v:
        return False
    EVIDENCE_KEYS = (
        "program_hash",     # evolved_analysis programs (Phase 1)
        "metric_name",      # any machine metric was computed
        "held_out_test_value",
        "gate",             # Phase 2 two-gate result (verification/novelty)
        "real_data_result",
    )
    return any(v.get(k) not in (None, "", []) for k in EVIDENCE_KEYS)


def dedup_key(record: Dict[str, Any]) -> tuple:
    """Normalised dedup key: (rounded effect, p-value fingerprint) when both are
    present; else the program_hash/metric/timestamp fallback.

    Two regenerated emissions of the SAME finding differ in program_hash AND in
    claim wording, but the underlying ``run_claim`` computation is identical, so
    the held-out effect and p-value are identical too. Keying on (effect, p-value)
    collapses them reliably. (Claim-text was tried first, but regenerated dupes
    vary wording, so effect+p-value is the reliable fingerprint — the spirit of
    "claim text + effect" with the discriminator that actually catches real
    dupes.) Distinct findings have distinct effect/p-value, so they keep distinct
    keys."""
    v = record.get("verification") or {}
    try:
        eff = round(float(v.get("effect")), 4)
        pv = float(f"{float(v.get('pvalue')):.6g}")
        return ("fp", eff, pv)
    except (TypeError, ValueError):
        pass
    # Fallback: preserves prior behaviour + the program_hash-only regression test.
    return ("legacy", v.get("program_hash") or v.get("metric_name")
            or record.get("timestamp")
            or json.dumps(v, sort_keys=True, default=str))


def _verification_key(record: Dict[str, Any]) -> tuple:
    """Stable dedup key for a verified record (effect+p-value-normalised)."""
    return dedup_key(record)


# --------------------------------------------------------------------------- #
# Low-level load / save (handle both bucket-dict and bare-list formats).      #
# --------------------------------------------------------------------------- #
def _split(raw: Any) -> Tuple[List[Dict[str, Any]], bool]:
    """Return (records, is_bucket_dict) from a parsed file."""
    if isinstance(raw, list):
        return raw, False
    if isinstance(raw, dict):
        recs = raw.get("discoveries", [])
        return (recs if isinstance(recs, list) else []), True
    return [], False


def load_records(path: Path) -> List[Dict[str, Any]]:
    """Read a store file and return just its record list (either format)."""
    try:
        if not path.exists():
            return []
        with open(path, "r") as f:
            recs, _ = _split(json.load(f))
        return [r for r in recs if isinstance(r, dict)]
    except Exception as e:
        logger.warning("[DiscoveryStore] load_records(%s) failed: %s", path, e)
        return []


def _atomic_write(path: Path, text: str) -> None:
    """Write *text* to *path* atomically (temp file + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def save_bucket(path: Path, records: List[Dict[str, Any]]) -> None:
    """Write records in the legacy bucket-dict format (what the loop expects)."""
    from datetime import datetime  # local import; module stays import-light
    payload = {
        "discoveries": records,
        "statistics": {
            "total_count": len(records),
            "last_updated": datetime.now().isoformat(),
        },
    }
    _atomic_write(path, json.dumps(payload, indent=2, default=str))


def save_list(path: Path, records: List[Dict[str, Any]]) -> None:
    """Write records as a bare JSON list (the evolved_discoveries.json format)."""
    _atomic_write(path, json.dumps(records, indent=2, default=str))


# --------------------------------------------------------------------------- #
# The chokepoint.                                                             #
# --------------------------------------------------------------------------- #
def append_verified(path: Path, discovery: Dict[str, Any]) -> bool:
    """Append *discovery* to *path* iff it is machine-verified and not a dup.

    This is the ONLY function that should add a record to a discovery store.
    Returns True if appended, False if rejected (with a logged reason). Never
    raises — callers (including the discovery loop) depend on that.
    """
    try:
        if not isinstance(discovery, dict):
            logger.warning("[DiscoveryStore] rejected: not a dict")
            return False
        if not has_machine_verification(discovery):
            logger.warning(
                "[DiscoveryStore] REJECTED unverified record "
                "(no machine verification block): %s",
                str(discovery.get("title", ""))[:70],
            )
            return False

        records = load_records(path)
        key = _verification_key(discovery)
        existing = {_verification_key(r) for r in records if isinstance(r, dict)}
        if key in existing:
            return False  # idempotent — not an error

        records.append(discovery)
        # Preserve the file's existing shape.
        is_bucket = True
        try:
            with open(path, "r") as f:
                is_bucket = not isinstance(json.load(f), list)
        except Exception:
            is_bucket = True
        if is_bucket:
            save_bucket(path, records)
        else:
            save_list(path, records)
        logger.info(
            "[DiscoveryStore] ✓ appended verified record to %s: %s",
            path.name, str(discovery.get("title", ""))[:70],
        )
        return True
    except Exception as e:  # never let a store write crash the loop
        logger.warning("[DiscoveryStore] append_verified failed: %s", e)
        return False


# --------------------------------------------------------------------------- #
# Hydration + hygiene (used by the supervisor on startup and by the purge).   #
# --------------------------------------------------------------------------- #
def load_verified(path: Path) -> List[Dict[str, Any]]:
    """Load only the machine-verified records from *path* (for hydration)."""
    return [r for r in load_records(path) if has_machine_verification(r)]


def dedup_verified(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Dedup a record list by verification key, keeping first; return (kept, dropped)."""
    seen: set = set()
    kept: List[Dict[str, Any]] = []
    dropped = 0
    for r in records:
        k = _verification_key(r)
        if k in seen:
            dropped += 1
            continue
        seen.add(k)
        kept.append(r)
    return kept, dropped


def near_duplicate_groups(
        records: List[Dict[str, Any]],
        effect_round: int = 3,
        p_order: float = 1.0,
) -> List[Tuple[float, List[Dict[str, Any]]]]:
    """Surface NEAR-duplicate records for HUMAN REVIEW — never merges or removes.

    The hard dedup (``dedup_key``) merges only EXACT (effect, p-value) matches.
    Sometimes two legitimately-distinct findings share the same rounded |effect|
    with p-values within an order of magnitude (e.g. two QSO-curvature relations
    both at |effect|=0.742, p 7.7e-141 vs 1.7e-140). These are kept separate
    (different computation => different p), but they're worth a human eye in case
    they are the same phenomenon described twice.

    Clusters on ``round(|effect|, effect_round)`` and, within that, a chain on
    ``|log10(p_a) - log10(p_b)| <= p_order``. Returns one ``(effect, [records])``
    per cluster of >=2. Pure read — does not modify anything."""
    buckets: Dict[float, List[Tuple[Dict[str, Any], float]]] = {}
    for r in records:
        v = r.get("verification") or {}
        try:
            eff = round(abs(float(v.get("effect"))), effect_round)
            pv = float(v.get("pvalue"))
            if not (pv > 0):
                continue
        except (TypeError, ValueError):
            continue
        buckets.setdefault(eff, []).append((r, math.log10(pv)))
    groups: List[Tuple[float, List[Dict[str, Any]]]] = []
    for eff, items in buckets.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda x: x[1])
        cur = [items[0]]
        for it in items[1:]:
            if abs(it[1] - cur[-1][1]) <= p_order:
                cur.append(it)
            else:
                if len(cur) >= 2:
                    groups.append((eff, [r for r, _ in cur]))
                cur = [it]
        if len(cur) >= 2:
            groups.append((eff, [r for r, _ in cur]))
    return groups


def purge_file(path: Path, dry_run: bool = True) -> Dict[str, int]:
    """Remove unverified records and duplicates from one store file.

    Returns counts: ``{before, kept_verified, dropped_unverified, dropped_dup,
    after}``. In dry-run nothing is written.
    """
    records = load_records(path)
    before = len(records)
    verified = [r for r in records if has_machine_verification(r)]
    dropped_unverified = before - len(verified)
    kept, dropped_dup = dedup_verified(verified)
    counts = {
        "before": before,
        "kept_verified": len(verified),
        "dropped_unverified": dropped_unverified,
        "dropped_dup": dropped_dup,
        "after": len(kept),
    }
    verb = "would remove" if dry_run else "removed"
    logger.info(
        "[DiscoveryStore] purge %s: %s %d unverified + %d dup -> %d remain (%s)",
        path.name, verb, dropped_unverified, dropped_dup, len(kept),
        "dry-run" if dry_run else "applied",
    )
    if not dry_run and kept != records:
        try:
            is_bucket = True
            with open(path, "r") as f:
                is_bucket = not isinstance(json.load(f), list)
        except Exception:
            is_bucket = True
        if is_bucket:
            save_bucket(path, kept)
        else:
            save_list(path, kept)
    return counts


def purge_all(dry_run: bool = True) -> Dict[str, Dict[str, int]]:
    """Purge every bucket file. Returns per-file counts."""
    results: Dict[str, Dict[str, int]] = {}
    for label, name in BUCKET_FILES.items():
        p = PERSIST_DIR / name
        if p.exists():
            results[label] = purge_file(p, dry_run=dry_run)
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Purge unverified ASTRA discoveries.")
    ap.add_argument("--apply", action="store_true",
                    help="actually rewrite files (default: dry-run)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    res = purge_all(dry_run=not args.apply)
    print(json.dumps(res, indent=2))
