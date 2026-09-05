#!/usr/bin/env python3
"""heat83 — CENSUS PRE-FLIGHT, two-point displaced-anchor check (trap #117 as amended
by m2 CYCLE 27, accepted m1-L162). The frozen census runner (m1-L158 e926548) is
SEALED: no in-runner change is possible without breaking the freeze. The amendment-
compatible remedy is external: import the sealed runner's own Instrument, verify its
sha256 first, and assert TWO anchors before 22:23 —

  ANCHOR-0 (undisplaced): control cell k=0, phi=4/8, d=0  vs the committed selftest
      value 4.7342065079869e-6 (data/machine1_heat78c_selftest.out), tol 1e-12 rel.
  ANCHOR-D (displaced, DISCLOSED cell): k=0, phi=4/8, d=0.1 vs my heat79 value
      -6.9732465e-6 (independent code path) and m3's published pilot value
      -6.9732465e-6 (rel 1.75e-13 between them), tol 5e-8 rel — printing-precision
      limited at 8 digits; corruption-class defects (m2 c27, my heat81) move values
      by >= 1e-2 rel, three orders above this tolerance.

The conj-defect class m2 demonstrated is EXACT at d=0 and invisible to ANCHOR-0 and
to every internal identity; ANCHOR-D is the only point that catches it. This cell
FIRES (public since m3's L158 pilot, 1/25) — asserting it adds no disclosure.
Nothing here computes any blind cell. No seal is touched: the runner file is read
byte-identical and imported, never re-written.
"""
import hashlib
import importlib.util
import json
import sys
import time

RUNNER = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat78c_survivor_census.py"
RUNNER_SHA = "88ab08f82fc8d14453dc064ba292dd35dc57541a5acc45f0d0bf10cd2721cd53"
SELFTEST_CTL_K0 = "4.7342065079869e-6"      # committed selftest, 14 digits
HEAT79_K0_D01 = "-6.9732465e-6"             # mine (heat79) = m3 published, rel 1.75e-13
T0 = time.time()

h = hashlib.sha256(open(RUNNER, "rb").read()).hexdigest()
if h != RUNNER_SHA:
    sys.exit("RUNNER SEAL MISMATCH: got %s" % h)
print("runner seal verified %s" % h[:16], flush=True)

spec = importlib.util.spec_from_file_location("heat78c_sealed", RUNNER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)   # safe: main() is __main__-guarded

from mpmath import mp, mpf, im as mpim, zetazero  # noqa: E402
mp.dps = 45

mod.check_seals()

gdata = json.load(open(mod.GEN))["genomes"]
idt = json.load(open(mod.IDT))["seeds"]["s1/M8"]
genomes = gdata["s1/M8"]
phis, edges = zip(*[mod.make_phi(g) for g in genomes])
K = mp.matrix(8, 8)
G = mp.matrix(8, 8)
for i in range(8):
    for j in range(8):
        K[i, j] = mpf(idt["K_T200"][i][j])
        G[i, j] = mpf(idt["G_raw"][i][j])
inst = mod.Instrument(8, K, G, phis, edges)
print("M8 instrument built from sealed runner %.1fs" % (time.time() - T0), flush=True)

zeros = [mpf(str(mpim(zetazero(n)))) for n in range(1, 27)]
g_of = lambda k, phi8: zeros[k] + (zeros[k + 1] - zeros[k]) * mpf(phi8) / 8


def lam(k, phi8, d):
    KS = inst.K - inst.gram(zeros[k]) - inst.gram(zeros[k + 1]) + inst.quad_ex(g_of(k, phi8), mpf(d))
    vals, _ = inst.eig(KS)
    return vals[0]


a0 = lam(0, 4, 0)
ad = lam(0, 4, "0.1")
a0_ref, ad_ref = mpf(SELFTEST_CTL_K0), mpf(HEAT79_K0_D01)
r0 = abs(a0 - a0_ref) / abs(a0_ref)
rd = abs(ad - ad_ref) / abs(ad_ref)
print("ANCHOR-0  control k=0 d=0   : %s" % mp.nstr(a0, 15), flush=True)
print("           selftest ref     : %s   rel %s  (tol 1e-12)" % (SELFTEST_CTL_K0, mp.nstr(r0, 3)), flush=True)
print("ANCHOR-D  k=0 phi=4/8 d=0.1 : %s   [DISCLOSED cell, FIRES - public since m3 L158 pilot]"
      % mp.nstr(ad, 15), flush=True)
print("           heat79/m3 ref    : %s   rel %s  (tol 5e-8 printing-limited)" % (HEAT79_K0_D01, mp.nstr(rd, 3)), flush=True)

ok0, okd = r0 < 1e-12, rd < 5e-8
if ok0 and okd:
    print("PREFLIGHT PASS — two-point anchor holds on the sealed runner; census may launch (GREEN gate)")
else:
    print("PREFLIGHT FAIL — %s — census does NOT launch; outcome (c) declared instead"
          % ("ANCHOR-0" if not ok0 else "ANCHOR-D"))
print("heat83 done %.1fs" % (time.time() - T0))
sys.exit(0 if (ok0 and okd) else 1)
