#!/usr/bin/env python3
"""heat68 — rectangular-Epstein REAL zeros, dual-source, per prereg 502dd9b
+ AMENDMENT-1 (C2 re-scope) + AMENDMENT-2 (A k-power fix, evaluator-B registered,
equivalence asserts, C2 tail formula).

Evaluator A (mine, Bessel; AMENDMENT-2 FIXED — t3 carries (m/k)^{s-1/2}):
    zeta2 = zeta(2s) + sqrt(pi)Gamma(s-1/2) D^{1-2s} zeta(2s-1)/Gamma(s)
            + (4 pi^s/Gamma(s)) D^{1/2-s} sum_{k,m>=1} (m/k)^{s-1/2} K_{s-1/2}(2 pi D k m)
Evaluator B (mine, theta-integral; registered AMENDMENT-2):
    Gamma(s) 2 zeta2 = int_pi^inf t^{s-1}(Theta-1)dt + (pi^s/D) int_1^inf u^{-s}(thth-1)du
                       + pi^s/(D(s-1)) - pi^s/s
Source B (literature, Betermin-Samaj-Travenec arXiv:2110.09368):
  L1  (D/pi)^(2d) = -Gamma(-d)zeta(-2d)/(Gamma(d)zeta(2d)),  rho = 1/2 + d
      [parsing adjudicated pre-run in prereg S2; asserted here as C5]
  L2  real zeros iff D < D*_c = e^gamma/(4 pi); negative probe at 0.15
  L3  rho_down(D) ~ (3/pi) D as D -> 0
  L4  Z(s,D)=Z(1-s,D) duality => rho_up = 1 - rho_down EXACTLY

Registered: 18-point D grid, both branches; 200-pt scan dps 30 -> bisection 1e-25 ->
secant dps 50; controls C1-C5 must ALL pass; L4 guard 1e-25. Implementation notes
(logged, not scored): each scan adds a 50-pt log-spaced sub-scan (rho- on (1e-5,1e-2),
rho+ mirrored at 1) because a uniform 200-pt scan cannot resolve roots within 2.5e-3 of
the endpoints (needed for Delta <~ 2.6e-3); bracket tolerances unchanged. Outcomes
(a)/(b)/(c) per prereg S4. Traps applied: #63 (no
hand-copied coordinates), #70c2 (truncation sized), #73 (module-level dps only), #74
(asserts at earliest point), #75 (parsing adjudication registered + asserted), #76 (no
nsum), #77 (off-special-point identity checks — C1's s=1.3/0.75 legs).
"""
import json
import math
import os
import time

from mpmath import (mp, mpf, pi, sqrt, exp, log, gamma, zeta, besselk,
                    quad, gammainc, euler)

mp.dps = 50  # #73: module level ONLY

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DELTA_GRID = [mpf(x) for x in ("0.14", "0.135", "0.13", "0.12", "0.11", "0.10",
                               "0.09", "0.08", "0.07", "0.06", "0.05", "0.04",
                               "0.03", "0.02", "0.01", "5e-3", "2e-3", "1e-3")]
D_NEG_PROBE = mpf("0.15")                     # > D*_c: must find NO zero (registered)
DSTAR_C = exp(euler) / (4 * pi)               # L2 closed form, derived not copied
TRUNC_REL = mpf("1e-45")                      # registered relative shell cutoff
C_CONST = 2 + euler - log(4 * pi)             # visibility constant 2+gamma-log(4pi)
TSTAR_MULT = mpf("30")                        # Ts = 30/D^2  =>  4 D^2 Ts = 120

out = open(os.path.join(SCRIPT_DIR, 'heat68_epstein_rect_zeros.out'), 'w', buffering=1)

def P(*a):
    msg = ' '.join(str(x) for x in a)
    print(msg, flush=True)
    print(msg, file=out, flush=True)

# ---------------------------------------------------------------- theta3
def theta3_direct(q):
    """1 + 2 sum_{n>=1} q^{n^2}; caller guarantees q <= e^{-2} (<= ~9 terms)."""
    assert q <= exp(mpf(-2))
    s = mpf(1); n = 1
    while True:
        t = 2 * q ** (n * n)
        s += t
        if t < mpf('1e-58'):
            return s
        n += 1

def th3(x):
    """theta3(e^{-x}) for any x>0 via channel identity, recursion depth <= 1.

    x >= 2: direct.  x < 2: sqrt(pi/x) theta3(e^{-pi^2/x}), inner pi^2/x > pi^2/2 > 2
    so the inner call is direct. Identity throughout, no approximation.
    """
    if x >= 2:
        return theta3_direct(exp(-x))
    return sqrt(pi / x) * theta3_direct(exp(-pi ** 2 / x))

# ------------------------------------------------- evaluator A (Bessel)
def zeta2_A(s, D):
    """Returns (value, n_bessel_terms). t3 factor (m/k)^{s-1/2} per AMENDMENT-2."""
    nu = s - mpf("0.5")
    t1 = zeta(2 * s)
    t2 = sqrt(pi) * gamma(s - mpf("0.5")) * D ** (1 - 2 * s) * zeta(2 * s - 1) / gamma(s)
    total = mpf(0)
    k = 1
    nterms = 0
    while True:
        shell = mpf(0)
        m = 1
        while True:
            z = 2 * pi * D * k * m
            if z > 160:                        # K underflows past exp(-160) ~ 1e-70
                break
            shell += (mpf(m) / k) ** nu * besselk(nu, z)
            nterms += 1
            m += 1
        if abs(shell) < TRUNC_REL * max(abs(total), mpf(1)):
            total += shell
            break
        total += shell
        k += 1
    t3 = (4 * pi ** s / gamma(s)) * D ** (mpf("0.5") - s) * total
    return t1 + t2 + t3, nterms

# --------------------------------------- evaluator B (theta-integral)
def zeta2_B(s, D):
    """Registered AMENDMENT-2 form. Split at Ts = 30/D^2; I1 tail extracted closed
    on [Ts,inf) with residual < 1e-50 asserted; J tail extracted, residual quad'd."""
    # Ts chosen so BOTH 4 D^2 Ts >= 120 and (1+D^2) Ts >= 120 (residual < 1e-50).
    # For D <= 0.577 this is Ts = 30/D^2; for D near 1 the cross-term dominates.
    Ts = max(TSTAR_MULT / (D * D), mpf(120) / (1 + D * D))
    DsTs = D * D * Ts
    res_bound = 2 * exp(-4 * DsTs) + 4 * exp(-(1 + D * D) * Ts) * Ts ** (s - 1)
    assert res_bound < mpf('1e-50'), 'residual bound D=%s Ts=%s' % (D, Ts)
    # I1a: [pi, Ts], both factors via th3 (channel identity, exact)
    def f1(t):
        Th = th3(t) * th3(D * D * t)
        return t ** (s - 1) * (Th - 1)
    pts = [pi, Ts] if 1 / (D * D) <= pi else [pi, 1 / (D * D), Ts]
    I1a = quad(f1, pts)
    # I1b: [Ts, inf): direct channels; 2e^{-t} + 2e^{-D^2 t} closed; residual asserted
    I1b = (2 * gammainc(s, Ts, mpf('inf'))
           + 2 * D ** (-2 * s) * gammainc(s, DsTs, mpf('inf')))
    # J: [1, inf): both direct (pi/D^2 >= pi/0.0196 > 2 on the grid, asserted);
    # tail 2e^{-pi u} + 2e^{-pi u/D^2} extracted closed, residual quad'd to inf
    assert pi / (D * D) > 2
    def f3(u):
        thth = theta3_direct(exp(-pi * u)) * theta3_direct(exp(-pi * u / (D * D)))
        return u ** (-s) * ((thth - 1) - 2 * exp(-pi * u) - 2 * exp(-pi * u / (D * D)))
    J = (quad(f3, [1, 4, mpf('inf')])
         + 2 * pi ** (s - 1) * gammainc(1 - s, pi, mpf('inf'))
         + 2 * (pi / D ** 2) ** (s - 1) * gammainc(1 - s, pi / D ** 2, mpf('inf')))
    S = I1a + I1b + pi ** s / D * J + pi ** s / (D * (s - 1)) - pi ** s / s
    return S / (2 * gamma(s))

# ---------------------------------------------------------------- helpers
def relerr(a, b):
    return abs(a - b) / max(abs(a), abs(b))

def digits(re_):
    return 99 if re_ == 0 else float(-mp.log10(re_))

def beta_h(s):
    return 4 ** (-s) * (zeta(s, mpf("0.25")) - zeta(s, mpf("0.75")))

def brute2d(s, D, R):
    tot = mpf(0)
    for j in range(-R, R + 1):
        jj = j * j
        for k in range(-R, R + 1):
            if j == 0 and k == 0:
                continue
            tot += (jj + D * D * k * k) ** (-s)
    return tot / 2

# ---------------------------------------------------------------- controls
def run_controls():
    P('=== CONTROLS (asserts; any failure = instrument halt per prereg) ===')
    ok = {}
    # C1: Delta=1 identity zeta2(s,1)=2 zeta(s) beta(s), BOTH evaluators,
    # s=1.3 (off-special point, trap #77: k>=2 rows non-negligible) and s=0.75
    for sv in ('1.3', '0.75'):
        s = mpf(sv)
        rhs = 2 * zeta(s) * beta_h(s)
        za, _ = zeta2_A(s, mpf(1))
        zb = zeta2_B(s, mpf(1))
        dA, dB = digits(relerr(za, rhs)), digits(relerr(zb, rhs))
        P('C1 s=%s: A %.1f dig, B %.1f dig (need 25)' % (sv, dA, dB))
        assert dA >= 25 and dB >= 25, 'C1 failed s=%s' % sv
        ok['C1_' + sv] = [dA, dB]
    # C2: brute s=3.5, R=120, Delta=0.1 vs A (AMENDMENT-1 scope; AMENDMENT-2 formula)
    s, D, R = mpf('3.5'), mpf('0.1'), 120
    b = brute2d(s, D, R)
    za, _ = zeta2_A(s, D)
    tail = 2 * pi * mpf(R) ** (2 - 2 * s) / (2 * s - 2)
    d = digits(relerr(za, b))
    P('C2 brute s=3.5 R=120 D=0.1: A vs brute %.1f dig (need 8); tail bound %s (< 3e-9)'
      % (d, mp.nstr(tail, 3)))
    assert d >= 8 and tail < mpf('3e-9'), 'C2 failed'
    ok['C2'] = d
    # C3: duality Z(s)=Z(1-s) at s=0.7, D=0.05, BOTH evaluators
    s, D = mpf('0.7'), mpf('0.05')
    ZA = lambda x: (D / pi) ** x * gamma(x) * zeta2_A(x, D)[0]
    ZB = lambda x: (D / pi) ** x * gamma(x) * zeta2_B(x, D)
    dA, dB = digits(relerr(ZA(s), ZA(1 - s))), digits(relerr(ZB(s), ZB(1 - s)))
    P('C3 duality s=0.7 D=0.05: A %.1f dig, B %.1f dig (need 20)' % (dA, dB))
    assert dA >= 20 and dB >= 20, 'C3 failed'
    ok['C3'] = [dA, dB]
    # C4: residue lim (s-1) zeta2 = pi/(2D) at D=0.1 via Richardson on A
    # at s = 1-1e-10, 1-2e-10 (cancels the linear term; error ~1e-20)
    D = mpf('0.1')
    def g(e):
        return -e * zeta2_A(1 - e, D)[0]
    rich = 2 * g(mpf('1e-10')) - g(mpf('2e-10'))
    d = digits(relerr(rich, pi / (2 * D)))
    P('C4 residue D=0.1: Richardson %s vs pi/(2D): %.1f dig (need 20)'
      % (mp.nstr(rich, 14), d))
    assert d >= 20, 'C4 failed'
    ok['C4'] = d
    # C5: parsing linearization — g(d) = -Gamma(-d)zeta(-2d)/(Gamma(d)zeta(2d))
    # equals 1 + 2[gamma - 2 log(2 pi)] d at d = 1e-6, coefficient to >= 8 digits
    d0 = mpf('1e-6')
    c = 2 * (euler - 2 * log(2 * pi))
    g0 = (-gamma(-d0) * zeta(-2 * d0)) / (gamma(d0) * zeta(2 * d0))
    d = digits(abs(g0 - (1 + c * d0)) / abs(c * d0))
    P('C5 parse linearization at d=1e-6: %.1f dig (need 8); implies Delta*_c=e^g/(4pi)=%s'
      % (d, mp.nstr(DSTAR_C, 16)))
    assert d >= 8, 'C5 failed'
    ok['C5'] = d
    # AMENDMENT-2 equivalence: A == B at (s,D) in {0.6,0.9} x {0.05,0.1}
    for sv in ('0.6', '0.9'):
        for Dv in ('0.05', '0.1'):
            s, D = mpf(sv), mpf(Dv)
            za, _ = zeta2_A(s, D)
            zb = zeta2_B(s, D)
            d = digits(relerr(za, zb))
            P('EQ A==B s=%s D=%s: %.1f dig (need 20)' % (sv, Dv, d))
            assert d >= 20, 'EQ failed s=%s D=%s' % (sv, Dv)
            ok['EQ_%s_%s' % (sv, Dv)] = d
    P('=== ALL CONTROLS GREEN ===')
    return ok

# ---------------------------------------------------------------- L1 solver
def l1_delta(D):
    """Solve (D/pi)^{2d} Gamma(d) zeta(2d) + Gamma(-d) zeta(-2d) = 0, d in (0,1/2)."""
    def h(d):
        return (D / pi) ** (2 * d) * gamma(d) * zeta(2 * d) + gamma(-d) * zeta(-2 * d)
    with mp.workdps(30):
        # uniform grid + 50-pt log-mirrored sub-scan near d=1/2 (for Delta <~ 2e-3
        # the root delta lies in (0.499, 0.5), beyond any affordable uniform edge)
        xs = sorted([mpf(i) / 800 for i in range(1, 400)]
                    + [mpf('0.5') - mpf('1e-5') * mpf(1000) ** (mpf(i) / 49) for i in range(50)])
        vals = [h(x) for x in xs]
        bracket = None
        for i in range(len(xs) - 1):
            if vals[i] == 0 or vals[i] * vals[i + 1] < 0:
                bracket = (xs[i], xs[i + 1])
                break
        assert bracket, 'L1: no sign change for D=%s' % D
        a, b = bracket
        for _ in range(90):
            m = (a + b) / 2
            if h(a) * h(m) <= 0:
                b = m
            else:
                a = m
        lo, hi = a, b
    with mp.workdps(50):
        x0, x1 = lo, hi
        f0, f1 = h(x0), h(x1)
        for _ in range(8):
            if f1 == f0 or x1 == x0:
                break
            x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
            if x2 == x1:
                break
            f2 = h(x2)
            x0, f0, x1, f1 = x1, f1, x2, f2
        return x1

# ---------------------------------------------------------------- roots
def find_roots_B(D):
    """200-pt scans dps 30 -> bisect to 1e-25 -> secant dps 50, evaluator B.
    Returns (rho_plus, rho_minus)."""
    with mp.workdps(30):
        # rho+ in (1/2, 1): registered 200-pt scan + 50-pt log sub-scan mirrored at 1
        # (at Delta <=~ 2.6e-3, rho+ = 1 - rho- > 0.9975 lies beyond the uniform edge)
        xs_up = sorted([mpf(1) / 2 + (mpf(1) / 2) * mpf(i) / 200 for i in range(1, 200)]
                       + [1 - mpf('1e-5') * mpf(1000) ** (mpf(i) / 49) for i in range(50)])
        vals_up = [zeta2_B(x, D) for x in xs_up]
        cr_up = [(xs_up[i], xs_up[i + 1]) for i in range(len(xs_up) - 1)
                 if vals_up[i] * vals_up[i + 1] < 0]
        assert len(cr_up) == 1, 'rho+ scan: %d crossings D=%s' % (len(cr_up), D)
        # rho- in (0, 1/2): registered 200-pt scan + 50-pt log sub-scan (1e-5, 1e-2)
        xs_lo = sorted([mpf(i) / 400 for i in range(1, 200)]
                       + [mpf('1e-5') * mpf(1000) ** (mpf(i) / 49) for i in range(50)])
        vals_lo = [zeta2_B(x, D) for x in xs_lo]
        cr_lo = [(xs_lo[i], xs_lo[i + 1]) for i in range(len(xs_lo) - 1)
                 if vals_lo[i] * vals_lo[i + 1] < 0]
        assert len(cr_lo) == 1, 'rho- scan: %d crossings D=%s' % (len(cr_lo), D)
        def bisect(br):
            a, b = br
            fa = zeta2_B(a, D)
            for _ in range(85):
                m = (a + b) / 2
                if fa * zeta2_B(m, D) <= 0:
                    b = m
                else:
                    a, fa = m, zeta2_B(m, D)
                if b - a < mpf('1e-25'):
                    break
            return a, b
        bu, bl = bisect(cr_up[0]), bisect(cr_lo[0])
    with mp.workdps(50):
        def secant(br):
            x0, x1 = br
            f0, f1 = zeta2_B(x0, D), zeta2_B(x1, D)
            for _ in range(10):
                if f1 == f0 or x1 == x0:      # converged to full dps-50 precision
                    break
                x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
                if x2 == x1:
                    break
                f2 = zeta2_B(x2, D)
                x0, f0, x1, f1 = x1, f1, x2, f2
            return x1
        return secant(bu), secant(bl)

def polish_A(x0, D):
    """Secant-polish a root with evaluator A at dps 50."""
    with mp.workdps(50):
        x1 = x0 + mpf('1e-18')
        f0, f1 = zeta2_A(x0, D)[0], zeta2_A(x1, D)[0]
        for _ in range(6):
            if f1 == f0 or x1 == x0:
                break
            x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
            if x2 == x1:
                break
            f2 = zeta2_A(x2, D)[0]
            x0, f0, x1, f1 = x1, f1, x2, f2
        return x1

# ---------------------------------------------------------------- main
def main():
    t00 = time.time()
    P('heat68 run start. dps=%d grid=%d pts DSTAR_C=%s (registered AMENDMENT-2 runner)'
      % (mp.dps, len(DELTA_GRID), mp.nstr(DSTAR_C, 22)))
    ok = run_controls()

    # L2 negative probe: D = 0.15 > D*_c, 61-pt sign scan in (0.1, 1.0), expect 0
    D = D_NEG_PROBE
    with mp.workdps(30):
        xs = [mpf('0.1') + mpf('0.9') * mpf(i) / 60 for i in range(61)]
        vals = [zeta2_B(x, D) for x in xs]
        cross = sum(1 for i in range(len(xs) - 1) if vals[i] * vals[i + 1] < 0)
    P('L2 negative probe D=0.15: %d sign changes over 61 pts in (0.1,1.0) (expect 0)' % cross)
    assert cross == 0, 'L2 negative probe FAILED'
    ok['L2'] = cross

    rows = []
    for Dv in DELTA_GRID:
        D = Dv
        t0 = time.time()
        rho_pB, rho_mB = find_roots_B(D)
        dAB_p = dAB_m = None
        if D >= mpf('0.01'):
            rho_pA, rho_mA = polish_A(rho_pB, D), polish_A(rho_mB, D)
            dAB_p, dAB_m = digits(relerr(rho_pB, rho_pA)), digits(relerr(rho_mB, rho_mA))
            assert dAB_p >= 20 and dAB_m >= 20, 'A/B root disagreement D=%s' % Dv
        dl1 = l1_delta(D)
        l1_p, l1_m = mpf('0.5') + dl1, mpf('0.5') - dl1
        dL1p, dL1m = digits(relerr(rho_pB, l1_p)), digits(relerr(rho_mB, l1_m))
        l4 = digits(abs(rho_pB + rho_mB - 1))
        floor = (2 * rho_pB - 1) / rho_pB ** 2
        P('D=%-7s rho+=%s' % (Dv, mp.nstr(rho_pB, 30)))
        P('         rho-=%s | A/B %s/%s dig | L1 %s/%s dig | L4 %.1f | floor %s | %ds'
          % (mp.nstr(rho_mB, 30),
             ('%.1f' % dAB_p) if dAB_p is not None else 'n/a',
             ('%.1f' % dAB_m) if dAB_m is not None else 'n/a',
             '%.1f' % dL1p, '%.1f' % dL1m, l4, mp.nstr(floor, 17), int(time.time() - t0)))
        rows.append(dict(D=str(Dv), rho_plus=str(rho_pB), rho_minus=str(rho_mB),
                         dAB_plus=dAB_p, dAB_minus=dAB_m, dL1_plus=float(dL1p),
                         dL1_minus=float(dL1m), L4=float(l4), floor=str(floor)))

    # strictly-decreasing-D grid assert (#74)
    floats = [float(r['D']) for r in rows]
    assert all(floats[i] > floats[i + 1] for i in range(len(floats) - 1))

    # L3: rho-(1e-3) / ((3/pi) 1e-3)
    rm1 = mpf(rows[-1]['rho_minus'])
    l3 = rm1 / ((3 / pi) * mpf('0.001'))
    P('L3: rho-(1e-3)/((3/pi) 1e-3) = %s' % mp.nstr(l3, 12))

    # floor dial: interpolate Delta with floor = 0.5 (target rho+ = 2-sqrt2)
    fl = [(float(r['D']), float(r['floor'])) for r in rows]
    interp = None
    for i in range(len(fl) - 1):
        if (fl[i][1] - 0.5) * (fl[i + 1][1] - 0.5) < 0:
            x0, y0 = fl[i]; x1, y1 = fl[i + 1]
            interp = math.exp(math.log(x0) + (0.5 - y0) * (math.log(x1) - math.log(x0)) / (y1 - y0))
            break
    P('floor=0.5 interpolated Delta (log-interp in Delta): %s' % interp)
    # visibility: floor > C/log N at N in {1e6,1e9,1e12}, C = 0.0461914...
    minfloor = min(f for _, f in fl)
    for n in (1e6, 1e9, 1e12):
        need = float(C_CONST) / math.log(n)
        P('visibility N=%.0e: min floor over grid %.8f vs C/logN %.8f -> %s'
          % (n, minfloor, need, 'PASS' if minfloor > need else 'FAIL'))

    # outcome dispatch per prereg S4 + AMENDMENT-3: L1 gated only on D <= 0.10
    # (L1 derives from the paper's approximate (3.32); near-D*_c degradation is the
    # scored approximation-error profile, not an instrument defect).
    gated = [r for r in rows if float(r['D']) <= 0.10]
    min_dL1 = min(min(r['dL1_plus'], r['dL1_minus']) for r in gated)
    min_dL1_full = min(min(r['dL1_plus'], r['dL1_minus']) for r in rows)
    worst_row = min(rows, key=lambda r: min(r['dL1_plus'], r['dL1_minus']))
    min_L4 = min(r['L4'] for r in rows)
    outcome = 'a' if (min_dL1 >= 20 and min_L4 >= 25) else ('b' if min_dL1 >= 10 else 'c')
    P('OUTCOME: (%s)  gated(D<=0.10) min L1 %.1f dig | full-grid min L1 %.1f dig at D=%s '
      '(approx-(3.32) profile) | min L4 %.1f dig'
      % (outcome, min_dL1, min_dL1_full, worst_row['D'], min_L4))
    P('total %ds' % int(time.time() - t00))

    json.dump(dict(controls=ok, rows=rows, L3=str(l3), floor05=interp,
                   C=float(C_CONST), outcome=outcome, DSTAR_C=str(DSTAR_C),
                   min_dL1_gated=min_dL1, min_dL1_full=min_dL1_full,
                   worst_L1_D=worst_row['D']),
              open(os.path.join(SCRIPT_DIR, 'heat68_epstein_rect_zeros.json'), 'w'), indent=1)
    out.close()

if __name__ == '__main__':
    main()
