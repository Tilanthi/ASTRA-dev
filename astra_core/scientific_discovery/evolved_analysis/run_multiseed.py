"""run_multiseed.py — WP4: publication-grade multi-seed ablation (Fig-7 with error bars).

Runs the rec-3 ablation at multiple seeds and aggregates mean ± std per condition,
so per-feature deltas can be judged against run-to-run (LLM + selection) noise.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from .ablation import Ablation, CONDITIONS

PERSIST = Path.home() / ".astra_persistent" / "evolved_programs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123])
    args = ap.parse_args()
    t0 = time.time()
    per_cond = {n: {"test_sigma": [], "test_eta": [], "eval_sigma": [],
                    "improved": [], "valid": []} for n, _ in CONDITIONS}

    for s in args.seeds:
        print(f"\n===== SEED {s} =====", flush=True)
        ab = Ablation(n_steps=args.steps, seed=s)
        res = ab.run_all()
        for r in res:
            n = r["condition"]
            per_cond[n]["test_sigma"].append(r["best_test_sigma"])
            per_cond[n]["test_eta"].append(r["best_test_eta"])
            per_cond[n]["eval_sigma"].append(r["best_eval_sigma"])
            per_cond[n]["improved"].append(r["stats"]["improved"])
            per_cond[n]["valid"].append(r["stats"]["valid"])

    def ms(x):
        x = np.array(x, float)
        return float(np.mean(x)), float(np.std(x, ddof=1)) if len(x) > 1 else 0.0
    print("\n" + "=" * 80)
    print(f"MULTI-SEED ABLATION (seeds={args.seeds}, steps={args.steps}/cond) — "
          f"mean ± std on held-out TEST")
    print("=" * 80)
    print(f"{'condition':<13}{'TEST σ (mean±std)':>22}{'EVAL σ (mean±std)':>22}"
          f"{'improved/valid':>16}")
    agg = {}
    for n, _ in CONDITIONS:
        d = per_cond[n]
        tm, ts = ms(d["test_sigma"]); em, es = ms(d["eval_sigma"])
        im, _ = ms(d["improved"]); vm, _ = ms(d["valid"])
        agg[n] = {"test_sigma_mean": tm, "test_sigma_std": ts,
                  "eval_sigma_mean": em, "eval_sigma_std": es,
                  "improved_mean": im, "valid_mean": vm}
        print(f"{n:<13}{tm:>16.4f}±{ts:.4f}{em:>16.4f}±{es:.4f}"
              f"{im:>9.1f}/{vm:<5.1f}")
    print(f"\nelapsed: {time.time()-t0:.0f}s")
    out = PERSIST / "multiseed_ablation.json"
    out.write_text(json.dumps({"seeds": args.seeds, "steps": args.steps,
                               "per_condition": agg}, indent=2))
    print(f"log -> {out}")


if __name__ == "__main__":
    main()
