#!/usr/bin/env python3
"""heat72m — counterparty checks for m2 CYCLE22 prereg + metric correction for my L143 §2.

(1) G-metric floors: my spec's eigenproblem is K v = lambda G v (Cholesky transform),
    NOT plain eigvalsh(K). L143's per-entry bar table used the Euclidean lambda_min —
    wrong observable. Recompute: lambda_min(K,G), lambda_min(G), cond(G), and the
    per-entry bar  eps_bar = lambda_min(K,G) * lambda_min(G) / (10 * 8)
    (perturbation: |dlambda| <= ||E||_2 / lambda_min(G); ||E||_2 <= ||E||_F <= 8*eps_entry).

(2) Off-line premise receipt (NOT the scored object): m2's core claim is that the
    analytic zero-side term  U_ij(s) = 1/2[u_i(s)u_j(1-s) + u_i(1-s)u_j(s)]
    differs O(1) from the bare Gram form 2Re[u_i conj(u_j)]  OFF the critical line,
    while coinciding ON it. Verify on my own instrument at the entry (0,0), PAIR-A
    midpoint gamma_0 = (Im z1 + Im z2)/2, delta in {0.1, 0.45}:
      analytic quadruple entry = 4*Re[u_0(s1)*u_0(s4)],  s1 = 1/2+d+i g0, s4 = 1-s1
      Gram/spec quadruple entry = 2|u_0(s1)|^2 + 2|u_0(s3)|^2,  s3 = 1/2-d+i g0
    No lambda_min is computed. Measurements only.
"""
import json, os
import numpy as np
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_JSON = os.path.join(HERE, "heat72k_identity_target_m8.json")
GENOME_JSON = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"


def theta_step(s):
    if s <= 0: return mpf(0)
    if s >= 1: return mpf(1)
    return exp(-1/s)/(exp(-1/s)+exp(-1/(1-s)))

def window(x): return theta_step((8-fabs(x))/2)

def bumpval(t):
    if fabs(t) >= 1: return mpf(0)
    return exp(-1/(1-t*t))

def make_phi(genome):
    triples = [(mpf(str(c)), mpf(str(mu)), mpf(str(s))) for (c, mu, s) in genome]
    def phi(x):
        tot = mpf(0)
        for (c, mu, s) in triples:
            tot += c*bumpval((x-mu)/s)
        return window(x)*tot
    edges = sorted(set([mpf(-8), mpf(-6), mpf(6), mpf(8)] +
                       [mu-s for (c, mu, s) in triples] + [mu+s for (c, mu, s) in triples]))
    return phi, edges

def U(phi, edges, rho):
    return quad(lambda t: phi(t)*exp(rho*t), edges)


def gmetric(seed, res):
    G = np.array([[float(x) for x in row] for row in res["G_raw"]])
    K = np.array([[float(x) for x in row] for row in res["K_T200"]])
    evG = np.linalg.eigvalsh(G)
    L = np.linalg.cholesky(G)
    Li = np.linalg.inv(L)
    Kp = Li @ K @ Li.T
    evK = np.linalg.eigvalsh(Kp)          # G-metric spectrum of K
    evK_eu = np.linalg.eigvalsh(K)        # Euclidean spectrum (L143's wrong-metric table)
    print(f"{seed}: lam_min(G)={evG.min():.6e}  cond(G)={evG.max()/evG.min():.3e}")
    print(f"{seed}: lam_min(K,G)={evK.min():.10e}   lam_max(K,G)={evK.max():.6e}   cond={evK.max()/evK.min():.3e}")
    print(f"{seed}: [Euclidean, wrong metric] lam_min={evK_eu.min():.6e}")
    eps_bar = evK.min()*evG.min()/(10*8)
    print(f"{seed}: per-entry bar (G-metric, 10% of lam_min) = {eps_bar:.3e}")
    return evK.min(), evG.min(), eps_bar


def offline_receipt():
    with open(GENOME_JSON) as fh:
        data = json.load(fh)
    genomes = data["genomes"]["s1/M8"]
    phi0, edges0 = make_phi(genomes[0])
    g1, g2 = mpim(zetazero(1)), mpim(zetazero(2))
    g0 = (g1+g2)/2
    print(f"\nPAIR-A: gamma_1={g1}  gamma_2={g2}  gamma_0={g0}")
    for d in (mpf('0.1'), mpf('0.45')):
        s1 = mpc(mpf('0.5')+d, g0)
        s3 = mpc(mpf('0.5')-d, g0)
        s4 = mpc(mpf('0.5')-d, -g0)   # = 1 - s1
        u1, u3, u4 = U(phi0, edges0, s1), U(phi0, edges0, s3), U(phi0, edges0, s4)
        # FE self-check: u(s4) should equal u(1-s1); identity u(1-s) has no closed form,
        # but U_ij symmetry means the quadruple entry only needs u at s1 and s4.
        analytic = 4*mpre(u1*u4)
        gram = 2*fabs(u1)**2 + 2*fabs(u3)**2
        print(f"delta={d}: u(s1)={u1}")
        print(f"delta={d}: analytic quad entry (0,0) = {analytic}")
        print(f"delta={d}: Gram/spec quad entry (0,0) = {gram}")
        print(f"delta={d}: ratio analytic/Gram = {analytic/gram}")
        # on-line coincidence control at delta=0 inserted midpoint (diagnostic-1 shape):
    s0 = mpc(mpf('0.5'), g0)
    u0v = U(phi0, edges0, s0)
    print(f"delta=0 control: U_00(1/2+i g0) = u0(g0)^2 real?  u0={u0v}")
    print(f"delta=0 control: Re[u0^2] vs |u0|^2 -> {mpre(u0v*u0v)} vs {fabs(u0v)**2} (equal iff u0 real-phase)")


def launch_points():
    """(3) Counterparty numbers for m2 CYCLE22: removal-only baselines (LAUNCH POINTS)
    and the PAIR-B magnitude bound. NOT the scored object (no +Q insertion computed).
    S_Z(delta) = K - Gram_k - Gram_{k+1} + Q(delta);  removal-only is a Gram sum => PSD.
    lam_min(S_Z^B) >= lam_min(K - Gram_k - Gram_{k+1}) - ||Q_B||_2 ; if the RHS > -1e-25
    PAIR-B cannot fire regardless of mechanism. ||Q||_2 <= ||Q||_F <= 8*max|Q_ij|,
    max|Q_ij| <= 4*max_i|u_i(s1)|*max_j|u_j(s4)| (entrywise bound)."""
    with open(TARGET_JSON) as fh:
        tgt = json.load(fh)
    res = tgt["seeds"]["s1/M8"]
    with open(GENOME_JSON) as fh:
        genomes = json.load(fh)["genomes"]["s1/M8"]
    M = len(genomes)
    phis, edges_list = zip(*[make_phi(g) for g in genomes])
    G = np.array([[float(x) for x in row] for row in res["G_raw"]])
    K = np.array([[float(x) for x in row] for row in res["K_T200"]])
    L = np.linalg.cholesky(G); Li = np.linalg.inv(L)

    def glmin(A):
        return np.linalg.eigvalsh(Li @ A @ Li.T).min()

    # verify smallest-gap claim cheaply (ordinates only)
    mp.dps = 30
    gs = []
    n = 1
    while True:
        g = mpim(zetazero(n))
        if g > 200: break
        gs.append(float(g)); n += 1
    gaps = [(gs[i+1]-gs[i], i) for i in range(len(gs)-1)]
    gmin, kmin = min(gaps)
    print(f"\n=== (3) launch points; {len(gs)} zeros to 200; smallest adjacent gap "
          f"{gmin:.5f} at k={kmin} (m2 claims 0.72432 at k=70) ===")
    mp.dps = 45
    for label, k in (("PAIR-A", 0), ("PAIR-B", 70)):
        zk, zk1 = zetazero(k+1), zetazero(k+2)
        uk  = [U(phis[i], edges_list[i], zk)  for i in range(M)]
        uk1 = [U(phis[i], edges_list[i], zk1) for i in range(M)]
        Gram = np.zeros((M, M)); Gram1 = np.zeros((M, M))
        for i in range(M):
            for j in range(M):
                Gram[i, j]  = 2*float(mpre(uk[i]*conj(uk[j])))
                Gram1[i, j] = 2*float(mpre(uk1[i]*conj(uk1[j])))
        base = K - Gram - Gram1
        lam0 = glmin(base)
        g0 = (mpim(zk)+mpim(zk1))/2
        # entrywise Q bound at worst ladder delta for THIS pair's midpoint
        worst = 0.0
        for d in (mpf('0.001'), mpf('0.01'), mpf('0.05'), mpf('0.1'), mpf('0.2'), mpf('0.3'), mpf('0.45')):
            s1 = mpc(mpf('0.5')+d, g0); s4 = mpc(mpf('0.5')-d, -g0)
            us1 = [U(phis[i], edges_list[i], s1) for i in range(M)]
            us4 = [U(phis[i], edges_list[i], s4) for i in range(M)]
            # Q_ij = 2 Re[a_i b_j + b_i a_j]  (a = u(s1), b = u(1-s1) = u(s4))
            Qmax = max(abs(2*float(mpre(us1[i]*us4[j] + us4[i]*us1[j])))
                       for i in range(M) for j in range(M))
            worst = max(worst, Qmax)
        qbound = 8*worst  # ||Q||_F <= 8 * max entry
        print(f"{label} (k={k}, gammas {float(mpim(zk)):.6f},{float(mpim(zk1)):.6f}, g0={float(g0):.6f}):")
        print(f"   removal-only lam_min(K-G_k-G_k1, G) = {lam0:.6e}   [launch point]")
        print(f"   max|Q_ij| over ladder = {worst:.3e}   ||Q||_F bound = {qbound:.3e}")
        print(f"   firing bound: lam_min(S_Z) >= {lam0 - qbound:.3e}"
              f"   -> {'CANNOT fire' if lam0 - qbound > -1e-25 else 'bound open'}")
        umax = max(abs(float(fabs(x))) for x in uk)
        print(f"   |u_i(rho_k)| max = {umax:.3e} (scale receipt)")


def main():
    import sys
    with open(TARGET_JSON) as fh:
        tgt = json.load(fh)
    if "1" not in sys.argv:
        print("=== (1) G-metric floors (spec line 82 eigenproblem) ===")
        for seed, res in tgt["seeds"].items():
            gmetric(seed, res)
    print("\n=== (2) off-line premise receipt, entry (0,0), PAIR-A midpoint ===")
    offline_receipt()
    print("\n=== (3) launch points + PAIR-B magnitude bound ===")
    launch_points()

if __name__ == "__main__":
    main()
