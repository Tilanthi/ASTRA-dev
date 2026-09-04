#!/usr/bin/env python3
"""heat72s — M32 legs of the r4 dps-45 republication (L123r4 letter §6).
Full pipeline at dps 45 for the M32 prefixes (genome = M64 rng-stream prefix,
established bitwise in heat72p): fresh G (smooth real quads), fresh U over
zeros <= T, K = sum 2Re[U_a conj(U_b)], certified Cholesky-congruence solve.

Implements the r4 standing rule INSIDE the runner: after building U at
dps 45, every entry of the highest-gamma zero-column is recomputed at
dps 60 and the max rel diff reported (trap #99 guard). Trap #100
discipline: argv coerced to int at the boundary; every comparison print
is guarded by existence of its reference.

Usage: python3 heat72s_m32_u45.py {s1_32|s2_32|s3_32} {200|150}
"""
import json, os, re, sys, time
from mpmath import mp, mpf, mpc, exp, quad, fabs, zetazero, im as mpim, \
    re as mpre, conj, matrix, lu_solve, cholesky

mp.dps = 45
GEN = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat70_genomes_m8_m64.json")
OUT = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat72s_m32_u45_matrices.json")
HEAT63B = {"s1_32": 2.5298447891e-9, "s2_32": 3.6543245166e-9,
           "s3_32": 1.9357195069e-8}          # grid route, immune (r4 operative)
SUSPECT_R3 = {"s1_32": 2.52984414636784616e-9, "s3_32": 1.93624047551130721e-8}
NUM = re.compile(r'[+-]?\d+\.?\d*(?:[eE][+-]?\d+)?')


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


def lam_min(K, G, m):
    L = cholesky(G)
    Y = matrix(m, m)
    for j in range(m):
        c = lu_solve(L, matrix([[K[i, j]] for i in range(m)]))
        for i in range(m):
            Y[i, j] = c[i, 0]
    A = matrix(m, m)
    for j in range(m):
        c = lu_solve(L, matrix([[Y[j, i]] for i in range(m)]))
        for i in range(m):
            A[i, j] = c[i, 0]
    for i in range(m):
        for j in range(i+1, m):
            A[i, j] = A[j, i] = (A[i, j] + A[j, i]) / 2
    return sorted(mp.eigsy(A, eigvals_only=True))[0]


def main(tag, T):
    t0 = time.time()
    seed = tag[:2]
    m = 32
    genomes = json.load(open(GEN))["genomes"]
    g = genomes[f"{seed}/M64"][:m]           # rng-stream prefix (heat72p bitwise)
    phis, eds = zip(*[make_phi(f) for f in g])
    zs, n = [], 1
    while True:
        z = zetazero(n)
        if mpim(z) > T:
            break
        zs.append(z); n += 1
    nz = len(zs)
    print(f"[{tag}/T{T}] dps-45 full pipeline: m={m} nz={nz}", flush=True)
    G = matrix(m, m)
    for a in range(m):
        for b in range(a, m):
            ed = sorted(set(eds[a]) | set(eds[b]))
            G[a, b] = G[b, a] = quad(lambda x: phis[a](x)*phis[b](x), ed)
        if (a+1) % 8 == 0:
            print(f"[{tag}/T{T}] G row {a+1}/{m} ({time.time()-t0:.0f}s)",
                  flush=True)
    U = matrix(m, nz)
    for a in range(m):
        for j, rho in enumerate(zs):
            U[a, j] = quad(lambda t: phis[a](t)*exp(rho*t), eds[a])
        if (a+1) % 8 == 0:
            print(f"[{tag}/T{T}] U row {a+1}/{m} ({time.time()-t0:.0f}s)",
                  flush=True)
    # trap-#99 guard (r4 standing rule): highest-gamma column at dps 60
    rho_hi = zs[-1]
    worst60 = mpf(0)
    for a in range(m):
        u60 = quad(lambda t: phis[a](t)*exp(rho_hi*t), eds[a])
        r = abs(u60 - U[a, nz-1])/abs(u60)
        if r > worst60:
            worst60 = r
    print(f"[{tag}/T{T}] dps-60 check, column {nz} "
          f"(gamma={mp.nstr(mpim(rho_hi), 8)}): max rel diff = "
          f"{mp.nstr(worst60, 4)}", flush=True)
    K = matrix(m, m)
    for a in range(m):
        for b in range(a, m):
            s = mpf(0)
            for j in range(nz):
                s += 2*mpre(U[a, j]*conj(U[b, j]))
            K[a, b] = K[b, a] = s
    l1 = lam_min(K, G, m)
    print(f"[{tag}/T{T}] lambda_min (dps-45) = {mp.nstr(l1, 20)}", flush=True)
    ref = HEAT63B[tag]
    print(f"[{tag}/T{T}] vs heat63b grid value {ref:.10e}: "
          f"rel = {float(abs(l1-mpf(str(ref)))/mpf(str(ref))):+.3e}", flush=True)
    if tag in SUSPECT_R3 and T == 200:
        s3r = SUSPECT_R3[tag]
        print(f"[{tag}/T{T}] vs suspect r3 raw {s3r:.10e}: "
              f"rel = {float(abs(l1-mpf(str(s3r)))/mpf(str(s3r))):+.3e}",
              flush=True)
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    out[f"{tag}_T{T}"] = {
        "m": m, "nz": nz, "gamma_max": mp.nstr(mpim(rho_hi), 15),
        "dps60_col_check": mp.nstr(worst60, 6),
        "U": [[mp.nstr(U[a, j], 40, strip_zeros=False) for j in range(nz)]
              for a in range(m)],
        "G": [[mp.nstr(G[a, b], 40, strip_zeros=False) for b in range(m)]
              for a in range(m)],
        "K": [[mp.nstr(K[a, b], 40, strip_zeros=False) for b in range(m)]
              for a in range(m)],
        "lambda_min_dps45": mp.nstr(l1, 25),
    }
    with open(OUT, "w") as f:
        json.dump(out, f)
    print(f"[{tag}/T{T}] dumped ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("s1_32", "s2_32", "s3_32") \
            or sys.argv[2] not in ("200", "150"):
        sys.exit("usage: heat72s_m32_u45.py {s1_32|s2_32|s3_32} {200|150}")
    main(sys.argv[1], int(sys.argv[2]))      # trap #100: coerce at the boundary
