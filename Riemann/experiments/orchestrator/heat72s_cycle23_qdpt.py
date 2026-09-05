#!/usr/bin/env python3
"""heat72s -- L153: verify m3's L152 quasi-degenerate PT result on my instrument, extend it,
and attribute the k-deficit by state -- the reconciliation with the L151 census.

Sections:
(1) construction identical to heat72r (genomes -> G-orthonormal launch eigbasis W, full spectrum).
(2) VERIFY: k-sweep k=1..8 of the lowest projected eigenvalue for m3's rungs R0/R1/R2/R3,
    compared digit-for-digit against their letter152_qdpt_result.json.
(3) EXTEND (their sec5 offer, executed): R1b, R0d, R1c, R4 + census for every rung.
(4) ATTRIBUTE: for each rung, the eigenvalue drop lam_k -> lam_{k+1} on admitting launch state w_k,
    against the second-order estimate c^2/(H[k,k]-E_k) with c = <w_k|S|psi_k> -- shows the deficit
    after the crossing pair is plain second-order coupling to excluded states, and which states hold it.
(5) the certificate arithmetic: weight of the exact ground state OUTSIDE span{w0,w1} vs the crude
    Rayleigh-quotient bound ||S||*(2*sqrt(eps)+eps) -- why 99.8%-inside can coexist with 27% eigenvalue
    error when the spectrum tops at ||S|| ~ 0.97 and |lam_min| ~ 8e-6.
"""
import json
import os
import numpy as np
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine1_heat72k_identity_target_m8.json"
M3JSON = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/letter152_qdpt_result.json"
DB = mpf('0.07208635197257083638787626')


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
    legs = {'a': quad_ex(GA, mpf('0.1')) - 2 * gram(GA),
            'b': quad_ex(GB, DB) - 2 * gram(GB),
            'b2': quad_ex(GB, mpf('0.2')) - 2 * gram(GB),
            'b4': quad_ex(GB4, mpf('0.1')) - 2 * gram(GB4)}

    # launch G-orthonormal eigendecomposition (columns of W, ascending ws) -- same basis m3 uses
    _, W, ws = gmin_v(Launch)
    _, W4, ws4 = gmin_v(Launch4)
    print("(1) launch spectrum (mine, float64):", " ".join(f"{x:.6e}" for x in ws))
    print("    m3:                             ", " ".join(
        f"{float(x):.6e}" for x in json.load(open(M3JSON))['launch_spectrum']))

    rungs = {'R0': (Launch, W, ws, ['a']),
             'R1': (Launch, W, ws, ['b']),
             'R1b': (Launch, W, ws, ['b2']),
             'R2': (Launch, W, ws, ['a', 'b']),
             'R3': (Launch, W, ws, ['a', 'b2']),
             'R0d': (Launch4, W4, ws4, ['a']),
             'R1c': (Launch4, W4, ws4, ['b4']),
             'R4': (Launch4, W4, ws4, ['a', 'b4'])}

    m3 = json.load(open(M3JSON))['results']

    # assemble every rung matrix once
    Smat, Sexact, Scensus = {}, {}, {}
    for nm, (base, Wb, wsb, lg) in rungs.items():
        S = base.copy()
        for l in lg:
            S = S + legs[l]
        Smat[nm] = S
        lam_ex, Wpost, _ = gmin_v(S)
        Sexact[nm] = lam_ex
        Scensus[nm] = Wb.T @ (G @ Wpost[:, 0])  # new ground state in the launch G-orthonormal basis

    print("\n(2) VERIFY against m3's L152 table (their k-values; rel diff mine/theirs):")
    for nm in ('R0', 'R1', 'R2', 'R3'):
        Wb = rungs[nm][1]
        line = []
        for k in (1, 2, 3, 4, 6, 8):
            lk = np.linalg.eigvalsh(Wb[:, :k].T @ Smat[nm] @ Wb[:, :k])[0]
            rd = abs(lk / float(m3[nm][str(k)]['lam']) - 1) if k < 8 else abs(lk / Sexact[nm] - 1)
            line.append(f"k={k}:{lk:+.4e}({rd:.0e})")
        print(f"  {nm:>3}: " + "  ".join(line) + f"   exact {Sexact[nm]:+.6e}")

    print("\n(3) FULL k-LADDERS, all eight rungs (sign-flip k, census, drops by state):")
    for nm in ('R0', 'R1', 'R1b', 'R2', 'R3', 'R0d', 'R1c', 'R4'):
        Wb = rungs[nm][1]
        cg = Scensus[nm]
        lams = [np.linalg.eigvalsh(Wb[:, :k].T @ Smat[nm] @ Wb[:, :k])[0] for k in range(1, 9)]
        flip = next((k for k in range(1, 9) if np.sign(lams[k - 1]) == np.sign(Sexact[nm])), 8)
        drops = [lams[k - 1] - lams[k] for k in range(1, 8)]
        print(f"  {nm:>3}: exact {Sexact[nm]:+.6e}  w0 {cg[0]**2:.3f} w1 {cg[1]**2:.3f} "
              f"w_out {1-cg[0]**2-cg[1]**2:.4f}  sign_ok_at k={flip}")
        print(f"        ladder " + " ".join(f"{x:+.2e}" for x in lams))
        print(f"        drops " + " ".join(f"w{j+1}:{d:.2e}" for j, d in enumerate(drops)) +
              f"   k6err {abs(lams[5]/Sexact[nm]-1)*100:.2f}%  k7err {abs(lams[6]/Sexact[nm]-1)*100:.2f}%")

    print("\n(4) ATTRIBUTION: drop on admitting w_k vs second-order estimate c^2/(H[k,k]-E_k)")
    for nm in ('R0', 'R2', 'R3', 'R4'):
        Wb = rungs[nm][1]
        S = Smat[nm]
        lam_ex = Sexact[nm]
        H8 = Wb.T @ S @ Wb
        prev = None
        print(f"  {nm}:")
        for k in range(1, 8):
            Hk = H8[:k, :k]
            ek, yk = np.linalg.eigh(Hk)
            E, y = ek[0], yk[:, 0]
            psi = Wb[:, :k] @ y
            c = float(Wb[:, k] @ S @ psi)
            pred = c * c / (H8[k, k] - E)
            lam_k1 = np.linalg.eigvalsh(H8[:k + 1, :k + 1])[0]
            drop = E - lam_k1
            print(f"    admit w{k}: drop {drop:+.4e}   2nd-order pred {pred:+.4e}   "
                  f"ratio {drop/pred if pred != 0 else float('nan'):.3f}   |c| {abs(c):.2e}")
        print(f"    total deficit k2->exact: {np.linalg.eigvalsh(H8[:2,:2])[0] - lam_ex:+.4e}")

    print("\n(5) CERTIFICATE ARITHMETIC: composition deficit vs Rayleigh-quotient crude bound")
    for nm in ('R0', 'R2', 'R3', 'R4'):
        Wb = rungs[nm][1]
        lam_ex = Sexact[nm]
        wfull = gmin_v(Smat[nm])[2]
        cg = Scensus[nm]
        eps_out = 1.0 - cg[0] ** 2 - cg[1] ** 2
        top = wfull[-1]
        bound = top * (2 * np.sqrt(eps_out) + eps_out)
        lk2 = np.linalg.eigvalsh(Wb[:, :2].T @ Smat[nm] @ Wb[:, :2])[0]
        print(f"  {nm}: w_out(span{{w0,w1}}) {eps_out:.4f}   ||S||top {top:.3f}   "
              f"crude RQ bound {bound:.2e}   vs |lam_exact| {abs(lam_ex):.2e}  "
              f"-> bound/|lam| {bound/abs(lam_ex):.0f}x   actual k2 err {abs(lk2 - lam_ex):.2e}")


if __name__ == "__main__":
    main()
