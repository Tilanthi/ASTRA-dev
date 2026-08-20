"""Variant-tree promotion test for the eureka gate (AstroMLab package #3).

A single-model comparison can fake an anomaly: pick the wrong variant or
parameterization of a model family and the observation looks anomalous when
it is really the mis-specification that is wrong. Promotion therefore
requires the anomaly to survive a TREE of named model variants — if the
best-fitting variant of the family brings the observation inside its
k-sigma band, the family is not falsified.

Run: python3 astra_core/tests/test_variant_tree.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.falsification import variant_tree as vt  # noqa: E402
from astra_core.scientific_discovery.falsification.eureka_gate import (  # noqa: E402
    classify, EUREKA_CANDIDATE, MODEL_CONFIRMED)
from astra_core.scientific_discovery.falsification.engine import AnomalyResult  # noqa: E402


class _FakeRec:
    """Registry-shaped record: evaluate() consults its predict/observe."""
    def __init__(self, predict, observe, systematics=(), k=4.0, min_abs=0.0):
        self.id = "test_pred"
        self.model = "TestModel"
        self.quantity = "q"
        self.units = "u"
        self.systematics = list(systematics)
        self.anomaly_k_sigma = k
        self.min_absolute_effect = min_abs
        self.fetch = lambda sid: {}
        self.predict = predict
        self.observe = lambda sid: observe


def _variant_result(delta_sigma, is_anom):
    return AnomalyResult(prediction_id="test_pred::v", system_id="s",
                         model="TestModel", quantity="q", units="u",
                         predicted=1.0, sigma_pred=0.1, observed=3.0,
                         sigma_obs=0.1, abs_deviation=2.0,
                         delta_sigma=delta_sigma, systematic_bound_total=0.0,
                         passes_systematics=is_anom,
                         passes_significance=is_anom,
                         passes_absolute=is_anom, is_anomaly=is_anom)


def test_variant_results_carry_names():
    res = vt.evaluate_variants(
        _FakeRec(lambda i: (1.0, 0.1), (3.0, 0.1)),
        "sys",
        variants=[("plain", lambda i: (1.0, 0.1)),
                  ("with-quadrupole", lambda i: (2.9, 0.1))])
    assert [r[0] for r in res] == ["plain", "with-quadrupole"]
    assert all(hasattr(r[1], "is_anomaly") for r in res)


def test_fitting_variant_explains_observation():
    """The 'with-quadrupole' variant predicts 2.9 where 3.0 is observed —
    inside the band, so the family is NOT falsified."""
    res = vt.evaluate_variants(
        _FakeRec(lambda i: (1.0, 0.1), (3.0, 0.1)),
        "sys",
        variants=[("plain", lambda i: (1.0, 0.1)),
                  ("with-quadrupole", lambda i: (2.9, 0.1))])
    fit = vt.best_variant(res)
    assert fit[0] == "with-quadrupole" and fit[1].is_anomaly is False


def test_survives_when_all_variants_anomalous():
    res = [("_v1", _variant_result(9.0, True)),
           ("_v2", _variant_result(11.0, True))]
    assert vt.promotion_test(res)["survives"] is True


def test_fails_when_one_variant_fits():
    res = [("_v1", _variant_result(9.0, True)),
           ("_v2", _variant_result(1.2, False))]
    out = vt.promotion_test(res)
    assert out["survives"] is False
    assert out["best_variant"] == "_v2"
    assert out["min_delta_sigma"] == 1.2


def test_classify_demotes_when_variant_explains():
    primary = _variant_result(9.0, True)
    replication = _variant_result(9.0, True)
    variants = [("v1", _variant_result(9.0, True)),
                ("v2", _variant_result(1.2, False))]
    assert classify(primary, replication,
                    variant_results=variants) == MODEL_CONFIRMED


def test_classify_promotes_when_variants_all_anomalous():
    primary = _variant_result(9.0, True)
    replication = _variant_result(9.0, True)
    variants = [("v1", _variant_result(9.0, True)),
                ("v2", _variant_result(8.0, True))]
    assert classify(primary, replication,
                    variant_results=variants) == EUREKA_CANDIDATE


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
