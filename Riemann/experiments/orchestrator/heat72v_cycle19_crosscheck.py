#!/usr/bin/env python3
"""heat72v — cross-check of m2's cycle-19 §1.3 claims on m1's independent
zeta2_C instrument (route-B ancestry; mpmath vs their scipy code path).

Claims under check (their letter, commit fdadbef):
  (1) F_{1/sqrt(50)} has a real zero at sigma0 = 0.5287118225735156977825694186946
      (dps 30 and dps 50 identical to 25 figures);
  (2) mirror 0.4712881774264843022174305813 is also a zero, sigma0+mirror = 1
      exactly (FE checks the root-finder);
  (3) (2 sigma0 - 1)/|s0|^2 = 0.20542472469850912805 (W=1/s floor constant);
  (4) F_{1/7} has NO real zero in sigma in [0.4, 0.7] (fold pair on the line
      above Delta*; my B1a anchor gives the on-line pair at t=0.0546 instead).

Instrument: zeta2_C verbatim from heat72 (trap-#91 fix; explicit Chowla-
Selberg sum, all (m,k) with 2*pi*D*m*k <= zcut).  Independent of their
eval_epstein.py in code, library (mpmath vs scipy), and ancestry
(route-B lineage vs their cycle-16 E2 lineage).

Usage: python3 heat72v_cycle19_crosscheck.py
"""
import sys
from mpmath import mp, mpf, findroot, fabs, besselk, zeta, gamma, sqrt, pi

mp.dps = 130  # parse literals at full precision FIRST (dps-15 trap)

SIG0_THEIRS = mpf("0.5287118225735156977825694186946")
MIRROR_THEIRS = mpf("0.4712881774264843022174305813")
FLOOR_THEIRS = mpf("0.20542472469850912805")
D_SQRT50 = 1 / sqrt(mpf(50))
D_SEVENTH = mpf(1) / mpf(7)

ZCUT_A = mpf("0.08")
ZCUT_B = mpf("160")


def zeta2_C(s, D):
    """Verbatim from heat72_birth_locus.py (frozen instrument)."""
    nu = s - mpf("0.5")
    zcut = ZCUT_B + ZCUT_A * (mpf(float(abs(s.imag if hasattr(s, 'imag') else 0))) ** 2)
    t1 = zeta(2 * s)
    t2 = sqrt(pi) * gamma(s - mpf("0.5")) * D ** (1 - 2 * s) * zeta(2 * s - 1) / gamma(s)
    total = mpf(0)
    k = 1
    while True:
        z = 2 * pi * D * k
        if z > zcut:
            break
        m = 1
        while z * m <= zcut:
            total += (mpf(m) / k) ** nu * besselk(nu, z * m)
            m += 1
        k += 1
    t3 = (4 * pi ** s / gamma(s)) * D ** (mpf("0.5") - s) * total
    return t1 + t2 + t3


def main():
    print("heat72v — cycle-19 cross-check on m1 zeta2_C (independent ancestry)",
          flush=True)
    print(f"D = 1/sqrt(50) = {mp.nstr(D_SQRT50, 30)}  (vs Delta* "
          f"{mp.nstr(mpf('0.141733239663887191395415685084185024'), 20)}: "
          f"{'BELOW' if D_SQRT50 < mpf('0.141733239663239663887191395415685084185024') else '?'})",
          flush=True)

    # (1) polish the real zero from their printed 25-figure value
    for dps in (50, 60):
        mp.dps = dps
        f = lambda x: zeta2_C(x, D_SQRT50)
        s0 = findroot(f, SIG0_THEIRS, tol=mpf("1e-45"), maxsteps=30)
        resid = abs(zeta2_C(s0, D_SQRT50))
        dev = abs(s0 - SIG0_THEIRS)
        print(f"(1) dps {dps}: sigma0 = {mp.nstr(s0, 30)}  "
              f"|resid|={mp.nstr(resid, 3)}  dev-from-theirs={mp.nstr(dev, 3)}",
              flush=True)

        # (2) mirror check: evaluate their mirror point + polish if a zero
        r_mirror = abs(zeta2_C(MIRROR_THEIRS, D_SQRT50))
        m0 = findroot(f, MIRROR_THEIRS, tol=mpf("1e-45"), maxsteps=30)
        sum_check = s0 + m0
        print(f"(2) mirror: |F(theirs-mirror)|={mp.nstr(r_mirror, 3)}  "
              f"polished mirror = {mp.nstr(m0, 30)}  "
              f"sigma0+mirror = {mp.nstr(sum_check, 20)}  "
              f"dev-from-1={mp.nstr(abs(sum_check - 1), 3)}", flush=True)

        # (3) floor constant from MY polished sigma0
        floor = (2 * s0 - 1) / (s0 * s0)
        print(f"(3) (2s0-1)/s0^2 = {mp.nstr(floor, 25)}  "
              f"theirs 0.20542472469850912805  "
              f"dev={mp.nstr(floor - FLOOR_THEIRS, 3)}", flush=True)

    # (4) F_{1/7} real-axis scan [0.4, 0.7]
    mp.dps = 50
    lo, hi, h = mpf("0.4"), mpf("0.7"), mpf("0.005")
    xs, vs = [], []
    x = lo
    while x <= hi:
        xs.append(x)
        vs.append(zeta2_C(x, D_SEVENTH))
        x += h
    sgn_changes = [(xs[i], vs[i], xs[i + 1], vs[i + 1])
                   for i in range(len(vs) - 1) if vs[i] * vs[i + 1] < 0]
    print(f"(4) F_1/7 real scan [{mp.nstr(lo,2)},{mp.nstr(hi,2)}] h={mp.nstr(h,3)}: "
          f"{len(xs)} points, sign changes = {len(sgn_changes)}", flush=True)
    for (a, fa, b, fb) in sgn_changes:
        print(f"    bracket ({mp.nstr(a,4)}, {mp.nstr(b,4)}) values "
              f"({mp.nstr(fa,3)}, {mp.nstr(fb,3)})", flush=True)
    min_i = min(range(len(vs)), key=lambda i: abs(vs[i]))
    print(f"    min |F| on grid at sigma={mp.nstr(xs[min_i],4)}: "
          f"{mp.nstr(vs[min_i], 6)}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
