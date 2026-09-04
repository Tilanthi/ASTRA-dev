#!/usr/bin/env python3
"""heat72v — dual a3^BL evaluation on heat72w kappa-ladder landing (L141 §3, pre-committed).

Pre-committed criterion (m1-L141 §3, exchange 4c5da84): the kappa-side analytic a3
(heat72w contour-route U3, ladder-agreed) is evaluated against BOTH BL-side readings
at the UNCHANGED <=1 threshold:
    |a3_kappa - r_median|     <= 1    (r_median = 11.8713, prereg line 67 = grid 6th point r(eps=0.0082668, D=0.15))
    |a3_kappa - a3_identity|  <= 1    (a3_identity = 11.7007174, 7-s.f. stable, m2's identity route)
"If they ever disagree in verdict, that disagreement is itself the finding and reports first."

This script only parses the runner's output and applies the pre-stated arithmetic.
Run: python3 heat72v_dual_a3_eval.py  (after heat72w prints ALL COMPLETE)
"""
import re, sys, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heat72w_kappa_a3.out")
R_MEDIAN = "11.8713"        # prereg machine1-prereg-heat72-birth-locus.md line 67
A3_IDENTITY = "11.7007174"  # m2 identity route, 7-s.f. stable; L141 corrected spec


def mpval(tok):
    from mpmath import mp
    mp.dps = 30
    return mp.mpf(tok)


def main():
    text = open(OUT).read()
    rungs = re.findall(r"HEAT72W RUNG (\d+) COMPLETE: U3 = ([0-9.eE+-]+)", text)
    if not rungs:
        print("no completed rungs found — ladder not landed"); return 1
    print(f"rungs completed: {len(rungs)}")
    vals = []
    for n, v in rungs:
        print(f"  rung {n}: U3 = {v}")
        vals.append(mpval(v))
    if "ALL COMPLETE" not in text:
        print("WARNING: ladder not yet ALL COMPLETE — evaluation below is provisional")
    a3k = vals[-1] if len(vals) == 1 else sum(vals)/len(vals)
    # ladder-agreed value: mean of completed rungs (runner prints its own spread; we report per-rung too)
    from mpmath import mp
    spread = max(vals) - min(vals)
    print(f"\na3^kappa (ladder mean of {len(vals)} rungs) = {mp.nstr(a3k, 20)}   cross-rung spread = {mp.nstr(spread, 5)}")
    d1 = abs(a3k - mpval(R_MEDIAN))
    d2 = abs(a3k - mpval(A3_IDENTITY))
    v1, v2 = d1 <= 1, d2 <= 1
    print(f"\nDUAL EVALUATION (pre-committed L141 §3, threshold unchanged <=1):")
    print(f"  |a3_kappa - r_median|    = |{mp.nstr(a3k,8)} - {R_MEDIAN}| = {mp.nstr(d1, 6)}   -> {'PASS' if v1 else 'FAIL'}")
    print(f"  |a3_kappa - a3_identity| = |{mp.nstr(a3k,8)} - {A3_IDENTITY}| = {mp.nstr(d2, 6)}   -> {'PASS' if v2 else 'FAIL'}")
    if v1 == v2:
        print(f"  verdict: BOTH {'PASS' if v1 else 'FAIL'} (agree)")
    else:
        print(f"  VERDICT: the two readings DISAGREE — per L141 §3, the disagreement is itself")
        print(f"  the finding and reports first. No silent resolution.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
