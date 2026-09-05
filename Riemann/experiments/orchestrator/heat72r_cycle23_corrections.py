#!/usr/bin/env python3
"""heat72r -- L151 verification addenda: m2's two corrections to L150, checked on my instrument.

(a) cross-term factor 2: recompute second-order RS for P = Pa+Pb as sum_k ((v0|Pa+Pb|vk)^2)/(...),
    expand manually into self_a + 2*cross + self_b, and confirm the cross slot carries the factor 2.
    (L150 sec4's 'double count' reading retracted if confirmed.)
(b) G-metric norm: ||dQ||_G = max |eigvalsh(Li dQ Li^T)| for all four legs (the parameter consistent
    with the RS decomposition actually run); compare to the raw-basis eigvalsh used in L150 (76.1 etc.)
    and to m2's 1145.41 / 242.63.
(c) mechanism receipt (m2 sec4 'spectrum reorganised wholesale'): G-metric overlap of the
    POST-perturbation ground state with the PRE-perturbation ground vector at R2/R3/R4 --
    if small, lam_min after is not the continuation of lam_min before, and no PT around v0 speaks.
"""
import json
import os
import numpy as np
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine1_heat72k_identity_target_m8.json"
DB = mpf('0.07208635197257083638787626')
REV = json.load(open(os.path.join(os.path.dirname(GEN), os.pardir, "machine2_cycle23_scored.json"))) \
    if os.path.exists(os.path.join(os.path.dirname(GEN), "machine2_cycle23_scored.json")) else None
REV = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle23_scored.json"))


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
    Lc = np.linalg.cholesky(G)
    Li = np.linalg.inv(Lc)

    def gmin_v(S):
        H = Li @ S @ Li.T
        w, V = np.linalg.eigh(H)
        return w[0], Li.T @ V, w

    phis, edges = zip(*[make_phi(g) for g in genomes])

    def gram(g0):
        uv = [U(phis[i], edges[i], mpc(mpf('0.5'), g0)) for i in range(M)]
        return np.array([[float(2 * mpre(uv[i] * conj(uv[j]))) for j in range(M)] for i in range(M)])

    def quad_ex(g0, d):
        p = mpc(mpf('0.5') + d, g0)
        q = mpc(mpf('0.5') - d, g0)
        up = [U(phis[i], edges[i], p) for i in range(M)]
        uq = [U(phis[i], edges[i], q) for i in range(M)]
        return np.array([[float(2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i]))) for j in range(M)]
                         for i in range(M)])

    GZ = [mpf(str(float(mpim(zetazero(n))))) for n in (1, 2, 3, 4)]
    GA = GZ[0] + (GZ[1] - GZ[0]) * mpf(5) / 8
    GB = GZ[2] + (GZ[3] - GZ[2]) * mpf(2) / 8
    GB4 = GZ[2] + (GZ[3] - GZ[2]) * mpf(1) / 8
    L2 = K200.copy()
    for gv in GZ:
        L2 -= gram(gv)
    Launch, Launch4 = L2 + 2 * gram(GA) + 2 * gram(GB), L2 + 2 * gram(GA) + 2 * gram(GB4)
    lam0, W, ws = gmin_v(Launch)
    lam04, W4, ws4 = gmin_v(Launch4)
    gap, gap4 = ws[1] - ws[0], ws4[1] - ws4[0]

    legs = {'a': quad_ex(GA, mpf('0.1')) - 2 * gram(GA),
            'b': quad_ex(GB, DB) - 2 * gram(GB),
            'b2': quad_ex(GB, mpf('0.2')) - 2 * gram(GB),
            'b4': quad_ex(GB4, mpf('0.1')) - 2 * gram(GB4)}

    print("(a) RS second order for P = Pa + Pb at R2 -- the square decides the cross factor")
    v0 = W[:, 0]
    tot2 = 0.0
    sa = sb = cross2 = 0.0
    for k in range(1, M):
        ak = float(v0 @ legs['a'] @ W[:, k])
        bk = float(v0 @ legs['b'] @ W[:, k])
        den = ws[0] - ws[k]
        tot2 += (ak + bk) ** 2 / den
        sa += ak * ak / den
        sb += bk * bk / den
        cross2 += 2 * ak * bk / den
    print(f"  sum_k (a_k+b_k)^2/(l0-lk) = {tot2:+.6e}")
    print(f"  self_a {sa:+.6e} + 2*cross {cross2:+.6e} + self_b {sb:+.6e} = {sa + cross2 + sb:+.6e}")
    print(f"  identity sum_k (a_k+b_k)^2 = self_a + 2*sum(a_k b_k) + self_b : "
          f"{'HOLDS' if abs(sa + cross2 + sb - tot2) < 1e-14 * abs(tot2) else 'FAILS'}")
    fa = float(v0 @ legs['a'] @ v0)
    fb = float(v0 @ legs['b'] @ v0)
    print(f"  PT2 lambda_pred(R2) = launch + f + sum = {lam0 + fa + tot2:+.6e}  (m2: +3.587e-6)")
    print(f"  exact lambda(R2) (m2 revealed) = {float(REV['R2']):+.6e}")

    print("\n(b) the trap-#111 parameter in BOTH metrics (leg: raw-basis eigvalsh vs G-conjugated)")
    for lbl, g_ in (('a', gap), ('b', gap), ('b2', gap), ('b4', gap4)):
        raw = np.abs(np.linalg.eigvalsh(legs[lbl])).max()
        gmet = np.abs(np.linalg.eigvalsh(Li @ legs[lbl] @ Li.T)).max()
        print(f"  leg {lbl:>2}: raw {raw:.4e} (/gap {raw / g_:.1f})   G-metric {gmet:.4e} (/gap {gmet / g_:.1f})"
              f"   ratio G/raw = {gmet / raw:.2f}")
    print("  (m2 G-metric: leg a 1145.41, leg b 242.63)")

    print("\n(c) mechanism receipt: is lam_min(after) the continuation of lam_min(before)?")
    print("    G-orthonormal overlap <v0_post, v0_pre> and weight of v0_pre in the new ground state")
    for nm, (Lb, lset, l0_, W_, ws_) in (('R2', (Launch, ['a', 'b'], lam0, W, ws)),
                                         ('R3', (Launch, ['a', 'b2'], lam0, W, ws)),
                                         ('R4', (Launch4, ['a', 'b4'], lam04, W4, ws4))):
        S = Lb.copy()
        for l in lset:
            S = S + legs[l]
        lam_post, Wpost, _ = gmin_v(S)
        v_pre, v_post = W_[:, 0], Wpost[:, 0]
        ovl = float(v_pre @ G @ v_post)
        # decomposition of the new ground state in the OLD G-orthonormal eigenbasis:
        # sum_k c_k w_k = v_post with w_k^T G w_j = delta_kj  =>  c_k = w_k^T G v_post
        cg = W_.T @ (G @ v_post)
        top = int(np.argmax(np.abs(cg)))
        print(f"  {nm}: |<v0_pre, v0_post>|_G = {abs(ovl):.3f}   largest old-basis component: "
              f"w{top} weight {cg[top] ** 2:.3f}   old w0 weight {cg[0] ** 2:.3f}")


if __name__ == "__main__":
    main()
