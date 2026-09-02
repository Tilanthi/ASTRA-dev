"""heat41c — SPLIT-LAW EXTENSION into the GUE q bands (merges the
  heat41b split-law lane with the heat53 GUE-band pool).

  heat41b validated the landing-split closed form c = sqrt(-2A'/G_zz)
  8/8 rows at 4 full-pool sites (devs -1.99%..+0.72%). heat53 then ran
  the b_c census at 16 sites in the two GUE q bands (q_far 0.0021-
  0.0223). Those sites' pencil machinery is on disk; this script runs
  heat41b's run_site VERBATIM (imported, not retyped — trap #60) on
  the 15 GUE-band indices NOT already in heat41b (5573 overlaps;
  G: 452 1747 1935 3149 3793 4086 4531; W40: 158 888 1579 2513 3357
  4196 4876 5524 — selection re-derived by the heat53 rule verbatim).

  PRE-REGISTERED (fresh thresholds per trap #18; written pre-run):
    Q1: c_census within 5% of c_theory at >= 22/30 rows (15 sites x 2
        above-rows). FALSIFIER: > 10% off at >= 6 rows => the split law
        fails in the GUE q bands.
    Q2: drift-sign agreement: landed-pair midpoint on the side the
        drift rate predicts (order-only, secondary; per-row across all
        sites; heat41b had 1.5x-low drift magnitude at W).
    Q3 [reproducibility, not new physics]: per-site b_c census error
        matches heat53's recorded errors within 0.3 pp (same machinery,
        cross-run check; trap #36 discipline).
  Traps: #36 (quote outputs), #38/#39/#41/#43 (via heat41b imports),
  #58 (__main__ guard; Pool(2) — heat54 holds the core grant until its
  stream stage drains).

  RESTART NOTE (honest record): first launch crashed AFTER pool.map
  completed — band_of was dict(SITES) which maps band->index, KeyError
  on the first reported row; ~1.5 h of site compute discarded by the
  reporting bug. Fixed here: {i: band} map + results persisted to JSON
  immediately after pool.map, before any reporting (a reporting crash
  can no longer discard compute).
"""
import json
import multiprocessing as mp_proc
from heat41b_split_pool import run_site

G_BAND = [452, 1747, 1935, 3149, 3793, 4086, 4531]
W40_BAND = [158, 888, 1579, 2513, 3357, 4196, 4876, 5524]
SITES = [(("G", i) if i in G_BAND else ("W40", i)) for i in G_BAND + W40_BAND]

if __name__ == "__main__":
    with mp_proc.Pool(2) as pool:
        results = pool.map(run_site, [i for _, i in SITES])
    band_of = {i: b for b, i in SITES}
    json.dump({"results": results},
              open("heat41c_split_gueband.results.json", "w"), indent=1)
    npass5 = 0; nfail10 = 0; ntest = 0; q2_agree = 0; q2_tot = 0
    for r in results:
        band = band_of[r["i"]]
        head = (f"\n[{band}] site i={r['i']} h={r['h']:.1f} d={r['d']:.3f} "
                f"eps1={r['eps1']:+.3f}")
        if r["status"] != "OK":
            print(head + f"  status={r['status']}", flush=True)
            continue
        print(head, flush=True)
        print(f"  bc_model={r['bc_model']:.4f} bc_census={r['bc_census']:.4f} "
              f"({r['err_bc']:+.2f}%) r2={r['r2_census']:.5f}", flush=True)
        print(f"  merge: x_m={r['x_m']:.5f} b_m={r['b_m']:.5f} "
              f"c_theory={r['c_theory']:.5f} drift={r['drift']:+.4f}", flush=True)
        for b, xh, xl, c_cn in r["above"]:
            ntest += 1
            dev = 100*(r["c_theory"]/c_cn - 1)
            ok5, bad10 = abs(dev) < 5, abs(dev) > 10
            npass5 += ok5
            nfail10 += bad10
            q2_tot += 1
            agree = ((xh+xl)/2 - r["x_m"])*r["drift"] > 0
            q2_agree += agree
            print(f"  b={b:.4f}: pair x=({xl:+.5f},{xh:+.5f}) c_census={c_cn:.5f} "
                  f"dev {dev:+.2f}% {'PASS' if ok5 else ('FALSIFIER-ROW' if bad10 else 'off')}"
                  f" | driftside {'Y' if agree else 'N'}", flush=True)
    print(f"\nQ1: {npass5}/{ntest} rows within 5% "
          f"(pre-reg PASS needs >= 22); >10%-off rows: {nfail10} "
          f"(FALSIFIER at >= 6)", flush=True)
    print(f"Q2: drift-side agreement {q2_agree}/{q2_tot} rows", flush=True)
    print(f"Q3: per-site err_bc above; compare vs heat53 .out census "
          f"errors (within 0.3 pp expected)", flush=True)
    print("done", flush=True)
