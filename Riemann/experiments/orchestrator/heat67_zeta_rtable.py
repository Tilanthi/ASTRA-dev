#!/usr/bin/env python3
"""heat67 — zeta-side R/q population table (joint experiment, Letter 61 division).

PRE-REGISTERED in machine1-prereg-heat67-zeta-rtable.md (exchange commit 7847b6c,
pushed BEFORE this script was written). Statistic = m3's measure_R (Letter 57 /
curve_population_run.py), zeta-side substitution: spectrum = consecutive zeta zeros
(t-space), g_poly -> xi(1/2 + i t). B = -2*k2, R = -4*k4/B^2, q = B*d^2/2 (all
scale-invariant). Two arms: PRIMARY W=8 (7 gaps = m3's g=4 selection intensity),
SECONDARY W=30 (29 gaps, reported separately). 12 windows, n = 1e3..5e6 log-spaced.

Registered guards, per row: taylor@dps60 vs taylor@dps70 vs explicit two-step
Richardson FD @dps90 must agree >= 20 significant digits on k2, k4 (epsilon-law guard);
k1,k3 != 0 (degeneracy check); zeros at dps 50 (A3); module-level dps management only
(#73); time budget 20 min/window -> DQ skip. DQ-SECTION written by this runner (R3/R6).
"""
import json
import os
import time

from mpmath import mp, mpf, mpc, log as mlog, pi as mpi, gamma as mgamma, \
    zeta as mzeta, zetazero, taylor as mtaylor, nstr, absmax  # noqa: F401

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
mp.dps = 50  # module-level only (#73); zero location at 50, measurement at 60/70/90

N_ANCHORS = [10**3, 2 * 10**3, 5 * 10**3, 10**4, 2 * 10**4, 5 * 10**4,
             10**5, 2 * 10**5, 5 * 10**5, 10**6, 2 * 10**6, 5 * 10**6]
W_SEC = 30
W_PRI = 8
CURVE_RANGE = (mpf("0.346"), mpf("0.608"))  # m3's 10 non-degenerate points, Letter 62


def xi(s):
    return (s * (s - 1) / 2) * mpi ** (-s / 2) * mgamma(s / 2) * mzeta(s)


def make_f(m0, d):
    def f(z):
        s = mpc("0.5") + 1j * (m0 + z)
        return mlog(xi(s) / (z**2 - d**2))
    return f


def measure(zeros):
    """m3's measure_R on a sorted window of t-zeros. Returns dict or raises."""
    gaps = [(zeros[i + 1] - zeros[i], i) for i in range(len(zeros) - 1)]
    gap, i = min(gaps)
    g1, g2 = zeros[i], zeros[i + 1]
    d = (g2 - g1) / 2
    m0 = (g1 + g2) / 2
    f = make_f(m0, d)
    mp.dps = 60
    c60 = mtaylor(f, 0, 4)
    with mp.workdps(70):
        c70 = mtaylor(f, 0, 4)
    # independent FD path at dps 90 (Richardson, two steps), k2 and k4 only.
    # h chosen by magnitude arithmetic (#70 clause 2 applied to the step): f ~ O(pi*t/4)
    # ~ 2e6 at the top window, so per-eval abs error at dps 90 is ~2e-84; h=1e-13 keeps
    # the 4th-derivative cancellation floor >= ~30 digits on k4 (h=1e-15 would leave
    # only ~3 digits of margin over the 20-digit gate). All comparisons stay in mpmath
    # -- a complex() cast would truncate to double precision and fail every row.
    with mp.workdps(90):
        h = mpf("1e-13")
        def d2(hh):
            return (f(hh) - 2 * f(0) + f(-hh)) / (2 * hh**2)
        def d4(hh):
            return (f(2*hh) - 4*f(hh) + 6*f(0) - 4*f(-hh) + f(-2*hh)) / (24 * hh**4)
        k2_fd = (4 * d2(h/2) - d2(h)) / 3
        k4_fd = (4 * d4(h/2) - d4(h)) / 3
    k1, k2, k3, k4 = c60[1], c60[2], c60[3], c60[4]
    def rel(a, b):
        return abs(a - b) / max(abs(a), abs(b))
    agree = max(rel(k2, c70[2]), rel(k4, c70[4]), rel(k2, k2_fd), rel(k4, k4_fd))
    B = -2 * k2
    R = -4 * k4 / B**2
    q = B * d**2 / 2
    return dict(gap=gap, d=d, m0=m0, k1=k1, B=B, k3=k3, k4=k4, R=R, q=q, agree=agree)


def main():
    lines = []

    def say(t):
        print(t, flush=True)
        lines.append(t)

    say("heat67 zeta-side R/q table (prereg 7847b6c). arms: primary W=%d, secondary W=%d"
        % (W_PRI, W_SEC))
    rows = []
    dq_rows = []
    for n in N_ANCHORS:
        t0 = time.time()
        try:
            zs = sorted(mp.im(zetazero(k)) for k in range(n, n + W_SEC))
            assert all(zs[i + 1] > zs[i] for i in range(len(zs) - 1))
        except Exception as exc:  # noqa: BLE001
            say("DQ window n=%d: zero-location failure: %s" % (n, exc))
            dq_rows.append(("locate", n, str(exc)))
            continue
        if time.time() - t0 > 1200:
            say("DQ window n=%d: zero-location exceeded time budget" % n)
            dq_rows.append(("budget", n, ""))
            continue
        for arm, W in (("pri", W_PRI), ("sec", W_SEC)):
            try:
                m = measure(zs[:W])
            except Exception as exc:  # noqa: BLE001
                say("DQ window n=%d arm=%s: measurement failure: %s" % (n, arm, exc))
                dq_rows.append(("measure", n, arm, str(exc)))
                continue
            ok_agree = m["agree"] < mpf("1e-20")
            ok_degen = abs(m["k1"]) > mpf("1e-15") and abs(m["k3"]) > mpf("1e-15")
            status = "OK" if (ok_agree and ok_degen) else "DQ"
            if status == "DQ":
                dq_rows.append(("guards", n, arm,
                                "agree=%s k1=%s k3=%s" % (nstr(m["agree"], 4),
                                                          nstr(abs(m["k1"]), 4),
                                                          nstr(abs(m["k3"]), 4))))
            say("n=%8d t~%s arm=%s d=%s R=%s q=%s k1=%s %s agree=%s [%s]" % (
                n, nstr(m["m0"], 8), arm, nstr(m["d"], 8), nstr(m["R"], 8),
                nstr(m["q"], 6), nstr(abs(m["k1"]), 4), status,
                nstr(m["agree"], 3), time.strftime("%H:%M:%S")))
            rows.append(dict(n=n, arm=arm, d=nstr(m["d"], 20), m0=nstr(m["m0"], 20),
                             R=nstr(m["R"], 20), q=nstr(m["q"], 20), status=status))
        mp.dps = 50
    # population summary, PRIMARY arm
    pri = [r for r in rows if r["arm"] == "pri" and r["status"] == "OK"]
    sec = [r for r in rows if r["arm"] == "sec" and r["status"] == "OK"]
    def summarize(tag, rs):
        if not rs:
            say("%s: no OK rows" % tag)
            return None, 0
        Rs = sorted(mpf(r["R"]) for r in rs)
        med = Rs[len(Rs)//2] if len(Rs) % 2 else (Rs[len(Rs)//2 - 1] + Rs[len(Rs)//2]) / 2
        inrange = sum(1 for x in Rs if CURVE_RANGE[0] <= x <= CURVE_RANGE[1])
        say("%s: n_ok=%d median R=%s min=%s max=%s  in-curve-range %d/%d" % (
            tag, len(Rs), nstr(med, 8), nstr(Rs[0], 8), nstr(Rs[-1], 8), inrange, len(Rs)))
        return med, inrange
    med_pri, in_pri = summarize("PRIMARY W=8", pri)
    summarize("SECONDARY W=30", sec)
    if med_pri is None:
        say("OUTCOME (d): no scored primary rows -> instrument red, defect letter.")
    elif CURVE_RANGE[0] <= med_pri <= CURVE_RANGE[1] and in_pri >= 8:
        say("OUTCOME (a): zeta primary median inside curve range with >=8/12 windows in "
            "range -> R-universality-in-range SURVIVES population test; synthesis follows.")
    elif CURVE_RANGE[0] <= med_pri <= CURVE_RANGE[1]:
        say("OUTCOME (b): median inside but <%d windows in range -> AMBIGUOUS; "
            "higher-genus OPEN lane is the tiebreaker." % 8)
    else:
        say("OUTCOME (c): median OUTSIDE curve range -> R-universality-in-range DIES; "
            "L57 n=1 agreement reclassified coincidence.")
    dq = ("DQ-SECTION: guards per row (registered): taylor@dps60 vs @dps70 vs two-step "
          "Richardson FD@dps90 (h=1e-13, h/2; step chosen by #70 clause 2 magnitude "
          "arithmetic -- f ~ O(pi t/4), per-eval abs err ~2e-84 at dps 90) "
          "(epsilon-law guard; conviction D1 stays retired); k1,k3 != 0 degeneracy check "
          "(no zeta-side forced-identity expected, checked not assumed); zeros dps 50 "
          "mpmath zetazero, sorted+strictly-increasing assert; windows anchored at the "
          "registered n list, W=8 primary / W=30 secondary from the SAME located 30 zeros "
          "(secondary superset of primary by construction — arms never pooled). FAILURE "
          "MODES: time-budget skip (none expected; zetazero ~0.6s/zero at n=5e6); branch "
          "cut in log xi near a zero of the divided argument (would surface as taylor/FD "
          "disagreement, not silently). CERTIFIED: population comparison only. NOT "
          "CERTIFIED: anything about RH; R-universality as a theorem.")
    say(dq)
    out = dict(rows=rows, dq=[list(map(str, d)) for d in dq_rows])
    with open(os.path.join(SCRIPT_DIR, "heat67_zeta_rtable.out"), "w") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n" + "\n".join(lines) + "\n" + dq + "\n")


if __name__ == "__main__":
    main()
