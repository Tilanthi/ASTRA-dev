"""meta_prompt.py — meta-prompt co-evolution (AlphaEvolve §1.1).

AlphaEvolve co-evolves prompt instructions in a database SEPARATE from the
solution programs: the LLM occasionally proposes improvements to the
instructions themselves, and instruction-variants are selected by the downstream
fitness of the programs they produce. This module implements that.

A HintSet is a short list of strategy hints appended to the proposer's system
prompt. The HintSetPopulation tracks each set's mean program-fitness and selects
among them (epsilon-greedy with a visit floor), periodically spawning LLM-proposed
variants of the best set and culling the worst.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class HintSet:
    name: str
    hints: List[str] = field(default_factory=list)
    fitness_sum: float = 0.0
    n: int = 0
    spawned_from: Optional[str] = None

    def mean(self) -> float:
        return self.fitness_sum / self.n if self.n else -1e9


_SEED_SETS = [
    ("none", []),
    ("colors", ["Add all four SDSS colours (u-g, g-r, r-i, i-z) as features."]),
    ("scale", ["Apply feature scaling (StandardScaler or RobustScaler) before fitting."]),
    ("ensemble", ["Use a regularised or ensemble model (Ridge, GradientBoosting or RandomForest)."]),
    ("biasfix", ["The residual profile shows z-dependent bias; add colour-colour "
                 "interaction or polynomial terms to correct the slope."]),
    ("robust", ["Reduce outliers (eta): use a robust or quantile-based model, or "
                "clip extreme colour outliers before fitting."]),
]


class HintSetPopulation:
    def __init__(self, seed: int = 0, proposer=None, eps: float = 0.2,
                 max_size: int = 8, evolve_every: int = 6, max_evolutions: int = 3):
        self.rng = np.random.default_rng(seed)
        self.proposer = proposer              # an LLMProposer (for hint generation)
        self.eps = eps
        self.max_size = max_size
        self.evolve_every = evolve_every
        self.max_evolutions = max_evolutions
        self.sets: List[HintSet] = [HintSet(n, list(h)) for n, h in _SEED_SETS]
        self._since_evolve = 0
        self.n_evolutions = 0

    def select(self) -> HintSet:
        if self.rng.random() < self.eps or all(s.n < 2 for s in self.sets):
            return self.sets[int(self.rng.integers(0, len(self.sets)))]
        return max(self.sets, key=lambda s: s.mean())

    def update(self, hs: HintSet, fitness: float):
        hs.fitness_sum += fitness
        hs.n += 1
        self._since_evolve += 1

    def maybe_evolve(self) -> Optional[HintSet]:
        """Every evolve_every updates (within budget), ask the LLM to propose ONE
        new hint that complements the current best set; add it; cull the worst.
        Returns the spawned HintSet or None."""
        if (self.proposer is None or self.n_evolutions >= self.max_evolutions
                or self._since_evolve < self.evolve_every):
            return None
        self._since_evolve = 0
        self.n_evolutions += 1
        best = max(self.sets, key=lambda s: s.mean())
        new_hint = self._llm_propose_hint(best)
        if not new_hint:
            return None
        spawned = HintSet(f"evo{self.n_evolutions}", list(best.hints) + [new_hint],
                          spawned_from=best.name)
        self.sets.append(spawned)
        if len(self.sets) > self.max_size:
            # cull the lowest-mean set that has been tried, keep untried ones
            tried = [s for s in self.sets if s.n > 0]
            if tried:
                worst = min(tried, key=lambda s: s.mean())
                if worst is not spawned:
                    self.sets.remove(worst)
        return spawned

    def _llm_propose_hint(self, best: HintSet) -> Optional[str]:
        """One small LLM call to invent a single concrete strategy hint."""
        try:
            cur = "\n".join(f"- {h}" for h in best.hints) or "(none)"
            r = self.proposer.client.messages.create(
                model=self.proposer.model, max_tokens=80,
                system=("You advise on improving a photometric-redshift pipeline. "
                        "Reply with ONE concrete, novel strategy hint as a single "
                        "sentence. It should COMPLEMENT, not repeat, the hints below. "
                        "No preamble."),
                messages=[{"role": "user", "content":
                           f"Current strategy hints:\n{cur}\n\n"
                           "Propose ONE new concrete hint (e.g. a feature, model, "
                           "or regularisation idea not already listed)."}])
            txt = "".join(b.text for b in r.content if hasattr(b, "text")).strip()
            # take the first sentence, strip quotes
            txt = txt.split("\n")[0].strip().strip('"').strip("'")
            return txt or None
        except Exception:
            return None

    def summary(self) -> List[dict]:
        return [{"name": s.name, "n": s.n, "mean": round(s.mean(), 4) if s.n else None,
                 "hints": s.hints, "from": s.spawned_from} for s in
                sorted(self.sets, key=lambda s: s.mean(), reverse=True)]
