"""heat57 — out-of-sample verification of the COMPLETE pair-residual law at
BEAST's cycle-8 X-sites — the sites chosen to falsify the leading-term-only
claim. If the two-term law closes their failing cells, the corrected law is
authored with their falsification sites as its verification sites.

Anchors parsed from the committed relay file (trap #63), lines of the form
  | **X1** | 33, 34 | 109.0990733637230410199 | **1.930462179446634** | ...
and cross-checked against mp.zetazero before use (parse AND verify).

THE LAW UNDER TEST (this is the statement machine 2 declined to author and
invited machine 1 or 3 to write; this run is its out-of-sample check):

  With kappa_n the plain Taylor coefficients of ln[Xi(m0+z)/(z^2-d^2)] at 0
  and eps a pure midpoint error (d exact):

    even n:  D kappa_n = (n+1) kappa_{n+1} eps
                        + [ C(n+2,2) kappa_{n+2} - (n+1) d^{-(n+2)} ] eps^2
                        + O(eps^3)
    odd  n:  D kappa_n = [ (n+1) kappa_{n+1} - 2 d^{-(n+1)} ] eps
                        + C(n+2,2) kappa_{n+2} eps^2
                        + [ -(n+1)(n+2)/3 d^{-(n+3)} ] eps^3 ... (pair eps^3)
                        + O(eps^3)

  (translation channel = all orders from the non-pair zeros; pair channel =
  exact binomial series of the divisor; odd pair channel has NO eps^2 term.)

PRE-REGISTERED verdicts (committed with this docstring):
  V1  for every site and every n in {2,4,6,3,5}: |obs/pred - 1| <= 0.01 at
      rho = eps/d = 1e-6 and 1e-4.
  V2  the leading-term-only prediction (their falsified claim for even n =
      H1 alone; for odd n = eps-law alone) is reported alongside, to show
      exactly which cells it misses and the two-term law closes.
  V3  n=6 cells flagged wherever |obs/pred-1| > 0.01 at any rho (their H1
      diagnostic failed at n=6; we do not pre-claim those close).
Instrument: mp.taylor at dps 60, plain coefficients, same as T2h/heat51h.
Serial run — heat54 owns the 5-worker grant.
"""
import re
import subprocess
import json
import mpmath as mp

mp.mp.dps = 60

RELAY = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/"
         "machine2-cycle8-oos-falsification-2026-09-03-RELAY-BY-astra-pa.md")
RAW = open(RELAY).read()
ANCH = {}
for m in re.finditer(r"\|\s*\*\*(X\d)\*\*\s*\|\s*([\d,\s]+?)\s*\|\s*([\d.]+)\s*\|\s*\*\*([\d.]+)\*\*",
                     RAW):
    tag, zeros, m0, d = m.group(1), m.group(2), m.group(3), m.group(4)
    ANCH[tag] = dict(zeros=[int(v.strip()) for v in zeros.split(",")],
                     m0=mp.mpf(m0), d=mp.mpf(d))
print("== heat57: anchors parsed from relay (trap #63) + zetazero cross-check ==")
for tag, a in ANCH.items():
    z1 = mp.zetazero(a["zeros"][0]); z2 = mp.zetazero(a["zeros"][1])
    m0c = (z1.imag + z2.imag)/2; dc = (z2.imag - z1.imag)/2
    ok = abs(m0c - a["m0"]) < mp.mpf("1e-9") and abs(dc - a["d"]) < mp.mpf("1e-9")
    print(f"  {tag}: zeros {a['zeros']} m0={mp.nstr(a['m0'], 16)} d={mp.nstr(a['d'], 10)}"
          f"  zetazero-agrees={'YES' if ok else 'NO '}"
          f" (dm0={mp.nstr(abs(m0c-a['m0']), 2)}, dd={mp.nstr(abs(dc-a['d']), 2)})")
    assert ok, f"anchor mismatch at {tag} — do not proceed on unparsed values"

def coeffs(m0v, dv):
    def f(z, m0v=m0v, dv=dv):
        s = mp.mpf('0.5') + 1j*(m0v+z)
        Xi = mp.mpf('0.5')*s*(s-1)*mp.power(mp.pi, -s/2)*mp.gamma(s/2)*mp.zeta(s)
        return mp.log(Xi/(z**2 - dv**2))
    return mp.taylor(f, 0, 8)

def pred_delta(n, eps, base, d):
    # FIRST RUN BUG (kept as a record, trap #60-class): k1 for odd n omitted
    # the pair first-order term -2*eps*d^{-(n+1)}; the odd "ratio(2-term)"
    # column of the first run is therefore obs/translation-only = the
    # reciprocal of BEAST's cycle-8 sec.2 floor (X3 n=3: 7.702e4 vs their
    # 1.29836e-5 floor) - an accidental 3-for-3 cross-check of THEIR table,
    # and NOT a test of this law. Corrected below per the docstring law.
    k1 = ((n+1)*base[n+1] - (0 if n % 2 == 0 else 2*mp.power(d, -(n+1))))*eps
    k2 = (mp.binomial(n+2, 2)*base[n+2]
          - ((n+1)*mp.power(d, -(n+2)) if n % 2 == 0 else 0))*eps**2
    return k1, k2

RHO = [mp.mpf("1e-8"), mp.mpf("1e-6"), mp.mpf("1e-4"), mp.mpf("3e-4"), mp.mpf("1e-3")]
ORD = [2, 4, 6, 3, 5]
v1_fail, v3_flag, out = [], [], []
for tag, a in ANCH.items():
    d = a["d"]; base = coeffs(a["m0"], d)
    print(f"\n-- {tag}  d={mp.nstr(d, 8)}  (kappa3={mp.nstr(base[3], 6)}, "
          f"kappa5={mp.nstr(base[5], 6)}, kappa6={mp.nstr(base[6], 6)}, "
          f"kappa7={mp.nstr(base[7], 4)})")
    for rho in RHO:
        eps = rho*d
        sh = coeffs(a["m0"]+eps, d)
        for n in ORD:
            obs = sh[n]-base[n]
            k1, k2 = pred_delta(n, eps, base, d)
            r_full = obs/(k1+k2)
            lead = k1 if n % 2 == 0 else k1 - 2*mp.power(d, -(n+1))*eps
            # lead = leading-only: H1 (even) / eps-law (odd)
            lead_only = ((n+1)*base[n+1]*eps if n % 2 == 0
                         else -2*eps*mp.power(d, -(n+1)))
            r_lead = obs/lead_only
            rec = dict(site=tag, rho=float(rho), n=n,
                       obs=float(obs), r_full=float(r_full), r_lead=float(r_lead))
            out.append(rec)
            if abs(r_full-1) > 0.01 and rho in (mp.mpf("1e-6"), mp.mpf("1e-4")):
                v1_fail.append(rec)
            if n == 6 and abs(r_full-1) > 0.01:
                v3_flag.append(rec)
            print(f"   rho={mp.nstr(rho, 2):>6s} n={n}: obs={mp.nstr(obs, 3):>10s} "
                  f"ratio(2-term)={mp.nstr(r_full, 4):>8s}  "
                  f"ratio(lead-only)={mp.nstr(r_lead, 4):>8s}"
                  + ("  <-- V1 FAIL" if abs(r_full-1) > 0.01
                     and rho in (mp.mpf("1e-6"), mp.mpf("1e-4")) else ""))

json.dump(out, open("heat57_xsite_law.results.json", "w"), indent=1)
print(f"\npersisted heat57_xsite_law.results.json")
print(f"V1 (|ratio-1|<=0.01 at rho=1e-6,1e-4, all n): "
      f"{'PASS' if not v1_fail else 'FAIL x' + str(len(v1_fail))}")
for r in v1_fail:
    print(f"   V1 fail: {r['site']} n={r['n']} rho={r['rho']:.0e} ratio={r['r_full']:.4f}")
print(f"V3 n=6 flags at any rho: {len(v3_flag)}")
for r in v3_flag:
    print(f"   n=6 flag: {r['site']} rho={r['rho']:.0e} ratio={r['r_full']:.4f}")
