"""heat61g — ASSUMPTION LEDGER A4 exposure test: is the near-null ladder reading
spectral structure or mutant-acceptance geometry?

CATEGORY: M (instrument/meta — assumption-ledger exposure route; zero RH claim possible)

WHAT: heat61e/f's diverse_mutants accepts candidates at |corr| < 0.98 (hardcoded).
The M=8 near-null eigenvector was a near-cancellation PAIR (coeffs 0.695/0.683),
so the ladder's approach to the floor plausibly measures how-similar-the-threshold-
lets-mutants-be, not the operator's spectral bottom. A4 (UNEXAMINED in the ledger)
says: test before interpreting any lambda_min(M) decay.

Vary the threshold at FIXED M=8, LB winner, same everything else; zero side only
(exact instrument; prime side adds nothing at these magnitudes — floor).

PRE-REGISTRATION (trap #32, written before running):
  Prediction (threshold-geometry story): lambda_min is MONOTONE in the threshold —
  higher threshold (more similar mutants admitted -> closer cancellation pairs)
  gives LOWER lambda_min:
      lambda_min(0.99) < lambda_min(0.98) = 3.066441e-13 < lambda_min(0.95)
  Expected magnitude of the effect: each threshold step moves lambda_min by
  orders of magnitude if geometry dominates (the 0.98->M=16 span step moved it
  3e-13 -> floor); comparable-order if spectrum dominates.
  Outcome (i): monotone as predicted -> A4 CONFIRMED (geometry-dominant): the
  heat61f decay fit is basis-geometry, NOT spectral bottom; ladder needs a
  diversity-normalized redesign before any c/M^alpha is quoted.
  Outcome (ii): lambda_min(0.95) <= lambda_min(0.98) (wrong direction) or
  non-monotone -> A4 REFUTED for this span: near-null direction is robust to
  acceptance geometry -> spectral reading stands (update ledger A4 to ENFORCED-
  BY-TEST).
  Outcome (iii): any variant < -1e-11 -> (b)-class freeze per heat61f protocol
  (not expected; would relay).
  Instrument falsifier: T-saturation |lmin150 - lmin200| > 0.1|lmin200| at any
  threshold -> that threshold's reading DQ'd.

CPU budget: single core, launched only after heat61f exits (5-core directive).
"""
import json

import numpy as np
from scipy.linalg import eigh

import heat61_w_search as H
import heat61e_gram_ladder as E

OUTSTEM = "heat61g_assumption_a4"
LGRID = E.LGRID
DX23 = 2 * LGRID / (1 << 23)
XS23 = -LGRID + DX23 * np.arange(1 << 23)


def diverse_mutants_thr(lineage, winner, xs, dx, m_basis, thr):
    """E.diverse_mutants verbatim with the 0.98 acceptance threshold parametrised
    (instrument frozen — heat61e untouched; this is a variant harness, not an edit)."""
    basis_f = [E.realize(lineage, winner, xs)]
    rng = np.random.default_rng(20260903)
    tries = 0
    while len(basis_f) < m_basis and tries < 200:
        tries += 1
        g = H.mutate(winner, lineage, rng)
        g = H.mutate(g, lineage, rng)
        f = E.realize(lineage, g, xs)
        nr = np.sqrt(dx * (f * f).sum())
        if nr < 1e-12:
            continue
        f = f / nr
        ok = True
        for fb in basis_f:
            if abs(dx * (f * fb).sum()) > thr:
                ok = False
                break
        if ok:
            basis_f.append(f)
    return np.array(basis_f)


if __name__ == "__main__":
    print("CATEGORY: M (assumption-ledger A4 exposure — instrument geometry test)",
          flush=True)
    with open("heat61_w_search.log.json") as fh:
        REC = json.load(fh)
    winner = json.loads(REC["final"]["LB"][1])

    res = {}
    for thr in (0.95, 0.98, 0.99):
        F = diverse_mutants_thr("LB", winner, XS23, DX23, 8, thr)
        m = len(F)
        G23 = DX23 * (F @ F.T)
        row = {"M": m, "condG": float(np.linalg.cond(G23))}
        for T in (150.0, 200.0):
            Kz, nz, last = E.zero_side_gram(F, XS23, DX23, T)
            ev = eigh(0.5 * (Kz + Kz.T), G23, eigvals_only=True)
            row[f"lmin_T{T:.0f}"] = float(ev[0])
            row[f"last_T{T:.0f}"] = float(last)
        res[thr] = row
        json.dump({str(k): v for k, v in res.items()},
                  open(f"{OUTSTEM}.results.json", "w"), indent=1)
        sat = abs(row["lmin_T150"] - row["lmin_T200"])
        flag = "T-SAT FAIL (DQ)" if sat > 0.1 * abs(row["lmin_T200"]) else "sat ok"
        print(f"thr={thr}: M={m} condG={row['condG']:.0f} "
              f"lmin T150 {row['lmin_T150']:+.6e} T200 {row['lmin_T200']:+.6e} "
              f"[{flag}]", flush=True)

    l95, l98, l99 = res[0.95]["lmin_T200"], res[0.98]["lmin_T200"], res[0.99]["lmin_T200"]
    if min(l95, l98, l99) < -1e-11:
        print("\n== OUTCOME (iii): (b)-class reading — FREEZE protocol ==", flush=True)
    elif l99 <= l98 <= l95:
        print("\n== OUTCOME (i): MONOTONE in threshold — A4 CONFIRMED (geometry-"
              "dominant; heat61f decay = basis geometry, not spectrum) ==", flush=True)
    else:
        print("\n== OUTCOME (ii): non-monotone/wrong-direction — A4 REFUTED for "
              "this span; spectral reading stands ==", flush=True)
