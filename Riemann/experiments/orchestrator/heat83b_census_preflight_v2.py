#!/usr/bin/env python3
"""heat83b — CENSUS PRE-FLIGHT v2: three-anchor form (trap #117 amendment v2,
leg-coverage, m2-C28 §1.6). heat83's two anchors stand; this adds the
defect-diversity second displaced anchor and prints the code-path coverage
statement the amendment demands ("these anchors execute these code paths"):

  ANCHOR-0 (undisplaced)  control k=0, phi=4/8, d=0   vs committed selftest
                         4.7342065079869e-6, tol 1e-12 rel.
  ANCHOR-D (displaced #1) k=0, phi=4/8, d=0.1         vs heat79 = m3-L158
                         -6.9732465e-6, tol 5e-8 (8-digit print limit).
  ANCHOR-E (displaced #2) k=1, phi=4/8, d=0.2         vs heat80 = m3-L159
                         -0.0015429806 (cross-verified 2.88e-14), tol 5e-8.
                         The JUMP-crosser cell: deep negative (~1.5e-3, 220x
                         threshold) vs anchor-D's near-floor firing — the two
                         displaced anchors sit at opposite cancellation depths.

Leg-coverage analysis for the census instrument (single-leg design): every
displaced cell, whatever its (k, phi, delta), executes the ONE runner code
object inst.quad_ex(g_of(k,phi8), delta); the runner has no branch on
(k, phi, delta) that could select a different quad path, and gram() is a
pure function of its argument for every zero used (controls k=0..7 and both
anchor cells execute it). There is NO second independently displaceable leg
to cover; ANCHOR-D + ANCHOR-E execute the identical code object as all 418
displaced scored cells, at two depths. The derivation layer (outcome dispatch,
class assignment) is covered by the frozen selftest + controls-first rule +
the scored letter re-deriving classes from the raw JSON.

Nothing here computes any blind cell (all three anchors disclosed); no seal
is touched — the sealed runner is read byte-identical and imported.
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
HEAT80_K1_D02 = "-0.0015429806"             # mine (heat80) = m3-L159, rel 2.88e-14
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
ae = lam(1, 4, "0.2")
a0_ref, ad_ref, ae_ref = mpf(SELFTEST_CTL_K0), mpf(HEAT79_K0_D01), mpf(HEAT80_K1_D02)
r0 = abs(a0 - a0_ref) / abs(a0_ref)
rd = abs(ad - ad_ref) / abs(ad_ref)
re_ = abs(ae - ae_ref) / abs(ae_ref)
print("ANCHOR-0  control k=0 d=0   : %s" % mp.nstr(a0, 15), flush=True)
print("           selftest ref     : %s   rel %s  (tol 1e-12)" % (SELFTEST_CTL_K0, mp.nstr(r0, 3)), flush=True)
print("ANCHOR-D  k=0 phi=4/8 d=0.1 : %s   [DISCLOSED cell, FIRES - public since m3 L158 pilot]"
      % mp.nstr(ad, 15), flush=True)
print("           heat79/m3 ref    : %s   rel %s  (tol 5e-8 printing-limited)" % (HEAT79_K0_D01, mp.nstr(rd, 3)), flush=True)
print("ANCHOR-E  k=1 phi=4/8 d=0.2 : %s   [DISCLOSED cell, JUMP-crosser, FIRES - m3 L159 + heat80]"
      % mp.nstr(ae, 15), flush=True)
print("           heat80/m3 ref    : %s   rel %s  (tol 5e-8 printing-limited)" % (HEAT80_K1_D02, mp.nstr(re_, 3)), flush=True)
print("\ncoverage: all three anchors + every displaced scored cell execute the ONE code object\n"
      "  inst.quad_ex(g_of(k,phi8), delta); no (k,phi,delta)-branching exists in the runner;\n"
      "  gram() is pure in its argument (exercised at zeros[1..8] by controls k=0..7 and here\n"
      "  at zeros[1..3]). Single-leg design: no second independently displaceable leg to cover.\n"
      "  Derivation layer -> frozen selftest + controls-first + scored-letter re-derivation.", flush=True)

ok0, okd, oke = r0 < 1e-12, rd < 5e-8, re_ < 5e-8
if ok0 and okd and oke:
    print("PREFLIGHT v2 PASS — three anchors hold on the sealed runner; census may launch (GREEN gate)")
else:
    failed = [n for (n, ok) in (("ANCHOR-0", ok0), ("ANCHOR-D", okd), ("ANCHOR-E", oke)) if not ok]
    print("PREFLIGHT v2 FAIL — %s — census does NOT launch; outcome (c) declared instead" % ", ".join(failed))
print("heat83b done %.1fs" % (time.time() - T0))
sys.exit(0 if (ok0 and okd and oke) else 1)
