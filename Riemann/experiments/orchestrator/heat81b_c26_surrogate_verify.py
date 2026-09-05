#!/usr/bin/env python3
"""heat81b — completion of heat81: the surrogate-q column + the (0.1, 0.1) row.

heat81 verified leg-1 (10 rungs) + leg-2 (9 d_b) + boundary point on my instrument.
This adds what heat81 skipped: (a) the two-leg (d_a=0.1, d_b=0.10)@site-b config =
row 1 of their surrogate table (their r 0.003392063, q 0.011620984); (b) the
observable q = |ty6-ty4|/|ty4-ty2| for every surrogate-table row vs their
boundary.out column; (c) ty2 itself via their err_ty2 field.
Same machinery as heat81 (now anchor-verified: launch 2.00047468657e-5).
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
REF = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle26_bandlaw.json"


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
    ref = json.load(open(REF))
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
    DC = mpf(S["delta_c"])
    remA, remB = gram(z3) + gram(z4), gram(z5) + gram(z6)

    def quad_ex(g0, d):
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [U(i, p) for i in range(N)]
        uq = [U(i, q) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i]))
        return M

    qA0, qB0 = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0))
    LAUNCH = K200 - remA - remB + qA0 + qB0
    print("anchor: launch lam_min = %s  (certified 2.0004746865698620975e-5)" % mp.nstr(eig0(LAUNCH, Graw), 20), flush=True)

    FACT = [mpf(1)] * 12
    for i in range(1, 12):
        FACT[i] = FACT[i - 1] * i

    def ders_at(g0, kmax=6):
        s0 = mpc(HALF, g0)
        return [[U(i, s0, kk) for i in range(N)] for kk in range(kmax + 1)]

    DRB = ders_at(g_b)
    DRA = ders_at(g_a)

    def quad_ty(DR, d, K):
        def dz(z):
            return [sum((z ** kk) * DR[kk][i] / FACT[kk] for kk in range(K + 1)) for i in range(N)]
        tp, tq = dz(d), dz(-d)
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(tp[i] * conj(tq[j]) + tp[j] * conj(tq[i]))
        return M

    def legA(d):
        return {K: quad_ty(DRA, d, K) - qA0 for K in (2, 4, 6)}

    def legB(d):
        return {K: quad_ty(DRB, d, K) - qB0 for K in (2, 4, 6)}

    LA = legA(DA)

    def rq(db):
        LB = legB(db)
        lam = {}
        for o in (2, 4, 6):
            lam[o] = eig0(LAUNCH + LA[o] + LB[o], Graw)
        ex = eig0(LAUNCH + (quad_ex(g_a, DA) - qA0) + (quad_ex(g_b, db) - qB0), Graw)
        e4, e6 = lam[4] - ex, lam[6] - ex
        r = fabs(e6) / fabs(e4)
        q = fabs(lam[6] - lam[4]) / fabs(lam[4] - lam[2])
        return r, q, ex, lam

    # (a) the (0.1, 0.1) row
    r, q, ex, _ = rq(DA)
    print("\n(0.1, 0.1)@b : r %s  q %s" % (mp.nstr(r, 10), mp.nstr(q, 10)))
    print("   their row: r 0.003392063  q 0.011620984")
    print("   rel: r %s   q %s" % (mp.nstr(fabs(r - mpf('0.003392063')) / mpf('0.003392063'), 3),
                                   mp.nstr(fabs(q - mpf('0.011620984')) / mpf('0.011620984'), 3)), flush=True)

    # (b) q column + ty2 check for the sweep rows; q for R2/R3 configs
    THEIR_Q = {"0.164990457617287927457442": "0.032210732", "0.20": "0.055622448",
               "0.30": "0.64072598", "0.35": "0.93960916", "0.40": "1.4604328",
               "0.45": "2.8237156", "0.50": "5.924234", "0.55": "13.475345",
               "0.60": "28.025588", "0.70": "38.091848", "0.80": "9.4209516"}
    LEG1_Q_CONFIGS = {"R2": DC, "R3": mpf("0.20")}
    print("\nq column (theirs from boundary.out):")
    worstq = mpf(0)
    for name, db in list(LEG1_Q_CONFIGS.items()) + [(k, mpf(k)) for k in
                                                    ("0.30", "0.35", "0.40", "0.45", "0.50", "0.55", "0.60", "0.70", "0.80")]:
        r, q, ex, lam = rq(db)
        key = mp.nstr(db, 25) if name in LEG1_Q_CONFIGS else name
        tq = mpf(THEIR_Q[{"R2": "0.164990457617287927457442", "R3": "0.20"}.get(name, name)])
        relq = fabs(q - tq) / tq
        worstq = max(worstq, relq)
        print("%-26s q %14s   theirs %12s   rel %s" % (name, mp.nstr(q, 10), tq, mp.nstr(relq, 3)), flush=True)

    # (c) ty2 via their err_ty2, for the 9 sweep records
    print("\nty2 check (|my ty2 - my exact| vs their err_ty2):")
    worst2 = mpf(0)
    for k, rec in ref["leg2_sweep"].items():
        r, q, ex, lam = rq(mpf(k))
        myerr2 = fabs(lam[2] - ex)
        rel2 = fabs(myerr2 - mpf(rec["err_ty2"])) / mpf(rec["err_ty2"])
        worst2 = max(worst2, rel2)
        print("%-6s rel %s" % (k, mp.nstr(rel2, 3)), flush=True)

    print("\nWORST: q-rel %s   err_ty2-rel %s" % (mp.nstr(worstq, 3), mp.nstr(worst2, 3)))
    print("heat81b done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
