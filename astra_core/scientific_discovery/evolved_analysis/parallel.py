"""parallel.py — WP6: async/parallel throughput pipeline (AlphaEvolve §1.5).

A parallel generation step: within one generation, λ (select-parent → propose →
evaluate) tasks run CONCURRENTLY in a thread pool. The LLM calls are I/O-bound
and the eval subprocesses are independent, so this is where the wall-clock wins
come from. The main thread snapshots the population/archive (read-only) so child
tasks never race on shared state, then merges the results as a single writer.

ParallelEvolutionEngine subclasses EvolutionEngine and overrides step(); everything
else (evaluator, proposer, archive, elitism) is unchanged.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import List

from .engine import EvolutionEngine, _src, _niche
from .leapcore import Chromosome


class ParallelEvolutionEngine(EvolutionEngine):
    def __init__(self, *args, workers: int = 4, **kwargs):
        super().__init__(*args, **kwargs)
        self.workers = workers

    def _make_child(self, parent: Chromosome, insp):
        """propose + evaluate one child (runs in a worker thread). Returns the
        child Chromosome or None."""
        res = self.proposer.propose(
            parent.metadata.get("source", ""),
            parent.metadata.get("metrics", {}),
            parent.metadata.get("spec"), insp, **self.propose_opts)
        self.stats["proposals"] += 1
        if not res or res[0] is None or res[0] == parent.metadata.get("source"):
            return None
        src, spec, info = res
        child = Chromosome(
            chromosome_id=f"p{self.rng.integers(0, 10**9):09d}", genes={},
            fitness=0.0, generation=parent.generation + 1,
            parent_ids=[parent.chromosome_id],
            metadata={"source": src, "spec": spec,
                      "origin": info.get("model", getattr(self.proposer, "name", "?"))})
        self.evaluator.evaluate(child)
        self.stats["accepted"] += 1
        if child.fitness > parent.fitness:
            self.stats["improved_parent"] += 1
        return child

    def step(self) -> dict:
        """Parallel generation: snapshot parents, run λ propose+eval concurrently,
        then merge (single writer)."""
        n_children = max(1, self.config.population_size - self.config.elite_count)
        # read-only snapshot so worker threads never race the population
        pop_snap = list(self.population)
        archive_snap = self.archive

        def pick_parent():
            if archive_snap is not None and archive_snap.cells:
                return archive_snap.sample_parent()
            k = min(self.config.tournament_size, len(pop_snap))
            idx = self.rng.choice(len(pop_snap), size=k, replace=False)
            return max((pop_snap[i] for i in idx), key=lambda c: c.fitness)

        tasks = []
        for _ in range(n_children):
            parent = pick_parent()
            if archive_snap is not None:
                insp = [_src(c)[:1100] for c in
                        archive_snap.inspirations(exclude=parent, k=self.inspiration_k)]
            else:
                pool = [c for c in pop_snap if c is not parent
                        and c.chromosome_id != "seed"]
                pool.sort(key=lambda c: c.fitness, reverse=True)
                insp = [_src(c)[:1100] for c in pool[:self.inspiration_k]]
            tasks.append((parent, insp))

        children: List[Chromosome] = []
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futures = [ex.submit(self._make_child, p, i) for p, i in tasks]
            for f in futures:
                c = f.result()
                if c is not None:
                    children.append(c)
                    if self.archive is not None:
                        self.archive.add(c)
        self._elitist_merge(children)
        best = max(self.population, key=lambda c: c.fitness)
        m = best.metadata.get("metrics", {})
        row = {"best_fitness": best.fitness, "best_sigma": m.get("sigma_nmad"),
               "n_children": len(children), "proposals": self.stats["proposals"]}
        self.history.append(row)
        return row
