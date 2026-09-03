"""heat61 G0 — convention + implementation balance gate for the W(f) search.

Pre-registered in m4_w_search_design.md (committed before this gate ran,
SHA-256 88b4a374eca8327c9ab14090b612b91fe2d96c01fa68cb1b4c436d8ba9b323be).
NO search evaluation happens here: G0 evaluates three FIXED named test
functions and checks that Weil's explicit formula balances, zero side vs prime
side, to certified precision. Any sign/shift/convention error breaks the
balance at O(1); G0 is a full verification of the instrument, not a sanity
check (design doc section 3).

Convention (Burnol math/9810169, exact quotes fetched from ar5iv 2026-09-03):
  Mellin: gh(s) = Int_0^inf g(u) u^s du/u          [exponent u^s]
  Z(g)  := gh(0) + gh(1) - lim_T Sum_{|Im rho|<T, NONTRIVIAL} gh(rho)
         = Sum_p (V_p(g) + V_p(g^tau)) + W_r(g)
  V_p(g) = log p * Sum_{k>=1} [ g(p^k) + p^{-k} g(p^{-k}) ]    (finite: compact support)
  g^tau(x) = (1/x) g(1/x),   gh^tau(s) = gh(1-s)
  W_r(g) = V_r(g) + V_r(g^tau)
  V_r(g) = ((log pi + gamma)/2) g(1) + Int_1^inf g(t) dt/t
           + Int_1^inf (g(t)-g(1))/(t^2-1) dt/t

Zero-side note: the T-truncated sum runs over NONTRIVIAL zeros only (the
trivial-zero moments gh(-2n) grow like e^{12n} for our class -- the full sum
diverges; the archimedean V_r terms carry the Gamma-factor/trivial-zero
package). Symmetric truncation = both half-planes; for real f this is
  Q = 2 * Sum_{gamma_n < T} Re[ gh(rho_n) gh(1-rho_n) ],  rho_n = 1/2 + i gamma_n.

Objective wiring: h := g * g^tau has hh(s) = gh(s) gh(1-s), so
hh(rho) = gh(rho) gh(1-rho) and hh(0)+hh(1) = 2 gh(0) gh(1). Moreover h^tau = h
(same Mellin transform), so the prime side collapses:
  Q(g) = Sum_rho gh(rho) gh(1-rho)
       = 2 gh(0) gh(1) - 2 [ Sum_p V_p(h) + V_r(h) ].

G0-development disclosures (before first run; design doc fixed the test
functions, not the arithmetic):
  D1. An earlier mpmath draft carried spurious e^x factors in the V_r
      t->x substitution; re-derivation gives dt/t = dx with NO weight:
      i1 = Int_0^16 f(x) dx, i2 = Int_0^16 (f(x)-f(0))/(e^{2x}-1) dx.
  D2. h^tau = h halving of the prime side, as above.
  D3. The zero side counts both half-planes via 2*Re per upper-half zero.
  D4. The smooth cutoff is the C^infty flat step theta(s) = e^{-1/s}/(e^{-1/s}
      + e^{-1/(1-s)}) on [CUT_IN, CUT_OUT], not a cos^2/Hann ramp (Hann is
      only C^1 at the edges -> breaks C_c^infty and the spectral quadrature);
      "truncated smoothly" in the hashed design is read as C^infty-flat.
  D5. Quadrature is trapezoid throughout (C^infty compact support makes it
      spectrally accurate by Euler-Maclaurin; Simpson was the first draft).

Test functions (fixed by the design doc):
  f1 = exp(-x^2/2), smoothly windowed to |x| <= 8 (cos^2 on [6,8])
  f2 = exp(-(x-1)^2/2) - 0.7 exp(-(x+2)^2/8), same window
  f3 = sinc-pair (bandwidth c=4, centers +-2), same window  [prolate-family stand-in]

Numerics: x-grid [-24,24], N = 2^17 nodes, FFT cross-correlation for h
(verified against direct mpmath quadrature at fixed points -- printed),
Simpson for Mellin integrals, primes sieved to e^16 (complete: support of h in
x is [-16,16]), h at prime powers by 8-point local Lagrange on the fine grid
(error ~ dx^8; dx = 3.66e-4). mpmath supplies zetazero and the cross-checks.
"""
import hashlib
import os
import sys

import mpmath as mp
import numpy as np

mp.mp.dps = 30

CUT_IN, CUT_OUT = 6.0, 8.0
LGRID = 24.0
NGRID = 1 << int(os.environ.get("G0_GRID_LOG2", "17"))
DX = 2 * LGRID / NGRID
XS = -LGRID + DX * np.arange(NGRID)

# ---------------- test functions ----------------
def _theta(s):
    """C^infty flat step: 0 for s<=0, 1 for s>=1, flat at both ends."""
    s = np.asarray(s, dtype=float)
    out = np.zeros_like(s)
    lo = s <= 0.0
    hi = s >= 1.0
    mid = ~(lo | hi)
    with np.errstate(over="ignore"):
        e = np.exp(-1.0 / s[mid])
        e2 = np.exp(-1.0 / (1.0 - s[mid]))
    out[mid] = e / (e + e2)
    out[hi] = 1.0
    return out

def _window(x):
    return _theta((CUT_OUT - np.abs(x)) / (CUT_OUT - CUT_IN))

def _theta_mp(s):
    if s <= 0:
        return mp.mpf(0)
    if s >= 1:
        return mp.mpf(1)
    e = mp.e ** (-1 / s)
    return e / (e + mp.e ** (-1 / (1 - s)))

def _window_mp(x):
    return _theta_mp((CUT_OUT - abs(mp.mpf(x))) / (CUT_OUT - CUT_IN))

def f1(x):
    return np.exp(-x ** 2 / 2) * _window(x)

def f2(x):
    return (np.exp(-(x - 1) ** 2 / 2) - 0.7 * np.exp(-(x + 2) ** 2 / 8)) * _window(x)

def f3(x, c=4.0):
    def sinc(t):
        out = np.where(np.abs(t) > 1e-12, np.sin(c * t) / (np.pi * np.where(np.abs(t) > 1e-12, t, 1.0)), c / np.pi)
        return out
    return (sinc(x - 2) + sinc(x + 2)) * _window(x)

FUNCS = {"f1": f1, "f2": f2, "f3": f3}

def f_mp(name, x):
    """mpmath version of the same test function (cross-checks only)."""
    x = mp.mpf(x)
    w = _window_mp(x)
    if name == "f1":
        return mp.e ** (-x ** 2 / 2) * w
    if name == "f2":
        return (mp.e ** (-(x - 1) ** 2 / 2) - mp.mpf("0.7") * mp.e ** (-(x + 2) ** 2 / 8)) * w
    c = 4.0
    def sinc_mp(t):
        return mp.sin(c * t) / (mp.pi * t) if abs(t) > mp.mpf("1e-12") else c / mp.pi
    return (sinc_mp(x - 2) + sinc_mp(x + 2)) * w

# ---------------- trapezoid on the fine grid (spectral for C^infty compact) ----
def trapz_grid(y, dx):
    return dx * (y.sum() - 0.5 * (y[0] + y[-1]))

def gh_grid(fgrid, s):
    """gh(s) = Int f(x) e^{s x} dx by trapezoid (s complex ok)."""
    return trapz_grid(fgrid * np.exp(s * XS), DX)

# ---------------- h = g * g^tau via FFT cross-correlation ----------------
def build_h(name):
    """h(e^x) = e^{-x} Int f(y) e^y f(y-x) dy = e^{-x} * (A corr f)(x),
    A = f e^x, via zero-padded FFT cross-correlation.

    Identity used (checked term by term): with arrays sampled on XS
    (index k <-> x = -L + k DX),
      irfft(rfft(A, n2) * conj(rfft(f, n2)))[m] = Sum_j A_j f_{(j-m) mod n2}
                                                    = Sum_j A(x_j) f(x_j - m DX)
    for |m| DX <= 20 (A's support [-8,8], f's support [-8,8]; j-m stays in
    [0, NGRID) so the mod never wraps into the padding). Hence
      C(m DX) = Int A(y) f(y - m DX) dy = DX * corr[m],  negative m -> corr[n2+m].
    NO extra index shift: the correlation index already samples f at
    x_j - m DX on the same XS grid.
    """
    f = FUNCS[name](XS)
    A = f * np.exp(XS)
    n2 = 2 * NGRID
    corr = np.fft.irfft(np.fft.rfft(A, n2) * np.conj(np.fft.rfft(f, n2)), n2)
    m_from = int(np.floor(-20 / DX))
    m_to = int(np.ceil(20 / DX))
    ms = np.arange(m_from, m_to + 1)
    Cvals = DX * corr[ms % n2]
    xs_out = ms * DX
    h = np.exp(-xs_out) * Cvals
    return xs_out, h

def lagrange8(xs_grid, ys_grid, xq):
    """Vectorized 8-point local Lagrange interpolation, error ~ dx^8."""
    xq = np.atleast_1d(np.asarray(xq, dtype=float))
    n = len(xs_grid)
    j0 = np.clip(np.searchsorted(xs_grid, xq) - 4, 0, n - 8)
    out = np.zeros_like(xq)
    for i in range(8):
        w = np.ones_like(xq)
        for j in range(8):
            if i != j:
                w *= (xq - xs_grid[j0 + j]) / (xs_grid[j0 + i] - xs_grid[j0 + j])
        out += w * ys_grid[j0 + i]
    return out

# ---------------- zero side ----------------
def zero_side(name, T):
    f = FUNCS[name](XS)
    total = 0.0
    n = 1
    last_term = None
    while True:
        z = mp.zetazero(n)
        if z.imag > T:
            break
        rho = complex(z)
        a = gh_grid(f, rho)
        b = gh_grid(f, 1 - rho)
        term = 2.0 * (a * b).real
        total += term
        last_term = abs(term)
        n += 1
    return total, n - 1, last_term

# ---------------- prime side ----------------
def sieve_primes(nmax):
    s = np.ones(nmax + 1, dtype=bool)
    s[:2] = False
    for i in range(2, int(nmax ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = False
    return np.nonzero(s)[0]

PMAX = int(np.exp(16.0)) + 2
PRIMES = sieve_primes(PMAX)

def full_prime_side(name, hx, hgrid):
    """Q = 2 gh(0) gh(1) - 2 [ Sum_p V_p(h) + V_r(h) ]  (h^tau = h halving, D2).

    V_p(h) = log p * Sum_{k>=1} [ h(k x) + e^{-k x} h(-k x) ],  x = log p,
    finite since support of h in x is [-16,16]. Vectorized over primes.
    """
    fgrid = FUNCS[name](XS)
    g0 = gh_grid(fgrid, 0.0)
    g1 = gh_grid(fgrid, 1.0)

    logp = np.log(PRIMES.astype(float))
    terms = np.zeros(len(PRIMES))
    kmax = np.floor(16.0 / logp).astype(int)
    for k in range(1, int(kmax.max()) + 1):
        active = kmax >= k
        if not active.any():
            continue
        xa = k * logp[active]
        terms[active] += lagrange8(hx, hgrid, xa)
        terms[active] += np.exp(-xa) * lagrange8(hx, hgrid, -xa)
    sump = float(np.sum(logp * terms))

    # --- V_r(h): c0 + i1 + i2 in x-space (dt/t = dx, NO weight -- disclosure D1)
    # W_r(h) = V_r(h) + V_r(h^tau) = 2 V_r(h) since h^tau = h (verified: h(x) = e^{-x} h(-x),
    # which also forces h'(0) = -h(0)/2 exactly -- used for the removable x=0 patch).
    h0 = lagrange8(hx, hgrid, 0.0)[0]
    c0 = (np.log(np.pi) + np.euler_gamma) / 2 * h0
    m = (XS >= 0) & (XS <= 16.0)
    xm = XS[m]
    hm = lagrange8(hx, hgrid, xm)
    i1 = trapz_grid(hm, DX)
    integrand2 = (hm - h0) / (np.exp(2 * xm) - 1)
    # removable singularity at x=0: (h(x)-h(0))/(e^{2x}-1) -> h'(0)/2 = -h(0)/4
    xm0 = np.abs(xm) < 10 * DX
    if xm0.any():
        integrand2[xm0] = -h0 / 4
    i2 = trapz_grid(integrand2, DX)

    # CORRECTED prime side per source re-fetch + heat61b closed-form verification:
    # W_p is a SINGLE sum (transpose folded in); no doubling of sump.
    return 2 * g0 * g1 - (sump + 2 * (c0 + i1 + i2)), dict(g0=g0, g1=g1, sump=sump,
                                                            c0=c0, i1=i1, i2=i2)

# ---------------- cross-checks ----------------
def h_direct_mp(name, x):
    x = mp.mpf(x)
    lo = max(-CUT_OUT, x - CUT_OUT)
    hi = min(CUT_OUT, x + CUT_OUT)
    if hi <= lo:
        return mp.mpf(0)
    return mp.e ** (-x) * mp.quad(lambda y: f_mp(name, y) * mp.e ** y * f_mp(name, y - x),
                                  [lo, hi])

def gh_direct_mp(name, s):
    s = mp.mpc(s)
    return mp.quad(lambda x: f_mp(name, x) * mp.e ** (s * x), [-CUT_OUT, CUT_OUT])

# ---------------- main ----------------
if __name__ == "__main__":
    out = []
    P = print
    P("== heat61 G0: explicit-formula balance (Burnol math/9810169 convention) ==")
    P(f"   grid: N={NGRID} dx={DX:.3e} on [-{LGRID},{LGRID}]; primes to e^16 = {PMAX}")
    P(f"   design-doc sha256 (record): ", end="")
    try:
        h = hashlib.sha256(open("m4_w_search_design.md", "rb").read()).hexdigest()
        P(h)
    except FileNotFoundError:
        P("(design file not in cwd -- hash on record in the commit)")

    results = {}
    for name in ["f1", "f2", "f3"]:
        P(f"\n--- {name} ---")
        hx, hgrid = build_h(name)
        # cross-check 1: FFT h vs direct mpmath quadrature
        for xc in [0.0, 3.0, -3.0, 7.0, -7.5]:
            hd = h_direct_mp(name, xc)
            hn = lagrange8(hx, hgrid, xc)[0]
            rel = float(abs(hd - hn) / max(abs(hd), 1e-300))
            P(f"  [xcheck-h] x={xc:+.1f}: mp {mp.nstr(hd, 8)} vs fft {hn:.10f}  rel {rel:.2e}")
        # cross-check 2: Mellin identity hh(s) = gh(s) gh(1-s)
        s = mp.mpf("0.3") + 1j
        lhs = mp.quad(lambda x: mp.mpf(float(lagrange8(hx, hgrid, float(x))[0])) * mp.e ** (s * x),
                      [-16, 16])
        rhs = gh_direct_mp(name, s) * gh_direct_mp(name, 1 - s)
        rel = abs(lhs - rhs) / abs(rhs)
        P(f"  [xcheck-Mellin] Int h e^{{sx}} vs gh(s)gh(1-s): rel {mp.nstr(rel, 3)}")

        qz100, nz100, last100 = zero_side(name, 100.0)
        qz50, nz50, _ = zero_side(name, 50.0)
        qp, parts = full_prime_side(name, hx, hgrid)
        rel = abs(qz100 - qp) / max(abs(qp), 1e-300)
        P(f"  zero-side  T=50  ({nz50:2d} zeros): {qz50:+.12f}")
        P(f"  zero-side  T=100 ({nz100:2d} zeros): {qz100:+.12f}   last |term| {last100:.2e}")
        P(f"  prime-side          : {qp:+.12f}")
        P(f"    parts: g0={parts['g0']:+.6f} g1={parts['g1']:+.6f} sum_p V_p={parts['sump']:+.8f}")
        P(f"           V_r: c0={parts['c0']:+.8f} i1={parts['i1']:+.8f} i2={parts['i2']:+.8f}")
        P(f"  REL DIFF: {rel:.3e}   -> {'PASS' if rel < 1e-6 else 'FAIL'} (gate 1e-6)")
        results[name] = rel
        sys.stdout.flush()

    P("\n== G0 VERDICT:", "PASS (all three)" if all(r < 1e-6 for r in results.values())
      else "FAIL — instrument not yet verified; NO search until fixed", "==")
    for name, r in results.items():
        P(f"   {name}: {r:.3e}")
