"""
Model-falsification discovery arm (Approach 1).

Atom = a FalsifiablePrediction: a *named, cited model prediction* paired with
the *code that evaluates it on real data*. The engine computes, in code,
whether the observed real-data value deviates from the model's prediction
beyond the combined statistical and *named systematic* uncertainty. Anomalies
that clear that bar and replicate are Eureka-tier candidates.

Fiction-safety contract (stricter than the correlation-mining chain):
  * predictions are CURATED + CITED + CODE (`predict()` implements
    `formula_doc`, which carries `model_citation`). The LLM never asserts what
    a model predicts -- it only narrates results.
  * each record ships an audit regression (`audit_inputs`/`audit_expected`)
    asserting `predict()` reproduces the cited formula on known inputs.
  * `fetch`/`observe` run on real data (cited published measurements in the
    seed registry; live archive fetchers in production). No synthetic data.
  * systematics are NAMED + CODE/VALUE-BOUNDED; an anomaly must clear the sum
    of the named systematic bounds, not just the statistical sigma.

References:
  N.R. Will, "The Confrontation between General Relativity and Experiment",
    LRR 21, 4 (2018) -- perihelion precession formula and measured values.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Dict, Any


@dataclass
class SystematicCheck:
    """A named systematic effect with an upper bound on its possible
    contribution (same units as the predicted quantity). The bound may be a
    fixed value (from the literature) or computed by `code(system_inputs)`."""
    name: str
    bound: float
    code: Optional[Callable[[Dict[str, Any]], float]] = None
    note: str = ""


@dataclass
class FalsifiablePrediction:
    id: str
    model: str                                       # the theory being tested
    model_citation: str                              # real reference for the formula
    quantity: str                                    # what is predicted/observed
    units: str
    system_class: str                                # class of astronomical system
    formula_doc: str                                 # human-auditable formula (cited)
    predict: Callable[[Dict[str, Any]], Tuple[float, float]]   # inputs -> (value, sigma_pred)
    fetch: Callable[[str], Dict[str, Any]]                      # system_id -> real inputs
    observe: Callable[[str], Tuple[float, float]]               # system_id -> (value, sigma_obs)
    observe_citation: str                            # real reference for the observed value
    systematics: List[SystematicCheck] = field(default_factory=list)
    min_absolute_effect: float = 0.0                 # deviation must exceed this
    anomaly_k_sigma: float = 4.0                     # Δ = |O-P|/√(σ²pred+σ²obs) threshold
    # audit regression: predict(audit_inputs) must ~= audit_expected (catches code/formula mismatch)
    audit_inputs: Optional[Dict[str, Any]] = None
    audit_expected: Optional[float] = None
    audit_tolerance: float = 0.05


class Registry:
    """A curated collection of FalsifiablePrediction records."""

    def __init__(self):
        self._records: List[FalsifiablePrediction] = []

    def register(self, record: FalsifiablePrediction) -> FalsifiablePrediction:
        self._records.append(record)
        return record

    def all(self) -> List[FalsifiablePrediction]:
        return list(self._records)

    def by_class(self, system_class: str) -> List[FalsifiablePrediction]:
        return [r for r in self._records if r.system_class == system_class]

    def get(self, prediction_id: str) -> Optional[FalsifiablePrediction]:
        for r in self._records:
            if r.id == prediction_id:
                return r
        return None


__all__ = ['SystematicCheck', 'FalsifiablePrediction', 'Registry']
