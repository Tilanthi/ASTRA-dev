#!/usr/bin/env python3
"""heat77 — S3 joint scan: exact-cancellation x insertion-disjointness x PT (m1-L155 addendum).

heat76b exposed a flaw in my C4 pick: f_b < 0 on the whole B ladder while f_a = -6.78e-6,
so NO delta_c exists there -- C4 is a non-cancelling control, not a family member.
This scan measures the JOINT constraint set:

  D-candidates (family members): leg A in gap k=1 @4/8 or 5/8 (removes #2,#3), leg B
    in gaps k=6/7 (fully disjoint) or k=5 (shares removal #6 with S2, marked) at
    near-edge fractions 2/8, 3/8 -- solve delta_c by bisection on f_b(delta) = -f_a.
  E-candidates (C4-class): leg A in gap k=0 @6/8 (f_a = -6.78e-6, PT_a ~1122) with
    near-edge B fractions -- does ANY disjoint B leg reach cancellation?  Expected NO:
    the structural claim is that leg-B strength enough to cancel a k=0-gap leg A lives
    only at low gamma, i.e. inside S1/S2's occupied gaps.

Reports per candidate: launch lam_min/gap, f_a, PT_a, delta_c (if crossing), PT_b(delta_c),
PT_b(0.30), max|f_b| seen.  dps 30; winners re-measured at dps 45 (heat77b).
"""
import json
import time
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 30
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

    # (name, kA, fracA, kB, fracB, note)
    CANDS = [
        ("D1", 1, 4, 6, 2, "disjoint"),
        ("D2", 1, 4, 6, 3, "disjoint"),
        ("D3", 1, 4, 7, 2, "disjoint"),
        ("D4", 1, 4, 7, 3, "disjoint"),
        ("D5", 1, 4, 5, 2, "SHARES #6 w/ S2"),
        ("D6", 1, 4, 5, 3, "SHARES #6 w/ S2"),
        ("D7", 1, 5, 6, 2, "disjoint"),
        ("D8", 1, 5, 7, 2, "disjoint"),
        ("E1", 0, 6, 6, 2, "C4-class: k=0 A, near-edge B"),
        ("E2", 0, 6, 7, 2, "C4-class: k=0 A, near-edge B"),
        ("E3", 0, 4, 6, 2, "k=0 A @4/8 (smaller |f_a|?)"),
    ]
    DA = mpf("0.1")
    DBLO, DBHI = mpf("0.03"), mpf("0.35")

    for (nm, kA, fA, kB, fB, note) in CANDS:
        GA1, GA2 = gam[kA], gam[kA + 1]
        GB1, GB2 = gam[kB], gam[kB + 1]
        g_a = GA1 + (GA2 - GA1) * mpf(fA) / 8
        g_b = GB1 + (GB2 - GB1) * mpf(fB) / 8
        remA, remB = gram(GA1) + gram(GA2), gram(GB1) + gram(GB2)
        qA0, qB0 = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0))
        vals, vecs = eig_full(K200 - remA - remB + qA0 + qB0, Graw)
        gap = vals[1] - vals[0]
        v0, nrm = vecs[0], bil(Graw, vecs[0], vecs[0])
        Pa = quad_ex(g_a, DA) - qA0
        fa = bil(Pa, v0, v0) / nrm
        pta = gnorm(Pa, Graw) / gap

        def fb(d):
            return bil(quad_ex(g_b, d) - qB0, v0, v0) / nrm

        lo, hi = DBLO, DBHI
        flo, fhi = fb(lo), fb(hi)
        target = -fa
        line = "%-3s A(k%d,%d/8) B(k%d,%d/8) %-22s" % (nm, kA, fA, kB, fB, note)
        line += " lam0 %s gap %s" % (mp.nstr(vals[0], 8), mp.nstr(gap, 6))
        line += " f_a %s PT_a %s" % (mp.nstr(fa, 6), mp.nstr(pta, 6))
        if (flo - target) * (fhi - target) < 0:
            for _ in range(40):
                mid = (lo + hi) / 2
                fm = fb(mid)
                if (flo - target) * (fm - target) <= 0:
                    hi = mid
                    fhi = fm
                else:
                    lo = mid
                    flo = fm
            dc = (lo + hi) / 2
            Pb = quad_ex(g_b, dc) - qB0
            ptb = gnorm(Pb, Graw) / gap
            conv = "CONVERGED" if dc <= mpf("0.25") else "delta>0.25 UNCONVERGED"
            line += " | delta_c %s PT_b(dc) %s %s" % (mp.nstr(dc, 8), mp.nstr(ptb, 6), conv)
        else:
            line += " | NO-CROSS (f_b %.2e..%.2e vs need %s)" % (
                mpf(flo), mpf(fhi), mp.nstr(target, 3))
        f30 = fb(mpf("0.30"))
        line += " | f_b(.3) %s PT_b(.3) %s" % (mp.nstr(f30, 4), mp.nstr(gnorm(quad_ex(g_b, mpf("0.30")) - qB0, Graw) / gap, 5))
        print(line, flush=True)
        print("     [%.0fs]" % (time.time() - T0), flush=True)

    print("heat77 done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
