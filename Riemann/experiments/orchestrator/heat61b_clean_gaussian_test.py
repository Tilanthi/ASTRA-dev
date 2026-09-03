"""heat61b — clean-formula isolation test for G0's residual ~1.5e-3.

The main-grid G0 run (heat61_g0_balance.out, run 3) closed to ~1.5e-3 absolute
after the prime-doubling fix identified by the failure structure and confirmed
against the source (single W_p sum, transpose folded in; W_r = V_r + V_r(g^tau)
stays doubled). That residual is too large for the 1e-6 gate. This script
removes ALL grid machinery to decide whether the residual is numerical or a
missing formula term:

Test function: g(u) = exp(-(log u)^2 / 2)  -- the UNWINDOWED Gaussian in
x = log u. Not compactly supported (outside Burnol's strict class) but its
tail beyond |x| > 8 is e^{-32} ~ 1e-14 and every piece has closed form:

  gh(s) = sqrt(2 pi) e^{s^2/2}                       (exact)
  zero side: gh(rho) gh(1-rho) = 2 pi e^{1/4 - gamma^2}  (exact, real);
             first zero gamma_1 = 14.13... -> e^{-199.6}: ZERO SIDE = 0
             to ~1e-85. The identity therefore reads, numerically:
             gh(0) + gh(1)  ==  Sum_p W_p(g) + W_r(g)   to machine precision.

  W_p(g) = log p * Sum_k [ e^{-(k L)^2/2} + e^{-k L} e^{-(k L)^2/2} ],
           L = log p (both pieces closed form).
  V_r(g) = c0 * g(1) + I1 + I2,  c0 = (log pi + gamma)/2,  g(1) = 1
           I1 = Int_0^inf e^{-x^2/2} dx = sqrt(pi/2)
           I2 = Int_0^inf (e^{-x^2/2} - 1)/(e^{2x} - 1) dx   (1-D quadrature)
  V_r(g^tau): g^tau(u) = u^{-1} e^{-(log u)^2/2}, i.e. f^tau(x) = e^{-x-x^2/2}
           I1t = Int_0^inf e^{-x - x^2/2} dx = e^{1/2} sqrt(pi/2) erfc(1/sqrt2)
           I2t = Int_0^inf (e^{-x-x^2/2} - 1)/(e^{2x} - 1) dx  (1-D quadrature)
           g^tau(1) = 1.

Prime sum bound: e^{-(log p)^2/2} < 1e-18 for log p > 8.6 -> primes to 6600
suffice; we take 10^6 for safety (k=1 only beyond log p > 8/har... k while
(kL)^2/2 < 40).
"""
import mpmath as mp
import numpy as np

mp.mp.dps = 30

# ----- left side -----
gh0 = mp.sqrt(2 * mp.pi)
gh1 = mp.sqrt(2 * mp.pi) * mp.e ** mp.mpf("0.5")
left = gh0 + gh1

# ----- prime side: W_p sum -----
NMAX = 10 ** 6
sieve = np.ones(NMAX + 1, dtype=bool)
sieve[:2] = False
for i in range(2, int(NMAX ** 0.5) + 1):
    if sieve[i]:
        sieve[i * i::i] = False
primes = np.nonzero(sieve)[0]

sump = mp.mpf(0)
for p in primes:
    L = mp.log(p)
    k = 1
    while (k * L) ** 2 / 2 < 40:          # term < e^-40 ~ 1e-18
        e = mp.e ** (-((k * L) ** 2) / 2)
        sump += L * (e + mp.e ** (-k * L) * e)
        k += 1

# ----- archimedean: V_r(g) + V_r(g^tau) -----
c0 = (mp.log(mp.pi) + mp.euler) / 2
I1 = mp.sqrt(mp.pi / 2)
I2 = mp.quad(lambda x: (mp.e ** (-x ** 2 / 2) - 1) / (mp.e ** (2 * x) - 1),
             [0, mp.inf])
I1t = mp.e ** mp.mpf("0.5") * mp.sqrt(mp.pi / 2) * mp.erfc(1 / mp.sqrt(2))
I2t = mp.quad(lambda x: (mp.e ** (-x - x ** 2 / 2) - 1) / (mp.e ** (2 * x) - 1),
              [0, mp.inf])
Vr = c0 + I1 + I2
Vrt = c0 + I1t + I2t
right = sump + Vr + Vrt

print("heat61b clean isolation test  (g = exp(-(log u)^2/2), zero side = 0 to ~1e-85)")
print(f"  left  = gh(0)+gh(1)                    = {mp.nstr(left, 20)}")
print(f"  right = Sum_p W_p + V_r + V_r(g^tau)   = {mp.nstr(right, 20)}")
print(f"  parts: Sum_p W_p = {mp.nstr(sump, 16)}")
print(f"         V_r      = {mp.nstr(Vr, 16)}   (c0 {mp.nstr(c0, 8)}, I1 {mp.nstr(I1, 8)}, I2 {mp.nstr(I2, 10)})")
print(f"         V_r(g^t) = {mp.nstr(Vrt, 16)}   (I1t {mp.nstr(I1t, 10)}, I2t {mp.nstr(I2t, 10)})")
diff = left - right
print(f"  left - right = {mp.nstr(diff, 8)}   (rel {mp.nstr(abs(diff/left), 3)})")
print()
print("  If |diff| < 1e-12: the 1.5e-3 residual in heat61 is NUMERICAL (grid/FFT).")
print("  If |diff| ~ 1e-3-scale: a formula term is missing -- fit which piece")
print("  diff/h'(0)-type candidates: diff vs c0, I1, I2 coefficients printed above.")
