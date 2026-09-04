#!/usr/bin/env python3
"""heat72u arch multibasis — mpmath adaptive-quad Arch1 (CORRECTED kernel)
for bases 1,2,3 of s1/M8 (basis 0 done in run-2: +0.10681, closure -4.0e-3).
The closure run supplied my independent Prime/Z(150)/u(1) per basis; this
script computes the arch leg only and prints the closure per basis:
    closure = (Prime - u(1) + Z) - Arch1
Targets from identity + confirmed columns: [-0.5598, -0.0285, +0.3218].
"""
import json, sys
from mpmath import (mp, mpf, mpc, exp, quad, fabs, digamma,
                    log as mplog, re as mpre, pi)

mp.dps = 25
GEN = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat70_genomes_m8_m64.json")
# from heat72u_basis_closure.out (my independent values, confirmed vs m3 L131)
CLOSURE_INPUT = {1: dict(u1='3.236997875', P='2.630664972', Z='0.046509681',
                         target='-0.5598'),
                 2: dict(u1=None, P=None, Z=None, target='-0.0285'),
                 3: dict(u1=None, P=None, Z=None, target='+0.3218')}


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
    genomes = json.load(open(GEN))["genomes"]
    key = "s1/M8" if "s1/M8" in genomes else "s1/M64"
    bases = [int(a) for a in sys.argv[1:4]] or [1, 2, 3]   # trap #100: T_MAX is argv[4], not a basis
    for bi in bases:
        phi, eds = make_phi(genomes[key][bi])
        T_ARCH = int(sys.argv[4]) if len(sys.argv) > 4 else 150

        def kern_u_re(t):
            s = mpc(mpf('-0.5'), t)
            K = digamma(s/2)/2 + digamma((1-s)/2)/2 - mplog(pi)
            U = quad(lambda x: phi(x)*exp(s*x), eds)
            return mpre(K*U)      # COMPLEX product, then real part (trap #103)
        panels = [i*T_ARCH//16 for i in range(17)]
        Arch1 = 2*quad(kern_u_re, panels, maxdegree=10)/(2*pi)
        print(f"basis {bi}: Arch1 (mpmath adaptive, t_max={T_ARCH}) = "
              f"{mp.nstr(Arch1, 12)}  [identity target {CLOSURE_INPUT[bi]['target']}]",
              flush=True)


if __name__ == '__main__':
    main()
