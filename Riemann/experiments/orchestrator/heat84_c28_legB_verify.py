#!/usr/bin/env python3
"""heat84 — verify m2's CYCLE 28 leg 1 on MY instrument (heat82 path), plus the
leg 2/3 data checks.

Section A (leg-B escape class): m2's catalogue claims three leg-B-only
transcription defects — bgap (displaced leg-B call passes g_a), bdel (passes
d_a instead of d_b), bhalf (passes d_b/2) — leave ANCHOR-U/ANCHOR-0/ANCHOR-D
BIT-IDENTICAL (all three prescribed points have d_b = 0, so the displaced
leg-B branch never executes there) while flipping R3b's FIRES verdict
(bdel, bhalf) or moving |λ_R3b| x48.8 (bgap); a third anchor at (0, δ_c)
= c25 rung R1 catches all three. All anchors here are computed THROUGH the
variant-corrupted leg-B call so bit-identity is demonstrated by execution,
not asserted.

Section B (leg-2 reproduction check): m2's committed cycle-21 r/u table
vs my heat72_birth_locus results JSON, both grids printed at 12 / 26 digits.

Section C (leg-2 estimator): polynomial ladder K=3/4/5 on MY full-precision
eleven points (m2 fit my 12-s.f. prints: 11.700718(3)).

Section D (leg-3 floor test): r recomputed with a/b at heat72w rung-3 full
printed precision (U1 = a 19 digits, U2 = |b| 21 digits) instead of the
registered 16/12-digit constants; ladder K=5..8 on both — tests m2's
hypothesis that b's 12 s.f. (δb/ε ~ 4e-9 at ε=1e-3) is the ~1e-10 residual
floor's cause. POST-HOC refinement of a completed, published run; no firing
clause, labelled as such.

Nothing here touches any sealed runner or unrevealed window.
"""
import json
import time
from mpmath import mp, mpf, mpc, exp, quad, re as mpre, fabs

mp.dps = 45
N = 8
HALF = mpf(1) / 2
T0 = time.time()

GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72k_identity_target_m8.json"
PREREG = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle25_prereg.json"
M2C21 = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle21_birth_locus.out"
RES72 = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72_birth_locus.results.json"

DSTAR = mpf("0.141733239663887191395415685084185024")
A_REG = mpf("2.645521411811663")
B_REG = mpf("7.46245287679")
A_U1 = mpf("2.645521411811664489")     # heat72w rung-3 U1 (19 printed digits)
B_U2 = mpf("7.4624528767937415788")    # heat72w rung-3 U2 (21 printed digits)


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


def section_a():
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

    qcache = {}

    def U(i, s, k=0):
        return quad(lambda t: (t ** k) * phis[i](t) * exp(s * t), edges[i])

    def gram(g0):
        uv = [U(i, mpc(HALF, g0)) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(uv[i] * conj_uv(uv[j]))
        return M

    def conj_uv(x):
        return x.conjugate()

    z3, z4, z5, z6 = [mpf(x) for x in S["removed"]]
    g_a, g_b = mpf(S["g_a"]), mpf(S["g_b"])
    DA = mpf(S["delta_a"])
    DLC = mpf(S["delta_c"])  # S2's own converged delta_c — c25 rung R1 = (0, delta_c) = ANCHOR-B
    D4 = mpf("0.30")
    remA, remB = gram(z3) + gram(z4), gram(z5) + gram(z6)
    base = K200 - remA - remB

    def quad_ex(g0, d):
        key = (mp.nstr(g0, 30), mp.nstr(d, 30))
        if key in qcache:
            return qcache[key]
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [U(i, p) for i in range(N)]
        uq = [U(i, q) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(up[i] * conj_uv(uq[j]) + up[j] * conj_uv(uq[i]))
        qcache[key] = M
        return M

    qA0, qB0 = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0))
    Lc = base + qA0 + qB0  # composed launch = ANCHOR-0

    lam_k200 = eig0(K200, Graw)
    lam_base = eig0(base, Graw)
    print("provenance: eig0(K200) = %s" % mp.nstr(lam_k200, 22))
    print("            eig0(base) = %s   (ANCHOR-U published 1.1761206927485314567e-5)" % mp.nstr(lam_base, 22))

    # leg-B displaced call sites — the ONLY thing variants corrupt
    LB = {
        "clean": lambda g, d: quad_ex(g_b, d),
        "bgap":  lambda g, d: quad_ex(g_a, d),   # passes g_a
        "bdel":  lambda g, d: quad_ex(g_b, DA),  # passes d_a instead of d_b
        "bhalf": lambda g, d: quad_ex(g_b, d / 2),  # passes d_b/2
    }

    def eig_cell(da, db, lb):
        M = Lc
        if da != 0:
            M = M + (quad_ex(g_a, da) - qA0)
        if db != 0:
            M = M + (lb(g_b, db) - qB0)
        return eig0(M, Graw)

    cert = {
        "ANCHOR-0": mpf("2.0004746865698620975e-5"),
        "ANCHOR-D": mpf("1.9160562986370759475e-5"),
        "ANCHOR-B": mpf("2.0626417939751361041e-5"),
        "R3b": mpf("-2.0432452753100828498e-6"),
    }
    vals = {}
    for name, lb in LB.items():
        vals[name] = {
            "ANCHOR-0": eig_cell(mpf(0), mpf(0), lb),
            "ANCHOR-D": eig_cell(DA, mpf(0), lb),
            "ANCHOR-B": eig_cell(mpf(0), DLC, lb),
            "R3b": eig_cell(DA, D4, lb),
        }

    print("\nclean cells vs certified published values (cross-instrument tol 1e-13):")
    for k in ("ANCHOR-0", "ANCHOR-D", "ANCHOR-B", "R3b"):
        v = vals["clean"][k]
        print("  %-9s = %s   rel vs cert %s" % (k, mp.nstr(v, 22),
                                                mp.nstr(fabs(v - cert[k]) / fabs(cert[k]), 4)))

    print("\nvariant table (rel move vs clean; bit-identical = 0 exactly):")
    print("  %-7s %-10s %-10s %-10s %-10s %s" % ("variant", "ANCHOR-0", "ANCHOR-D", "ANCHOR-B", "dR3b", "R3b verdict"))
    for name in ("bgap", "bdel", "bhalf"):
        v, c = vals[name], vals["clean"]
        ident = lambda k: (v[k] - c[k] == 0)
        movB = fabs(v["ANCHOR-B"] - c["ANCHOR-B"]) / fabs(c["ANCHOR-B"])
        movR = fabs(v["R3b"] - c["R3b"]) / fabs(c["R3b"])
        flips = (v["R3b"] > 0) != (c["R3b"] > 0)
        print("  %-7s %-10s %-10s %-10s %-10s %s  lam=%s" % (
            name,
            "BIT-ID" if ident("ANCHOR-0") else mp.nstr(fabs(v["ANCHOR-0"] - c["ANCHOR-0"]) / fabs(c["ANCHOR-0"]), 4),
            "BIT-ID" if ident("ANCHOR-D") else mp.nstr(fabs(v["ANCHOR-D"] - c["ANCHOR-D"]) / fabs(c["ANCHOR-D"]), 4),
            mp.nstr(movB, 4),
            "x" + mp.nstr(1 + movR, 4) if not flips else "FLIPS",
            "NEG->POS" if flips else "still FIRES",
            mp.nstr(v["R3b"], 12)))
    print("\nm2-C28 reference moves: bgap ANCHOR-B 0.71 dR3b x48.8 fires; bdel 0.0301 FLIPS; bhalf 0.0214 FLIPS")


def r_of(u, e, A, B):
    # r = (u^2 - A*e - B*e^2)/e^3  with B = |b| > 0 (register b = -7.46...);
    # verified against the scored table: (0.0515072381894006, 0.001) -> 11.7212
    return (u * u) / e ** 3 - A / e ** 2 - B / e


def polyfit_ladder(pts, ks, A, B, tag):
    """fit r(e) = sum_k c_k e^k (k=0..K) at dps 60; returns table rows."""
    mp.dps = 60
    out = []
    data = [(e, r_of(u, e, A, B)) for (e, u) in pts]
    for K in ks:
        rows = []
        rhs = []
        for (e, r) in data:
            rows.append([e ** k for k in range(K + 1)])
            rhs.append(r)
        Amat = mp.matrix(len(rows), K + 1)
        for i, row in enumerate(rows):
            for j in range(K + 1):
                Amat[i, j] = row[j]
        bvec = mp.matrix(len(rhs), 1)
        for i, r in enumerate(rhs):
            bvec[i] = r
        coef = mp.lu_solve(Amat, bvec)
        maxres = max(abs(sum(coef[k] * e ** k for k in range(K + 1)) - r) for (e, r) in data)
        out.append((K, coef, maxres))
        print("  [%s] K=%d  a3=%s  a4=%s  a5=%s  maxres=%s"
              % (tag, K, mp.nstr(coef[0], 16), mp.nstr(coef[1], 12), mp.nstr(coef[2], 9), mp.nstr(maxres, 3)))
    mp.dps = 45
    return out


def section_bcd():
    d = json.load(open(RES72))
    mine = sorted((mpf(e), mpf(u)) for (e, u, _r) in d["rtable"])
    # also pull my scored r strings for the print-floor comparison
    mine_r = {(mp.nstr(mpf(e), 20), mp.nstr(mpf(u), 24)): mpf(r) for (e, u, r) in d["rtable"]}

    theirs = []
    for line in open(M2C21):
        if line.startswith("eps=") and " u=" in line and " r=" in line:
            parts = dict(p.split("=", 1) for p in line.strip().split(" ") if "=" in p)
            theirs.append((mpf(parts["eps"]), mpf(parts["u"]), mpf(parts["r"])))
    print("\nsection B: m2 cycle-21 grid vs my JSON (%d vs %d rows)" % (len(theirs), len(mine)))
    worst_u = worst_r = mpf(0)
    for (e, u, r) in theirs:
        # match by epsilon string
        cand = [(me, mu) for (me, mu) in mine if fabs(me - e) <= mpf("5e-16") * fabs(e)]
        if not cand:
            print("  NO MATCH for eps=%s" % e)
            continue
        me, mu = cand[0]
        du = fabs(mu - u) / fabs(u)
        # compare recomputed r from each pair (avoids both print floors)
        rm = r_of(mu, me, A_REG, B_REG)
        rt = r_of(u, e, A_REG, B_REG)
        dr = fabs(rm - rt) / fabs(rt)
        worst_u = max(worst_u, du)
        worst_r = max(worst_r, dr)
    print("  worst rel u (26-digit prints vs my dps-50 strings): %s" % mp.nstr(worst_u, 4))
    print("  worst rel r (recomputed from each pair, registered A/B): %s" % mp.nstr(worst_r, 4))
    print("  m2 claim: 3.413e-11 over 11 r (12-s.f. print floor); recomputed-from-pairs is the floor-free read")

    print("\nsection C: ladder on MY full-precision points (registered a/b) — m2 on my 12-s.f. prints:")
    print("  m2: K=3 11.7007200919  K=4 11.7007190323  K=5 11.7007176099 => 11.700718(3)")
    polyfit_ladder(mine, (3, 4, 5), A_REG, B_REG, "reg a/b")

    print("\nsection D: b-republication floor test (a=U1 19d, |b|=U2 21d):")
    print("  delta-B contribution to r at eps=1e-3: %s (m2 floor hypo 5e-9)" % mp.nstr((B_U2 - B_REG) / mpf("0.001"), 3))
    polyfit_ladder(mine, (5, 6, 7, 8), A_REG, B_REG, "reg a/b")
    polyfit_ladder(mine, (5, 6, 7, 8), A_U1, B_U2, "U1/U2  ")
    print("  m2's own ladder (their u, their B): K=6 3.13e-10  K=7 1.94e-10  K=8 7.95e-11")


def main():
    print("=== SECTION A: leg-B escape class on my heat82 path ===")
    section_a()
    section_bcd()
    print("\nheat84 done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
