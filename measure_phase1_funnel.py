"""measure_phase1_funnel.py — before/after funnel for the Phase-1 discovery-
performance change (v14.9: correlation_seeds + explored_themes / novelty-steering).

Partitions ~/.astra_persistent/evolved_programs/claim_verdicts.jsonl (non-seed
verdicts only) by timestamp and prints the gate1/gate2/novel funnel for each side,
a 95% Wilson CI on the after gate1-pass rate, a per-dataset breakdown, and a
one-line verdict. Designed to be re-run as the after-sample grows (the supervisor
appends new-code verdicts), so the gate1-pass number firms up over time.

Cutoffs (override with --before-cut / --after-cut):
  BEFORE = ts < 2026-07-15T18:31   (pre-1a baseline; the 1a commit landed 18:31:11)
  AFTER  = ts >= 2026-07-15T19:24  (clean new-code: the controlled burst + the
                                    supervisor's ongoing runs. The 13 gaia_variables
                                    verdicts at 19:00-19:12 are excluded as
                                    possibly-old-code.)

Usage:
  python3 measure_phase1_funnel.py
  python3 measure_phase1_funnel.py --after-cut 2026-07-15T19:24:00
"""
from __future__ import annotations

import argparse
import collections
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EA = HERE / "astra_core" / "scientific_discovery"
sys.path.insert(0, str(EA))
from evolved_analysis.predictions import load_verdicts            # noqa: E402
from evolved_analysis.improvement_loop import failure_class       # noqa: E402

DEFAULT_BEFORE = "2026-07-15T18:31"
DEFAULT_AFTER = "2026-07-15T19:24:00"
DEFAULT_FIX = "2026-07-15T20:14:48"  # commit 64faa17 (correlation_seeds fix) took effect
BASELINE_GATE1PASS = 25.2  # %, from the pre-1a N=745 sample


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h) * 100, min(1.0, c + h) * 100


def funnel(xs: list) -> dict:
    n = len(xs)
    if n == 0:
        return {"n": 0}
    c = collections.Counter(failure_class(x) for x in xs)
    g1 = sum(1 for x in xs if (x.get("gate1") or {}).get("pass"))
    novel = sum(1 for x in xs if x.get("both_pass"))
    return {
        "n": n,
        "gate1_fail": c.get("gate1_fail", 0),
        "gate2_known": c.get("gate2_known", 0),
        "novel_emit": c.get("novel_emit", 0),
        "g1pass": g1,
        "g1pass_pct": g1 / n * 100,
        "novel_pct": novel / n * 100,
        "novel_of_g1pass": novel / max(g1, 1) * 100,
    }


def show(label: str, f: dict):
    if f["n"] == 0:
        print(f"  {label}: (no verdicts)")
        return
    n = f["n"]
    print(f"  {label} (N={n}):")
    print(f"    gate1_fail   {f['gate1_fail']:4d}  {f['gate1_fail']/n*100:5.1f}%")
    print(f"    gate2_known  {f['gate2_known']:4d}  {f['gate2_known']/n*100:5.1f}%")
    print(f"    novel_emit   {f['novel_emit']:4d}  {f['novel_emit']/n*100:5.1f}%")
    print(f"    GATE1 pass   {f['g1pass']:4d}  {f['g1pass_pct']:5.1f}%")
    print(f"    novel/pass   {f['novel_of_g1pass']:.0f}%")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before-cut", default=DEFAULT_BEFORE)
    ap.add_argument("--after-cut", default=DEFAULT_AFTER)
    ap.add_argument("--fix-cut", default=DEFAULT_FIX)
    args = ap.parse_args()

    rows = [x for x in load_verdicts() if (x.get("label") or "") != "seed"]
    before = [x for x in rows if x.get("ts", "") < args.before_cut]
    orig = [x for x in rows if args.after_cut <= x.get("ts", "") < args.fix_cut]
    fix = [x for x in rows if x.get("ts", "") >= args.fix_cut]

    bf, of, ff = funnel(before), funnel(orig), funnel(fix)
    print("=" * 72)
    print(f"PHASE-1 FUNNEL  before<{args.before_cut} | orig[{args.after_cut},"
          f"{args.fix_cut}) | fix>={args.fix_cut}")
    print("=" * 72)
    show("BEFORE (pre-1a baseline)   ", bf)
    show("ORIG   (1a/1b/1c old seeds)", of)
    show("FIX    (1a/1b/1c +seed fix)", ff)

    # Measure the FIX partition once it has data; until then fall back to ORIG.
    if ff["n"]:
        target, label, target_rows = ff, "FIX", fix
    else:
        target, label, target_rows = of, "ORIG (fix sample still empty)", orig
    if target["n"]:
        lo, hi = wilson(target["g1pass"], target["n"])
        spans = lo <= BASELINE_GATE1PASS <= hi
        print(f"\n  {label} gate1-pass 95% CI: {lo:.1f}% .. {hi:.1f}%   "
              f"(baseline {BASELINE_GATE1PASS:.1f}% -> "
              f"{'CI still spans baseline' if spans else 'CI EXCLUDES baseline'})")
        byds = collections.defaultdict(list)
        for x in target_rows:
            byds[x.get("dataset", "?")].append(x)
        if byds:
            print(f"\n  {label} by dataset:")
            for ds in sorted(byds):
                xs = byds[ds]
                g = sum(1 for x in xs if (x.get("gate1") or {}).get("pass"))
                dlo, dhi = wilson(g, len(xs))
                print(f"    {ds:22s} N={len(xs):3d}  gate1-pass {g/len(xs)*100:5.1f}% "
                      f"(CI {dlo:.0f}-{dhi:.0f})")
        upper = hi
        if ff["n"] == 0:
            verdict = (f"FIX sample empty (fix-cut {args.fix_cut}); supervisor hasn't run an "
                       f"episode since. ORIG gate1-pass {of.get('g1pass_pct', 0):.1f}%.")
        elif ff["n"] >= 150:
            verdict = (f"FIX N={ff['n']} >= 150: FIRM. gate1-pass {ff['g1pass_pct']:.1f}% vs "
                       f"{BASELINE_GATE1PASS:.1f}% baseline.")
        elif upper < 32:
            verdict = (f"FIX N={ff['n']}: CI upper {upper:.1f}% < 32% -> rules out a >~7pp "
                       f"improvement (seed fix did NOT meaningfully raise gate1-pass).")
        else:
            verdict = (f"FIX N={ff['n']}: directional (CI {lo:.0f}-{hi:.0f}); keep accumulating.")
        print(f"\n  VERDICT: {verdict}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
