#!/usr/bin/env python3
"""heat75b — exact eigenvector overlaps for m2's CYCLE 25 H3/R3b claims (m1-L155 verification).

Two-instrument check of the scored runner's overlap column:
  ovl_v0 = |<v0^new, G v0^launch>|,  ovl_v1 = |<v0^new, G v1^launch>|
at R2/R3/R4 (H3: > 0.99) and R3b (claimed 0.702246 / 0.429956 -- the reorganisation regime).
Same independent path as heat75: my export, my quadrature at dps 45, my zetazero, pure-mpmath
eigensolves.  Site locked to their committed machine2_cycle25_prereg.json.
"""
import json
import os
import time
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72k_identity_target_m8.json"
PREREG = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle25_prereg.json"
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

    def quad_ex(g0, d):
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [U(i, p) for i in range(N)]
        uq = [U(i, q) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i]))
        return M

    z3, z4, z5, z6 = [mpf(x) for x in S["removed"]]
    g_a, g_b, g_bs = mpf(S["g_a"]), mpf(S["g_b"]), mpf(S["g_bs"])
    DA, DC = mpf(S["delta_a"]), mpf(S["delta_c"])
    D3 = mpf("0.20")
    D4 = mpf("0.30")

    print("building base + launches [%.0fs]" % (time.time() - T0), flush=True)
    remA = gram(z3) + gram(z4)
    remB = gram(z5) + gram(z6)
    qA0, qB0, qB0s = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0)), quad_ex(g_bs, mpf(0))
    base = K200 - remA - remB
    _, lvec_b = eig_full(base + qA0 + qB0, Graw)
    _, lvec_s = eig_full(base + qA0 + qB0s, Graw)

    legs = {"Pa": quad_ex(g_a, DA) - qA0,
            "Pb_dc": quad_ex(g_b, DC) - qB0,
            "Pb_20": quad_ex(g_b, D3) - qB0,
            "Pb_30": quad_ex(g_b, D4) - qB0,
            "Pbs": quad_ex(g_bs, DA) - qB0s}

    cases = {"R2": ("b", ["Pa", "Pb_dc"]), "R3": ("b", ["Pa", "Pb_20"]),
             "R3b": ("b", ["Pa", "Pb_30"]), "R4": ("bs", ["Pa", "Pbs"])}
    print("%-4s %22s %12s %12s   (scored runner: R2 .998939/.0307998  R3 .997712/.0398285"
          "  R3b .702246/.429956  R4 .999346/.0360487)" % ("rung", "lam_min", "ovl_v0", "ovl_v1"))
    for nm, (site, ls) in cases.items():
        Lb = (base + qA0 + qB0) if site == "b" else (base + qA0 + qB0s)
        for l in ls:
            Lb = Lb + legs[l]
        vals, vecs = eig_full(Lb, Graw)
        lv = lvec_b if site == "b" else lvec_s
        o0 = fabs(bil(Graw, vecs[0], lv[0]))
        o1 = fabs(bil(Graw, vecs[0], lv[1]))
        print("%-4s %22s %12s %12s" % (nm, mp.nstr(vals[0], 16), mp.nstr(o0, 8), mp.nstr(o1, 8)),
              flush=True)
        if nm == "R3b":
            print("     R3b spectrum: %s" % [mp.nstr(x, 8) for x in vals[:3]])

    print("heat75b done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
