"""run_engine.py — WP2 demo: the promoted EvolutionEngine on real photo-z.

Verifies the canonical engine (reusing the real leapcore classes, RNG-injected,
proposer-driven, with rec-4 CV evaluator + MAP-Elites archive composed in)
reproduces the LLM-driven improvement on real SDSS data.
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from .leapcore import EvolutionConfig
from .program import NAIVE_SEED_SOURCE, NAIVE_SPEC
from .leapcore import Chromosome
from .evaluator import RealDataProgramEvaluator
from .selection import SelectionEvaluator
from .archive import MAPElitesArchive
from .proposer import LLMProposer
from .engine import EvolutionEngine

FAST = "claude-haiku-4-5-20251001"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=4)
    ap.add_argument("--pop", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--stan", action="store_true",
                    help="narrate via ASTRA STAN (default OFF: STAN answer() currently returns canned content ignoring the prompt)")
    args = ap.parse_args()
    print("=" * 76)
    print("WP2 — promoted EvolutionEngine on real photo-z")
    print("(real leapcore classes · RNG-injected · proposer-driven · CV eval + MAP-Elites)")
    print("=" * 76)
    base = RealDataProgramEvaluator(seed=args.seed, timeout=90)
    evaluator = SelectionEvaluator(base, K=5, cascade=True,
                                   cascade_thresh=0.08, parsimony_weight=0.002)
    proposer = LLMProposer(model=FAST, context_level="rich")
    archive = MAPElitesArchive(seed=args.seed)
    seed_ch = Chromosome(chromosome_id="seed", genes={}, fitness=0.0, generation=0,
                         metadata={"source": NAIVE_SEED_SOURCE, "spec": NAIVE_SPEC,
                                   "origin": "seed"})
    cfg = EvolutionConfig(population_size=args.pop, elite_count=2,
                          tournament_size=3)
    eng = EvolutionEngine(evaluator, proposer, seed_ch, config=cfg,
                          rng=np.random.default_rng(args.seed), archive=archive,
                          propose_opts={"context_level": "rich"})
    t0 = time.time()
    for g in range(1, args.generations + 1):
        row = eng.step()
        b = eng.best()
        print(f"  gen {g:02d}  best CV σ={row['best_sigma']:.4f}  "
              f"cells={archive.diversity()}  children={row['n_children']}  "
              f"t={time.time()-t0:.0f}s")
    best = eng.best()
    test = base.evaluate_split(best.metadata["source"], "test")
    seed_test = base.evaluate_split(NAIVE_SEED_SOURCE, "test")
    print("\n" + "=" * 76)
    print(f"engine stats: proposals={eng.stats['proposals']} "
          f"accepted={eng.stats['accepted']} improved_parent={eng.stats['improved_parent']}")
    print(f"seed TEST σ = {seed_test['sigma_nmad']:.4f}  ->  best TEST σ = {test['sigma_nmad']:.4f}  "
          f"(eta {test['eta']:.3f})  family={archive.summary()['by_family']}")
    print(f"best CV σ   = {best.metadata['metrics']['sigma_nmad']:.4f}  "
          f"|CV−TEST| gap = {abs(best.metadata['metrics']['sigma_nmad']-test['sigma_nmad']):.4f}")
    print("VERDICT:", "PASS — promoted engine drives real improvement on real data"
          if test["sigma_nmad"] < seed_test["sigma_nmad"] else "CHECK — no improvement")

    if test["sigma_nmad"] < seed_test["sigma_nmad"]:
        from .discovery_emit import emit_verified_discovery
        from .real_data import load_split as _ls
        _sp = _ls(args.seed)
        rec = emit_verified_discovery(
            task="photoz", program_source=best.metadata["source"],
            eval_metrics=best.metadata.get("metrics", {}),
            held_out_metrics=test, data_source="SDSS CAS (real galaxies)",
            n_train=len(_sp["train"]), n_eval=len(_sp["eval"]),
            n_test=len(_sp["test"]), use_stan=args.stan)
        print(f"emit ASTRA discovery -> ~/.astra_persistent/evolved_discoveries.json")
        print(f"  title: {rec['title']}")
        print(f"  verification: {rec['verification']['metric_name']}="
              f"{rec['verification']['eval_value']} (TEST="
              f"{rec['verification']['held_out_test_value']}) "
              f"stan_narrated={rec['verification']['stan_narrated']}")


if __name__ == "__main__":
    main()
