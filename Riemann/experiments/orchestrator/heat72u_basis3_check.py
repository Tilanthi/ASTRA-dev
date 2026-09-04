#!/usr/bin/env python3
"""heat72u basis-3 cross-verification — independent check of one of the four
m3-L131 predictions: Arch1_true(basis 3) = Prime - Endpoint + Zero = +0.3218
(their wrong-kernel scipy value: -0.2683). Same corrected kernel as run-2:
K(t) = 0.5[ps(s/2) + ps((1-s)/2)] - log(pi), s = -1/2+it.
Runs both Simpson (dps 25) and reports; genome s1/M8 basis 3.
"""
import json
from mpmath import (mp, mpf, mpc, exp, quad, fabs, digamma, pi,
                    log as mplog, re as mpre)

mp.dps = 25
GEN = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat70_genomes_m8_m64.json")


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
    phi, eds = make_phi(genomes[key][3])

    def u_re(t):
        s = mpc(mpf('-0.5'), t)
        return mpre(quad(lambda x: phi(x)*exp(s*x), eds))

    def kern(t):
        s = mpc(mpf('-0.5'), t)
        return mpre(digamma(s/2)/2 + digamma((1-s)/2)/2 - mplog(pi))

    N = 400
    a, b = mpf(-80), mpf(80)
    h = (b-a)/N
    tot = mpf(0)
    for i in range(N+1):
        t = a + i*h
        w = mpf(4) if i % 2 == 1 else mpf(2)
        if i == 0 or i == N: w = mpf(1)
        tot += w*kern(t)*u_re(t)
    arch = tot*h/(3*2*pi)
    print(f"Simpson CORRECTED-kernel Arch1 (basis 3, N={N}) = {mp.nstr(arch, 10)}")
    print("m3-L131 identity prediction (Prime-Endpoint+Zero) = +0.3218")
    print("m3 wrong-kernel scipy value                        = -0.2683")


if __name__ == '__main__':
    main()
