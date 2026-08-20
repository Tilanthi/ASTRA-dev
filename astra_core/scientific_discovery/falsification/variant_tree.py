"""variant_tree.py — the anomaly must survive the model's own variant tree.

AstroMLab package #3 (variant-tree promotion test): a single model-vs-data
comparison can fake an anomaly — test the wrong variant or parameterization
of a model family and the observation looks anomalous when the mis-
specification is the only thing wrong. Promotion at the eureka gate therefore
requires the anomaly to survive a TREE of named model variants:

    variants = [(name, predict_fn), ...]   # each a cited parameterization

If the best-fitting variant brings the observation inside its k-sigma band,
the model FAMILY is not falsified and the candidate is demoted to
MODEL_CONFIRMED. Only an anomaly that survives every named variant (and the
replication + literature + temporal gates) promotes.

Variants are named and their formulas must be citable in the registry record
(``formula_doc``), so every branch of the tree is auditable — never an
unnamed "we tried fitting it" escape hatch.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from .engine import AnomalyResult, evaluate as _evaluate

Variant = Tuple[str, Callable[[Dict], Tuple[float, float]]]


def evaluate_variants(rec, system_id: str,
                      variants: Optional[List[Variant]] = None
                      ) -> List[Tuple[str, AnomalyResult]]:
    """Evaluate each named variant of ``rec`` against ``system_id``.

    Each variant is a ``predict(inputs) -> (value, sigma)`` replacement for
    the base record's predict; observe/fetch/systematics come from the base
    record so the comparison is apples-to-apples (same data, same gates).
    Results are tagged ``<rec.id>::<variant-name>`` for auditability.
    """

    class _VariantRec:
        pass

    out: List[Tuple[str, AnomalyResult]] = []
    for name, predict_fn in (variants or []):
        v = _VariantRec()
        for attr in ("id", "model", "quantity", "units", "systematics",
                     "anomaly_k_sigma", "min_absolute_effect", "fetch",
                     "observe"):
            setattr(v, attr, getattr(rec, attr))
        v.id = f"{rec.id}::{name}"
        v.predict = predict_fn
        try:
            out.append((name, _evaluate(v, system_id)))
        except Exception as e:  # a broken variant must not sink the tree
            out.append((name, AnomalyResult(
                prediction_id=v.id, system_id=system_id, model=v.model,
                quantity=v.quantity, units=v.units,
                predicted=float('nan'), sigma_pred=float('nan'),
                observed=float('nan'), sigma_obs=float('nan'),
                abs_deviation=float('nan'), delta_sigma=float('nan'),
                systematic_bound_total=float('nan'),
                passes_systematics=False, passes_significance=False,
                passes_absolute=False, is_anomaly=False,
                machine_verified=False, notes=f"variant error: {e}")))
    return out


def best_variant(results: List[Tuple[str, AnomalyResult]]
                 ) -> Optional[Tuple[str, AnomalyResult]]:
    """The variant closest to explaining the observation: smallest delta_sigma
    (ties -> first). This is the branch the anomaly must beat."""
    clean = [(n, r) for n, r in results if r.delta_sigma == r.delta_sigma]
    return min(clean, key=lambda nr: nr[1].delta_sigma) if clean else None


def promotion_test(results: List[Tuple[str, AnomalyResult]]) -> dict:
    """Does the anomaly survive every named variant of the model family?

    survives=True requires ALL variants to remain anomalies. If any variant
    fits the observation (is_anomaly=False), survives=False and best_variant
    names the branch that explained it — the audit trail for the demotion.
    """
    if not results:
        return {"survives": True, "n_variants": 0, "best_variant": None,
                "min_delta_sigma": None,
                "note": "no variants registered; single-model comparison"}
    fit = best_variant(results)
    survives = all(r.is_anomaly for _n, r in results)
    return {"survives": bool(survives),
            "n_variants": len(results),
            "best_variant": None if fit is None else fit[0],
            "min_delta_sigma": None if fit is None else round(
                fit[1].delta_sigma, 3)}


__all__ = ["Variant", "evaluate_variants", "best_variant", "promotion_test"]
