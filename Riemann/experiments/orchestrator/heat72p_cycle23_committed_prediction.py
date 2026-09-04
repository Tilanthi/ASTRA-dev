#!/usr/bin/env python3
"""heat72p — m1's COMMITTED two-order prediction for m2's CYCLE 23 composition family (L150).

Configuration exactly as m2's hash-frozen runner (data/code/m2_c23_scored.py):
  S(da,gb,db) = K_T200 - sum_{n=1..4} Gram(zero n) + quad(da, g_a) + quad(db, g_b)
  quad = CROSS-FORM (verified against m2's CYCLE22 sweep to 0.005%):
      Q[i,j] = 2 Re[ u_i(p) conj(u_j(q)) + u_j(p) conj(u_i(q)) ],  p = 1/2+d+i g0,  q = 1/2-d+i g0
  => quad(0, g0) = 2 Gram(g0)  (double weight: p=q=1/2+i g0)  -- the rung family's
     launch already contains both legs' delta=0 baselines.
  g_a  = g1 + (g2-g1)*5/8 = 18.43929670238273204181427   (grid point 5 of 9, gap A)
  g_b  = g3 + (g4-g3)*2/8 = 26.36436221657414487498832   (grid point 2 of 9, gap B)
  g_b4 = g3 + (g4-g3)*1/8 = 25.68760989835991681910105   (R4's same-sign leg, grid point 1)

Two-order prediction (L148/L149 spec): ty2/ty4 = quad with u(p), u(q) replaced by their
delta^2 / delta^4 Taylor forms at s0 = 1/2 + i g0, u^(k)(s0) = int phi t^k e^{s0 t} dt
(differentiating under the integral, #104-compliant). DISPLACEMENT series keeps the u0
cross terms -- only u0*conj(u0) cancels in Q(d)-Q(0). ty6 column = banding instrument
only (|ty6-ty4| remainder proxy, x2 safety). EXACT column = instrument certification,
HELD from the exchange until m3's scoring is done (kept in the local .out only).

Also emits the Rayleigh-Schroedinger decomposition (f / self / cross on the launch's
G-orthonormal eigenvectors) and ||dQ||/gap -- trap #111's parameter. m2's committed PT
table is reproduced to 0.03% on f and both self terms; the third-order remainder
carries ~18x the total second-order shift at R2 (L150 sec 4).
"""
import json
import os
import numpy as np
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine1_heat72k_identity_target_m8.json"
DB = mpf('0.07208635197257083638787626')  # m2's solved cancellation delta_b


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

    def gmin(S):
        return float(np.linalg.eigvalsh(Li @ S @ Li.T)[0])

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

    FACT = [mpf(1)] * 8
    for i in range(1, 8):
        FACT[i] = FACT[i - 1] * i

    def quad_ty(order, g0, d):
        s0 = mpc(mpf('0.5'), g0)
        ders = [[U(phis[i], edges[i], s0, k) for i in range(M)] for k in range(order + 1)]

        def dz(z):
            return [sum((z ** k) * ders[k][i] / FACT[k] for k in range(0, order + 1)) for i in range(M)]

        tp, tq = dz(d), dz(-d)
        return np.array([[float(2 * mpre(tp[i] * conj(tq[j]) + tp[j] * conj(tq[i]))) for j in range(M)]
                         for i in range(M)])

    GZ = [mpf(str(float(mpim(zetazero(n))))) for n in (1, 2, 3, 4)]
    GA = GZ[0] + (GZ[1] - GZ[0]) * mpf(5) / 8
    GB = GZ[2] + (GZ[3] - GZ[2]) * mpf(2) / 8
    GB4 = GZ[2] + (GZ[3] - GZ[2]) * mpf(1) / 8
    L2 = K200.copy()
    for gv in GZ:
        L2 -= gram(gv)
    GA0, GB0, GB40 = 2 * gram(GA), 2 * gram(GB), 2 * gram(GB4)
    Launch, Launch4 = L2 + GA0 + GB0, L2 + GA0 + GB40
    lam0, W, ws = gmin_v(Launch)
    lam04, W4, ws4 = gmin_v(Launch4)
    print(f"launch  = {lam0:.13e}  (m2 4.2496273813877281464e-6)")
    print(f"launch4 = {lam04:.13e}  (m2 4.0845380841648368441e-6)")

    legs = {}
    for lbl, (g0, d, base) in (('a', (GA, mpf('0.1'), GA0)), ('b', (GB, DB, GB0)),
                               ('b2', (GB, mpf('0.2'), GB0)), ('b4', (GB4, mpf('0.1'), GB40))):
        legs[lbl] = {o: quad_ty(o, g0, d) - base for o in (2, 4, 6)}
        legs[lbl]['ex'] = quad_ex(g0, d) - base

    rungs = {
        'R0': (Launch, ['a']), 'R1': (Launch, ['b']), 'R2': (Launch, ['a', 'b']),
        'R1b': (Launch, ['b2']), 'R3': (Launch, ['a', 'b2']),
        'R0d': (Launch4, ['a']), 'R1c': (Launch4, ['b4']), 'R4': (Launch4, ['a', 'b4']),
    }
    print(f"\n{'rung':>4} {'ty2':>13} {'ty4':>13} {'ty6':>13} {'EXACT':>13} {'ty4/ex-1':>9} {'|ty6-ty4|':>10}")
    res = {}
    for nm, (Lb, lset) in rungs.items():
        vals = {}
        for o in (2, 4, 6, 'ex'):
            S = Lb.copy()
            for l in lset:
                S = S + legs[l][o]
            vals[o] = gmin(S)
        res[nm] = vals
        print(f"{nm:>4} {vals[2]:>13.5e} {vals[4]:>13.5e} {vals[6]:>13.5e} {vals['ex']:>13.5e} "
              f"{vals[4] / vals['ex'] - 1:>9.2%} {abs(vals[6] - vals[4]):>10.3e}")

    def shift(nm, o):
        return res[nm][o] - (lam0 if nm not in ('R0d', 'R1c', 'R4') else lam04)

    print("\n--- graded quantities (ty4 committed; ty6/ex = bands/certification) ---")
    for o in (4, 6, 'ex'):
        sA, sB, sBb = shift('R0', o), shift('R1', o), shift('R1b', o)
        sA4, sB4 = shift('R0d', o), shift('R1c', o)
        D2 = res['R2'][o] - (lam0 + sA + sB)
        D3 = res['R3'][o] - (lam0 + sA + sBb)
        D4 = res['R4'][o] - (lam04 + sA4 + sB4)
        print(f"[{o}] s_A={sA:+.4e} s_B={sB:+.4e} s_Bb={sBb:+.4e} s_A4={sA4:+.4e} s_B4={sB4:+.4e}")
        print(f"    D2={D2:+.4e} D3={D3:+.4e} D4={D4:+.4e}  shifts {shift('R2', o):+.4e} "
              f"{shift('R3', o):+.4e} {shift('R4', o):+.4e}  fires R0={res['R0'][o] < 0} "
              f"R2={res['R2'][o] < 0} R3={res['R3'][o] < 0} R4={res['R4'][o] < 0}")

    print("\n--- Rayleigh-Schroedinger decomposition (ty6 matrices; trap #111 parameter) ---")
    def pt2(DQ, Ws, wsv):
        v = Ws[:, 0]
        return float(v @ DQ @ v), sum((float(v @ DQ @ Ws[:, k])) ** 2 / (wsv[0] - wsv[k]) for k in range(1, M))

    v0 = W[:, 0]
    fa, sa = pt2(legs['a'][6], W, ws)
    fb, sb = pt2(legs['b'][6], W, ws)
    fb2, sb2 = pt2(legs['b2'][6], W, ws)
    cross = sum(float(v0 @ legs['a'][6] @ W[:, k]) * float(W[:, k] @ legs['b'][6] @ v0) / (ws[0] - ws[k])
                for k in range(1, M))
    v04 = W4[:, 0]
    fa4, sa4 = pt2(legs['a'][6], W4, ws4)
    fb4, sb4 = pt2(legs['b4'][6], W4, ws4)
    cross4 = sum(float(v04 @ legs['a'][6] @ W4[:, k]) * float(W4[:, k] @ legs['b4'][6] @ v04) / (ws4[0] - ws4[k])
                 for k in range(1, M))
    print(f"R2: f_a={fa:+.4e} f_b={fb:+.4e} self_a={sa:+.4e} self_b={sb:+.4e} cross={cross:+.4e}")
    print(f"R3: f_b(0.2)={fb2:+.4e} self_b(0.2)={sb2:+.4e}")
    print(f"R4: f_a={fa4:+.4e} f_b={fb4:+.4e} self_a={sa4:+.4e} self_b={sb4:+.4e} cross={cross4:+.4e}")
    for lbl, gap in (('a', ws[1] - ws[0]), ('b', ws[1] - ws[0]), ('b2', ws[1] - ws[0]), ('b4', ws4[1] - ws4[0])):
        print(f"||dQ_{lbl}||/gap = {np.abs(np.linalg.eigvalsh(legs[lbl][6])).max() / gap:.1f}")


if __name__ == "__main__":
    main()
