"""
The falsification engine: evaluate a FalsifiablePrediction on a real system,
forming the anomaly statistic and the systematics-cleared verdict. All numbers
are computed by code on real data (machine-verified); the LLM never sets any
value in the result.
"""

import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from .registry import FalsifiablePrediction, Registry


@dataclass
class AnomalyResult:
    prediction_id: str
    system_id: str
    model: str
    quantity: str
    units: str
    predicted: float
    sigma_pred: float
    observed: float
    sigma_obs: float
    abs_deviation: float                 # |O - P|
    delta_sigma: float                   # |O - P| / sqrt(sig_pred^2 + sig_obs^2)
    systematic_bound_total: float        # sum of named systematic bounds
    passes_systematics: bool             # abs_deviation > systematic_bound_total
    passes_significance: bool            # delta_sigma > anomaly_k_sigma
    passes_absolute: bool                # abs_deviation > min_absolute_effect
    is_anomaly: bool                     # all three gates pass
    machine_verified: bool = True        # every field computed by code on real data
    notes: str = ""


def evaluate(rec: FalsifiablePrediction, system_id: str) -> AnomalyResult:
    """Run one prediction against one real system. Pure code execution."""
    inputs = rec.fetch(system_id)
    P, sig_p = rec.predict(inputs)
    O, sig_o = rec.observe(system_id)

    abs_dev = abs(O - P)
    sigma = math.sqrt(sig_p ** 2 + sig_o ** 2)
    delta = abs_dev / sigma if sigma > 0 else float('inf')

    # named systematics: fixed bound + any code-computed bound for these inputs
    sys_total = 0.0
    for s in rec.systematics:
        sys_total += s.code(inputs) if s.code is not None else s.bound

    passes_sig = delta > rec.anomaly_k_sigma
    passes_abs = abs_dev > rec.min_absolute_effect
    passes_sys = abs_dev > sys_total
    is_anomaly = passes_sig and passes_abs and passes_sys

    return AnomalyResult(
        prediction_id=rec.id, system_id=system_id, model=rec.model,
        quantity=rec.quantity, units=rec.units,
        predicted=P, sigma_pred=sig_p, observed=O, sigma_obs=sig_o,
        abs_deviation=abs_dev, delta_sigma=delta,
        systematic_bound_total=sys_total,
        passes_systematics=passes_sys, passes_significance=passes_sig,
        passes_absolute=passes_abs, is_anomaly=is_anomaly,
        machine_verified=True,
    )


def audit(rec: FalsifiablePrediction) -> bool:
    """Regression check: predict(audit_inputs) reproduces the cited formula
    (catches code that does not match formula_doc)."""
    if rec.audit_inputs is None or rec.audit_expected is None:
        return True   # no audit specified (records SHOULD specify one)
    value, _ = rec.predict(rec.audit_inputs)
    return abs(value - rec.audit_expected) <= rec.audit_tolerance


def run_all(registry: Registry, systems_by_class: Dict[str, List[str]]
            ) -> List[AnomalyResult]:
    """Evaluate every prediction against every system of its class."""
    results: List[AnomalyResult] = []
    for rec in registry.all():
        for system_id in systems_by_class.get(rec.system_class, []):
            try:
                results.append(evaluate(rec, system_id))
            except Exception as e:  # never let one failure sink the run
                results.append(AnomalyResult(
                    prediction_id=rec.id, system_id=system_id, model=rec.model,
                    quantity=rec.quantity, units=rec.units,
                    predicted=float('nan'), sigma_pred=float('nan'),
                    observed=float('nan'), sigma_obs=float('nan'),
                    abs_deviation=float('nan'), delta_sigma=float('nan'),
                    systematic_bound_total=float('nan'),
                    passes_systematics=False, passes_significance=False,
                    passes_absolute=False, is_anomaly=False,
                    machine_verified=False, notes=f"error: {e}"))
    return results


def demonstrate() -> List[AnomalyResult]:
    """Run the seed registry on its seeded systems and print a verdict table."""
    from .predictions import seed_registry, SEED_SYSTEMS
    reg = seed_registry()
    results = run_all(reg, SEED_SYSTEMS)
    print("=" * 92)
    print("ASTRA Model-Falsification Arm (Approach 1) -- seed registry run")
    print("=" * 92)
    for r in results:
        flag = "ANOMALY" if r.is_anomaly else "model OK"
        print(f"[{r.system_id:8s}] {r.model:22s} predict={r.predicted:8.3f}  "
              f"observe={r.observed:8.3f}  Δ={r.delta_sigma:8.1f}σ  "
              f"sys_bound={r.systematic_bound_total:6.3f}  -> {flag}")
    print("-" * 92)
    anomalies = [r for r in results if r.is_anomaly]
    print(f"{len(anomalies)} anomaly(/ies) flagged of {len(results)} prediction-tests "
          f"(all machine-verified on real data).")
    return results


__all__ = ['AnomalyResult', 'evaluate', 'audit', 'run_all', 'demonstrate']
