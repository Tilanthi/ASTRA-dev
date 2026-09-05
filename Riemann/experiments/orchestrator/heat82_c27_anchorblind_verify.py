#!/usr/bin/env python3
"""heat82 — verify m2's CYCLE 27 leg-B headline on MY instrument: the c1 conj-defect
(conj(up_i) for conj(uq_i) in the cross-form second term) leaves the composed-launch
anchor BIT-IDENTICAL (it is exact at d=0 by construction) while flipping the R3b
FIRES verdict and moving the displaced ANCHOR-D (R0 at d_a=0.1).

Machine: my verified heat81 path (anchor-checked launch 2.0004746865698620975e-5),
with quad_ex/quad_ty in two variants: clean (as heat81) and c1 (founding defect 2).
Verified against data/machine2_cycle27_firesflip_{clean,c1}.json +
machine2_cycle27_anchorblind_{clean,c1}.json.
"""
import json
import time
from mpmath import mp, mpf, mpc, exp, quad, re as mpre, im as mpim, conj, fabs

mp.dps = 45
N = 8
HALF = mpf(1) / 2
T0 = time.time()

GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72k_identity_target_m8.json"
PREREG = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle25_prereg.json"


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


def eig0(F, Gm):
    L = mp.cholesky(Gm)
    Li = mp.inverse(L)
    B = Li * F * Li.T
    B = (B + B.T) / 2
    E, _ = mp.eigsy(B)
    return min(E)


def main():
    genomes = json.load(open(GEN))["genomes"]["s1/M8"]
    idt = json.load(open(IDT))["seeds"]["s1/M8"]
    S = json.load(open(PREREG))["site"]
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

    z3, z4, z5, z6 = [mpf(x) for x in S["removed"]]
    g_a, g_b, g_bs = mpf(S["g_a"]), mpf(S["g_b"]), mpf(S["g_bs"])
    DA = mpf(S["delta_a"])
    D3, D4 = mpf("0.20"), mpf("0.30")
    remA, remB = gram(z3) + gram(z4), gram(z5) + gram(z6)

    def quad_ex(g0, d, c1=False):
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [U(i, p) for i in range(N)]
        uq = [U(i, q) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                second = conj(up[i]) if c1 else conj(uq[i])
                M[i, j] = 2 * mpre(up[i] * conj(uq[j]) + up[j] * second)
        return M

    qA0c, qB0c = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0))
    qA0b, qB0b = quad_ex(g_a, mpf(0), c1=True), quad_ex(g_b, mpf(0), c1=True)
    dmax = max(fabs(qA0c[i, j] - qA0b[i, j]) for i in range(N) for j in range(N))
    print("d=0 quads, clean vs c1: max |entry diff| = %s  (expect exactly 0)" % mp.nstr(dmax, 3))
    base = K200 - remA - remB
    Lc = base + qA0c + qB0c
    Lb = base + qA0b + qB0b
    dL = max(fabs(Lc[i, j] - Lb[i, j]) for i in range(N) for j in range(N))
    lamL = eig0(Lc, Graw)
    print("composed launch clean = %s" % mp.nstr(lamL, 22))
    print("clean-vs-c1 composed launch matrix max |diff| = %s  (ANCHOR-0 blind: expect 0)" % mp.nstr(dL, 3))

    FACT = [mpf(1)] * 12
    for i in range(1, 12):
        FACT[i] = FACT[i - 1] * i

    def ders_at(g0, kmax=6):
        s0 = mpc(HALF, g0)
        return [[U(i, s0, kk) for i in range(N)] for kk in range(kmax + 1)]

    DR = {"a": ders_at(g_a), "b": ders_at(g_b)}

    def quad_ty(site, d, K, c1=False):
        def dz(z):
            return [sum((z ** kk) * DR[site][kk][i] / FACT[kk] for kk in range(K + 1)) for i in range(N)]
        tp, tq = dz(d), dz(-d)
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                second = conj(tp[i]) if c1 else conj(tq[i])
                M[i, j] = 2 * mpre(tp[i] * conj(tq[j]) + tp[j] * second)
        return M

    def leg(site, d, c1=False):
        Q0 = qA0c if site == "a" else qB0c
        return {K: (quad_ty(site, d, K, c1) - Q0) for K in (2, 4, 6)}

    def lam_r3b(c1):
        LA = leg("a", DA, c1)
        LB = leg("b", D4, c1)
        ex = eig0(Lc + (quad_ex(g_a, DA, c1) - qA0c) + (quad_ex(g_b, D4, c1) - qB0c), Graw)
        return ex

    def lam_r0(c1):
        return eig0(Lc + (quad_ex(g_a, DA, c1) - qA0c), Graw)

    r3b_clean, r3b_c1 = lam_r3b(False), lam_r3b(True)
    r0_clean, r0_c1 = lam_r0(False), lam_r0(True)
    print("\nR3b clean = %s   (certified cycle-25 value -2.0432452753100828498e-6; FIRES)"
          % mp.nstr(r3b_clean, 22))
    print("R3b c1    = %s   (m2: +4.2393644119057858163e-5; verdict FLIPS)"
          % mp.nstr(r3b_c1, 22))
    print("  rel vs m2 c1: %s" % mp.nstr(fabs(r3b_c1 - mpf("4.2393644119057858163e-5")) / mpf("4.2393644119057858163e-5"), 4))
    print("\nANCHOR-D R0 clean = %s  (certified 1.9160562986370759475e-5)" % mp.nstr(r0_clean, 22))
    print("         R0 c1    = %s  (m2: 2.0434144895797e-5)" % mp.nstr(r0_c1, 22))
    print("  rel move = %s  (m2: 0.0664689 -> displaced anchor FIRES)"
          % mp.nstr(fabs(r0_c1 - r0_clean) / r0_clean, 6))
    print("\nheat82 done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
