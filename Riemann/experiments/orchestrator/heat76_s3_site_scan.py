#!/usr/bin/env python3
"""heat76 — S3 site-picker scan (m1 picks the third cancellation site; m2's CYCLE-25 ask 2).

Goal: a site with PT = ||P||_G/gap in [300, 600] at a rung whose delta-Taylor predictor is
CONVERGED (delta <= 0.25), filling the sign-inversion interval between S2's 214 (delta 0.30,
unconverged) and S1's 1145.  Architecture follows S2: two on-line pairs removed, two
delta=0 quadruples inserted, leg A at delta_a=0.1, leg B laddered.

Disjointness ledger (insertion ordinates must be disjoint from S1: 18.439/26.364 and
S2: 29.748/35.261/34.679; removal sharing allowed per S2's own precedent, recorded):

  gap k = up200 index of the pair's lower zero.  zeros removed by S1: #1-4; by S2: #3-6.
  k=0 (14.13, 21.02)  removal shares S1's;   k=1 (21.02, 25.01) shares #3 with both
  k=3 (30.42, 32.94)  shares #4,#5 with S2;   k=5 (37.59, 40.92) shares #6 with S2
  k=6 (40.92, 43.33)  fully disjoint;         k=7 (43.33, 48.01) fully disjoint

Candidates measured per site: launch lam_min + gap, ||P_a(0.1)||/gap, ||P_b(delta)||/gap at
delta in {0.165, 0.2, 0.25, 0.3}, second-order overlap-loss proxy at the PT-target rung.
dps 30 (scan precision: 3-4 significant digits suffice; the chosen site's numbers get
re-measured at dps 45 before commitment).

Output: per-candidate PT table + the S3 recommendation (site, ordinates at 25 digits,
delta ladder, PT at each rung).
"""
import json
import os
import time
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 30
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72k_identity_target_m8.json"
N = 8
HALF = mpf(1) / 2
T0 = time.time()


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

    # candidate sites: (name, kA, fracA, kB, fracB) — grid fractions of the gap
    CANDS = [("C1", 1, 4, 6, 4), ("C2", 1, 5, 7, 4), ("C3", 5, 4, 6, 4),
             ("C4", 0, 6, 6, 4), ("C5", 6, 4, 7, 5), ("C6", 1, 4, 7, 4)]
    DLAD = [mpf("0.165"), mpf("0.20"), mpf("0.25"), mpf("0.30")]
    DA = mpf("0.1")

    out = {}
    for (nm, kA, fA, kB, fB) in CANDS:
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
        row = {"g_a": mp.nstr(g_a, 20), "g_b": mp.nstr(g_b, 20),
               "rem": [mp.nstr(x, 16) for x in (GA1, GA2, GB1, GB2)],
               "lam0": mp.nstr(vals[0], 12), "gap": mp.nstr(gap, 8),
               "f_a": mp.nstr(fa, 8), "PT_a": mp.nstr(pta, 5), "PT_b": {}}
        print("%-3s g_a %s  g_b %s" % (nm, row["g_a"], row["g_b"]), flush=True)
        print("     lam0 %s  gap %s  f_a %s  PT_a %s" % (row["lam0"], row["gap"], row["f_a"], row["PT_a"]),
              flush=True)
        for d in DLAD:
            Pb = quad_ex(g_b, d) - qB0
            fb = bil(Pb, v0, v0) / nrm
            ptb = gnorm(Pb, Graw) / gap
            row["PT_b"][mp.nstr(d, 4)] = mp.nstr(ptb, 5)
            print("     d_b %s: PT_b %s  f_b %s" % (mp.nstr(d, 4), mp.nstr(ptb, 5), mp.nstr(fb, 6)),
                  flush=True)
        out[nm] = row
        print("     [%.0fs]" % (time.time() - T0), flush=True)

    json.dump(out, open(os.path.join(HERE, "heat76_s3_scan.json"), "w"), indent=1)
    print("\nheat76 done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
