#!/usr/bin/env python3
"""heat72r — dps-45 U-table rebuild (quad-convergence correction, found in
the L124/L125 follow-up: mpmath quad at dps 30 returns WRONG values on the
most-oscillatory columns -- worst measured 300x magnitude error at
(basis 14, rho_79), stable/correct at dps 45 and 60 to 1e-44). Rebuilds the
full U table at dps 45 for (tag, T), recomputes K and lambda_min via the
certified Cholesky congruence, prints the worst 45-vs-30 entries, and dumps
the corrected U/K to machine1_heat72r_u45_matrices.json for the exchange.

G is NOT rebuilt (non-oscillatory smooth real integrands; persisted dps-30
G verified against dps-45 recomputes in the spot-check rows).

Usage: python3 heat72r_u45_rebuild.py {s3_M64|s1_M64} {200|150}
"""
import json, re, sys, time
from mpmath import mp, mpf, mpc, exp, quad, fabs, zetazero, im as mpim, \
    re as mpre, conj, matrix, lu_solve, cholesky

mp.dps = 45
MAT30 = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
         "machine1_heat72m_raw_matrices.json")
GEN = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat70_genomes_m8_m64.json")
OUT = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat72r_u45_matrices.json")
NUM = re.compile(r'[+-]?\d+\.?\d*(?:[eE][+-]?\d+)?')

def mcdeser(s):
    t = NUM.findall(s.replace("(", "").replace(")", "").replace(" ", ""))
    return mpc(mpf(t[0]), mpf(t[1]))

def theta_step(s):
    if s <= 0: return mpf(0)
    if s >= 1: return mpf(1)
    return exp(-1/s)/(exp(-1/s)+exp(-1/(1-s)))

def window(x): return theta_step((8-fabs(x))/2)

def bumpval(t):
    if fabs(t) >= 1: return mpf(0)
    return exp(-1/(1-t*t))

def make_phi(genome):
    tr = [(mpf(str(c)), mpf(str(mu)), mpf(str(s))) for (c, mu, s) in genome]
    def phi(x):
        tot = mpf(0)
        for (c, mu, s) in tr:
            tot += c*bumpval((x-mu)/s)
        return window(x)*tot
    edges = sorted(set([mpf(-8), mpf(-6), mpf(6), mpf(8)] +
                       [mu-s for (c, mu, s) in tr] + [mu+s for (c, mu, s) in tr]))
    return phi, edges

def colv(vals):
    v = matrix(len(vals), 1)
    for i, x in enumerate(vals):
        v[i, 0] = x
    return v

def lam_min(K, G, m):
    L = cholesky(G)
    Y = matrix(m, m)
    for j in range(m):
        c = lu_solve(L, colv([K[i, j] for i in range(m)]))
        for i in range(m):
            Y[i, j] = c[i, 0]
    A = matrix(m, m)
    for j in range(m):
        c = lu_solve(L, colv([Y[j, i] for i in range(m)]))
        for i in range(m):
            A[i, j] = c[i, 0]
    for i in range(m):
        for j in range(i+1, m):
            A[i, j] = A[j, i] = (A[i, j] + A[j, i]) / 2
    return sorted(mp.eigsy(A, eigvals_only=True))[0]

def main(tag, T):
    t0 = time.time()
    seed = tag[:2]
    blk30 = json.load(open(MAT30))[tag]
    m = blk30["m"]
    G = matrix([[mpf(x) for x in r] for r in blk30["G"]])
    genomes = json.load(open(GEN))["genomes"]
    g = genomes[f"{seed}/M64"]
    phis, eds = zip(*[make_phi(f) for f in g])
    zs, n = [], 1
    while True:
        z = zetazero(n)
        if mpim(z) > int(T):
            break
        zs.append(z); n += 1
    nz = len(zs)
    print(f"[{tag}/T{T}] rebuilding U at dps 45: m={m} nz={nz}", flush=True)
    # U30 only exists for T=200 in the persisted dump
    # (trap #100: T arrives as a STRING from argv -- compare as int, or this
    # branch silently never fires and every comparison print below is vacuous)
    U30 = None
    if int(T) == 200:
        U30 = [[mcdeser(x) for x in row] for row in blk30["U"]]
    U = matrix(m, nz)
    worst = []
    for a in range(m):
        for j, rho in enumerate(zs):
            u = quad(lambda t: phis[a](t)*exp(rho*t), eds[a])
            U[a, j] = u
            if U30 is not None:
                r = abs(u - U30[a][j])/abs(U30[a][j])
                if r > mpf('1e-20'):
                    worst.append((float(r), a+1, j+1))
        if (a+1) % 16 == 0:
            print(f"[{tag}/T{T}] U row {a+1}/{m} ({time.time()-t0:.0f}s)",
                  flush=True)
    worst.sort(reverse=True)
    if U30 is not None:
        print(f"[{tag}/T{T}] entries off >1e-20 vs dps30: {len(worst)} "
              f"of {m*nz}; worst 5:", flush=True)
        for r, a, j in worst[:5]:
            print(f"    basis {a} zero {j}: rel diff {r:.4e}", flush=True)
    else:
        print(f"[{tag}/T{T}] no dps-30 U for T={T} in the persisted dump "
              f"-- comparison skipped", flush=True)
    K = matrix(m, m)
    for a in range(m):
        for b in range(a, m):
            s = mpf(0)
            for j in range(nz):
                s += 2*mpre(U[a, j]*conj(U[b, j]))
            K[a, b] = K[b, a] = s
    l1 = lam_min(K, G, m)
    print(f"[{tag}/T{T}] lambda_min (dps-45 U) = {mp.nstr(l1, 20)}", flush=True)
    if T == 200:
        old = {"s3_M64": mpf("9.70653446567550195e-10"),
               "s1_M64": mpf("1.18132670405788889e-10")}[tag]
        print(f"[{tag}/T{T}] vs dps-30 value: |shift|/lambda = "
              f"{mp.nstr(abs(l1-old)/abs(old), 4)}", flush=True)
    out = json.load(open(OUT)) if __import__('os').path.exists(OUT) else {}
    out[f"{tag}_T{T}"] = {
        "m": m, "nz": nz,
        "U": [[mp.nstr(U[a, j], 40, strip_zeros=False) for j in range(nz)]
              for a in range(m)],
        "K": [[mp.nstr(K[a, b], 40, strip_zeros=False) for b in range(m)]
              for a in range(m)],
        "lambda_min_dps45": mp.nstr(l1, 25),
    }
    with open(OUT, "w") as f:
        json.dump(out, f)
    print(f"[{tag}/T{T}] dumped ({time.time()-t0:.0f}s total)", flush=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
