#!/usr/bin/env python3
"""heat72t — post-hoc trap-#99 guard over ALL published dps-45 U tables
(the r4 standing rule, executed properly: recompute the tail zero-columns at
dps 60 and compare against the DUMPED strings, so the certificate covers the
persisted artifact rather than an in-process copy).

Covers both dumps:
  machine1_heat72r_u45_matrices.json  (M64 blocks; heat72r had no in-runner
                                       dps-60 check)
  machine1_heat72s_m32_u45_matrices.json (M32 blocks; heat72s's in-runner
                                       guard ran at ambient dps by trap #101
                                       and printed vacuous 0.0)

For each block: last TWO zero-columns (the contaminated region was the tail),
all rows, quad at dps 60, max rel diff vs dumped U. PASS = max rel diff
< 1e-30 (dps-45 truncation floor; the trap-#99 failure mode shows up at
1e-2..1e0 scale). Trap #101 discipline: precision is SET inside the check.

Usage: python3 heat72t_posthoc_guard.py
"""
import json, re, sys
from mpmath import mp, mpf, mpc, exp, quad, fabs, zetazero, im as mpim

DUMPS = [("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
          "machine1_heat72r_u45_matrices.json", 64),
         ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
          "machine1_heat72s_m32_u45_matrices.json", 32)]
GEN = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat70_genomes_m8_m64.json")
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


def main():
    mp.dps = 45
    genomes = json.load(open(GEN))["genomes"]
    all_pass = True
    for path, m in DUMPS:
        try:
            blocks = json.load(open(path))
        except FileNotFoundError:
            print(f"(skip {path.split('/')[-1]}: not present)", flush=True)
            continue
        for tag in sorted(blocks):
            blk = blocks[tag]
            if blk.get("m") != m:
                print(f"[{tag}] m mismatch vs {m} -- skip", flush=True)
                continue
            nz = blk["nz"]
            seed = tag.split("_")[0]
            g = genomes[f"{seed}/M64"][:m]
            phis, eds = zip(*[make_phi(f) for f in g])
            zs, n = [], 1
            while len(zs) < nz:
                zs.append(zetazero(n)); n += 1
            mp.dps = 60                       # trap #101: SET it, don't assume it
            worst = (mpf(0), None)
            for j in (nz-1, nz-2):
                rho = zs[j]
                for a in range(m):
                    u60 = quad(lambda t: phis[a](t)*exp(rho*t), eds[a])
                    ud = mcdeser(blk["U"][a][j])
                    r = abs(u60 - ud)/abs(u60)
                    if r > worst[0]:
                        worst = (r, (a+1, j+1))
            mp.dps = 45
            verdict = "PASS" if worst[0] < mpf('1e-30') else "FAIL"
            if verdict == "FAIL":
                all_pass = False
            print(f"[{tag}] dps-60 tail-columns check ({nz-1},{nz}): "
                  f"max rel diff {mp.nstr(worst[0], 4)} at {worst[1]} "
                  f"[gamma_max={blk.get('gamma_max', '?')}] {verdict}", flush=True)
    print(f"POST-HOC GUARD: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}",
          flush=True)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
