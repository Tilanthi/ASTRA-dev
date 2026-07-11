"""selection.py — Recommendation 4 search-quality evaluators.

Composable wrappers around RealDataProgramEvaluator (the subprocess scorer) that
change HOW candidates are graded and selected. All subclass the REAL leapcore
FitnessEvaluator.

  SelectionEvaluator(base, K, cascade=, cascade_thresh=, parsimony_weight=)
    - K-fold cross-validated fitness (out-of-fold over the TRAIN+EVAL pool;
      TEST stays fully held out). This is the rec-3 overfitting fix: a program
      can no longer "get lucky" on a single EVAL split.
    - cascade: a cheap stage-1 probe on ONE fold prunes clearly-bad programs
      before paying for the full K-fold (AlphaEvolve §1.3 cascade).
    - parsimony_weight>0: multi-objective scalarisation adding a simplicity term
      (AlphaEvolve §1.3 "multiple scores" — auxiliary objectives help the primary).

The flags map 1:1 onto the three rec-4 search-quality features, so the demo can
toggle them independently.
"""
from __future__ import annotations

from .leapcore import FitnessEvaluator

NEG_INF = -1e9


def parsimony(src: str) -> float:
    """Normalised complexity in ~[0,1]: 0 = minimal, 1 = verbose. Based on the
    count of non-blank code lines beyond a minimal baseline."""
    nlines = sum(1 for ln in src.splitlines() if ln.strip())
    return min(1.0, max(0.0, (nlines - 6) / 40.0))


class SelectionEvaluator(FitnessEvaluator):
    def __init__(self, base, K: int = 5, cascade: bool = False,
                 cascade_thresh: float = 0.08, parsimony_weight: float = 0.0,
                 stage1_fold: int = 0):
        self.base = base                  # a RealDataProgramEvaluator
        self.K = K
        self.cascade = cascade
        self.cascade_thresh = cascade_thresh
        self.parsimony_weight = parsimony_weight
        self.stage1_fold = stage1_fold
        # diagnostics
        self.n_total = 0
        self.n_pruned = 0
        self.n_errors = 0

    # -- the one required FitnessEvaluator method --
    def evaluate(self, chrom) -> float:
        self.n_total += 1
        src = (chrom.metadata or {}).get("source", "")
        chrom.metadata = dict(chrom.metadata or {})

        if self.cascade:                  # cheap stage-1 on a single fold
            s1 = self.base.evaluate_split(src, f"cv:{self.K}:{self.stage1_fold}")
            if "error" in s1 or s1.get("sigma_nmad", 9.99) > self.cascade_thresh:
                self.n_pruned += 1
                chrom.fitness = NEG_INF
                chrom.metadata["metrics"] = {"sigma_nmad": 9.99, "eta": 1.0,
                                             "pruned": True}
                chrom.metadata["parsimony"] = parsimony(src)
                return chrom.fitness

        m = self.base.evaluate_split(src, f"cv:{self.K}")    # full out-of-fold CV
        par = parsimony(src)
        chrom.metadata["parsimony"] = par
        if "error" in m:
            self.n_errors += 1
            chrom.fitness = NEG_INF
            chrom.metadata["metrics"] = m
            return chrom.fitness
        chrom.metadata["metrics"] = m
        chrom.metadata["metrics_cv_std"] = m.get("cv_sigma_std")
        # primary = -(sigma + 3*eta); optional multi-objective parsimony term
        chrom.fitness = -(m["sigma_nmad"] + 3.0 * m["eta"]
                          + self.parsimony_weight * par)
        return chrom.fitness

    # convenience pass-throughs
    def evaluate_split(self, src: str, split: str) -> dict:
        return self.base.evaluate_split(src, split)

    def stats(self) -> dict:
        return {"n_total": self.n_total, "n_pruned": self.n_pruned,
                "n_errors": self.n_errors,
                "prune_rate": (self.n_pruned / self.n_total) if self.n_total else 0.0}
