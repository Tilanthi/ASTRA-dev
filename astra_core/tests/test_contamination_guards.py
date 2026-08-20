"""Contamination guards for the falsification arm (AstroMLab package #7).

EAIRA keeps ~70% of its benchmark private as a sliding contamination probe;
IOAA checks model-cutoff vs exam-date. ASTRA's translation: a deterministic
30% of registry predictions are holdout — never shown to the LLM — and any
narrated claim that matches a holdout entry raises a confabulation alarm.
Predictions are also checked against data-release dates: a "prediction" that
postdates its own test data could have been fit to it.

Run: python3 astra_core/tests/test_contamination_guards.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.falsification import contamination_guards as cg  # noqa: E402


class _Rec:
    def __init__(self, pid, quantity, doc):
        self.id = pid
        self.quantity = quantity
        self.formula_doc = doc


def test_holdout_split_is_deterministic_and_partial():
    a = cg.is_holdout("gr_perihelion_mercury")
    assert a == cg.is_holdout("gr_perihelion_mercury")
    ids = [f"pred_{i}" for i in range(200)]
    frac = sum(cg.is_holdout(i) for i in ids) / len(ids)
    assert 0.15 < frac < 0.45, frac


def test_llm_visible_excludes_holdout():
    recs = [_Rec(f"p{i}", "perihelion shift", "GR predicts 43 arcsec/century")
            for i in range(50)]
    visible = cg.llm_visible(recs)
    assert all(not cg.is_holdout(r.id) for r in visible)
    assert len(visible) < len(recs)


def test_holdout_alarm_fires_on_verbatim_leak():
    recs = [_Rec("leaky_pred", "perihelion shift",
                 "GR predicts a perihelion advance of 43 arcsec per century")]
    # force it into the holdout set for the test
    cg._FORCE_HOLDOUT = {"leaky_pred"}
    try:
        alarm = cg.holdout_alarm(
            "the perihelion advance of 43 arcsec per century predicted by GR",
            recs)
        assert alarm and alarm["matched_id"] == "leaky_pred"
    finally:
        cg._FORCE_HOLDOUT = set()


def test_holdout_alarm_quiet_on_unrelated_text():
    recs = [_Rec("leaky_pred", "perihelion shift",
                 "GR predicts a perihelion advance of 43 arcsec per century")]
    cg._FORCE_HOLDOUT = {"leaky_pred"}
    try:
        assert cg.holdout_alarm("molecular cloud filaments follow "
                                "magnetic field directions", recs) is None
    finally:
        cg._FORCE_HOLDOUT = set()


def test_temporal_check_prediction_postdating_data_fails():
    ok, reason = cg.temporal_check(prediction_year=2020,
                                   data_release_year=2015)
    assert not ok and "postdates" in reason


def test_temporal_check_data_after_prediction_passes():
    ok, reason = cg.temporal_check(prediction_year=1990,
                                   data_release_year=2015)
    assert ok, reason


def test_temporal_check_unknown_year_defers():
    ok, reason = cg.temporal_check(prediction_year=None,
                                   data_release_year=2015)
    assert ok and "unknown" in reason


# --- wiring into the eureka gate -----------------------------------------
from astra_core.scientific_discovery.falsification.eureka_gate import (  # noqa: E402
    classify, quarantine_narration, EUREKA_CANDIDATE, ANOMALY_CANDIDATE)
from astra_core.scientific_discovery.falsification.engine import AnomalyResult  # noqa: E402


def _anomaly():
    return AnomalyResult(prediction_id="p", system_id="s", model="m",
                         quantity="q", units="u", predicted=1.0,
                         sigma_pred=0.1, observed=3.0, sigma_obs=0.1,
                         abs_deviation=2.0, delta_sigma=14.0,
                         systematic_bound_total=0.5, passes_systematics=True,
                         passes_significance=True, passes_absolute=True,
                         is_anomaly=True)


def test_classify_promotes_replicated_anomaly():
    assert classify(_anomaly(), _anomaly()) == EUREKA_CANDIDATE


def test_temporal_contamination_demotes_promotion():
    tier = classify(_anomaly(), _anomaly(),
                    prediction_year=2020, data_release_year=2015)
    assert tier == ANOMALY_CANDIDATE


def test_temporal_clean_still_promotes():
    tier = classify(_anomaly(), _anomaly(),
                    prediction_year=1915, data_release_year=2015)
    assert tier == EUREKA_CANDIDATE


def test_quarantine_narration_blocks_holdout_leak():
    recs = [_Rec("leaky_pred", "perihelion shift",
                 "GR predicts a perihelion advance of 43 arcsec per century")]
    cg._FORCE_HOLDOUT = {"leaky_pred"}
    try:
        ok, alarm = quarantine_narration(
            "the perihelion advance of 43 arcsec per century predicted by GR",
            recs)
        assert not ok and alarm and alarm["matched_id"] == "leaky_pred"
    finally:
        cg._FORCE_HOLDOUT = set()


def test_classify_combined_temporal_demotion():
    from astra_core.scientific_discovery.falsification.eureka_gate import (
        classify_combined)
    tier_ok = classify_combined([_anomaly(), _anomaly()])
    assert tier_ok == EUREKA_CANDIDATE
    tier_bad = classify_combined([_anomaly(), _anomaly()],
                                 prediction_year=2020,
                                 data_release_year=2015)
    assert tier_bad == ANOMALY_CANDIDATE


def test_quarantine_narration_clean_text_passes():
    recs = [_Rec("leaky_pred", "perihelion shift",
                 "GR predicts a perihelion advance of 43 arcsec per century")]
    cg._FORCE_HOLDOUT = {"leaky_pred"}
    try:
        ok, alarm = quarantine_narration("filaments align with fields", recs)
        assert ok and alarm is None
    finally:
        cg._FORCE_HOLDOUT = set()


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
