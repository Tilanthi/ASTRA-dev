"""
evolve_photoz.py — Prototype for recommendation 1.

A minimal but HONEST evolutionary discovery loop, modelled on AlphaEvolve's core
recipe:

    parent programs  --LLM/diff-->  child programs  --EVALUATE-->  real scalar
         ^                                                              |
         +--------------- program database (elites + diversity) <-------+

What is evolved
---------------
Not "a description of a discovery". We evolve an *analysis pipeline* (the thing
AlphaEvolve calls "evolving the search algorithm, not the solution"): a
photo-z estimator whose hyper-structure (which colours, scaling, polynomial
degree, model family, regularisation) is encoded as genes.

What grades it (the part ASTRA currently lacks)
------------------------------------------------
EVALUATE() fits the pipeline on real TRAIN galaxies and scores it on a real held
out EVAL split by two standard, objective, machine-computed photo-z metrics:

    sigma_NMAD = 1.4826 * median(|z_phot - z_spec|)      (robust scatter)
    eta        = fraction with |z_phot-z_spec|/(1+z_spec) > 0.15   (outlier rate)

Both are computed against SPECTROSCOPIC redshifts — an independent real
measurement, not the photometry used to predict them. No LLM judges its own
output. No mock data.

The gene classes (Gene/Chromosome) intentionally mirror the API of
astra_core/intelligence/leapcore_evolution.py so recommendation 2 can promote
this to the real ASTRA evolutionary engine with a one-line swap.
"""
from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from .real_data import load_split, BANDS

# --------------------------------------------------------------------------- #
# Gene / Chromosome  (API-compatible with astra_core leapcore_evolution)      #
# --------------------------------------------------------------------------- #


@dataclass
class Gene:
    """A single evolvable gene. kinds: numeric | int | log | categorical | list."""
    gene_id: str
    kind: str
    value: Any
    bounds: Tuple[Any, Any] = None          # (lo, hi) for numeric/int/log
    options: List[Any] = None               # for categorical
    element_options: List[Any] = None       # for list
    mutation_rate: float = 0.3

    def mutate(self, rng: np.random.Generator, strength: float = 1.0) -> "Gene":
        g = copy.deepcopy(self)
        if rng.random() > self.mutation_rate * strength:
            return g  # this gene not touched this time
        if g.kind in ("numeric", "log"):
            lo, hi = g.bounds
            span = hi - lo
            g.value = float(np.clip(g.value + rng.normal(0, 0.10) * span, lo, hi))
        elif g.kind == "int":
            lo, hi = g.bounds
            v = int(round(g.value + rng.normal(0, 0.5)))
            g.value = int(np.clip(v, lo, hi))
        elif g.kind == "categorical":
            g.value = str(rng.choice([o for o in g.options if o != g.value] or g.options))
        elif g.kind == "list":
            cur = list(g.value)
            if not cur or (rng.random() < 0.5 and len(cur) > 1):
                # remove a random element
                del cur[rng.integers(0, len(cur))]
            else:
                # add a not-yet-present element
                missing = [o for o in g.element_options if o not in cur]
                if missing:
                    cur.append(str(rng.choice(missing)))
            g.value = cur
        return g

    def snapshot(self) -> Any:
        v = self.value
        if self.kind == "log":
            return round(float(10 ** v), 4)
        if self.kind == "int":
            return int(v)
        return v


@dataclass
class Chromosome:
    """A complete photo-z pipeline specification."""
    genes: Dict[str, Gene]
    fitness: float = -np.inf
    eval_metrics: Dict[str, float] = field(default_factory=dict)
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    cid: str = ""

    def phenotype(self) -> Dict[str, Any]:
        ph = {}
        for gid, g in self.genes.items():
            v = g.snapshot()
            if isinstance(v, list):           # strip numpy str types for clean JSON
                v = [str(x) for x in v]
            ph[gid] = v
        return ph

    def mutate(self, rng, strength=1.0) -> "Chromosome":
        return Chromosome(
            genes={gid: g.mutate(rng, strength) for gid, g in self.genes.items()},
            generation=self.generation + 1, parent_ids=[self.cid])

    def crossover(self, other: "Chromosome", rng) -> "Chromosome":
        genes = {gid: (g if rng.random() < 0.5 else other.genes[gid])
                 for gid, g in self.genes.items()}
        return Chromosome(genes=genes,
                          generation=max(self.generation, other.generation) + 1,
                          parent_ids=[self.cid, other.cid])


# --------------------------------------------------------------------------- #
# Gene blueprint + seed                                                        #
# --------------------------------------------------------------------------- #

ALL_PAIRS = ["ug", "gr", "ri", "iz"]   # adjacent SDSS colours


def random_chromosome(rng) -> Chromosome:
    """A uniformly-sampled pipeline (used to seed the population)."""
    genes = {
        "color_pairs": Gene("color_pairs", "list",
                            value=list(rng.choice(ALL_PAIRS, size=rng.integers(1, 4),
                                                  replace=False)),
                            element_options=ALL_PAIRS, mutation_rate=0.4),
        "include_r": Gene("include_r", "numeric", value=float(rng.random()),
                          bounds=(0.0, 1.0), mutation_rate=0.3),
        "degree": Gene("degree", "int", value=int(rng.choice([1, 2, 3])),
                       bounds=(1, 3), mutation_rate=0.3),
        "scale": Gene("scale", "categorical",
                      value=str(rng.choice(["none", "standard", "robust"])),
                      options=["none", "standard", "robust"], mutation_rate=0.3),
        "model": Gene("model", "categorical",
                      value=str(rng.choice(["linear", "ridge", "rf"])),
                      options=["linear", "ridge", "rf"], mutation_rate=0.3),
        "log_alpha": Gene("log_alpha", "log", value=float(rng.uniform(-3, 3)),
                          bounds=(-3.0, 3.0), mutation_rate=0.4),
        "rf_trees": Gene("rf_trees", "int", value=int(rng.integers(20, 201)),
                         bounds=(20, 200), mutation_rate=0.4),
        "rf_depth": Gene("rf_depth", "int", value=int(rng.integers(3, 16)),
                         bounds=(3, 15), mutation_rate=0.4),
    }
    return Chromosome(genes=genes, cid=f"c{rng.integers(0,10**9):09d}")


def naive_seed() -> Chromosome:
    """A deliberately weak baseline: raw r-band magnitude, plain linear model.
    Evolution should beat this clearly — that contrast is the whole point."""
    genes = {
        "color_pairs": Gene("color_pairs", "list", value=[],
                            element_options=ALL_PAIRS, mutation_rate=0.4),
        "include_r": Gene("include_r", "numeric", value=1.0, bounds=(0.0, 1.0)),
        "degree": Gene("degree", "int", value=1, bounds=(1, 3)),
        "scale": Gene("scale", "categorical", value="none",
                      options=["none", "standard", "robust"]),
        "model": Gene("model", "categorical", value="linear",
                      options=["linear", "ridge", "rf"]),
        "log_alpha": Gene("log_alpha", "log", value=0.0, bounds=(-3.0, 3.0)),
        "rf_trees": Gene("rf_trees", "int", value=50, bounds=(20, 200)),
        "rf_depth": Gene("rf_depth", "int", value=6, bounds=(3, 15)),
    }
    return Chromosome(genes=genes, cid="NAIVE_SEED")


# --------------------------------------------------------------------------- #
# EVALUATE — the machine-checkable fitness on REAL data                       #
# --------------------------------------------------------------------------- #

def _design_matrix(df, color_pairs, include_r):
    band = {b: df[b].to_numpy(float) for b in BANDS}
    cols = [band[a] - band[b] for (a, b) in color_pairs]
    if include_r:
        cols.append(band["r"])
    if not cols:
        return None
    return np.column_stack(cols)


def _metrics(z_pred, z_true):
    delta = z_pred - z_true
    sigma_nmad = 1.4826 * np.median(np.abs(delta))
    eta = float(np.mean(np.abs(delta) / (1.0 + z_true) > 0.15))
    bias = float(np.median(delta))
    return {"sigma_nmad": float(sigma_nmad), "eta": eta, "bias": bias}


def evaluate(chrom: Chromosome, splits) -> float:
    """Fit the pipeline on TRAIN, score on EVAL. Mutates chrom.fitness/metrics.
    Fitness (maximised) = -(sigma_NMAD + 3*eta): low scatter AND low outliers."""
    from sklearn.preprocessing import StandardScaler, RobustScaler, PolynomialFeatures
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor

    p = chrom.phenotype()
    include_r = p["include_r"] > 0.5
    Xtr = _design_matrix(splits["train"], p["color_pairs"], include_r)
    Xev = _design_matrix(splits["eval"], p["color_pairs"], include_r)
    if Xtr is None or Xtr.shape[1] == 0:
        chrom.fitness, chrom.eval_metrics = -1e9, {"sigma_nmad": 9.99, "eta": 1.0}
        return chrom.fitness

    ytr = splits["train"]["z_spec"].to_numpy(float)
    yev = splits["eval"]["z_spec"].to_numpy(float)
    deg = int(p["degree"])

    try:
        # scaling (fit on TRAIN only)
        if p["scale"] == "standard":
            sc = StandardScaler().fit(Xtr); Xtr, Xev = sc.transform(Xtr), sc.transform(Xev)
        elif p["scale"] == "robust":
            sc = RobustScaler().fit(Xtr); Xtr, Xev = sc.transform(Xtr), sc.transform(Xev)
        # polynomial expansion (fit on TRAIN only)
        if deg > 1:
            pf = PolynomialFeatures(deg, include_bias=False).fit(Xtr)
            Xtr, Xev = pf.transform(Xtr), pf.transform(Xev)
        # model (fit on TRAIN only)
        if p["model"] == "ridge":
            mdl = Ridge(alpha=float(10 ** p["log_alpha"])).fit(Xtr, ytr)
        elif p["model"] == "rf":
            mdl = RandomForestRegressor(
                n_estimators=int(p["rf_trees"]), max_depth=int(p["rf_depth"]),
                n_jobs=-1, random_state=0).fit(Xtr, ytr)
        else:
            mdl = LinearRegression().fit(Xtr, ytr)
        pred = mdl.predict(Xev)
    except Exception as e:  # never let a bad gene crash the loop
        chrom.fitness, chrom.eval_metrics = -1e9, {"sigma_nmad": 9.99, "eta": 1.0,
                                                   "error": str(e)[:80]}
        return chrom.fitness

    m = _metrics(pred, yev)
    chrom.eval_metrics = m
    chrom.fitness = -(m["sigma_nmad"] + 3.0 * m["eta"])
    return chrom.fitness


# --------------------------------------------------------------------------- #
# Evolutionary loop (μ+λ with elitism + tournament + diversity bonus)         #
# --------------------------------------------------------------------------- #

def tournament(pop, rng, k):
    contenders = rng.choice(len(pop), size=min(k, len(pop)), replace=False)
    return pop[int(contenders[np.argmax([pop[i].fitness for i in contenders])])]


def niche_key(chrom: Chromosome) -> Tuple:
    p = chrom.phenotype()
    return (tuple(sorted(p["color_pairs"])), p["model"], p["degree"], p["scale"])


def run(pop_size=20, generations=30, elites=4, cx_rate=0.7,
        mut_rate=0.9, seed=42, verbose=True):
    rng = np.random.default_rng(seed)
    splits = load_split(seed=seed)

    # population = naive seed + random individuals
    pop = [naive_seed()] + [random_chromosome(rng) for _ in range(pop_size - 1)]
    seed_chrom = pop[0]
    for c in pop:
        c.cid = c.cid or f"c{rng.integers(0,10**9):09d}"
        evaluate(c, splits)

    history = []
    for gen in range(1, generations + 1):
        pop.sort(key=lambda c: c.fitness, reverse=True)
        best = pop[0]
        history.append({"gen": gen, "best": best.fitness,
                        "mean": float(np.mean([c.fitness for c in pop])),
                        "best_sigma": best.eval_metrics.get("sigma_nmad"),
                        "best_eta": best.eval_metrics.get("eta")})
        if verbose:
            print(f"  gen {gen:02d}  best={best.fitness:+.4f}  "
                  f"mean={history[-1]['mean']:+.4f}  "
                  f"[σ={best.eval_metrics['sigma_nmad']:.4f} η={best.eval_metrics['eta']:.3f}]  "
                  f"{best.phenotype()['model']}/{best.phenotype()['degree']} "
                  f"{best.phenotype()['color_pairs']}")

        # next generation: elites (diversified by niche) + offspring
        kept, seen = [], set()
        for c in pop:                      # elitism with light niche dedup
            k = niche_key(c)
            if k in seen:
                continue
            seen.add(k); kept.append(c)
            if len(kept) >= elites:
                break
        breeders = pop[:max(elites, pop_size // 2)]

        new_pop = [copy.deepcopy(c) for c in kept]
        while len(new_pop) < pop_size:
            a = tournament(breeders, rng, 3)
            b = tournament(breeders, rng, 3)
            child = a.crossover(b, rng) if rng.random() < cx_rate else copy.deepcopy(a)
            if rng.random() < mut_rate:
                child = child.mutate(rng, strength=1.0)
            child.cid = f"c{rng.integers(0,10**9):09d}"
            evaluate(child, splits)
            new_pop.append(child)
        pop = new_pop

    pop.sort(key=lambda c: c.fitness, reverse=True)
    return pop[0], seed_chrom, history, splits


def _eval_on(chrom, splits, split_name):
    """Re-fit + score a chosen pipeline on a named split (for the honest TEST)."""
    from sklearn.preprocessing import StandardScaler, RobustScaler, PolynomialFeatures
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor
    # Train on TRAIN, then score on the requested split (TEST is held out).
    p = chrom.phenotype()
    Xtr = _design_matrix(splits["train"], p["color_pairs"], p["include_r"] > 0.5)
    Xs = _design_matrix(splits[split_name], p["color_pairs"], p["include_r"] > 0.5)
    ytr = splits["train"]["z_spec"].to_numpy(float)
    ys = splits[split_name]["z_spec"].to_numpy(float)
    if p["scale"] == "standard":
        sc = StandardScaler().fit(Xtr); Xtr, Xs = sc.transform(Xtr), sc.transform(Xs)
    elif p["scale"] == "robust":
        sc = RobustScaler().fit(Xtr); Xtr, Xs = sc.transform(Xtr), sc.transform(Xs)
    if p["degree"] > 1:
        pf = PolynomialFeatures(p["degree"], include_bias=False).fit(Xtr)
        Xtr, Xs = pf.transform(Xtr), pf.transform(Xs)
    if p["model"] == "ridge":
        mdl = Ridge(alpha=float(10 ** p["log_alpha"])).fit(Xtr, ytr)
    elif p["model"] == "rf":
        mdl = RandomForestRegressor(n_estimators=int(p["rf_trees"]),
                                    max_depth=int(p["rf_depth"]),
                                    n_jobs=-1, random_state=0).fit(Xtr, ytr)
    else:
        mdl = LinearRegression().fit(Xtr, ytr)
    return _metrics(mdl.predict(Xs), ys)


def main():
    t0 = time.time()
    print("=" * 72)
    print("AlphaEvolve-style POC — evolving a photometric-redshift pipeline")
    print("Data: REAL SDSS galaxies; target: independent z_spec. No mock data.")
    print("=" * 72)
    best, seed_chrom, history, splits = run()
    dt = time.time() - t0

    seed_test = _eval_on(seed_chrom, splits, "test")
    best_test = _eval_on(best, splits, "test")

    print("\n" + "=" * 72)
    print("RESULT (TEST = held-out real galaxies, never used for selection)")
    print("=" * 72)
    print(f"{'metric':<14}{'naive seed':>14}{'evolved best':>16}")
    print(f"{'σ_NMAD':<14}{seed_test['sigma_nmad']:>14.4f}{best_test['sigma_nmad']:>16.4f}")
    print(f"{'outlier η':<14}{seed_test['eta']:>14.3f}{best_test['eta']:>16.3f}")
    print(f"\nSeed   phenotype: {seed_chrom.phenotype()}")
    print(f"Best   phenotype: {best.phenotype()}")
    improvement = seed_test["sigma_nmad"] - best_test["sigma_nmad"]
    print(f"\nσ_NMAD improvement on held-out TEST: "
          f"{seed_test['sigma_nmad']:.4f} -> {best_test['sigma_nmad']:.4f}  "
          f"(Δ={improvement:+.4f}, {(improvement/seed_test['sigma_nmad'])*100:+.1f}%)")
    verdict = "PASS — evolution improved a real, machine-graded metric on held-out data" \
        if improvement > 0 else "FAIL — no improvement (investigate fitness landscape)"
    print(f"VERDICT: {verdict}")
    print(f"runtime: {dt:.1f}s")

    log = {
        "task": "photometric_redshift",
        "data_source": "SDSS CAS (real)",
        "n_train": len(splits["train"]), "n_eval": len(splits["eval"]),
        "n_test": len(splits["test"]),
        "seed": seed_chrom.phenotype(),
        "seed_test_metrics": seed_test,
        "best": best.phenotype(),
        "best_test_metrics": best_test,
        "history": history,
        "runtime_s": round(dt, 1),
    }
    out = Path(__file__).resolve().parent / "run_log.json"
    out.write_text(json.dumps(log, indent=2))
    print(f"\nrun log -> {out}")


if __name__ == "__main__":
    main()
