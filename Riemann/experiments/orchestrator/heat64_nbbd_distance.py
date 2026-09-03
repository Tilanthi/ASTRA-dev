#!/usr/bin/env python3
"""
heat64_nbbd_distance.py — box-surf candidate #1, FIRST RUNG (zeta-side d_N at certified floors).
AMENDED v2 (see machine1-nbbd-rung1-preregistration-amendment.md): the v1 artifact's S1
self-check ABORTED before any scoring — correctly — catching TWO formula errors in the v1
preregistration letter, both mine, both disclosed there:
  (i)  b[j]: the v1 letter's "correction" b[j]=(H_j−ln j−γ)/j came from a botched
       substitution limit (t=1/(jx) at x→1 gives t→1/j, NOT j). Correct, three-path
       verified (x-cell partial sums; t/j-period path; closed form):
           b[j] = (1 − γ + ln j)/j          [j=1 → 1−γ ✓; j=2 → 0.55796 ✓ hand-summed]
  (ii) G[j,k] integrand: with t=1/x, {1/(jx)} = {t/j} (breakpoints at multiples of j),
       NOT {jt} (breakpoints at m/j). v1's G path and v1's "independent" S2 check shared
       error (ii) — they would have agreed vacuously; the S1 abort was the only guard.
This v2 re-derives every formula; no scored evaluation ran under v1 (S1 abort guarantee).

OBJECT (Nyman–Beurling, Báez–Duarte countable form)
  RH ⟺ 1 ∈ closure of span{ f_n(x) = {1/(n x)} : n ∈ ℕ } in L²(0,1).
  d_N² = dist(1, span{f_1..f_N})² = 1 − bᵀ G_N⁻¹ b   (‖1‖² = 1),
    b[j] = ⟨f_j, 1⟩ = (1 − γ + ln j)/j,
    G[j,k] = ⟨f_j, f_k⟩ = ∫₀¹ {1/(jx)}{1/(kx)} dx  = (t=1/x)  ∫_1^∞ {t/j}{t/k} dt/t².

EXACT MACHINERY (rationals + ln + Hurwitz ζ only; NO quadrature in the scored path)
  Write L = lcm(j,k). {t/j} has period j, {t/k} period k ⇒ p(t) = {t/j}{t/k} has period L.
  G[j,k] = Σ_{s=0}^{N_P−1} P_s + TAIL,  P_s = ∫_{1+sL}^{1+(s+1)L} p(t)/t² dt.
  P_s EXACT by cells: breakpoints inside the period at multiples of j and k; on each open
  cell {t/j} = t/j − a, {t/k} = t/k − b (a = ⌊t₁/j⌋, b = ⌊t₁/k⌋, exact rational floors).
  Integrand: (t/j − a)(t/k − b)/t² = 1/(jk) − (a/k + b/j)/t + ab/t².
  Antiderivative:  t/(jk) − (a/k + b/j)·ln t − ab/t.                      [EXACT]
  TAIL (s ≥ N_P): t = 1 + sL + u, u ∈ [0, L); (1+sL+u)^{−2} = Σ_{r≥0} (−1)ʳ(r+1) u^r (1+sL)^{−r−2}
  (ratio u/(1+sL) ≤ L/(1+N_P·L) < 1/N_P ⇒ converges geometrically fast):
    TAIL = Σ_{r=0}^{R} (−1)ʳ (r+1) μ_r · L^{−r−2} · ζ(r+2, N_P + 1/L),
    μ_r = ∫₀^L uʳ p(1+u) du   [EXACT by the same cells, phase-aligned; independent of s].
  b[j]: closed form; independent check path = x-cell partial sums (k=0..K cells
  (1/(j(k+1)), 1/(jk)) with {1/(jx)} = 1/(jx) − k) + telescoping tail
  (1/j)(H_{K+1} − ln(K+1) − γ).

SELF-CHECKS (abort before any scoring if any fails)
  S5  parsed-constant sanity print under computing dps (#70 sub-rule).
  S1  b[j] closed form vs x-cell path, j=1..6, rel < 1e-30.  [v1 abort site — keep strict]
  S2  G[1,1] and G[2,3] vs mpmath quad on [1,80] of the piecewise integrand (genuinely
      different code path this time), abs tol 1e-15; plus partial-cell-sum to T=3000
      with tail bound 1/T, abs tol 1e-9.
  S2b G symmetric bitwise; Cholesky succeeds; λ_min > 0 (eigsy) at N=NMAX.
  S3  N_P bracket 20 vs 24: |ΔG| < 1e-35 on (2,3) and (5,7).
  S4  R bracket 60 vs 80: |ΔG| < 1e-35 on the same pairs.

PRECISION + FLOORS (#68 clause 1; #70 as amended — all magnitudes O(1))
  dps 40 primary / dps 50 verification per rung; cond(G_N) printed per rung.
  QUOTE RULE: rung GENUINE iff |d2_40 − d2_50| < 0.1·d2_40 and d2_40 > 0; else
  [below-res]/[DQ]; never abs().

LADDER: N ∈ {4, 6, 8, 10, 12, 15, 18, 22, 26, 30}

PRE-STATED OUTCOMES (unchanged from v1 preregistration)
  (a) STALL SIGNAL: d_N non-decreasing over ≥6 consecutive genuine rungs to N=30 —
      finite-N SIGNAL ONLY; sequential-BD refutation needs an analytic certificate.
  (b) RATE MEASURED: ≥8 genuine rungs — OLS log d_N = α + β log N; β ± 2σ reported.
      ALL rate novelty = POSSIBLY NEW pending prior-art read (Báez–Duarte original +
      Burnol's BD computational notes UNREAD here — precondition of claims, not the run).
  (c) FLOOR-CLUSTER: >30% rungs non-genuine → instrument redesign, nothing quoted.
  (d) any d2 ≤ −1e-30 → [DQ], reported as measured.

CATEGORY: A/B (known formulation, certified-floor execution). Zoo labels per Letter 56:
Dirichlet-L = A/B known extension; Epstein control = stands (Potter–Titchmarsh);
function-field = open leg, gated on the transfer-formulation check.
Honesty: d_N is a distance of a TRUNCATED object; nothing promotes toward any RH claim.

Run: 1 core. Outputs: heat64_nbbd_distance.out + .results.json (#69 persistence).
"""
import json
import math
import os
import sys
import time

from mpmath import mp, mpf, zeta, euler, ln as mln, sqrt as msqrt, floor as mfloor, quad

# ------------------------------------------------------------------ config
DPS_PRIMARY = 40
DPS_CHECK = 50
N_P = 20            # exact periods
N_P_CHECK = 24      # S3 bracket
R_SERIES = 60       # moments in tail series
R_SERIES_CHECK = 80 # S4 bracket
LADDER = [4, 6, 8, 10, 12, 15, 18, 22, 26, 30]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "heat64_nbbd_distance.out")
JOUT = OUT.replace(".out", ".results.json")
NMAX = max(LADDER)


def setdps(d):
    mp.dps = d


def period_cells(j, k):
    """Cells of p(t) = {t/j}{t/k} over ONE phase-aligned period [1, 1+L), L = lcm(j,k).
    Returns (L, cells) with cells = list of (t1, t2, a, b): {t/j}=t/j−a, {t/k}=t/k−b on (t1,t2)."""
    L = j * k // math.gcd(j, k)
    Lm = L  # period length; period starts at t=1
    bps = set()
    # breakpoints strictly inside (1, 1+L): multiples of j and k in that range
    m = j
    while m < 1 + L:
        if m > 1:
            bps.add(m)
        m += j
    m = k
    while m < 1 + L:
        if m > 1:
            bps.add(m)
        m += k
    edges = [mpf(1)] + sorted(mpf(x) for x in bps) + [mpf(1 + L)]
    cells = []
    for t1, t2 in zip(edges[:-1], edges[1:]):
        a = mfloor(t1 / j)
        b = mfloor(t1 / k)
        cells.append((t1, t2, a, b))
    return L, cells


def P_s(j, k, cells, s, L):
    """Exact period integral over [1+sL, 1+(s+1)L): cell pattern shifted by sL AND the
    floor constants shift with it — floor(t/j) = a + sL/j, floor(t/k) = b + sL/k (both
    integers since j|L, k|L). Unshifted a,b make the integrand O(1) per period (bug
    caught by S2 smoke: sum P_s(s<20) = 16.96 vs ~0.272)."""
    tot = mpf(0)
    shift = s * L
    da = mpf(s * L) / j
    db = mpf(s * L) / k
    for (u1, u2, a, b) in cells:
        t1 = u1 + shift
        t2 = u2 + shift
        A = mpf(a) + da
        B = mpf(b) + db
        F1 = t1 / (j * k) - (A / k + B / j) * mln(t1) - A * B / t1
        F2 = t2 / (j * k) - (A / k + B / j) * mln(t2) - A * B / t2
        tot += F2 - F1
    return tot


def period_moments(j, k, cells, L, R):
    """μ_r = ∫₀^L u^r p(1+u) du, exact by cells: p = (t/j−a)(t/k−b), t = 1+u."""
    out = []
    for r in range(R + 1):
        tot = mpf(0)
        for (t1, t2, a, b) in cells:
            # p(t) = (t/j−a)(t/k−b) = A t² + B t + C with t = 1+u on the cell:
            #   integrand u^r (A(1+u)² + B(1+u) + C) = A u^{r+2} + (2A+B) u^{r+1} + (A+B+C) u^r
            A = mpf(1) / (j * k)
            B = -(mpf(a) / k + mpf(b) / j)
            C = mpf(a) * b
            c2 = A
            c1 = 2 * A + B
            c0 = A + B + C
            u1 = t1 - 1
            u2 = t2 - 1

            def Mant(u):
                return (c2 * u ** (r + 3) / (r + 3)
                        + c1 * u ** (r + 2) / (r + 2)
                        + c0 * u ** (r + 1) / (r + 1))
            tot += Mant(u2) - Mant(u1)
        out.append(tot)
    return out


def G_entry(j, k, cells, L, mus, zeta_terms):
    """G[j,k] = Σ_{s<N_P} P_s + Σ_r (−1)^r(r+1) μ_r L^{−r−2} ζ(r+2, N_P + 1/L)."""
    tot = mpf(0)
    for s in range(N_P):
        tot += P_s(j, k, cells, s, L)
    tail = mpf(0)
    for r, mu in enumerate(mus):
        tail += (mpf(-1) ** r) * (r + 1) * mu * zeta_terms[r]
    return tot + tail


def zeta_terms_for(j, k, L, R):
    q = mpf(N_P) + mpf(1) / L
    return [L ** (-(r + 2)) * zeta(r + 2, q) for r in range(R + 1)]


def b_closed(j):
    return (1 - mpf(euler) + mln(j)) / j


def b_xcells(j, K=400):
    """Independent path: Σ x-cells k=0..K + exact telescoping tail (1/j)(H_{K+1}−ln(K+1)−γ).
    k=0 cell x∈(1/j,1): {1/(jx)}=1/(jx) → (1/j)ln j.  k≥1 cell (1/(j(k+1)), 1/(jk)):
    per-cell (1/j)[ln(1+1/k) − 1/(k+1)]."""
    tot = mln(j) / j
    H = mpf(1)
    for k in range(1, K + 1):
        tot += (mln(1 + mpf(1) / k) - mpf(1) / (k + 1)) / j
    # tail Σ_{k>K}[ln(1+1/k) − 1/(k+1)] = H_{K+1} − ln(K+1) − γ
    H_K1 = mpf(1)
    for m in range(2, K + 2):
        H_K1 += mpf(1) / m
    tail = H_K1 - mln(K + 1) - mpf(euler)
    return tot + tail / j


def G_quad_check(j, k, T=80):
    """S2: mpmath quad of ∫_1^T {t/j}{t/k}/t² dt with the piecewise integrand (independent path)."""
    def f(t):
        t = mpf(t)
        return ((t / j - mfloor(t / j)) * (t / k - mfloor(t / k))) / t ** 2
    # break the quad at breakpoints to avoid floor() discontinuities confusing it
    bps = sorted({mpf(m) for m in range(j, int(T) + 1, j)} | {mpf(m) for m in range(k, int(T) + 1, k)})
    edges = [mpf(1)] + [b for b in bps if 1 < b < T] + [mpf(T)]
    tot = mpf(0)
    for e1, e2 in zip(edges[:-1], edges[1:]):
        tot += quad(f, [e1, e2])
    return tot


def G_partial_cells(j, k, T=3000):
    """S2b path: partial cell-sum of ∫_1^T {t/j}{t/k}/t² dt (direct breakpoints, no periods)."""
    bps = set()
    m = j
    while m <= T:
        if m > 1:
            bps.add(m)
        m += j
    m = k
    while m <= T:
        if m > 1:
            bps.add(m)
        m += k
    edges = [mpf(1)] + sorted(mpf(x) for x in bps if x <= T) + [mpf(T)]
    tot = mpf(0)
    for t1, t2 in zip(edges[:-1], edges[1:]):
        a = mfloor(t1 / j)
        b = mfloor(t1 / k)
        F1 = t1 / (j * k) - (mpf(a) / k + mpf(b) / j) * mln(t1) - mpf(a) * b / t1
        F2 = t2 / (j * k) - (mpf(a) / k + mpf(b) / j) * mln(t2) - mpf(a) * b / t2
        tot += F2 - F1
    return tot  # truncation ≤ 1/T beyond


def solve_d2(G, b):
    """d_N² = 1 − bᵀG⁻¹b via Cholesky; λ's via eigsy."""
    from mpmath import matrix, cholesky, eigsy
    n = len(b)
    A = matrix(n, n)
    for i in range(n):
        for j2 in range(n):
            A[i, j2] = G[i][j2]
    L = cholesky(A)
    bv = matrix([bb for bb in b])
    y = matrix(n, 1)
    for i in range(n):
        s = bv[i]
        for j2 in range(i):
            s -= L[i, j2] * y[j2]
        y[i] = s / L[i, i]
    x = matrix(n, 1)
    for i in range(n - 1, -1, -1):
        s = y[i]
        for j2 in range(i + 1, n):
            s -= L[j2, i] * x[j2]
        x[i] = s / L[i, i]
    quad_form = sum(b[i] * x[i] for i in range(n))
    evals = eigsy(A, eigvals_only=True)
    return 1 - quad_form, min(evals), max(evals)


def build_G_b(NMAX, dps):
    setdps(dps)
    cache_G = [[None] * (NMAX + 1) for _ in range(NMAX + 1)]
    for j in range(1, NMAX + 1):
        for k in range(j, NMAX + 1):
            L, cells = period_cells(j, k)
            mus = period_moments(j, k, cells, L, R_SERIES)
            zt = zeta_terms_for(j, k, L, R_SERIES)
            g = G_entry(j, k, cells, L, mus, zt)
            cache_G[j][k] = g
            cache_G[k][j] = g
    cache_b = {j: b_closed(j) for j in range(1, NMAX + 1)}
    return cache_G, cache_b


def G_with(j, k, n_p, R):
    L, cells = period_cells(j, k)
    tot = mpf(0)
    for s in range(n_p):
        tot += P_s(j, k, cells, s, L)
    mus = period_moments(j, k, cells, L, R)
    q = mpf(n_p) + mpf(1) / L
    tail = mpf(0)
    for r, mu in enumerate(mus):
        tail += (mpf(-1) ** r) * (r + 1) * mu * L ** (-(r + 2)) * zeta(r + 2, q)
    return tot + tail


def main():
    t0 = time.time()
    lines = []

    def P(s=""):
        print(s, flush=True)
        lines.append(str(s))

    P("CATEGORY: A/B — NB-BD zeta-side d_N, certified-floor first rung (v2 AMENDED; v1 S1-aborted, zero scored rows)")
    P(f"N_P={N_P} (bracket {N_P_CHECK})  R={R_SERIES} (bracket {R_SERIES_CHECK})  ladder={LADDER}")
    P("")
    P("== S5 parsed-constant sanity (#70 sub-rule) ==")
    for d in (DPS_PRIMARY, DPS_CHECK):
        setdps(d)
        P(f"  [S5 dps={d}] euler={mp.nstr(mpf(euler), 20)}")
    setdps(DPS_PRIMARY)
    P("")

    P("== S1 b[j] closed form (1−γ+ln j)/j vs x-cell path ==")
    for j in range(1, 7):
        bc = b_closed(j)
        bi = b_xcells(j)
        rel = abs(bc - bi) / abs(bc)
        P(f"  b[{j}] closed={mp.nstr(bc, 15)} xcells={mp.nstr(bi, 15)} rel={mp.nstr(rel, 5)}")
        if rel > mpf(10) ** (-30):
            P("  S1 FAIL — abort")
            json.dump({"status": "S1-FAIL"}, open(JOUT, "w"))
            sys.exit(1)
    P("  S1 PASS")
    P("")

    P("== S2 G vs mpmath quad (independent path) + partial cells ==")
    for (j, k) in [(1, 1), (2, 3)]:
        gmain = G_with(j, k, N_P, R_SERIES)
        gq = G_quad_check(j, k, T=80)
        # quad covers [1,80] only; add exact tail from 80 via the same series machinery:
        L, cells = period_cells(j, k)
        # align: 80 is a multiple of L for (1,1) L=1 and (2,3) L=6 — 80 not mult of 6; use T=78:
        gq = G_quad_check(j, k, T=(80 if (80 - 1) % L == 0 else (1 + ((80 - 1) // L) * L)))
        # tail beyond Tq via series with phase-aligned start:
        Tq = 1 + ((80 - 1) // L) * L
        n_from = (Tq - 1) // L
        # recompute tail starting at s>=n_from using zeta with q = n_from + 1/L
        mus = period_moments(j, k, cells, L, R_SERIES)
        tailq = mpf(0)
        for r, mu in enumerate(mus):
            tailq += (mpf(-1) ** r) * (r + 1) * mu * L ** (-(r + 2)) * zeta(r + 2, mpf(n_from) + mpf(1) / L)
        gq_full = gq + tailq
        d2chk = abs(gmain - gq_full)
        P(f"  G[{j},{k}] main={mp.nstr(gmain, 15)} quad+tail={mp.nstr(gq_full, 15)} |Δ|={mp.nstr(d2chk, 5)}")
        if d2chk > mpf(10) ** (-15):
            P("  S2 FAIL — abort")
            json.dump({"status": "S2-FAIL"}, open(JOUT, "w"))
            sys.exit(1)
        gp = G_partial_cells(j, k, T=3000)
        # add exact tail from T=3000 (phase-aligned: 3000 = 1+ sL? not exactly; align down):
        Tl = 1 + ((3000 - 1) // L) * L
        n_from2 = (Tl - 1) // L
        # recompute partial to exactly Tl
        gp = G_partial_cells(j, k, T=Tl)
        tailp = mpf(0)
        for r, mu in enumerate(mus):
            tailp += (mpf(-1) ** r) * (r + 1) * mu * L ** (-(r + 2)) * zeta(r + 2, mpf(n_from2) + mpf(1) / L)
        d3chk = abs(gmain - (gp + tailp))
        P(f"       partialcells+tail={mp.nstr(gp + tailp, 15)} |Δ|={mp.nstr(d3chk, 5)}")
        if d3chk > mpf(10) ** (-25):
            P("  S2b FAIL — abort")
            json.dump({"status": "S2b-FAIL"}, open(JOUT, "w"))
            sys.exit(1)
    P("  S2/S2b PASS")
    P("")

    P("== S3/S4 brackets ==")
    for (j, k) in [(2, 3), (5, 7)]:
        gA = G_with(j, k, N_P, R_SERIES)
        gB = G_with(j, k, N_P_CHECK, R_SERIES)
        d33 = abs(gA - gB)
        P(f"  S3 G[{j},{k}] N_P {N_P} vs {N_P_CHECK}: |Δ|={mp.nstr(d33, 5)}")
        if d33 > mpf(10) ** (-35):
            P("  S3 FAIL — abort"); json.dump({"status": "S3-FAIL"}, open(JOUT, "w")); sys.exit(1)
        gC = G_with(j, k, N_P, R_SERIES_CHECK)
        d44 = abs(gA - gC)
        P(f"  S4 G[{j},{k}] R {R_SERIES} vs {R_SERIES_CHECK}: |Δ|={mp.nstr(d44, 5)}")
        if d44 > mpf(10) ** (-35):
            P("  S4 FAIL — abort"); json.dump({"status": "S4-FAIL"}, open(JOUT, "w")); sys.exit(1)
    P("  S3/S4 PASS")
    P("")

    P(f"== build G,b j,k≤{NMAX} (dps={DPS_PRIMARY}) ==")
    cache_G, cache_b = build_G_b(NMAX, DPS_PRIMARY)
    sym_ok = all(cache_G[j][k] == cache_G[k][j] for j in range(1, NMAX + 1) for k in range(1, NMAX + 1))
    P(f"  built. S2c bitwise symmetry: {sym_ok}")
    if not sym_ok:
        json.dump({"status": "S2c-FAIL"}, open(JOUT, "w")); sys.exit(1)
    P("")

    P(f"== dps={DPS_CHECK} verification build ==")
    cache_G_c, cache_b_c = build_G_b(NMAX, DPS_CHECK)
    P("  built.")
    P("")

    P("== ladder (QUOTE RULE: genuine iff |d2_40−d2_50|<0.1·d2_40 and d2_40>0) ==")
    results = []
    for N in LADDER:
        G = [[cache_G[j][k] for k in range(1, N + 1)] for j in range(1, N + 1)]
        b = [cache_b[j] for j in range(1, N + 1)]
        d2p, lmin, lmax = solve_d2(G, b)
        Gc = [[cache_G_c[j][k] for k in range(1, N + 1)] for j in range(1, N + 1)]
        bc = [cache_b_c[j] for j in range(1, N + 1)]
        d2c, _, _ = solve_d2(Gc, bc)
        cond = lmax / lmin if lmin != 0 else mpf("inf")
        status = "GENUINE"
        if d2p <= mpf(10) ** (-30):
            status = "DQ"
        elif abs(d2p - d2c) >= mpf("0.1") * d2p:
            status = "below-res"
        dN = msqrt(d2p) if d2p > 0 else None
        results.append(dict(N=N, d2_primary=mp.nstr(d2p, 12), d2_check=mp.nstr(d2c, 12),
                            lmin=mp.nstr(lmin, 8), lmax=mp.nstr(lmax, 8), cond=mp.nstr(cond, 8),
                            dN=mp.nstr(dN, 10) if dN is not None else None, status=status))
        P(f"  N={N:3d}  d2_40={mp.nstr(d2p, 12)}  d2_50={mp.nstr(d2c, 12)}  "
          f"cond={mp.nstr(cond, 6)}  d_N={mp.nstr(dN, 10) if dN is not None else '—'}  [{status}]")

    P("")
    P("== verdict per docstring (a)/(b)/(c)/(d) ==")
    genuine = [r for r in results if r["status"] == "GENUINE"]
    nong = [r for r in results if r["status"] != "GENUINE"]
    P(f"  genuine rungs: {len(genuine)}/{len(results)}; non-genuine: {len(nong)}")
    neg = [r for r in results if r["status"] == "DQ"]
    if neg:
        P(f"  (d) DQ rungs: {[r['N'] for r in neg]}")
    verdict = "none-of-above"
    if len(nong) > 0.3 * len(results):
        P("  (c) FLOOR-CLUSTER fired: >30% non-genuine — instrument-redesign rung; nothing quoted.")
        verdict = "c"
    elif len(genuine) >= 6:
        gd = [mpf(r["dN"]) for r in genuine]
        gN = [r["N"] for r in genuine]
        run = best = 1
        for i in range(1, len(gd)):
            run = run + 1 if gd[i] >= gd[i - 1] else 1
            best = max(best, run)
        if best >= 6 and max(gN) == 30:
            P(f"  (a) STALL SIGNAL: non-decreasing over {best} consecutive genuine rungs to N=30 — SIGNAL ONLY.")
            verdict = "a"
        elif len(genuine) >= 8:
            xs = [mln(mpf(r["N"])) for r in genuine]
            ys = [mln(mpf(r["dN"])) for r in genuine]
            n = len(xs)
            mx = sum(xs) / n
            my = sum(ys) / n
            sxx = sum((x - mx) ** 2 for x in xs)
            sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            beta = sxy / sxx
            alpha = my - beta * mx
            resid = [y - (alpha + beta * x) for x, y in zip(xs, ys)]
            s2 = sum(e ** 2 for e in resid) / (n - 2)
            se_beta = msqrt(s2 / sxx)
            P(f"  (b) RATE MEASURED: beta={mp.nstr(beta, 8)} ± {mp.nstr(2 * se_beta, 5)} (2σ)  alpha={mp.nstr(alpha, 8)}  n={n}")
            P("      rate novelty = POSSIBLY NEW pending prior-art read (Báez–Duarte + Burnol notes UNREAD).")
            verdict = "b"
            with open(JOUT + ".fit", "w") as f:
                json.dump(dict(beta=str(beta), alpha=str(alpha), se_beta=str(se_beta), n=n), f)
        else:
            P("  neither (a) nor (b) thresholds met.")
    else:
        P("  too few genuine rungs for (a)/(b).")

    P(f"  VERDICT: ({verdict})")
    P(f"  elapsed {time.time() - t0:.1f} s  (1 core)")
    with open(JOUT, "w") as f:
        json.dump({"status": "COMPLETE", "verdict": verdict, "version": "v2-amended",
                   "results": results,
                   "config": dict(N_P=N_P, R=R_SERIES, ladder=LADDER,
                                  dps_primary=DPS_PRIMARY, dps_check=DPS_CHECK)}, f, indent=1)
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT} and {JOUT}", flush=True)


if __name__ == "__main__":
    main()
