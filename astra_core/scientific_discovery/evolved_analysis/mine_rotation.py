"""mine_rotation.py — Sub-project C scale lever.

Mines the productive (non-textbook-saturated) data-lake datasets in sequence,
running the Phase-2 two-gate claim search on each. This is the durable "scale"
lever: one command that focuses effort on the niches that yield novelty (galaxy
morphology, QSO colour×redshift interactions) and skips the textbook-saturated
stellar samples (sdss_stars, gaia_nearby — ~100% "known" in pilots) by default.

The 2026-07-14 pilots showed novelty is rare and roughly linear in candidate-
evals, and that object type matters (stars -> 0 novel; galaxies/QSOs -> some).
So scaling = mine the productive niches repeatedly.

Run (token must be in the env, e.g. sourced from ~/.astra_persistent/llm_env):
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.mine_rotation --steps 30
    # also mine the textbook-saturated datasets (usually low-novelty):
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.mine_rotation --steps 30 --include-high-risk
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .data_lake import productive_datasets, list_datasets, fetch_and_cache


_ROUND_ROBIN_POINTER = (Path.home() / ".astra_persistent" / "evolved_programs"
                        / "rotation_pointer.json")


def _round_robin_pick(datasets):
    """Pick ONE dataset, round-robin across invocations, via a persisted pointer.

    Lets the always-on supervisor mine a single niche per evolution episode
    (short, user-yielding) while cycling through all productive niches over time."""
    n = max(len(datasets), 1)
    idx = 0
    try:
        if _ROUND_ROBIN_POINTER.exists():
            idx = int(json.loads(_ROUND_ROBIN_POINTER.read_text()).get("next", 0)) % n
    except Exception:
        idx = 0
    picked = datasets[idx % n]
    try:
        _ROUND_ROBIN_POINTER.parent.mkdir(parents=True, exist_ok=True)
        _ROUND_ROBIN_POINTER.write_text(json.dumps({"next": (idx + 1) % n}))
    except Exception:
        pass
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Rotate the Phase-2 claim search across productive data-lake "
                    "datasets (the scale lever; skips textbook-saturated samples).")
    ap.add_argument("--steps", type=int,
                    default=int(os.environ.get("ASTRA_MINE_STEPS", "30")),
                    help="LLM-proposed candidates per dataset "
                         "(env: ASTRA_MINE_STEPS)")
    ap.add_argument("--include-high-risk", action="store_true",
                    help="also mine textbook-saturated datasets (stars/gaia) — "
                         "usually low-novelty")
    ap.add_argument("--no-gate2", action="store_true",
                    help="pass through to run_claim_search (Gate 1 only)")
    ap.add_argument("--round-robin", action="store_true",
                    help="mine ONE productive dataset per invocation, round-robin "
                         "(for the always-on supervisor; also enabled by "
                         "ASTRA_MINE_ROUND_ROBIN=1)")
    args = ap.parse_args()

    datasets = list_datasets() if args.include_high_risk else productive_datasets()
    datasets = [ds for ds in datasets if ds.fetcher is not None]
    if not datasets:
        print("[rotate] no minable datasets")
        return 1

    # Round-robin: mine one niche per call (supervisor-friendly: short episodes
    # that cycle galaxy morphology -> QSOs -> ... over successive episodes).
    if args.round_robin or os.environ.get("ASTRA_MINE_ROUND_ROBIN", "").lower() in (
            "1", "true", "yes"):
        picked = _round_robin_pick(datasets)
        datasets = [picked]
        print(f"[rotate] round-robin mode: mining one niche -> {picked.name}")

    print(f"[rotate] mining {len(datasets)} dataset(s), {args.steps} steps each: "
          f"{[d.name for d in datasets]}")
    repo = Path(__file__).resolve().parents[3]
    pypp = str(Path(__file__).resolve().parents[1])  # astra_core/scientific_discovery
    env = {**os.environ, "PYTHONPATH": pypp}
    last_rc = 0
    for ds in datasets:
        # Ensure the cache (network) BEFORE the sandboxed search reads it.
        try:
            fetch_and_cache(ds.name)
        except Exception as e:
            print(f"[rotate] SKIP {ds.name}: fetch failed ({type(e).__name__}: {e})")
            continue
        cmd = [sys.executable, "-m", "evolved_analysis.run_claim_search",
               "--data-source", ds.name, "--steps", str(args.steps)]
        if args.no_gate2:
            cmd.append("--no-gate2")
        # Self-improvement #1: predict-before-act (statistical baseline from history),
        # then after the run score surprise against actuals and append to the ledger.
        try:
            from .predictions import (predict_for_episode, write_prediction,
                                      episode_actuals, score_surprise, append_surprise)
            pred = predict_for_episode(ds.name)
            write_prediction(pred)
            print(f"[rotate] predict {ds.name}: gate1~{pred.predicted_gate1_pass_rate}, "
                  f"novel~{pred.predicted_novel_emits}, conf={pred.confidence:.2f} "
                  f"(n_hist={pred.n_history})")
        except Exception as e:
            pred = None
            print(f"[rotate] prediction skipped ({type(e).__name__})")
        print(f"[rotate] === {ds.name}: {args.steps} steps "
              f"({time.strftime('%H:%M:%S')}) ===")
        proc = subprocess.run(cmd, cwd=str(repo), env=env, check=False)
        last_rc = proc.returncode or last_rc
        if pred is not None:
            try:
                actuals = episode_actuals(ds.name, pred.ts)
                surprise = score_surprise(pred, actuals)
                append_surprise(pred, actuals, surprise)
                print(f"[rotate] surprise {ds.name}: {surprise} "
                      f"(actual gate1={actuals.get('gate1_pass_rate')}, "
                      f"novel={actuals.get('novel_emits')})")
            except Exception as e:
                print(f"[rotate] surprise scoring skipped ({type(e).__name__})")
    print(f"[rotate] done (last rc={last_rc})")
    return last_rc


if __name__ == "__main__":
    sys.exit(main())
