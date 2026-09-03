"""heat61 W(f) search — the negative-cell evolutionary search (M4).

Runs ONLY after gate G0 PASSED (heat61_g0_balance.py at grid 2^23; closed-form
verification heat61b at 4e-15; verdict block in heat61_g0_grid23.out).

Pre-registration: m4_w_search_design.md (SHA-256
88b4a374eca8327c9ab14090b612b91fe2d96c01fa68cb1b4c436d8ba9b323be, committed
before any scored evaluation). Protocol per design section 5:

  L-A Gaussian mixture: f = Sum_{j<=J} c_j exp(-(x-mu_j)^2/2 sigma_j^2) * win,
      J <= 8, elitist selection, sigma-scaled Gaussian mutation steps.
  L-B prolate/band-limited: sinc pairs, mutations on bandwidth c and centers.
  L-C mollifier: gh(s) = P(s) P(1-s) w(s), P = truncated Dirichlet-type
      polynomial (<= 6 terms a_i p_i^{-s}, primes among first 20), w a fixed
      Paley-Wiener window; realized by inverse Mellin on the search grid, then
      x-windowed into the compact class.
  Population 24 per lineage, 200 generations, best-individual migration every
  25 generations. Fitness = Q(g) via the PRIME side (zero-free). G1 admissibility:
  support width >= 4 (automatic: window |x|<=8), ||f||_2 = 1.
  Search grid 2^19 with halt-confirmation at 2^21 (run-3 configuration; see the
  D7 note at the NGRID definition for why 2^17 was abandoned mid-run-2).
  Halt-and-verify: any confirmed Q < -eps_cert (1e-3)
  => FREEZE the individual, recompute on the ZERO side at grid 2^23, and post to
  the exchange for counterparty re-derivation BEFORE any claim language.

Conventions certified by G0 (Burnol math/9810169):
  Q(g) = 2 gh(0) gh(1) - [ Sum_p W_p(h) + 2 V_r(h) ],  h = g * g^tau,
  W_p(h) = log p Sum_k [ h(k L) + e^{-k L} h(-k L) ],  L = log p,
  V_r(h) = (log pi + gamma)/2 h(0) + Int_0^16 h dx + Int_0^16 (h-h(0))/(e^{2x}-1) dx.
"""
import json
import os
import sys
import time

import numpy as np

rng = np.random.default_rng(20260903)

# ---------------- instrument (shared with G0, verified there) ----------------
CUT_IN, CUT_OUT = 6.0, 8.0
LGRID = 24.0
# Search grid 2^19 (run-2 change): run-1/2 at 2^17 showed the L-B class carries
# a systematic ~-1.5e-3 V_r error at 2^17 (measured 2^19: ~1e-4; 2^21: ~5e-6) —
# selection was partially chasing instrument error. At 2^19 the class error sits
# ~10x below eps_cert and ~1x below typical |Q| (~1e-4): honest exploration.
NGRID = 1 << int(os.environ.get("W_SEARCH_GRID_LOG2", "19"))
CONFIRM_LOG2 = int(os.environ.get("W_CONFIRM_GRID_LOG2", "21"))
DX = 2 * LGRID / NGRID
XS = -LGRID + DX * np.arange(NGRID)
EPS_CERT = 1e-3

def _theta(s):
    s = np.asarray(s, dtype=float)
    out = np.zeros_like(s)
    lo = s <= 0.0
    hi = s >= 1.0
    mid = ~(lo | hi)
    with np.errstate(over="ignore"):
        e = np.exp(-1.0 / s[mid])
        e2 = np.exp(-1.0 / (1.0 - s[mid]))
    out[mid] = e / (e + e2)
    out[hi] = 1.0
    return out

def window(x):
    return _theta((CUT_OUT - np.abs(x)) / (CUT_OUT - CUT_IN))

def trapz_grid(y):
    return DX * (y.sum() - 0.5 * (y[0] + y[-1]))

def build_h(f):
    A = f * np.exp(XS)
    n2 = 2 * NGRID
    corr = np.fft.irfft(np.fft.rfft(A, n2) * np.conj(np.fft.rfft(f, n2)), n2)
    m_from = int(np.floor(-20 / DX))
    m_to = int(np.ceil(20 / DX))
    ms = np.arange(m_from, m_to + 1)
    Cvals = DX * corr[ms % n2]
    xs_out = ms * DX
    return xs_out, np.exp(-xs_out) * Cvals

def lagrange8(xs_grid, ys_grid, xq):
    xq = np.atleast_1d(np.asarray(xq, dtype=float))
    n = len(xs_grid)
    j0 = np.clip(np.searchsorted(xs_grid, xq) - 4, 0, n - 8)
    out = np.zeros_like(xq)
    for i in range(8):
        w = np.ones_like(xq)
        for j in range(8):
            if i != j:
                w *= (xq - xs_grid[j0 + j]) / (xs_grid[j0 + i] - xs_grid[j0 + j])
        out += w * ys_grid[j0 + i]
    return out

def sieve_primes(nmax):
    s = np.ones(nmax + 1, dtype=bool)
    s[:2] = False
    for i in range(2, int(nmax ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = False
    return np.nonzero(s)[0]

PMAX = int(np.exp(16.0)) + 2
PRIMES = sieve_primes(PMAX)
LOGP = np.log(PRIMES.astype(float))
KMAX = np.floor(16.0 / LOGP).astype(int)

def Q_prime(f):
    """Prime-side Q for a grid-sampled f (np array on XS). Returns (Q, parts)."""
    g0 = trapz_grid(f)
    g1 = trapz_grid(f * np.exp(XS))
    hx, hgrid = build_h(f)
    def H(xq):
        return lagrange8(hx, hgrid, xq)
    terms = np.zeros(len(PRIMES))
    for k in range(1, int(KMAX.max()) + 1):
        active = KMAX >= k
        if not active.any():
            continue
        xa = k * LOGP[active]
        terms[active] += H(xa)
        terms[active] += np.exp(-xa) * H(-xa)
    sump = float(np.sum(LOGP * terms))
    h0 = H(0.0)[0]
    c0 = (np.log(np.pi) + np.euler_gamma) / 2 * h0
    m = (XS >= 0) & (XS <= 16.0)
    xm = XS[m]
    hm = H(xm)
    i1 = trapz_grid(hm)
    integ2 = (hm - h0) / (np.exp(2 * xm) - 1)
    xm0 = np.abs(xm) < 10 * DX
    if xm0.any():
        integ2[xm0] = -h0 / 4          # h'(0)/2, exact by tau-invariance
    i2 = trapz_grid(integ2)
    Q = 2 * g0 * g1 - (sump + 2 * (c0 + i1 + i2))
    return Q, dict(g0=g0, g1=g1, sump=sump, c0=c0, i1=i1, i2=i2)

# ---------------- lineage parametrizations ----------------
def f_of_LA(genome):
    """genome: (J, [c_j, mu_j, sigma_j]*J)."""
    J = genome["J"]
    f = np.zeros_like(XS)
    for j in range(J):
        c, mu, sg = genome["terms"][j]
        f += c * np.exp(-((XS - mu) ** 2) / (2 * sg * sg))
    f = f * window(XS)
    nrm = np.sqrt(trapz_grid(f * f))
    return f / max(nrm, 1e-300)

def f_of_LB(genome):
    """genome: K sinc pairs, mutations on bandwidth c and centers."""
    f = np.zeros_like(XS)
    c = genome["c"]
    for ctr, amp in genome["pairs"]:
        t = XS - ctr
        f += amp * np.where(np.abs(t) > 1e-10, np.sin(c * t) / (np.pi * t), c / np.pi)
    f = f * window(XS)
    nrm = np.sqrt(trapz_grid(f * f))
    return f / max(nrm, 1e-300)

# L-C: gh(s) = P(s)P(1-s)w(s) with P(s) = sum_i a_i p_i^{-s}; realize f by
# inverse Mellin along Re s = 1/2: f(x) = e^{-x/2} (1/2pi) Int gh(1/2+it) e^{-itx} dt.
# FFT identity (SELF-TESTED at startup, not trusted): with t_k = -T + k DT,
# DT = 2T/NT, the inverse FT at x_n = n pi/T is
#   (1/2pi) Sum_k gh_k e^{-i t_k x_n} = (DT/2pi) (-1)^n fft(gh)_n,
# valid because e^{i T x_n} = e^{i pi n} = (-1)^n exactly.
TMAX = 200.0
NT = 1 << 14
DT = 2 * TMAX / NT
TS = -TMAX + DT * np.arange(NT)
DXX = np.pi / TMAX                    # x-sample spacing of the realized f
_xraw = np.arange(NT) * DXX           # covers [0, NT*pi/T), period NT*pi/T ~ 257
XQ_ORDER = np.argsort(np.where(_xraw >= NT * DXX / 2, _xraw - NT * DXX, _xraw))
XQ_SORTED = np.sort(np.where(_xraw >= NT * DXX / 2, _xraw - NT * DXX, _xraw))
def _realize_f(gh):
    F = np.fft.fft(gh) * (DT / (2 * np.pi)) * ((-1.0) ** np.arange(NT))
    return np.interp(XS, XQ_SORTED, F.real[XQ_ORDER])

def f_of_LC(genome):
    w_t = _theta((TMAX - np.abs(TS)) / (TMAX / 4))   # flat window in t
    P = np.zeros(NT, dtype=complex)
    for a, p in genome["terms"]:
        P += a * np.exp(-(0.5 + 1j * TS) * np.log(p))
    gh = P * np.conj(P) * w_t                        # P(s) conj-P = P(s)P(1-s) on the line
    f = np.exp(-XS / 2) * _realize_f(gh)
    f = f * window(XS)
    nrm = np.sqrt(trapz_grid(f * f))
    return f / max(nrm, 1e-300)

def lc_selftest():
    """Known pair: gh(1/2+it) = e^{-t^2}  =>  g(e^x) = e^{-x/2} e^{-x^2/4}/(2 sqrt(pi))."""
    raw = _realize_f(np.exp(-TS ** 2))
    expect = np.exp(-XS ** 2 / 4) / (2 * np.sqrt(np.pi))
    return float(np.max(np.abs(raw - expect)))

def make_LA(rng):
    J = int(rng.integers(1, 9))
    return {"J": J, "terms": [[float(rng.normal(0, 1)), float(rng.uniform(-5, 5)),
                               float(rng.uniform(0.3, 2.5))] for _ in range(J)]}

def make_LB(rng):
    K = int(rng.integers(1, 5))
    return {"c": float(rng.uniform(1, 8)),
            "pairs": [[float(rng.uniform(-4, 4)), float(rng.normal(0, 1))] for _ in range(K)]}

FIRST20 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
def make_LC(rng):
    n = int(rng.integers(1, 7))
    idx = rng.choice(20, size=n, replace=False)
    return {"terms": [[float(rng.normal(0, 1)), FIRST20[i]] for i in idx]}

def mutate(genome, lineage, rng):
    g = json.loads(json.dumps(genome))
    if lineage == "LA":
        for t in g["terms"]:
            if rng.random() < 0.5:
                t[0] += float(rng.normal(0, 0.3))
            if rng.random() < 0.3:
                t[1] += float(rng.normal(0, 0.5))
            if rng.random() < 0.3:
                t[2] = float(np.clip(t[2] + rng.normal(0, 0.2), 0.15, 4.0))
        if rng.random() < 0.1 and g["J"] < 8:
            g["J"] += 1
            g["terms"].append([float(rng.normal(0, 0.5)), float(rng.uniform(-5, 5)),
                               float(rng.uniform(0.3, 2.5))])
        if rng.random() < 0.1 and g["J"] > 1:
            g["J"] -= 1
            g["terms"].pop(int(rng.integers(0, g["J"])))
    elif lineage == "LB":
        if rng.random() < 0.4:
            g["c"] = float(np.clip(g["c"] + rng.normal(0, 0.5), 0.5, 12.0))
        for pr in g["pairs"]:
            if rng.random() < 0.4:
                pr[0] += float(rng.normal(0, 0.5))
            if rng.random() < 0.3:
                pr[1] += float(rng.normal(0, 0.3))
    else:
        for t in g["terms"]:
            if rng.random() < 0.5:
                t[0] += float(rng.normal(0, 0.3))
        if rng.random() < 0.15 and len(g["terms"]) < 6:
            i = int(rng.integers(0, 20))
            if all(p != FIRST20[i] for _, p in g["terms"]):
                g["terms"].append([float(rng.normal(0, 0.5)), FIRST20[i]])
        if rng.random() < 0.15 and len(g["terms"]) > 1:
            g["terms"].pop(int(rng.integers(0, len(g["terms"]))))
    return g

F_OF = {"LA": f_of_LA, "LB": f_of_LB, "LC": f_of_LC}
MAKE = {"LA": make_LA, "LB": make_LB, "LC": make_LC}

# ---------------- two-grid halt confirmation (post heat61c disclosure D7) ----------------
# The first halt (LB gen 2, Q(2^17) = -1.389e-3) was a GRID ARTIFACT: ladder
# 2^17/19/21/23 gave -1.389e-3 / -4.74e-5 / +3.67e-5 / +4.19e-5 with the zero
# side at 2^23 agreeing (+4.230e-5, T-saturated). The G0-calibrated 2^17 floor
# (~5e-6, Gaussian-class) does NOT transfer to oscillatory L-B genomes: their
# measured 2^17 V_r error is ~1.4e-3 (2^19: ~9e-5). New halt rule: freeze only
# if Q < -eps_cert at BOTH 2^17 and 2^19; single-grid sub-threshold events are
# logged as drift-rejects (territory data on the instrument floor by class).
PRIMES_C = PRIMES
LOGP_C = LOGP
KMAX_C = KMAX

def prime_side_genome(lineage, genome, grid_log2):
    LGRID = 24.0
    N = 1 << grid_log2
    dx = 2 * LGRID / N
    xs = -LGRID + dx * np.arange(N)
    win = window(xs)
    if lineage == "LA":
        f = np.zeros_like(xs)
        for c, mu, sg in genome["terms"]:
            f += c * np.exp(-((xs - mu) ** 2) / (2 * sg * sg))
    elif lineage == "LB":
        f = np.zeros_like(xs)
        cc = genome["c"]
        for ctr, amp in genome["pairs"]:
            t = xs - ctr
            f += amp * np.where(np.abs(t) > 1e-10,
                                np.sin(cc * t) / (np.pi * np.where(np.abs(t) > 1e-10, t, 1.0)),
                                cc / np.pi)
    else:
        P = np.zeros(NT, dtype=complex)
        for a, p in genome["terms"]:
            P += a * np.exp(-(0.5 + 1j * TS_C) * np.log(p))
        gh = P * np.conj(P) * _theta((TMAX - np.abs(TS_C)) / (TMAX / 4))
        f = np.exp(-xs / 2) * _realize_f_on(gh, xs)
    f = f * win
    nrm = np.sqrt(dx * (f * f).sum())
    f = f / max(nrm, 1e-300)
    g0 = dx * (f.sum() - 0.5 * (f[0] + f[-1]))
    fw = f * np.exp(xs)
    g1 = dx * (fw.sum() - 0.5 * (fw[0] + fw[-1]))
    A = f * np.exp(xs)
    n2 = 2 * N
    corr = np.fft.irfft(np.fft.rfft(A, n2) * np.conj(np.fft.rfft(f, n2)), n2)
    ms = np.arange(int(np.floor(-20 / dx)), int(np.ceil(20 / dx)) + 1)
    hx = ms * dx
    hgrid = np.exp(-hx) * dx * corr[ms % n2]
    terms = np.zeros(len(PRIMES_C))
    for k in range(1, int(KMAX_C.max()) + 1):
        active = KMAX_C >= k
        if not active.any():
            continue
        xa = k * LOGP_C[active]
        terms[active] += lagrange8(hx, hgrid, xa)
        terms[active] += np.exp(-xa) * lagrange8(hx, hgrid, -xa)
    sump = float(np.sum(LOGP_C * terms))
    h0 = lagrange8(hx, hgrid, 0.0)[0]
    c0 = (np.log(np.pi) + np.euler_gamma) / 2 * h0
    m = (xs >= 0) & (xs <= 16.0)
    xm = xs[m]
    hm = lagrange8(hx, hgrid, xm)
    i1 = dx * (hm.sum() - 0.5 * (hm[0] + hm[-1]))
    with np.errstate(invalid="ignore", divide="ignore"):
        integ2 = (hm - h0) / np.expm1(2 * xm)
    integ2[np.abs(xm) < 10 * dx] = -h0 / 4
    i2 = dx * (integ2.sum() - 0.5 * (integ2[0] + integ2[-1]))
    return 2 * g0 * g1 - (sump + 2 * (c0 + i1 + i2))

# realization onto an arbitrary x-grid (L-C confirm at 2^19)
TS_C = TS
def _realize_f_on(gh, xs):
    F = np.fft.fft(gh) * (DT / (2 * np.pi)) * ((-1.0) ** np.arange(NT))
    return np.interp(xs, XQ_SORTED, F.real[XQ_ORDER])

# ---------------- evolution ----------------
POP, GENS, MIG_EVERY = 24, 200, 25

def run():
    log = []
    frozen = []
    drift_rejects = []
    populations = {L: [MAKE[L](rng) for _ in range(POP)] for L in F_OF}
    fitness = {L: [np.inf] * POP for L in F_OF}
    t0 = time.time()
    for gen in range(1, GENS + 1):
        for L in F_OF:
            # evaluate
            for i, g in enumerate(populations[L]):
                try:
                    Q, _ = Q_prime(F_OF[L](g))
                    if Q < -EPS_CERT:
                        # two-grid confirmation (heat61c disclosure D7)
                        Qc = prime_side_genome(L, g, CONFIRM_LOG2)
                        if Qc < -EPS_CERT:
                            frozen.append(dict(lineage=L, gen=gen, genome=g,
                                               Q_search=Q, Q_confirm=Qc,
                                               confirm_log2=CONFIRM_LOG2))
                            print(f"  !! HALT-AND-VERIFY CONFIRMED: {L} gen {gen} "
                                  f"Q({NGRID.bit_length()-1}^2-grid)={Q:.3e} "
                                  f"Q(2^{CONFIRM_LOG2})={Qc:.3e}", flush=True)
                        else:
                            drift_rejects.append(dict(lineage=L, gen=gen,
                                                      Q_search=Q, Q_confirm=Qc,
                                                      drift=Qc - Q))
                            print(f"  ~~ drift-reject: {L} gen {gen} Q_search={Q:.3e} "
                                  f"-> Q(2^{CONFIRM_LOG2})={Qc:.3e} (grid artifact, logged)",
                                  flush=True)
                            Q = Qc
                    fitness[L][i] = Q
                except Exception:
                    fitness[L][i] = np.inf
            # elitist selection: keep best half, mutate copies
            order = np.argsort(fitness[L])
            keep = [populations[L][i] for i in order[:POP // 2]]
            newpop = list(keep)
            while len(newpop) < POP:
                newpop.append(mutate(keep[int(rng.integers(0, len(keep)))], L, rng))
            populations[L] = newpop
        if gen % MIG_EVERY == 0:
            Ls = list(F_OF)
            bests = {L: min(zip(fitness[L], populations[L]), key=lambda t: t[0]) for L in Ls}
            for Lsrc in Ls:
                Ldst = Ls[(Ls.index(Lsrc) + 1) % len(Ls)]
                populations[Ldst][int(rng.integers(0, POP))] = json.loads(json.dumps(bests[Lsrc][1]))
        if gen % 5 == 0 or gen == 1:
            stat = {L: float(np.min(fitness[L])) for L in F_OF}
            log.append(dict(gen=gen, **stat))
            print(f"  gen {gen:3d}  " + "  ".join(f"{L}: {v:+.4e}" for L, v in stat.items())
                  + f"   [{time.time()-t0:.0f}s]", flush=True)
            with open("heat61_w_search.log.json", "w") as fh:
                json.dump(dict(log=log, frozen=frozen, drift_rejects=drift_rejects), fh, indent=1)
        if frozen:
            break
    print("== search complete ==")
    print(f"  generations run: {gen}; frozen candidates: {len(frozen)}")
    for L in F_OF:
        best = min(zip(fitness[L], populations[L]), key=lambda t: t[0])
        print(f"  {L} min-Q all-time: {np.min([e[0] for e in zip(fitness[L])]):+.4e}")
    with open("heat61_w_search.log.json", "w") as fh:
        json.dump(dict(log=log, frozen=frozen,
                       final={L: min(zip(fitness[L], [json.dumps(g) for g in populations[L]]))
                              for L in F_OF}), fh, indent=1)
    if frozen:
        print("FROZEN — halt-and-verify protocol engaged; NO claim language until zero-side + counterparty.")

if __name__ == "__main__":
    err = lc_selftest()
    print(f"   L-C inverse-FFT self-test (pair e^{{-t^2}} -> e^{{-x^2/4}}/2sqrt(pi)): "
          f"max abs err {err:.2e}")
    # gate 1e-4: the realization grid (DXX = pi/200) has a linear-interp floor
    # (DXX^2/8)|f''| ~ 4.3e-6 for the Gaussian pair (measured); a convention or
    # index error in the FFT identity shows up at O(0.1+), 4+ orders above gate.
    if err > 1e-4:
        print("   SELF-TEST FAIL — aborting before any scored evaluation.")
        sys.exit(1)
    print("== heat61 W(f) negative-cell search (post-G0-PASS) ==")
    print(f"   grid 2^{NGRID.bit_length()-1}, primes to e^16, eps_cert {EPS_CERT}")
    print(f"   population {POP} x 3 lineages x {GENS} generations, migration /{MIG_EVERY}")
    run()
