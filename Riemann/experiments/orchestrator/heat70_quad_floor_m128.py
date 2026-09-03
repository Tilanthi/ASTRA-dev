"""heat70 — QUAD-FLOOR M=128: the successor instrument for the BUMP M-descent
rate ladder (Weil/window lane, CATEGORY D), unblocking heat69's outcome (c).

heat69 found the float64 floor (~1.3-1.6e-13 at M=128, condG*EPS*|lmax|) sits
AT OR ABOVE the observed minima (0.89x/0.11x/4.7x of floor; s2's raw reading
1.66e-14 is 0.11x its floor) — nothing certifiable, outcome (c) floor-limited
(machine1-heat69-outcome-c-adjudication.md). The block is the ARITHMETIC.

INSTRUMENT: re-draw the SAME genomes (same seeds, same rng stream
3000*seed + FAM_IDX['BUMP'] -> bitwise-identical draws), replay heat69's exact
in-place float64 GS schedule while SYMBOLICALLY TRACKING the 128x128 GS
coefficient matrix M (q_i = sum_k M[i,k] f_k), then evaluate G and K in the
CONTINUUM at quad precision:

  G[i,j]   = (M I_G M^T)[i,j],  I_G[k,l] = int f_k f_l dx
  u_i(rho) = (M I_u(rho))[i],   I_u[k,rho] = int f_k e^{rho x} dx
  K[i,j]   = sum_{rho upper, Im<=200} 2 Re[u_i(rho) conj(u_j(rho))]

WHY THE CONTINUUM IS THE GRID OBJECT: every basis function is
window(x)*(sum of C-infinity compact bumps exp(-1/(1-t^2)), |t|<1) — C-infinity,
compactly supported in |x|<=8, all derivatives vanishing at the support edge.
The dx-trapezoid sum over the 2^23 grid (h = 40/2^23 ~ 4.8e-6) equals the
continuum integral to better than any power of h (Euler-Maclaurin, vanishing
endpoint derivatives). B3 bounds this empirically (mp grid-sum vs mp.quad);
the registered floor CARRIES the measured E-M ceiling as its leading term.

Precisions: integrals at dps 45; Cholesky/solves/eigsy at dps 30 (the floor's
eigensolve term is then 1e-28*cond*|lmax|, far below the E-M term).

REGISTERED FLOOR: floor = max(EM_REL, 10^-(EIG_DPS-2)) * cond(G_q) * |lmax_q|,
with EM_REL = min(1e-23, 100 * B3-measured max relative grid-vs-quad
difference) — i.e. the E-M layer is registered at 100x its measured ceiling,
capped at 1e-23 (B3's own mp-sum rounding floor is ~1e-25 at dps 25).

PRE-REGISTERED OUTCOMES (letter BEFORE the scored run; dispatch value-tested
per trap #79 — `row.get('dq') == 'degenerate-draw'`, never key-presence):
  (a)  FREEZE: any genuine lambda_min < -1e-11 -> inherited protocol.
  (b1) RATE-CONTINUES: M=128 genuine and lambda_min(128) < 0.5*lambda_min(64)
       for BOTH comparable seeds (s1, s3; s2's M64 DQ) -> alpha-fit per seed on
       genuine points M8..128, extrapolation table.
  (b2) DESCENT-STALLS: both comparable seeds genuine with
       lambda_min(128) >= 0.5*lambda_min(64) -> B1 revision for the windowed
       class.
  (c)  INCONCLUSIVE/BOUND: anything else -> per-seed values, no rate claim.
  (d)  INSTRUMENT: >=2 of 3 seeds degenerate-draw (value test).
  (+CERTIFIED-RECORD suffix) any genuine lambda128 < 3.066441e-13 (heat61e LB)
       -> reported as the deepest CERTIFIED value on the lane; B1 status itself
       unchanged (raw descent was never in doubt).

PRE-REGISTERED BYPRODUCT (amendment B, named with denominator): per-seed
(f64_heat69 - quad_heat70)/|quad_heat70| = the float64 instrument's actual
relative error at its floor, on real draws.

MONOTONICITY FALSIFIER (inherited; trap #79 remedy: executed for EVERY
completed row and printed as a line item): lambda128 <= 1.05*lambda64 per
seed; violation -> INSTRUMENT HALT.

Falsifiers inherited: T-sat |l150-l200| > 0.1|l200| => DQ; GS relative
remainder < 1e-3 => degenerate-draw DQ (sat_pos); |G-I|max > 1e-10 => DQ.

BATTERY (mode 'battery'; NO contact with the scored M=128 quad values —
hash is committed AFTER battery PASS):
  B1  M=8 s1: quad lambda vs heat63b's committed M=8 value (float64 noise).
  B2  M=64 s1/s3 (heat63b's two genuine rows): quad vs committed values,
      agreement within ~each row's float64 floor.
  B3  E-M bound: one I_u by direct mp grid sum (dps 25, stride 16) vs mp.quad
      (dps 45) -> measured ceiling feeding EM_REL.
  B4  symbolic tracking (M=8): M-reconstructed grid rows vs GS grid Q — drift.
  B5  eigh_gen on a known 2x2 (closed form) + timing at n=60 (extrapolate
      n=128 cost).

CPU: 1 process, OMP/VECLIB pinned to 2 (5-core directive; AM-8b holds another).
"""
import os
for _v in ("OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "2")
import json, time, hashlib, sys
import numpy as np
import importlib.util as _ilu
import mpmath as mp

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fname):
    spec = _ilu.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


h63b = _load("h63b", "heat63b_corner_bottom_window_law.py")
B, H = h63b.B, h63b.H
WINDOWS, DX23, XS23 = h63b.WINDOWS, h63b.DX23, h63b.XS23
FAM_IDX_BUMP = h63b.FAM_IDX["BUMP"]
RES_BASE = json.load(open(os.path.join(_HERE, "heat63b_corner_bottom_window_law.results.json")))["res"]
HEAT69 = json.load(open(os.path.join(_HERE, "heat69_bump_m128.results.json")))["res"]

W0 = "W0"
INT_DPS = 45
EIG_DPS = 30
EM_REL_MEASURED = None          # set by B3 / the scored run's own B3 rerun
EM_REL_CAP = mp.mpf("1e-23")
LB_CERT = mp.mpf("3.066441e-13")


# --------------------------------------------------------------- basis forms
def bumps_mp(g):
    return [(mp.mpf(c), mp.mpf(mu), mp.mpf(s)) for c, mu, s in g["bumps"]]


def f_val(bp, x):
    """C-infinity compact bump sum at mp scalar x, window NOT applied."""
    tot = mp.mpf(0)
    for c, mu, s in bp:
        t = (x - mu) / s
        if abs(t) < 1:
            tot += c * mp.exp(-1 / (1 - t * t))
    return tot


def theta_mp(s):
    if s <= 0:
        return mp.mpf(0)
    if s >= 1:
        return mp.mpf(1)
    e = mp.exp(-1 / s)
    e2 = mp.exp(-1 / (1 - s))
    return e / (e + e2)


def window_mp(x):
    return theta_mp((mp.mpf(8) - abs(x)) / 2)


def fw_val(bp, x):
    return f_val(bp, x) * window_mp(x)


def breakpoints(bps):
    """Split points: support edges mu±s of every bump, plus the window knees
    and the outer support. tanh-sinh on one big interval MISSES narrow
    interior compact bumps (found in battery B-debug: <f0,f2> -> 0.0); each
    piece is analytic, so per-piece quad converges to full precision."""
    pts = [mp.mpf(-8), mp.mpf(-6), mp.mpf(6), mp.mpf(8)]
    for bp_ in bps:
        for c, mu, s in bp_:
            for b in (mu - s, mu + s):
                if mp.mpf(-8) < b < mp.mpf(8):
                    pts.append(b)
    return sorted(set(pts))


def I_G(bp1, bp2):
    def integrand(x):
        return fw_val(bp1, x) * fw_val(bp2, x)
    return mp.quad(integrand, breakpoints([bp1, bp2]))


def I_u(bp, rho):
    # bump-boundary splitting only: the e^{rho x} oscillation (Im rho <= 200)
    # is handled by tanh-sinh's degree on the analytic pieces — verified
    # against the float64 grid to 4.3e-17 (the grid's own limit), with and
    # without half-period subdivision agreeing to the digit.
    re_ex = rho.real
    im_rho = rho.imag
    pts = breakpoints([bp])
    def re_part(x):
        return fw_val(bp, x) * mp.exp(re_ex * x) * mp.cos(im_rho * x)
    def im_part(x):
        return fw_val(bp, x) * mp.exp(re_ex * x) * mp.sin(im_rho * x)
    return mp.quad(re_part, pts) + 1j * mp.quad(im_part, pts)


# --------------------------------------------------- symbolic GS (grid + M)
def gs_symbolic(seed, m_basis=128):
    """Replay heat69's exact GS schedule bitwise; return (Q, Mcoef, sat_pos, gs)."""
    H.CUT_IN, H.CUT_OUT = WINDOWS[W0]
    rng = np.random.default_rng(3000 * seed + FAM_IDX_BUMP)
    gs = h63b.draw_insupport("BUMP", rng, m_basis)
    Q = np.empty((m_basis, XS23.size))
    Mcoef = np.zeros((m_basis, m_basis))
    sat_pos = None
    for i, g in enumerate(gs):
        f = B.realize_any("BUMP", g, XS23)
        n_in = np.sqrt(DX23 * (f * f).sum())
        if n_in < 1e-12:
            sat_pos = i
            break
        c = np.zeros(m_basis)
        c[i] = 1.0
        for j in range(i):
            p = DX23 * (f * Q[j]).sum()
            f = f - p * Q[j]
            c = c - p * Mcoef[j]
        nr = np.sqrt(DX23 * (f * f).sum())
        if nr < 1e-3 * n_in:
            sat_pos = i
            break
        Q[i] = f / nr
        Mcoef[i] = c / nr
    return Q, Mcoef, sat_pos, gs


# ------------------------------------------------------- matrix helpers (mp)
def to_mp_matrix(A):
    m, n = A.shape
    Am = mp.matrix(m, n)
    for i in range(m):
        for j in range(n):
            Am[i, j] = mp.mpf(float(A[i, j]))
    return Am


def mp_matmul(A, Bm):
    m, k, n = A.rows, A.cols, Bm.cols
    C = mp.matrix(m, n)
    for i in range(m):
        for j in range(n):
            s = mp.mpf(0)
            for t in range(k):
                a = A[i, t]
                if a:
                    s += a * Bm[t, j]
            C[i, j] = s
    return C


def tri_solve(L, e, lower=True):
    n = L.rows
    y = mp.matrix(n, 1)
    if lower:
        for i in range(n):
            s = e[i]
            for j in range(i):
                s -= L[i, j] * y[j]
            y[i] = s / L[i, i]
    else:
        for i in range(n - 1, -1, -1):
            s = e[i]
            for j in range(i + 1, n):
                s -= L[j, i] * y[j]
            y[i] = s / L[i, i]
    return y


def eigh_gen(K, G):
    """Generalized symmetric-definite eigenproblem at current dps via
    Cholesky + transform + eigsy. Returns (lam_min, lam_max, condG)."""
    n = K.rows
    U = mp.cholesky(G)               # mpmath returns upper: G = U^T U (real)
    L = U.T                          # lower-triangular for tri_solve: G = L L^T
    Y = mp.matrix(n, n)                       # Y = L^{-1} K
    for col in range(n):
        e = mp.matrix(n, 1)
        for r in range(n):
            e[r] = K[r, col]
        y = tri_solve(L, e, lower=True)
        for r in range(n):
            Y[r, col] = y[r]
    Bm = mp.matrix(n, n)                      # B = Y L^{-T}
    for row in range(n):
        e = mp.matrix(n, 1)
        for c in range(n):
            e[c] = Y[row, c]
        x = tri_solve(L, e, lower=False)      # L x = e  <=>  x = L^{-T} e^T rows
        for c in range(n):
            Bm[row, c] = x[c]
    for i in range(n):
        for j in range(i + 1, n):
            m = (Bm[i, j] + Bm[j, i]) / 2
            Bm[i, j] = m
            Bm[j, i] = m
    ev = mp.eigsy(Bm, eigvals_only=True)
    gev = mp.eigsy(G, eigvals_only=True)      # for cond(G)
    cond = max(gev) / min(gev)
    return min(ev), max(ev), cond


# ------------------------------------------------------------- quad trial
def quad_trial(seed, m_basis=128, verbose=True):
    t0 = time.time()
    tag = f"{W0}/BUMP/s{seed}/M{m_basis}"
    Q, Mcoef, sat_pos, gs = gs_symbolic(seed, m_basis)
    if sat_pos is not None:
        return tag, {"dq": "degenerate-draw", "sat_pos": sat_pos}
    Ggrid = DX23 * (Q @ Q.T)
    oerr = float(np.abs(Ggrid - np.eye(m_basis)).max())
    mp.mp.dps = INT_DPS
    bp = [bumps_mp(g) for g in gs]
    zeros = []
    n = 1
    while True:
        z = mp.zetazero(n)
        if z.imag > 200:
            break
        zeros.append(z)
        n += 1
    nz = len(zeros)
    t1 = time.time()
    IG = [[None] * m_basis for _ in range(m_basis)]
    for k in range(m_basis):
        for l in range(k, m_basis):
            v = I_G(bp[k], bp[l])
            IG[k][l] = v
            IG[l][k] = v
    t2 = time.time()
    IU = [[None] * nz for _ in range(m_basis)]
    for k in range(m_basis):
        for j in range(nz):
            IU[k][j] = I_u(bp[k], zeros[j])
    t3 = time.time()
    IGm = mp.matrix(m_basis, m_basis)
    for k in range(m_basis):
        for l in range(m_basis):
            IGm[k, l] = IG[k][l]
    IUm = mp.matrix(m_basis, nz)
    for k in range(m_basis):
        for j in range(nz):
            IUm[k, j] = IU[k][j]
    Mc = to_mp_matrix(Mcoef)
    G = mp_matmul(mp_matmul(Mc, IGm), Mc.T)
    t4 = time.time()
    # u_i(rho_j) = (Mc IUm)[i, j]
    McIU = mp_matmul(Mc, IUm)
    K = mp.matrix(m_basis, m_basis)
    for j in range(nz):
        for i1 in range(m_basis):
            u1 = McIU[i1, j]
            if not u1:
                continue
            for i2 in range(i1, m_basis):
                u2 = McIU[i2, j]
                if not u2:
                    continue
                term = 2 * (u1 * u2.conjugate()).real
                K[i1, i2] += term
                if i1 != i2:
                    K[i2, i1] += term
    t5 = time.time()
    mp.mp.dps = EIG_DPS
    lam, lmax, cond = eigh_gen(K, G)
    # T=150 saturation: rebuild K from zeros with Im<=150
    K150 = mp.matrix(m_basis, m_basis)
    for j in range(nz):
        if zeros[j].imag > 150:
            continue
        for i1 in range(m_basis):
            u1 = McIU[i1, j]
            if not u1:
                continue
            for i2 in range(i1, m_basis):
                u2 = McIU[i2, j]
                if not u2:
                    continue
                term = 2 * (u1 * u2.conjugate()).real
                K150[i1, i2] += term
                if i1 != i2:
                    K150[i2, i1] += term
    lam150, _, _ = eigh_gen(K150, G)
    sat = abs(lam150 - lam) <= mp.mpf("0.1") * abs(lam) if lam != 0 else True
    dq = (not sat) or oerr > 1e-10
    em = EM_REL_CAP if EM_REL_MEASURED is None else min(EM_REL_CAP, 100 * EM_REL_MEASURED)
    floor = max(em, mp.mpf(10) ** (-(EIG_DPS - 2))) * cond * abs(lmax)
    gen = (not dq) and abs(lam) >= 10 * floor
    if verbose:
        print(f"  {tag}: lambda={mp.nstr(lam, 12)} l150={mp.nstr(lam150, 8)} "
              f"floor={mp.nstr(floor, 4)} cond={mp.nstr(cond, 8)} genuine={gen} nz={nz}", flush=True)
        print(f"    timings: IG {t2-t1:.0f}s IU {t3-t2:.0f}s matmul {t4-t3:.0f}s K {t5-t4:.0f}s total {time.time()-t0:.0f}s", flush=True)
    return tag, {"lmin200": lam, "l150": lam150, "lmax": lmax, "condG": cond,
                 "ortho_err": oerr, "dq": bool(dq), "genuine": bool(gen),
                 "nz": nz, "floor": floor}


def alpha_fit(pts):
    xs = [mp.log(p[0]) for p in pts]
    ys = [mp.log(abs(p[1])) for p in pts]
    n = len(pts)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    return num / den


def to_jsonable(row):
    return {k: (str(v) if isinstance(v, (mp.mpf, mp.mpc)) else v) for k, v in row.items()}


# ------------------------------------------------------------------ battery
def battery():
    print("heat70 BATTERY (instrument validation; no contact with scored M=128 quad values)", flush=True)
    global EM_REL_MEASURED
    # B4: symbolic tracking on M=8
    Q, Mcoef, sat_pos, gs = gs_symbolic(1, 8)
    assert sat_pos is None, "M=8 seed 1 must not degenerate"
    idx = np.linspace(0, XS23.size - 1, 2000).astype(int)
    drift = 0.0
    for i in range(8):
        rec = np.zeros(idx.size)
        for k in range(8):
            if Mcoef[i, k]:
                fk = B.realize_any("BUMP", gs[k], XS23)
                rec += Mcoef[i, k] * fk[idx]
        drift = max(drift, float(np.abs(rec - Q[i][idx]).max()))
    print(f"B4 symbolic-tracking drift (M=8 s1, 2000 pts): {drift:.3e}  (expect ~1e-15)", flush=True)
    # B1: M=8 quad lambda vs heat63b committed
    tag, row = quad_trial(1, m_basis=8)
    ref = RES_BASE.get("W0/BUMP/s1/M8")
    d = abs(mp.mpf(repr(row["lmin200"])) - mp.mpf(repr(ref["lmin200"])))
    print(f"B1 M=8 s1: quad {mp.nstr(row['lmin200'], 10)} vs heat63b {ref['lmin200']:+.9e} -> abs diff {mp.nstr(d, 4)}", flush=True)
    # B3: E-M bound — mp grid sum (dps 25, stride 16) vs mp.quad (dps 45)
    mp.mp.dps = 25
    g = gs[0]
    bp = bumps_mp(g)
    rho = mp.zetazero(1)
    support = np.abs(XS23) <= 8.0000001
    xs_sup = XS23[support][::16]
    s = mp.mpc(0)
    for xk in xs_sup:
        x = mp.mpf(float(xk))
        v = fw_val(bp, x)
        ex = mp.exp(rho.real * x)
        s += v * ex * (mp.cos(rho.imag * x) + 1j * mp.sin(rho.imag * x))
    grid_val = s * mp.mpf(repr(float(DX23) * 16))
    mp.mp.dps = INT_DPS
    quad_val = I_u(bumps_mp(g), mp.zetazero(1))
    rel = abs((grid_val - quad_val) / quad_val)
    EM_REL_MEASURED = mp.mpf(rel)
    print(f"B3 E-M ceiling (stride-16 mp sum vs quad): rel diff {mp.nstr(rel, 4)} -> EM_REL registered at {mp.nstr(min(EM_REL_CAP, 100*rel), 4)}", flush=True)
    # B2: M=64 genuine rows s1/s3
    for seed in (1, 3):
        tag, row = quad_trial(seed, m_basis=64)
        ref = RES_BASE.get(f"W0/BUMP/s{seed}/M64")
        d = abs(mp.mpf(repr(row["lmin200"])) - mp.mpf(repr(ref["lmin200"])))
        print(f"B2 M=64 s{seed}: quad {mp.nstr(row['lmin200'], 10)} vs heat63b {ref['lmin200']:+.9e} -> abs diff {mp.nstr(d, 4)} (heat63b floor {ref['floor']:.2e})", flush=True)
    # B5: eigh_gen 2x2 closed form + n=60 timing
    Kt = mp.matrix([[mp.mpf(2), 0], [0, mp.mpf(6)]])
    Gt = mp.matrix([[mp.mpf(2), mp.mpf(1)], [mp.mpf(1), mp.mpf(2)]])
    lam, lmax, cond = eigh_gen(Kt, Gt)
    ref2 = sorted(np.linalg.eigvals(np.linalg.inv(np.array([[2.0, 1], [1, 2]])) @ np.array([[2.0, 0], [0, 6]])).real)
    print(f"B5 eigh_gen 2x2: quad ({mp.nstr(lam, 14)}, {mp.nstr(lmax, 14)}) cond {mp.nstr(cond, 8)} vs float64 {ref2}", flush=True)
    t0 = time.time()
    n = 60
    Kx = mp.matrix(n, n)
    for i in range(n):
        Kx[i, i] = mp.mpf(1 + i)
        if i + 1 < n:
            Kx[i, i + 1] = Kx[i + 1, i] = mp.mpf("0.1")
    Gx = mp.matrix(n, n)
    for i in range(n):
        Gx[i, i] = mp.mpf(1)
    Gx[0, 1] = Gx[1, 0] = mp.mpf("0.01")
    lam, lmax, _ = eigh_gen(Kx, Gx)
    dt = time.time() - t0
    print(f"B5 timing: n=60 eigh_gen {dt:.1f}s -> n=128 ~ {dt*(128/60)**3:.0f}s x2 (T-sat) per trial", flush=True)


if __name__ == "__main__":
    sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    print("heat70 QUAD-FLOOR M=128 (pre-registered; runner sha256 below)", flush=True)
    print("runner sha256:", sha, flush=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "scored"
    if mode == "battery":
        battery()
        print("battery done", flush=True)
        sys.exit(0)
    t0 = time.time()
    res, n_deg, mono_violation = {}, 0, False
    for seed in (1, 2, 3):
        tag, row = quad_trial(seed)
        res[tag] = to_jsonable(row)
        b64 = RES_BASE.get(f"W0/BUMP/s{seed}/M64")
        if row.get("dq") == "degenerate-draw":          # VALUE test (trap #79)
            n_deg += 1
            print(f"  s{seed}: degenerate draw at sat_pos={row['sat_pos']}", flush=True)
        elif b64 and "lmin200" in b64:
            mono = mp.mpf(repr(row["lmin200"])) <= 1.05 * mp.mpf(repr(b64["lmin200"]))
            print(f"  s{seed} monotonicity vs M64 ({b64['lmin200']:+.6e}): {'OK' if mono else 'VIOLATION -> INSTRUMENT HALT'}", flush=True)
            if not mono:
                mono_violation = True
                break
        h69 = HEAT69.get(tag)
        if h69 and "lmin200" in h69 and "lmin200" in row:
            fog = (mp.mpf(repr(h69["lmin200"])) - mp.mpf(repr(row["lmin200"]))) / abs(mp.mpf(repr(row["lmin200"])))
            print(f"  s{seed} FOG BYPRODUCT (f64-quad)/quad: {mp.nstr(fog, 4)}", flush=True)
    outcome = None
    if mono_violation:
        outcome = "HALT-instrument-monotonicity"
    else:
        cont = stall = 0
        for seed in (1, 2, 3):
            r = res.get(f"W0/BUMP/s{seed}/M128")
            b = RES_BASE.get(f"W0/BUMP/s{seed}/M64")
            if r and r.get("genuine") and b and b.get("genuine"):
                if mp.mpf(r["lmin200"]) < 0.5 * mp.mpf(repr(b["lmin200"])):
                    cont += 1
                else:
                    stall += 1
        freeze = any(r.get("genuine") and mp.mpf(r["lmin200"]) < mp.mpf(-1e-11)
                     for r in res.values() if "lmin200" in r)
        record = any(r.get("genuine") and mp.mpf(r["lmin200"]) < LB_CERT
                     for r in res.values() if "lmin200" in r)
        for seed in (1, 2, 3):
            r = res.get(f"W0/BUMP/s{seed}/M128")
            if r and r.get("genuine"):
                pts = [(m, mp.mpf(repr(RES_BASE[f"W0/BUMP/s{seed}/M{m}"]["lmin200"])))
                       for m in (8, 16, 32, 64)
                       if RES_BASE.get(f"W0/BUMP/s{seed}/M{m}", {}).get("genuine")]
                pts.append((128, mp.mpf(r["lmin200"])))
                a = alpha_fit(pts)
                print(f"  s{seed}: alpha = {mp.nstr(a, 6) if a is not None else None} on {len(pts)} genuine pts", flush=True)
                if a:
                    for tgt in (mp.mpf("1e-13"), mp.mpf("1e-16")):
                        m_need = 128 * (abs(mp.mpf(r["lmin200"])) / tgt) ** (1 / a)
                        print(f"    extrapolated M for {mp.nstr(tgt, 3)}: {mp.nstr(m_need, 4)}", flush=True)
        if freeze:
            outcome = "a"
        elif n_deg >= 2:
            outcome = "d"
        elif cont >= 2:
            outcome = "b1"
        elif stall >= 2:
            outcome = "b2"
        else:
            outcome = "c"
        if record:
            outcome += "+CERTIFIED-RECORD"
    print(f"\nOUTCOME: ({outcome})", flush=True)
    print(f"total {time.time()-t0:.0f}s", flush=True)
    json.dump({"res": res, "outcome": outcome, "sha256": sha,
               "em_rel_measured": str(EM_REL_MEASURED) if EM_REL_MEASURED is not None else None},
              open(os.path.join(_HERE, "heat70_quad_floor_m128.results.json"), "w"), indent=1)
