"""heat63 — the random-basis M-LADDER: the honest decay-rate measurement of
lambda_min(M) -> 0+ that the mutant ladder could not give (its cond(G)
exploded before the rate was measurable).

CATEGORY: D (W(f)/Weil positivity lane — B2 follow-up; ridge-generic decay)

WHY: heat62 (hash-committed db7de084, outcome b RIDGE-GENERIC): orthonormal
random bases at M=8 land +5.9e-16..+1.7e-14 — 20-500x closer to the bottom
than the GA's winner+mutant span (+3.07e-13) — and random BUMP (compact
support) draws at M=16 already match the GA's whole history (+7.9e-14).
The near-null structure is a fat generic ridge. The unmeasured object is
the RATE: lambda_min ~ c/M^alpha on random spans, with per-trial floors
~1e-16 (cond=1) that do NOT explode with M. Under RH + Weil the spectral
bottom is 0 (inf unattained); alpha is the shape of the generic approach.

CHANGES vs heat62 (fixes for its 15/40 DQ rate — narrow draws made M=16
near-dependent):
  - wider draws: mu ~ U(-16,16), sigma ~ exp(U(ln 0.3, ln 8)), nterm ~ 2-6;
  - families LA-rand, LB-rand, BUMP at 5 seeds x M in {16, 32}; LC-rand 1
    seed as control (heat62 showed it bottom-blind at +0.02..+0.79 — kept
    for the contrast record, not expected to compete);
  - M=64 on the two best families x 2 seeds (zero-side cost grows ~M^2 in
    the Gram but the zero sum is the same 79 zeros).
  NESTED-PREFIX DESIGN: trial() seeds a fresh rng per (family, seed), and
  draw_wide consumes it genome-by-genome, so for a fixed (family, seed) the
  M=16 basis is a strict prefix of M=32 (and of M=64) — GS then reproduces
  the first 16 rows bitwise. Rayleigh-Ritz monotonicity is therefore
  checkable per seed (lambda_min(M=32) <= lambda_min(M=16) in exact
  arithmetic; a violation = stream bug, instrument falsifier, checked at
  adjudication from the results JSON).

PRE-REGISTRATION (trap #32; hash committed on the exchange BEFORE any
scored evaluation; trap #68 rules applied — per-trial floors, below-
resolution arm, tolerance = record precision):
  Outcome (a) FREEZE: any genuine trial lambda_min < -1e-11 -> (b)-class
      protocol inherited (freeze, dps re-certify, relay BEFORE claim
      language). Would be route-1 negative.
  Outcome (b) RATE MEASURED: genuine readings (>= 10x floor, T-sat ok) at
      >= 3 values of M for a family -> fit lambda_min ~ c/M^alpha on that
      family's per-seed minima, alpha reported with floor-derived error
      bars; record c, alpha. THE object of interest.
  Outcome (c) FLOOR-CLASS at large M: M=32/64 readings < 10x floor ->
      bound only (alpha >= from last genuine rung), no fit.
  Outcome (d) INSTRUMENT: > 50% of a family's M=32 draws DQ'd degenerate ->
      ranges still too narrow; report, widen, re-run that family only.
  Below-resolution readings (|lmin| < 3x floor) are EXCLUDED from fits and
  reported separately (heat62 lesson: its best-trial -2.08e-16 was 0.35x
  floor — not quotable as a minimum).
  Instrument falsifiers: T-sat |lmin150-lmin200| > 0.1|lmin200| -> DQ;
  Gram-Schmidt relative remainder < 1e-3 -> DQ; |G-I| > 1e-10 -> DQ.

CPU: single core, ~1.5-2 h, after heat62 (5-core directive).
"""
import json

import numpy as np
from scipy.linalg import eigh

import heat61_w_search as H
import heat61e_gram_ladder as E
import heat62_random_basis_ladder as B

OUTSTEM = "heat63_random_mladder"
LGRID = E.LGRID
DX23 = 2 * LGRID / (1 << 23)
XS23 = -LGRID + DX23 * np.arange(1 << 23)
EPS = 2.22e-16


def draw_wide(family, rng, m):
    gs = []
    for _ in range(m):
        nt = int(rng.integers(2, 7))
        if family == "LA-rand":
            gs.append({"terms": [
                [float(rng.uniform(-1, 1)), float(rng.uniform(-16, 16)),
                 float(np.exp(rng.uniform(np.log(0.3), np.log(8.0))))]
                for _ in range(nt)]})
        elif family == "LB-rand":
            gs.append({"c": float(rng.uniform(0.5, 2.0)),
                       "pairs": [[float(rng.uniform(-16, 16)),
                                  float(rng.uniform(-1, 1))] for _ in range(nt)]})
        elif family == "LC-rand":
            ps = rng.choice(H.PRIMES_C, size=nt)
            gs.append({"terms": [[float(rng.uniform(-1, 1)), float(p)] for p in ps]})
        else:  # BUMP
            gs.append({"bumps": [
                [float(rng.uniform(-1, 1)), float(rng.uniform(-16, 16)),
                 float(np.exp(rng.uniform(np.log(0.3), np.log(8.0))))]
                for _ in range(nt)]})
    return gs


def trial(family, seed, m_basis):
    rng = np.random.default_rng(2000 * seed + {"LA-rand": 11, "LB-rand": 23,
                                               "LC-rand": 37, "BUMP": 53}[family])
    gs = draw_wide(family, rng, m_basis)
    F0 = np.array([B.realize_any(family, g, XS23) for g in gs])
    Q, oerr = B.gram_schmidt(F0, DX23)
    tag = f"{family}/s{seed}/M{m_basis}"
    if Q is None:
        return tag, {"dq": "degenerate-draw"}
    G = DX23 * (Q @ Q.T)
    Kz, nz, _ = E.zero_side_gram(Q, XS23, DX23, 200.0)
    ev = eigh(0.5 * (Kz + Kz.T), G, eigvals_only=True)
    l200, lmax = float(ev[0]), float(ev[-1])
    floor = float(np.linalg.cond(G)) * EPS * abs(lmax)
    Kz2, _, _ = E.zero_side_gram(Q, XS23, DX23, 150.0)
    l150 = float(eigh(0.5 * (Kz2 + Kz2.T), G, eigvals_only=True)[0])
    sat = abs(l150 - l200) <= 0.1 * abs(l200) if l200 != 0 else True
    dq = (not sat) or oerr > 1e-10
    gen = (not dq) and abs(l200) >= 10 * floor   # genuine per pre-registration
    return tag, {"lmin200": l200, "floor": floor, "condG": float(np.linalg.cond(G)),
                 "ortho_err": oerr, "dq": bool(dq), "genuine": bool(gen)}


if __name__ == "__main__":
    print("CATEGORY: D (random-basis M-ladder — ridge decay-rate measurement; "
          "hash-committed pre-registration)", flush=True)
    res = {}
    jobs = ([(fam, s, m) for fam in ("LA-rand", "LB-rand", "BUMP")
             for s in (1, 2, 3, 4, 5) for m in (16, 32)]
            + [("LC-rand", 9, 16), ("LC-rand", 9, 32)]
            + [("LA-rand", 1, 64), ("LA-rand", 2, 64),
               ("BUMP", 1, 64), ("BUMP", 2, 64)])
    for fam, seed, m in jobs:
        tag, row = trial(fam, seed, m)
        res[tag] = row
        if "lmin200" in row:
            g = "GENUINE" if row["genuine"] else ("below-res" if not row["dq"] else "DQ")
            print(f"{tag}: lmin {row['lmin200']:+.6e}  floor {row['floor']:.1e}  "
                  f"[{g}]", flush=True)
        else:
            print(f"{tag}: {row['dq']}", flush=True)
        json.dump(res, open(f"{OUTSTEM}.results.json", "w"), indent=1)

    # per-family rate fit on genuine per-seed minima (outcome b)
    print("\n== per-family genuine minima by M ==", flush=True)
    fits = {}
    for fam in ("LA-rand", "LB-rand", "BUMP"):
        bym = {}
        for tag, row in res.items():
            if tag.startswith(fam) and row.get("genuine"):
                m = int(tag.split("/M")[1])
                bym.setdefault(m, []).append(row["lmin200"])
        ms = sorted(bym)
        mins = [min(bym[m]) for m in ms]
        for m, v in zip(ms, mins):
            print(f"  {fam} M={m}: min {v:+.6e} (n={len(bym[m])})", flush=True)
        fits[fam] = {"M": ms, "minima": mins}
        if len(ms) >= 3 and all(v > 0 for v in mins):
            a = np.polyfit(np.log2(ms), np.log(mins), 1)[0]
            fits[fam]["alpha_log2"] = float(a)
            print(f"  {fam}: lambda_min ~ M^-{abs(a):.2f} (log2-slope)", flush=True)
    json.dump({"res": res, "fits": fits},
              open(f"{OUTSTEM}.results.json", "w"), indent=1)
    print("\n== verdict per docstring (a)/(b)/(c)/(d); below-res rows excluded "
          "from fits ==", flush=True)
