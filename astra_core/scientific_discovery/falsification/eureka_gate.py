"""
The Eureka gate: promote an anomaly to a paradigm-shift-tier candidate.

This is the IMPORTANCE filter (today's chain only has a significance filter).
It is narrower and more falsifiable than "is the correlation real + novel":

  model_confirmed    -- observation agrees with the model (no anomaly)
  anomaly_candidate  -- single-system anomaly that cleared significance +
                        absolute-effect + named-systematics gates
  eureka_candidate   -- an anomaly_candidate that also REPLICATES on an
                        independent system/measurement of the same class
                        (holdout); promoted to Eureka only after a literature
                        check confirms it is not already explained.

Replication and literature-check are external inputs here (callables), so the
gate stays deterministic and machine-verifiable.
"""

from typing import Callable, Optional
from .engine import AnomalyResult

# Result tiers
MODEL_CONFIRMED = "model_confirmed"
ANOMALY_CANDIDATE = "anomaly_candidate"
EUREKA_CANDIDATE = "eureka_candidate"


def classify(primary: AnomalyResult,
             replication: Optional[AnomalyResult] = None,
             literature_explained: Optional[Callable[[AnomalyResult], bool]] = None
             ) -> str:
    """Classify a falsification outcome into a discovery tier.

    Args:
        primary: the anomaly result on the primary system.
        replication: an independent anomaly result (holdout system/measurement).
            If it is also an anomaly, the primary is promoted.
        literature_explained: optional callable returning True if the anomaly is
            already explained by existing literature (demotes a eureka candidate
            back to anomaly_candidate). None = literature check pending.
    """
    if not primary.is_anomaly:
        return MODEL_CONFIRMED
    if replication is None:
        return ANOMALY_CANDIDATE
    if not replication.is_anomaly:
        return ANOMALY_CANDIDATE
    # anomaly replicates -> eureka candidate, unless literature already explains it
    if literature_explained is not None and literature_explained(primary):
        return ANOMALY_CANDIDATE
    return EUREKA_CANDIDATE


__all__ = ['classify', 'MODEL_CONFIRMED', 'ANOMALY_CANDIDATE', 'EUREKA_CANDIDATE']
