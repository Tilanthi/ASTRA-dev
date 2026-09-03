"""heat61h — A1 exposure resolver: the 4% prime-side discrepancy between
heat61e (LB 2^23 prime lmin -3.322801e-6, from Kp_23 saved in results JSON)
and heat61f (M=8 prime lmin -3.1972e-6) on nominally the same basis + code.

CATEGORY: M (instrument/meta — assumption-ledger A1 open detail; no RH content)

WHAT WAS ESTABLISHED BY INSPECTION (this session, before writing this file):
  - prime-side construction is line-for-line identical in both scripts
    (diag Qs + 0.5 polarization identity -> Kp -> symmetrize -> eigh(Kp, G));
  - at gl=23 heat61e's np.interp(xs, xs23, F[i]) is the identity (same float
    grid), and its renormalization divides by exactly 1.0;
  - the zero side agrees BIT-IDENTICALLY (+3.066441e-13 both runs), so the
    bases F are the same to the bit — the difference is in the prime-side
    evaluation chain given identical inputs, or in cross-process arithmetic.
  - scale check: 4% of 3.3e-6 = 1.3e-7 — this sits far below every certified
    prime-side class floor (LB/sinc floor at 2^23 is ~few e-6), so whatever
    the mechanism, both readings are floor-class and no above-floor result
    depends on the answer. This test CLOSES A1 either way; it cannot open a
    claim.

METHOD: heat61e saved genomes + Kp_23 + eig_23 in its results JSON. Rebuild
everything in one process, twice where nondeterminism is possible:
  (1) genomes_fresh = E.diverse_mutants(...) -> genome-level identity vs saved;
  (2) F rebuilt from SAVED genomes via E.realize + same normalization ->
      bit-compare vs F_fresh (prefix-determinism at the array level);
  (3) Kp_recomputed (heat61f path) vs Kp_saved: per-entry max|diff|, computed
      TWICE to probe in-process nondeterminism (threaded BLAS);
  (4) eigh(Kp_saved, G23) vs saved eig_23 (does the saved matrix reproduce the
      heat61e .out number on this machine today?) and eigh(Kp_recomputed, G23)
      vs heat61f's -3.1972e-6.

PRE-REGISTRATION (trap #32):
  Mechanism hypothesis (from source reading, pre-run): diverse_mutants leaves
  the WINNER row unnormalized; heat61e's rung code renormalized every row.
  Exact arithmetic is scale-invariant (eigh(DKD, DGD) = eigh(K,G)), so both
  runs measured the same operator — but bitwise they differ, and the near-null
  prime eigenvalue amplifies ||f0|| != 1 by eps into ~1e-7 absolute shift
  (4% of 3.3e-6), while the zero side agrees to 7 digits.
  Outcome (alpha) MECHANISM CONFIRMED: renormalized-path Kp reproduces the
  SAVED Kp_23 (bit-exact or <= float noise) AND the unnormalized-path lmin
  reproduces heat61f's -3.1972e-6 (within 1e-12) -> the 4% discrepancy is
  named: winner-row normalization difference; both readings floor-class; A1
  CLOSED benign; no above-floor result affected.
  Outcome (beta) RESIDUAL: genomes and F identical but neither path
  reproduces both .out numbers -> cross-process arithmetic variance at floor
  scale (D7-flavored scatter) -> A1 CLOSED benign-with-mechanism-unlocalized;
  prime readings at |lmin| < class floor carry ~1e-7 cross-run scatter.
  Outcome (gamma) PREFIX QUESTION: genomes differ -> prefix-determinism
  broken at genome level despite zero-side agreement -> A5 reopens, M-ladder
  interpretation pauses until understood.

CPU budget: single core, chained after heat61g (5-core directive).
"""
import json

import numpy as np
from scipy.linalg import eigh

import heat61_w_search as H
import heat61e_gram_ladder as E

OUTSTEM = "heat61h_kphash_a1"
LGRID = E.LGRID
DX23 = 2 * LGRID / (1 << 23)
XS23 = -LGRID + DX23 * np.arange(1 << 23)

HEAT61E_LMIN = -3.322801e-6   # from heat61e .out LB 2^23 (letter table source)
HEAT61F_LMIN = -3.1972e-6     # from heat61f .out M=8 prime


def build_kp(F):
    m = len(F)
    Qs = np.array([E.Q_grid(XS23, DX23, F[i]) for i in range(m)])
    Kp = np.diag(Qs).copy()
    for i in range(m):
        for j in range(i + 1, m):
            Kp[i, j] = Kp[j, i] = \
                0.5 * (E.Q_grid(XS23, DX23, F[i] + F[j]) - Qs[i] - Qs[j])
    return Kp, Qs


if __name__ == "__main__":
    print("CATEGORY: M (A1 exposure resolver — Kp hash comparison; no RH content)",
          flush=True)
    with open("heat61_w_search.log.json") as fh:
        REC = json.load(fh)
    winner = json.loads(REC["final"]["LB"][1])
    saved = json.load(open("heat61e_gram_ladder.results.json"))

    genomes_saved = [np.array(g, dtype=float) for g in saved["genomes"]]
    Kp_saved = np.array(saved["Kp_23"])
    eig_saved = np.array(saved["eig_23"])
    m = len(genomes_saved)

    # (1) genome-level prefix-determinism
    genomes_fresh, F_fresh = E.diverse_mutants("LB", winner, XS23, DX23, m)
    genomes_equal = all(np.array_equal(g, s)
                        for g, s in zip(genomes_fresh, genomes_saved))
    print(f"[1] genomes equal: {genomes_equal} "
          f"(fresh {len(genomes_fresh)} vs saved {m})", flush=True)

    # (2) F rebuilt from SAVED genomes EXACTLY as diverse_mutants builds it
    #     (first element = winner realization, NOT normalized — line 155 of
    #     heat61e; mutants are normalized at acceptance). Bit-compare to fresh.
    F_saved = [E.realize("LB", genomes_saved[0], XS23)]
    for g in genomes_saved[1:]:
        f = E.realize("LB", g, XS23)
        nr = np.sqrt(DX23 * (f * f).sum())
        F_saved.append(f / nr)
    F_saved = np.array(F_saved)
    F_equal = np.array_equal(F_saved, F_fresh)
    print(f"[2] F bit-identical (saved-genome rebuild vs fresh): {F_equal}",
          flush=True)

    # (3) Kp recomputed twice (in-process nondeterminism probe) vs saved
    Kp_a, Qs_a = build_kp(F_fresh)
    Kp_b, Qs_b = build_kp(F_fresh)
    rep_equal = np.array_equal(Kp_a, Kp_b)
    dkps = float(np.max(np.abs(Kp_a - Kp_saved)))
    dqs = float(np.max(np.abs(Qs_a - np.diag(Kp_saved))))
    print(f"[3] recomputed-twice identical: {rep_equal} | "
          f"max|Kp_recomputed - Kp_saved| = {dkps:.3e} | max diag diff {dqs:.3e}",
          flush=True)

    # (4) eigen checks
    G23 = DX23 * (F_fresh @ F_fresh.T)
    for tag, K in (("saved", Kp_saved), ("recomputed", Kp_a)):
        ev = eigh(0.5 * (K + K.T), G23, eigvals_only=True)
        print(f"[4] lmin from {tag} Kp: {ev[0]:+.6e} "
              f"(heat61e .out {HEAT61E_LMIN:+.6e}; heat61f .out {HEAT61F_LMIN:+.6e})",
              flush=True)
    ev_saved_check = eigh(0.5 * (Kp_saved + Kp_saved.T), G23, eigvals_only=True)
    print(f"    saved eig_23[0] (as stored): {float(eig_saved[0]):+.6e} | "
          f"recomputed-from-saved-matrix {ev_saved_check[0]:+.6e}",
          flush=True)

    # (5) RENORMALIZATION PROBE — candidate mechanism: heat61e's rung code
    #     renormalized EVERY row (P = P/sqrt(dx*(P*P).sum())); diverse_mutants
    #     leaves the winner row unnormalized. Generalized eigh is scale-
    #     invariant in exact arithmetic (D K D, D G D) but NOT bitwise — and
    #     ||f0|| != 1 by eps-level amounts perturbs the near-null prime
    #     eigenvalue at exactly the observed 4%-of-3e-6 scale, while leaving
    #     the zero side (well-conditioned rows) agreeing to 7 digits.
    n0 = np.sqrt(DX23 * (F_fresh[0] * F_fresh[0]).sum())
    print(f"[5] ||f0|| (winner row, diverse_mutants path) = {n0:.17f} "
          f"(|dev from 1| = {abs(n0 - 1.0):.3e})", flush=True)
    P_e = F_fresh / np.sqrt(DX23 * (F_fresh * F_fresh).sum(axis=1))[:, None]
    Kp_e, _ = build_kp(P_e)
    G_e = DX23 * (P_e @ P_e.T)
    dkpe = float(np.max(np.abs(Kp_e - Kp_saved)))
    ev_e = eigh(0.5 * (Kp_e + Kp_e.T), G_e, eigvals_only=True)
    print(f"    renormalized-path Kp vs heat61e SAVED Kp_23: max|diff| = "
          f"{dkpe:.3e} | lmin = {ev_e[0]:+.6e}", flush=True)

    # verdict per pre-registration
    lmin_recomputed = float(eigh(0.5 * (Kp_a + Kp_a.T), G23,
                                 eigvals_only=True)[0])
    out = {"genomes_equal": bool(genomes_equal), "F_equal": bool(F_equal),
           "recompute_repeat_identical": bool(rep_equal),
           "max_dKp_vs_saved": dkps, "max_dQs_vs_saved": dqs,
           "norm_f0": float(n0), "max_dKp_renorm_vs_saved": dkpe,
           "lmin_recomputed": lmin_recomputed,
           "lmin_renorm_path": float(ev_e[0]),
           "lmin_from_saved_Kp": float(ev_saved_check[0]),
           "eig23_saved_stored": float(eig_saved[0])}
    json.dump(out, open(f"{OUTSTEM}.results.json", "w"), indent=1)
    if not genomes_equal:
        v = "gamma"
    elif (dkpe <= 1e-18 and abs(float(ev_e[0]) - float(eig_saved[0])) <= 1e-12
          and abs(lmin_recomputed - HEAT61F_LMIN) <= 1e-12):
        v = "alpha"
    else:
        v = "beta"
    labels = {
        "alpha": "MECHANISM CONFIRMED (winner-row normalization; A1 CLOSED benign)",
        "beta": "RESIDUAL (floor-scale cross-process scatter; A1 CLOSED benign-unlocalized)",
        "gamma": "PREFIX QUESTION (A5 reopens; M-ladder interpretation pauses)",
    }
    print(f"\n== OUTCOME ({v}) — {labels[v]} ==", flush=True)
