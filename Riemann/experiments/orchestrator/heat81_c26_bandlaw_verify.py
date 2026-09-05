#!/usr/bin/env python3
"""heat81 — verify m2's CYCLE 26 SCORED run (band-rule identity + failure boundary)
on m1's OWN instrument (heat75 machinery verbatim: my export, my composite quadrature,
my eigensolves, my Taylor ladder — nothing of m2's code).

Verified objects (vs data/machine2_cycle26_bandlaw.json + machine2_cycle26_boundary.json):
  LEG 1  the ten committed cycle-25 rungs: recompute ty2/ty4/ty6/exact -> ratio, r,
         identity 0.5/(1-r)
  LEG 2  delta_b sweep at delta_a=0.1 (9 values 0.30..0.80): same quantities
  PLUS   the single-leg (0, 0.1) config (their q-table first row)
  PLUS   delta_b* = 0.58139179348946 (their bisected failure boundary): ratio ~ 1, r ~ 1/2
  CHECKS the branch regime: all ratios >= 0.5 (no overshoot anywhere -> m1-L159's
         branch-aware form never triggered; same-sign branch held 19/19); r < 1.921
         everywhere (the un-fail window untouched)
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
PREREG = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle25_prereg.json"
REF = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle26_bandlaw.json"
REFB = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle26_boundary.json"


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
    refb = json.load(open(REFB))
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

    G0 = {"a": g_a, "b": g_b, "bs": g_bs}

    def quad_ex(g0, d):
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [U(i, p) for i in range(N)]
        uq = [U(i, q) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i]))
        return M

    qA0, qB0, qB0s = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0)), quad_ex(g_bs, mpf(0))
    base = K200 - remA - remB
    LAUNCH = base + qA0 + qB0
    LAUNCH_S = base + qA0 + qB0s
    print("site built %.1fs  (launch lam_min %s)" % (time.time() - T0, mp.nstr(eig0(LAUNCH, Graw), 12)), flush=True)

    FACT = [mpf(1)] * 12
    for i in range(1, 12):
        FACT[i] = FACT[i - 1] * i

    def ders_at(g0, kmax=6):
        s0 = mpc(HALF, g0)
        return [[U(i, s0, kk) for i in range(N)] for kk in range(kmax + 1)]

    DR = {"a": ders_at(g_a), "b": ders_at(g_b), "bs": ders_at(g_bs)}

    def quad_ty(site, d, K):
        def dz(z):
            return [sum((z ** kk) * DR[site][kk][i] / FACT[kk] for kk in range(K + 1)) for i in range(N)]
        tp, tq = dz(d), dz(-d)
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(tp[i] * conj(tq[j]) + tp[j] * conj(tq[i]))
        return M

    Q0 = {"a": qA0, "b": qB0, "bs": qB0s}

    def leg(site, d):
        """returns {2,4,6,ex} leg increment matrices at displacement d"""
        out = {}
        for K in (2, 4, 6):
            out[K] = (quad_ty(site, d, K) - Q0[site]) if d != 0 else mp.matrix(N, N)
        out["ex"] = (quad_ex(G0[site], d) - Q0[site]) if d != 0 else mp.matrix(N, N)
        return out

    # ---- configuration list --------------------------------------------------------
    D3, D4 = mpf("0.20"), mpf("0.30")
    LEGB = {}  # cache of leg-b ladders keyed by nstr(d)

    def getb(d):
        key = mp.nstr(d, 25)
        if key not in LEGB:
            LEGB[key] = leg("b", d)
        return LEGB[key]

    LEG_A = leg("a", DA)
    LEG_BS = leg("bs", DA)
    L = {"a": LEG_A, "bs": LEG_BS}

    RUNGS = {"R0": (DA, mpf(0), "b", "a", None),
             "R1": (mpf(0), DC, "b", None, "b"),
             "R2": (DA, DC, "b", "a", "b"),
             "R1b": (mpf(0), D3, "b", None, "b"),
             "R3": (DA, D3, "b", "a", "b"),
             "R1e": (mpf(0), D4, "b", None, "b"),
             "R3b": (DA, D4, "b", "a", "b"),
             "R0s": (DA, mpf(0), "bs", "a", None),
             "R1d": (mpf(0), DA, "bs", None, "bs"),
             "R4": (DA, DA, "bs", "a", "bs")}
    LEG2 = [mpf(x) for x in ("0.30", "0.35", "0.40", "0.45", "0.50", "0.55", "0.60", "0.70", "0.80")]
    DBS = mpf(refb["delta_b_star"])

    def solve_rung(lsite, la_key, lb_key, db):
        """la_key/lb_key in {None,'a','bs','b'}; db = leg-b displacement"""
        Lb = LAUNCH if lsite == "b" else LAUNCH_S
        lam = {}
        for o in (2, 4, 6, "ex"):
            S_ = Lb
            if la_key == "a":
                S_ = S_ + LEG_A[o]
            elif la_key == "b":
                S_ = S_ + getb(DA)[o]
            if lb_key == "b":
                S_ = S_ + getb(db)[o]
            elif lb_key == "bs":
                S_ = S_ + LEG_BS[o]
            lam[o] = eig0(S_, Graw)
        e4, e6, ex, e2 = lam[4] - lam["ex"], lam[6] - lam["ex"], lam["ex"], lam[2] - lam["ex"]
        ratio = fabs(e4) / (2 * fabs(lam[6] - lam[4]))
        r = fabs(e6) / fabs(e4)
        ident = mpf(1) / (2 * (1 - r))
        q = fabs(lam[6] - lam[4]) / fabs(lam[4] - lam[2])
        return {"ty2": lam[2], "ty4": lam[4], "ty6": lam[6], "exact": ex,
                "ratio": ratio, "r": r, "ident": ident, "q": q,
                "ident_relerr": fabs(ratio - ident) / ident}

    def rel(mine, theirs):
        return fabs(mine - mpf(theirs)) / max(fabs(mpf(theirs)), mpf("1e-30"))

    worst = {"exact": mpf(0), "ty4": mpf(0), "ty6": mpf(0), "ratio": mpf(0), "r": mpf(0)}
    min_ratio = mpf(10)
    max_r = mpf(0)

    print("\nLEG 1 (ten committed rungs)")
    print("%-5s %14s %14s %14s %10s %10s %8s" % ("rung", "ratio", "r", "ident_relerr", "ex_rel", "r4_rel", "r6_rel"))
    for name, rec in ref["leg1_committed_rungs"].items():
        da, db, lsite, la, lb = RUNGS[name]
        mine = solve_rung(lsite, la, lb, db)
        ex_rel, r4_rel, r6_rel = rel(mine["exact"], rec["exact"]), rel(mine["ty4"], rec["ty4"]), rel(mine["ty6"], rec["ty6"])
        ra_rel, rr_rel = rel(mine["ratio"], rec["ratio"]), rel(mine["r"], rec["r"])
        for k, v in (("exact", ex_rel), ("ty4", r4_rel), ("ty6", r6_rel), ("ratio", ra_rel), ("r", rr_rel)):
            worst[k] = max(worst[k], v)
        min_ratio = min(min_ratio, mine["ratio"])
        max_r = max(max_r, mine["r"])
        print("%-5s %14s %14s %14s %10s %10s %8s" % (
            name, mp.nstr(mine["ratio"], 12), mp.nstr(mine["r"], 12), mp.nstr(mine["ident_relerr"], 3),
            mp.nstr(ex_rel, 3), mp.nstr(r4_rel, 3), mp.nstr(r6_rel, 3)), flush=True)

    print("\nLEG 2 (delta_b sweep, delta_a = 0.1) + boundary + single-leg check")
    print("%-10s %14s %14s %14s %10s %10s" % ("d_b", "ratio", "r", "ident_relerr", "ex_rel", "ratio_rel"))
    for k, rec in ref["leg2_sweep"].items():
        db = mpf(k)
        mine = solve_rung("b", "a", "b", db)
        ex_rel, ra_rel = rel(mine["exact"], rec["exact"]), rel(mine["ratio"], rec["ratio"])
        for k2, v in (("exact", ex_rel), ("ratio", ra_rel)):
            worst[k2] = max(worst[k2], v)
        worst["r"] = max(worst["r"], rel(mine["r"], rec["r"]))
        min_ratio = min(min_ratio, mine["ratio"])
        max_r = max(max_r, mine["r"])
        print("%-10s %14s %14s %14s %10s %10s" % (
            k, mp.nstr(mine["ratio"], 12), mp.nstr(mine["r"], 12), mp.nstr(mine["ident_relerr"], 3),
            mp.nstr(ex_rel, 3), mp.nstr(ra_rel, 3)), flush=True)

    # boundary point: ratio ~ 1, r ~ 1/2
    mine = solve_rung("b", "a", "b", DBS)
    print("\ndelta_b* = %s  ->  ratio %s  (want ~1)   r %s  (want ~0.5)  ident_relerr %s" % (
        refb["delta_b_star"], mp.nstr(mine["ratio"], 10), mp.nstr(mine["r"], 10),
        mp.nstr(mine["ident_relerr"], 3)), flush=True)
    max_r = max(max_r, mine["r"])

    # single-leg (0, 0.1) at site b -- their q-table first row (r = 0.003392...)
    mine = solve_rung("b", None, "b", DA)
    print("single-leg (0, 0.1): r %s  q %s   (their q-table row 1: r 0.003392063 q 0.011620984)" % (
        mp.nstr(mine["r"], 10), mp.nstr(mine["q"], 10)), flush=True)

    print("\nWORST rel diffs vs their JSON: exact %s  ty4 %s  ty6 %s  ratio %s  r %s" % (
        tuple(mp.nstr(worst[k], 3) for k in ("exact", "ty4", "ty6", "ratio", "r"))))
    print("branch check: min ratio = %s  (all > 0.5 -> same-sign branch held everywhere;"
          " overshoot form 0.5/(1+r) never triggered)" % mp.nstr(min_ratio, 8))
    print("un-fail window check: max r = %s  (< 1.921 -> r in [1.921,2.0] window untouched)" % mp.nstr(max_r, 8))
    print("heat81 done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
