"""discovery_review.py — rank novel claims for human review (Phase 3a) + record
human confirmation (Phase 3b).

The autonomous pipeline emits "best-effort novel" claims (both-gate survivors) whose
novelty is machine-judged, not human-confirmed. This surfaces the strongest by real
|effect|, joins each to its Gate-2 novelty reasoning (from the verdict log), and
lets a human record a confirm/reject verdict. The confirmation rate then feeds the
capability index's Discovery signal (a real, human-judged outcome metric).

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.discovery_review [--top 10]
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.discovery_review mark <program_hash> confirmed|rejected
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PERSIST = Path.home() / ".astra_persistent"
EVOLVED = PERSIST / "evolved_discoveries.json"
GENUINE = PERSIST / "genuine_discoveries.json"
VERDICT_LOG = PERSIST / "evolved_programs" / "claim_verdicts.jsonl"
CONFIRMED = PERSIST / "evolved_programs" / "confirmed_discoveries.jsonl"


def _novel_claims():
    recs = []
    for f in (EVOLVED, GENUINE):
        if f.exists():
            try:
                d = json.loads(f.read_text())
                recs += d if isinstance(d, list) else d.get("discoveries", [])
            except Exception:
                pass
    # join Gate-2 reasoning from the verdict log by program_hash
    reasoning = {}
    try:
        if VERDICT_LOG.exists():
            for l in VERDICT_LOG.read_text().splitlines():
                if not l.strip():
                    continue
                v = json.loads(l)
                ph = (v.get("gate1") or {}).get("reason") and v.get("program_hash")
                if v.get("program_hash"):
                    reasoning[v["program_hash"]] = (v.get("gate2") or {}).get("reasoning", "")
    except Exception:
        pass
    seen, out = set(), []
    for r in recs:
        if not isinstance(r, dict):
            continue
        v = r.get("verification") or {}
        g = v.get("gate") or {}
        ph = v.get("program_hash")
        if not ph or ph in seen:
            continue
        if g.get("gate1_real_data") == "pass" and g.get("gate2_novelty") == "novel":
            seen.add(ph)
            try:
                eff = abs(float(v.get("effect", 0)))
            except (TypeError, ValueError):
                eff = 0.0
            out.append((eff, r, reasoning.get(ph, "")))
    out.sort(key=lambda x: -x[0])
    return out


def _review(top: int = 10) -> int:
    claims = _novel_claims()
    print(f"[review] {len(claims)} machine-verified novel claim(s); "
          f"top {min(top, len(claims))} by |effect|:")
    for i, (eff, r, why) in enumerate(claims[:top], 1):
        v = r.get("verification") or {}
        ds = r.get("dataset") or v.get("dataset") or "?"
        print(f"\n#{i}  |effect|={eff:.3f}  p={v.get('pvalue')}  ds={ds}  ph={v.get('program_hash')}")
        print(f"    {str(r.get('abstract', ''))[:150]}")
        if why:
            print(f"    why-novel: {str(why)[:130]}")
    print("\nConfirm/reject: python -m evolved_analysis.discovery_review "
          "mark <program_hash> confirmed|rejected")
    return 0


def _mark(ph: str, verdict: str) -> int:
    if verdict not in ("confirmed", "rejected"):
        print("verdict must be 'confirmed' or 'rejected'")
        return 1
    CONFIRMED.parent.mkdir(parents=True, exist_ok=True)
    with CONFIRMED.open("a") as f:
        f.write(json.dumps({"program_hash": ph, "verdict": verdict,
                            "ts": datetime.now().isoformat(timespec="seconds")}) + "\n")
    print(f"[review] marked {ph} -> {verdict}")
    return 0


def confirmation_rate():
    """Phase 3b: confirmed / (confirmed+rejected) over human-reviewed novel claims,
    or None if nothing reviewed yet."""
    if not CONFIRMED.exists():
        return None
    rows = [json.loads(l) for l in CONFIRMED.read_text().splitlines() if l.strip()]
    if not rows:
        return None
    c = sum(1 for r in rows if r.get("verdict") == "confirmed")
    total = len(rows)
    return {"confirmed": c, "reviewed": total,
            "rate": round(c / total, 3) if total else None}


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "mark" and len(args) >= 3:
        return _mark(args[1], args[2])
    top = int(args[0]) if args and args[0].isdigit() else 10
    return _review(top)


if __name__ == "__main__":
    sys.exit(main())
