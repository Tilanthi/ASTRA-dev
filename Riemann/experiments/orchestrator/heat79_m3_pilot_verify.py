#!/usr/bin/env python3
"""heat79 — independent verification of m3-L158's survivor-set pilot (all 25 rows).

m3 (astra-pa, 02904f4) scanned the single-pair witness test across adjacent on-line
pairs k=0..24 at delta=0.1, M=8, s1: only k=0 fires; lambda_min plateaus near the
untouched-matrix floor. Their kernel side is MY committed identity target; their
U-path is structurally independent (split real/imag quad vs my complex-form quad).

This verifies every row on MY path (heat77b architecture verbatim):
  K_S = K_T200 - gram(z_k) - gram(z_{k+1}) + quad_ex(gamma0_k, 0.1)
  gamma0 = midpoint (their 4/8), fires iff lambda_min < 0 (their rule).
Plus the untouched floor lambda_min(K_T200, G) against my published anchor
1.1761206927492675e-5 and their quoted 1.1761206927485e-5.

M8 displaced configs only — the M64 half stays sealed until the census prereg.
"""
import json
import time
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
N = 8
HALF = mpf(1) / 2
T0 = time.time()

GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72k_identity_target_m8.json"
REF = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/m3_L158_survivor_pilot_result.json"


def theta_step(s):
    if s <= 0:
        return mpf(0)
    if s >= 1:
        return mpf(1)
    return exp(-1 / s) / (exp(-1 / s) + exp(-1 / (1 - s)))


def window(x):
    return theta_step((8 - fabs(x)) / 2)


def bumpval(t):
    if fabs(t) >= 1:
        return mpf(0)
    return exp(-1 / (1 - t * t))


def make_phi(genome):
    triples = [(mpf(str(c)), mpf(str(mu)), mpf(str(s))) for (c, mu, s) in genome]

    def phi(x):
        tot = mpf(0)
        for (c, mu, s) in triples:
            tot += c * bumpval((x - mu) / s)
        return window(x) * tot

    edges = sorted(set([mpf(-8), mpf(-6), mpf(6), mpf(8)] +
                       [mu - s for (c, mu, s) in triples] + [mu + s for (c, mu, s) in triples]))
    return phi, edges


def eig_min(F, Gm):
    L = mp.cholesky(Gm)
    Li = mp.inverse(L)
    B = Li * F * Li.T
    B = (B + B.T) / 2
    E, _ = mp.eigsy(B)
    return min(E)


def main():
    genomes = json.load(open(GEN))["genomes"]["s1/M8"]
    idt = json.load(open(IDT))["seeds"]["s1/M8"]
    ref = json.load(open(REF))
    K200 = mp.matrix(N, N)
    Graw = mp.matrix(N, N)
    for i in range(N):
        for j in range(N):
            K200[i, j] = mpf(idt["K_T200"][i][j])
            Graw[i, j] = mpf(idt["G_raw"][i][j])
    phis, edges = zip(*[make_phi(g) for g in genomes])

    def U(i, s):
        return quad(lambda t: (t ** 0) * phis[i](t) * exp(s * t), edges[i])

    def gram(g0):
        uv = [U(i, mpc(HALF, g0)) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(uv[i] * conj(uv[j]))
        return M

    def quad_ex(g0, d):
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [U(i, p) for i in range(N)]
        uq = [U(i, q) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i]))
        return M

    # untouched floor vs both anchors
    floor = eig_min(K200, Graw)
    print("floor mine      %s" % mp.nstr(floor, 20))
    print("floor anchor(m1) 1.1761206927492675e-5   m3-quoted 1.1761206927485e-5")
    print("  vs m1 anchor rel %s   vs m3 quote rel %s" % (
        mp.nstr(fabs(floor - mpf("1.1761206927492675e-5")) / floor, 3),
        mp.nstr(fabs(floor - mpf("1.1761206927485e-5")) / floor, 3)))

    # zeros 1..26
    zeros = [mpf(str(mpim(zetazero(n)))) for n in range(1, 27)]

    gram_cache = {}

    def Gc(idx):
        if idx not in gram_cache:
            gram_cache[idx] = gram(zeros[idx])
        return gram_cache[idx]

    d = mpf("0.1")
    worst_rel = mpf(0)
    mism = 0
    for row in ref["results"]:
        k = row["k"]
        g0 = (zeros[k] + zeros[k + 1]) / 2
        KS = K200 - Gc(k) - Gc(k + 1) + quad_ex(g0, d)
        lmin = eig_min(KS, Graw)
        theirs = mpf(row["lam_min"])
        rel = fabs(lmin - theirs) / max(fabs(theirs), mpf("1e-30"))
        worst_rel = max(worst_rel, rel)
        fire_mine = lmin < 0
        if fire_mine != row["fires"]:
            mism += 1
        print("k=%2d  mine %s  theirs %s  rel %s  fire %s/%s" % (
            k, mp.nstr(lmin, 8), mp.nstr(theirs, 8), mp.nstr(rel, 3),
            "Y" if fire_mine else "n", "Y" if row["fires"] else "n"), flush=True)

    print("WORST rel diff %s   verdict mismatches %d/25" % (mp.nstr(worst_rel, 3), mism))
    print("n_fire theirs %d" % ref["n_fire"])
    print("heat79 done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
