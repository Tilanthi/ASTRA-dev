#!/usr/bin/env python3
"""heat86b -- the a-dispute ladder (m1-L171), re-freeze after heat86 went RED on a control.

WHY heat86b EXISTS: heat86 (frozen 2708650, runner 775b34cc) went RED at gate BG4
BEFORE any rung was computed: its control injected +5e-15 into r formed over the
17 rungs (11 published u + m2's six xi_D u) and demanded the fitted eps^-2 coeff
land in [-6e-15, -4e-15].  It returned -6.63339e-15 = -(5e-15 + 1.63339e-15): the
fitter recovered the injection ADDITIVELY on top of the eps^-2 signature the six
xi_D u values themselves carry (my own refit had already measured that data at
c0 = -1.633394698e-15).  The control's PASS band had assumed that data is clean at
c0 = 0 -- which assumes MY side of the dispute as the control's baseline.  A
control that presumes the conclusion under test cannot gate the measurement.
Nothing was measured (DQ fired before any rung); the RED is published verbatim
(heat86b_red_disclosure_of_heat86.out + the results JSON in the exchange).

THE ONLY CHANGE FROM heat86: gate BG4 is replaced by BG4v2, a KNOWN-BASELINE
synthetic control -- synthetic u generated from the law with r = K6-poly + c_inj/eps^2,
c_inj = -5e-15, at the SAME 17 eps, refit through the SAME measurement path; PASS
iff the fitted c0 lands in [-6e-15, -4e-15].  The old real-data injection is kept
as BG4c, REPORTED NOT GRADED (a linearity calibration: it should return
-(5e-15 + c0_data) whatever c0_data is).  Every gate that passed in heat86
(BG1, BG2, BG3) is unchanged; the rungs, fits, V1 bands and worthlessness
conditions are unchanged.  This is a stricter gate on a known baseline, not a
weakened one (#119 discipline: nothing was retired mid-flight; the failed gate
was a control whose band was ill-posed, and its replacement has a firing world
by construction).

m2-c30 section 4.6 ask, unchanged: "m1 computes u(eps) on his own heat72x lineage
at the same six eps below 1e-3 and reports the coefficient of eps^-2 in the same
fit."  Their claim: a_true - a_operative = -1.633e-15, i.e. m1-L164 sect5's
19-s.f. republication of a moved the constant the wrong way.

Frozen prereg: Riemann_exchange/data/machine1_heat86b_prereg.json (hashed and
committed BEFORE this run started; the commit is the timestamp).

Instrument: the SCORED heat72 runner imported byte-identical (2-D Newton on
(Re F, Im F), zeta2_C Chowla-Selberg family, D = DSTAR + eps).  Nothing about the
kernel path changes.  Battery: scored battery's B1a/B1b anchors, m2's G4 b-drop
injection, BG4v2 synthetic fit-power control, BG5 determinism.
"""
import hashlib
import json
import os
import time

import importlib.util
from mpmath import mp, mpf, mpc, sqrt

T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "heat72_birth_locus.py")

spec = importlib.util.spec_from_file_location("h72", RUNNER)
h72 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h72)

A_USED = mpf("2.645521411811664489")
B_OP = mpf("-7.4624528767937415788")
DSTAR = h72.DSTAR

# m1-L165 sect9a published column (heat72x republication, native dps 50)
L165_9A = [
    ("0.001",              "0.05150723818940063653522997138655916611777128352831"),
    ("0.0011239031932557", "0.054614584740162860829271236079197856379810987308508"),
    ("0.002",              "0.072945092837465636911527414020464645263120485246671"),
    ("0.0035",             "0.09670183421043065840984313002276196906002275045949"),
    ("0.006",              "0.12706034318675893153656817913317280690430806327895"),
    ("0.0082667603361",    "0.14962144595780802891341103521644637411107076093496"),
    ("0.012",              "0.18122223459720552038513232631511513662541625076064"),
    ("0.02",               "0.23662703502895471893639804350283991882970959834519"),
    ("0.035",              "0.31979403084190422618229559433082050463362878645843"),
    ("0.06",               "0.43405746526370626569197604987746105430711695666647"),
    ("0.1",                "0.59427921830513711248148784269207030531776649353816"),
]
NEW_EPS = ["0.0001", "0.00015", "0.00022", "0.00033", "0.0005", "0.00075"]
# m2's published xi_D u values (c30 scored JSON) -- SECONDARY comparison only
M2_U = {
    "0.0001": "0.01626735311637081543652166235648198533749",
    "0.00015": "0.01992476239411063527334232617346140282631",
    "0.00022": "0.02413246812812595998486983709533875808145",
    "0.00033": "0.02956070276139769356253217112920061589147",
    "0.0005": "0.03639543629351059261305814257433460217533",
    "0.00075": "0.04459084694558961727534415865200776265643",
}

RESULTS = {"runner_sha256_72": hashlib.sha256(open(RUNNER, "rb").read()).hexdigest(),
           "runner_sha256_86": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()}


def n(v, d=8):
    return mp.nstr(v, d)


def r_of(eps, u, a=A_USED, b=B_OP):
    return (u * u - a * eps + b * eps ** 2) / eps ** 3


# ---------------- frozen fitter (pinned: mpmath qr_solve, dps 60) ----------------
mp.dps = 60


def lsq(basis, xs, ys):
    ncol = len(basis)
    Am = mp.matrix(len(xs), ncol)
    bv = mp.matrix(len(xs), 1)
    for i, (x, y) in enumerate(zip(xs, ys)):
        for j, f in enumerate(basis):
            Am[i, j] = f(x)
        bv[i] = y
    c, _ = mp.qr_solve(Am, bv)
    return [c[j] for j in range(ncol)]


def evalfit(basis, c, x):
    return mp.fsum(f(x) * cj for f, cj in zip(basis, c))


def poly_basis(K):
    return [(lambda j: (lambda e: e ** j))(j) for j in range(K + 1)]


# ---------------- battery ----------------
def battery(c11_6):
    print("=== BATTERY ===", flush=True)
    ok = True
    for tag, Dv, y_ref in [("BG1 y(1/7)", mpf(1) / mpf(7), mpf("0.054614584740162026")),
                           ("BG2 y(0.15)", mpf("0.15"), mpf("0.149621445957926652"))]:
        mp.dps = 50
        d = Dv - DSTAR
        got = None
        for w in (mpf("0.7"), mpf(1), mpf("1.3")):
            z, _, rr, _ = h72.locate_zero(mpf("0.5"), sqrt(A_USED * d) * w, Dv)
            if z is not None and rr < h72.NEWTON_FLOOR:
                got = z
                break
        if got is None:
            print("%s: FAILED" % tag, flush=True)
            ok = False
            continue
        dev = abs(got.imag - y_ref)
        verdict = dev < mpf("5e-16")
        ok = ok and verdict
        print("%s: t0=%s dev=%s %s" % (tag, n(got.imag, 18), n(dev, 3),
                                       "PASS" if verdict else "FAIL"), flush=True)

    # BG3: r-path defect injection at eps=0.0001 (m2's G4 adopted)
    mp.dps = 60
    e = mpf("0.0001")
    u1 = mpf(M2_U["0.0001"])  # any accurate u; the control is on the r PATH
    r_clean = r_of(e, u1)
    r_drop = (u1 * u1 - A_USED * e) / e ** 3
    move = abs(r_drop - r_clean) / abs(r_clean)
    verdict = move > mpf("1e3")
    ok = ok and verdict
    print("BG3 b-term drop: rel move = %s %s" % (n(move, 8), "PASS" if verdict else "FAIL"),
          flush=True)

    # BG5 determinism is folded into the rung loop (re-solve rung 1 from x0.7)
    return ok, c11_6


# ---------------- rungs ----------------
def solve_rung(es, c11_6, alt_seed=None):
    """Returns (u, recheck_drift, recheck_resid, n_zeros_found)."""
    mp.dps = 50
    e = mpf(es)
    D = DSTAR + e
    t0 = time.time()
    # law + model seeds
    r_pred = evalfit(poly_basis(6), c11_6, e)
    u_model = sqrt((A_USED - B_OP * e) * e + r_pred * e ** 3)
    seeds = [u_model * w for w in (mpf("0.7"), mpf(1), mpf("1.3"))]
    if alt_seed is not None:
        seeds = [u_model * alt_seed]
    # scan for completeness (declared window [0.003, 0.08] h=0.001)
    ts, t, prev, cur = [], mpf("0.003"), None, None
    while t <= mpf("0.08"):
        v = abs(h72.F(mpc(mpf("0.5"), t), D))
        if prev is not None and cur is not None and cur[1] < prev[1] and cur[1] <= v:
            ts.append(cur[0])
        prev, cur = cur, (t, v)
        t += mpf("0.001")
    seeds += ts
    zeros = []
    for tc in seeds:
        z, _, rr, _ = h72.locate_zero(mpf("0.5"), tc, D)
        if z is not None and rr < h72.NEWTON_FLOOR:
            zeros.append(z)
    zeros = h72.dedupe(sorted(zeros, key=lambda w: w.imag))
    firsts = [z for z in zeros if abs(z.real - mpf("0.5")) < h72.ONLINE_TOL]
    if not firsts:
        return None, None, None, len(zeros), time.time() - t0
    u = firsts[0].imag
    # dps-65 recheck, fresh Newton from the converged point
    zr, _, rr, _ = h72.locate_zero(mpf("0.5"), u, D, dps=65)
    drift = abs(zr.imag - u) if zr is not None else mpf("inf")
    mp.dps = 60
    return u, drift, rr, len(zeros), time.time() - t0


def main():
    sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    print("heat86b a-dispute ladder (prereg machine1_heat86b_prereg.json, re-freeze after "
          "heat86 RED at BG4; frozen in the exchange before this run)", flush=True)
    print("runner sha256:", sha, flush=True)
    print("START %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), flush=True)

    # 11-rung constants-consistent K=6 fit (model seeds + BG4's baseline)
    E11 = [mpf(e) for e, _ in L165_9A]
    U11 = [mpf(u) for _, u in L165_9A]
    R11 = [r_of(e, u) for e, u in zip(E11, U11)]
    c11_6 = lsq(poly_basis(6), E11, R11)

    ok, c11_6 = battery(c11_6)

    # BG4v2 fit-power positive control, KNOWN BASELINE (the only change from heat86):
    # synthetic u from the law with r = K6-poly(11-published fit) + c_inj/eps^2 at the
    # SAME 17 eps, pushed through the SAME measurement path (u -> r -> fit).  The
    # baseline is known by construction (a polynomial has no eps^-2 component), so the
    # gate does not presume either side of the dispute.
    inj = mpf("-5e-15")
    E17c = [mpf(e) for e in NEW_EPS] + E11
    R17s = [evalfit(poly_basis(6), c11_6, e) + inj / e ** 2 for e in E17c]
    U17s = [sqrt((A_USED - B_OP * e) * e + r * e ** 3) for e, r in zip(E17c, R17s)]
    R17b = [r_of(e, u) for e, u in zip(E17c, U17s)]
    c_inj = lsq(poly_basis(6) + [lambda e: 1 / e ** 2], E17c, R17b)[7]
    verdict = mpf("-6e-15") <= c_inj <= mpf("-4e-15")
    ok = ok and verdict
    print("BG4v2 fit-power (synthetic, known baseline): injected -5e-15 -> fitted c0 = %s %s"
          % (n(c_inj, 8), "PASS" if verdict else "FAIL"), flush=True)

    # BG4c: heat86's real-data injection, REPORTED NOT GRADED -- a linearity
    # calibration.  Whatever eps^-2 coefficient the real 17-rung data carries
    # (c0_data), the injected +5e-15 must return -(5e-15 + c0_data) if the fitter
    # is additive in this channel.
    E17r = [mpf(e) for e in NEW_EPS] + E11
    U17r = [mpf(M2_U[es]) for es in NEW_EPS] + U11
    R17p = [r_of(e, u, a=A_USED + mpf("5e-15")) for e, u in zip(E17r, U17r)]
    c_bg4c = lsq(poly_basis(6) + [lambda e: 1 / e ** 2], E17r, R17p)[7]
    c0_data = lsq(poly_basis(6) + [lambda e: 1 / e ** 2], E17r,
                  [r_of(e, u) for e, u in zip(E17r, U17r)])[7]
    print("BG4c linearity (reported, not graded): real-data c0 = %s ; +5e-15 injection -> %s "
          "(additivity residual %s)" % (n(c0_data, 8), n(c_bg4c, 8),
                                        n(c_bg4c - (c0_data - mpf("5e-15")), 3)), flush=True)
    RESULTS["bg4c_calibration"] = {"c0_data": n(c0_data, 12),
                                   "c0_with_plus5e-15": n(c_bg4c, 12)}
    print("BATTERY: %s" % ("PASS" if ok else "FAIL"), flush=True)
    if not ok:
        print("DQ: battery failure -- run RED, nothing measured.", flush=True)
        RESULTS["outcome"] = "RED"
        json.dump(RESULTS, open(os.path.join(HERE, "heat86b_a_dispute_ladder.results.json"), "w"), indent=1)
        return

    rungs = {}
    for i, es in enumerate(NEW_EPS):
        u, drift, rr, nz, dt = solve_rung(es, c11_6)
        print("  eps=%-8s u=%s  drift65=%s  resid65=%s  zeros=%d  (%.0fs)"
              % (es, n(u, 30), n(drift, 3), n(rr, 3), nz, dt), flush=True)
        rungs[es] = {"u": n(u, 50), "drift65": n(drift, 4), "resid65": n(rr, 4),
                     "zeros_found": nz}
        if u is None or drift > mpf("1e-30"):
            print("DQ: rung %s failed recheck -- run RED." % es, flush=True)
            RESULTS["outcome"] = "RED"
            RESULTS["rungs"] = rungs
            json.dump(RESULTS, open(os.path.join(HERE, "heat86b_a_dispute_ladder.results.json"), "w"), indent=1)
            return
    # BG5 determinism on rung 1
    u_alt, d_alt, _, _, _ = solve_rung("0.0001", c11_6, alt_seed=mpf("0.7"))
    bg5 = u_alt is not None and abs(u_alt - mpf(rungs["0.0001"]["u"])) < mpf("1e-35")
    print("BG5 determinism: drift=%s %s" % (n(abs(u_alt - mpf(rungs["0.0001"]["u"])), 3),
                                            "PASS" if bg5 else "FAIL"), flush=True)
    if not bg5:
        RESULTS.update({"outcome": "RED", "rungs": rungs})
        json.dump(RESULTS, open(os.path.join(HERE, "heat86b_a_dispute_ladder.results.json"), "w"), indent=1)
        return

    # ---------------- primary + secondary fits ----------------
    print("\n=== V1 PRIMARY: 17-rung K=6 poly + eps^-2 ===", flush=True)
    E17 = [mpf(e) for e in NEW_EPS] + E11
    U17 = [mpf(rungs[es]["u"]) for es in NEW_EPS] + U11
    R17 = [r_of(e, u) for e, u in zip(E17, U17)]
    bas = poly_basis(6) + [lambda e: 1 / e ** 2]
    c = lsq(bas, E17, R17)
    mr = max(abs(evalfit(bas, c, x) - y) for x, y in zip(E17, R17))
    c0 = c[7]
    print("  c0 = %s   max res = %s" % (n(c0, 12), n(mr, 9)), flush=True)
    band = ("m2-CONFIRMED" if mpf("-2.2e-15") <= c0 <= mpf("-1.0e-15")
            else ("MINE-STANDS" if abs(c0) <= mpf("3e-16") else "OPEN"))
    print("  band: %s" % band, flush=True)

    print("\n=== SECONDARY ===", flush=True)
    E6 = [mpf(e) for e in NEW_EPS]
    U6 = [mpf(rungs[es]["u"]) for es in NEW_EPS]
    R6 = [r_of(e, u) for e, u in zip(E6, U6)]
    bas6 = [lambda e: 1 / e ** 2] + poly_basis(3)
    c6 = lsq(bas6, E6, R6)
    mr6 = max(abs(evalfit(bas6, c6, x) - y) for x, y in zip(E6, R6))
    print("  six new alone: c0 = %s  a3 = %s  max res = %s"
          % (n(c6[0], 10), n(c6[1], 20), n(mr6, 9)), flush=True)

    print("  per-rung rel u-diff vs m2 xi_D:", flush=True)
    for es in NEW_EPS:
        du = abs(mpf(rungs[es]["u"]) - mpf(M2_U[es])) / mpf(M2_U[es])
        print("    eps=%-8s rel = %s" % (es, n(du, 6)), flush=True)

    print("  power table (K=6 + one extra, my 17 rungs):", flush=True)
    for tag, ex in (("none", []), ("eps^-1", [lambda e: 1 / e]),
                    ("eps^-2", [lambda e: 1 / e ** 2]),
                    ("eps^-3", [lambda e: 1 / e ** 3]),
                    ("eps^-3/2", [lambda e: 1 / (e * sqrt(e))])):
        cc = lsq(poly_basis(6) + ex, E17, R17)
        mrx = max(abs(evalfit(poly_basis(6) + ex, cc, x) - y) for x, y in zip(E17, R17))
        tail = (" coeff %s" % n(cc[7], 9)) if ex else ""
        print("    %-8s max res = %s%s" % (tag, n(mrx, 9), tail), flush=True)

    # decisive refit with a_used + c0
    a_fix = A_USED + c0
    Rf = [r_of(e, u, a=a_fix) for e, u in zip(E17, U17)]
    print("  decisive refit a = %s:" % n(a_fix, 20), flush=True)
    for K in (5, 6, 7, 8):
        cf = lsq(poly_basis(K), E17, Rf)
        mrf = max(abs(evalfit(poly_basis(K), cf, x) - y) for x, y in zip(E17, Rf))
        print("    K=%d max res %s  a3 %s" % (K, n(mrf, 9), n(cf[0], 19)), flush=True)

    RESULTS.update({"outcome": "GREEN", "rungs": rungs,
                    "V1": {"c0": n(c0, 15), "max_res": n(mr, 10), "band": band,
                           "a_fix": n(a_fix, 22)},
                    "six_alone": {"c0": n(c6[0], 12), "a3": n(c6[1], 21),
                                  "max_res": n(mr6, 10)},
                    "bg4_fitted_c0_on_injection": n(c_inj, 8),
                    "u_diff_vs_m2": {es: n(abs(mpf(rungs[es]["u"]) - mpf(M2_U[es]))
                                            / mpf(M2_U[es]), 6) for es in NEW_EPS}})
    json.dump(RESULTS, open(os.path.join(HERE, "heat86b_a_dispute_ladder.results.json"), "w"),
              indent=1)
    print("\nEND %s  total %.0fs" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                     time.time() - T0), flush=True)


if __name__ == "__main__":
    main()
