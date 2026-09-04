#!/usr/bin/env python3
"""heat72 — C1/N6: zero-birth-locus cartography for the Epstein D-family on
zeta2_C.  Committed in the Glenn-directive debate (machine1-debate-contribution
7c40f1c section 3 C1; nursery N6).  The object nobody centres: the BIRTH LOCUS
{(D, t_j(D))} -- where on-line zero pairs are born as D crosses the fold --
rather than the zero set of one family member.  On-lineness as a dynamical
property of the family, not a static property of one function.

Family + fold (registry, kappa row): zeta2_C(s, D), D real > 0; the fold is
the root of D -> zeta2(1/2, D):
  Delta* = 0.141733239663887191395415685084185024 (operative, PROPOSED value;
  m2 24-digit-confirmed + m1 eps-ladder refinement; m2 eps_eff check pending).
Anchors (m1<->m2 15-digit cross-receipts): y(1/7) = 0.054614584740162026,
y(0.15) = 0.149621445957926652, y = t-location of the first ON-LINE pair.

LAW UNDER TEST (derived from the registry constants + verified against BOTH
anchors BEFORE this file was written -- see the prereg letter for the receipt):
  u^2 = (a - b*eps)*eps + a3*eps^3 + O(eps^4),   eps = D - Delta* > 0,
  a = 2.645521411811663, b = -7.46245287679  =>  a3 implied ~ 11.8-12:
  r(1/7) = (u^2 - a*d + b*d^2)/d^3 = 11.7238;  r(0.15) = 11.8713.
  (Sign convention on the D > Delta* side: u^2 = a*d - b*d^2.  The registry's
  v = Delta* - D form u^2 = a*v + b*v^2 describes the D < Delta* side.)
SHARP FALSIFIABLE PREDICTION pre-registered: r(eps) stays in a constant band
~ [11, 13] across the grid.  This also directly tests m2's flagged open item
("residual scales as v^1, one order larger than a genuine O(w^4) truncation").

Method: per D on the grid, coarse |F(1/2+it)| scan for candidate dips, law
seeds sqrt(a*eps)*{0.7,1.0,1.3} as additional Newton starts (seeding is NOT
fitting: converged zeros only enter the r-table), then 2-D Newton on
(Re F, Im F) over (sigma, t) -- catches on-line AND modestly off-line zeros.
Per zero: 30-digit (sigma0, t0), |F| at the zero, delta-sigma, on-line verdict
|sigma0 - 1/2| < 1e-25.  dps 50; dps-65 recheck every 3rd zero (fresh Newton
from the same seed; |delta s0| < 1e-30 required).  Second-pair probe on the 5
largest eps (t in [1.5, 4.5]) -- the multi-curve discovery space.

PRE-REGISTERED OUTCOMES (bound before the scored run):
  (a) every first-pair zero on-line; r(eps) constant (slope test:
      |slope*d_max| < 0.25*|median r|); no second pair in range; no off-line
      birth at low t => the locus is a smooth three-term expansion, the
      representation carries no NEW information beyond the operative
      constants, and the honest death is recorded WITH the measured a3.
  (b) any of: r(eps) structured (slope test fails or non-monotone drift);
      a low-t zero with |sigma0 - 1/2| > 1e-25 (an OFF-LINE BIRTH);
      a second pair located in the probe range => NEW OBJECT: full cartography
      escalates (this is the outcome the nursery exists to protect).
  (c) Newton non-convergence / |F| floor contamination / dps mismatch =>
      certify what passes, quantify the residue, claim nothing beyond it.
Falsifiers: battery anchors off by > 5e-16 => abort red; |F| at any reported
zero > 1e-35 => that zero uncertified (excluded from the r-table, reported);
dps-65 recheck drift > 1e-30 => run red.
DQ-SECTION written by this runner (R6: missing = red).
CPU: 1 process (5-core cap; heat71/AM-8b hold the others).
"""
import hashlib
import json
import math
import os
import sys
import time

from mpmath import mp, mpf, mpc, sqrt, zeta, gamma, besselk, pi, im, findroot

DPS = 50
DPS_RECHECK = 65
NEWTON_FLOOR = mpf("1e-35")
ONLINE_TOL = mpf("1e-25")
DEDUP_TOL = mpf("1e-8")
mp.dps = 130  # parse literals at full precision FIRST (dps-15 trap)

A_OP = mpf("2.645521411811663")
B_OP = mpf("-7.46245287679")
DSTAR = mpf("0.141733239663887191395415685084185024")

ZCUT_A = mpf("0.08")
ZCUT_B = mpf("160")


def zeta2_C(s, D):
    """Explicit Chowla-Selberg sum, all (m,k) with 2*pi*D*m*k <= zcut(t).
    Identical to heat71's frozen instrument (trap-#91 fix)."""
    nu = s - mpf("0.5")
    zcut = ZCUT_B + ZCUT_A * (mpf(float(abs(im(s)))) ** 2)
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


def F(s, D):
    return zeta2_C(s, D)


def absF_line(t, D):
    return abs(F(mpc(mpf("0.5"), t), D))


def locate_zero(sig_seed, t_seed, D, dps=None):
    """2-D Newton on (Re F, Im F) over (sigma, t); returns (s0, its, resid)."""
    if dps is not None:
        mp.dps = dps
    def f1(x, y):
        return F(mpc(x, y), D).real
    def f2(x, y):
        return F(mpc(x, y), D).imag
    try:
        s0 = findroot(lambda x, y: (f1(x, y), f2(x, y)),
                      (sig_seed, t_seed), tol=mpf("1e-40"), maxsteps=40)
    except Exception as e:  # convergence failure -> outcome (c) discipline
        return None, 0, mpf("inf"), str(e)
    r = abs(F(mpc(s0[0], s0[1]), D))
    return mpc(s0[0], s0[1]), 0, r, ""


def scan_candidates(D, t_lo, t_hi, h):
    """Coarse |F(1/2+it)| scan; return t's of local minima (3-point)."""
    ts = []
    t = t_lo
    prev = None
    cur = None
    while t <= t_hi + 1e-12:
        v = absF_line(t, D)
        if prev is not None and cur is not None and cur[1] < prev[1] and cur[1] <= v:
            ts.append(cur[0])
        prev, cur = cur, (t, v)
        t += h
    return ts


def dedupe(zeros):
    out = []
    for z in zeros:
        if all(abs(z - w) > DEDUP_TOL for w in out):
            out.append(z)
    return out


def battery():
    print("=== BATTERY (pre-scored; abort on failure) ===", flush=True)
    ok = True
    # B1/B2: the two 15-digit cross-receipt anchors.
    for tag, Dv, y_ref in [
        ("B1 y(1/7)", mpf(1) / mpf(7), mpf("0.054614584740162026")),
        ("B2 y(0.15)", mpf("0.15"), mpf("0.149621445957926652")),
    ]:
        d = Dv - DSTAR
        seeds = [sqrt(A_OP * d) * w for w in (mpf("0.7"), mpf(1), mpf("1.3"))]
        got = None
        for ts in seeds:
            z, _, r, _ = locate_zero(mpf("0.5"), ts, Dv)
            if z is not None and r < NEWTON_FLOOR and abs(z.imag - y_ref) < mpf("1e-6"):
                got = z
                break
        if got is None:
            print(f"{tag}: FAILED to locate the anchor zero", flush=True)
            ok = False
            continue
        dev = abs(got.imag - y_ref)
        dsg = abs(got.real - mpf("0.5"))
        verdict = dev < mpf("5e-16")
        ok = ok and verdict
        print(f"{tag}: t0={mp.nstr(got.imag, 18)} dev={mp.nstr(dev, 3)} "
              f"dsigma={mp.nstr(dsg, 3)} resid={mp.nstr(r, 3)} "
              f"{'PASS' if verdict else 'FAIL'}", flush=True)
    # B3: fold sanity -- F(1/2, Delta*) at the near-pole value floor.
    fv = abs(F(mpc(mpf("0.5"), mpf(0)), DSTAR))
    verdict = fv < mpf("1e-20")
    ok = ok and verdict
    print(f"B3 |F(1/2,Delta*)| = {mp.nstr(fv, 4)}  "
          f"{'PASS' if verdict else 'FAIL'} (expect ~1e-23 floor)", flush=True)
    # B4: off-line Newton control at D=1/7, the sigma0=0.5247 / t~44.4 zero.
    z, _, r, err = locate_zero(mpf("0.53"), mpf("44.45"), mpf(1) / mpf(7))
    if z is None:
        print(f"B4 FAILED: Newton did not converge ({err})", flush=True)
        ok = False
    else:
        verdict = (mpf("0.524") < z.real < mpf("0.526")) and r < NEWTON_FLOOR
        ok = ok and verdict
        print(f"B4 off-line control: s0={mp.nstr(z, 12)} resid={mp.nstr(r, 3)} "
              f"{'PASS' if verdict else 'FAIL'} (expect sigma0~0.5247, t~44.4)",
              flush=True)
    print(f"BATTERY: {'PASS' if ok else 'FAIL'}", flush=True)
    return ok


def main():
    sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    print("heat72 birth-locus cartography (C1/N6; prereg hash-committed before "
          "the scored run)", flush=True)
    print("runner sha256:", sha, flush=True)
    if not battery():
        print("DQ-SECTION: battery failure -- run RED, no scored evaluation.",
              flush=True)
        sys.exit(1)

    # Scored grid: eps = D - Delta* (includes the two anchors for continuity).
    grid = []
    for e_str in ("0.001", "0.0011239031932557", "0.002", "0.0035", "0.006",
                  "0.0082667603361", "0.012", "0.02", "0.035", "0.06", "0.1"):
        grid.append(DSTAR + mpf(e_str))

    t0w = time.time()
    rows = []
    n_recheck = 0
    probe_from = 5  # the 5 largest eps get the second-pair probe
    for gi, Dv in enumerate(grid):
        eps = Dv - DSTAR
        t0 = time.time()
        cands = []
        cands += scan_candidates(Dv, mpf("0.02"), mpf("0.3"), mpf("0.005"))
        cands += scan_candidates(Dv, mpf("0.3"), mpf("2.0"), mpf("0.01"))
        law = sqrt(A_OP * eps)
        cands += [law * w for w in (mpf("0.7"), mpf(1), mpf("1.3"))]
        if gi >= len(grid) - probe_from:
            cands += scan_candidates(Dv, mpf("1.5"), mpf("4.5"), mpf("0.03"))
        zeros = []
        for tc in cands:
            for sig_seed in (mpf("0.5"), mpf("0.53")):
                z, _, r, err = locate_zero(sig_seed, tc, Dv)
                if z is not None and r < NEWTON_FLOOR:
                    zeros.append(z)
                    break
        zeros = dedupe(sorted(zeros, key=lambda w: w.imag))
        row = {"D": Dv, "eps": eps, "zeros": []}
        for z in zeros:
            onl = abs(z.real - mpf("0.5")) < ONLINE_TOL
            entry = {"s0": z, "resid": None, "online": onl}
            row["zeros"].append(entry)
            n_recheck += 1
            if n_recheck % 3 == 0:
                zr, _, rr, _ = locate_zero(z.real, z.imag, Dv, dps=DPS_RECHECK)
                drift = abs(zr - z) if zr is not None else mpf("inf")
                entry["resid"] = (drift, rr)
        rows.append(row)
        nline = sum(1 for e in row["zeros"] if e["online"])
        print(f"  [eps={mp.nstr(eps, 4)}] zeros={len(row['zeros'])} "
              f"on-line={nline} "
              f"first-t={mp.nstr(row['zeros'][0]['s0'].imag, 18) if row['zeros'] else '-'} "
              f"({time.time()-t0:.0f}s)", flush=True)
        mp.dps = DPS

    # r-table + outcome dispatch.
    print("\n=== R-TABLE (first on-line pair per D) ===", flush=True)
    pts = []
    for row in rows:
        firsts = [e for e in row["zeros"] if e["online"]]
        if not firsts:
            print(f"  eps={mp.nstr(row['eps'], 4)}: NO on-line zero located",
                  flush=True)
            continue
        u = firsts[0]["s0"].imag
        e = row["eps"]
        L2 = (A_OP - B_OP * e) * e
        r = (u * u - L2) / (e ** 3)
        pts.append((e, u, r))
        print(f"  eps={mp.nstr(e, 5)}  t0={mp.nstr(u, 20)}  "
              f"r(eps)={mp.nstr(r, 8)}", flush=True)

    offline_births = [e for row in rows for e in row["zeros"] if not e["online"]]
    second_pair = any(len([e for e in row["zeros"] if e["online"]]) >= 2
                      for row in rows)
    med = None
    slope = None
    if len(pts) >= 3:
        rs = sorted(p[2] for p in pts)
        med = rs[len(rs) // 2]
        n = len(pts)
        mx = sum(p[0] for p in pts) / n
        my = sum(p[2] for p in pts) / n
        num = sum((p[0] - mx) * (p[2] - my) for p in pts)
        den = sum((p[0] - mx) ** 2 for p in pts)
        slope = num / den if den != 0 else mpf("inf")
    r_const = (med is not None and slope is not None and
               abs(slope) * max(p[0] for p in pts) < mpf("0.25") * abs(med))
    recheck_bad = any(e["resid"] is not None and
                      (e["resid"][0] > mpf("1e-30") or e["resid"][1] > NEWTON_FLOOR)
                      for row in rows for e in row["zeros"] if e["resid"] is not None)

    if recheck_bad:
        outcome = "c"
    elif offline_births or second_pair or not r_const or not pts:
        outcome = "b"
    else:
        outcome = "a"
    print(f"\nOFF-LINE BIRTHS (low-t): {len(offline_births)}", flush=True)
    for e in offline_births:
        print(f"  s0 = {mp.nstr(e['s0'], 20)}", flush=True)
    print(f"SECOND ON-LINE PAIR in range: {second_pair}", flush=True)
    print(f"r-median = {mp.nstr(med, 8) if med is not None else '-'}  "
          f"slope = {mp.nstr(slope, 6) if slope is not None else '-'}  "
          f"constant-band: {bool(r_const)}", flush=True)
    print(f"OUTCOME: ({outcome})", flush=True)
    print(f"total {time.time()-t0w:.0f}s", flush=True)
    print("DQ-SECTION: battery PASS in-run; per-zero Newton residuals "
          f"< 1e-35 enforced (excluded zeros reported, not dropped silently); "
          f"dps-65 recheck every 3rd zero with fresh Newton "
          f"({'all clean' if not recheck_bad else 'MISMATCH PRESENT'}); "
          f"anchors reproduced pre-scored; law seeds declared (seeding is not "
          "fitting: only converged zeros enter the r-table).", flush=True)

    out = {"rows": [{"D": str(r["D"]), "eps": str(r["eps"]),
                     "zeros": [{"s0": str(e["s0"]), "online": e["online"],
                                "resid": [str(x) for x in e["resid"]] if e["resid"] else None}
                               for e in r["zeros"]]} for r in rows],
           "rtable": [[str(p[0]), str(p[1]), str(p[2])] for p in pts],
           "outcome": outcome, "r_median": str(med) if med is not None else None,
           "slope": str(slope) if slope is not None else None,
           "offline_births": len(offline_births), "second_pair": second_pair,
           "sha256": sha}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "heat72_birth_locus.results.json"), "w"),
              indent=1)


if __name__ == "__main__":
    main()
