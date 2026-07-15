"""verify_discovery_holdout.py — generic in-sample / hold-out / multiple-testing
audit for a genuine ASTRA discovery.

Replaces the record-8-specific script (record 8, program_hash f3ccafa9f6, was
removed in the 2026-07-13 store re-gate, so the old audit targeted a record that
no longer exists). This version audits ANY current survivor.

WHAT IT DOES (no side effects on the verdict log / family counter / novelty cache):
  1. Pick a genuine_discoveries.json record (--record INDEX, default = latest
     Phase-2 claim; or --hash PROGRAM_HASH).
  2. Cross-reference program_hash -> program_source in evolved_discoveries.json.
  3. Re-run the claim's ACTUAL code on the real train/eval/test splits via the
     pipeline's own sandboxed evaluator (gate1_run) and compare the freshly
     computed (effect, p, effect_insample) to the STORED values -> reproducibility.
  4. Hold-out integrity: is the stored headline effect genuinely held out
     (distinct from the in-sample effect, with plausible shrinkage)?  [Fix 6 spirit]
  5. Multiple-testing: does the stored p-value still clear the Bonferroni-corrected
     threshold for the current search-family size?  [Fix 5 spirit]

HONEST LIMITS
  - The family counter is cumulative across all time, so the Bonferroni bar here is
    the CURRENT (conservative) one, not the one at emit time. A record that survives
    today's larger family would also have survived at emit time.
  - Bonferroni corrects the p-threshold; it does not fully remove the optimism from
    the search selecting on the held-out statistic (a second-order residual).
  - The re-run executes the stored claim source inside the ASTRA sandbox
    (sandbox-exec: no network, temp-writes-only) — same path the search used.

Usage:
  python3 verify_discovery_holdout.py                 # audit the latest claim
  python3 verify_discovery_holdout.py --record -3     # audit a specific index
  python3 verify_discovery_holdout.py --hash 0e0f610ee5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EA = HERE / "astra_core" / "scientific_discovery"
sys.path.insert(0, str(EA))
from evolved_analysis.run_claim_search import gate1_run, ENTRY_POINT, PMAX  # noqa: E402
from evolved_analysis.claim_gates import bonferroni_pmax, family_size        # noqa: E402

PERSIST = Path.home() / ".astra_persistent"
GENUINE = PERSIST / "genuine_discoveries.json"
EVOLVED = PERSIST / "evolved_discoveries.json"


def _load(path: Path) -> list:
    d = json.load(open(path))
    return d if isinstance(d, list) else d.get("discoveries", d.get("records", []))


def find_source(program_hash: str):
    """Cross-reference a genuine record's hash to its program_source in the
    evolved store (the genuine store persists only the hash, not the code)."""
    if not program_hash:
        return None
    for r in _load(EVOLVED):
        if (r.get("verification") or {}).get("program_hash") == program_hash:
            return r.get("program_source")
    return None


def candidate_sources(preferred: str) -> list:
    """Datasets to try for the re-run, in order: the stored one first, then every
    registered data-lake dataset. Records emitted via the data-lake path do not
    always persist their dataset in the verification block, so a KeyError on the
    first try means 'wrong dataset' and we move to the next."""
    seen, out = set(), []
    for s in [preferred, "legacy"]:
        if s and s not in seen:
            out.append(s); seen.add(s)
    try:
        from evolved_analysis.data_lake import list_datasets
        for d in list_datasets():
            nm = getattr(d, "name", None)
            if nm and nm not in seen:
                out.append(nm); seen.add(nm)
    except Exception:
        pass
    return out


def pick_default(gn: list):
    """Latest genuine record that is a Phase-2 claim (has run_claim source + an
    effect). Falls back to the last record if none qualify."""
    for i in range(len(gn) - 1, -1, -1):
        v = gn[i].get("verification") or {}
        ph = v.get("program_hash")
        src = find_source(ph) or ""
        has_effect = ((v.get("real_data_result") or {}).get("effect") is not None
                      or v.get("effect") is not None)
        if f"def {ENTRY_POINT}" in src and has_effect:
            return i
    return len(gn) - 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", type=int, default=None,
                    help="index into genuine_discoveries.json (default: latest claim)")
    ap.add_argument("--hash", help="program_hash to audit (overrides --record)")
    args = ap.parse_args()

    gn = _load(GENUINE)
    if not gn:
        sys.exit("genuine_discoveries.json has no records")
    if args.hash:
        rec = next((r for r in gn if (r.get("verification") or {}).get("program_hash")
                   == args.hash), None)
        if rec is None:
            sys.exit(f"no genuine record with hash {args.hash}")
        idx = gn.index(rec)
    else:
        idx = pick_default(gn) if args.record is None else args.record
        rec = gn[idx]

    v = rec.get("verification") or {}
    rdr = v.get("real_data_result") or {}
    ph = v.get("program_hash")
    ds = v.get("data_source") or rdr.get("data_source") or "legacy"
    stored_eff = rdr.get("effect", v.get("effect"))
    stored_p = rdr.get("pvalue", v.get("pvalue"))
    stored_ins = rdr.get("effect_insample", v.get("effect_insample"))
    summary = rdr.get("summary") or ""

    print("=" * 78)
    print("DISCOVERY HOLD-OUT / MULTIPLE-TESTING AUDIT")
    print(f"record index={idx}  hash={ph}  stored dataset={ds}")
    print("=" * 78)
    print(f"title  : {(rec.get('title') or '')[:90]}")
    print(f"summary: {summary}")
    print(f"stored : effect={stored_eff}  in-sample={stored_ins}  p={stored_p}")
    print()

    # 1. Reproducibility re-run (no side effects). Try the stored dataset first,
    # then every data-lake dataset, until one runs without a column error.
    src = find_source(ph)
    drift = None
    if not src:
        print("program_source NOT FOUND in evolved_discoveries.json — cannot re-run.")
    elif f"def {ENTRY_POINT}" not in src:
        print(f"program_source has no `def {ENTRY_POINT}` (Phase-1 program, not a claim). "
              "Skipping re-run.")
    else:
        print(f"re-running claim via sandboxed gate1_run (seed=42), trying datasets "
              f"{candidate_sources(ds)} ...")
        fresh, used = None, None
        for cs in candidate_sources(ds):
            f = gate1_run(src, seed=42, source=cs)
            err = str(f.get("error", ""))
            # A KeyError means 'column not in this dataset' -> wrong dataset, try next.
            if f.get("error") and "KeyError" in err:
                continue
            fresh, used = f, cs
            break
        if used != ds and used is not None:
            print(f"  NOTE: stored dataset '{ds}' did not carry the claim's columns; "
                  f"re-run succeeded on '{used}'.")
        if fresh is None or fresh.get("error"):
            print(f"  re-run ERROR on every dataset: {fresh.get('error') if fresh else 'none ran'}")
        else:
            fe, fp, fi = fresh.get("effect"), fresh.get("pvalue"), fresh.get("effect_insample")
            print(f"  fresh ({used}): effect={fe}  in-sample={fi}  p={fp}")
            if stored_eff is not None and fe is not None:
                drift = abs(fe - stored_eff)
                tag = "MATCH (reproducible)" if drift < 1e-6 else "DRIFT (investigate)"
                print(f"  |fresh - stored| effect = {drift:.4e}  -> {tag}")
    print()

    # 2. Hold-out integrity (stored numbers — Fix 6 spirit)
    print("HOLD-OUT INTEGRITY (stored)")
    if stored_eff is not None and stored_ins is not None:
        distinct = abs(stored_eff - stored_ins)
        denom = max(abs(stored_ins), 1e-12)
        retain = abs(stored_eff) / denom * 100
        if distinct < 1e-9:
            verdict = "FLAG: effect == in-sample (NOT held out; Fix 6 would reject)"
        elif retain > 100:
            verdict = (f"NOTE: held-out |effect| LARGER than in-sample ({retain:.0f}%) — "
                       "unusual; check the split")
        elif retain > 99.5:
            verdict = f"WARN: held-out ~= in-sample ({retain:.0f}%) — suspiciously little shrinkage"
        else:
            verdict = f"OK: genuine hold-out (retains {retain:.0f}% of in-sample |effect|)"
        print(f"  |effect - effect_insample| = {distinct:.4e}  -> {verdict}")
    else:
        print("  (no in-sample effect stored)")
    print()

    # 3. Multiple-testing (Bonferroni over current cumulative family — Fix 5 spirit)
    print("MULTIPLE-TESTING (Bonferroni, current cumulative family)")
    fam = family_size()
    bpmax = bonferroni_pmax(PMAX)
    print(f"  family_size={fam}  bonferroni_pmax={bpmax:.2e}  (nominal PMAX={PMAX:.0e})")
    if stored_p is not None:
        ok = stored_p <= bpmax
        print(f"  stored p={stored_p:.2e}  ->  "
              f"{'SURVIVES correction' if ok else 'FLAG: does NOT survive correction'}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
