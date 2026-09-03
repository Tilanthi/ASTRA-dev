"""heat61f — Gram-ladder M-extension on the LB (sinc) span: does lambda_min(M)
decrease monotonically toward 0 from above? (route-1 continuation of heat61e)

CATEGORY: D (W(f)/Weil positivity lane — the forced-mutation ladder's next rung)

WHAT: heat61e found the LB span minimum = +3.066441e-13 (zero side, T=200,
T-stable to 7 digits, float64 eig floor ~1e-15) — a genuine near-null direction
of the polarized Weil form, 8 orders below the GA's best (+6.2e-5). Under RH +
Weil's criterion the form is >= 0 with spectrum bottom plausibly 0 (inf
unattained) — so nested-subspace ladders should show lambda_min(M) -> 0+ .

LADDER STRUCTURE: diverse_mutants(rng seed 20260903) is prefix-deterministic —
the M=8 basis of heat61e is a strict PREFIX of the M=16 basis, which prefixes
M=32. Nested subspaces => Rayleigh-Ritz monotonicity:
lambda_min(M=32) <= lambda_min(M=16) <= lambda_min(M=8) = 3.066441e-13
(guaranteed by variational principle — the ladder tests the SIGN and the RATE,
monotonicity itself is theorem-grade bookkeeping).

PRE-REGISTRATION (trap #32; written before any scored evaluation):
  Expected: lambda_min(M) strictly decreasing, positive at every M, both
  instruments agreeing within GATE-Z floors; decay roughly power-law
  lambda_min ~ c/M^alpha (record c, alpha — the object of interest: the shape
  of the approach to the spectral bottom).
  Outcome (a): lambda_min > 0 at M = 16 AND 32 (zero side primary, T=200
  saturated; prime 2^23 secondary within class floors) -> span family stays
  consistent-with-RH; ladder validated as route-1 instrument; publish
  decay fit.
  Outcome (b): lambda_min < -1e-11 on the ZERO side at any M (30x the float64
  eig floor; prime side alone does not fire this) -> FREEZE, dps-50 zero-side
  re-certify, exchange relay BEFORE any claim language (W-search halt rule
  inherited). This would be route-1 negative.
  Outcome (c): sign-positive but GATE-E/Z failures dominate the reading
  (entries floor-limited) -> instrument-floor result (D7 class), no RH
  content claimed, floors remeasured per class.
  Falsifier (instrument): |lambda_min(T=150) - lambda_min(T=200)| >
  0.1*|lambda_min| at any M -> T-saturation failure, that M's zero-side
  reading DQ'd (reported, excluded from the certificate).
  Falsifier (ladder): lambda_min(M=16) > lambda_min(M=8) + 1e-14 -> prefix
  property VIOLATED (basis construction bug — stop and debug, nothing scored).

Also recorded: the M=8 near-null eigenvector's coefficients over the basis
(which mutants carry the direction) — structure of the near-null space.

CPU budget: single core (user directive 2026-09-03; runs beside heat54's 4).
"""
import json

import numpy as np
from scipy.linalg import eigh

import heat61_w_search as H
import heat61e_gram_ladder as E

OUTSTEM = "heat61f_gram_ladder_m"
LGRID = E.LGRID
DX23 = 2 * LGRID / (1 << 23)
XS23 = -LGRID + DX23 * np.arange(1 << 23)


def span_at(m_basis, lineage, winner):
    genomes, F = E.diverse_mutants(lineage, winner, XS23, DX23, m_basis)
    assert len(F) == m_basis, f"basis short: {len(F)} of {m_basis}"
    return genomes, F


if __name__ == "__main__":
    print("CATEGORY: D (W(f)/Weil positivity — Gram ladder M-extension)", flush=True)
    with open("heat61_w_search.log.json") as fh:
        REC = json.load(fh)
    winner = json.loads(REC["final"]["LB"][1])

    res = {}
    prev_lmin = None
    for m_basis in (8, 16, 32):
        genomes, F = span_at(m_basis, "LB", winner)
        G23 = DX23 * (F @ F.T)

        # -- prime side at 2^23 only (class floors already certified heat61e) --
        Qs = np.array([E.Q_grid(XS23, DX23, F[i]) for i in range(m_basis)])
        Kp = np.diag(Qs).copy()
        for i in range(m_basis):
            for j in range(i + 1, m_basis):
                Kp[i, j] = Kp[j, i] = \
                    0.5 * (E.Q_grid(XS23, DX23, F[i] + F[j]) - Qs[i] - Qs[j])
        evp = eigh(0.5 * (Kp + Kp.T), G23, eigvals_only=True)

        # -- zero side, T=150 and 200 (saturation falsifier per M) --
        rows = {}
        for T in (150.0, 200.0):
            Kz, nz, last = E.zero_side_gram(F, XS23, DX23, T)
            evz = eigh(0.5 * (Kz + Kz.T), G23, eigvals_only=True)
            rows[T] = (evz, nz, last)

        # near-null eigenvector coefficients (generalized eigvec at lambda_min)
        Kz, nz, _ = E.zero_side_gram(F, XS23, DX23, 200.0)
        w, V = eigh(0.5 * (Kz + Kz.T), G23)
        coeff = V[:, 0] / np.sqrt(np.sum(V[:, 0] ** 2))

        res[m_basis] = {
            "prime_lmin": float(evp[0]), "prime_lmax": float(evp[-1]),
            "zero_lmin_150": float(rows[150.0][0][0]),
            "zero_lmin_200": float(rows[200.0][0][0]),
            "nz_200": int(rows[200.0][1]),
            "last_200": float(rows[200.0][2]),
            "nearnull_coeff": [float(c) for c in coeff],
        }
        json.dump({str(k): v for k, v in res.items()},
                  open(f"{OUTSTEM}.results.json", "w"), indent=1)

        print(f"M={m_basis:2d}: prime 2^23 lmin {evp[0]:+.4e} | "
              f"zero T=150 {rows[150.0][0][0]:+.6e} T=200 "
              f"{rows[200.0][0][0]:+.6e} (nz {rows[200.0][1]}, "
              f"last {rows[200.0][2]:.1e})", flush=True)
        print(f"        near-null eigvec coeff (top 4 |.|): "
              f"{sorted(np.abs(coeff))[-4:][::-1]}", flush=True)

        if prev_lmin is not None:
            dl = rows[200.0][0][0] - prev_lmin
            print(f"        ladder step: {dl:+.3e} "
                  f"({'monotone OK' if dl <= 1e-14 else 'PREFIX VIOLATION — STOP'})",
                  flush=True)
            if dl > 1e-14:
                break
        prev_lmin = rows[200.0][0][0]

        # T-saturation falsifier
        sat = abs(rows[150.0][0][0] - rows[200.0][0][0])
        if sat > 0.1 * abs(rows[200.0][0][0]):
            print(f"        [F-T FIRED] |lmin150-lmin200| {sat:.2e} > "
                  f"10% of |lmin200| — this M zero-side reading DQ'd", flush=True)

    print("\n== verdict per pre-registration in docstring (a)/(b)/(c) ==",
          flush=True)
