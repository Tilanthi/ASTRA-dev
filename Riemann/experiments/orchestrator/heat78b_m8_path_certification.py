#!/usr/bin/env python3
"""heat78b — certify the heat78a probe code path at M8 against the committed artifact.

Rebuilds K_T200 + G_raw for s1/M8 from the genomes JSON through the SAME functions the
M64 build ran (theta_step/window/bumpval/make_phi/U/pair_edges, same zero cut), then
compares every entry to heat72k_identity_target_m8.json (the committed, two-instrument-
used artifact). Agreement certifies the M64 kernel's construction path; disagreement
means the M64 build is uncertified until fixed.

No displacements, no census data — instrument certification only.
"""
import json
import time
from mpmath import mp, mpf, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
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


def main():
    genomes = json.load(open(GEN))["genomes"]["s1/M8"]
    idt = json.load(open(IDT))["seeds"]["s1/M8"]
    M = len(genomes)
    phis, edges_list = zip(*[make_phi(g) for g in genomes])

    zs = []
    n = 1
    while True:
        z = zetazero(n)
        if mpim(z) > 200:
            break
        zs.append(z)
        n += 1
    ref_zeros = idt.get("n_zeros", None)
    print("zeros rebuilt %d" % len(zs), flush=True)

    def U(i, rho):
        return quad(lambda t: phis[i](t) * exp(rho * t), edges_list[i])

    Uc = {}
    for zi, z in enumerate(zs):
        for i in range(M):
            Uc[(i, zi)] = U(i, z)
    print("U-cache done %.1fs" % (time.time() - T0), flush=True)

    def pair_edges(i, j):
        return sorted(set(edges_list[i]) | set(edges_list[j]))

    worst = {"G_raw": mpf(0), "K_T200": mpf(0), "U0": mpf(0), "U1": mpf(0)}
    scale = {"G_raw": mpf(0), "K_T200": mpf(0), "U0": mpf(0), "U1": mpf(0)}
    for i in range(M):
        for key, rho in (("U0", 0), ("U1", 1)):
            mine = U(i, mpf(rho))
            theirs = mpf(idt[key][i])
            worst[key] = max(worst[key], fabs(mine - theirs))
            scale[key] = max(scale[key], fabs(theirs))
    for i in range(M):
        for j in range(M):
            gmine = quad(lambda t: phis[i](t) * phis[j](t), pair_edges(i, j))
            gtheirs = mpf(idt["G_raw"][i][j])
            worst["G_raw"] = max(worst["G_raw"], fabs(gmine - gtheirs))
            scale["G_raw"] = max(scale["G_raw"], fabs(gtheirs))
            acc = mpf(0)
            for zi in range(len(zs)):
                acc += 2 * mpre(Uc[(i, zi)] * conj(Uc[(j, zi)]))
            ktheirs = mpf(idt["K_T200"][i][j])
            worst["K_T200"] = max(worst["K_T200"], fabs(acc - ktheirs))
            scale["K_T200"] = max(scale["K_T200"], fabs(ktheirs))
        print("  row %d/%d  %.1fs" % (i + 1, M, time.time() - T0), flush=True)

    ok = True
    for key in ("U0", "U1", "G_raw", "K_T200"):
        rel = worst[key] / scale[key] if scale[key] > 0 else worst[key]
        verdict = "PASS" if rel < mpf("1e-40") else "FAIL"
        if verdict == "FAIL":
            ok = False
        print("%s: max abs diff %s  (scale %s, rel %s)  %s" % (
            key, mp.nstr(worst[key], 3), mp.nstr(scale[key], 3), mp.nstr(rel, 3), verdict))
    print("heat78b %s %.1fs" % ("CERTIFIED" if ok else "RED", time.time() - T0))


if __name__ == "__main__":
    main()
