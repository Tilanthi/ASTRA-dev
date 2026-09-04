"""End-to-end synthetic test of the master identity A+B = u(1) - Z + Arch1
on a toy phi (single bump, support [-1,1]): every leg computed independently;
closure must be ~0 if the identity is right. Small support => u decays like
e^{-|t|}, arch integral converges fast, no truncation excuse.
Corrected kernel: K(t) = 0.5[ps(s/2)+ps((1-s)/2)] - log(pi).
"""
from mpmath import (mp, mpf, mpc, exp, quad, fabs, zetazero, digamma,
                    log as mplog, re as mpre, im as mpi, pi)

mp.dps = 30

def bump(x):
    return exp(-1/(1-x*x)) if fabs(x) < 1 else mpf(0)

def phi(x):
    return bump(x)

EDS = [mpf(-1), mpf(1)]

def lam(n):
    # von Mangoldt
    if n == 1: return mpf(0)
    m = n; f = 2; e = 0; last = mpf(0); distinct = 0
    d = 2
    while d*d <= n:
        if n % d == 0:
            distinct += 1; last = mplog(d)
            while n % d == 0: n //= d
        d += 1 if d == 2 else 2
        if d*d > n and n > 1: break
    if n > 1 and distinct >= 1: return mpf(0)   # two distinct primes
    if n > 1: return mplog(n)                    # n itself prime, exponent 1 -> but exponent?
    return last

def lam2(n):
    m = n; p = 2; last = mpf(0); cnt = 0
    while m > 1:
        if m % p == 0:
            e = 0
            while m % p == 0: m //= p; e += 1
            cnt += 1; last = mplog(p)
        p += 1
    return last if cnt == 1 else mpf(0)

u1 = quad(lambda x: phi(x)*exp(x), EDS)
A = mpf(0); B = mpf(0); k = 1; nt = 0
while True:
    n = 2
    # enumerate prime powers p^k with k*log p <= 1 (support |x|<=1)
    # do it directly: p^k <= e
    break
import math
for p in [2,3,5,7]:
    lp = mplog(p); kk = 1
    while kk*lp <= 1:
        sh = kk*lp
        if sh <= 1:
            v = phi(sh); w = phi(-sh)
            A += lp*v
            B += exp(-sh)*lp*w
            nt += 1
        kk += 1
P = A + B
Z = mpf(0); n = 1
while True:
    g = mpi(zetazero(n))
    if g > 120: break
    Z += 2*mpre(quad(lambda x: phi(x)*exp(mpc(mpf('0.5'), g)*x), EDS))
    n += 1

def kern_u_re(t):
    s = mpc(mpf('-0.5'), t)
    K = digamma(s/2)/2 + digamma((1-s)/2)/2 - mplog(pi)
    U = quad(lambda x: phi(x)*exp(s*x), EDS)
    return mpre(K*U)      # COMPLEX product, then real part (trap #103)

panels = [i*200//20 for i in range(21)]
Arch1 = 2*quad(kern_u_re, panels, maxdegree=12)/(2*pi)
print(f"u(1)   = {mp.nstr(u1, 15)}")
print(f"A      = {mp.nstr(A, 15)}   B = {mp.nstr(B, 15)}  ({nt} pp terms)")
print(f"Z(60)  = {mp.nstr(Z, 15)}")
print(f"Arch1  = {mp.nstr(Arch1, 15)}")
print(f"CLOSURE A+B-u(1)+Z-Arch1 = {mp.nstr(P - u1 + Z - Arch1, 8)}")
