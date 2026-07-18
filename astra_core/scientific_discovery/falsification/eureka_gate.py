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

  classify_combined() uses Fisher's method to combine evidence across N systems,
  so that individually-marginal anomalies (z~2.5-3) can reach formal detection
  when they replicate independently.

Replication and literature-check are external inputs here (callables), so the
gate stays deterministic and machine-verifiable.
"""

import math
from typing import Callable, List, Optional
from scipy import stats
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


def classify_combined(results: List[AnomalyResult],
                      combined_threshold_sigma: float = 3.0,
                      literature_explained: Optional[Callable] = None) -> str:
    """Combine evidence across N independent systems using Fisher's method.

    Each result's z-score (delta_sigma) is converted to a one-sided p-value;
    Fisher's statistic chi2 = -2 * sum(ln(p_i)) is tested against chi2(2N).
    This lets individually-marginal anomalies (z~2.5-3) reach formal detection
    when they replicate across multiple independent systems.

    Args:
        results: list of AnomalyResult from independent systems.
        combined_threshold_sigma: the combined z-score required for detection.
        literature_explained: optional callable to demote if literature explains.
    """
    if not results:
        return MODEL_CONFIRMED

    # Convert each result's delta_sigma to a one-sided p-value
    p_values = []
    for r in results:
        z = r.delta_sigma
        if z <= 0:
            p_values.append(0.5)
        else:
            p_values.append(float(stats.norm.sf(z)))

    # Fisher's combined probability
    fisher_stat = -2.0 * sum(math.log(max(p, 1e-300)) for p in p_values)
    df = 2 * len(p_values)
    combined_p = float(stats.chi2.sf(fisher_stat, df))
    combined_z = float(stats.norm.isf(combined_p)) if combined_p > 0 else 10.0

    if combined_z < combined_threshold_sigma:
        return MODEL_CONFIRMED
    if literature_explained is not None and literature_explained(results[0]):
        return ANOMALY_CANDIDATE
    return EUREKA_CANDIDATE


__all__ = ['classify', 'classify_combined', 'MODEL_CONFIRMED', 'ANOMALY_CANDIDATE',
           'EUREKA_CANDIDATE']
