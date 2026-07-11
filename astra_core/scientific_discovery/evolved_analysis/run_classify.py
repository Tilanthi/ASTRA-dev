"""run_classify.py — WP5: the engine on a SECOND real task (SDSS classification).

Proves generality: same EvolutionEngine + leapcore FitnessEvaluator pattern, now
on a classification problem (STAR/GALAXY/QSO) graded by balanced accuracy — a
different problem type and metric than photo-z, on real spectroscopic labels.
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from .leapcore import Chromosome, EvolutionConfig
from .cls_data import load_split  # triggers fetch+cache
from .cls_program import NAIVE_SEED_SOURCE, NAIVE_SPEC, SYSTEM, ENTRY
from .cls_evaluator import ClsEvaluator
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
    print("WP5 — engine on a SECOND real task: SDSS STAR/GALAXY/QSO classification")
    print("(balanced accuracy · different problem type + metric than photo-z)")
    print("=" * 76)
    # ensure data present
    splits = load_split(seed=args.seed)
    print(f"data: {len(splits['train'])}/{len(splits['eval'])}/{len(splits['test'])} "
          f"train/eval/test (REAL, balanced)")

    evaluator = ClsEvaluator(seed=args.seed, timeout=90)
    proposer = LLMProposer(model=FAST, context_level="rich",
                           task_system=SYSTEM, entry_point=ENTRY)
    archive = MAPElitesArchive(seed=args.seed)
    seed_ch = Chromosome(chromosome_id="seed", genes={}, fitness=0.0, generation=0,
                         metadata={"source": NAIVE_SEED_SOURCE, "spec": NAIVE_SPEC,
                                   "origin": "seed"})
    cfg = EvolutionConfig(population_size=args.pop, elite_count=2, tournament_size=3)
    eng = EvolutionEngine(evaluator, proposer, seed_ch, config=cfg,
                          rng=np.random.default_rng(args.seed), archive=archive,
                          propose_opts={"context_level": "rich"})
    t0 = time.time()
    for g in range(1, args.generations + 1):
        row = eng.step()
        print(f"  gen {g:02d}  best bal_acc={row['best_sigma'] if False else eng.best().fitness:.4f}  "
              f"cells={archive.diversity()}  children={row['n_children']}  t={time.time()-t0:.0f}s")
    best = eng.best()
    seed_test = evaluator.evaluate_split(NAIVE_SEED_SOURCE, "test")
    best_test = evaluator.evaluate_split(best.metadata["source"], "test")
    print("\n" + "=" * 76)
    print(f"engine stats: proposals={eng.stats['proposals']} "
          f"accepted={eng.stats['accepted']} improved_parent={eng.stats['improved_parent']}")
    print(f"seed  TEST balanced_acc = {seed_test['balanced_accuracy']:.4f}  ->  "
          f"best TEST balanced_acc = {best_test['balanced_accuracy']:.4f}")
    print(f"  per-class recall (best): STAR={best_test.get('recall_STAR',0):.2f} "
          f"GALAXY={best_test.get('recall_GALAXY',0):.2f} QSO={best_test.get('recall_QSO',0):.2f}")
    print(f"archive families: {archive.summary()['by_family']}")
    print("VERDICT:", "PASS — engine generalises to a second real task + metric"
          if best_test["balanced_accuracy"] > seed_test["balanced_accuracy"] + 0.05
          else "CHECK")

    if best_test["balanced_accuracy"] > seed_test["balanced_accuracy"] + 0.05:
        from .discovery_emit import emit_verified_discovery
        _sp = load_split(args.seed)
        rec = emit_verified_discovery(
            task="classification", program_source=best.metadata["source"],
            eval_metrics=best.metadata.get("metrics", {}), held_out_metrics=best_test,
            data_source="SDSS CAS (real STAR/GALAXY/QSO, balanced)",
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
