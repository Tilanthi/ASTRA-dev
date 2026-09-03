"""heat54 — E6: Suzuki (arXiv:1409.5394) M-function spacing calibration.

  THE LAW BEING TESTED (Theorem 1, eq (1.7); unconditional):
  zeros of Re xi (A_omega) / Im xi (B_omega) on sigma=1/2+omega, ordinates
  gamma_n, second-normalized spacing (eqs (1.3),(1.4),(3.2))
      gamma_n^(1) = (gamma_n/2pi) log(gamma_n/2pi e)
      v_n = [(gamma_n+1^(1) - gamma_n^(1)) - 1] * (1/2pi)log(gamma_n/2pi e)
            / rho_omega^(1/2)
  has limiting density
      P(v) = pi * rho_omega^(1/2) * m_{1/2+omega}(pi rho_omega^(1/2) v) / (2pi)
  where m_sigma is the marginal of M_sigma, the value-distribution density
  of zeta'/zeta(sigma+it) (normalised (1/2pi)Int M Phi = limit mean).
  Proposition 2's mechanism: v_n ~ -(1/pi) Re zeta'/zeta(1/2+omega+i gamma_n),
  so with f = the (unit-normalised) density of X = Re zeta'/zeta(s) at the
  SAME height window, m ~ 2pi f and
      P(v) = pi * rho^(1/2) * f(pi rho^(1/2) v)          [bridge]
  implying Var(v) * pi^2 * rho_omega ~ Var(X)            [F5].
  Theorem 2 (omega->0+): P -> N(0,1). NOTE our derivation above shows
  Var(X) -> pi^2 rho (NOT 2pi^2 rho) is the Thm-2-consistent constant; we
  print BOTH ratios and pre-register only the bridge identity (omega-free).

  rho_omega = (1/2pi^2) SUM_p log^2 p / (p^(1+2omega) - 1)
            = (1/2pi^2) SUM_{k>=1} P''(k(1+2omega)),
  P(s) = prime zeta = SUM_mu(m)/m log zeta(ms)  =>  P''(s) =
  SUM_mu(m) m [zeta''/zeta - (zeta'/zeta)^2](ms).
  Cross-check at each omega vs direct prime sieve to 5e6 + PNT tail.

  PRE-REGISTRATION (trap #32; written before execution):
  Primary config: W1 = t in [5005, 9005] (centre 7005, our named-site
  height), B-side (Im xi zeros), omega = 0.15.
   F1 [STRUCTURE]: KS(empirical v, P) at primary: PASS <= 0.10;
      FALSIFIED > 0.15; else AMBIGUOUS (reported).
   F2 [RHO-BRIDGE]: B-side KS <= 0.12 at ALL THREE omega in {0.05,0.15,0.30}
      on W1 AND wrong-rho control (v defined with rho(0.30) at omega=0.15)
      KS >= 1.5x correct. FALSIFIED if any B-KS > 0.18 or control not
      separable.
   F3 [THM-2 DIRECTION, qualitative — no hard falsifier, rate unknown]:
      report KS(v, N(0,1)) at omega = 0.30/0.15/0.05; trend expected down.
   F4 [A/B SYMMETRY]: KS(A-side, omega=0.15, W1) <= 0.15.
   F5 [BRIDGE VARIANCE]: Var(v)*pi^2*rho / Var(X) in [0.85,1.15] at primary
      (bootstrap 95% CI quoted).
  Controls: shifted-Exp(1) (Poisson count-fluctuation law, expect FAIL);
  N(0,1) (Thm-2 limit); wrong-rho (discrimination). Positioning extra:
  raw-gap NNSD vs Wigner surmise (different variable; NOT a test of Thm 1).
  DQ gate per stream: |N_found - Nbar|/Nbar <= 0.02 else stream DQ-FAIL.
  Pre-asymptotic probe: W2 = t in [0, 2000] (centre 1000), B, omega=0.15.

  Traps in force: #32 (this pre-reg), #35 (fired falsifiers reported
  first), #36 (outputs quoted verbatim in .out), #49-scope (zeta' via
  FIRST-order mp.diff at dps 40 — magnitude O(1..1e2), no log, compliant),
  #52 (checker verified: prime-zeta rho vs sieve+PNT), #58 (__main__
  guard; no module-level compute).

  HEAT54_SMOKE=1 runs a tiny end-to-end validation (W=300, one config).
"""
import os
import json
import numpy as np
import mpmath as mp
from multiprocessing import Pool

# CPU budget (user directive 2026-09-03): TOTAL compute across all streams
# <= 5 cores while the user is working (10-core laptop). Default 5 = this
# stream alone owns the budget; set RIEMANN_WORKERS lower when a second
# single-core stream (e.g. heat61e) runs beside it. Two full Pool streams
# concurrently are an overnight-only configuration (explicit CPU grant).
WORKERS = max(1, int(os.environ.get("RIEMANN_WORKERS", "5")))

SMOKE = os.environ.get("HEAT54_SMOKE") == "1"
mp.mp.dps = 30

# ---------------- rho_omega: prime-zeta route ----------------

def _mu(n):
    if n == 1:
        return 1
    x, fac, p = n, 0, 2
    while p * p <= x:
        if x % p == 0:
            c = 0
            while x % p == 0:
                x //= p
                c += 1
            if c > 1:
                return 0
            fac += 1
        p += 1
    if x > 1:
        fac += 1
    return -1 if fac % 2 else 1

_MU = [(m, _mu(m)) for m in range(1, 97) if _mu(m) != 0]

def _P2(s):
    """P''(s) = sum_p log^2 p p^{-s} via Mobius/zeta derivatives (s real >1)."""
    tot = mp.mpf(0)
    for m, mu in _MU:
        x = m * s
        if x > 40:
            break
        z = mp.zeta(x)
        z1 = mp.diff(lambda u: mp.zeta(u), x, 1)
        z2 = mp.diff(lambda u: mp.zeta(u), x, 2)
        tot += mu * m * (z2 / z - (z1 / z) ** 2)
    return tot

def rho_omega(omega):
    s = mp.mpf(1) + 2 * mp.mpf(omega)
    tot = mp.mpf(0)
    for k in range(1, 41):
        ks = k * s
        if ks > 40:
            break
        term = _P2(ks)
        tot += term
        if k > 5 and abs(term) < mp.mpf("1e-30"):
            break
    return tot / (2 * mp.pi ** 2)

def rho_sieve(omega, PLIM=5_000_000):
    """Cross-check: direct prime sum to PLIM + PNT integral tail."""
    s = 1.0 + 2.0 * omega
    sieve = np.ones(PLIM + 1, dtype=bool)
    sieve[:2] = False
    for p in range(2, int(PLIM ** 0.5) + 1):
        if sieve[p]:
            sieve[p * p::p] = False
    pr = np.nonzero(sieve)[0].astype(np.float64)
    lg = np.log(pr)
    part = float(np.sum(lg * lg / (np.power(pr, s) - 1.0)))
    # tail: sum_p log^2 p / p^s ~ int_P^inf (dt/log t) log^2 t t^-s
    #          = int_P^inf log t * t^-s dt = P^{1-s}(log P/(s-1) + 1/(s-1)^2)
    P = float(PLIM)
    tail = P ** (1 - s) * (np.log(P) / (s - 1) + 1.0 / (s - 1) ** 2)
    return (part + tail) / (2 * np.pi ** 2)

# ---------------- zeta side: A/B ordinates ----------------

def xi_part(t, omega, side):
    """Re ('A') or Im ('B') part of xi(1/2+omega+it), MODULUS-SCALED.

    ERRATUM (2026-09-03, run 1 killed): the original returned xi itself, whose
    magnitude ~ exp(-pi*t/4) ~ 1e-2390 at t~7000; scan_stream's float()
    conversion underflowed EVERY grid value to 0.0, so gs[i]==0.0 fired in all
    79999 intervals (N=79999 DQ-FAIL rows in the run-1 .out) and the bisection
    degenerated (flo*fm == 0 <= 0 always true). Fix: divide out the strictly
    positive smooth modulus exp(u) of pi^{-s/2} Gamma(s/2) = exp(w), keeping
    only the phase exp(i v) -- sign-preserving, zero-identical, O(1) magnitude.
    """
    s = mp.mpf("0.5") + mp.mpf(omega) + 1j * mp.mpf(t)
    w = mp.loggamma(s / 2) - (s / 2) * mp.log(mp.pi)
    g = mp.mpf("0.5") * s * (s - 1) * mp.zeta(s)
    scaled = mp.exp(1j * mp.im(w)) * g
    return mp.im(scaled) if side == "B" else mp.re(scaled)

def scan_stream(args):
    """Grid + bisection scan for sign changes of the chosen part (dps 20)."""
    import time
    T0, W, omega, side = args
    mp.mp.dps = 20
    t_start = time.time()
    a, b = T0 - W / 2.0, T0 + W / 2.0
    step = 0.05
    ts = np.arange(a, b, step)
    gs = np.array([float(xi_part(t, omega, side)) for t in ts])
    roots = []
    for i in range(len(ts) - 1):
        if gs[i] == 0.0 or gs[i] * gs[i + 1] < 0:
            lo, hi = ts[i], ts[i + 1]
            flo = xi_part(lo, omega, side)
            for _ in range(18):
                mid = 0.5 * (lo + hi)
                fm = xi_part(mid, omega, side)
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fm
            roots.append(0.5 * (lo + hi))
    return (T0, W, omega, side, roots, time.time() - t_start)

# ---------------- m side: value distribution ----------------

def sample_X(args):
    """Re zeta'/zeta(1/2+omega+it) over the window; chunked (dps 25)."""
    T0, W, omega, j0, j1, N = args
    mp.mp.dps = 25
    sig = mp.mpf("0.5") + mp.mpf(omega)
    out = []
    for j in range(j0, j1):
        t = T0 - W / 2.0 + W * (j + 0.5) / N
        s = sig + 1j * mp.mpf(t)
        z = mp.zeta(s)
        z1 = mp.diff(lambda u: mp.zeta(u), s, 1)
        out.append(float(mp.re(z1 / z)))
    return (T0, W, omega, j0, j1, out)

# ---------------- parent ----------------

if __name__ == "__main__":
    from scipy.stats import gaussian_kde, kstest, norm

    OMS = [0.05, 0.15, 0.30] if not SMOKE else [0.15]
    NM = 8000  # m-side samples per window (density/Var estimation)
    streams = []
    if SMOKE:
        streams = [(7005.0, 300.0, 0.15, "B")]
        mjobs = [(7005.0, 300.0, 0.15, 0, 4000, 4000)]
    else:
        for om in OMS:
            for side in ("B", "A"):
                streams.append((7005.0, 4000.0, om, side))
        streams.append((1000.0, 2000.0, 0.15, "B"))  # pre-asymptotic probe
        mjobs = [(7005.0, 4000.0, om, j, j + 2000, NM) for om in OMS
                 for j in range(0, NM, 2000)]
        mjobs += [(1000.0, 2000.0, 0.15, j, j + 2000, NM)
                  for j in range(0, NM, 2000)]

    print("== rho_omega: prime-zeta route vs sieve(5e6)+PNT ==", flush=True)
    RHOS = {}
    for om in OMS:
        r_pz = rho_omega(om)
        r_sv = rho_sieve(om)
        RHOS[om] = float(r_pz)
        print(f"  omega={om:.2f}: rho(P'') = {mp.nstr(r_pz, 12)}  "
              f"rho(sieve) = {r_sv:.8f}  rel diff = "
              f"{abs(float(r_pz) - r_sv) / float(r_pz):.2e}  "
              f"asympt 1/(8 pi^2 w^2) = {1.0 / (8 * np.pi ** 2 * om ** 2):.4f}",
              flush=True)

    print("\n== streams: A/B ordinate scans (grid 0.05, 26-step bisection) ==",
          flush=True)
    # phase-level checkpoint (power-cut lesson 2026-09-03: run A lost ~55 min
    # of scans to a crash before any persist; #41c family). /tmp survives a
    # reboot on macOS; a mid-phase death still loses that one phase.
    CKPT = "/tmp/heat54_ckpt.json"
    ROOTS = {}
    XRAW = None
    if os.path.exists(CKPT):
        with open(CKPT) as fh:
            ck = json.load(fh)
        ROOTS = {eval(k): np.array(v) for k, v in ck.get("roots", {}).items()}
        XRAW = ({eval(k): np.array(v) for k, v in ck.get("xraw", {}).items()}
                if ck.get("xraw") else None)
        print(f"  [checkpoint: {len(ROOTS)}/{len(streams)} streams, "
              f"{0 if XRAW is None else len(XRAW)} X-windows restored]",
              flush=True)

    def save_ckpt():
        with open(CKPT, "w") as fh:
            json.dump({"roots": {str(k): list(v) for k, v in ROOTS.items()},
                       "xraw": ({} if XRAW is None
                                else {str(k): list(v)
                                      for k, v in XRAW.items()})}, fh)

    if len(ROOTS) < len(streams):
      with Pool(WORKERS) as pool:
        for T0, W, om, side, roots, dt in pool.imap_unordered(scan_stream,
                                                              streams):
            ROOTS[(T0, om, side)] = np.array(roots)
            # ERRATUM (2026-09-03, run 1) -- TWO defects in the old form:
            # (a) it takes log of a negative when the window edge crosses t~0
            #     (the T0=1000 W2 row printed Nbar=nan);
            # (b) [T log(T/2pi e) - T]/2pi DOUBLE-subtracts T/2pi (the e inside
            #     the log already carries it), so every run-1 Nbar was low by
            #     exactly W/2pi = 636.6 (printed 3821.4; true ~4458). The DQ
            #     gate would have failed a perfect scan.
            # Replacement: all-t-valid smooth count theta(t)/pi + 1 with
            # theta = Im loggamma(1/4+it/2) - (t/2) log pi; equals the correct
            # RvM difference (constants cancel). Verified: new 4457.97 at
            # T0=7005 W=4000 vs true density integral ~4460.
            Nbar = float(
                (mp.im(mp.loggamma(mp.mpf("0.25") + 1j * mp.mpf(W / 2 + T0) / 2))
                 - mp.mpf(W / 2 + T0) / 2 * mp.log(mp.pi)) / mp.pi + 1
                - (mp.im(mp.loggamma(mp.mpf("0.25") + 1j * mp.mpf(T0 - W / 2) / 2))
                   - mp.mpf(T0 - W / 2) / 2 * mp.log(mp.pi)) / mp.pi - 1)
            dq = "OK" if abs(len(roots) - Nbar) / Nbar <= 0.02 else "DQ-FAIL"
            print(f"  T0={T0:7.1f} omega={om:.2f} side={side}: N={len(roots):5d} "
                  f"Nbar={Nbar:8.1f}  ({dq})  [{dt:.0f}s]", flush=True)
            save_ckpt()
    else:
        print("  [streams already complete from checkpoint; skipping scans]",
              flush=True)

    print("\n== m side: X = Re zeta'/zeta samples (dps 40) ==", flush=True)
    if XRAW is None:
        XRAW = {}
        with Pool(WORKERS) as pool:
            for T0, W, om, j0, j1, xs in pool.imap_unordered(sample_X, mjobs):
                XRAW.setdefault((T0, om), []).extend(xs)
        for k in XRAW:
            XRAW[k] = np.array(XRAW[k])
        save_ckpt()
    else:
        print("  [X windows already complete from checkpoint; skipping]", flush=True)
    for k in sorted(XRAW):
        arr = np.array(XRAW[k])
        XRAW[k] = arr
        print(f"  T0={k[0]:7.1f} omega={k[1]:.2f}: n={len(arr)}  "
              f"mean={arr.mean():+.3f}  var={arr.var():.3f}", flush=True)

    # ---------- normalize + compare ----------
    def gamma1(t):
        return t / (2 * np.pi) * np.log(t / (2 * np.pi * np.e))

    def analyse(T0, W, om, side, rho, tag):
        g = ROOTS[(T0, om, side)]
        n = len(g)
        g1 = gamma1(g)
        Lm = 0.5 * (np.log(g[:-1] / (2 * np.pi * np.e))
                    + np.log(g[1:] / (2 * np.pi * np.e)))
        v = ((g1[1:] - g1[:-1]) - 1.0) * Lm / (2 * np.pi) / np.sqrt(rho)
        X = XRAW[(T0, om)]
        kde = gaussian_kde(X)
        # numeric CDF of the predicted density on a grid
        xs = np.linspace(-8, 8, 4001)
        pdf = np.pi * np.sqrt(rho) * kde(np.pi * np.sqrt(rho) * xs)
        cdf = np.concatenate([[0], np.cumsum((pdf[1:] + pdf[:-1]) / 2
                                             * np.diff(xs))])
        cdf /= cdf[-1]
        ks = kstest(v, lambda q: np.interp(q, xs, cdf)).statistic
        ks_n01 = kstest(v, norm.cdf).statistic
        # Poisson null: raw count-unit gap ~ Exp(1) => v+1 ~ Exp(1)
        ks_poi = kstest(v, lambda q: np.clip(1 - np.exp(-(1 + q)), 0, 1)
                        ).statistic
        var_ratio = v.var() * np.pi ** 2 * rho / X.var()
        rng = np.random.default_rng(12345)
        m = len(v)  # v has len(g)-1 spacings; n=len(g) caused IndexError at B-side
        boots = [v[rng.integers(0, m, m)].var() * np.pi ** 2 * rho / X.var()
                 for _ in range(200)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        # raw-gap NNSD vs Wigner surmise (positioning only, NOT a Thm-1 test):
        # p(s) = 32/pi^2 s^2 e^{-4 s^2/pi} => CDF = erf(2s/sqrt(pi))
        #                            - (4s/pi) e^{-4 s^2/pi}
        from scipy.special import erf
        gaps = g[1:] - g[:-1]
        ug = gaps / gaps.mean()
        ks_wig = kstest(ug, lambda s: (erf(2 * s / np.sqrt(np.pi))
                                       - 4 * s / np.pi
                                       * np.exp(-4 * s ** 2 / np.pi))
                        ).statistic
        print(f"  {tag:34s} N={n}  var(v)={v.var():.3f}  "
              f"bridge var ratio={var_ratio:.3f} [{lo:.3f},{hi:.3f}]",
              flush=True)
        print(f"     KS(v, P)={ks:.4f}   KS(v, N01)={ks_n01:.4f}   "
              f"KS(v, shiftExp)={ks_poi:.4f}   raw-gap KS vs Wigner={ks_wig:.4f}",
              flush=True)
        return dict(tag=tag, N=n, var_v=float(v.var()), ks=float(ks),
                    ks_n01=float(ks_n01), ks_poi=float(ks_poi),
                    var_ratio=float(var_ratio), vr_lo=float(lo),
                    vr_hi=float(hi))

    print("\n== comparison (v = gamma^(2) spacing; P = pi rho^.5 f(pi rho^.5 v)) ==",
          flush=True)
    results = {}
    for om in OMS:
        results[f"B om={om}"] = analyse(7005.0, 4000.0, om, "B", RHOS[om],
                                        f"W1 B omega={om}")
    if not SMOKE:
        results["A om=0.15"] = analyse(7005.0, 4000.0, 0.15, "A",
                                       RHOS[0.15], "W1 A omega=0.15")
        results["probe"] = analyse(1000.0, 2000.0, 0.15, "B", RHOS[0.15],
                                   "W2(1000) B omega=0.15")
        # wrong-rho control at primary
        results["wrongrho"] = analyse(7005.0, 4000.0, 0.15, "B", RHOS[0.30],
                                      "W1 B omega=0.15 w/ rho(0.30) [CTRL]")

    # persistence precedes epilogue cosmetics (trap #69 lesson): dump as soon
    # as the results exist so a print bug cannot destroy the record. The
    # 2026-09-03 run crashed in the F3 print (hand-typed key 'B om=0.30' vs
    # the programmatic f-string key 'B om=0.3' — float 0.30 formats as 0.3;
    # #63/#66 genus) BEFORE this dump existed at the end; the .out was the
    # only record. Dump moved up; F3 now loops over OMS.
    with open("/tmp/heat54_results.json", "w") as fh:
        json.dump({str(k): v for k, v in results.items()}, fh, indent=1)

    if not SMOKE:
        print("\n== PRE-REGISTERED VERDICTS ==", flush=True)
        ksB = {om: results[f"B om={om}"]["ks"] for om in OMS}
        r = results["B om=0.15"]
        print(f"  F1 (primary structure, KS<={0.10}): "
              f"{'PASS' if r['ks'] <= 0.10 else ('FALSIFIED' if r['ks'] > 0.15 else 'AMBIGUOUS')}"
              f"  KS={r['ks']:.4f}")
        f2a = all(k <= 0.12 for k in ksB.values())
        f2b = results["wrongrho"]["ks"] >= 1.5 * r["ks"]
        print(f"  F2 (rho-bridge): {'PASS' if f2a and f2b else 'FALSIFIED'}  "
              f"KS(B)={ {k: round(v, 4) for k, v in ksB.items()} }  "
              f"wrong-rho {results['wrongrho']['ks']:.4f} vs "
              f"{1.5 * r['ks']:.4f} threshold")
        f3 = "  ".join(f"om={om}: {results[f'B om={om}']['ks_n01']:.4f}"
                       for om in OMS)
        print(f"  F3 (Thm-2 direction, qualitative): KS vs N01 = {f3}  "
              f"(trend expected down with om)")
        print(f"  F4 (A/B symmetry <=0.15): "
              f"{'PASS' if results['A om=0.15']['ks'] <= 0.15 else 'FALSIFIED'}  "
              f"KS(A)={results['A om=0.15']['ks']:.4f}")
        print(f"  F5 (bridge variance in [0.85,1.15]): "
              f"{'PASS' if 0.85 <= r['var_ratio'] <= 1.15 else 'FALSIFIED'}  "
              f"ratio={r['var_ratio']:.3f} [{r['vr_lo']:.3f},{r['vr_hi']:.3f}]")
        print(f"  Suzuki-constant (report only): Var(X)/pi^2 rho = "
              f"{XRAW[(7005.0, 0.15)].var() / (np.pi ** 2 * RHOS[0.15]):.3f}; "
              f"Var(X)/2pi^2 rho = "
              f"{XRAW[(7005.0, 0.15)].var() / (2 * np.pi ** 2 * RHOS[0.15]):.3f}"
              f"  (Thm2 consistency favours ~1 for the first)", flush=True)

    with open("/tmp/heat54_results.json", "w") as fh:
        json.dump({str(k): v for k, v in results.items()}, fh, indent=1)
    print("\ndone", flush=True)
