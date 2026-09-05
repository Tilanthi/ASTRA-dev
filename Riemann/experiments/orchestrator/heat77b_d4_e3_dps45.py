#!/usr/bin/env python3
"""heat77b — dps-45 re-measure of heat77's winners for the m1-L155 S3 addendum.

D4 = family member: A(k1,4/8) B(k7,3/8), heat77 delta_c 0.2235 -> confirm at dps 45
     with a 60-step bisection + PT_a/PT_b(delta_c) + 25-digit ordinates.
E3 = high-PT non-cancelling control: A(k0,4/8), PT_a 356 -> confirm + ordinates.
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


def eig_full(F, Gm):
    L = mp.cholesky(Gm)
    Li = mp.inverse(L)
    B = Li * F * Li.T
    B = (B + B.T) / 2
    E, V = mp.eigsy(B)
    idx = sorted(range(N), key=lambda i: E[i])
    return [E[i] for i in idx], [Li.T * mp.matrix([V[r, i] for r in range(N)]) for i in idx]


def bil(M, v, w):
    return sum(v[i] * M[i, j] * w[j] for i in range(N) for j in range(N))


def gnorm(P, Gm):
    L = mp.cholesky(Gm)
    Li = mp.inverse(L)
    B = Li * P * Li.T
    B = (B + B.T) / 2
    E, _ = mp.eigsy(B)
    return max(fabs(E[i]) for i in range(N))


def main():
    genomes = json.load(open(GEN))["genomes"]["s1/M8"]
    idt = json.load(open(IDT))["seeds"]["s1/M8"]
    K200 = mp.matrix(N, N)
    Graw = mp.matrix(N, N)
    for i in range(N):
        for j in range(N):
            K200[i, j] = mpf(idt["K_T200"][i][j])
            Graw[i, j] = mpf(idt["G_raw"][i][j])
    phis, edges = zip(*[make_phi(g) for g in genomes])

    def U(i, s, k=0):
        return quad(lambda t: (t ** k) * phis[i](t) * exp(s * t), edges[i])

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

    gam = []
    k = 1
    while True:
        g = mpf(str(mpim(zetazero(k))))
        if g > 200:
            break
        gam.append(g)
        k += 1

    # ---- D4: A(k1,4/8) + B(k7,3/8)
    zA1, zA2 = gam[1], gam[2]      # zeros #2,#3
    zB1, zB2 = gam[7], gam[8]      # zeros #8,#9
    g_a = zA1 + (zA2 - zA1) * mpf(4) / 8
    g_b = zB1 + (zB2 - zB1) * mpf(3) / 8
    rem = gram(zA1) + gram(zA2) + gram(zB1) + gram(zB2)
    qA0, qB0 = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0))
    vals, vecs = eig_full(K200 - rem + qA0 + qB0, Graw)
    gap = vals[1] - vals[0]
    v0, nrm = vecs[0], bil(Graw, vecs[0], vecs[0])
    Pa = quad_ex(g_a, mpf("0.1")) - qA0
    fa = bil(Pa, v0, v0) / nrm
    pta = gnorm(Pa, Graw) / gap

    def fb(d):
        return bil(quad_ex(g_b, d) - qB0, v0, v0) / nrm

    print("D4 removed z2 %s" % mp.nstr(zA1, 26))
    print("        z3 %s" % mp.nstr(zA2, 26))
    print("        z8 %s" % mp.nstr(zB1, 26))
    print("        z9 %s" % mp.nstr(zB2, 26))
    print("   g_a (k1 4/8) %s" % mp.nstr(g_a, 26))
    print("   g_b (k7 3/8) %s" % mp.nstr(g_b, 26))
    print("   launch lam_min %s  gap %s" % (mp.nstr(vals[0], 17), mp.nstr(gap, 12)))
    print("   f_a(0.1) %s   PT_a %s" % (mp.nstr(fa, 10), mp.nstr(pta, 8)))
    lo, hi = mpf("0.03"), mpf("0.35")
    flo = fb(lo)
    tgt = -fa
    for _ in range(60):
        mid = (lo + hi) / 2
        fm = fb(mid)
        if (flo - tgt) * (fm - tgt) <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    dc = (lo + hi) / 2
    Pb = quad_ex(g_b, dc) - qB0
    print("   delta_c %s   f_b(dc) %s  depth %s" % (
        mp.nstr(dc, 20), mp.nstr(fb(dc), 10), mp.nstr(fb(dc) + fa, 3)))
    print("   PT_b(delta_c) %s" % mp.nstr(gnorm(Pb, Graw) / gap, 8))

    # ---- E3: A(k0,4/8), B(k6,4/8) quad at delta 0 (control-style)
    zE1, zE2 = gam[0], gam[1]
    zF1, zF2 = gam[6], gam[7]
    gE = zE1 + (zE2 - zE1) * mpf(4) / 8
    gF = zF1 + (zF2 - zF1) * mpf(4) / 8
    remE = gram(zE1) + gram(zE2) + gram(zF1) + gram(zF2)
    qE0, qF0 = quad_ex(gE, mpf(0)), quad_ex(gF, mpf(0))
    valsE, vecsE = eig_full(K200 - remE + qE0 + qF0, Graw)
    gapE = valsE[1] - valsE[0]
    v0E, nrmE = vecsE[0], bil(Graw, vecsE[0], vecsE[0])
    PaE = quad_ex(gE, mpf("0.1")) - qE0
    faE = bil(PaE, v0E, v0E) / nrmE
    print("E3 g_a (k0 4/8) %s" % mp.nstr(gE, 26))
    print("   g_b (k6 4/8) %s" % mp.nstr(gF, 26))
    print("   launch lam_min %s  gap %s" % (mp.nstr(valsE[0], 17), mp.nstr(gapE, 12)))
    print("   f_a(0.1) %s   PT_a %s" % (mp.nstr(faE, 10), mp.nstr(gnorm(PaE, Graw) / gapE, 8)))
    print("heat77b done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
