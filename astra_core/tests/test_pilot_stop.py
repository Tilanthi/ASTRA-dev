"""Tests for the F2 pilot-before-scale early-stop (2026-09-08).

Pins the cold-dataset pilot window in run_claim_search:
  * windowed history — "cold" means zero gate1 passes in the dataset's LAST
    PILOT_HISTORY_WINDOW verdict rows (lifetime passes do not count, and
    neither do other datasets' rows);
  * the arming rule — legacy source, disabled pilot, steps <= window, and
    warm datasets all leave the pilot unarmed;
  * the stop predicate — never stops on a gate1 pass or a worker error; the
    two stop reasons stay distinct (degenerate-proposals vs
    cold-dataset-no-gate1-pass);
  * the stop act — a kind="note" ledger line (NOT "trial": a pilot decision
    must not tighten the lifetime Bonferroni) carrying the counts that tell
    bar-too-tight / dataset-dead / degenerate-proposer apart, and the episode
    actually ends (no further steps evaluated);
  * the unchanged-skip — a proposal identical to its parent is never
    re-evaluated (pure spend; the pilot counts the degeneracy instead).

All heavy collaborators (two_gate_eval, the verdict log, the ledger) are
faked/redirected; no sandbox, no network, no persistent store is touched.

Run: python3 astra_core/tests/test_pilot_stop.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import astra_core.scientific_discovery.evolved_analysis.run_claim_search as rcs  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis import evidence_ledger as el  # noqa: E402


_SPLIT_CORRECT = ('CLAIM = "c%d"\n\n\ndef run_claim(df_train, df_eval):\n'
                  '    df = df_train\n'
                  '    return {"effect": 0.1, "pvalue": 0.2, "effect_type": "t", '
                  '"summary": "s"}\n')


class _SimpleMonkey:
    """Minimal monkeypatch for the plain (non-pytest) runner."""

    def __init__(self):
        self._undo = []

    def setattr(self, obj, name, value):
        self._undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def undo(self):
        for obj, name, old in reversed(self._undo):
            setattr(obj, name, old)
        self._undo = []


class _Redirected:
    """Redirect the verdict log + ledger to a tempdir."""

    def __enter__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="pilot_test_"))
        self.orig = {"VERDICT_LOG": rcs.VERDICT_LOG, "LEDGER": el.LEDGER}
        rcs.VERDICT_LOG = self.tmp / "claim_verdicts.jsonl"
        el.LEDGER = self.tmp / "evidence_ledger.jsonl"
        return self

    def __exit__(self, *exc):
        rcs.VERDICT_LOG = self.orig["VERDICT_LOG"]
        el.LEDGER = self.orig["LEDGER"]
        return False


def _vrow(ds, gate1_pass, ts="2026-09-01T00:00:00"):
    return {"ts": ts, "label": "step0", "dataset": ds, "claim": "c",
            "gate1": {"pass": gate1_pass}}


# --------------------------------------------------------------------------- #
# windowed history read                                                        #
# --------------------------------------------------------------------------- #
def test_history_is_windowed_per_dataset():
    """Cold = no gate1 pass in the LAST window rows: lifetime passes outside
    the window do not warm the dataset, and other datasets never count."""
    with _Redirected() as red:
        rows = []
        # 200 rows for cold_ds: the only passes sit ABOVE the 120-row window
        for i in range(200):
            rows.append(_vrow("cold_ds", gate1_pass=(i < 80)))
        # a warm dataset: one pass inside its own recent rows
        rows += [_vrow("warm_ds", gate1_pass=False) for _ in range(10)]
        rows.append(_vrow("warm_ds", gate1_pass=True))
        red.rcs_verdict = rows
        rcs.VERDICT_LOG.write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
        h_cold = rcs._dataset_gate1_history("cold_ds", window=120)
        h_warm = rcs._dataset_gate1_history("warm_ds", window=120)
    assert h_cold["n_trials"] == 120 and h_cold["n_gate1_pass"] == 0
    assert h_warm["n_trials"] == 11 and h_warm["n_gate1_pass"] == 1


def test_history_never_raises_on_missing_or_broken_log():
    with _Redirected():
        assert rcs._dataset_gate1_history("any")["n_trials"] == 0
        rcs.VERDICT_LOG.write_text("not json\n\nalso not json\n")
        h = rcs._dataset_gate1_history("any")
    assert h["n_trials"] == 0 and h["n_gate1_pass"] == 0


# --------------------------------------------------------------------------- #
# arming rule                                                                  #
# --------------------------------------------------------------------------- #
def test_arm_pilot_not_armed_for_legacy_disabled_or_short():
    with _Redirected():
        assert rcs._arm_pilot(steps=30, pilot_steps=3, source="legacy") is None
        assert rcs._arm_pilot(steps=30, pilot_steps=0, source="sdss_qso") is None
        assert rcs._arm_pilot(steps=3, pilot_steps=3, source="sdss_qso") is None
        assert rcs._arm_pilot(steps=2, pilot_steps=3, source="sdss_qso") is None


def test_arm_pilot_warm_dataset_not_armed_cold_armed():
    with _Redirected():
        rows = ([_vrow("warm_ds", True)] +
                [_vrow("warm_ds", False) for _ in range(30)])
        rcs.VERDICT_LOG.write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
        assert rcs._arm_pilot(steps=30, pilot_steps=3, source="warm_ds") is None
        rows = [_vrow("cold_ds", False) for _ in range(30)]
        rcs.VERDICT_LOG.write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
        pilot = rcs._arm_pilot(steps=30, pilot_steps=3, source="cold_ds")
    assert pilot is not None
    assert pilot["window"] == 3 and pilot["trials"] == 0
    assert pilot["hashes"] == set() and pilot["history"]["n_gate1_pass"] == 0


# --------------------------------------------------------------------------- #
# stop predicate                                                               #
# --------------------------------------------------------------------------- #
def _pilot(**kw):
    base = {"window": 3, "trials": 3, "gate1_pass": 0, "errors": 0,
            "unchanged": 0, "hashes": {"h1", "h2", "h3"}}
    base.update(kw)
    return base


def test_predicate_never_stops_on_pass_or_error_or_partial_window():
    assert rcs._pilot_should_stop(_pilot(gate1_pass=1)) is None
    assert rcs._pilot_should_stop(_pilot(errors=1)) is None
    assert rcs._pilot_should_stop(_pilot(trials=2)) is None    # window unfilled


def test_predicate_distinguishes_the_two_reasons():
    assert rcs._pilot_should_stop(_pilot(hashes={"only"})) == "degenerate-proposals"
    assert (rcs._pilot_should_stop(_pilot(unchanged=2, trials=1, hashes={"a", "b"}))
            == "cold-dataset-no-gate1-pass")


# --------------------------------------------------------------------------- #
# the step loop under an armed pilot                                           #
# --------------------------------------------------------------------------- #
class _FakeProposer:
    """Returns a distinct split-correct program each step (n = call count),
    or the parent verbatim with mode='unchanged' when degenerate=True."""

    def __init__(self, degenerate=False):
        self.degenerate = degenerate
        self.n = 0

    def propose(self, parent, parent_metrics, *_a, **_kw):
        self.n += 1
        if self.degenerate:
            return parent, None, {"mode": "unchanged"}
        return _SPLIT_CORRECT % self.n, None, {"mode": "mutate"}


def _patch_eval(monkeypatch, *, gate1_pass=False, error=None):
    calls = {"n": 0}

    def fake_eval(child, run_gate2=True, source="legacy", **kw):
        calls["n"] += 1
        metrics = {"effect": 0.1, "pvalue": 0.9}
        if error:
            metrics["error"] = error
        return {"claim": f"claim-{calls['n']}",
                "both_pass": False,
                "program_hash": f"h{calls['n']}",
                "source": child, "dataset": source,
                "gate1": {"pass": gate1_pass, "reason": "stubbed",
                          "metrics": metrics,
                          "bonferroni_pmax": 1e-5, "family_size": 50},
                "gate2": None}
    monkeypatch.setattr(rcs, "two_gate_eval", fake_eval)
    monkeypatch.setattr(rcs, "_append_verdict_log", lambda *a, **kw: None)
    return calls


def test_evolve_steps_stops_after_cold_window():
    """3-step window, 10 requested, distinct programs, no pass: the episode
    ends after step 3 with the cold-dataset reason and a ledger NOTE."""
    monkey = _SimpleMonkey()
    try:
        with _Redirected():
            calls = _patch_eval(monkey, gate1_pass=False)
            monkey.setattr(rcs, "_emit", lambda v: False)
            proposer = _FakeProposer()
            pilot = {"window": 3, "trials": 0, "gate1_pass": 0, "errors": 0,
                     "unchanged": 0, "hashes": set(), "history": {}}
            rcs._evolve_steps(proposer, _SPLIT_CORRECT % 0, {}, steps=10,
                              source="cold_ds", run_gate2=False, pilot=pilot)
            assert calls["n"] == 3, f"episode ran {calls['n']} steps, expected 3"
            notes = [json.loads(l) for l in el.LEDGER.read_text().splitlines()
                     if l.strip()]
            stops = [n for n in notes if n.get("kind") == "note"
                     and n.get("disposition") == "pilot-stop"]
            assert len(stops) == 1, notes
            s = stops[0]
            assert s["dataset"] == "cold_ds"
            assert s["n_trials"] == 3 and s["n_distinct_programs"] == 3
            assert s["skipped_steps"] == 7
            assert s["bonferroni_pmax"] is not None
            # kind note, NOT trial: a pilot decision is not a statistical look
            assert not any(n.get("kind") == "trial" for n in notes)
    finally:
        monkey.undo()


def test_evolve_steps_no_stop_when_gate1_passes():
    monkey = _SimpleMonkey()
    try:
        with _Redirected():
            calls = _patch_eval(monkey, gate1_pass=True)
            monkey.setattr(rcs, "_emit", lambda v: True)
            pilot = {"window": 3, "trials": 0, "gate1_pass": 0, "errors": 0,
                     "unchanged": 0, "hashes": set(), "history": {}}
            rcs._evolve_steps(_FakeProposer(), _SPLIT_CORRECT % 0, {},
                              steps=6, source="cold_ds", run_gate2=False,
                              pilot=pilot)
            assert calls["n"] == 6, "alive dataset must run the full episode"
            # accounting is window-scoped: only the first `window` steps count
            assert pilot["gate1_pass"] == 3
    finally:
        monkey.undo()


def test_evolve_steps_no_stop_on_worker_errors():
    monkey = _SimpleMonkey()
    try:
        with _Redirected():
            calls = _patch_eval(monkey, error="sandbox timeout")
            monkey.setattr(rcs, "_emit", lambda v: False)
            pilot = {"window": 3, "trials": 0, "gate1_pass": 0, "errors": 0,
                     "unchanged": 0, "hashes": set(), "history": {}}
            rcs._evolve_steps(_FakeProposer(), _SPLIT_CORRECT % 0, {},
                              steps=6, source="cold_ds", run_gate2=False,
                              pilot=pilot)
            assert calls["n"] == 6, "machine failure is not dataset evidence"
            assert pilot["errors"] == 3    # window-scoped accounting
    finally:
        monkey.undo()


def test_evolve_steps_degenerate_proposals_stop_early():
    """Proposer falls back to the parent verbatim every step: nothing is
    re-evaluated (zero sandbox runs) and the window fills on unchanged
    skips alone, firing the degenerate-proposals reason."""
    monkey = _SimpleMonkey()
    try:
        with _Redirected():
            calls = _patch_eval(monkey, gate1_pass=False)
            monkey.setattr(rcs, "_emit", lambda v: False)
            pilot = {"window": 3, "trials": 0, "gate1_pass": 0, "errors": 0,
                     "unchanged": 0, "hashes": set(), "history": {}}
            rcs._evolve_steps(_FakeProposer(degenerate=True),
                              _SPLIT_CORRECT % 0, {}, steps=10,
                              source="cold_ds", run_gate2=False, pilot=pilot)
            assert calls["n"] == 0, "unchanged proposals must never re-evaluate"
            stops = [json.loads(l) for l in el.LEDGER.read_text().splitlines()
                     if l.strip()]
            s = [n for n in stops if n.get("kind") == "note"
                 and n.get("disposition") == "pilot-stop"][0]
            assert s["reason"] == "degenerate-proposals"
            assert s["n_unchanged_skips"] == 3 and s["n_trials"] == 0
    finally:
        monkey.undo()


def test_evolve_steps_without_pilot_runs_all():
    monkey = _SimpleMonkey()
    try:
        with _Redirected():
            calls = _patch_eval(monkey, gate1_pass=False)
            monkey.setattr(rcs, "_emit", lambda v: False)
            rcs._evolve_steps(_FakeProposer(), _SPLIT_CORRECT % 0, {},
                              steps=5, source="cold_ds", run_gate2=False,
                              pilot=None)
            assert calls["n"] == 5
    finally:
        monkey.undo()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except AssertionError as ex:
            failed += 1
            print(f"FAIL {fn.__name__}: {ex}")
        except Exception as ex:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(ex).__name__}: {ex}")
        else:
            print(f"PASS {fn.__name__}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
