#!/usr/bin/env python3
"""heat78a — M64 feasibility probe for the survivor-set census (heat78 spec §8).

Engineering + instrument prep only, NO census data: builds the config-independent
s1/M64 kernel pair (K_T200, G_raw) by the committed heat72k export path (same
conventions, same zero cut), then times the generalized eigensolve at dps 45.
Nothing here displaces anything — no verdicts, no survivor data. The census
config list + verdict rule freeze only in the prereg letter.

Stages (each timed, progress prints for the buffered log):
  1. U-cache: U_i(rho_n) for 64 genomes x all zeros Im<=200  (the one-off cost)
  2. G_raw 64x64 (pairwise edges)
  3. K_T200 64x64 from the cache
  4. cholesky(G) -> symmetrize -> eigsy  (the per-config eigensolve cost)
  5. launch report: lambda_min, first gap, spectrum ends, PSD check
Output: heat78a_m64_kernel.json (K/G as strings) + timings to stdout.
"""
import json
import time
from mpmath import mp, mpf, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
M = 64
T0 = time.time()

GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
OUT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat78a_m64_kernel.json"


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


def main():
    genomes = json.load(open(GEN))["genomes"]["s1/M64"]
    assert len(genomes) == M
    phis, edges_list = zip(*[make_phi(g) for g in genomes])

    zs = []
    n = 1
    while True:
        z = zetazero(n)
        if mpim(z) > 200:
            break
        zs.append(z)
        n += 1
    print("zeros to T=200: %d" % len(zs), flush=True)

    def U(i, rho):
        return quad(lambda t: phis[i](t) * exp(rho * t), edges_list[i])

    # stage 1: U-cache
    tc = time.time()
    Uc = {}
    for zi, z in enumerate(zs):
        for i in range(M):
            Uc[(i, zi)] = U(i, z)
        if (zi + 1) % 10 == 0:
            print("  U-cache zeros %d/%d  %.1fs" % (zi + 1, len(zs), time.time() - tc), flush=True)
    t_cache = time.time() - tc
    print("STAGE1 U-cache done %.1fs (%d integrals)" % (t_cache, M * len(zs)), flush=True)

    # stage 2: G_raw
    tg = time.time()
    Graw = mp.matrix(M, M)

    def pair_edges(i, j):
        return sorted(set(edges_list[i]) | set(edges_list[j]))

    for i in range(M):
        for j in range(i, M):
            v = quad(lambda t: phis[i](t) * phis[j](t), pair_edges(i, j))
            Graw[i, j] = v
            Graw[j, i] = v
        print("  G row %d/%d  %.1fs" % (i + 1, M, time.time() - tg), flush=True)
    t_g = time.time() - tg
    print("STAGE2 G_raw done %.1fs" % t_g, flush=True)

    # stage 3: K_T200
    tk = time.time()
    K200 = mp.matrix(M, M)
    for i in range(M):
        for j in range(M):
            acc = mpf(0)
            for zi in range(len(zs)):
                acc += 2 * mpre(Uc[(i, zi)] * conj(Uc[(j, zi)]))
            K200[i, j] = acc
        print("  K row %d/%d  %.1fs" % (i + 1, M, time.time() - tk), flush=True)
    t_k = time.time() - tk
    print("STAGE3 K_T200 done %.1fs" % t_k, flush=True)

    # stage 4/5: generalized eigensolve timing on the LAUNCH (no displacement)
    te = time.time()
    L = mp.cholesky(Graw)
    print("  cholesky %.1fs" % (time.time() - te), flush=True)
    t1 = time.time()
    Li = mp.inverse(L)
    print("  inverse %.1fs" % (time.time() - t1), flush=True)
    t1 = time.time()
    B = Li * K200 * Li.T
    B = (B + B.T) / 2
    print("  conj-transform %.1fs" % (time.time() - t1), flush=True)
    t1 = time.time()
    E, V = mp.eigsy(B)
    print("  eigsy(64) %.1fs" % (time.time() - t1), flush=True)
    t_eig = time.time() - te
    idx = sorted(range(M), key=lambda i: E[i])
    Es = [E[i] for i in idx]
    print("STAGE4 generalized eigensolve done %.1fs total" % t_eig, flush=True)

    print("LAUNCH s1/M64: lam_min %s" % mp.nstr(Es[0], 17))
    print("  gap01 %s" % mp.nstr(Es[1] - Es[0], 12))
    print("  spectrum top %s  median-ish %s" % (mp.nstr(Es[-1], 12), mp.nstr(Es[M // 2], 12)))
    print("  smallest five: %s" % ", ".join(mp.nstr(e, 8) for e in Es[:5]))

    out = {
        "convention": "heat72k export path verbatim; s1/M64; zeros Im<=200; dps 45; measurements only",
        "M": M,
        "n_zeros": len(zs),
        "timings_s": {"u_cache": t_cache, "g_raw": t_g, "k_t200": t_k, "eig_total": t_eig},
        "launch": {"lam_min": mp.nstr(Es[0], 25), "gap01": mp.nstr(Es[1] - Es[0], 18),
                   "top": mp.nstr(Es[-1], 18)},
        "K_T200": [[mp.nstr(K200[i, j], 50) for j in range(M)] for i in range(M)],
        "G_raw": [[mp.nstr(Graw[i, j], 50) for j in range(M)] for i in range(M)],
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh)
    print("WROTE %s" % OUT, flush=True)
    print("heat78a done %.1fs" % (time.time() - T0), flush=True)


if __name__ == "__main__":
    main()
