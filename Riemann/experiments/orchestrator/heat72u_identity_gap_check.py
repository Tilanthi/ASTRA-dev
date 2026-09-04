#!/usr/bin/env python3
"""heat72u — independent second-instrument check of m3's Letter-129 identity gap
(scalar Kowalski Prop 1.2.1 on s1/M8 basis 0, my heat72k export target).

Their numbers (scipy/float64):  Endpoint u(1) = -32.11546578397509
  Prime = -32.46680847049009 (45 nonzero terms)   Z(T->300) = +0.45419
  Arch  = -0.25547 (stable t_max 80 -> 150)
  RHS = u(1) - Prime + Arch = 0.096   vs   Z = 0.454   gap ~ 0.358.

My independent derivation (raw contour, no Kowalski transcription):
  FE:  -zeta'/zeta(s) = zeta'/zeta(1-s) + K(t),  K(t) = 0.5[ps(s/2) - ps((1-s)/2)]
  Master:  A + B = u(1) - Z + Arch1   [A = sum Lam(n) phi(log n),
          B = sum Lam(n) phi(-log n)/n,  Arch1 = (1/2pi) int K(t) u(-1/2+it) dt]
  with u(s) = int phi_x(x) e^{s x} dx (Mellin transform in y = e^x).

PRE-REGISTERED PREDICTION (written before running):
  Arch1 = A + B - u(1) + Z ~ +0.1029  (their scipy -0.25547 converged to a
  wrong value; trap-#99's scipy cousin).  FE pointwise exact < 1e-30.
Precision: dps 35 for u/zeros/FE; arch integral at dps 30 with t<=80
(justified by their own convergence table; 3 digits decide +0.103 vs -0.255).
u(1)/u(0) must reproduce the export U1[0]/U0[0] (validates genome choice).

Usage: python3 heat72u_identity_gap_check.py [T_zero] [t_arch]
"""
import json, sys
from mpmath import (mp, mpf, mpc, exp, quad, fabs, zetazero, digamma,
                    zeta, diff, log as mplog, re as mpre, im as mpi, pi)

GEN = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/"
       "machine1_heat70_genomes_m8_m64.json")
EXPORT = ("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
          "machine1_heat72k_identity_target_m8.json")
T_ZERO = int(sys.argv[1]) if len(sys.argv) > 1 else 300
T_ARCH = int(sys.argv[2]) if len(sys.argv) > 2 else 80


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


def zetadolog(s):
    return diff(zeta, s)/zeta(s)


def lam_of(isp, nn):
    """von Mangoldt Lambda(nn) via smallest-prime-factor table."""
    m = nn; distinct = 0; last = mpf(0)
    while m > 1:
        pk = isp[m]; e = 0
        while m % pk == 0:
            m //= pk; e += 1
        distinct += 1; last = mplog(pk)
    return last if distinct == 1 else mpf(0)


def main():
    genomes = json.load(open(GEN))["genomes"]
    expd = json.load(open(EXPORT))["seeds"]["s1/M8"]
    key = "s1/M8" if "s1/M8" in genomes else "s1/M64"
    phi, eds = make_phi(genomes[key][0])
    print(f"genome key {key} basis0; support [{mp.nstr(eds[0],4)}, "
          f"{mp.nstr(eds[-1],4)}], {len(eds)} intervals", flush=True)

    mp.dps = 35
    u1 = quad(lambda x: phi(x)*exp(x), eds)
    u0 = quad(phi, eds)
    print(f"u(1) = {mp.nstr(u1, 20)}  vs export U1[0]: rel "
          f"{mp.nstr(abs(u1-mpf(expd['U1'][0]))/abs(mpf(expd['U1'][0])), 3)}",
          flush=True)
    print(f"u(0) = {mp.nstr(u0, 20)}  vs export U0[0]: rel "
          f"{mp.nstr(abs(u0-mpf(expd['U0'][0]))/abs(mpf(expd['U0'][0])), 3)}",
          flush=True)

    # prime side
    NMAX = 3300
    isp = list(range(NMAX+1))
    for p in range(2, int(NMAX**0.5)+1):
        if isp[p] == p:
            for q in range(p*p, NMAX+1, p):
                if isp[q] == q:
                    isp[q] = p
    A = mpf(0); B = mpf(0); nterm = 0
    lo, hi = eds[0], eds[-1]
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
    print(f"A = {mp.nstr(A, 20)}\nB = {mp.nstr(B, 20)}\n"
          f"Prime A+B = {mp.nstr(P, 20)}  ({nterm} nonzero terms; "
          f"m3 scipy: -32.46680847049009, 45 terms)", flush=True)

    # zero side
    Z = mpf(0); n = 1; nz = 0
    while True:
        g = mpi(zetazero(n))
        if g > T_ZERO:
            break
        Z += 2*mpre(quad(lambda x: phi(x)*exp(mpc(mpf('0.5'), g)*x), eds))
        n += 1; nz += 1
    print(f"Z (T={T_ZERO}, {nz} zeros) = {mp.nstr(Z, 12)}  (m3: 0.45419@300)",
          flush=True)

    # arch side: CORRECTED kernel from the FE (heat72u first run caught the
    # error via its own pointwise check): -z'/z(s) = z'/z(1-s) + K(t) with
    #   K(t) = 0.5[ps(s/2) + ps((1-s)/2)] - log(pi)   [SUM, not difference]
    # classical limit: K(t) -> log(t/2pi) as t->infty (Weil archimedean term).
    mp.dps = 30
    def kern_u_re(t):
        s = mpc(mpf('-0.5'), t)
        K = digamma(s/2)/2 + digamma((1-s)/2)/2 - mplog(pi)
        U = quad(lambda x: phi(x)*exp(s*x), eds)
        return mpre(K*U)      # COMPLEX product, then real part (trap #103)
    # t->-t symmetry: kernel(-t)=conj(kernel(t)), u(-t)=conj(u(t)) => real part doubles
    panels = [i*T_ARCH//16 for i in range(17)]
    arch_num = 2*quad(kern_u_re, panels, maxdegree=10)
    Arch1 = arch_num/(2*pi)
    mp.dps = 35
    print(f"Arch1 = {mp.nstr(Arch1, 20)}  [t_max={T_ARCH}, symmetry-halved]"
          f"\n  m3 scipy: -0.25547; derivation prediction "
          f"A+B-u(1)+Z = {mp.nstr(P-u1+Z, 12)}", flush=True)

    # FE pointwise: -z'/z(s) = z'/z(1-s) + K(t)
    print("FE pointwise |LHS-RHS| at s=-1/2+it:", flush=True)
    for t in ['0.7', '3.3', '17.2', '41.5']:
        tt = mpf(t); s = mpc(mpf('-0.5'), tt)
        lhs = -zetadolog(s)
        rhs = zetadolog(1-s) + digamma(s/2)/2 + digamma((1-s)/2)/2 - mplog(pi)
        print(f"  t={t}: {mp.nstr(abs(lhs-rhs), 3)}", flush=True)

    # Dirichlet spot check at Re 3/2 (truncation-limited, validity only)
    mp.dps = 30
    s = mpc(mpf('1.5'), -mpf('3.3'))
    ds = -zetadolog(s)
    part = mpf(0)
    for nn in range(2, 3000):
        L = lam_of(isp, nn)
        if L:
            part += L*exp(-s*mplog(nn))
    print(f"Dirichlet t=3.3: -z'/z = {mp.nstr(ds, 10)}  sum(n<3e4) = "
          f"{mp.nstr(part, 10)} (tail-limited agreement expected)",
          flush=True)

    mp.dps = 35
    print(f"\nMASTER CLOSURE  A+B - u(1) + Z - Arch1 = "
          f"{mp.nstr(P - u1 + Z - Arch1, 6)}  (0 => m3's formula correct, "
          "gap located in their arch integral)", flush=True)
    print(f"gap (their arch deficit) = {mp.nstr(Arch1 - (P-u1+Z), 8)}",
          flush=True)


if __name__ == '__main__':
    main()
