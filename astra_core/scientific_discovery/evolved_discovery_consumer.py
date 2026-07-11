"""evolved_discovery_consumer.py — bridge evolved_analysis → ASTRA's discovery loop.

The auto-start discovery loop calls consume_evolved_discoveries(system) once per
cycle. It folds any NEW machine-verified records from
~/.astra_persistent/evolved_discoveries.json into the loop's in-memory store
(``system.genuine_discoveries``), shaped as ASTRA discoveries with
``validation.quality='GENUINE'`` / ``is_genuine=True`` (they ARE genuine — verified
by code execution on real data, unlike ASTRA's LLM-self-judged discoveries). The
loop's existing _save_discovery_store then persists them in the GENUINE bucket.

Design constraints (the loop has a deadlock/blocking history, CLAUDE.md v5–v7):
  - NEVER raises — every failure is logged and swallowed.
  - No locks, no blocking I/O, no network. One small file read + list append.
  - Idempotent across cycles AND service restarts: dedup by
    verification.program_hash against what is already in system.genuine_discoveries.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

EVOLVED_STORE = lambda: Path.home() / ".astra_persistent" / "evolved_discoveries.json"


def consume_evolved_discoveries(system: Any) -> int:
    """Fold new evolved discoveries into system.genuine_discoveries.

    Returns the number newly ingested (0 if none/new). Never raises."""
    try:
        path = EVOLVED_STORE()
        if not path.exists():
            return 0
        raw = path.read_text()
        records = json.loads(raw)
        if not isinstance(records, list) or not records:
            return 0

        # dedup against what the system already holds (survives restarts)
        existing = set()
        for d in getattr(system, "genuine_discoveries", []) or []:
            if not isinstance(d, dict) or d.get("source") != "evolved_analysis":
                continue
            v = d.get("verification") or {}
            h = v.get("program_hash") or d.get("timestamp")
            if h:
                existing.add(h)

        n = 0
        for r in records:
            if not isinstance(r, dict):
                continue
            v = r.get("verification") or {}
            h = v.get("program_hash") or r.get("timestamp")
            if not h or h in existing:
                continue
            existing.add(h)
            discovery = {
                "title": r.get("title", "Evolved analysis pipeline"),
                "abstract": r.get("abstract", ""),
                "discovery_type": r.get("discovery_type", "machine_verified_analysis"),
                "timestamp": r.get("timestamp"),
                # ASTRA-shaped validation: machine-verified => genuinely GENUINE
                "validation": {
                    "quality": "GENUINE",
                    "is_genuine": True,
                    "confidence": 1.0,
                    "note": "machine-verified by code execution on real archival "
                            "data (NOT LLM self-judgment)",
                },
                "verification": v,            # the proof (metric, held-out value, n, …)
                "source": "evolved_analysis",
            }
            system.genuine_discoveries.append(discovery)
            n += 1
            logger.info("[GenuineDiscovery] ✅ INGESTED machine-verified evolved "
                        "discovery: %s [%s=%s, TEST=%s]", discovery["title"][:60],
                        v.get("metric_name", "?"), v.get("eval_value", "?"),
                        v.get("held_out_test_value", "?"))
        if n:
            logger.info("[GenuineDiscovery] consumed %d new evolved discovery(ies) "
                        "into the genuine store.", n)
        return n
    except Exception as e:  # never let the consumer crash/block the discovery loop
        logger.warning("[GenuineDiscovery] consume_evolved_discoveries skipped: %s", e)
        return 0
