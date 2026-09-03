"""heat69 — BUMP M=128: the M-descent RATE rung (Weil/window lane, CATEGORY D).

Extends heat63b's W0 BUMP ladder (M8/16/32/64, seeds s1-s3) to M=128. The
object: per-seed log-log slope alpha of lambda_min ~ c M^-alpha on GENUINE
(>=10x floor) points, and whether the descent CONTINUES at 128 or STALLS.

CATEGORY: D. Pre-registered + hash-committed on the exchange BEFORE first
scored evaluation (trap #32); trap #68 clause 1 floors per rung; trap #78:
floors printed at their evaluation point alongside every reading.

NESTING / MONOTONICITY FALSIFIER (inherited from heat63/63b): same seed =>
same rng stream => the first 64 genomes are bitwise identical to heat63b's
M=64 basis, so lambda_min(128) <= lambda_min(64) to float accuracy.
Violation threshold 5% (lambda128 > 1.05*lambda64): eigh relative noise on
lambda~1e-10 with condG~1 is ~1e-4, so 5% is 50x beyond instrument noise
while a stream/inheritance bug gives O(1) differences. Violation => INSTRUMENT
halt, no readings scored.

MEMORY HARDENING (disclosed in prereg; same math, bitwise-identical float ops
as heat63b's gs_saturating): in-place GS on a single preallocated
(M x 2^23) array (heat63b materialized F0 + Q list + np.array copy, ~3x
footprint). Projection order and expressions match gs_saturating exactly, so
Q[0:64] is bitwise the M=64 basis. Orthonormality validated identically via
|G - I|_max > 1e-10 => DQ. Peak RSS ~9-10 GB (34 GB machine verified).

Pre-stated outcomes (registered in the exchange letter before the run):
  (a)  FREEZE: any genuine lambda_min < -1e-11 -> inherited protocol.
  (b1) RATE-CONTINUES: M=128 genuine and lambda_min(128) < 0.5*lambda_min(64)
       for BOTH comparable seeds (s1, s3; s2's M64 is DQ) -> fit alpha per
       seed on genuine points M8..128, report c, alpha, cross-seed spread,
       and the extrapolation table (M needed for 1e-13 / 1e-16, feasibility
       caveat stated).
  (b2) DESCENT-STALLS: M=128 genuine but BOTH comparable seeds have
       lambda_min(128) >= 0.5*lambda_min(64) -> the BUMP corner bottom stops
       descending at M~64-128: B1 revision for the windowed class; report
       sat_pos / d_eff diagnostics alongside.
  (c)  INCONCLUSIVE/BOUND: anything else (mixed continuation, floor-limited,
       single-comparable-seed) -> rate unresolved at this M; per-seed values
       reported, no rate claim.
  (d)  INSTRUMENT: >=2 of 3 seeds degenerate-draw at M=128 (sat_pos < 128)
       -> d_eff cap diagnosis: basis exhaustion, not class bottom.

Falsifiers inherited: T-sat |l150-l200| > 0.1|l200| => DQ; GS relative
remainder < 1e-3 at position i => degenerate-draw DQ (sat_pos recorded);
|G-I|max > 1e-10 => DQ.

CPU: 1 process, threads pinned (OMP/VECLIB = 2) to respect the 5-core
directive; heat68b probe keeps its own core.
"""
import os
for _v in ("OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "2")
import json, time, hashlib
import numpy as np
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("h63b", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heat63b_corner_bottom_window_law.py"))
h63b = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(h63b)
B, H, E = h63b.B, h63b.H, h63b.E
eigh = h63b.eigh                     # scipy.linalg.eigh (generalized), as in heat63b
WINDOWS, DX23, XS23 = h63b.WINDOWS, h63b.DX23, h63b.XS23
FAM_IDX_BUMP, EPS = h63b.FAM_IDX["BUMP"], h63b.EPS
W0 = "W0"

RES_BASE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "heat63b_corner_bottom_window_law.results.json")))["res"]


def trial_m128(seed, m_basis=128):
    H.CUT_IN, H.CUT_OUT = WINDOWS[W0]
    rng = np.random.default_rng(3000 * seed + FAM_IDX_BUMP)
    gs = h63b.draw_insupport("BUMP", rng, m_basis)
    tag = f"{W0}/BUMP/s{seed}/M{m_basis}"
    # --- in-place GS: identical expressions/order to gs_saturating ---
    Q = np.empty((m_basis, XS23.size))
    sat_pos = None
    for i, g in enumerate(gs):
        f = B.realize_any("BUMP", g, XS23)
        n_in = np.sqrt(DX23 * (f * f).sum())
        if n_in < 1e-12:
            sat_pos = i
            break
        for j in range(i):
            f = f - DX23 * (f * Q[j]).sum() * Q[j]
        nr = np.sqrt(DX23 * (f * f).sum())
        if nr < 1e-3 * n_in:
            sat_pos = i
            break
        Q[i] = f / nr
    if sat_pos is not None:
        return tag, {"dq": "degenerate-draw", "sat_pos": sat_pos}
    G = DX23 * (Q @ Q.T)
    oerr = float(np.abs(G - np.eye(m_basis)).max())
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


def alpha_fit(pts):
    """pts = [(M, lambda)]. Least-squares slope of log|lambda| vs log M."""
    xs = np.log([p[0] for p in pts]); ys = np.log([abs(p[1]) for p in pts])
    if len(pts) < 3:
        return None
    return float(np.polyfit(xs, ys, 1)[0])


if __name__ == "__main__":
    sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    print("CATEGORY: D — BUMP M=128 M-descent rate rung (pre-registered, hash-committed)", flush=True)
    print("runner sha256:", sha, flush=True)
    print("baseline (heat63b W0 BUMP):", {k: v["lmin200"] for k, v in sorted(RES_BASE.items()) if "BUMP" in k and k.startswith("W0")}, flush=True)
    t0 = time.time()
    res, n_deg, mono_violation = {}, 0, False
    for seed in (1, 2, 3):
        tag, row = trial_m128(seed)
        res[tag] = row
        print(tag, "->", row, flush=True)
        b64 = RES_BASE.get(f"W0/BUMP/s{seed}/M64")
        if "dq" in row:
            n_deg += 1
            continue
        if b64 and "lmin200" in b64:
            mono = row["lmin200"] <= 1.05 * b64["lmin200"]
            print(f"  monotonicity vs M64 ({b64['lmin200']:+.6e}): {'OK' if mono else 'VIOLATION -> INSTRUMENT HALT'}", flush=True)
            if not mono:
                mono_violation = True
                break
    outcome = None
    if mono_violation:
        outcome = "HALT-instrument-monotonicity"
    else:
        cont = stall = 0
        for seed in (1, 2, 3):
            r = res.get(f"W0/BUMP/s{seed}/M128")
            b = RES_BASE.get(f"W0/BUMP/s{seed}/M64")
            if r and r.get("genuine") and b and b.get("genuine"):
                if r["lmin200"] < 0.5 * b["lmin200"]:
                    cont += 1
                else:
                    stall += 1
        freeze = any(r.get("genuine") and r["lmin200"] < -1e-11
                     for r in res.values() if "lmin200" in r)
        for seed in (1, 2, 3):
            r = res.get(f"W0/BUMP/s{seed}/M128")
            if r and r.get("genuine"):
                pts = [(m, RES_BASE[f"W0/BUMP/s{seed}/M{m}"]["lmin200"])
                       for m in (8, 16, 32, 64)
                       if RES_BASE.get(f"W0/BUMP/s{seed}/M{m}", {}).get("genuine")]
                pts.append((128, r["lmin200"]))
                a = alpha_fit(pts)
                print(f"  s{seed}: alpha = {a if a is None else round(a, 4)} on {len(pts)} genuine pts", flush=True)
                if a:
                    for tgt in (1e-13, 1e-16):
                        m_need = 128 * (abs(r["lmin200"]) / tgt) ** (1.0 / a)
                        print(f"    extrapolated M for {tgt:g}: {m_need:.3g} (memory ~ {m_need * XS23.size * 8 / 1e9:.3g} GB)", flush=True)
        if freeze:
            outcome = "a"
        elif n_deg >= 2:
            outcome = "d"
        elif cont >= 2:
            outcome = "b1"
        elif stall >= 2:
            outcome = "b2"
        else:
            outcome = "c"
    print(f"\nOUTCOME: ({outcome})", flush=True)
    print(f"total {time.time()-t0:.0f}s", flush=True)
    json.dump({"res": res, "outcome": outcome, "sha256": sha},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "heat69_bump_m128.results.json"), "w"), indent=1)
