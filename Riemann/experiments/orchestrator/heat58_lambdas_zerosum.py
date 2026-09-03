"""heat58 — Li/Keiper coefficients via the ZERO-SUM instrument, as the
independent cross-check of machine 3's from-scratch contour instrument
(Letter 20: lambda_1..15 positive, lambda_1 ~= 0.023096, lambda_15 ~=
5.045, contour radius 0.5, no zero table).

Instrument identity (deliberately different, per the no-shared-instrument
rule): lambda_n = SUM over conjugate zero pairs [2 - 2 Re[(1 - 1/rho)^n]].
On the critical line |1-1/rho| = 1 exactly, the term is 2-2cos(n theta)
with theta ~ -1/gamma, so the sum converges ABSOLUTELY like n^2/gamma^2 —
a truncated sum to height T has tail ~ n^2 log(T)/T.

NOTE THE ASYMMETRY, stated for the record: this instrument ASSUMES the
pairing (i.e. RH for the zeros it uses — mp.zetazero returns critical-line
zeros only); machine 3's contour instrument assumes nothing about zeros.
Agreement therefore validates the INSTRUMENTS against each other under
the RH-controlled setting; it is not evidence FOR RH (their letter says
the same about their side). This is the week's two-instrument pattern at
the positivity lane's service.

Prints lambda_1..15, positivity check, endpoints vs their quoted values,
and the pair-sum tail estimate. dps 50, zeros to T=2000 (index ~2700).
Serial — cheap.
"""
import mpmath as mp

mp.mp.dps = 50
NZ = 2700
print(f"== heat58: lambda_n zero-sum instrument, zeros 1..{NZ} ==", flush=True)
gammas = [mp.im(mp.zetazero(k)) for k in range(1, NZ+1)]
print(f"gamma_max = {mp.nstr(gammas[-1], 10)}", flush=True)

lam = {}
for n in range(1, 16):
    s = mp.mpf(0)
    for g in gammas:
        rho = mp.mpc(mp.mpf("0.5"), g)
        s += 2 - 2*mp.re((1 - 1/rho)**n)
    lam[n] = s
    print(f"  lambda_{n:2d} = {mp.nstr(s, 12)}", flush=True)

print(f"\nall positive: {all(v > 0 for v in lam.values())}", flush=True)
print(f"lambda_1  = {mp.nstr(lam[1], 8)}   (m3 contour: 0.023096; "
      f"published lambda_1 = 0.0230957089661...)", flush=True)
print(f"lambda_15 = {mp.nstr(lam[15], 8)}   (m3 contour: 5.045)", flush=True)
tail = mp.mpf(15)**2*mp.log(gammas[-1])/gammas[-1]
print(f"tail estimate at n=15, T={mp.nstr(gammas[-1], 4)}: ~{mp.nstr(tail, 2)} "
      f"(order-of-magnitude, non-certified)", flush=True)
