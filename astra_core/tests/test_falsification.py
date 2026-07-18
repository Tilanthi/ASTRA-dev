"""Tests for the model-falsification discovery arm.

Verifies: (a) audit regression -- predict() matches the cited formula on known
inputs; (b) the engine's negative control -- GR perihelion is CONFIRMED on
Mercury (no false anomaly); (c) the engine's anomaly detection -- Newtonian
gravity is FALSIFIED on Mercury (the historical anomaly); (d) the eureka gate
tier classification.
"""

import pytest
from astra_core.scientific_discovery.falsification import (
    evaluate, audit, classify, MODEL_CONFIRMED, ANOMALY_CANDIDATE, EUREKA_CANDIDATE)
from astra_core.scientific_discovery.falsification.predictions import seed_registry


@pytest.fixture(scope="module")
def reg():
    return seed_registry()


def test_audit_regression_gr(reg):
    # GR perihelion formula reproduces the cited ~42.98 arcsec/century for Mercury
    rec = reg.get("gr_perihelion_mercury")
    assert rec is not None
    assert audit(rec) is True, "GR predict() must match the cited Will(2018) formula"
    value, _ = rec.predict(rec.audit_inputs)
    assert abs(value - 42.98) < 0.6


def test_audit_regression_newton(reg):
    rec = reg.get("newton_perihelion_mercury")
    assert audit(rec) is True


def test_gr_confirmed_negative_control(reg):
    """GR perihelion on Mercury: model agrees with observation -> NOT an anomaly.
    (This is the false-positive guard.)"""
    r = evaluate(reg.get("gr_perihelion_mercury"), "mercury")
    assert r.machine_verified
    assert r.is_anomaly is False, "GR should be confirmed (no anomaly) on Mercury"
    assert r.delta_sigma < 1.5
    assert classify(r) == MODEL_CONFIRMED


def test_newton_falsified_anomaly(reg):
    """Newtonian gravity on Mercury: predicts 0, observed ~42.98 -> ANOMALY.
    This is the canonical paradigm-shift anomaly (resolved by GR)."""
    r = evaluate(reg.get("newton_perihelion_mercury"), "mercury")
    assert r.machine_verified
    assert r.is_anomaly is True, "Newton should be falsified on Mercury"
    assert r.delta_sigma > 4.0
    assert r.passes_systematics is True   # deviation >> named systematics
    assert classify(r) == ANOMALY_CANDIDATE  # no replication -> anomaly, not eureka yet


def test_eureka_promotion_requires_replication(reg):
    """An anomaly only becomes a eureka candidate when it replicates."""
    primary = evaluate(reg.get("newton_perihelion_mercury"), "mercury")
    # no replication -> stays anomaly_candidate
    assert classify(primary) == ANOMALY_CANDIDATE
    # a replication (independent anomaly result) -> eureka_candidate
    assert classify(primary, replication=primary) == EUREKA_CANDIDATE
