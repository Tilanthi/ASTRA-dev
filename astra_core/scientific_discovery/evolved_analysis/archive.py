"""archive.py — Recommendation 4 MAP-Elites archive + diversity-aware selection.

MAP-Elites keeps the best program per *behavioral niche* (cell), so the search
cannot collapse onto a single family of solutions — AlphaEvolve's "balance
exploration and exploitation" + island-population idea (§1.4). Cells here act as
islands; sampling parents across cells supplies the diversity that island
migration would, without needing crossover (the LLM proposer edits code directly).

The behavior descriptor is derived from the program SOURCE (LLM programs carry no
spec): (model_family, complexity_bucket). model_family is sniffed by keyword.
"""
from __future__ import annotations

import re
from typing import Dict, Tuple, List, Optional

from .selection import parsimony

Cell = Tuple[str, int]

_MODEL_PATTERNS = [
    ("GradientBoosting", re.compile(r"GradientBoosting|XGBoost|HistGradientBoosting")),
    ("RandomForest", re.compile(r"RandomForest|ExtraTrees")),
    ("NearestNeighbor", re.compile(r"KNeighbors|NearestNeighbor|knn", re.I)),
    ("SVR", re.compile(r"SVR|SupportVector", re.I)),
    ("Ridge", re.compile(r"\bRidge\b")),
    ("Lasso", re.compile(r"\bLasso\b")),
    ("Linear", re.compile(r"LinearRegression")),
    ("Other", None),
]


def descriptor(src: str) -> Cell:
    """Behavior descriptor (model_family, complexity_bucket in 0..2)."""
    fam = "Other"
    for name, pat in _MODEL_PATTERNS:
        if pat is None:
            continue
        if pat.search(src):
            fam = name
            break
    bucket = min(2, int(parsimony(src) * 3))
    return (fam, bucket)


class MAPElitesArchive:
    def __init__(self, seed: int = 0):
        import numpy as np
        self.rng = np.random.default_rng(seed)
        self.cells: Dict[Cell, "object"] = {}   # cell -> best Chromosome
        self.history_added = 0

    def add(self, chrom) -> bool:
        """Insert into its cell if empty or strictly better. Returns True if it
        became/was the cell elite."""
        c = descriptor((chrom.metadata or {}).get("source", ""))
        cur = self.cells.get(c)
        if cur is None or chrom.fitness > cur.fitness:
            self.cells[c] = chrom
            self.history_added += 1
            return True
        return False

    def filled_cells(self) -> List[Cell]:
        return list(self.cells.keys())

    def diversity(self) -> int:
        return len(self.cells)

    def best(self):
        if not self.cells:
            return None
        return max(self.cells.values(), key=lambda c: c.fitness)

    def sample_parent(self, diversity_bias: float = 0.3):
        """Pick a filled cell (mostly by fitness, sometimes uniformly for
        diversity), return that cell's elite as the parent."""
        if not self.cells:
            return None
        cells = list(self.cells.values())
        if self.rng.random() < diversity_bias:
            return cells[int(self.rng.integers(0, len(cells)))]
        # fitness-proportional (softmax-ish on the positive parts)
        import numpy as np
        fits = np.array([c.fitness for c in cells])
        fits = fits - fits.max() + 1e-6
        w = np.exp(fits)
        i = int(self.rng.choice(len(cells), p=w / w.sum()))
        return cells[i]

    def inspirations(self, exclude=None, k: int = 2):
        """Up to k diverse elites (distinct cells) other than `exclude`, for the
        proposer's inspiration context."""
        els = [c for c in self.cells.values() if c is not exclude]
        els.sort(key=lambda c: c.fitness, reverse=True)
        # pick from distinct cells if possible
        seen, out = set(), []
        for c in els:
            d = descriptor((c.metadata or {}).get("source", ""))
            if d in seen:
                continue
            seen.add(d); out.append(c)
            if len(out) >= k:
                break
        return out

    def summary(self) -> dict:
        from collections import Counter
        fams = Counter(c[0] for c in self.cells)
        return {"filled_cells": len(self.cells),
                "by_family": dict(fams),
                "best_fitness": (self.best().fitness if self.cells else None)}
