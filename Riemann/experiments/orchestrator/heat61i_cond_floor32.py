"""heat61i — post-verdict instrument check for the heat61f M=32 reading:
is -2.440884e-14 floor-class (cond(G) grew with the basis) or a precision-
robust sub-threshold negative?

CATEGORY: M (instrument — adjudication support for heat61f; no RH content)

WHY: heat61f M=32 zero side read -2.440884e-14 (T-saturated: |T150-T200| =
1.4e-15 < 2.4e-15 budget; ladder monotone; NO (b): -1e-11 threshold not
breached). The float64 generalized-eig floor was estimated ~2e-15 from
cond(G)~200 AT M=8; heat61f did not record cond(G) per rung. -2.44e-14 is
12x the M=8-era floor. EITHER cond(G) grew (plausible: 32 near-correlated
mutants accepted at |corr|<0.98) making the reading floor-class, OR it is a
sub-threshold instrument negative — not (b) by pre-registration (which
governs), but the deepest negative reading in the programme's record, and
the letter's verdict language must wait for this check.

METHOD (escalation ladder, cheapest first):
  (1) rebuild the three prefix bases (deterministic, no Q_grid); record
      cond(G) at M=8/16/32; rebuild Kz(T=200) at M=32 and record the
      spectrum top (||K~|| = lambda_max of (Kz, G));
  (2) floor(M) = cond(G_M) * 2.22e-16 * lambda_max(Kz,G).
      Outcome (i) FLOOR-CLASS: floor(32) >= 2.44e-14 -> M=32 reading sits
      under its own rung's floor; verdict (c)-flavored stands as drafted;
      trap #68 gains the per-rung-floor clause.
  (3) else solver triangulation at M=32 (same float64 data, three routes):
      scipy eigh(Kz,G) | eigvals(G^-1 Kz) | Cholesky-reduced standard
      eigh(L^-1 Kz L^-T).  Agreement across routes -> the negative is in
      the DATA, not the solver.
  (4) data-noise probe: recompute Kz with every u summed in REVERSED point
      order (different summation tree); if lambda_min moves << 2.4e-14,
      the negative is stable in the zero-side data.
      Outcome (iii) SUB-THRESHOLD NEGATIVE, precision-robust: report as-is,
      cross-machine replication requested, NO RH claim language (M-category;
      pre-registration governs — (b) stays -1e-11).
      Outcome (i') NOISE-CLASS: either probe scatters at reading scale ->
      reading not separable from summation noise; verdict (c)-flavored as
      drafted, with the honest note that M=32's "monotone OK" step is
      noise-scale bookkeeping.

INFEASIBILITY NOTE (honesty): a full dps-100 zero-side recompute needs
high-precision sums over 2^23 grid points per (zero, basis) pair — ~10^6x
slower than float64 BLAS; not run. A true interval certificate belongs to a
formal-verification lane (machine 3's side if they want it). The ladder
above separates solver / data / summation-noise contributions only.

Committed BEFORE its run (trap #32). CPU: single core, ~5 min, chained
after heat61h.
"""
import json

import numpy as np
import scipy.linalg as sla

import heat61_w_search as H
import heat61e_gram_ladder as E

OUTSTEM = "heat61i_cond_floor32"
LGRID = E.LGRID
DX23 = 2 * LGRID / (1 << 23)
XS23 = -LGRID + DX23 * np.arange(1 << 23)
M32_READING = -2.440884e-14  # heat61f .out, M=32 zero T=200

EPS = 2.22e-16


def zero_side_gram_rev(Psi, xs, dx, T):
    """zero_side_gram with each u summed in reversed point order (different
    summation tree) — data-noise probe, not an independent instrument."""
    import mpmath as mp
    mp.mp.dps = 30
    PsiR = Psi[:, ::-1]
    xR = xs[::-1].copy()
    n, K = 1, np.zeros((len(Psi), len(Psi)))
    while True:
        z = mp.zetazero(n)
        if z.imag > T:
            break
        rho = complex(z)
        w = np.exp(rho * xR)
        u = PsiR @ w * dx
        K += 2.0 * np.outer(u, u.conj()).real
        n += 1
    return K


if __name__ == "__main__":
    print("CATEGORY: M (M=32 floor re-statement + precision triangulation; "
          "no RH content)", flush=True)
    with open("heat61_w_search.log.json") as fh:
        REC = json.load(fh)
    winner = json.loads(REC["final"]["LB"][1])

    out = {"rungs": {}}
    F32 = None
    for m_basis in (8, 16, 32):
        _, F = E.diverse_mutants("LB", winner, XS23, DX23, m_basis)
        G = DX23 * (F @ F.T)
        cond = float(np.linalg.cond(G))
        out["rungs"][m_basis] = {"condG": cond}
        print(f"M={m_basis:2d}: cond(G) = {cond:.1f}", flush=True)
        F32 = F
    G32 = DX23 * (F32 @ F32.T)

    Kz, nz, last = E.zero_side_gram(F32, XS23, DX23, 200.0)
    ev = sla.eigh(0.5 * (Kz + Kz.T), G32, eigvals_only=True)
    lmin, lmax = float(ev[0]), float(ev[-1])
    floor32 = out["rungs"][32]["condG"] * EPS * abs(lmax)
    print(f"\nM=32 zero side rebuilt: lmin {lmin:+.6e} lmax {lmax:+.4e} "
          f"(nz {nz}) | floor(32) = cond*eps*lmax = {floor32:.3e}",
          flush=True)
    out.update({"lmin_rebuilt": lmin, "lmax": lmax, "floor32": floor32,
                "nz": nz})
    json.dump(out, open(f"{OUTSTEM}.results.json", "w"), indent=1)

    if floor32 >= abs(M32_READING):
        print("\n== OUTCOME (i) FLOOR-CLASS: cond(G) growth covers the M=32 "
              "reading; verdict (c)-flavored stands; trap #68 gains the "
              "per-rung-floor clause ==", flush=True)
        out["outcome"] = "i-floor-class"
        json.dump(out, open(f"{OUTSTEM}.results.json", "w"), indent=1)
        raise SystemExit(0)

    # solver triangulation (same float64 Kz, three routes)
    Ks = 0.5 * (Kz + Kz.T)
    r1 = float(sla.eigh(Ks, G32, eigvals_only=True)[0])
    Gi = np.linalg.inv(G32)
    r2 = float(np.linalg.eigvals(Gi @ Ks)[0].real)
    L = np.linalg.cholesky(G32)
    Li = sla.solve_triangular(L, np.eye(len(G32)), lower=True)
    r3 = float(np.linalg.eigvalsh(Li @ Ks @ Li.T)[0])
    print(f"solver routes: eigh(K,G) {r1:+.6e} | eig(G^-1 K) {r2:+.6e} | "
          f"chol {r3:+.6e}", flush=True)
    out.update({"route_eigh": r1, "route_inv": r2, "route_chol": r3})
    spread = max(r1, r2, r3) - min(r1, r2, r3)

    # data-noise probe: reversed summation order
    Kz2 = zero_side_gram_rev(F32, XS23, DX23, 200.0)
    r4 = float(sla.eigh(0.5 * (Kz2 + Kz2.T), G32, eigvals_only=True)[0])
    print(f"reversed-order Kz: lmin {r4:+.6e} | move {abs(r4 - r1):.3e}",
          flush=True)
    out.update({"route_revsum": r4, "revsum_move": abs(r4 - r1)})

    if spread < 0.5 * abs(M32_READING) and abs(r4 - r1) < 0.5 * abs(M32_READING):
        v = "iii-sub-threshold-negative"
        msg = ("SUB-THRESHOLD NEGATIVE, precision-robust (solver-stable, "
               "summation-stable): report as-is, replication requested, NO "
               "RH claim language; (b) stays -1e-11 by pre-registration")
    else:
        v = "i-prime-noise-class"
        msg = ("NOISE-CLASS: solver/summation scatter at reading scale; M=32 "
               "reading not separable from float noise; verdict (c)-flavored "
               "as drafted; monotone step = noise-scale bookkeeping")
    out["outcome"] = v
    json.dump(out, open(f"{OUTSTEM}.results.json", "w"), indent=1)
    print(f"\n== OUTCOME {v} — {msg} ==", flush=True)
