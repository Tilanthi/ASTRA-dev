"""engine.py — WP2: the promoted, canonical evolutionary engine.

A clean, general, RNG-injectable, proposer-driven evolutionary loop that reuses
the REAL astra_core leapcore classes (Gene/Chromosome/EvolutionConfig/
FitnessEvaluator, loaded by file path) and supersedes the hand-rolled loops in
run.py / ablation.py / run_quality.py. AlphaEvolve's recipe in one place:

    parent program --proposer--> child program --evaluator (real data)--> scalar
         ^                                                              |
         +----------------- population + archive (diversity) <---------+

Everything task- and feature-specific plugs in:
  - evaluator : a leapcore FitnessEvaluator (e.g. RealDataProgramEvaluator,
                or rec-4 SelectionEvaluator for K-fold CV / cascade / multi-obj).
  - proposer  : anything with .propose(parent_source, parent_metrics, parent_spec,
                inspirations, **opts) -> (source, spec, info) | None
                (e.g. LLMProposer / GeneticProposer; ensemble = caller picks per call).
  - archive   : optional MAPElitesArchive for diversity-aware parent sampling
                (rec 4); if None, plain elitist selection.

Selection mirrors LEAPCoreEvolution's tournament + elitism, but uses an INJECTED
numpy Generator (deterministic, thread-safe) instead of global np.random.
"""
from __future__ import annotations

import copy
from typing import Any, Callable, List, Optional

import numpy as np

from .leapcore import (
    Chromosome, EvolutionConfig, FitnessEvaluator)


class EvolutionEngine:
    def __init__(self, evaluator: FitnessEvaluator, proposer: Any,
                 seed_chrom: Chromosome, config: Optional[EvolutionConfig] = None,
                 rng: Optional[np.random.Generator] = None,
                 archive: Optional[Any] = None,
                 propose_opts: Optional[dict] = None,
                 inspiration_k: int = 2):
        self.evaluator = evaluator
        self.proposer = proposer
        self.config = config or EvolutionConfig()
        self.rng = rng if rng is not None else np.random.default_rng(0)
        self.archive = archive
        self.propose_opts = propose_opts or {}
        self.inspiration_k = inspiration_k
        self.history: List[dict] = []
        self.stats = {"proposals": 0, "accepted": 0, "improved_parent": 0}

        self.evaluator.evaluate(seed_chrom)
        self.population: List[Chromosome] = [seed_chrom]
        if self.archive is not None:
            self.archive.add(seed_chrom)

    # -- selection (mirrors LEAPCoreEvolution tournament, RNG-injected) --
    def _tournament(self, k: Optional[int] = None) -> Chromosome:
        k = k or self.config.tournament_size
        if self.archive is not None and self.archive.cells:
            return self.archive.sample_parent()
        k = min(k, len(self.population))
        idx = self.rng.choice(len(self.population), size=k, replace=False)
        return max((self.population[i] for i in idx), key=lambda c: c.fitness)

    def _inspirations(self, parent: Chromosome) -> List[str]:
        pool = [c for c in self.population if c is not parent
                and c.chromosome_id != "seed"]
        pool.sort(key=lambda c: c.fitness, reverse=True)
        if self.archive is not None:
            insp = self.archive.inspirations(exclude=parent, k=self.inspiration_k)
            return [_src(c)[:1100] for c in insp]
        return [_src(c)[:1100] for c in pool[:self.inspiration_k]]

    def _elitist_merge(self, children: List[Chromosome]):
        """Keep config.population_size best, diversified by niche if no archive."""
        merged = sorted(self.population + children, key=lambda c: c.fitness,
                        reverse=True)
        if self.archive is not None:
            self.population = merged[:self.config.population_size]
            return
        kept, seen = [], set()
        for c in merged:
            if len(kept) >= self.config.population_size:
                break
            nk = _niche(c)
            if nk in seen:
                continue
            seen.add(nk); kept.append(c)
        while len(kept) < self.config.population_size and len(kept) < len(merged):
            kept.append(merged[len(kept)])
        self.population = kept

    def step(self) -> dict:
        """One generation: produce (population_size - elite_count) children via
        the proposer, evaluate, elitist merge. Returns a summary dict."""
        n_children = max(1, self.config.population_size - self.config.elite_count)
        children: List[Chromosome] = []
        attempts = 0
        while len(children) < n_children and attempts < n_children * 3:
            attempts += 1
            parent = self._tournament()
            insp = self._inspirations(parent)
            res = self.proposer.propose(
                parent.metadata.get("source", ""),
                parent.metadata.get("metrics", {}),
                parent.metadata.get("spec"),
                insp, **self.propose_opts)
            self.stats["proposals"] += 1
            if not res or res[0] is None or res[0] == parent.metadata.get("source"):
                continue
            src, spec, info = res
            child = Chromosome(
                chromosome_id=f"e{self.rng.integers(0, 10**9):09d}", genes={},
                fitness=0.0, generation=parent.generation + 1,
                parent_ids=[parent.chromosome_id],
                metadata={"source": src, "spec": spec,
                          "origin": info.get("model", getattr(self.proposer, "name", "?"))})
            self.evaluator.evaluate(child)
            self.stats["accepted"] += 1
            if child.fitness > parent.fitness:
                self.stats["improved_parent"] += 1
            children.append(child)
            if self.archive is not None:
                self.archive.add(child)
        self._elitist_merge(children)
        best = max(self.population, key=lambda c: c.fitness)
        m = best.metadata.get("metrics", {})
        row = {"best_fitness": best.fitness, "best_sigma": m.get("sigma_nmad"),
               "best_eta": m.get("eta"), "n_children": len(children),
               "proposals": self.stats["proposals"]}
        self.history.append(row)
        return row

    def run(self, generations: int) -> Chromosome:
        for _ in range(generations):
            self.step()
        return max(self.population, key=lambda c: c.fitness)

    def best(self) -> Chromosome:
        return max(self.population, key=lambda c: c.fitness)


def _src(c: Chromosome) -> str:
    return (c.metadata or {}).get("source", "")


def _niche(c: Chromosome):
    s = (c.metadata or {}).get("spec") or {}
    if s:
        return (s.get("model", "llm"), len(s.get("color_pairs", []) or []),
                s.get("degree", 0))
    # fall back to source-hash bucket for LLM programs without a spec
    return ("llm", hash(_src(c)) % 5, 0)
