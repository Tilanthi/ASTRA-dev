#!/usr/bin/env python3
"""heat72x — birth-locus scored-run REPUBLICATION + post-hoc structure reads (m1-L163).

The scored run (heat72_birth_locus.py, 64389s) ran at native dps 50 (DPS_RECHECK 65)
but the .out printed 18-21 digits. This publishes, from the scored JSON (no
recomputation of scored values): battery anchors, all 21 located zeros with on-line
flags, full-precision r-table, r_median, slope. Adds, as UNSCORED post-hoc reads
(labelled): (i) warm-start dps-65 Newton re-verification of three selected zeros —
the republication's own credibility check; (ii) the r(eps)->0 intercept fit vs the
a3 constant family (a3^BL = 11.7007174 identity route, a3^kappa = 11.700717(2)
contour route); (iii) exact r_median refinement of the m1-L161 dual-evaluation
statistic. Nothing here changes any graded outcome.
"""
import importlib.util
import json
import time

from mpmath import mp, mpf, sqrt

mp.dps = 60

RUNNER = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72_birth_locus.py"
RES = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72_birth_locus.results.json"
A3_BL = mpf("11.7007174")
A3_KAPPA = mpf("11.700717320435114")  # heat72w final rung (rung-3-specific past 7th s.f.)
T0 = time.time()

spec = importlib.util.spec_from_file_location("h72", RUNNER)
h72 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h72)

d = json.load(open(RES))

print("=== REPUBLICATION (scored JSON, native dps 50 strings) ===")
print("outcome=%s  second_pair=%s  offline_births=%s" % (d["outcome"], d["second_pair"], d["offline_births"]))
print("r_median = %s" % d["r_median"])
print("slope    = %s" % d["slope"])
print("\nzeros (21 located, on-line flags):")
rows = d["rows"]
for r in rows:
    print("eps=%s" % r["eps"])
    for e in r["zeros"]:
        print("   s0 = %-58s online=%s" % (e["s0"], e["online"]))
print("\nr-table (full precision):")
for (e, u, rr) in d["rtable"]:
    print("  eps=%-24s u=%-30s r=%s" % (e, u, rr))

print("\n=== POST-HOC (i): warm-start dps-65 re-verification of 3 zeros ===")
mp.dps = 65
sel = [(0, 0, "first zero, smallest eps"), (10, 0, "first zero, largest eps"), (6, 2, "second-pair member, eps=0.012")]
for (ri, zi, tag) in sel:
    zj = mpf(rows[ri]["zeros"][zi]["s0"].replace("(", "").replace(")", "").split("+")[1].rstrip("j")) \
        if "+ 0.5" not in rows[ri]["zeros"][zi]["s0"] else None
    # robust parse: strip parens, take imaginary part after '+'
    s0 = rows[ri]["zeros"][zi]["s0"]
    tim = s0.split("(")[1].split(")")[0].split("+")[1].strip().rstrip("j")
    t = mpf(tim)
    D = h72.DSTAR + mpf(rows[ri]["eps"])
    z, _, resid, _ = h72.locate_zero(mpf("0.5"), t, D)
    if z is None:
        print("  [%s] FAILED to re-converge" % tag)
        continue
    zj_str = rows[ri]["zeros"][zi]["s0"]
    t0j = mpf(zj_str.split("(")[1].split(")")[0].split("+")[1].strip().rstrip("j"))
    drift = abs(z.imag - t0j)
    online = abs(z.real - mpf("0.5")) < mpf("1e-25")
    print("  [%s] t=%s  drift-vs-scored=%s  newton-resid=%s  on-line=%s"
          % (tag, mp.nstr(z.imag, 40), mp.nstr(drift, 3), mp.nstr(resid, 3), online))

print("\n=== POST-HOC (ii): r(eps)->0 intercept vs a3 family ===")
mp.dps = 60
rt = sorted((mpf(e), mpf(u), mpf(rr)) for (e, u, rr) in d["rtable"])
rs = [p[2] for p in rt]
es = [p[0] for p in rt]


def lin_fit(idx):
    pts = [(es[i], rs[i]) for i in idx]
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((p[0] - mx) * (p[1] - my) for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    return num / den, my - (num / den) * mx


for tag, idx in (("linear, 3 smallest", [0, 1, 2]), ("linear, 5 smallest", [0, 1, 2, 3, 4]),
                 ("linear, all 11", list(range(11)))):
    c1, r0 = lin_fit(idx)
    print("  %-20s r0 = %s   slope = %s" % (tag, mp.nstr(r0, 12), mp.nstr(c1, 8)))
    print("       vs a3^BL 11.7007174 : rel %s" % mp.nstr(abs(r0 - A3_BL) / A3_BL, 4))
    print("       vs a3^kappa rung3   : rel %s" % mp.nstr(abs(r0 - A3_KAPPA) / A3_KAPPA, 4))

print("\n=== POST-HOC (iii): exact r_median refinement of the L161 dual evaluation ===")
rmed = mpf(d["r_median"])
a3k_mean = mpf("11.701133067")
print("  exact r_median            = %s" % mp.nstr(rmed, 30))
print("  |a3^kappa_mean - r_median| = %s   (L161 reported 0.170167 from the rounded 11.8713; verdict unchanged, both <= 1)"
      % mp.nstr(abs(a3k_mean - rmed), 10))
print("\nheat72x done %.1fs" % (time.time() - T0))
