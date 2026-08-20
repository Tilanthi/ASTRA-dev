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
from .contamination_guards import temporal_check

# Result tiers
MODEL_CONFIRMED = "model_confirmed"
ANOMALY_CANDIDATE = "anomaly_candidate"
EUREKA_CANDIDATE = "eureka_candidate"


def classify(primary: AnomalyResult,
             replication: Optional[AnomalyResult] = None,
             literature_explained: Optional[Callable[[AnomalyResult], bool]] = None,
             prediction_year: Optional[int] = None,
             data_release_year: Optional[int] = None,
             variant_results: Optional[List[tuple]] = None,
             ) -> str:
    """Classify a falsification outcome into a discovery tier.

    Args:
        primary: the anomaly result on the primary system.
        replication: an independent anomaly result (holdout system/measurement).
            If it is also an anomaly, the primary is promoted.
        literature_explained: optional callable returning True if the anomaly is
            already explained by existing literature (demotes a eureka candidate
            back to anomaly_candidate). None = literature check pending.
        prediction_year / data_release_year: temporal-contamination guard
            (contamination_guards.temporal_check). A prediction made AFTER the
            data it is tested against was released could have been fit to it,
            so promotion to EUREKA_CANDIDATE is withheld (stays
            ANOMALY_CANDIDATE). Unknown years defer.
        variant_results: optional output of variant_tree.evaluate_variants —
            (name, AnomalyResult) per named variant of the model family. If
            ANY variant fits the observation, the anomaly was a mis-
            specification artifact and the tier is MODEL_CONFIRMED for the
            family (variant_tree.promotion_test).
    """
    if not primary.is_anomaly:
        return MODEL_CONFIRMED
    if variant_results is not None:
        from .variant_tree import promotion_test
        if not promotion_test(variant_results)["survives"]:
            return MODEL_CONFIRMED
    if replication is None:
        return ANOMALY_CANDIDATE
    if not replication.is_anomaly:
        return ANOMALY_CANDIDATE
    # anomaly replicates -> eureka candidate, unless literature already explains it
    if literature_explained is not None and literature_explained(primary):
        return ANOMALY_CANDIDATE
    # temporal contamination: prediction postdates the data release
    ok, _reason = temporal_check(prediction_year, data_release_year)
    if not ok:
        return ANOMALY_CANDIDATE
    return EUREKA_CANDIDATE


def quarantine_narration(narration: str, records) -> tuple:
    """Emission chokepoint for LLM narrations of falsification results.

    Holdout registry entries never enter an LLM context
    (contamination_guards.llm_visible), so a narration that restates a holdout
    entry's content is confabulation or a leak. Returns (ok, alarm): ok=False
    means the narration must be quarantined (never emitted/promoted) until a
    human inspects the pipeline.
    """
    from .contamination_guards import holdout_alarm
    alarm = holdout_alarm(narration, records)
    return (alarm is None), alarm


def classify_combined(results: List[AnomalyResult],
                      combined_threshold_sigma: float = 3.0,
                      literature_explained: Optional[Callable] = None,
                      prediction_year: Optional[int] = None,
                      data_release_year: Optional[int] = None) -> str:
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
    ok, _reason = temporal_check(prediction_year, data_release_year)
    if not ok:
        return ANOMALY_CANDIDATE
    return EUREKA_CANDIDATE


__all__ = ['classify', 'classify_combined', 'MODEL_CONFIRMED', 'ANOMALY_CANDIDATE',
           'EUREKA_CANDIDATE']
