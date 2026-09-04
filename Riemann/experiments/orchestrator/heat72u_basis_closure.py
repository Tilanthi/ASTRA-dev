#!/usr/bin/env python3
"""heat72u basis closure — localize the basis-1/2 discrepancy.
For bases 1,2,3 of s1/M8 (basis 0 done in run-2): compute MY prime side
(A+B sieve-exact), MY zero side Z(T=150, zetazero), Simpson arch with the
CORRECTED kernel, and the per-basis closure  A+B - u(1) + Z - Arch.
Basis 0 closed at -4.0e-3 (quadrature scale). If bases 1/2 fail to close
with my numbers, the m3-L131 table columns for those bases are suspect;
if they close, my earlier basis12 Simpson had the error.
"""
import json
from mpmath import (mp, mpf, mpc, exp, quad, fabs, zetazero, digamma,
                    log as mplog, re as mpre, im as mpi, pi)

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

    NMAX = 3300
    isp = list(range(NMAX+1))
    for p in range(2, int(NMAX**0.5)+1):
        if isp[p] == p:
            for q in range(p*p, NMAX+1, p):
                if isp[q] == q:
                    isp[q] = p

    for bi in [1, 2, 3]:
        phi, eds = make_phi(genomes[key][bi])
        lo, hi = eds[0], eds[-1]
        u1 = quad(lambda x: phi(x)*exp(x), eds)

        A = mpf(0); B = mpf(0); nterm = 0
        for p in range(2, NMAX+1):
            if isp[p] != p:
                continue
            lp = mplog(p); k = 1
            while k*lp <= 8 + 1e-9:
                sh = k*lp
                if lo <= sh <= hi:
                    v = phi(sh)
                    if v != 0:
                        A += lp*v; nterm += 1
                if lo <= -sh <= hi:
                    v = phi(-sh)
                    if v != 0:
                        B += exp(-sh)*lp*v; nterm += 1
                k += 1
        P = A + B

        Z = mpf(0); n = 1
        while True:
            g = mpi(zetazero(n))
            if g > 150:
                break
            Z += 2*mpre(quad(lambda x: phi(x)*exp(mpc(mpf('0.5'), g)*x), eds))
            n += 1

        # Simpson arch, corrected kernel, N=400 on [-80,80]
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
        Arch = tot*h/(3*2*pi)

        pred = P - u1 + Z
        print(f"basis {bi}: u(1)={mp.nstr(u1,10)}  Prime={mp.nstr(P,10)} ({nterm} terms)"
              f"  Z(150)={mp.nstr(Z,8)}", flush=True)
        print(f"  Arch_simpson={mp.nstr(Arch,10)}  identity_pred={mp.nstr(pred,10)}"
              f"  closure={mp.nstr(pred-Arch,6)}", flush=True)
        print(f"  [m3 L131: Endpoint/Prime/Arch/Zero -> their-gap-basis]", flush=True)


if __name__ == '__main__':
    main()
