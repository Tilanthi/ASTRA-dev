"""
ASTRA Model-Falsification discovery arm (Approach 1).

Repoints discovery from catalog correlation-mining toward model falsification:
test named, cited, code-evaluated predictions of physical models against real
data and flag ANOMALIES (deviations surviving statistical + named-systematic +
absolute-effect gates). Replicating, literature-unexplained anomalies are
Eureka-tier candidates.

See registry.py for the fiction-safety contract. Seed predictions live in
`predictions/`; the engine and eureka gate are in engine.py / eureka_gate.py.
"""

from .registry import FalsifiablePrediction, SystematicCheck, Registry
from .engine import AnomalyResult, evaluate, audit, run_all, demonstrate
from .eureka_gate import classify, classify_combined, MODEL_CONFIRMED, ANOMALY_CANDIDATE, EUREKA_CANDIDATE

__all__ = [
    'FalsifiablePrediction', 'SystematicCheck', 'Registry',
    'AnomalyResult', 'evaluate', 'audit', 'run_all', 'demonstrate',
    'classify', 'classify_combined',
    'MODEL_CONFIRMED', 'ANOMALY_CANDIDATE', 'EUREKA_CANDIDATE',
]
