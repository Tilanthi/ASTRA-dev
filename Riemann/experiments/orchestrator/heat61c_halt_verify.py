"""heat61c — halt-and-verify for the frozen W(f) candidate (design section 5).

The search froze an LB (sinc-pair) genome at generation 2 with 2^17-grid
Q = -1.389e-3 < -eps_cert = -1e-3. Per the pre-registered protocol: NO claim
language until (a) the same genome is recomputed at 3x precision (grid 2^23),
prime side AND zero side, and (b) a counterparty on the exchange re-derives it.

This script performs (a) plus a refinement ladder 2^17 / 2^19 / 2^21 / 2^23 on
the prime side. Verdict logic:
  - If the 2^23 prime side and the 2^23 zero side AGREE to ~2e-9 scale-relative
    AND the common value is < -eps_cert: genuine negative cell -> freeze,
    counterparty, absolute no-claims-until-confirmed posture.
  - If Q drifts with grid (Q(2^23) materially different from Q(2^17)):
    grid artifact. Document, raise the search's effective floor (eps_cert
    margin vs measured drift), resume.
Zero-side truncation: sinc-pair Mellin transforms decay like a shifted Gaussian
in t for the windowed realization; we verify saturation empirically at
T = 100 / 150 / 200 and report the tail term.

Genome loaded from heat61_w_search.log.json (frozen[0]) — parsed, never
hand-copied (trap #63).
"""
import json
import sys

import mpmath as mp
import numpy as np

mp.mp.dps = 30

CUT_IN, CUT_OUT = 6.0, 8.0
EPS_CERT = 1e-3

with open("heat61_w_search.log.json") as fh:
    REC = json.load(fh)
FR = REC["frozen"][0]
GENOME = FR["genome"]
LINEAGE = FR["lineage"]
print(f"frozen candidate: lineage {LINEAGE}, gen {FR['gen']}, 2^17 Q = {FR['Q']:+.6e}")
print(f"  genome: {json.dumps(GENOME)}")

def _theta(s):
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

def build_f(grid_log2):
    LGRID = 24.0
    NGRID = 1 << grid_log2
    DX = 2 * LGRID / NGRID
    XS = -LGRID + DX * np.arange(NGRID)
    win = _theta((CUT_OUT - np.abs(XS)) / (CUT_OUT - CUT_IN))
    f = np.zeros_like(XS)
    c = GENOME["c"]
    for ctr, amp in GENOME["pairs"]:
        t = XS - ctr
        f += amp * np.where(np.abs(t) > 1e-10, np.sin(c * t) / (np.pi * np.where(np.abs(t) > 1e-10, t, 1.0)), c / np.pi)
    f = f * win
    nrm = np.sqrt(DX * (f * f).sum())
    return XS, DX, f / nrm

def sieve_primes(nmax):
    s = np.ones(nmax + 1, dtype=bool)
    s[:2] = False
    for i in range(2, int(nmax ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = False
    return np.nonzero(s)[0]

PRIMES = sieve_primes(int(np.exp(16.0)) + 2)
LOGP = np.log(PRIMES.astype(float))
KMAX = np.floor(16.0 / LOGP).astype(int)

def lagrange8(xs_grid, ys_grid, xq):
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

def prime_side(grid_log2):
    XS, DX, f = build_f(grid_log2)
    g0 = DX * (f.sum() - 0.5 * (f[0] + f[-1]))
    g1 = DX * ((f * np.exp(XS)).sum() - 0.5 * ((f * np.exp(XS))[0] + (f * np.exp(XS))[-1]))
    A = f * np.exp(XS)
    n2 = 2 * len(f)
    corr = np.fft.irfft(np.fft.rfft(A, n2) * np.conj(np.fft.rfft(f, n2)), n2)
    m_from = int(np.floor(-20 / DX))
    m_to = int(np.ceil(20 / DX))
    ms = np.arange(m_from, m_to + 1)
    hx = ms * DX
    hgrid = np.exp(-hx) * DX * corr[ms % n2]
    def H(xq):
        return lagrange8(hx, hgrid, xq)
    terms = np.zeros(len(PRIMES))
    for k in range(1, int(KMAX.max()) + 1):
        active = KMAX >= k
        if not active.any():
            continue
        xa = k * LOGP[active]
        terms[active] += H(xa)
        terms[active] += np.exp(-xa) * H(-xa)
    sump = float(np.sum(LOGP * terms))
    h0 = H(0.0)[0]
    c0 = (np.log(np.pi) + np.euler_gamma) / 2 * h0
    m = (XS >= 0) & (XS <= 16.0)
    xm = XS[m]
    hm = H(xm)
    i1 = DX * (hm.sum() - 0.5 * (hm[0] + hm[-1]))
    with np.errstate(invalid="ignore", divide="ignore"):
        integ2 = (hm - h0) / (np.expm1(2 * xm))
    integ2[np.abs(xm) < 10 * DX] = -h0 / 4
    i2 = DX * (integ2.sum() - 0.5 * (integ2[0] + integ2[-1]))
    Q = 2 * g0 * g1 - (sump + 2 * (c0 + i1 + i2))
    return Q, dict(g0=g0, g1=g1, sump=sump, c0=c0, i1=i1, i2=i2)

def zero_side(grid_log2, T):
    XS, DX, f = build_f(grid_log2)
    def gh(s):
        w = f * np.exp(complex(s) * XS)
        return DX * (w.sum() - 0.5 * (w[0] + w[-1]))
    total = 0.0
    n = 1
    last = None
    while True:
        z = mp.zetazero(n)
        if z.imag > T:
            break
        rho = complex(z)
        a = gh(rho)
        b = gh(1 - rho)
        term = 2.0 * (a * b).real
        total += term
        last = abs(term)
        n += 1
    return total, n - 1, last

if __name__ == "__main__":
    print("\n== refinement ladder, prime side ==")
    ladder = {}
    for gl in [17, 19, 21, 23]:
        Q, parts = prime_side(gl)
        ladder[gl] = Q
        print(f"  2^{gl}: Q = {Q:+.8e}   (g0 {parts['g0']:+.4f} g1 {parts['g1']:+.4f} "
              f"sump {parts['sump']:+.6f} 2Vr {2*(parts['c0']+parts['i1']+parts['i2']):+.6f})")
        sys.stdout.flush()
    q17, q23 = ladder[17], ladder[23]
    drift = abs(q23 - q17)
    print(f"\n  drift 2^17 -> 2^23: {drift:.3e}   |Q(2^23)| = {abs(q23):.3e}")

    print("\n== zero side at 2^23 (3x precision per protocol) ==")
    for T in [100.0, 150.0, 200.0]:
        Qz, nz, last = zero_side(23, T)
        print(f"  T={T:5.0f} ({nz:3d} zeros): Q_zero = {Qz:+.8e}   last |term| {last:.2e}")
        sys.stdout.flush()

    print("\n== verdict ==")
    print(f"  prime 2^23: {q23:+.6e}   (2^17 claim was {FR['Q']:+.6e})")
    print(f"  if prime==zero at 2^23 and common value < -{EPS_CERT}: NEGATIVE CELL -> freeze + counterparty, no claims")
    print(f"  if drift ~ |Q|: grid artifact -> document, resume search with corrected floor")
