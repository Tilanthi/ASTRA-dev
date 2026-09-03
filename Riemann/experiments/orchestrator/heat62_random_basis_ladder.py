"""heat62 — ASSUMPTION LEDGER B2 (+B3) exposure: random admissible bases vs
the winner+mutant span — is the near-null ridge GENERIC, and did the GA earn
its direction?

CATEGORY: D (W(f)/Weil positivity lane — B2 random-basis exposure + the
missing compact-support family B3)

WHY: the mutant M-ladder is exhausted at M~16 (cond(G) 970 -> 7.6e3 -> 1.15e7,
heat61i) — acceptance-rule geometry buys spectral reach with conditioning
death. Two ledger assumptions become testable with one instrument:
  B2 (winners+mutants span the GA's directions — UNEXAMINED): random bases
  at the same M measure whether the GA-winner span is special or the ridge
  is generic in the admissible class.
  B3 (three lineages cover the class — SURVEY-GRADE, compact support
  absent): a fourth, compact-support family (smooth bumps) joins the pool.

INSTRUMENT: per trial — draw M random functions from one family, Gram-
Schmidt orthonormalize over L2(dx) so cond(G) ~= 1 (floors ~ eps*|K|,
i.e. ~1e-17 — the whole point: the mutant ladder's floor death came from
cond, and orthonormal random bases do not have that problem), then the
EXACT zero side only (T=200 primary, T=150 falsifier; prime side is class-
dependent per D7 and NOT run here — any follow-up on the best trial needs
its class floor certified first, separately).

FAMILIES (random genome spaces, seeds fixed below):
  LA-rand: sums of Gaussians exp(-(x-mu)^2/2s^2), mu ~ U(-15,15), s ~ U(0.5,5)
  LB-rand: sinc pairs (winner's family, random centers/amplitudes)
  LC-rand: Fourier-type sums (winner's family, random modes)
  BUMP  :  compact support, phi(t)=exp(-1/(1-t^2)) on |t|<1, random
           centers/widths — B3's absent family, zero-side-primary only

PRE-REGISTRATION (trap #32; hash-committed on the exchange BEFORE any
scored evaluation; trap #68 rule applied — per-trial floor measured, a
below-resolution branch exists):
  Trials: 5 seeds x 4 families x M in {8,16} = 40 runs, 1 core.
  Per-trial floor = cond(G_actual) * 2.22e-16 * lambda_max(Kz,G), recorded.
  Outcome (a) FREEZE: any trial lambda_min < -1e-11 (zero side) -> (b)-class
      protocol inherited from heat61f: freeze, dps re-certify, relay BEFORE
      any claim language. Would be route-1 negative.
  Outcome (b) RIDGE-GENERIC: min over trials < +3.066441e-13 / 10 (i.e.
      random spans sit materially closer to the bottom than the GA's best
      8-dim span) -> B2 WEAKENED: winners do not uniquely span the
      approach; the near-null ridge is generic in the admissible class;
      next rung = enlarge M on random bases (their floors stay ~1e-17).
  Outcome (c) WINNER-EARNED: every trial >= +3.066441e-13 -> B2 CONFIRMED:
      the GA's direction is genuinely closer to the bottom than random —
      the search earned something the class average does not give.
  Outcome (d) FLOOR-CLASS: readings indistinguishable from their per-trial
      floors -> inconclusive at this M; report and enlarge M or T.
  Instrument falsifiers: T-saturation |lmin150-lmin200| > 0.1|lmin200| ->
      trial DQ'd; Gram-Schmidt orthonormality check |G - I|_max > 1e-10 ->
      trial DQ'd (basis construction bug).

CPU: single core, ~30-60 min total, after heat61h (5-core directive).
"""
import json

import numpy as np
from scipy.linalg import eigh

import heat61_w_search as H
import heat61e_gram_ladder as E

OUTSTEM = "heat62_random_basis_ladder"
LGRID = E.LGRID
DX23 = 2 * LGRID / (1 << 23)
XS23 = -LGRID + DX23 * np.arange(1 << 23)
EPS = 2.22e-16
MUTANT8_LMIN = 3.066441e-13   # heat61e/f M=8 reference
SEEDS = (1, 2, 3, 4, 5)


def draw(family, rng, m):
    """Random genome dictionaries per family, in each winner family's OWN
    schema (LC's real schema is terms of [a, p] with p prime — mirror of
    realize's else-branch; BUMP is new)."""
    gs = []
    for _ in range(m):
        if family == "LA-rand":
            nterm = rng.integers(2, 5)
            gs.append({"terms": [
                [float(rng.uniform(-1, 1)), float(rng.uniform(-15, 15)),
                 float(rng.uniform(0.5, 5.0))] for _ in range(nterm)]})
        elif family == "LB-rand":
            npair = int(rng.integers(2, 6))
            gs.append({"c": float(rng.uniform(0.5, 2.0)),
                       "pairs": [[float(rng.uniform(-15, 15)),
                                  float(rng.uniform(-1, 1))] for _ in range(npair)]})
        elif family == "LC-rand":
            nm = int(rng.integers(2, 6))
            ps = rng.choice(H.PRIMES_C, size=nm)
            gs.append({"terms": [[float(rng.uniform(-1, 1)), float(p)] for p in ps]})
        else:  # BUMP
            nb = int(rng.integers(2, 6))
            gs.append({"bumps": [[float(rng.uniform(-1, 1)),
                                  float(rng.uniform(-15, 15)),
                                  float(rng.uniform(0.5, 5.0))] for _ in range(nb)]})
    return gs


def realize_any(family, g, xs):
    """E.realize for the three winner families (H.window applied inside);
    BUMP builds compact support then applies the SAME window for class
    admissibility (the window is part of the admissible class's definition).
    """
    if family == "BUMP":
        f = np.zeros_like(xs)
        for c, mu, s in g["bumps"]:
            t = (xs - mu) / s
            msk = np.abs(t) < 1.0
            f[msk] += c * np.exp(-1.0 / (1.0 - t[msk] ** 2))
        return f * H.window(xs)
    lin = {"LA-rand": "LA", "LB-rand": "LB", "LC-rand": "LC"}[family]
    return E.realize(lin, g, xs)


def gram_schmidt(F, dx):
    """Orthonormalize rows over L2(dx); returns (Q, max|G-I|).

    Carries heat61e's SMOKE LESSON forward: on near-dependent draws GS
    manufactures cancellation-remainder noise directions — guarded here by a
    RELATIVE remainder DQ (remainder norm must be >= 1e-3 of the incoming
    draw's norm; absolute-threshold guards miss normalized noise)."""
    B = []
    for f in F:
        n_in = np.sqrt(dx * (f * f).sum())
        if n_in < 1e-12:
            return None, None
        q = f.copy()
        for b in B:
            q = q - dx * (q * b).sum() * b
        nr = np.sqrt(dx * (q * q).sum())
        if nr < 1e-3 * n_in:
            return None, None   # near-dependent draw -> trial DQ'd
        B.append(q / nr)
    Q = np.array(B)
    G = dx * (Q @ Q.T)
    return Q, float(np.abs(G - np.eye(len(Q))).max())


if __name__ == "__main__":
    print("CATEGORY: D (B2 random-basis + B3 compact-support exposure; "
          "zero-side-primary; pre-registered + hash-committed)", flush=True)
    res = {}
    best = None
    fam_idx = {"LA-rand": 11, "LB-rand": 23, "LC-rand": 37, "BUMP": 53}
    for family in ("LA-rand", "LB-rand", "LC-rand", "BUMP"):
        for seed in SEEDS:
            rng = np.random.default_rng(1000 * seed + fam_idx[family])
            for m_basis in (8, 16):
                gs = draw(family, rng, m_basis)
                F0 = np.array([realize_any(family, g, XS23) for g in gs])
                Q, ortho_err = gram_schmidt(F0, DX23)
                tag = f"{family}/s{seed}/M{m_basis}"
                if Q is None:
                    print(f"{tag}: DEGENERATE DRAW — DQ", flush=True)
                    res[tag] = {"dq": "degenerate-draw"}
                    continue
                G = DX23 * (Q @ Q.T)
                Kz, nz, _ = E.zero_side_gram(Q, XS23, DX23, 200.0)
                ev200 = eigh(0.5 * (Kz + Kz.T), G, eigvals_only=True)
                l200, lmax = float(ev200[0]), float(ev200[-1])
                floor = np.linalg.cond(G) * EPS * abs(lmax)
                Kz2, _, _ = E.zero_side_gram(Q, XS23, DX23, 150.0)
                l150 = float(eigh(0.5 * (Kz2 + Kz2.T), G, eigvals_only=True)[0])
                sat = abs(l150 - l200) <= 0.1 * abs(l200) if l200 != 0 else True
                dq = (not sat) or ortho_err > 1e-10
                res[tag] = {"lmin200": l200, "lmin150": l150, "floor": float(floor),
                            "condG": float(np.linalg.cond(G)), "ortho_err": ortho_err,
                            "dq": bool(dq)}
                if not dq and (best is None or l200 < best[1]):
                    best = (tag, l200)
                print(f"{tag}: lmin {l200:+.6e}  floor {floor:.1e}  "
                      f"cond {np.linalg.cond(G):.1f}  "
                      f"{'DQ' if dq else 'ok'}", flush=True)
                json.dump(res, open(f"{OUTSTEM}.results.json", "w"), indent=1)

    scored = [v["lmin200"] for v in res.values() if not v.get("dq")]
    if not scored or best is None:
        print("\n== ALL TRIALS DQ'd — instrument report, nothing scored ==",
              flush=True)
        json.dump({"res": res, "outcome": "all-dq"},
                  open(f"{OUTSTEM}.results.json", "w"), indent=1)
        raise SystemExit(0)
    lo = min(scored)
    print(f"\nbest trial: {best[0]} lmin {best[1]:+.6e} | "
          f"mutant-ladder M=8 reference +{MUTANT8_LMIN:.6e}", flush=True)
    if lo < -1e-11:
        v = "a-FREEZE"
    elif lo < MUTANT8_LMIN / 10:
        v = "b-RIDGE-GENERIC"
    elif lo >= MUTANT8_LMIN:
        v = "c-WINNER-EARNED"
    else:
        v = "d-FLOOR-CLASS-CLUSTER"
    json.dump({"res": res, "outcome": v},
              open(f"{OUTSTEM}.results.json", "w"), indent=1)
    print(f"\n== OUTCOME ({v}) — see docstring pre-registration ==", flush=True)
