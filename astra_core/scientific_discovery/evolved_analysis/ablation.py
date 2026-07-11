"""ablation.py — Recommendation 3: an AlphaEvolve Fig-7-style ablation.

Runs the SAME real photo-z task under a staircase of conditions with an EQUAL
LLM-call budget, to measure the marginal effect of each cheap-ablation feature:

    floor_seed   re-seed from naive every step, minimal context   (≈ ASTRA today)
    no_context   memory ON, but proposer sees source only
    context      + rendered evaluation results (error profile) + inspirations
    ensemble     + route across a fast (Haiku) and powerful (Sonnet) model
    meta_prompt  + co-evolved strategy hints
    full         all of the above

Each condition gets the same number of LLM program-proposals and the same seed
for selection/routing. The LLM is non-deterministic, so this is a single-run
PRELIMINARY ablation (multi-seed averaging is the production version). Reports
held-out TEST sigma_NMAD/eta per condition + proposer stats.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from .leapcore import Chromosome
from .program import NAIVE_SEED_SOURCE, NAIVE_SPEC
from .evaluator import RealDataProgramEvaluator
from .proposer import LLMProposer
from .meta_prompt import HintSetPopulation

FAST_MODEL = "claude-haiku-4-5-20251001"
STRONG_MODEL = "claude-sonnet-5-20250929"

CONDITIONS = [
    ("floor_seed",  dict(evolution=False, context="minimal", ensemble=False, meta=False)),
    ("no_context",  dict(evolution=True,  context="minimal", ensemble=False, meta=False)),
    ("context",     dict(evolution=True,  context="rich",    ensemble=False, meta=False)),
    ("ensemble",    dict(evolution=True,  context="rich",    ensemble=True,  meta=False)),
    ("meta_prompt", dict(evolution=True,  context="rich",    ensemble=False, meta=True)),
    ("full",        dict(evolution=True,  context="rich",    ensemble=True,  meta=True)),
]


def _shash(src: str) -> str:
    return hashlib.sha1(src.encode()).hexdigest()[:12]


def _trim(src: str, n: int = 1200) -> str:
    return src if len(src) <= n else src[:n] + "\n# ... (truncated)"


def _niche(chrom: Chromosome):
    s = (chrom.metadata or {}).get("spec") or {}
    return (s.get("model", "llm"), len(s.get("color_pairs", []) or []),
            s.get("degree", 0)) if s else ("llm", -1, -1)


def _merge(pop, child, elite):
    merged = sorted(pop + [child], key=lambda c: c.fitness, reverse=True)
    kept, seen = [], set()
    for c in merged:
        if len(kept) >= elite:
            break
        nk = _niche(c)
        if nk in seen:
            continue
        seen.add(nk); kept.append(c)
    while len(kept) < elite and len(kept) < len(merged):
        kept.append(merged[len(kept)])
    return kept


class Ablation:
    def __init__(self, n_steps=12, elite=4, seed=42, eval_timeout=60):
        self.n_steps = n_steps
        self.elite = elite
        self.seed = seed
        self.eval_timeout = eval_timeout
        self.ev = RealDataProgramEvaluator(seed=seed, timeout=eval_timeout)
        self.cache: dict[str, float] = {}
        self.results = []

    def _eval(self, chrom):
        h = _shash(chrom.metadata["source"])
        if h in self.cache:
            chrom.fitness = self.cache[h][0]
            chrom.metadata["metrics"] = self.cache[h][1]
            return
        self.ev.evaluate(chrom)
        self.cache[h] = (chrom.fitness, chrom.metadata.get("metrics", {}))

    def run_condition(self, name: str, flags: dict) -> dict:
        rng = np.random.default_rng(self.seed + abs(hash(name)) % 99991)
        fast = LLMProposer(model=FAST_MODEL, context_level=flags["context"])
        strong = (LLMProposer(model=STRONG_MODEL, context_level=flags["context"])
                  if flags["ensemble"] else None)
        hint_pop = HintSetPopulation(seed=self.seed, proposer=fast) if flags["meta"] else None

        seed_ch = Chromosome(chromosome_id="seed", genes={}, fitness=0.0, generation=0,
                             metadata={"source": NAIVE_SEED_SOURCE, "spec": NAIVE_SPEC,
                                       "origin": "seed"})
        self._eval(seed_ch)
        pop = [seed_ch]
        stats = {"llm_calls": 0, "valid": 0, "improved": 0, "by_model": {}}
        t0 = time.time()

        for step in range(self.n_steps):
            if flags["evolution"]:
                parent = max(pop, key=lambda c: c.fitness)
                if len(pop) > 1 and rng.random() < 0.25:        # occasional diversity
                    cand = [c for c in pop if c is not parent]
                    parent = max(cand, key=lambda c: c.fitness)
            else:
                parent = seed_ch                                  # floor: never learn
            prop = strong if (strong is not None and step % 3 == 0) else fast
            hs = hint_pop.select() if hint_pop else None
            hints = hs.hints if hs else None
            if flags["context"] == "rich" and flags["evolution"]:
                cand = [c for c in pop if c is not parent and c.chromosome_id != "seed"]
                cand.sort(key=lambda c: c.fitness, reverse=True)
                inspirations = [_trim(c.metadata["source"]) for c in cand[:2]]
            else:
                inspirations = []
            src, _, info = prop.propose(
                parent.metadata["source"], parent.metadata.get("metrics", {}),
                parent.metadata.get("spec"), inspirations,
                hints=hints, context_level=flags["context"])
            stats["llm_calls"] += 1
            mdl = info.get("model", "?")
            stats["by_model"].setdefault(mdl, {"calls": 0, "valid": 0, "improved": 0})
            stats["by_model"][mdl]["calls"] += 1
            if info.get("error") or src is None or src == parent.metadata["source"]:
                continue
            child = Chromosome(chromosome_id=f"{name[0]}{rng.integers(0,10**9):09d}",
                               genes={}, fitness=0.0, generation=parent.generation + 1,
                               parent_ids=[parent.chromosome_id],
                               metadata={"source": src, "spec": None,
                                         "origin": info.get("model", "llm")})
            self._eval(child)
            pop = _merge(pop, child, self.elite)
            stats["valid"] += 1
            stats["by_model"][mdl]["valid"] += 1
            if child.fitness > parent.fitness:
                stats["improved"] += 1
                stats["by_model"][mdl]["improved"] += 1
            if hint_pop and hs:
                hint_pop.update(hs, child.fitness)
                hint_pop.maybe_evolve()

        best = max(pop, key=lambda c: c.fitness)
        best_test = self.ev.evaluate_split(best.metadata["source"], "test")
        seed_test = self.ev.evaluate_split(NAIVE_SEED_SOURCE, "test")
        rec = {
            "condition": name, "flags": flags, "n_steps": self.n_steps,
            "elapsed_s": round(time.time() - t0, 1),
            "seed_test_sigma": seed_test["sigma_nmad"],
            "best_eval_sigma": best.metadata.get("metrics", {}).get("sigma_nmad"),
            "best_test_sigma": best_test["sigma_nmad"],
            "best_test_eta": best_test["eta"],
            "best_origin": best.metadata.get("origin"),
            "best_gen": best.generation,
            "stats": stats,
            "hint_summary": hint_pop.summary() if hint_pop else None,
            "best_source": best.metadata["source"],
        }
        self.results.append(rec)
        return rec

    def run_all(self, names=None):
        names = names or [n for n, _ in CONDITIONS]
        flagmap = dict(CONDITIONS)
        for n in names:
            print(f"\n--- condition: {n} (steps={self.n_steps}) ---")
            r = self.run_condition(n, flagmap[n])
            print(f"    best TEST sigma={r['best_test_sigma']:.4f} eta={r['best_test_eta']:.3f}  "
                  f"(eval sigma={r['best_eval_sigma']:.4f})  "
                  f"llm={r['stats']['llm_calls']} valid={r['stats']['valid']} "
                  f"improved={r['stats']['improved']}  t={r['elapsed_s']}s")
        return self.results


def _bar(val, vmax, width=30):
    n = int(round(width * max(0.0, val) / vmax)) if vmax else 0
    return "#" * n + "." * (width - n)


def report(results, seed_sigma):
    print("\n" + "=" * 78)
    print("ABLATION RESULT — held-out TEST sigma_NMAD by condition (lower is better)")
    print("=" * 78)
    sigmas = [r["best_test_sigma"] for r in results] + [seed_sigma]
    vmax = max(sigmas)
    print(f"{'condition':<13}{'TEST sigma':>12}{'TEST eta':>10}{'  valid/impr':>14}  bar (0..%.3f)" % vmax)
    for r in results:
        st = r["stats"]
        print(f"{r['condition']:<13}{r['best_test_sigma']:>12.4f}{r['best_test_eta']:>10.3f}"
              f"{st['valid']:>9}/{st['improved']:<4}  {_bar(r['best_test_sigma'], vmax)}")
    print(f"{'naive seed':<13}{seed_sigma:>12.4f}{'':>10}{'':>14}  {_bar(seed_sigma, vmax)}")
    print("\n(marginal effect read top-to-bottom: each row adds one feature to the row above.)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=12, help="LLM proposals per condition")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--elite", type=int, default=4)
    args = ap.parse_args()
    print("=" * 78)
    print("Recommendation 3 — ABLATION of context feedback / ensemble / meta-prompt")
    print("Task: REAL SDSS photo-z. Fast=Haiku, Strong=Sonnet. Equal LLM budget/cond.")
    print("=" * 78)
    ab = Ablation(n_steps=args.steps, elite=args.elite, seed=args.seed)
    res = ab.run_all()
    seed_sigma = res[0]["seed_test_sigma"]
    report(res, seed_sigma)

    out = Path.home() / ".astra_persistent" / "evolved_programs" / "ablation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"seed_test_sigma": seed_sigma,
                               "fast_model": FAST_MODEL, "strong_model": STRONG_MODEL,
                               "n_steps": args.steps, "results": res}, indent=2))
    print(f"\nablation log -> {out}")


if __name__ == "__main__":
    main()
