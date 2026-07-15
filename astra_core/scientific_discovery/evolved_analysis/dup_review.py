"""dup_review.py — surface NEAR-duplicate discoveries for HUMAN REVIEW.

The hard dedup (``discovery_store.dedup_key``) merges only EXACT (effect,
p-value) matches. Two legitimately-distinct findings can share |effect| with
p-values within an order of magnitude (e.g. two QSO-curvature relations both at
|effect|=0.742, p 7.7e-141 vs 1.7e-140). These are NOT auto-merged (a different
computation gives a different p-value), but a human should decide whether they're
the same phenomenon. This tool lists such groups — it never modifies a store.

Run (token not required — pure local read):
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.dup_review
"""
from __future__ import annotations

import sys
from pathlib import Path

from discovery_store import load_records, near_duplicate_groups


def main() -> int:
    seen = set()
    recs = []
    for name in ("evolved_discoveries.json", "genuine_discoveries.json"):
        p = Path.home() / ".astra_persistent" / name
        if not p.exists():
            continue
        for r in load_records(p):
            v = r.get("verification") or {}
            key = (v.get("program_hash"), v.get("effect"), v.get("pvalue"))
            if key in seen:
                continue
            seen.add(key)
            recs.append(r)

    groups = near_duplicate_groups(recs)
    if not groups:
        print(f"[dup_review] no near-duplicate groups among {len(recs)} records.")
        return 0

    nflagged = sum(len(g[1]) for g in groups)
    print(f"[dup_review] {len(groups)} near-duplicate group(s) covering "
          f"{nflagged}/{len(recs)} records — for human review (NOT merged):")
    for i, (eff, rs) in enumerate(groups, 1):
        print(f"\n--- group {i}: |effect| ~ {eff}, {len(rs)} record(s) ---")
        for r in rs:
            v = r.get("verification") or {}
            try:
                e = f"{abs(float(v.get('effect', 0))):.3f}"
                pv = f"{float(v.get('pvalue', 0)):.2e}"
            except (TypeError, ValueError):
                e, pv = "?", "?"
            print(f"  {str(r.get('timestamp', ''))[:19]}  |effect|={e}  p={pv}  "
                  f"ph={v.get('program_hash')}")
            print(f"    {str(r.get('abstract', ''))[:128]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
