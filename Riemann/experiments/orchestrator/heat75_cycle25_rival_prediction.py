#!/usr/bin/env python3
"""heat75 — m1's RIVAL PREDICTION for m2's CYCLE 25 site S2 (m1-L155).

Committed BEFORE m2's hash-frozen scored runner (m2_c25_scored.py, sha256
0120a029173dafbe575a36a2f2376ad2ae836267bd31cb1debecb4c1aa263362) is run.
Everything gradeable is fixed in their prereg (6454ea5); this script measures
the same object on m1's OWN instrument:

  site S2   = K_T200 - Gram(z3) - Gram(z4) - Gram(z5) - Gram(z6)
              + 2*Gram(g_a) + 2*Gram(g_b)          [launch, site b]
              + 2*Gram(g_a) + 2*Gram(g_b')         [launch', site bs]
  g_a  = z3 + (z4-z3)*7/8 = 29.74812380764528515442463
  g_b  = z5 + (z6-z5)*4/8 = 35.26061987328243047394007   (cancellation site)
  g_b' = z5 + (z6-z5)*3/8 = 34.67923030189662027812064   (same-sign control)
  d_a = 0.1;  d_c solved on MY instrument by bisection so f_b(d_c) = -f_a(d_a)
  quad = CROSS-FORM (heat72p convention, verified vs m2 twice):
      Q[i,j] = 2 Re[ u_i(p) conj(u_j(q)) + u_j(p) conj(u_i(q)) ],
      p = 1/2+d+i g0, q = 1/2-d+i g0  =>  quad(0) = 2*Gram(g0)

INDEPENDENT PATH (nothing imported from m2 code):
  * K_T200 / G_raw from MY heat72k export (dps-45 strings), not their matrices
  * u-values from MY composite quadrature (mp.quad over per-genome breakpoint
    lists, dps 45) — a different scheme family from their degree-8 Gauss-
    Legendre instrument
  * eigensolves in pure mpmath at dps 45
  * delta_c re-solved here from MY launch eigenvector

Taylor predictor (their pre-stated form, independently implemented):
  u^(k)(s0) = int phi(t) t^k e^{s0 t} dt,  u_d = sum_k d^k/k! u^(k);
  tyK = lam_min of launch with a leg's quad replaced by its order-K Taylor
  form.  Band halfwidth = 2*|ty6 - ty4| (m1-L150 sec 3 rule).

DISCIPLINE (heat72p precedent): the EXACT column (untruncated quadruples,
true eigensolve at the rung deltas) is computed here for my own post-reveal
certification but is HELD from the exchange letter — the letter carries
ty2/ty4/ty6 + bands only, so my exact column cannot pre-empt their scored
reveal.  It stays in the local .out.
"""
import json
import os
import time
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72k_identity_target_m8.json"
PREREG = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/machine2_cycle25_prereg.json"
N = 8
HALF = mpf(1) / 2
T0 = time.time()


def theta_step(s):
    if s <= 0:
        return mpf(0)
    if s >= 1:
        return mpf(1)
    return exp(-1 / s) / (exp(-1 / s) + exp(-1 / (1 - s)))


def window(x):
    return theta_step((8 - fabs(x)) / 2)


def bumpval(t):
    if fabs(t) >= 1:
        return mpf(0)
    return exp(-1 / (1 - t * t))


def make_phi(genome):
    triples = [(mpf(str(c)), mpf(str(mu)), mpf(str(s))) for (c, mu, s) in genome]

    def phi(x):
        tot = mpf(0)
        for (c, mu, s) in triples:
            tot += c * bumpval((x - mu) / s)
        return window(x) * tot

    edges = sorted(set([mpf(-8), mpf(-6), mpf(6), mpf(8)] +
                       [mu - s for (c, mu, s) in triples] + [mu + s for (c, mu, s) in triples]))
    return phi, edges


def eig_full(F, Gm):
    """generalized symmetric eigensolve F v = lam G v; returns (sorted lams, G-orthonormal vecs)."""
    L = mp.cholesky(Gm)
    Li = mp.inverse(L)
    B = Li * F * Li.T
    B = (B + B.T) / 2
    E, V = mp.eigsy(B)
    idx = sorted(range(N), key=lambda i: E[i])
    return [E[i] for i in idx], [Li.T * mp.matrix([V[r, i] for r in range(N)]) for i in idx]


def lam0(F, Gm):
    return eig_full(F, Gm)[0][0]


def bil(M, v, w):
    return sum(v[i] * M[i, j] * w[j] for i in range(N) for j in range(N))


def gnorm(P, Gm):
    L = mp.cholesky(Gm)
    Li = mp.inverse(L)
    B = Li * P * Li.T
    B = (B + B.T) / 2
    E, _ = mp.eigsy(B)
    return max(fabs(E[i]) for i in range(N))


def main():
    genomes = json.load(open(GEN))["genomes"]["s1/M8"]
    idt = json.load(open(IDT))["seeds"]["s1/M8"]
    pre = json.load(open(PREREG))
    S = pre["site"]
    K200 = mp.matrix(N, N)
    Graw = mp.matrix(N, N)
    for i in range(N):
        for j in range(N):
            K200[i, j] = mpf(idt["K_T200"][i][j])
            Graw[i, j] = mpf(idt["G_raw"][i][j])

    # --- cert block: my export's own anchor + my K reconstruction -----------------
    print("=" * 78)
    print("A  CERT BLOCK (my export, my quadrature, nothing of m2's)")
    print("=" * 78)
    anchor = lam0(K200, Graw)
    print("lam_min(K_T200, G_raw) on MY export = %s" % mp.nstr(anchor, 20))
    print("  (letter-quoted m1 anchor 1.176119142e-5 is NOT my published value;")
    print("   my published anchor (L121/L122) = 1.1761206927492675e-5)")

    phis, edges = zip(*[make_phi(g) for g in genomes])
    U0ref = [mpf(x) for x in idt["U0"]]

    def U(i, s, k=0):
        return quad(lambda t: (t ** k) * phis[i](t) * exp(s * t), edges[i])

    d0 = max(fabs(U(i, mpf(0)) - U0ref[i]) for i in range(N))
    print("max|u_i(0) - U0_export| = %s" % mp.nstr(d0, 6))

    def gram(g0):
        uv = [U(i, mpc(HALF, g0)) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(uv[i] * conj(uv[j]))
        return M

    k = 1
    Krecon = mp.matrix(N, N)
    nz = 0
    while True:
        g = mpf(str(mpim(zetazero(k))))
        if g > 200:
            break
        Krecon += gram(g)
        nz += 1
        k += 1
    dK = max(fabs(Krecon[i, j] - K200[i, j]) for i in range(N) for j in range(N))
    print("K reconstruction: %d zeta zeros <= 200 (my zetazero source), max|dK| = %s" % (nz, mp.nstr(dK, 6)))

    # --- site, locked to their committed prereg strings ---------------------------
    print()
    print("=" * 78)
    print("B  SITE S2 (locked to their committed machine2_cycle25_prereg.json)")
    print("=" * 78)
    z3, z4, z5, z6 = [mpf(x) for x in S["removed"]]
    g_a, g_b, g_bs = mpf(S["g_a"]), mpf(S["g_b"]), mpf(S["g_bs"])
    my_ga = z3 + (z4 - z3) * mpf(7) / 8
    my_gb = z5 + (z6 - z5) * mpf(4) / 8
    my_gbs = z5 + (z6 - z5) * mpf(3) / 8
    print("grid check |mine-theirs|: g_a %s  g_b %s  g_bs %s"
          % tuple(mp.nstr(fabs(a - b), 4) for a, b in ((my_ga, g_a), (my_gb, g_b), (my_gbs, g_bs))))
    zcheck = max(fabs(mpf(str(mpim(zetazero(kk)))) - zz) / zz for kk, zz in ((3, z3), (4, z4), (5, z5), (6, z6)))
    print("removed vs my zetazero, worst rel = %s" % mp.nstr(zcheck, 4))

    t1 = time.time()
    remA = gram(z3) + gram(z4)
    remB = gram(z5) + gram(z6)

    def quad_ex(g0, d):
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [U(i, p) for i in range(N)]
        uq = [U(i, q) for i in range(N)]
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i]))
        return M

    qA0, qB0, qB0s = quad_ex(g_a, mpf(0)), quad_ex(g_b, mpf(0)), quad_ex(g_bs, mpf(0))
    base = K200 - remA - remB
    LAUNCH, LAUNCH_S = base + qA0 + qB0, base + qA0 + qB0s
    vals, vecs = eig_full(LAUNCH, Graw)
    vals_s, vecs_s = eig_full(LAUNCH_S, Graw)
    v0, nrm = vecs[0], bil(Graw, vecs[0], vecs[0])
    v0s, nrm_s = vecs_s[0], bil(Graw, vecs_s[0], vecs_s[0])
    gapL, gapLs = vals[1] - vals[0], vals_s[1] - vals_s[0]
    print("launch   lam_min = %s   (theirs 2.0004746865698620975e-5)" % mp.nstr(vals[0], 20))
    print("         gap     = %s   (theirs 5.88105697061e-5)" % mp.nstr(gapL, 12))
    print("launch'  lam_min = %s   (theirs 1.2476977651181365402e-5)" % mp.nstr(vals_s[0], 20))
    print("         gap     = %s   (theirs 5.9346306721e-5)" % mp.nstr(gapLs, 12))
    print("launch   spectrum: %s" % [mp.nstr(x, 10) for x in vals])
    print("[site setup %.1fs]" % (time.time() - t1))

    # --- functionals and my delta_c ------------------------------------------------
    print()
    print("=" * 78)
    print("C  FUNCTIONALS (my instrument) + MY delta_c")
    print("=" * 78)
    DA = mpf(S["delta_a"])
    Pa = quad_ex(g_a, DA) - qA0

    def fb_of(d):
        return bil(quad_ex(g_b, d) - qB0, v0, v0) / nrm

    fa = bil(Pa, v0, v0) / nrm
    print("f_a(0.1)   = %s   (theirs -7.77892637869409366e-7)" % mp.nstr(fa, 18))

    t2 = time.time()
    lo, hi = mpf("0.02"), mpf("0.40")
    glo = fb_of(lo) + fa
    ghi = fb_of(hi) + fa
    assert (glo > 0) != (ghi > 0), "no bracket"
    it = 0
    while hi - lo > mpf("1e-20"):
        mid = (lo + hi) / 2
        gm = fb_of(mid) + fa
        if (gm > 0) == (glo > 0):
            lo, glo = mid, gm
        else:
            hi, ghi = mid, gm
        it += 1
    DC = (lo + hi) / 2
    Pb = quad_ex(g_b, DC) - qB0
    fb = bil(Pb, v0, v0) / nrm
    print("MY delta_c = %s   [%d bisections]" % (mp.nstr(DC, 22), it))
    print("their d_c  = %s" % S["delta_c"])
    print("f_b(d_c)   = %s" % mp.nstr(fb, 18))
    print("f_a + f_b  = %s   = %s of |f_a|   (theirs -7.14e-39 = 9.18e-33)"
          % (mp.nstr(fa + fb, 8), mp.nstr(abs(fa + fb) / abs(fa), 6)))

    D3, D4 = mpf("0.20"), mpf("0.30")
    Pb3, Pb4 = quad_ex(g_b, D3) - qB0, quad_ex(g_b, D4) - qB0
    fb3, fb4 = bil(Pb3, v0, v0) / nrm, bil(Pb4, v0, v0) / nrm
    Pas, Pbs = quad_ex(g_a, DA) - qA0, quad_ex(g_bs, DA) - qB0s
    fas = bil(Pas, v0s, v0s) / nrm_s
    fbs = bil(Pbs, v0s, v0s) / nrm_s
    print("f_b(0.20)  = %s   (theirs 1.17150614272e-6)" % mp.nstr(fb3, 12))
    print("f_b(0.30)  = %s" % mp.nstr(fb4, 12))
    print("launch' f_a= %s   f_b' = %s" % (mp.nstr(fas, 12), mp.nstr(fbs, 12)))
    print("[bisection %.1fs]" % (time.time() - t2))

    # --- second order + PT parameters ----------------------------------------------
    print()
    print("=" * 78)
    print("D  SECOND-ORDER DECOMPOSITION (my eigenvectors)")
    print("=" * 78)

    def second_order(Pa_, Pb_, vals_, vecs_, nrm_):
        sa = sb = X = mpf(0)
        for kk in range(1, N):
            nk = bil(Graw, vecs_[kk], vecs_[kk])
            A = bil(Pa_, vecs_[0], vecs_[kk]) / mp.sqrt(nrm_ * nk)
            Bv = bil(Pb_, vecs_[0], vecs_[kk]) / mp.sqrt(nrm_ * nk)
            den = vals_[0] - vals_[kk]
            sa += A * A / den
            sb += Bv * Bv / den
            X += 2 * A * Bv / den
        return sa, sb, X

    sa2, sb2, X2 = second_order(Pa, Pb, vals, vecs, nrm)
    sa3, sb3, X3 = second_order(Pa, Pb3, vals, vecs, nrm)
    sa3b, sb3b, X3b = second_order(Pa, Pb4, vals, vecs, nrm)
    sa4, sb4, X4 = second_order(Pas, Pbs, vals_s, vecs_s, nrm_s)
    print("R2 : self_a %s  self_b %s  CROSS %s  |self|/|X| %s"
          % (mp.nstr(sa2, 10), mp.nstr(sb2, 10), mp.nstr(X2, 12), mp.nstr(abs((sa2 + sb2) / X2), 6)))
    print("      (theirs self_a -5.52449909e-8  self_b -1.324267209e-7  CROSS -6.1128597945e-8  3.07)")
    print("R3 : self_a %s  self_b %s  CROSS %s" % (mp.nstr(sa3, 10), mp.nstr(sb3, 10), mp.nstr(X3, 12)))
    print("R3b: self_a %s  self_b %s  CROSS %s" % (mp.nstr(sa3b, 10), mp.nstr(sb3b, 10), mp.nstr(X3b, 12)))
    print("R4 : self_a %s  self_b %s  CROSS %s" % (mp.nstr(sa4, 10), mp.nstr(sb4, 10), mp.nstr(X4, 12)))

    print("\nPT parameters (G-metric ||P||/gap; theirs 34.6 / 56.1 / 84.8 / 214.1 / 19.4):")
    for nm, P, gp in (("P_a", Pa, gapL), ("P_b(d_c)", Pb, gapL), ("P_b(0.20)", Pb3, gapL),
                      ("P_b(0.30)", Pb4, gapL), ("P_b'", Pbs, gapLs)):
        print("   %-10s %s" % (nm, mp.nstr(gnorm(P, Graw) / gp, 8)))

    # --- H3 overlap predictions (second-order loss) ---------------------------------
    print("\noverlap-loss prediction (2nd order): ovl >= 1 - 1/2 * sum_k (|A_k|+|B_k|)^2/den_k^2")
    for nm, legs_, vals_, vecs_, nrm_ in (("R2", (Pa, Pb), vals, vecs, nrm),
                                          ("R3", (Pa, Pb3), vals, vecs, nrm),
                                          ("R4", (Pas, Pbs), vals_s, vecs_s, nrm_s)):
        loss = mpf(0)
        for kk in range(1, N):
            nk = bil(Graw, vecs_[kk], vecs_[kk])
            A = bil(legs_[0], vecs_[0], vecs_[kk]) / mp.sqrt(nrm_ * nk)
            Bv = bil(legs_[1], vecs_[0], vecs_[kk]) / mp.sqrt(nrm_ * nk)
            den = vals_[0] - vals_[kk]
            loss += (A + Bv) ** 2 / den ** 2
        print("   %s: 1 - ovl2 <= %s   => ovl >= %s" % (nm, mp.nstr(loss, 6), mp.nstr(1 - loss / 2, 12)))

    # --- Taylor ladder ---------------------------------------------------------------
    print()
    print("=" * 78)
    print("E  TAYLOR LADDER (my quadrature, my eigensolves) + MY EXACT COLUMN [LOCAL ONLY]")
    print("=" * 78)
    FACT = [mpf(1)] * 10
    for i in range(1, 10):
        FACT[i] = FACT[i - 1] * i

    def ders_at(g0, kmax=6):
        s0 = mpc(HALF, g0)
        return [[U(i, s0, kk) for i in range(N)] for kk in range(kmax + 1)]

    DR = {"a": ders_at(g_a), "b": ders_at(g_b), "bs": ders_at(g_bs)}

    def quad_ty(site, d, K):
        def dz(z):
            return [sum((z ** kk) * DR[site][kk][i] / FACT[kk] for kk in range(K + 1)) for i in range(N)]
        tp, tq = dz(d), dz(-d)
        M = mp.matrix(N, N)
        for i in range(N):
            for j in range(N):
                M[i, j] = 2 * mpre(tp[i] * conj(tq[j]) + tp[j] * conj(tq[i]))
        return M

    EXACT = {("a", DA): Pa, ("b", DC): Pb, ("b", D3): Pb3, ("b", D4): Pb4, ("bs", DA): Pbs}

    def leg_matrices(site, d):
        q0 = {"a": qA0, "b": qB0, "bs": qB0s}[site]
        out = {}
        for K in (2, 4, 6):
            out[K] = (quad_ty(site, d, K) - q0) if d != 0 else mp.matrix(N, N)
        out["ex"] = EXACT[(site, d)] if d != 0 else mp.matrix(N, N)
        return out

    t3 = time.time()
    LE = {"a": leg_matrices("a", DA), "b_dc": leg_matrices("b", DC), "b_20": leg_matrices("b", D3),
          "b_30": leg_matrices("b", D4), "bs": leg_matrices("bs", DA)}
    print("[derivative ladders %.1fs]" % (time.time() - t3))

    RUNGS = {"R0": (DA, mpf(0), "b", "a", None, "b"),
             "R1": (mpf(0), DC, "b", None, "b_dc", "b"),
             "R2": (DA, DC, "b", "a", "b_dc", "b"),
             "R1b": (mpf(0), D3, "b", None, "b_20", "b"),
             "R3": (DA, D3, "b", "a", "b_20", "b"),
             "R1e": (mpf(0), D4, "b", None, "b_30", "b"),
             "R3b": (DA, D4, "b", "a", "b_30", "b"),
             "R0s": (DA, mpf(0), "bs", "a", None, "bs"),
             "R1d": (mpf(0), DA, "bs", None, "bs", "bs"),
             "R4": (DA, DA, "bs", "a", "bs", "bs")}
    lam_launch = {"b": vals[0], "bs": vals_s[0]}
    res = {}
    print("\n%-5s %8s %10s %20s %20s %20s %22s" % ("rung", "d_a", "d_b", "ty2", "ty4", "ty6", "EXACT[LOCAL ONLY]"))
    for r, (da, db, site, la, lb, lsite) in RUNGS.items():
        Lb = (base + qA0 + qB0) if lsite == "b" else (base + qA0 + qB0s)
        row = {}
        for o in (2, 4, 6, "ex"):
            S_ = Lb
            if la is not None:
                S_ = S_ + LE[la][o]
            if lb is not None:
                S_ = S_ + LE[lb][o]
            row[o] = lam0(S_, Graw)
        res[r] = row
        print("%-5s %8s %10s %20s %20s %20s %22s"
              % (r, mp.nstr(da, 4), mp.nstr(db, 6), mp.nstr(row[2], 14), mp.nstr(row[4], 14),
                 mp.nstr(row[6], 14), mp.nstr(row["ex"], 14)), flush=True)

    # --- graded quantities from ty4 (+ my bands, my second-order cross) ---------------
    print()
    print("=" * 78)
    print("F  GRADED QUANTITIES (ty4 committed; band = 2|ty6-ty4|; EXACT local only)")
    print("=" * 78)
    def shift(r, o):
        return res[r][o] - lam_launch[RUNGS[r][2]]

    fam = {"R2": ("R0", "R1", fa, fb, X2), "R3": ("R0", "R1b", fa, fb3, X3),
           "R3b": ("R0", "R1e", fa, fb4, X3b), "R4": ("R0s", "R1d", fas, fbs, X4)}
    print("\n%-4s %14s %14s %14s %14s %12s %11s %11s"
          % ("rung", "s_A", "s_B", "shift", "D", "R_c", "|D|/|sh|%", "D/X"))
    for r, (ra, rb, fa_, fb_, X_) in fam.items():
        sA, sB, sh = shift(ra, 4), shift(rb, 4), shift(r, 4)
        Dv = sh - sA - sB
        Rc = abs(Dv) / (abs(fa_) + abs(fb_))
        print("%-4s %14s %14s %14s %14s %12s %11s %11s"
              % (r, mp.nstr(sA, 10), mp.nstr(sB, 10), mp.nstr(sh, 10), mp.nstr(Dv, 10),
                 mp.nstr(Rc, 8), mp.nstr(100 * abs(Dv / sh), 6), mp.nstr(Dv / X_, 6)))
    print("\ntheir committed values: R2 D=-1.29768e-7 Rc=0.083410 37.87%%;  R3 D=-2.63182e-7 Rc=0.135007 85.05%%;")
    print("                        R3b D=-7.11694e-6 Rc=1.9347;       R4 D=-6.45573e-9 Rc=0.0053916 0.497%%")
    fr = {}
    for r, (ra, rb, fa_, fb_, X_) in fam.items():
        sh = shift(r, 4)
        Dv = sh - shift(ra, 4) - shift(rb, 4)
        fr[r] = 100 * abs(Dv / sh)
    print("\nH1 replication ratio (frac_R2/frac_R3) = %s   (their prediction 0.445, band [0.147, 1.567])"
          % mp.nstr(fr["R2"] / fr["R3"], 6))

    print("\n%-5s %10s %12s" % ("rung", "band(+-)", "fires(ty4)"))
    for r in RUNGS:
        print("%-5s %10s %12s" % (r, mp.nstr(2 * abs(res[r][6] - res[r][4]), 6), res[r][4] < 0))

    print("\nheat75 done in %.1fs" % (time.time() - T0))


if __name__ == "__main__":
    main()
