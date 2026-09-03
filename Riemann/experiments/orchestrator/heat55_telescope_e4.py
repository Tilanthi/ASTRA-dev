"""heat55 — E4: the FULL telescope two-radius census (the division-of-labour
  item behind heat54; E9/heat32c was the 4-row first pass).

CATEGORY: C (κ/telescope lane — E4 census; the C4 stop-rule applies after
this run; zero RH claim possible from it).

Site: idx 95248/95249, mid=71732.9085586, d=0.0073507 (2/d^2 = 37,014) —
anchors copied from heat32c_telescope.py's committed header (trap #51: from
the on-disk file, not memory). B(measured) = 4.6481 -> B d^2/2 = 1.26e-4, so
pure ~ extended here: the closed form tested bare, at the tightest pair in
our pool (a/d = 1.36 > 1 regime).

PRE-REGISTERED (this docstring committed before the run; thresholds fixed):

E1  b-grid at (a=0.01, lam=0.5), 11 rows 0.0060..0.0080:
      - birth rows: |y| measured, |y|^2 = C*(b_c - b) fitted (>=3 df);
      - F1 FAIL if b_c^emp deviates from extended b_c^model = 0.0074084
        by > 1% (E9 2-row gave +0.013%; pool-typical |err| 0.5%);
      - F2 FAIL if |y|^2-linearity r^2 < 0.999 over the birth rows;
      - F3 FAIL if any row's birth/clean verdict contradicts its
        pre-registered label below.
    Row labels from b_c^model: births for b < 0.0074084, clean above.
E2  lam-slice at a=0.01: lam in {0.65, 0.80}, b = b_c^model(lam) - 0.0004
    (pre-registered BIRTH both; closed form b_c(lam) = sqrt(sqrt(lam)*
    sqrt(a^2+d^2)... computed in-script as bc_model). F4 FAIL if either
    comes back clean, or if the measured b_c^emp(lam) (2-row sqrt system
    per lam: b and b+0.0002) deviates > 2% from bc_model(lam).
E3  a-slice at lam=0.5: a in {0.005, 0.015}, same construction. F5 FAIL
    mirrors F4.

NO C closed form is predicted our-side (beast's C=0.1240 was k922-specific;
the c(a,lam) derivation is still their outstanding ask) — E1 measures
C^emp(telescope) for that lane. Pure-model |y| per row from the heat32c
two-zero quadratic (imported verbatim below, trap #60).

Runtime: zeta ~0.03-0.05 s/call at h=71733; each census row = ~1200 grid
evals + winding (700) + fine locates; ~2-4 min/row single-proc; 15 rows
~ 45 min; Pool(5) ~ 12-15 min. Launched only after heat54 exits (CPU grant
= 5 workers on this 10-core machine).
"""
import os
import mpmath as mp

mp.mp.dps = 30
MID = mp.mpf("71732.9085586")
D = mp.mpf("0.0073507")
LAM = mp.mpf("0.5")

def xi_z(z):
    s = mp.mpf("0.5") + mp.mpc(0, 1)*z
    return mp.power(mp.pi, -s/2)*mp.gamma(s/2)*mp.zeta(s)*s*(s-1)/2

def mixed(z, b, a, lam):                      # verbatim heat32c
    Xp = xi_z(z + mp.mpc(0, 1)*b); Xm = xi_z(z - mp.mpc(0, 1)*b)
    Xb2 = ((Xp+Xm)/2)**2 if b != 0 else xi_z(z)**2
    Xp = xi_z(z + mp.mpc(0, 1)*a); Xm = xi_z(z - mp.mpc(0, 1)*a)
    return Xb2 - lam*Xp*Xm

def real_zeros_f(f, x0, x1, h):               # verbatim heat32c
    zs = []; tp = mp.mpf(x0); vp = f(tp).real
    n = int(float((mp.mpf(x1)-mp.mpf(x0))/h))
    for k in range(1, n+1):
        t = mp.mpf(x0)+h*k
        v = f(t).real
        if (v > 0) != (vp > 0):
            lo, hi = tp, t
            for _ in range(70):
                m = (lo+hi)/2
                if (f(m).real > 0) == (vp > 0): lo = m
                else: hi = m
            zs.append((lo+hi)/2)
        tp = t; vp = v
    return zs

def wind_f(f, x0, x1, W, N=700):              # verbatim heat32c
    x0, x1, W = mp.mpf(x0), mp.mpf(x1), mp.mpf(W)
    def boundary(k):
        per = [
            (lambda u: mp.mpc(x0 + u*(x1-x0), -W), 0.0, 1.0),
            (lambda u: mp.mpc(x1, -W + u*2*W), 1.0, 2.0),
            (lambda u: mp.mpc(x1 - u*(x1-x0), W), 2.0, 3.0),
            (lambda u: mp.mpc(x0, W - u*2*W), 3.0, 4.0),
        ]
        for f2, s0, s1 in per:
            if s0 <= k < s1:
                return f2((k - s0)/(s1 - s0))
        return mp.mpc(x0, -W)
    tot = mp.mpf(0); prev = f(boundary(0))
    for i in range(1, N+1):
        cur = f(boundary(4.0*i/N))
        d = mp.arg(cur) - mp.arg(prev)
        while d > mp.pi: d -= 2*mp.pi
        while d < -mp.pi: d += 2*mp.pi
        tot += d; prev = cur
    return int(round(float(tot/(2*mp.pi))))

def locate_fine(f, xc, W, n=41, ylo=None, yhi=None):   # verbatim heat32c
    ylo = -W if ylo is None else ylo
    yhi = W if yhi is None else yhi
    xs = [xc - W + (2*W)*k/n for k in range(n+1)]
    ys = [ylo + (yhi-ylo)*k/n for k in range(n+1)]
    pts = []
    for x in xs:
        for y in ys:
            z0 = mp.mpc(x, y)
            pts.append((abs(f(z0)), z0))
    pts.sort(key=lambda p: p[0])
    out = []
    for _, z0 in pts[:6]:
        try:
            z = mp.findroot(f, z0, tol=mp.mpf("1e-25"), maxsteps=60)
        except Exception:
            continue
        if abs(f(z)) < mp.mpf("1e-18"):
            if not any(abs(z-o) < mp.mpf("1e-7") for o in out):
                out.append(z)
    return out

def model_y(a, b, d, lam):                    # verbatim heat32c (pure two-zero)
    A = mp.mpf(1)-lam; B = -2*(b*b + (1-lam)*d*d + lam*a*a)
    C = (b*b+d*d)**2 - lam*(a*a+d*d)**2
    disc = B*B - 4*A*C
    if disc < 0: return None
    w1 = (-B - mp.sqrt(disc))/(2*A); w2 = (-B + mp.sqrt(disc))/(2*A)
    ys = [mp.sqrt(-w) for w in (w1, w2) if w < 0]
    return max(ys) if ys else None

def bc_model(a, d, lam):                      # beast closed form (NOTES (12))
    return mp.sqrt(mp.sqrt(lam)*(a*a + d*d) - d*d)

def census_row(a_s, b_s, lam_s, tag):
    """returns dict: verdict, n_real, wind, ym (max |Im| of off-axis zeros)"""
    a, b, lam = mp.mpf(a_s), mp.mpf(b_s), mp.mpf(lam_s)
    f = lambda t: mixed(t, b, a, lam)
    zs = real_zeros_f(f, MID-mp.mpf("0.6"), MID+mp.mpf("0.6"), mp.mpf("0.001"))
    w = wind_f(f, MID-mp.mpf("0.6"), MID+mp.mpf("0.6"), "0.25")
    row = dict(tag=tag, a=float(a), b=float(b), lam=float(lam),
               n_real=len(zs), wind=w)
    if w == len(zs):
        row["verdict"] = "CLEAN(all-on-line)"
    else:
        off = locate_fine(f, MID, mp.mpf("0.006"), n=41,
                          ylo=mp.mpf("0.00005"), yhi=mp.mpf("0.006"))
        ym = max(abs(float(mp.im(o))) for o in off) if off else float("nan")
        row["verdict"] = "BIRTH" if off else "NO-LOCATE"
        row["ym"] = ym
        row["ymodel_pure"] = float(model_y(a, b, D, lam)) if model_y(a, b, D, lam) else None
    return row

def fmt(r):
    s = (f"  {r['tag']:14s} a={r['a']:.4f} b={r['b']:.5f} lam={r['lam']:.2f}: "
         f"{r['verdict']:20s} real={r['n_real']} wind={r['wind']}")
    if "ym" in r:
        s += f"  |y|={r['ym']:.7f}"
        if r.get("ymodel_pure"):
            s += f"  pure={r['ymodel_pure']:.7f}"
    return s

def job(spec):
    fam, b_s, a_s, lam_s = spec
    tag = (f"E1 b={b_s}" if fam == "E1"
           else f"SL a={a_s} lam={lam_s} b={b_s}")
    return census_row(a_s, b_s, lam_s, tag)


if __name__ == "__main__":
    import json
    from multiprocessing import Pool

    print("CATEGORY: C (κ/telescope lane — E4 census; C4 stop-rule after this)",
          flush=True)
    print("== heat55: E4 telescope full census (pre-registered) ==", flush=True)
    print(f"site mid={MID} d={D}  a/d={float(mp.mpf('0.01')/D):.4f}  "
          f"2/d^2={float(2/D**2):.0f}", flush=True)
    bcm = bc_model(mp.mpf("0.01"), D, LAM)
    print(f"bc_model(0.01, 0.5) = {mp.nstr(bcm, 8)}  (E9 2-row b_c^emp "
          f"0.007409379 = +0.013%; beast committed 0.007408 +- 2e-6)",
          flush=True)

    # all row specs upfront (thresholds/rows pre-registered in docstring)
    specs = [("E1", b, "0.01", "0.5") for b in
             ("0.0060", "0.0065", "0.0070", "0.0072", "0.0073",
              "0.0074", "0.00745", "0.0075", "0.0076", "0.0078", "0.0080")]
    slices = {}
    for tag, a_s, lam_s in (("E2 lam=0.65", "0.01", "0.65"),
                            ("E2 lam=0.80", "0.01", "0.80"),
                            ("E3 a=0.005", "0.005", "0.5"),
                            ("E3 a=0.015", "0.015", "0.5")):
        bmod = bc_model(mp.mpf(a_s), D, mp.mpf(lam_s))
        slices[tag] = (a_s, lam_s, mp.nstr(bmod, 10))
        for db in ("-0.0004", "-0.0002"):
            specs.append(("SLICE", mp.nstr(bmod + mp.mpf(db), 8), a_s, lam_s))

    with Pool(max(1, int(os.environ.get("RIEMANN_WORKERS", "5")))) as pool:
        # CPU budget (user directive 2026-09-03): total across all streams
        # <= 5 cores while the user works; job lives at module top level
        # (trap #58 — spawn): workers re-import __mp_main__ and would
        # die on unpickling a guard-nested def (heat55 v1's 70-min stall)
        rows = pool.map(job, specs)
    json.dump(rows, open("heat55_telescope_e4.results.json", "w"), indent=1)  # heat41c lesson: persist BEFORE reporting
    for r in rows:
        print(fmt(r), flush=True)

    # ---- E1 verdicts (F1/F2/F3) ----
    e1 = [r for r in rows if r["tag"].startswith("E1")]
    births = [r for r in e1 if r["verdict"] == "BIRTH" and "ym" in r]
    if len(births) >= 3:
        import numpy as np
        bb = np.array([r["b"] for r in births])
        yy = np.array([r["ym"] for r in births])**2
        A_ = np.vstack([np.ones_like(bb), -bb]).T
        coef, *_ = np.linalg.lstsq(A_, yy, rcond=None)
        C_fit, bc_emp = coef
        yy_hat = A_ @ coef
        ss_res = float(((yy - yy_hat)**2).sum())
        ss_tot = float(((yy - yy.mean())**2).sum())
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else float("nan")
        dev = (bc_emp - float(bcm))/float(bcm)*100
        print(f"\nE1 sqrt-fit: b_c^emp = {bc_emp:.9f}  C^emp = {C_fit:.6f}  "
              f"r^2 = {r2:.6f}", flush=True)
        print(f"F1 (b_c^emp vs model, >1% FAIL): dev = {dev:+.3f}% -> "
              f"{'FAIL' if abs(dev) > 1 else 'PASS'}", flush=True)
        print(f"F2 (linearity r^2 >= 0.999): -> "
              f"{'FAIL' if r2 < 0.999 else 'PASS'}", flush=True)
        bad = [r["tag"] for r in e1
               if (r["b"] < float(bcm)) and r["verdict"].startswith("CLEAN")]
        bad += [r["tag"] for r in e1
                if (r["b"] > float(bcm)) and not r["verdict"].startswith("CLEAN")]
        print(f"F3 (row labels): {'FAIL ' + str(bad) if bad else 'PASS'}",
              flush=True)
        print("  (C^emp handed to beast's c(a,lam) lane — no our-side "
              "closed-form prediction pre-registered)", flush=True)
    else:
        print(f"\nE1: only {len(births)} birth rows with |y| — fit "
              "under-determined, F1/F2 reported INDETERMINATE", flush=True)

    # ---- E2/E3 slice verdicts (F4/F5) ----
    for tag, (a_s, lam_s, bmod_s) in slices.items():
        bmod = mp.mpf(bmod_s)
        pts = [r for r in rows if r["tag"].startswith("SL")
               and f"a={a_s} lam={lam_s}" in r["tag"]]
        print(f"\n{tag}: bc_model = {mp.nstr(bmod, 8)}", flush=True)
        ok = [r for r in pts if r["verdict"] == "BIRTH" and "ym" in r]
        if len(ok) == 2:
            (r1, r2_) = sorted(ok, key=lambda r: r["b"])
            C_sl = (r1["ym"]**2 - r2_["ym"]**2)/(r1["b"] - r2_["b"])
            bc_sl = r1["b"] + r1["ym"]**2/C_sl
            dev = (bc_sl - float(bmod))/float(bmod)*100
            print(f"  2-row system: b_c^emp = {bc_sl:.9f}  dev = {dev:+.3f}%"
                  f"  (gate 2%) -> {'FAIL' if abs(dev) > 2 else 'PASS'}",
                  flush=True)
        else:
            print(f"  2-row system INDETERMINATE (birth rows with |y|: "
                  f"{len(ok)}/2) — F4/F5 flag", flush=True)
    print("\ndone", flush=True)
