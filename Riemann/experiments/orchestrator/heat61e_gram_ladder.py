"""heat61e — Rayleigh–Ritz Gram ladder over the run-3 winner spans (forced mutation,
Glenn directive 2026-09-03; renamed from "heat62 first act" — erratum NOTES 88k).

WHAT: K[i,j] = B(phi_i, phi_j), the polarized Weil quadratic form
  Q(f) = 2 g0 g1 - [Sum_p W_p(h) + 2 V_r(h)],  h = f * f^tau
over an orthonormalized basis {psi_i} spanning (run-3 lineage winner + its
deterministic mutants). lambda_min(K) = the EXACT constrained minimum of Q over
that span at ||f||_2 = 1 — the GA search was a stochastic lambda_min estimator;
this replaces sampling with one eigenvalue per level.

INSTRUMENTS (two, disjoint — machine-3 Letter 42/44 constraints adopted):
  PRIMARY  zero side:  K_z[i,j] = Sum_{rho upper, Im<T} 2 Re[gh_i(rho) gh_j(1-rho)]
            (gh_j(1-rho) = conj gh_j(rho) for real f), T = 100/150/200 saturation.
  DISJOINT prime side: K_p[i,j] = [Q(f_i+f_j) - Q(f_i) - Q(f_j)] / 2, every Q from
            the G0-certified grid instrument (heat61_w_search.prime_side_genome
            post-realization block, copied verbatim per grid). NO hand-derived
            polarization of W_p/V_r (traps #36/#63): only the certified evaluator
            and the algebraic identity Q(x+y)-Q(x)-Q(y) = 2B(x,y).
  Basis psi built at 2^23, down-sampled by interp to 2^21 (same psi, two grids —
  the entry-stability gate must not conflate grid refinement with basis shift).

PRECISION BUDGET (Letter 42, adopted as hard gates — drift-reject discipline moved
from the GA generation loop into the deterministic instrument):
  GATE-E entry stability: |K_p(2^23)[i,j] - K_p(2^21)[i,j]| <= max(2e-5, 0.2|K23|)
            per entry (run-3 demonstrated cross-grid Q agreement 4.0e-6 LA /
            4.2e-5 LB; entries inherit the class floor).
  GATE-Z prime/zero agreement: |K_p - K_z| <= max(5e-5, 0.3 |K_z|) per entry at
            T = 200 (zero side must also be T-saturated: last |term| reported).
  GATE-S symmetry: max|K - K^T| <= 1e-6 * max|K| (float64 noise check).
  Machine-3's "two dps levels" maps onto TWO GRID LEVELS + the mpmath zero side
  (the prime instrument is float64 numpy; its precision axis IS the grid).

PRE-REGISTRATION (trap #32; written before any scored evaluation):
  Expected: lambda_min > 0 over all three spans (consistent with RH + run-3
  outcome (a)); magnitude ~1e-5..1e-4, at or below the winners' certified true Q
  (LA +6.2e-5, LB +1.5e-4, LC +0.26) since each winner is IN its span.
  Outcomes (NOTES 88f discipline):
   (a) lambda_min > 0 at 2^23 AND zero side, all gates pass
       -> span CERTIFIED positive; ladder validated; scale M next (route-1
          deterministic upgrade).
   (b) lambda_min < 0 on BOTH instruments beyond the combined gate floors
       -> FREEZE, zero-side certify at dps 50, exchange relay BEFORE any claim
          language (W-search halt rule inherited). This is route-1 negative.
   (c) gates fail / drift in between -> instrument-floor result (D7 class),
       no RH content claimed, floors remeasured per class.
  Falsifiers for the INSTRUMENT itself:
   F-E: any entry failing GATE-E is drift-rejected (reported, excluded from the
        certificate, counted).
   F-Z: prime/zero systematic offset beyond GATE-Z on > 1/4 of entries -> run
        DQ'd, outcome (c).
  Circularity label (trap #34): this sits on the RH-CONSISTENCY side —
  lambda_min > 0 is consistent-with, never evidence-for; only outcome (b)
  would be mathematical content (against RH).

Basis determinism: winner genomes PARSED from heat61_w_search.log.json (never
hand-copied, #63); mutants = H.mutate(winner, lineage, rng(seed 20260903+i))
— reproducible bit-for-bit from this file + the log.
"""
import json
import os
import sys

import numpy as np

import heat61_w_search as H

SMOKE = os.environ.get("HEAT61E_SMOKE") == "1"
M_BASIS = 4 if SMOKE else 8
GRIDS = (19, 21) if SMOKE else (21, 23)
T_LIST = (100.0,) if SMOKE else (100.0, 150.0, 200.0)
LGRID = 24.0
OUTSTEM = "heat61e_gram_ladder"


# ---------- certified prime-side Q on an arbitrary (xs, f) — verbatim ----------
def Q_grid(xs, dx, f):
    """heat61_w_search.prime_side_genome lines 292-320, with (xs, dx, f) given."""
    g0 = dx * (f.sum() - 0.5 * (f[0] + f[-1]))
    fw = f * np.exp(xs)
    g1 = dx * (fw.sum() - 0.5 * (fw[0] + fw[-1]))
    A = f * np.exp(xs)
    n2 = 2 * len(f)
    corr = np.fft.irfft(np.fft.rfft(A, n2) * np.conj(np.fft.rfft(f, n2)), n2)
    ms = np.arange(int(np.floor(-20 / dx)), int(np.ceil(20 / dx)) + 1)
    hx = ms * dx
    hgrid = np.exp(-hx) * dx * corr[ms % n2]
    terms = np.zeros(len(H.PRIMES_C))
    for k in range(1, int(H.KMAX_C.max()) + 1):
        active = H.KMAX_C >= k
        if not active.any():
            continue
        xa = k * H.LOGP_C[active]
        terms[active] += H.lagrange8(hx, hgrid, xa)
        terms[active] += np.exp(-xa) * H.lagrange8(hx, hgrid, -xa)
    sump = float(np.sum(H.LOGP_C * terms))
    h0 = H.lagrange8(hx, hgrid, 0.0)[0]
    c0 = (np.log(np.pi) + np.euler_gamma) / 2 * h0
    m = (xs >= 0) & (xs <= 16.0)
    xm = xs[m]
    hm = H.lagrange8(hx, hgrid, xm)
    i1 = dx * (hm.sum() - 0.5 * (hm[0] + hm[-1]))
    with np.errstate(invalid="ignore", divide="ignore"):
        integ2 = (hm - h0) / np.expm1(2 * xm)
    integ2[np.abs(xm) < 10 * dx] = -h0 / 4
    i2 = dx * (integ2.sum() - 0.5 * (integ2[0] + integ2[-1]))
    return 2 * g0 * g1 - (sump + 2 * (c0 + i1 + i2))


def realize(lineage, genome, xs):
    """Mirror of prime_side_genome realization lines (no window/normalise)."""
    if lineage == "LA":
        f = np.zeros_like(xs)
        for c, mu, sg in genome["terms"]:
            f += c * np.exp(-((xs - mu) ** 2) / (2 * sg * sg))
    elif lineage == "LB":
        f = np.zeros_like(xs)
        cc = genome["c"]
        for ctr, amp in genome["pairs"]:
            t = xs - ctr
            safe = np.abs(t) > 1e-10
            f += amp * np.where(safe, np.sin(cc * t) / (np.pi * np.where(safe, t, 1.0)),
                                cc / np.pi)
    else:
        P = np.zeros(H.NT, dtype=complex)
        for a, p in genome["terms"]:
            P += a * np.exp(-(0.5 + 1j * H.TS_C) * np.log(p))
        gh = P * np.conj(P) * H._theta((H.TMAX - np.abs(H.TS_C)) / (H.TMAX / 4))
        f = np.exp(-xs / 2) * H._realize_f_on(gh, xs)
    return f * H.window(xs)


def gram_schmidt(F, dx):
    """Orthonormalize rows of F (M x N) in the trapz L2 inner product.

    SMOKE LESSON (2026-09-03, first fire): on a near-parallel basis (winner +
    mild mutants, pairwise corr ~0.999) this MANUFACTURES noise directions —
    later psi are float64 cancellation remainders, Q(psi) ~ 1e3 garbage, and
    the eigenvalue GROWS with the grid (smoke LA lambda_max 1.9e2 -> 2.5e3).
    Guarded by diverse-mutant selection below + the lambda-growth DQ; the
    certificate path uses the generalized eigenproblem instead, which never
    builds orthogonal complements."""
    Psi = np.zeros_like(F)
    for i in range(len(F)):
        v = F[i].copy()
        for j in range(i):
            v -= (dx * (v * Psi[j]).sum()) * Psi[j]
        Psi[i] = v / np.sqrt(dx * (v * v).sum())
    return Psi


def diverse_mutants(lineage, winner, xs, dx, m_basis):
    """Winner + mutants accepted only if max |corr| with accepted basis < 0.98.
    Each candidate = two chained mutate() steps (bigger jumps than the search's
    single step; the smoke showed single steps give corr~0.999 degeneracy)."""
    basis_f = [realize(lineage, winner, xs)]
    basis_g = [winner]
    rng = np.random.default_rng(20260903)
    tries = 0
    while len(basis_f) < m_basis and tries < 200:
        tries += 1
        g = H.mutate(winner, lineage, rng)
        g = H.mutate(g, lineage, rng)
        f = realize(lineage, g, xs)
        nr = np.sqrt(dx * (f * f).sum())
        if nr < 1e-12:
            continue
        f = f / nr
        ok = True
        for fb in basis_f:
            if abs(dx * (f * fb).sum()) > 0.98:
                ok = False
                break
        if ok:
            basis_f.append(f)
            basis_g.append(g)
    return basis_g, np.array(basis_f)


def zero_side_gram(Psi, xs, dx, T):
    """K_z[i,j] = Sum_{rho upper, Im<T} 2 Re[gh_i(rho) gh_j(1-rho)]."""
    import mpmath as mp
    mp.mp.dps = 30
    n, K = 1, np.zeros((len(Psi), len(Psi)))
    last = 0.0
    while True:
        z = mp.zetazero(n)
        if z.imag > T:
            break
        rho = complex(z)
        w = np.exp(rho * xs)          # gh_i(rho) = dx * Psi[i] . w
        u = Psi @ w * dx              # gh_i(1-rho) = conj(u_i) for real f
        K += 2.0 * np.outer(u, u.conj()).real
        last = float(np.abs(u).max() ** 2)
        n += 1
    return K, n - 1, last


if __name__ == "__main__":
    with open("heat61_w_search.log.json") as fh:
        REC = json.load(fh)
    winners = {L: json.loads(blob) for L, pair in REC["final"].items()
               for blob in [pair[1]]}

    report = {}
    for L in ("LA", "LB", "LC"):
        print(f"\n===== {L}: basis = winner + diverse mutants (generalized eig) =====",
              flush=True)
        xs23 = -LGRID + (2 * LGRID / (1 << 23)) * np.arange(1 << 23)
        genomes, F = diverse_mutants(L, winners[L], xs23,
                                     2 * LGRID / (1 << 23), M_BASIS)
        m = len(F)
        print(f"  basis size {m} (of {M_BASIS} requested), winner included",
              flush=True)
        res = {"M": m, "genomes": genomes}

        for gl in GRIDS:
            N = 1 << gl
            dx = 2 * LGRID / N
            xs = -LGRID + dx * np.arange(N)
            P = np.array([np.interp(xs, xs23, F[i]) for i in range(m)])
            P = P / np.sqrt(dx * (P * P).sum(axis=1))[:, None]
            # L2 Gram + condition (degeneracy DQ)
            G = dx * (P @ P.T)
            res[f"Gcond_{gl}"] = float(np.linalg.cond(G))
            # prime-side Gram via the algebraic identity only
            Qs = np.array([Q_grid(xs, dx, P[i]) for i in range(m)])
            Kp = np.diag(Qs).copy()
            for i in range(m):
                for j in range(i + 1, m):
                    Kp[i, j] = Kp[j, i] = \
                        0.5 * (Q_grid(xs, dx, P[i] + P[j]) - Qs[i] - Qs[j])
            asym = float(np.abs(Kp - Kp.T).max())
            from scipy.linalg import eigh
            ev = eigh(0.5 * (Kp + Kp.T), G, eigvals_only=True)
            res[f"Kp_{gl}"] = Kp.tolist()
            res[f"eig_{gl}"] = ev.tolist()
            res[f"asym_{gl}"] = asym
            print(f"  2^{gl}: lambda_min = {ev[0]:+.6e}  lambda_max = {ev[-1]:+.6e}"
                  f"  asym {asym:.1e}  cond(G) {res[f'Gcond_{gl}']:.1f}", flush=True)
            print(f"    eigs: {' '.join(f'{e:+.3e}' for e in ev)}", flush=True)
            # persist per level (power-cut lesson: #41c)
            json.dump(res, open(f"{OUTSTEM}.results.json", "w"), indent=1)

        # zero side at the finest grid, T ladder
        for T in T_LIST:
            Kz, nz, last = zero_side_gram(F, xs23, 2 * LGRID / (1 << 23), T)
            from scipy.linalg import eigh
            G23 = (2 * LGRID / (1 << 23)) * (F @ F.T)
            evz = eigh(0.5 * (Kz + Kz.T), G23, eigvals_only=True)
            res[f"Kz_T{T:.0f}"] = Kz.tolist()
            res[f"eigz_T{T:.0f}"] = evz.tolist()
            res[f"nz_T{T:.0f}"] = nz
            print(f"  zero T={T:.0f} ({nz} zeros): lambda_min = {evz[0]:+.6e}"
                  f"  last|u|max^2 {last:.2e}", flush=True)
            json.dump(res, open(f"{OUTSTEM}.results.json", "w"), indent=1)

        # gates (only when both grid levels ran)
        if len(GRIDS) == 2:
            lo, hi = min(GRIDS), max(GRIDS)
            Klo = np.array(res[f"Kp_{lo}"])
            Khi = np.array(res[f"Kp_{hi}"])
            d = np.abs(Khi - Klo)
            thr = np.maximum(2e-5, 0.2 * np.abs(Khi))
            nfail = int((d > thr).sum())
            res["gate_E_fail"] = nfail
            print(f"  GATE-E: {nfail}/{d.size} entries fail "
                  f"max|dK| {d.max():.2e} (thr base 2e-5)", flush=True)
            # noise-direction DQ: eigenvalues unstable across grids (smoke
            # lesson — manufactured/manufacturing-grade directions move by
            # >50% relative; certificate only covers the stable spectrum)
            evlo, evhi = np.array(res[f"eig_{lo}"]), np.array(res[f"eig_{hi}"])
            unstable = int((np.abs(evlo - evhi)
                            > 0.5 * np.maximum(np.abs(evlo), np.abs(evhi))).sum())
            res["eig_unstable"] = unstable
            print(f"  eig-stability DQ: {unstable}/{evlo.size} eigenvalues move "
                  f">50% rel between 2^{lo} and 2^{hi}", flush=True)
            if "Kz_T200" in res:
                dz = np.abs(np.array(res[f"Kp_{hi}"]) - np.array(res["Kz_T200"]))
                thrz = np.maximum(5e-5, 0.3 * np.abs(res["Kz_T200"]))
                nzf = int((dz > thrz).sum())
                res["gate_Z_fail"] = nzf
                print(f"  GATE-Z: {nzf}/{M_BASIS ** 2} entries fail "
                      f"max|dK| {dz.max():.2e}", flush=True)
        json.dump(res, open(f"{OUTSTEM}.results.json", "w"), indent=1)
        report[L] = res

    print("\n== verdict (pre-stated): (a) all lambda_min>0 both instruments & gates "
          "-> spans certified positive; (b) stable negative -> FREEZE + counterparty; "
          "(c) gates fail -> instrument floor, D7 class ==", flush=True)
