"""leapcore.py — load the REAL astra_core leapcore_evolution classes by file path.

We import the actual module from ``astra_core/intelligence/leapcore_evolution.py``
WITHOUT going through ``astra_core/__init__.py``. This wires us to the genuine
ASTRA evolutionary data structures (FitnessEvaluator ABC, Chromosome, Gene,
EvolutionConfig) while staying fully decoupled from the auto-start discovery
service and the rest of the astra_core import graph.

If the file moves or is renamed, point LEAPCORE_PATH at the new location.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]          # .../ASTRA-dev-main
LEAPCORE_PATH = REPO_ROOT / "astra_core" / "intelligence" / "leapcore_evolution.py"


def _load():
    if not LEAPCORE_PATH.exists():
        raise FileNotFoundError(
            f"Real leapcore_evolution.py not found at {LEAPCORE_PATH}. "
            "Update LEAPCORE_PATH in code_evolve/leapcore.py.")
    spec = importlib.util.spec_from_file_location("astra_leapcore_real", LEAPCORE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load()
FitnessEvaluator = _mod.FitnessEvaluator      # ABC: subclass and implement evaluate()
Chromosome = _mod.Chromosome                  # fields: chromosome_id, genes, fitness,
                                              #         generation, parent_ids, metadata
Gene = _mod.Gene
EvolutionConfig = _mod.EvolutionConfig

__all__ = ["FitnessEvaluator", "Chromosome", "Gene", "EvolutionConfig",
           "LEAPCORE_PATH", "REPO_ROOT"]
