#!/usr/bin/env python3
"""heat72w — the kappa-side analytic Taylor leg for a3 (m1-L136 repair leg).

Context (m1-L136): the L135 s3 claim of held kappa-side constants was an
overclaim; this extraction is dated post-correction. Route: analytic
differentiation of the CLOSED Chowla-Selberg form of zeta2_C at the fold
(s = 1/2 + u, D = Delta* + w), by 2-D trapezoid-on-torus — geometric
convergence, no derivative-order penalty (the m1-L135 s4 geometry).

Object (verbatim zeta2_C structure, generalized to complex s AND complex D):
  F(s,D) = t1 + t2 + t3
  t1 = zeta(2s)
  t2 = sqrt(pi)*Gamma(s-1/2)*D^(1-2s)*zeta(2s-1)/Gamma(s)
  t3 = (4*pi^s/Gamma(s)) * D^(1/2-s) * S(nu,D),
  S(nu,D) = sum_{k>=1} sum_{m>=1} (m/k)^nu * K_nu(2*pi*D*m*k),  nu = s-1/2,
  truncated at 2*pi*Re(D)*m*k <= ZCUT (tail < e^-ZCUT ~ 1e-96 at ZCUT=220).

Singularity bounds: |u| < 1/2 (zeta(2u) pole at u=1/2); |w| < Delta* = 0.1417
(D = 0). On-contour u != 0 always, so the t1/t2 pole pair at u=0 is never
sampled (they cancel: zeta(1+2u) ~ +1/(2u), t2 ~ -1/(2u) via Gamma(u) pole
against zeta(0) = -1/2); the centre is regular for the SUM.

Bivariate Taylor F = sum c_jk u^j w^k via 2-D DFT on the torus. Layer
constants (t-derivatives via d_t^k = i^k d_u^k, even orders alternate sign):
  F2 = -2*c20          F4 = 24*c40          F6 = -720*c60
  G0 = c01             G2 = -2*c21          G4 = 24*c41
  H0 = c02             H2 = -2*c22          K0 = c03
  U1 = -2*G0/F2                                        (= a, registry check)
  U2 = -2*[(F4/24)a^2 + (G2/2)a + H0]/F2               (= -b, check)
  U3 = -2*[(F4/12)aU2 + (F6/720)a^3 + (G2/2)U2
            + (G4/24)a^2 + (H2/2)a + K0]/F2            (= a3, DELIVERABLE)

Free structural checks printed per rung (no extra cost):
  - |c00| ~ |F(1/2,Delta*)| ~ 0        (fold receipt)
  - |c10|, |c30|, |c50| ~ 0 vs |c20|   (fold evenness in t: odd pure-t
                                         Taylor coefficients vanish at the
                                         fold — the fold IS that symmetry)

Guards (#99/#101 discipline):
  - guard A: 3 torus samples re-evaluated at dps+15, rel diff < 1e-55
  - guard B: one u-column re-summed with ZCUT*1.35, rel diff < 1e-55
  - U1/U2 checked against registry a = 2.645521411811663 and
    U2reg = +7.46245287679 (= -b); reported, NOT substituted (self-consistent
    assembly from own-extracted constants only)

Ladder: rungs differ in radii/points/dps/phase; U3 must agree across rungs.
Rung-1 aliasing: (0.25/0.5)^48 ~ 4e-15, (0.08/0.1417)^48 ~ 6e-12 — both far
below the ~1e-6 relative the U3 cancellation demands.

Usage: python3 heat72w_kappa_a3.py RUNG     (1 | 2 | 3 | all)
"""
import sys
import time

from mpmath import (mp, mpf, mpc, pi, sqrt, gamma, zeta, besselk,
                    re as mpre)

DSTAR = mpf("0.141733239663887191395415685084185024")
A_REG = mpf("2.645521411811663")
U2_REG = mpf("7.46245287679")
ZCUT = mpf("220")

RUNGS = {
    1: dict(rho_t="0.25", M_t=40, rho_D="0.08", M_D=32, dps=70, ph_t="0", ph_D="0"),
    2: dict(rho_t="0.18", M_t=32, rho_D="0.05", M_D=24, dps=70, ph_t="0.5", ph_D="0.5"),
    3: dict(rho_t="0.22", M_t=40, rho_D="0.07", M_D=32, dps=70, ph_t="0.25", ph_D="0.75"),
}


def zeta2_C_ext(s, D, zcut=ZCUT):
    """Chowla-Selberg continuation, complex s and complex D (heat72 frozen
    structure generalized; truncation on 2*pi*Re(D)*m*k)."""
    nu = s - mpf("0.5")
    t1 = zeta(2 * s)
    t2 = sqrt(pi) * gamma(nu) * D ** (1 - 2 * s) * zeta(2 * s - 1) / gamma(s)
    total = mpc(0)
    k = 1
    reD = mpre(D)
    while True:
        if 2 * pi * reD * k > zcut:
            break
        z = 2 * pi * D * k
        m = 1
        while 2 * pi * reD * k * m <= zcut:
            total += (mpf(m) / k) ** nu * besselk(nu, z * m)
            m += 1
        k += 1
    t3 = (4 * pi ** s / gamma(s)) * D ** (mpf("0.5") - s) * total
    return t1 + t2 + t3


def zeta2_C_frozen(s, D):
    """Frozen real-D reference (heat72/heat72v verbatim) for the pre-flight
    agreement check at u != 0 points."""
    nu = s - mpf("0.5")
    zcut = mpf("160") + mpf("0.08") * abs(s.imag) ** 2
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


def preflight(dps):
    """Validate zeta2_C_ext against the frozen real-D version at u != 0."""
    mp.dps = dps + 10
    pts = [(mpc("0.5", "0.25"), DSTAR),
           (mpc("0.75", "0"), DSTAR + mpf("0.05")),
           (mpc("0.5", "-0.18"), DSTAR + mpf("0.03"))]
    worst = mpf(0)
    for s, D in pts:
        a = zeta2_C_ext(s, D)
        b = zeta2_C_frozen(s, D)
        rel = abs(a - b) / abs(b)
        worst = max(worst, rel)
    print(f"PREFLIGHT ext-vs-frozen worst rel diff: {mp.nstr(worst, 5)}", flush=True)
    return worst


def rung(n, cfg):
    mp.dps = cfg["dps"]
    rho_t = mpf(cfg["rho_t"]); M_t = cfg["M_t"]
    rho_D = mpf(cfg["rho_D"]); M_D = cfg["M_D"]
    ph_t = mpf(cfg["ph_t"]); ph_D = mpf(cfg["ph_D"])
    dps = cfg["dps"]
    print(f"\n===== RUNG {n}: rho_t={cfg['rho_t']} M_t={M_t} "
          f"rho_D={cfg['rho_D']} M_D={M_D} dps={dps} "
          f"ph_t={cfg['ph_t']} ph_D={cfg['ph_D']} =====", flush=True)

    two_pi = 2 * pi
    us = [rho_t * exp_ip(two_pi * (mpf(i) + ph_t) / M_t) for i in range(M_t)]
    ws = [rho_D * exp_ip(two_pi * (mpf(j) + ph_D) / M_D) for j in range(M_D)]

    t0 = time.time()
    F = [[None] * M_D for _ in range(M_t)]
    for i, u in enumerate(us):
        s = mpf("0.5") + u
        for j, w in enumerate(ws):
            F[i][j] = zeta2_C_ext(s, DSTAR + w)
        if (i + 1) % 8 == 0 or i == M_t - 1:
            el = time.time() - t0
            eta = el / (i + 1) * (M_t - i - 1)
            print(f"  sampled u-column {i+1}/{M_t}  elapsed {el:.0f}s  "
                  f"eta {eta:.0f}s", flush=True)

    # --- guard A: 3 samples at dps+15 ---
    mp.dps = dps + 15
    guard_pairs = [(0, 0), (M_t // 3, M_D // 2), (M_t - 1, M_D - 1)]
    gA = mpf(0)
    for (i, j) in guard_pairs:
        v = zeta2_C_ext(mpf("0.5") + us[i], DSTAR + ws[j])
        rel = abs(v - F[i][j]) / abs(F[i][j])
        gA = max(gA, rel)
    # --- guard B: u-column 0 re-summed with ZCUT*1.35 ---
    gB = mpf(0)
    for j in range(M_D):
        v = zeta2_C_ext(mpf("0.5") + us[0], DSTAR + ws[j], zcut=ZCUT * mpf("1.35"))
        rel = abs(v - F[0][j]) / abs(F[0][j])
        gB = max(gB, rel)
    mp.dps = dps
    print(f"  GUARD A (dps+15 recheck x3):    worst rel {mp.nstr(gA, 5)}  "
          f"{'PASS' if gA < mpf('1e-55') else 'FAIL'}", flush=True)
    print(f"  GUARD B (ZCUT*1.35 column):     worst rel {mp.nstr(gB, 5)}  "
          f"{'PASS' if gB < mpf('1e-55') else 'FAIL'}", flush=True)

    # --- 2-D DFT: c_jk = (1/(M_t*M_D)) sum_ij F_ij u_i^-j w_l^-k ---
    max_j, max_k = 6, 3
    upow = [[us[i] ** (-j) for i in range(M_t)] for j in range(max_j + 1)]
    wpow = [[ws[l] ** (-k) for l in range(M_D)] for k in range(max_k + 1)]
    norm = 1 / (M_t * M_D)
    c = {}
    for j in range(max_j + 1):
        for k in range(max_k + 1):
            acc = mpc(0)
            for i in range(M_t):
                fi = F[i]
                ui = upow[j][i]
                row = mpc(0)
                for l in range(M_D):
                    row += fi[l] * wpow[k][l]
                acc += ui * row
            c[(j, k)] = norm * acc
    immax = max(abs(mpre(v.imag)) for v in c.values() if abs(v) > 0)
    relim = max(abs(mpre(v.imag)) / abs(v) for v in c.values() if abs(v) > 0)
    print(f"  coefficient imag-parts: max |Im| {mp.nstr(immax, 5)}, "
          f"max |Im|/|c| {mp.nstr(relim, 5)}  (real-analyticity check)",
          flush=True)

    def realc(j, k):
        return mpre(c[(j, k)].real)

    c00 = abs(c[(0, 0)])
    sym = [abs(c[(1, 0)]), abs(c[(3, 0)]), abs(c[(5, 0)])]
    c20a = abs(c[(2, 0)])
    print(f"  FOLD CHECK  |c00| = {mp.nstr(c00, 5)}   (target ~0)", flush=True)
    print(f"  EVENNESS    |c10|,|c30|,|c50| = "
          f"{mp.nstr(sym[0], 3)}, {mp.nstr(sym[1], 3)}, {mp.nstr(sym[2], 3)}"
          f"   vs |c20| = {mp.nstr(c20a, 5)}", flush=True)

    print("  --- Taylor coefficients c_jk (real parts) ---", flush=True)
    for j in range(max_j + 1):
        rowtxt = "  ".join(f"c{j}{k}={mp.nstr(realc(j, k), 12)}"
                           for k in range(max_k + 1))
        print(f"    {rowtxt}", flush=True)

    F2 = -2 * realc(2, 0)
    F4 = 24 * realc(4, 0)
    F6 = -720 * realc(6, 0)
    G0 = realc(0, 1)
    G2 = -2 * realc(2, 1)
    G4 = 24 * realc(4, 1)
    H0 = realc(0, 2)
    H2 = -2 * realc(2, 2)
    K0 = realc(0, 3)
    print("  --- layer constants ---", flush=True)
    print(f"    F2 = {mp.nstr(F2, 20)}", flush=True)
    print(f"    F4 = {mp.nstr(F4, 20)}", flush=True)
    print(f"    F6 = {mp.nstr(F6, 20)}", flush=True)
    print(f"    G0 = {mp.nstr(G0, 20)}", flush=True)
    print(f"    G2 = {mp.nstr(G2, 20)}", flush=True)
    print(f"    G4 = {mp.nstr(G4, 20)}", flush=True)
    print(f"    H0 = {mp.nstr(H0, 20)}", flush=True)
    print(f"    H2 = {mp.nstr(H2, 20)}", flush=True)
    print(f"    K0 = {mp.nstr(K0, 20)}", flush=True)

    a = -2 * G0 / F2
    U2 = -2 * ((F4 / 24) * a ** 2 + (G2 / 2) * a + H0) / F2
    U3 = -2 * ((F4 / 12) * a * U2 + (F6 / 720) * a ** 3 + (G2 / 2) * U2
               + (G4 / 24) * a ** 2 + (H2 / 2) * a + K0) / F2
    da = abs(a - A_REG) / A_REG
    dU2 = abs(U2 - U2_REG) / U2_REG
    print("  --- assembly ---", flush=True)
    print(f"    U1 = a  = {mp.nstr(a, 20)}   vs reg {mp.nstr(A_REG, 16)}"
          f"   rel dev {mp.nstr(da, 5)}", flush=True)
    print(f"    U2      = {mp.nstr(U2, 20)}   vs reg {mp.nstr(U2_REG, 12)}"
          f"   rel dev {mp.nstr(dU2, 5)}", flush=True)
    # term decomposition (trap #104 remedy: publish the terms beside the sum)
    t_a = (F4 / 12) * a * U2
    t_b = (F6 / 720) * a ** 3
    t_c = (G2 / 2) * U2
    t_d = (G4 / 24) * a ** 2
    t_e = (H2 / 2) * a
    t_f = K0
    bracket = t_a + t_b + t_c + t_d + t_e + t_f
    print("  --- U3 bracket decomposition (trap #104 discipline) ---", flush=True)
    print(f"    (F4/12)aU2 = {mp.nstr(t_a, 18)}", flush=True)
    print(f"    (F6/720)a^3 = {mp.nstr(t_b, 18)}", flush=True)
    print(f"    (G2/2)U2   = {mp.nstr(t_c, 18)}", flush=True)
    print(f"    (G4/24)a^2 = {mp.nstr(t_d, 18)}", flush=True)
    print(f"    (H2/2)a    = {mp.nstr(t_e, 18)}", flush=True)
    print(f"    K0         = {mp.nstr(t_f, 18)}", flush=True)
    print(f"    bracket    = {mp.nstr(bracket, 18)}   (target ~ -a3*F2/2)",
          flush=True)
    print(f"    U3 = a3    = {mp.nstr(U3, 20)}", flush=True)
    print(f"HEAT72W RUNG {n} COMPLETE: U3 = {mp.nstr(U3, 20)}  "
          f"guards {'PASS' if (gA < mpf('1e-55') and gB < mpf('1e-55')) else 'FAIL'}"
          f"  U1dev {mp.nstr(da, 3)}  U2dev {mp.nstr(dU2, 3)}", flush=True)
    return U3


def exp_ip(x):
    """exp(i*x) without importing exp into the module namespace twice."""
    from mpmath import exp, mpc
    return exp(mpc(0, 1) * x)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("heat72w — kappa-side analytic a3 (m1-L136 repair leg; contour route)",
          flush=True)
    print("guarded: dps+15 recheck x3, ZCUT*1.35 column, U1/U2 registry checks,"
          " fold/evenness receipts", flush=True)
    mp.dps = 60
    pf = preflight(50)
    if pf > mpf("1e-40"):
        print("PREFLIGHT FAILED — ext disagrees with frozen; ABORT", flush=True)
        sys.exit(1)
    rungs = [int(which)] if which.isdigit() else [1, 2, 3]
    results = {}
    for n in rungs:
        results[n] = rung(n, RUNGS[n])
    if len(results) > 1:
        vals = list(results.values())
        spread = max(abs(v - vals[0]) / abs(vals[0]) for v in vals)
        per = ", ".join(f"rung{n}: {mp.nstr(v, 17)}" for n, v in results.items())
        print(f"\nHEAT72W ALL COMPLETE: U3 {per}", flush=True)
        print(f"  cross-rung max rel spread: {mp.nstr(spread, 5)}", flush=True)


if __name__ == "__main__":
    main()
