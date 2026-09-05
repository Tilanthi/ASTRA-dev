#!/usr/bin/env python3
"""heat76b — S3 = C4 site ordinates + PT table re-measured at dps 45 (m1-L155 §6 ask 2).

heat76 scanned at dps 30; this firms the recommended site to commitment precision:
removed zeros #1/#2 (gap k=0) + #7/#8 (gap k=6), insertions g_a = 6/8, g_b = 4/8,
delta_a = 0.1, delta_b ladder.  Prints the 25-digit ordinates + launch lam_min/gap +
f_a + PT_a + PT_b ladder so m2's prereg can quote them directly.
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

    z1, z2, z7, z8 = gam[0], gam[1], gam[6], gam[7]
    g_a = z1 + (z2 - z1) * mpf(6) / 8
    g_b = z7 + (z8 - z7) * mpf(4) / 8
    print("removed  z1 %s" % mp.nstr(z1, 26))
    print("         z2 %s" % mp.nstr(z2, 26))
    print("         z7 %s" % mp.nstr(z7, 26))
    print("         z8 %s" % mp.nstr(z8, 26))
    print("g_a (6/8 of gap #1-#2)   %s" % mp.nstr(g_a, 26))
    print("g_b (4/8 of gap #7-#8)   %s" % mp.nstr(g_b, 26))

    rem = gram(z1) + gram(z2) + gram(z7) + gram(z8)
    qA0, qB0 = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0))
    vals, vecs = eig_full(K200 - rem + qA0 + qB0, Graw)
    gap = vals[1] - vals[0]
    v0, nrm = vecs[0], bil(Graw, vecs[0], vecs[0])
    print("launch lam_min %s" % mp.nstr(vals[0], 17))
    print("       gap    %s" % mp.nstr(gap, 12))

    Pa = quad_ex(g_a, mpf("0.1")) - qA0
    fa = bil(Pa, v0, v0) / nrm
    pta = gnorm(Pa, Graw) / gap
    print("f_a(0.1)   %s" % mp.nstr(fa, 10))
    print("PT_a       %s" % mp.nstr(pta, 8))
    for d in ("0.165", "0.20", "0.25", "0.30"):
        Pb = quad_ex(g_b, mpf(d)) - qB0
        fb = bil(Pb, v0, v0) / nrm
        ptb = gnorm(Pb, Graw) / gap
        print("d_b %-5s PT_b %-10s f_b %s" % (d, mp.nstr(ptb, 8), mp.nstr(fb, 8)))
    print("heat76b done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
