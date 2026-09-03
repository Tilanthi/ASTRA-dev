"""heat61h (v2) — A1 exposure resolver: the 4% prime-side discrepancy between
heat61e (LB 2^23 prime lmin -3.322801e-6, from the .out section) and heat61f
(M=8 prime lmin -3.1972e-6) on nominally the same basis + code.

CATEGORY: M (instrument/meta — assumption-ledger A1 open detail; no RH content)

v2 NOTE (both crashes happened pre-measurement; nothing was ever scored from
this script): v1 crashed twice at input load — first on numeric-array
assumption (genomes are dicts), then on the discovery that heat61e's results
JSON holds ONLY THE LAST LINEAGE (LC: res is reused and re-dumped per
lineage; the flat file cannot attribute numbers to lineages — the .out
section headers are the only map; proposed trap #69, same genus as my
letter §5 erratum). v2 therefore uses NO saved matrix: it rebuilds both
evaluation paths from scratch and tests which .out number each reproduces.

MECHANISM HYPOTHESIS (from source reading + heat61g's condG print, pre-run):
  diverse_mutants leaves the WINNER row unnormalized (heat61e line 155);
  heat61g measured cond(G)=970 on that unnormalized M=8 basis where heat61e's
  RENORMALIZED rung printed 200.2 — ratio 4.85 => ||f0|| ~ 2.2, a genuine
  factor-2 rescaling, not eps. Exact arithmetic is scale-invariant
  (eigh(DKD, DGD) = eigh(K,G), D diagonal invertible) so both runs measured
  the SAME operator — hence zero-side agreement to 7 digits — but bitwise
  the (K,G) pairs differ, and float64 eigh scatters the near-null prime
  eigenvalue by ~1e-7 absolute = the whole 4%-of-3.3e-6.

PROBES:
  [1] basis determinism: diverse_mutants built twice, bit-identical F.
  [2] ||f0|| measured (expect ~2.2, NOT 1).
  [3] heat61f path: Kp from F as-is, eigh vs G as-is -> compare -3.1972e-6.
  [4] heat61e path: rows renormalized exactly as heat61e's rung lines
      220-221 (np.interp is the identity at gl=23), Kp rebuilt, eigh vs
      renormalized G -> compare -3.322801e-6.

PRE-REGISTRATION (trap #32):
  (alpha) MECHANISM CONFIRMED: [3] reproduces heat61f's number AND [4]
      reproduces heat61e's number (both within 1e-12 absolute) -> the 4%
      discrepancy is the winner-row normalization difference; both readings
      floor-class (per-class prime floors exceed 1.3e-7); A1 CLOSED benign;
      standing practice: normalize rows before polarizing.
  (beta) PARTIAL: exactly one path reproduces -> A1 CLOSED with the
      reproducing path named; the other .out number gets a caveat.
  (gamma) NEITHER: cross-process arithmetic variance at floor scale ->
      A1 CLOSED benign-unlocalized (D7-flavored scatter).
  Scale check either way: 1.3e-7 absolute sits below every certified
  per-class prime floor; no above-floor result depends on the answer.

CPU: single core, ~30-40 min (72 Q_grid calls at 2^23), after heat61i.
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

HEAT61E_LMIN = -3.322801e-6   # heat61e .out, LB section, 2^23 prime
HEAT61F_LMIN = -3.1972e-6     # heat61f .out, M=8 prime


def build_kp(F):
    m = len(F)
    Qs = np.array([E.Q_grid(XS23, DX23, F[i]) for i in range(m)])
    Kp = np.diag(Qs).copy()
    for i in range(m):
        for j in range(i + 1, m):
            Kp[i, j] = Kp[j, i] = \
                0.5 * (E.Q_grid(XS23, DX23, F[i] + F[j]) - Qs[i] - Qs[j])
    return Kp


if __name__ == "__main__":
    print("CATEGORY: M (A1 exposure resolver v2 — dual-path reproduction; "
          "no RH content)", flush=True)
    with open("heat61_w_search.log.json") as fh:
        REC = json.load(fh)
    winner = json.loads(REC["final"]["LB"][1])

    _, F1 = E.diverse_mutants("LB", winner, XS23, DX23, 8)
    _, F2 = E.diverse_mutants("LB", winner, XS23, DX23, 8)
    det = bool(np.array_equal(F1, F2))
    print(f"[1] diverse_mutants built twice: bit-identical = {det}", flush=True)

    n0 = float(np.sqrt(DX23 * (F1[0] * F1[0]).sum()))
    print(f"[2] ||f0|| (winner row) = {n0:.6f}  "
          f"(cond ratio prediction ~{np.sqrt(n0):.3f}^2 = {n0**2:.1f}; "
          f"heat61g saw 970/200.2 = 4.85)", flush=True)

    # [3] heat61f path (rows as-is)
    G_u = DX23 * (F1 @ F1.T)
    Kp_u = build_kp(F1)
    lam_u = float(eigh(0.5 * (Kp_u + Kp_u.T), G_u, eigvals_only=True)[0])
    print(f"[3] heat61f path (as-is rows): lmin {lam_u:+.6e}  "
          f"(target {HEAT61F_LMIN:+.6e}, diff {abs(lam_u - HEAT61F_LMIN):.2e})",
          flush=True)

    # [4] heat61e path (renormalized rows, rung lines 220-221; interp=identity)
    P = np.array([np.interp(XS23, XS23, F1[i]) for i in range(8)])
    P = P / np.sqrt(DX23 * (P * P).sum(axis=1))[:, None]
    G_e = DX23 * (P @ P.T)
    Kp_e = build_kp(P)
    lam_e = float(eigh(0.5 * (Kp_e + Kp_e.T), G_e, eigvals_only=True)[0])
    print(f"[4] heat61e path (renormalized): lmin {lam_e:+.6e}  "
          f"(target {HEAT61E_LMIN:+.6e}, diff {abs(lam_e - HEAT61E_LMIN):.2e})",
          flush=True)
    print(f"    cond(G): as-is {np.linalg.cond(G_u):.1f} vs renormalized "
          f"{np.linalg.cond(G_e):.1f} (heat61f-era vs heat61e-era: 970 vs 200)",
          flush=True)

    ok_u = abs(lam_u - HEAT61F_LMIN) <= 1e-12
    ok_e = abs(lam_e - HEAT61E_LMIN) <= 1e-12
    if ok_u and ok_e:
        v = "alpha"
    elif ok_u or ok_e:
        v = "beta"
    else:
        v = "gamma"
    labels = {
        "alpha": "MECHANISM CONFIRMED (winner-row normalization; A1 CLOSED benign)",
        "beta": "PARTIAL (one path reproduces; A1 CLOSED with that path named)",
        "gamma": "NEITHER (cross-process variance; A1 CLOSED benign-unlocalized)",
    }
    out = {"basis_deterministic": det, "norm_f0": n0,
           "lmin_as_is": lam_u, "reproduces_61f": bool(ok_u),
           "lmin_renorm": lam_e, "reproduces_61e": bool(ok_e),
           "condG_as_is": float(np.linalg.cond(G_u)),
           "condG_renorm": float(np.linalg.cond(G_e)), "outcome": v}
    json.dump(out, open(f"{OUTSTEM}.results.json", "w"), indent=1)
    print(f"\n== OUTCOME ({v}) — {labels[v]} ==", flush=True)
