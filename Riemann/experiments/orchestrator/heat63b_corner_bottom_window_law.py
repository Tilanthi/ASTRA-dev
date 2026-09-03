"""heat63b — CORNER BOTTOM + WINDOW LAW: the two measurable objects that
replace the dead rate-alpha question, with draws that live inside the
class support.

CATEGORY: D (W(f)/Weil positivity lane — windowed-class structure)

WHY: heat63 (hash 5e9f51ca, verdict (d)-INSTRUMENT) refuted its own
pre-registered prescription: it widened the draw ranges, but the
admissible class is COMPACTLY SUPPORTED (window theta((8-|x|)/2): full
support |x|<=6, zero at |x|>=8) — far-centered draws window to near-zero
clones (LB 10/10, LA M=32 5/5 degenerate) AND broad survivors raise
lmax, hence the per-trial floor, pushing near-null readings under their
own resolution. Wide was backwards on BOTH axes. What survived said the
real things: BUMP (compact support) is the only family whose dimension
endures (nested s3: M16 +1.2228e-10 -> M32 +4.8835e-12, monotone ok);
LC blind (+0.133/+0.026, T-sat DQ, known slow tail).

THE TWO OBJECTS (this run):
  1. CORNER BOTTOM: with IN-SUPPORT draws (mu in U(-5.5,5.5), sigma
     log-U [0.3,2.5], nterm 2-6), the per-family minimum genuine
     lambda_min at the largest surviving M — the bottom of the windowed
     class corner reachable by random spans, with floors.
  2. WINDOW LAW: the SAME genomes re-windowed at W0=(6,8), W1=(10,14),
     W2=(16,20) (paired design: same seed => same draws => differences
     are pure window effects). Pre-stated readings:
       MONOTONE-DEEPENING: corner bottom shrinks as the window widens
         => the near-null ridge is scale-extended; consistent with B1
         (inf Q = 0, unattained) — record ratios lambda_min(W1)/lambda_min(W0) etc.
       NOT-DEEPENING: flat or rising => a scale-tied positive floor;
         B1 requires revision for the windowed class family-by-family.
  W2 CAVEAT (pre-stated): the W2 taper ends exactly at the grid edge
  (|x|=20 on the LGRID=20 grid) — zero margin for FFT wrap-around;
  W2 readings carry a boundary caveat and W1 is the primary widening
  rung. Per-trial floors + T-sat inherited; genuine gate >= 10x floor;
  below-resolution reported separately, excluded from conclusions.

PRE-REGISTRATION (trap #32; hash committed on the exchange BEFORE first
scored evaluation; trap #68 rules applied; NEW discipline from heat63's
self-refutation: the DIAGNOSIS is pre-registered SEPARATELY from the
outcome — if (d) fires again, the attached fix is itself falsifiable
and adjudication must test it, not assume it):
  Trials (nested per family/seed/window, 1 core):
    W0=(6,8):  LA x3 seeds x M{8,16,32}; LB x3 x M{8,16};
               BUMP x3 x M{8,16,32,64}
    W1=(10,14), W2=(16,20): BUMP x2 x M{16,32}; LA x2 x M{16,32}
  Outcome (a) FREEZE: genuine lambda_min < -1e-11 -> inherited protocol.
  Outcome (b) MEASURED: corner bottoms per family with >= 10x-floor
      margins + the paired window ratios; both window-law readings
      pre-stated above — report which fires, per family.
  Outcome (c) FLOOR-CLASS: best readings under 10x floor -> bounds only.
  Outcome (d) INSTRUMENT: > 50% of a family's trials degenerate at
      M<=32 EVEN with in-support draws -> the saturation is a property
      of the family corners, not the draw ranges (diagnosis tested, not
      assumed); report d_eff lower bounds (first GS rejection position).
  Instrument falsifiers: T-sat |l150-l200| > 0.1|l200| -> DQ; GS
      relative remainder < 1e-3 -> DQ at that position (record it);
      |G-I|_max > 1e-10 -> DQ.

CPU: single core, ~1.5-2.5 h (5-core directive).
"""
import json

import numpy as np
from scipy.linalg import eigh

import heat61_w_search as H
import heat61e_gram_ladder as E
import heat62_random_basis_ladder as B

OUTSTEM = "heat63b_corner_bottom_window_law"
LGRID = E.LGRID
DX23 = 2 * LGRID / (1 << 23)
XS23 = -LGRID + DX23 * np.arange(1 << 23)
EPS = 2.22e-16
FAM_IDX = {"LA-rand": 11, "LB-rand": 23, "LC-rand": 37, "BUMP": 53}
WINDOWS = {"W0": (6.0, 8.0), "W1": (10.0, 14.0), "W2": (16.0, 20.0)}


def draw_insupport(family, rng, m):
    """In-support genomes: centers inside the full-support zone |x|<5.5,
    widths small enough that broad terms stay inside the taper."""
    gs = []
    for _ in range(m):
        nt = int(rng.integers(2, 7))
        if family == "LA-rand":
            gs.append({"terms": [
                [float(rng.uniform(-1, 1)), float(rng.uniform(-5.5, 5.5)),
                 float(np.exp(rng.uniform(np.log(0.3), np.log(2.5))))]
                for _ in range(nt)]})
        elif family == "LB-rand":
            gs.append({"c": float(rng.uniform(0.5, 2.0)),
                       "pairs": [[float(rng.uniform(-5.5, 5.5)),
                                  float(rng.uniform(-1, 1))] for _ in range(nt)]})
        elif family == "LC-rand":
            ps = rng.choice(H.PRIMES_C, size=nt)
            gs.append({"terms": [[float(rng.uniform(-1, 1)), float(p)] for p in ps]})
        else:  # BUMP
            gs.append({"bumps": [
                [float(rng.uniform(-1, 1)), float(rng.uniform(-5.5, 5.5)),
                 float(np.exp(rng.uniform(np.log(0.3), np.log(2.5))))]
                for _ in range(nt)]})
    return gs


def gs_saturating(F, dx):
    """GS that records the first rejection position (d_eff lower bound)
    and returns the partial orthonormal set built up to rejection."""
    Qs = []
    for i, f in enumerate(F):
        n_in = np.sqrt(dx * (f * f).sum())
        if n_in < 1e-12:
            return None, i, None
        q = f.copy()
        for b in Qs:
            q = q - dx * (q * b).sum() * b
        nr = np.sqrt(dx * (q * q).sum())
        if nr < 1e-3 * n_in:
            return None, i, None   # saturated at position i
        Qs.append(q / nr)
    Q = np.array(Qs)
    G = dx * (Q @ Q.T)
    return Q, None, float(np.abs(G - np.eye(len(Q))).max())


def trial(family, seed, m_basis, win):
    H.CUT_IN, H.CUT_OUT = WINDOWS[win]      # window read at realize time
    rng = np.random.default_rng(3000 * seed + FAM_IDX[family])
    gs = draw_insupport(family, rng, m_basis)
    F0 = np.array([B.realize_any(family, g, XS23) for g in gs])
    Q, sat_pos, oerr = gs_saturating(F0, DX23)
    tag = f"{win}/{family}/s{seed}/M{m_basis}"
    if Q is None:
        return tag, {"dq": "degenerate-draw", "sat_pos": sat_pos}
    G = DX23 * (Q @ Q.T)
    Kz, nz, _ = E.zero_side_gram(Q, XS23, DX23, 200.0)
    ev = eigh(0.5 * (Kz + Kz.T), G, eigvals_only=True)
    l200, lmax = float(ev[0]), float(ev[-1])
    floor = float(np.linalg.cond(G)) * EPS * abs(lmax)
    Kz2, _, _ = E.zero_side_gram(Q, XS23, DX23, 150.0)
    l150 = float(eigh(0.5 * (Kz2 + Kz2.T), G, eigvals_only=True)[0])
    sat = abs(l150 - l200) <= 0.1 * abs(l200) if l200 != 0 else True
    dq = (not sat) or oerr > 1e-10
    gen = (not dq) and abs(l200) >= 10 * floor
    return tag, {"lmin200": l200, "floor": floor, "condG": float(np.linalg.cond(G)),
                 "ortho_err": oerr, "dq": bool(dq), "genuine": bool(gen), "nz": int(nz)}


if __name__ == "__main__":
    print("CATEGORY: D (corner bottom + window law; in-support draws; "
          "pre-registered + hash-committed)", flush=True)
    res = {}
    jobs = ([("W0", f, s, m) for f, ms in (("LA-rand", (8, 16, 32)),
                                           ("LB-rand", (8, 16)),
                                           ("BUMP", (8, 16, 32, 64)))
             for s in (1, 2, 3) for m in ms]
            + [("W1", f, s, m) for f in ("BUMP", "LA-rand")
               for s in (1, 2) for m in (16, 32)]
            + [("W2", f, s, m) for f in ("BUMP", "LA-rand")
               for s in (1, 2) for m in (16, 32)])
    for win, fam, seed, m in jobs:
        tag, row = trial(fam, seed, m, win)
        res[tag] = row
        if "lmin200" in row:
            g = "GENUINE" if row["genuine"] else ("below-res" if not row["dq"] else "DQ")
            print(f"{tag}: lmin {row['lmin200']:+.6e}  floor {row['floor']:.1e}  [{g}]",
                  flush=True)
        else:
            print(f"{tag}: degenerate at position {row['sat_pos']}", flush=True)
        json.dump(res, open(f"{OUTSTEM}.results.json", "w"), indent=1)

    # corner bottoms per family (W0) + paired window ratios
    print("\n== W0 corner bottoms (largest surviving M per family) ==", flush=True)
    for fam in ("LA-rand", "LB-rand", "BUMP"):
        for m in (64, 32, 16, 8):
            rows = [v for k, v in res.items()
                    if k.startswith(f"W0/{fam}/") and k.endswith(f"/M{m}")
                    and v.get("genuine")]
            if rows:
                print(f"  {fam} M={m}: min {min(r['lmin200'] for r in rows):+.6e} "
                      f"(n={len(rows)})", flush=True)
                break
    print("\n== paired window ratios (same family/seed/M across windows) ==",
          flush=True)
    for fam in ("BUMP", "LA-rand"):
        for s in (1, 2):
            for m in (16, 32):
                vals = {}
                for w in ("W0", "W1", "W2"):
                    r = res.get(f"{w}/{fam}/s{s}/M{m}", {})
                    if r.get("genuine"):
                        vals[w] = r["lmin200"]
                if len(vals) >= 2:
                    rat = "  ".join(f"{w}:{vals[w]:+.3e}" for w in sorted(vals))
                    print(f"  {fam}/s{s}/M{m}: {rat}", flush=True)
    json.dump({"res": res}, open(f"{OUTSTEM}.results.json", "w"), indent=1)
    print("\n== verdict per docstring (a)/(b)/(c)/(d); diagnosis tested "
          "separately from outcome ==", flush=True)
