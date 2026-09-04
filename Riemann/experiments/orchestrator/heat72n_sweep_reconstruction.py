#!/usr/bin/env python3
"""heat72n — third-party reconstruction of m2's CYCLE22 §4.3 ordinate sweep (m1-L146).

Two legs, both from my own exports + dps-45 breakpoint-piecewise quadrature (#99-compliant):
  (exact)  S_Z = K_T200 - Gram(u(g1)) - Gram(u(g2)) + S_quad(delta, gamma_0), lam_min in G-metric
  (taylor2/taylor4) same, but u(p), u(q) replaced by their delta^2 / delta^4-truncated Taylor
           forms at s0 = 1/2 + i*gamma_0:
             u(p) ~ sum_k  d^k/k! u^{(k)}(s0),   u(q) ~ sum_k (-d)^k/k! u^{(k)}(s0)
           with u^{(k)}(s0) = integral phi(t) t^k e^{s0 t} dt  (local data only, no fitted params)
           m1-L148 finding: delta^4 closes the taylor2 magnitude gap (18-76% -> 0.24-2.2% at
           all nine ordinates, residual sign-free) — the taylor2 under-negativity IS the
           delta^4 remainder.

m2 scored row (letter f871287 sec 4.3), for grading:
  gamma_0  14.1347 14.9956 15.8566 16.7175 17.5784 18.4393 19.3002 20.1611 21.0220
  lam_min -5.91e-3 -5.54e-3 -4.69e-5 -3.84e-4 -6.97e-6 +3.39e-6 -8.11e-6 -6.10e-6 +1.07e-6
"""
import json
import os
import numpy as np
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine1_heat72k_identity_target_m8.json"
DELTA = mpf('0.1')
SWEEPS = ["14.134725", "14.9956", "15.8566", "16.7175", "17.5784", "18.4393", "19.3002", "20.1611", "21.0220"]
M2_ROW = [-5.91e-3, -5.54e-3, -4.69e-5, -3.84e-4, -6.97e-6, 3.39e-6, -8.11e-6, -6.10e-6, 1.07e-6]


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


def U(phi, ed, s, k=0):
    return quad(lambda t: (t ** k) * phi(t) * exp(s * t), ed)


def main():
    genomes = json.load(open(GEN))["genomes"]["s1/M8"]
    idt = json.load(open(IDT))["seeds"]["s1/M8"]
    M = len(genomes)
    K200 = np.array(idt["K_T200"], dtype=float)
    G = np.array(idt["G_raw"], dtype=float)
    Li = np.linalg.inv(np.linalg.cholesky(G))

    def gmin(S):
        return float(np.linalg.eigvalsh(Li @ S @ Li.T)[0])

    phis, edges = zip(*[make_phi(g) for g in genomes])

    g1 = float(mpim(zetazero(1)))
    g2 = float(mpim(zetazero(2)))
    L = K200.copy()
    for gv in (g1, g2):
        uv = [U(phis[i], edges[i], mpc(mpf('0.5'), mpf(str(gv)))) for i in range(M)]
        L -= np.array([[float(2 * mpre(uv[i] * conj(uv[j]))) for j in range(M)] for i in range(M)])
    print(f"launch check: lam_min(L,G) = {gmin(L):.6e}  (m2 removal-only: 3.375750739e-7)")

    d = DELTA
    print(f"\n{'gamma_0':>10} {'m2 scored':>12} {'m1 exact':>12} {'m1 taylor2':>12} {'m1 taylor4':>12} "
          f"{'|ex-m2|/|m2|':>13} {'ty4/ex-1':>10}")
    for gs, m2v in zip(SWEEPS, M2_ROW):
        g0 = mpf(gs)
        s0 = mpc(mpf('0.5'), g0)
        p = mpc(mpf('0.5') + d, g0)
        q = mpc(mpf('0.5') - d, g0)
        ap = [U(phis[i], edges[i], p) for i in range(M)]
        aq = [U(phis[i], edges[i], q) for i in range(M)]
        Sq_ex = np.array([[float(2 * mpre(ap[i] * conj(aq[j]) + ap[j] * conj(aq[i]))) for j in range(M)]
                          for i in range(M)])
        lam_ex = gmin(L + Sq_ex)
        ders = [[U(phis[i], edges[i], s0, k) for i in range(M)] for k in range(5)]
        tp2 = [ders[0][i] + d * ders[1][i] + (d * d / 2) * ders[2][i] for i in range(M)]
        tq2 = [ders[0][i] - d * ders[1][i] + (d * d / 2) * ders[2][i] for i in range(M)]
        tp4 = [tp2[i] + (d ** 3 / 6) * ders[3][i] + (d ** 4 / 24) * ders[4][i] for i in range(M)]
        tq4 = [tq2[i] - (d ** 3 / 6) * ders[3][i] + (d ** 4 / 24) * ders[4][i] for i in range(M)]
        lams = {}
        for lbl, tp, tq in (('ty2', tp2, tq2), ('ty4', tp4, tq4)):
            Sq_ty = np.array([[float(2 * mpre(tp[i] * conj(tq[j]) + tp[j] * conj(tq[i]))) for j in range(M)]
                              for i in range(M)])
            lams[lbl] = gmin(L + Sq_ty)
        rel = abs(lam_ex - m2v) / abs(m2v)
        print(f"{gs:>10} {m2v:>12.3e} {lam_ex:>12.3e} {lams['ty2']:>12.3e} {lams['ty4']:>12.3e} "
              f"{rel:>12.3%} {lams['ty4'] / lam_ex - 1:>10.2%}")


if __name__ == "__main__":
    main()
