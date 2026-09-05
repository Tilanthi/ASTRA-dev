#!/usr/bin/env python3
"""heat80 — verify m3-L159's delta-sweep (3 pairs x 5 deltas) + run the overlap check
they flagged but did not: is k=1's four-order jump (delta 0.15 -> 0.2) a level
reorganization (CYCLE-25 mechanism: new ground state descending from a higher
eigenvalue of the delta=0 config), and is k=2's gradual crossing NOT one?

M8 only, all cells already published by m3 (public baseline data, not census-blind
content — the census deliverable is the M64 column; this strengthens the disclosed
M8 baseline to two instruments).

Config (m3-L158/159 conventions): K_S = K_T200 - gram(z_k) - gram(z_{k+1})
                                            + quad_ex(midpoint_k, delta).
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
REF = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/m3_L159_delta_sweep_result.json"


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
    K200 = mp.matrix(N, N)
    Graw = mp.matrix(N, N)
    for i in range(N):
        for j in range(N):
            K200[i, j] = mpf(idt["K_T200"][i][j])
            Graw[i, j] = mpf(idt["G_raw"][i][j])
    phis, edges = zip(*[make_phi(g) for g in genomes])

    def U(i, s):
        return quad(lambda t: phis[i](t) * exp(s * t), edges[i])

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

    zeros = [mpf(str(mpim(zetazero(n)))) for n in range(1, 12)]

    def config(k, d):
        g0 = (zeros[k] + zeros[k + 1]) / 2
        return K200 - gram(zeros[k]) - gram(zeros[k + 1]) + quad_ex(g0, d)

    ref = json.load(open(REF))
    # --- part 1: verify all 15 published cells (schema: results[kN].deltas[delta_str])
    worst = mpf(0)
    mism = 0
    ntot = 0
    for kname, entry in sorted(ref["results"].items()):
        k = int(kname[1:])
        for dstr, cell in sorted(entry["deltas"].items(), key=lambda kv: float(kv[0])):
            d = mpf(str(dstr))
            vals, _ = eig_full(config(k, d), Graw)
            mine = vals[0]
            theirs = mpf(cell["lam_min"])
            rel = fabs(mine - theirs) / max(fabs(theirs), mpf("1e-30"))
            worst = max(worst, rel)
            fire = mine < 0
            if fire != cell["fires"]:
                mism += 1
            ntot += 1
            print("k=%d d=%-5s mine %s  theirs %s  rel %s  %s" % (
                k, dstr, mp.nstr(mine, 8), mp.nstr(theirs, 8), mp.nstr(rel, 3),
                "FIRES" if fire else "survives"), flush=True)
    print("PART1 worst rel %s  mismatches %d/%d" % (mp.nstr(worst, 3), mism, ntot))

    # --- part 2: overlap check (the reorganization question m3 flagged)
    for (k, dstr, tag) in ((1, "0.2", "k=1 JUMP crosser"), (2, "0.45", "k=2 gradual crosser")):
        d = mpf(str(dstr))
        vL, VL = eig_full(config(k, mpf(0)), Graw)          # delta=0 config spectrum
        vD, VD = eig_full(config(k, d), Graw)               # displaced spectrum
        print("\n%s  (delta=%s): displaced lam_min %s | delta0 spectrum %s %s %s" % (
            tag, dstr, mp.nstr(vD[0], 8), mp.nstr(vL[0], 8), mp.nstr(vL[1], 8), mp.nstr(vL[2], 8)))
        for j in range(4):
            ov = bil(Graw, VD[0], VL[j])
            print("   <new_ground | delta0_state_%d>_G = %s   (lam%d = %s)" % (
                j, mp.nstr(fabs(ov), 6), j, mp.nstr(vL[j], 8)))
    print("heat80 done %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
