#!/usr/bin/env python3
"""heat73 — m1 adjudication check of m2 CYCLE 20's central causal claim.

The claim (cycle-20 §3): for the sliding weight W_{T0,e}(s) = 1/((s-(1/2-e))^2+T0^2),
the SAME carrier (zeta) and SAME N stall when the weight's mass sits ON an
on-line zero (cell b: T0 = 49.7738 = 10th zeta zero) and descend when it sits
in a zero gap (cell c: T0 = 45.666 = midpoint of the 43.327-48.005 gap),
differing otherwise by nothing (height control).

m1 instrument (independent of both m2 pipelines): real-line Hermitian
reduction — full-line integrals reduced to [0,120] via phi_k(-t)=conj(phi_k(t));
piecewise Gauss-Legendre panels, refined around t=T0 where |W|^2 concentrates
(half-width eps=0.3); unconstrained weighted LS d^2 = ||1||^2 - b^+ G^-1 b;
N=16 (vs m2's N=48) — the QUALITATIVE contrast is N-robust (blocking decays
like Sum m^2/N; descending rows sit far lower).

Checks in file:
  1. ||1||^2 closed form 1/(4*e*(e^2+T0^2))  (cycle-20 §3 states it)
  2. cell (b) on-zero stall vs cell (c) in-gap descent, d^2/||1||^2
  3. cell (a) T0=0 far-below-first-zero descent
Acceptance for adjudication: (b)/(c) ratio >= 2 at N=16 with (b) >= 0.2.

m2's N=48 numbers for comparison: (a) 2.231e-6, (b) 0.56742, (c) 0.05772.
No pole constraint applied (zeta's penalty share ~0.01% per cycle-20 §2 —
irrelevant at this resolution; noted, not hidden).
"""
import time

from mpmath import (mp, mpf, mpc, pi, zeta, exp, quad, legendre, sqrt)

mp.dps = 22
TMAX = mpf("120")


def wnorm2_density(t, T0, eps):
    """|W(1/2+it)|^2 for the slide family."""
    tt = mpf(t)
    den = (T0 ** 2 + eps ** 2 - tt ** 2) ** 2 + 4 * eps ** 2 * tt ** 2
    return 1 / den


def wnorm2(T0, eps):
    """(1/2pi) int |W|^2 dt over the full line, PANEL-based (adaptive quad
    on a width-eps spike misses it — trap #99 genus; the panel norm is the
    one the measurement itself uses, so the check and the measurement share
    quadrature only by construction, not by luck)."""
    ts, ws = [], []
    for (a, b, n) in panel_partition(T0, eps):
        xn, wn = gl_nodes(a, b, n)
        ts += xn
        ws += wn
    val = sum(w * wnorm2_density(t, T0, eps) for t, w in zip(ts, ws))
    return 2 * val / (2 * pi)


_GL_CACHE = {}


def gl_rule(n):
    """Gauss-Legendre nodes/weights on [-1,1] via recurrence + Newton,
    mirrored for exact symmetry (mpmath's legendre(n,x) is the polynomial
    value, not a rule — this replaces it)."""
    if n in _GL_CACHE:
        return _GL_CACHE[n]
    import math
    half = []
    for i in range(1, n // 2 + 1):
        x = mpf(math.cos(math.pi * (i - 0.25) / (n + 0.5)))
        for _ in range(80):
            p0, p1 = mpf(1), x
            for k in range(1, n):
                p0, p1 = p1, ((2 * k + 1) * x * p1 - k * p0) / (k + 1)
            dp = n * (x * p1 - p0) / (x * x - 1)
            dx = p1 / dp
            x = x - dx
            if abs(dx) < mpf("1e-28"):
                break
        p0, p1 = mpf(1), x
        for k in range(1, n):
            p0, p1 = p1, ((2 * k + 1) * x * p1 - k * p0) / (k + 1)
        dp = n * (x * p1 - p0) / (x * x - 1)
        w = 2 / ((1 - x * x) * dp * dp)
        half.append((x, w))
    nodes = [h[0] for h in half] + ([] if n % 2 == 0 else [mpf(0)]) \
        + [-h[0] for h in reversed(half)]
    if n % 2 == 0:
        mid_w = []
    else:
        # middle weight: w = 2 / (n P_{n-1}(0))^2
        p0, p1 = mpf(1), mpf(0)
        for k in range(1, n):
            p0, p1 = p1, ((2 * k + 1) * 0 * p1 - k * p0) / (k + 1)
        mid_w = [2 / (n * p0) ** 2]
    weights = [h[1] for h in half] + mid_w + [h[1] for h in reversed(half)]
    _GL_CACHE[n] = (nodes, weights)
    return nodes, weights


def gl_nodes(a, b, n):
    x, w = gl_rule(n)
    xm = (b + a) / 2
    xr = (b - a) / 2
    return [xm + xr * xi for xi in x], [xr * wi for wi in w]


def panel_partition(T0, eps):
    """Panels: coarse away, fine panels across [T0-3e, T0+3e]; clamped to
    t >= 0 with NO overlap (a coarse panel covering a fine one double-counts
    the spike mass — caught on cell (a) where it doubled the norm)."""
    e = 3 * eps
    parts = [(mpf("0"), T0 - e, 24)]
    parts.append((T0 - e, T0 - eps, 40))
    parts.append((T0 - eps, T0 + eps, 80))
    parts.append((T0 + eps, T0 + e, 40))
    parts.append((T0 + e, min(TMAX, T0 + 10), 24))
    top = min(TMAX, T0 + 10)
    if top < TMAX:
        parts.append((top, TMAX, 40))
    out = []
    for (a, b, n) in sorted(parts):
        a = max(a, mpf("0"))
        if b > a:
            out.append((a, b, n))
    return out


def build_system(T0, eps, N):
    """Nodes, zeta values, then Hermitian G and b over [0,TMAX]."""
    ts, ws = [], []
    for (a, b, n) in panel_partition(T0, eps):
        xn, wn = gl_nodes(a, b, n)
        ts += xn
        ws += wn
    zs = [zeta(mpc(mpf("0.5"), t)) for t in ts]
    # full-line reduction: G_jk = (2/2pi) Re int_0 phi_k conj(phi_j) |W|^2
    #   phi_k = zeta * k^{-1/2-it}
    # b_k    = (2/2pi) int_0 Re(phi_k) |W|^2     (since conj(phi)+phi = 2Re)
    # ||1||^2= (2/2pi) int_0 |W|^2
    dens = [wnorm2_density(t, T0, eps) for t in ts]
    nrm = sum(w * d for w, d in zip(ws, dens)) * 2 / (2 * pi)
    # precompute k^{-1/2} cos/sin(t log k)
    import math
    kln = [math.log(k) for k in range(1, N + 1)]
    G = [[None] * N for _ in range(N)]
    b = [None] * N
    # accumulate cos/sin tables once
    costab = []
    sintab = []
    for lk in kln:
        costab.append([mpf(math.cos(lk * float(t))) for t in ts])
        sintab.append([mpf(math.sin(lk * float(t))) for t in ts])
    kscale = [mpf(k) ** mpf("-0.5") for k in range(1, N + 1)]
    for k in range(N):
        rk = kscale[k]
        ck, sk = costab[k], sintab[k]
        # Re(phi_k) = Re(zeta)*rk*cos - Im(zeta)*rk*sin ... careful:
        # phi_k = zeta * rk * e^{-i t log k} = zeta * rk (cos - i sin)
        re_phik = [(z.real * c + z.imag * s) * rk for z, c, s in zip(zs, ck, sk)]
        b[k] = sum(w * rp * d for w, rp, d in zip(ws, re_phik, dens)) * 2 / (2 * pi)
    for j in range(N):
        rj = kscale[j]
        cj, sj = costab[j], sintab[j]
        re_phij = [(z.real * c + z.imag * s) * rj for z, c, s in zip(zs, cj, sj)]
        im_phij = [(z.imag * c - z.real * s) * rj for z, c, s in zip(zs, cj, sj)]
        for k in range(j, N):
            rk2 = kscale[k]
            ck2, sk2 = costab[k], sintab[k]
            re_phik = [(z.real * c + z.imag * s) * rk2 for z, c, s in zip(zs, ck2, sk2)]
            im_phik = [(z.imag * c - z.real * s) * rk2 for z, c, s in zip(zs, ck2, sk2)]
            # phi_k conj(phi_j) = (re_k + i im_k)(re_j - i im_j)
            # Re = re_k re_j + im_k im_j
            acc = sum(w * (a1 * a2 + b1 * b2) * d for w, a1, b1, a2, b2, d
                      in zip(ws, re_phik, im_phik, re_phij, im_phij, dens))
            Gjk = acc * 2 / (2 * pi)
            G[j][k] = Gjk
            G[k][j] = Gjk
    return G, b, nrm


def solve_d2(G, b, nrm):
    N = len(b)
    A = mp.matrix(N, N)
    for j in range(N):
        for k in range(N):
            A[j, k] = G[j][k]
    bv = mp.matrix(N, 1)
    for j in range(N):
        bv[j] = b[j]
    x = mp.lu_solve(A, bv)
    quad_form = sum(b[j] * x[j] for j in range(N))
    return nrm - quad_form


def cell(name, T0f, epsf, N=16):
    T0 = mpf(T0f)
    eps = mpf(epsf)
    t0 = time.time()
    nrm_closed = 1 / (4 * eps * (eps ** 2 + T0 ** 2))
    nrm_num = wnorm2(T0, eps)
    dev = abs(nrm_num - nrm_closed) / nrm_closed
    G, b, nrm = build_system(T0, eps, N)
    d2 = solve_d2(G, b, nrm)
    rel = d2 / nrm
    print(f"cell {name} (T0={T0f}, eps={epsf}, N={N}): "
          f"||1||^2 num/closed dev {mp.nstr(dev, 3)} | "
          f"d^2/||1||^2 = {mp.nstr(rel, 6)}   [norm used {mp.nstr(nrm, 6)}] "
          f"({time.time()-t0:.0f}s)", flush=True)
    return rel


def main():
    print("heat73 — m1 independent re-measure of m2 cycle-20 sliding-weight "
          "cells (zeta, unconstrained d^2, N=16 vs m2 N=48)", flush=True)
    print("m2 N=48 reference: (a) 2.231e-6  (b) 0.56742  (c) 0.05772",
          flush=True)
    a = cell("a T0=0 far below 1st zero", "0", "0.3")
    c = cell("c T0=45.666 in gap", "45.666", "0.3")
    b = cell("b T0=49.7738 ON 10th zero", "49.7738", "0.3")
    print(f"\nADJUDICATION: (b)/(c) ratio = {mp.nstr(b/c, 4)} "
          f"(m2 at N=48: 9.8x); (b) = {mp.nstr(b, 4)} "
          f"{'STALL CONFIRMED' if b > 0.2 else 'no stall at N=16'}; "
          f"(c) = {mp.nstr(c, 4)} "
          f"{'DESCENT CONFIRMED' if c < 0.2 else 'no descent'}; "
          f"(a) = {mp.nstr(a, 4)}", flush=True)


if __name__ == "__main__":
    main()
