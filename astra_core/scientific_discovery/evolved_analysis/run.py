"""run.py — Recommendation 2 driver: the AlphaEvolve loop, end to end.

    parent program --LLM-diff / genetic--> child program --EVALUATE(real data)--> scalar
         ^                                                                  |
         +------------------- program database (elites + niches) <---------+

Evolves EXECUTABLE CODE (estimate_redshift), graded by a real leapcore
FitnessEvaluator on real SDSS data. The LLM proposer is primary when an API key
is present; the genetic proposer is the offline fallback and also runs mixed in
to keep diversity and reproducibility.

Persists every program (source, spec, metrics, lineage) and the per-generation
history to ~/.astra_persistent/evolved_programs/, and reports the honest
held-out TEST metric at the end.

Usage:
    python -m evolved_analysis.run                # LLM primary
    python -m evolved_analysis.run --no-llm       # genetic only
    python -m evolved_analysis.run --generations 6 --lambda 6
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
from .proposer import LLMProposer, GeneticProposer

PERSIST_DIR = Path.home() / ".astra_persistent" / "evolved_programs"


def source_hash(src: str) -> str:
    return hashlib.sha1(src.encode()).hexdigest()[:12]


def niche(chrom: Chromosome) -> tuple:
    spec = (chrom.metadata or {}).get("spec") or {}
    return (spec.get("model", "llm"), len(spec.get("color_pairs", []) or []),
            spec.get("degree", 0), spec.get("scale", "")) \
        if spec else ("llm", -1, -1, "")


def _trim(src: str, n: int = 1400) -> str:
    return src if len(src) <= n else src[:n] + "\n# ... (truncated)"


class Evolution:
    def __init__(self, generations=5, mu=6, lam=6, elites=3, seed=42,
                 use_llm=True, llm_frac=0.5, eval_timeout=60,
                 max_llm_calls=40, max_wall_s=900):
        self.generations = generations
        self.mu = mu
        self.lam = lam
        self.elites = elites
        self.seed = seed
        self.use_llm = use_llm and bool(__import__("os").environ.get(
            "ANTHROPIC_AUTH_TOKEN") or __import__("os").environ.get("ANTHROPIC_API_KEY"))
        self.llm_frac = llm_frac
        self.max_llm_calls = max_llm_calls
        self.max_wall_s = max_wall_s
        self.ev = RealDataProgramEvaluator(seed=seed, timeout=eval_timeout)
        self.rng = np.random.default_rng(seed)
        self.llm = None
        self.genetic = GeneticProposer(seed=seed)
        self.cache: dict[str, float] = {}
        self.history: list[dict] = []
        self.stats = {"llm_calls": 0, "llm_children_valid": 0,
                      "llm_children_improved": 0, "genetic_calls": 0}

    # -- evaluation with caching --
    def _evaluate(self, chrom: Chromosome) -> None:
        h = source_hash(chrom.metadata["source"])
        if h in self.cache:
            chrom.fitness, metrics = self.cache[h]
            chrom.metadata["metrics"] = metrics
            return
        self.ev.evaluate(chrom)
        self.cache[h] = (chrom.fitness, chrom.metadata.get("metrics", {}))

    def _ensure_llm(self):
        if self.llm is None and self.use_llm:
            try:
                self.llm = LLMProposer()
            except Exception as e:
                print(f"  [llm] unavailable ({type(e).__name__}); using genetic only")
                self.use_llm = False

    def _propose_child(self, parent: Chromosome, inspirations):
        """Return a child Chromosome (unevaluated) or None."""
        use_llm_now = (self.use_llm and self.llm is not None
                       and self.stats["llm_calls"] < self.max_llm_calls
                       and self.rng.random() < self.llm_frac)
        if use_llm_now:
            src, spec, info = self.llm.propose(
                parent.metadata["source"], parent.metadata.get("metrics", {}),
                parent.metadata.get("spec"), inspirations)
            self.stats["llm_calls"] += 1
            origin = "llm"
            if info.get("error") or src is None:
                return None
        else:
            src, spec, info = self.genetic.propose(
                parent.metadata["source"], parent.metadata.get("metrics", {}),
                parent.metadata.get("spec"), inspirations)
            self.stats["genetic_calls"] += 1
            origin = "genetic"
        if src is None or src == parent.metadata["source"]:
            return None
        return Chromosome(
            chromosome_id=f"{origin[0]}{self.rng.integers(0, 10**9):09d}",
            genes={}, fitness=0.0, generation=parent.generation + 1,
            parent_ids=[parent.chromosome_id],
            metadata={"source": src, "spec": spec, "origin": origin, "propose": info})

    def _select_elites(self, pop, k):
        """Top-k by fitness, diversified by niche; robust to small populations."""
        pop = sorted(pop, key=lambda c: c.fitness, reverse=True)
        if k >= len(pop):
            return list(pop)
        kept, seen = [], set()
        for c in pop:                              # niche-diverse pass
            if len(kept) >= k:
                break
            nk = niche(c)
            if nk in seen:
                continue
            seen.add(nk); kept.append(c)
        for c in pop:                              # fill remaining by fitness
            if len(kept) >= k:
                break
            if not any(c is x for x in kept):
                kept.append(c)
        return kept

    def run(self):
        self._ensure_llm()
        print(f"proposer: {'LLM+genetic' if self.use_llm else 'genetic-only'}  "
              f"(model={getattr(self.llm,'model','-') if self.llm else '-'})")
        seed = Chromosome(chromosome_id="seed", genes={}, fitness=0.0, generation=0,
                          metadata={"source": NAIVE_SEED_SOURCE, "spec": NAIVE_SPEC,
                                    "origin": "seed"})
        self._evaluate(seed)
        pop = [seed]
        t0 = time.time()

        for gen in range(1, self.generations + 1):
            if time.time() - t0 > self.max_wall_s:
                print(f"  [wall budget {self.max_wall_s}s reached; stopping early]")
                break
            parents = self._select_elites(pop, max(self.elites, self.mu // 2))
            best_par = max(pop, key=lambda c: c.fitness)
            inspirations = [_trim(c.metadata["source"]) for c in
                            sorted([p for p in pop if p.chromosome_id != "seed"],
                                   key=lambda c: c.fitness, reverse=True)[:2]]
            children = []
            tries = 0
            while len(children) < self.lam and tries < self.lam * 3:
                tries += 1
                parent = parents[int(self.rng.integers(0, len(parents)))]
                child = self._propose_child(parent, inspirations)
                if child is None:
                    continue
                self._evaluate(child)
                if child.metadata.get("origin") == "llm":
                    self.stats["llm_children_valid"] += 1
                    if child.fitness > parent.fitness:
                        self.stats["llm_children_improved"] += 1
                children.append(child)

            merged = self._select_elites(pop + children, self.mu)
            pop = merged
            best = max(pop, key=lambda c: c.fitness)
            self.history.append({
                "gen": gen, "best": best.fitness, "mean": float(np.mean([c.fitness for c in pop])),
                "best_sigma": best.metadata.get("metrics", {}).get("sigma_nmad"),
                "best_eta": best.metadata.get("metrics", {}).get("eta"),
                "n_children": len(children), "elapsed_s": round(time.time() - t0, 1),
            })
            b = best.metadata.get("metrics", {})
            print(f"  gen {gen:02d}  best={best.fitness:+.4f}  [σ={b.get('sigma_nmad',9):.4f} "
                  f"η={b.get('eta',1):.3f}]  origin={best.metadata.get('origin')}  "
                  f"llm_used={self.stats['llm_calls']}  t={time.time()-t0:.0f}s")

        pop.sort(key=lambda c: c.fitness, reverse=True)
        self.best = pop[0]
        self.seed_metrics = self.ev.evaluate_split(NAIVE_SEED_SOURCE, "test")
        self.best_test = self.ev.evaluate_split(self.best.metadata["source"], "test")
        return self

    def report_and_persist(self):
        s, b = self.seed_metrics, self.best_test
        print("\n" + "=" * 74)
        print("RESULT — held-out TEST split (real galaxies, never used for selection)")
        print("=" * 74)
        print(f"{'metric':<12}{'naive seed':>14}{'evolved best':>16}")
        print(f"{'sigma_NMAD':<12}{s['sigma_nmad']:>14.4f}{b['sigma_nmad']:>16.4f}")
        print(f"{'outlier eta':<12}{s['eta']:>14.3f}{b['eta']:>16.3f}")
        imp = s["sigma_nmad"] - b["sigma_nmad"]
        print(f"\nsigma_NMAD: {s['sigma_nmad']:.4f} -> {b['sigma_nmad']:.4f}  "
              f"(Δ={imp:+.4f}, {100*imp/s['sigma_nmad']:+.1f}%)")
        print(f"best origin: {self.best.metadata.get('origin')}  generation: {self.best.generation}")
        print(f"proposer stats: llm_calls={self.stats['llm_calls']} "
              f"valid={self.stats['llm_children_valid']} "
              f"improved_parent={self.stats['llm_children_improved']} "
              f"genetic_calls={self.stats['genetic_calls']}")
        verdict = ("PASS — an LLM/code-evolved program improved a real machine-graded "
                   "metric on held-out data") if imp > 0 else "FAIL — no improvement"
        print(f"VERDICT: {verdict}")

        PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        best_py = PERSIST_DIR / f"best_program_{ts}.py"
        best_py.write_text(self.best.metadata["source"])
        log = {
            "task": "photometric_redshift_code_evolution",
            "data_source": "SDSS CAS (real)",
            "proposer": "llm+genetic" if self.use_llm else "genetic",
            "seed_test_metrics": s, "best_test_metrics": b,
            "best_origin": self.best.metadata.get("origin"),
            "best_generation": self.best.generation,
            "best_spec": self.best.metadata.get("spec"),
            "best_program_path": str(best_py),
            "history": self.history, "stats": self.stats,
        }
        log_path = PERSIST_DIR / f"run_{ts}.json"
        log_path.write_text(json.dumps(log, indent=2))
        print(f"\npersisted best program -> {best_py}")
        print(f"persisted run log      -> {log_path}")


def main():
    ap = argparse.ArgumentParser(description="AlphaEvolve-style photo-z code evolution")
    ap.add_argument("--generations", type=int, default=5)
    ap.add_argument("--mu", type=int, default=6, help="population size")
    ap.add_argument("--lambda", dest="lam", type=int, default=6, help="children/gen")
    ap.add_argument("--elites", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-llm", action="store_true", help="genetic proposer only")
    ap.add_argument("--llm-frac", type=float, default=0.5)
    ap.add_argument("--max-llm-calls", type=int, default=40)
    args = ap.parse_args()
    print("=" * 74)
    print("Recommendation 2 — evolving CODE (photo-z) with an LLM diff-proposer")
    print("Data: REAL SDSS galaxies; target: independent z_spec. No mock data.")
    print("Evolved artifact: executable estimate_redshift() program.")
    print("=" * 74)
    evo = Evolution(generations=args.generations, mu=args.mu, lam=args.lam,
                    elites=args.elites, seed=args.seed,
                    use_llm=not args.no_llm, llm_frac=args.llm_frac,
                    max_llm_calls=args.max_llm_calls).run()
    evo.report_and_persist()


if __name__ == "__main__":
    main()
