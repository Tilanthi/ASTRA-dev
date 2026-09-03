#!/usr/bin/env python3
"""heat65 — D-H Re>1 small-|s0| zero census (zoo rescue test).

PRE-REGISTERED in machine1-prereg-heat65-dh-census.md (exchange commit 7745559,
pushed BEFORE this script was written). Outcomes (a)-(d) pre-stated there.

Instrument: Davenport-Heilbronn f(s) = 1/2(1-i*kappa)L(s,chi) + 1/2(1+i*kappa)L(s,chibar),
chi mod 5 with chi(2)=i (quartic): chi(1)=1, chi(2)=i, chi(3)=-i, chi(4)=-1.
kappa is DERIVED from the functional equation (linear in kappa at generic s), NOT
hand-copied (#63); cross-checked against Ferry arXiv:1602.06328's printed anchor
tan(phi) = 0.284079.

Census: (i) real-axis sign scan sigma in (1,12); (ii) winding census on
sigma in (1,2) x t in (0,8), steps 0.05 and 0.025 must agree on the count.
All values at Re s > 1 are inside absolute convergence; Hurwitz form used for
exactness/speed. DQ-SECTION written into the .out by this runner (R3/R6).
"""
import os

from mpmath import mp, mpf, mpc, log as mlog, cos as mcos, sin as msin, \
    gamma as mgamma, pi as mpi, exp as mexp, hurwitz as mhurwitz, phase, \
    findroot, absmax

mp.dps = 30

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LN5 = log5 = mlog(5)  # noqa: F841 (parsed-constant style print below)

# chi mod 5, chi(2)=i (Ferry 2016); completely multiplicative
CHI = {1: mpc(1), 2: mpc(0, 1), 3: mpc(0, -1), 4: mpc(-1)}


def L(s, use_chibar=False):
    """L(s,chi) via Hurwitz continuation: 5^-s sum_a chi(a) zeta(s, a/5)."""
    tot = mpc(0)
    for a in (1, 2, 3, 4):
        c = CHI[a].conjugate() if use_chibar else CHI[a]
        tot += c * mhurwitz(s, mpf(a) / 5)
    return mexp(-s * log5) * tot


def A(s):
    """A(s) = (L_chi + L_chibar)/2 = sum Re chi(n) n^-s (by continuation)."""
    return (L(s) + L(s, True)) / 2


def B(s):
    """B(s) = (i/2)(L_chibar - L_chi) = sum Im chi(n) n^-s (by continuation)."""
    return (L(s, True) - L(s)) * mpc(0, 1) / 2


def W(s):
    """zeta-shape FE kernel for f (Ferry eq 3): 2^s pi^(s-1) 5^(1/2-s) G(1-s) cos(pi s/2)."""
    return (mpc(2) ** s) * (mpi ** (s - 1)) * (5 ** (mpf(1) / 2 - s)) \
        * mgamma(1 - s) * mcos(mpi * s / 2)


def f(s, kappa):
    return (1 - mpc(0, 1) * kappa) * L(s) / 2 + (1 + mpc(0, 1) * kappa) * L(s, True) / 2


def derive_kappa(s):
    """FE: A + kB = W(A' + kB') -> k = [W A' - A] / [B - W B'], primed = at 1-s."""
    w = W(s)
    return (w * A(1 - s) - A(s)) / (B(s) - w * B(1 - s))


def fe_residual(s, kappa):
    return abs(f(s, kappa) - W(s) * f(1 - s, kappa))


def main():
    lines = []

    def say(txt):
        print(txt, flush=True)
        lines.append(txt)

    # ---- S0: parsed-constant sanity (#70 sub-rule) ----
    say("ln5 = %s   euler = %s   ln(4pi) = %s" % (
        mp.nstr(log5, 12), mp.nstr(mp.euler, 12), mp.nstr(mlog(4 * mpi), 12)))
    C_floor = 2 + mp.euler - mlog(4 * mpi)
    say("C = 2+euler-ln(4pi) = %s" % mp.nstr(C_floor, 12))

    # ---- S1: kappa from the FE at two generic s; paper anchor 0.284079 ----
    s1 = mpc("0.65", "3.1")
    s2 = mpc("-1.3", "0.7")
    k1 = derive_kappa(s1)
    k2 = derive_kappa(s2)
    say("kappa derived at s=%s : %s" % (s1, mp.nstr(k1, 16)))
    say("kappa derived at s=%s : %s" % (s2, mp.nstr(k2, 16)))
    if abs(k1 - k2) > mpf("1e-20") or abs(k1.imag) > mpf("1e-20"):
        say("INSTRUMENT RED: kappa derivation inconsistent -> outcome (d), stop.")
        finish(lines, kappa=None)
        return
    kappa = k1.real
    say("kappa = %s  (Ferry anchor tan phi = 0.284079; diff = %s)" % (
        mp.nstr(kappa, 12), mp.nstr(abs(kappa - mpf("0.284079")), 6)))
    for s in (s1, s2, mpc("2.3", "-4.1")):
        say("  FE residual at %s : %s" % (s, mp.nstr(fe_residual(s, kappa), 6)))
    if abs(kappa - mpf("0.284079")) > mpf("5e-7"):
        say("INSTRUMENT RED: derived kappa disagrees with printed anchor -> outcome (d).")
        finish(lines, kappa)
        return

    # ---- S2: real-axis sign scan, sigma in (1,12) ----
    sig_lo, sig_hi, dsg = mpf("1.001"), mpf(12), mpf("0.002")
    npts = int((sig_hi - sig_lo) / dsg) + 1
    worst_im = mpf(0)
    real_zeros = []
    prev_s, prev_v = None, None
    for i in range(npts):
        sg = sig_lo + dsg * i
        v = f(sg, kappa)
        worst_im = max(worst_im, abs(v.imag))
        if prev_v is not None and prev_v.real * v.real < 0:
            lo, hi = prev_s, sg
            flo = prev_v.real
            for _ in range(120):  # bisection with margin
                mid = (lo + hi) / 2
                fm = f(mid, kappa).real
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fm
                if hi - lo < mpf("1e-18"):
                    break
            z = (lo + hi) / 2
            real_zeros.append(z)
            say("REAL ZERO sigma* = %s   |f| = %s" % (
                mp.nstr(z, 18), mp.nstr(abs(f(z, kappa)), 6)))
        prev_s, prev_v = sg, v
    say("real-axis scan: %d points, worst |Im f| on axis = %s (must be ~0)" % (
        npts, mp.nstr(worst_im, 6)))
    if worst_im > mpf("1e-18"):
        say("INSTRUMENT RED: f(sigma) not real -> outcome (d).")
        finish(lines, kappa)
        return

    # ---- S3: winding census, sigma (1,2) x t (0,8), two steps ----
    def census(step):
        # cell-centred grid: strictly inside the OPEN region (1,2)x(0,8) as pre-registered.
        # (A grid edge at sigma=1 exactly lands on the Hurwitz pole s=1: the exact
        #  sum-chi(a)=0 cancellation cannot survive numeric overflow there -> nan phase.)
        sig_vals = [mpf(1) + step / 2 + step * i for i in range(int(1 / step))]
        t_vals = [step / 2 + step * j for j in range(int(8 / step))]
        grid = {}
        for sg in sig_vals:
            for tv in t_vals:
                grid[(sg, tv)] = f(mpc(sg, tv), kappa)
        hits = []
        for i in range(len(sig_vals) - 1):
            for j in range(len(t_vals) - 1):
                p1 = grid[(sig_vals[i], t_vals[j])]
                p2 = grid[(sig_vals[i + 1], t_vals[j])]
                p3 = grid[(sig_vals[i + 1], t_vals[j + 1])]
                p4 = grid[(sig_vals[i], t_vals[j + 1])]
                wind = 0
                for (u, v) in ((p1, p2), (p2, p3), (p3, p4), (p4, p1)):
                    wind += phase(v / u)
                n = int(mp.nint(wind / (2 * mpi)))
                if n != 0:
                    hits.append(((sig_vals[i], t_vals[j]), step, n))
        return hits

    say("census step 0.05 ...", )
    h_coarse = census(mpf("0.05"))
    say("  coarse hits: %d cells" % len(h_coarse))
    say("census step 0.025 ...")
    h_fine = census(mpf("0.025"))
    say("  fine hits: %d cells" % len(h_fine))
    tot_coarse = sum(abs(n) for (_, _, n) in h_coarse)
    tot_fine = sum(abs(n) for (_, _, n) in h_fine)
    say("total winding count coarse = %d, fine = %d" % (tot_coarse, tot_fine))
    if tot_coarse != tot_fine:
        say("INSTRUMENT RED: step-refinement disagreement -> outcome (d).")
        finish(lines, kappa)
        return

    # Newton-refine one zero per coarse hit cell (centre start)
    zeros = []
    for ((sg, tv), step, n) in h_coarse:
        x0 = mpc(sg + step / 2, tv + step / 2)
        try:
            z = findroot(lambda w: f(w, kappa), (x0, x0 + step / 10))
        except Exception as exc:  # noqa: BLE001
            say("  refine FAILED at cell (%s,%s): %s" % (sg, tv, exc))
            continue
        in_cell = (sg - 0.1 <= z.real <= sg + step + 0.1) and (tv - 0.1 <= z.imag <= tv + step + 0.1)
        if abs(in_cell) and abs(f(z, kappa)) < mpf("1e-20"):
            zeros.append(z)
        else:
            say("  refined point rejected (outside cell or residual): %s  |f|=%s" % (
                mp.nstr(z, 16), mp.nstr(abs(f(z, kappa)), 6)))
    # dedupe
    uniq = []
    for z in zeros:
        if not any(abs(z - u) < mpf("1e-8") for u in uniq):
            uniq.append(z)
    say("located complex zeros (deduped): %d" % len(uniq))
    lnN = mlog(10 ** 4)
    for z in sorted(uniq, key=lambda w: abs(w)):
        s0 = z.real
        bound = mp.sqrt((2 * s0 - 1) * lnN / C_floor)
        vis = "VISIBLE at N=1e4" if abs(z) < bound else "invisible at N=1e4"
        say("  zero s0 = %s   |s0| = %s   boundary = %s   %s   |f| = %s" % (
            mp.nstr(z, 18), mp.nstr(abs(z), 10), mp.nstr(bound, 10), vis,
            mp.nstr(abs(f(z, kappa)), 6)))
    for z in real_zeros:
        bound = mp.sqrt((2 * z - 1) * lnN / C_floor)
        say("  REAL zero sigma* = %s  |s0| = %s  boundary = %s  %s" % (
            mp.nstr(z, 18), mp.nstr(z, 10), mp.nstr(bound, 10),
            "VISIBLE at every N>=2 (maximal rescue)" if z < bound else "check boundary"))
    # ---- outcome dispatch (pre-stated) ----
    vis_real = [z for z in real_zeros if 1 < z < 2]
    vis_cplx = [z for z in uniq
                if z.real > 1 and abs(z) < mp.sqrt((2 * z.real - 1) * lnN / C_floor)]
    if vis_real:
        say("OUTCOME (a): maximal-rescue real target exists -> transfer request to m2; "
            "NO distance run before their Lemma-5-analogue lands.")
    elif vis_cplx:
        say("OUTCOME (b): complex target under the visibility boundary -> transfer request "
            "to m2; NO distance run before their Lemma-5-analogue lands.")
    else:
        say("OUTCOME (c): no D-H zeros in the floor-gate-satisfiable region -> D-H arm DEAD; "
            "Epstein floor check carries the arm; ledger update follows.")
    finish(lines, kappa)


def finish(lines, kappa):
    if kappa is not None:
        dq = ("DQ-SECTION: FE-derived kappa (two generic s, dps 30, agreement <1e-20; "
              "printed-anchor match to 5e-7); real-axis worst |Im f| stated; winding census "
              "double-step agreement forced (red otherwise); Newton residuals < 1e-20 or "
              "rejected. FAILURE MODES guarded: wrong FE shape -> kappa inconsistency; "
              "hand-copied constants -> none used (derivation + parsed prints only); "
              "step-aliasing of phase -> 0.05/0.025 count equality. NOT CERTIFIED here: "
              "existence of a D-H-family basis with the annihilation property (m2's owed "
              "Lemma-5-analogue) — this census locates targets only and schedules no "
              "distance run.")
        lines.append(dq)
        print(dq)
    with open(os.path.join(SCRIPT_DIR, "heat65_dh_census.out"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
