#!/usr/bin/env python3
"""heat72k — K-export for m3's N2/N5 second instrument: term-by-term identity target.

Exports, in the RAW GENOME basis (pre-GS, the basis of the exported genomes JSON):
  K_FE(T)[a,b] = sum over upper-half zeros Im(rho)<=T of 2*Re[U_a(rho)*conj(U_b(rho))]
                 (for the TRUE on-line zeros this IS the FE-paired zero side;
                  m3's Letter 119 shows these coincide on the line)
  G_raw[a,b]   = integral f_a f_b
  U_a(0), U_a(1) per genome (endpoint term u_i(1)u_j(0) building blocks)
at T = 200 and T = 150 (empirical tail bracket), for M=8 seeds 1/2/3, quad precision.

No derivations here — measurements only. The identity check is m3's:
  K_FE + Endpoint + Arch - Prime = 0  (their sign convention, Kowalski Prop 1.2.1)
must close to within the T-bracket |K(150)-K(200)| + their term accuracy.

Conventions identical to machine1-spec-n2-n5-second-instrument.md:
  phi = w * f, w = theta((8-|x|)/2) smooth step, f = sum of bumps c*exp(-1/(1-t^2))
  breakpoints: {-8,-6,6,8} U {mu+-s per bump of BOTH genomes in the pair}
  integrals: mp.quad per piece, dps 45; zeros: zetazero(n) while Im <= T.
Output: JSON to stdout-adjacent file, m8 all seeds.
"""
import json, os, sys
from mpmath import mp, mpf, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
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

def main():
    with open(GENOME_JSON) as fh:
        data = json.load(fh)
    out = {"convention": "raw genome basis; K_FE = sum_{0<Im rho<=T} 2Re[U_a(rho) conj(U_b(rho))]; "
                         "U_a(rho)=int phi_a e^{rho t}; breakpoints per spec; mp.dps 45",
           "note": "measurements only, no derivations; identity check is m3's (Kowalski Prop 1.2.1 signs)",
           "seeds": {}}
    for seed in ("1", "2", "3"):
        key = f"s{seed}/M8"
        if key not in data["genomes"]: continue
        genomes = data["genomes"][key]
        M = len(genomes)
        phis, edges_list = zip(*[make_phi(g) for g in genomes])
        # per-genome edges for U; pairwise for products
        def pair_edges(i, j):
            return sorted(set(edges_list[i]) | set(edges_list[j]))
        res = {"M": M, "U0": [], "U1": [], "G_raw": [], "K_T200": [], "K_T150": []}
        for i in range(M):
            res["U0"].append(str(U(phis[i], edges_list[i], 0)))
            res["U1"].append(str(U(phis[i], edges_list[i], 1)))
        for i in range(M):
            rowG, row200, row150 = [], [], []
            for j in range(M):
                pe = pair_edges(i, j)
                rowG.append(str(quad(lambda t: phis[i](t)*phis[j](t), pe)))
                row200.append(""); row150.append("")
            res["G_raw"].append(rowG); res["K_T200"].append(row200); res["K_T150"].append(row150)
        # zeros
        zs = []
        n = 1
        while True:
            z = zetazero(n)
            if mpim(z) > 200: break
            zs.append(z); n += 1
        print(f"seed {seed}: {len(zs)} zeros to T=200", flush=True)
        # U cache keyed (genome, zero-index); NB never use setdefault here --
        # the default is evaluated eagerly and the cache would save nothing.
        Uvals = {}
        def Uc(i, zi, z):
            key = (i, zi)
            if key not in Uvals:
                Uvals[key] = U(phis[i], edges_list[i], z)
            return Uvals[key]
        for T, Kkey in ((200, "K_T200"), (150, "K_T150")):
            for i in range(M):
                for j in range(M):
                    acc = mpf(0)
                    for zi, z in enumerate(zs):
                        if mpim(z) > T: continue
                        acc += 2*(Uc(i, zi, z)*conj(Uc(j, zi, z))).real
                    res[Kkey][i][j] = str(acc)
                print(f"  seed {seed} {Kkey} row {i}/{M} done", flush=True)
        out["seeds"][key] = res
    path = os.path.join(HERE, "heat72k_identity_target_m8.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("WROTE", path, flush=True)

if __name__ == "__main__":
    main()
