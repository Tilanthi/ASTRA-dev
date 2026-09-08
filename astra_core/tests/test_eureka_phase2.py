"""Tests for the Phase-1 external clock + Phase-2 Eureka build (2026-08-30).

Covers:
  * eureka_clock — offsets (nothing re-processed on the second firing),
    new-vs-old collision detection (dataset + claim-content), re-encounter
    entries written and annotated onto the register, pairing surfaced in the
    proposer prompt head, never-raises contract;
  * fresh_attacker — disposition rules (survived / killed / not-runnable /
    suspect) with the sandbox re-run stubbed, and the hard rule at the emit
    point (killed findings are never written to the store);
  * claim_eval_worker._permute_splits — marginals preserved, cross-column
    associations destroyed;
  * calibration_lens — note form, head ordering, the verdicts-changed counter,
    delivery inside task_system_for;
  * novelty_gate live-source check — a cached known-verdict without a fresh
    live check is downgraded to known-cache-only and never cached; with live
    papers it stands and the check is stamped; a fresh check within the TTL
    does not re-retrieve;
  * discovery_review — an attack the finding survived earns the "escalated"
    label by rule.

All tests run against a tempdir: the real ~/.astra_persistent stores are
never touched.

Run: python3 astra_core/tests/test_eureka_phase2.py
"""
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import evidence_ledger as el  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis import eureka_clock as ck    # noqa: E402
from astra_core.scientific_discovery.evolved_analysis import calibration_lens as cl  # noqa: E402


class _Isolated:
    """Redirect every store path the clock/lens/ledger touch to a tempdir."""

    def __init__(self, verdict_lines=None, ledger_lines=None):
        self.tmp = Path(tempfile.mkdtemp(prefix="eureka_phase2_test_"))
        led = self.tmp / "evidence_ledger.jsonl"
        ver = self.tmp / "claim_verdicts.jsonl"
        reg = self.tmp / "unsolved_register.json"
        cor = self.tmp / "lifetime_correction_report.json"
        nots = self.tmp / "calibration_notes.json"
        self.el_paths = {"EVOLVED_PROGRAMS": self.tmp, "LEDGER": led,
                         "VERDICT_LOG": ver, "CONDUCT_LOG": self.tmp / "conduct.jsonl",
                         "QUARANTINE": self.tmp / "quarantine.json",
                         "REGISTER": reg, "CORRECTION_REPORT": cor}
        self.ck_paths = {"LEDGER": led, "VERDICT_LOG": ver, "REGISTER": reg}
        self.cl_paths = {"NOTES": nots, "VERDICT_LOG": ver}
        if verdict_lines is not None:
            ver.write_text("".join(json.dumps(v) + "\n" for v in verdict_lines))
        if ledger_lines is not None:
            led.write_text("".join(json.dumps(v) + "\n" for v in ledger_lines))

    def __enter__(self):
        self.orig = {}
        for mod, paths in ((el, self.el_paths), (ck, self.ck_paths), (cl, self.cl_paths)):
            for k, v in paths.items():
                self.orig[(id(mod), k)] = getattr(mod, k)
                setattr(mod, k, v)
        return self

    def __exit__(self, *exc):
        for mod, paths in ((el, self.el_paths), (ck, self.ck_paths), (cl, self.cl_paths)):
            for k in paths:
                setattr(mod, k, self.orig[(id(mod), k)])
        return False


def _verdict(claim, ds="sdss_qso", status="judge-failed", pass_g1=True, ts="2026-08-20T00:00:00"):
    g2_pass = None
    if status == "novel":
        g2_pass = True
    elif status == "known":
        g2_pass = False
    return {"ts": ts, "claim": claim, "program_hash": "h" + claim[:6],
            "dataset": ds,
            "gate1": {"pass": pass_g1, "effect": 0.4, "pvalue": 1e-8,
                      "reason": "ok",
                      "metrics": {"effect": 0.4, "pvalue": 1e-8},
                      "bonferroni_pmax": 4e-8, "family_size": 4},
            "triviality": True, "consistency": True, "holdout": True,
            "gate2": {"status": status, "pass": g2_pass, "n_retrieved": 4,
                      "reasoning": "r"},
            "both_pass": status == "novel"}


# --------------------------------------------------------------------------- #
# eureka_clock                                                                 #
# --------------------------------------------------------------------------- #

def test_clock_first_firing_finds_collision_and_annotates_register(monkeypatch):
    """A new verdict on the same dataset with overlapping claim content must
    re-encounter the old narrow-gate-failure, write a register/re-encountered
    entry, and stamp the register entry so the proposer head leads with it."""
    from astra_core.scientific_discovery.evolved_analysis import data_lake as dl
    # hermetic: no real falsification-prediction fetches from the clock's
    # lens step (the lens has its own tests)
    monkeypatch.setattr(cl, "recompute", lambda write=True: [])
    verdicts = [_verdict("quasars with red W1-W2 colour show broad CIV lines",
                         status="judge-failed", ts="2026-08-01T00:00:00"),
                # NEW evidence after the register entry: same dataset, overlapping content
                _verdict("quasars with red W1-W2 colour show broad CIV emission shifts",
                         status="known", ts="2026-08-28T00:00:00")]
    with _Isolated(verdict_lines=verdicts):
        summary = ck.run_clock()
        assert summary["disposition"] == "clock-ran"
        assert summary["register_entries"] >= 1
        assert summary["n_reencounters"] >= 1, summary
        # the re-encounter is a ledger entry of its own
        re = [e for e in el.read_ledger()
              if e.get("kind") == "register" and e.get("disposition") == "re-encountered"]
        assert re and "what do they share" in re[0]["detail"]
        # the register entry now carries the count, and the proposer head
        # leads with the pairing
        entries = el.build_register(write=False)
        matched = [e for e in entries if e.get("reencounters")]
        assert matched, "re-encounter not annotated onto the register entry"
        head = dl.unsolved_register_head("sdss_qso", 3)
        assert any("NEW EVIDENCE" in line for line in head), head
        # the clock entry itself stamped the offsets it consumed
        clock_entries = [e for e in el.read_ledger() if e.get("kind") == "clock"]
        assert clock_entries[-1]["ledger_lines_seen"] >= 1


def test_clock_second_firing_processes_nothing_new(monkeypatch):
    monkeypatch.setattr(cl, "recompute", lambda write=True: [])
    verdicts = [_verdict("c-old", status="judge-failed", ts="2026-08-01T00:00:00")]
    with _Isolated(verdict_lines=verdicts):
        first = ck.run_clock()
        second = ck.run_clock()
        assert second["disposition"] == "clock-ran"
        assert second["n_new_evidence"] == 0, second
        assert second["n_reencounters"] == 0, second
        assert first["ledger_lines_seen"] <= second["ledger_lines_seen"]


def test_clock_never_raises_on_broken_ledger():
    with _Isolated():
        # malformed ledger content: the clock must record the failure, not crash
        ck.LEDGER.write_text("this is not json\n")
        ck.VERDICT_LOG.write_text("also not json\n")
        summary = ck.run_clock()
        assert summary["disposition"] in ("clock-ran", "clock-failed")


def test_clock_tokens_and_jaccard():
    a = ck._tokens("quasars with red W1-W2 colour show broad CIV lines")
    b = ck._tokens("quasars with red W1-W2 colour show broad CIV emission shifts")
    assert ck._jaccard(a, b) >= 0.45
    assert ck._jaccard(a, ck._tokens("pulsar timing residuals constrain planet mass")) < 0.1


# --------------------------------------------------------------------------- #
# fresh_attacker (dispositions + the emit-point hard rule)                     #
# --------------------------------------------------------------------------- #

_SRC = "CLAIM = 'test claim'\ndef run_claim(df_train, df_eval):\n    return {'effect': 0.3, 'pvalue': 1e-9}\n"


def _patch_gate1(monkey, *, resplit_results, permute_results):
    """Stub run_claim_search.gate1_run; fresh_attacker imports it lazily."""
    from astra_core.scientific_discovery.evolved_analysis import run_claim_search as rcs
    calls = []
    per_bucket = {"resplit": 0, "permute": 0}

    def fake(src, seed=42, source="legacy", timeout=90.0, permute_seed=None):
        calls.append({"seed": seed, "permute_seed": permute_seed})
        which = "permute" if permute_seed is not None else "resplit"
        bucket = permute_results if which == "permute" else resplit_results
        i = min(per_bucket[which], len(bucket) - 1)
        per_bucket[which] += 1
        r = dict(bucket[i] if bucket else {})
        return r
    monkey.setattr(rcs, "gate1_run", fake)
    return calls


def test_attacker_survived(monkeypatch):
    from astra_core.scientific_discovery.evolved_analysis import fresh_attacker as fa
    calls = _patch_gate1(monkeypatch,
                         resplit_results=[{"effect": 0.32, "pvalue": 1e-9},
                                          {"effect": 0.33, "pvalue": 5e-9},
                                          {"effect": 0.31, "pvalue": 2e-9}],
                         permute_results=[{"effect": 0.01, "pvalue": 0.6},
                                          {"effect": 0.02, "pvalue": 0.4}])
    with _Isolated():
        rep = fa.attack_claim(_SRC, "sdss_qso")
        kinds = [e.get("kind") for e in el.read_ledger()]
    assert rep["disposition"] == "survived", rep["detail"]
    # 3 re-splits + 2 permutation nulls, and permute seeds went through
    assert len(calls) == 5
    assert {c["permute_seed"] for c in calls} == {None, 777, 20461}
    assert "attack" in kinds


def test_attacker_killed_on_resplit_failure(monkeypatch):
    from astra_core.scientific_discovery.evolved_analysis import fresh_attacker as fa
    _patch_gate1(monkeypatch,
                 resplit_results=[{"effect": 0.3, "pvalue": 1e-9},
                                  {"effect": 0.02, "pvalue": 0.5},   # dies here
                                  {"effect": 0.3, "pvalue": 1e-9}],
                 permute_results=[{"effect": 0.0, "pvalue": 0.9}])
    with _Isolated():
        rep = fa.attack_claim(_SRC, "sdss_qso")
    assert rep["disposition"] == "killed"


def test_attacker_not_runnable_on_error(monkeypatch):
    from astra_core.scientific_discovery.evolved_analysis import fresh_attacker as fa
    _patch_gate1(monkeypatch,
                 resplit_results=[{"effect": 0.3, "pvalue": 1e-9, "error": "timeout"}],
                 permute_results=[{"effect": 0.0, "pvalue": 0.9}])
    with _Isolated():
        rep = fa.attack_claim(_SRC, "sdss_qso")
    assert rep["disposition"] == "not-runnable"


def test_attacker_suspect_when_effect_survives_permutation(monkeypatch):
    from astra_core.scientific_discovery.evolved_analysis import fresh_attacker as fa
    _patch_gate1(monkeypatch,
                 resplit_results=[{"effect": 0.3, "pvalue": 1e-9},
                                  {"effect": 0.31, "pvalue": 1e-9},
                                  {"effect": 0.3, "pvalue": 1e-9}],
                 permute_results=[{"effect": 0.35, "pvalue": 1e-8},  # survives null
                                  {"effect": 0.01, "pvalue": 0.5}])
    with _Isolated():
        rep = fa.attack_claim(_SRC, "sdss_qso")
    assert rep["disposition"] == "suspect"


def test_emit_hard_rule_killed_never_reaches_store(monkeypatch):
    """A both-gate survivor the attacker kills is NOT written to the store."""
    from astra_core.scientific_discovery.evolved_analysis import run_claim_search as rcs
    import types
    store = Path(tempfile.mkdtemp(prefix="emit_test_")) / "evolved.json"
    monkeypatch.setattr(rcs, "EVOLVED_STORE", store)

    def fake_attack(src, source, **kw):
        return {"disposition": "killed", "detail": "re-split seed 1337 failed"}
    import astra_core.scientific_discovery.evolved_analysis.fresh_attacker as fa
    monkeypatch.setattr(fa, "attack_claim", fake_attack)

    # no second-family endpoint in tests: the audit must be an honest
    # non-blocking "not-configured" (F1)
    import os
    env_backup = {k: os.environ.pop(k) for k in
                  ("ASTRA_JUDGE2_TOKEN", "ASTRA_JUDGE2_MODEL", "ASTRA_JUDGE2_BASE_URL")
                  if k in os.environ}
    try:
        verdict = _verdict("a novel claim that will die", status="novel")
        verdict["source"] = _SRC
        verdict["dataset"] = "sdss_qso"
        with _Isolated():
            rcs._emit(verdict)
            assert not store.exists(), "killed finding reached the store!"
        # F3(a): the verdict itself records the promotion outcome
        assert verdict["emitted"] is False
        assert verdict["emit_reason"] == "attacker-killed"

        # ...and a survivor IS written, with the attack report attached
        def good_attack(src, source, **kw):
            return {"disposition": "survived", "detail": "all re-splits reproduce"}
        monkeypatch.setattr(fa, "attack_claim", good_attack)
        with _Isolated():
            rcs._emit(verdict)
        data = json.loads(store.read_text())
        assert data and data[0]["verification"]["fresh_attacker"]["disposition"] == "survived"
        assert data[0]["verification"]["second_judge"]["status"] == "not-configured"
        assert data[0]["verification"]["second_judge"]["block"] is False
    finally:
        os.environ.update(env_backup)


# --------------------------------------------------------------------------- #
# worker permutation null                                                      #
# --------------------------------------------------------------------------- #

def test_permute_splits_preserves_marginals_destroys_associations():
    import numpy as np
    import pandas as pd
    from astra_core.scientific_discovery.evolved_analysis import claim_eval_worker as w
    rng = np.random.default_rng(3)
    n = 400
    x = rng.normal(size=n)
    y = 0.8 * x + rng.normal(scale=0.2, size=n)     # strongly associated
    splits = {"train": pd.DataFrame({"x": x, "y": y})}
    w._permute_splits(splits, 777)
    df = splits["train"]
    # marginals preserved (same multiset per column)
    assert np.allclose(sorted(df["x"].to_numpy()), sorted(x))
    assert np.allclose(sorted(df["y"].to_numpy()), sorted(y))
    # association destroyed
    assert abs(np.corrcoef(df["x"], df["y"])[0, 1]) < 0.15


# --------------------------------------------------------------------------- #
# calibration lens                                                             #
# --------------------------------------------------------------------------- #

class _FakePred:
    """Minimal falsifiable-prediction stand-in."""
    id = "fake_pred"
    system_class = "fake_system"
    model = "FakeModel"
    quantity = "fake_quantity"
    units = "arcsec"
    anomaly_k_sigma = 3.0
    min_absolute_effect = 0.01
    systematics = []

    def fetch(self, system_id):
        return {}

    def predict(self, inputs):
        return 1.0, 0.01

    def observe(self, system_id):
        return 3.0, 0.01          # 141 sigma off -> DISAGREE


def test_lens_recompute_writes_plain_notes_and_ledger(monkeypatch):
    from astra_core.scientific_discovery import falsification as fals_pkg
    import astra_core.scientific_discovery.falsification.predictions as preds
    class _Reg:
        def all(self):
            return [_FakePred()]
    monkeypatch.setattr(preds, "seed_registry", lambda: _Reg())
    monkeypatch.setattr(preds, "SEED_SYSTEMS", {"fake_system": ["fake_sys"]})
    with _Isolated():
        notes = cl.recompute()
        assert len(notes) == 1
        assert notes[0]["status"] == "disagree"
        assert "-> DISAGREE" in notes[0]["note"] and "-> AGREE" not in notes[0]["note"]
        assert "FakeModel" in notes[0]["note"] and "fake_quantity" in notes[0]["note"]
        assert cl.NOTES.exists()
        cal = [e for e in el.read_ledger() if e.get("kind") == "calibration"]
        assert cal and cal[0]["disposition"] == "disagree"


def test_lens_notes_head_dataset_matched_first():
    with _Isolated():
        cl.NOTES.write_text(json.dumps({"notes": [
            {"ts": "2026-08-29", "dataset": "other_ds", "status": "agree",
             "note": "other note"},
            {"ts": "2026-08-29", "dataset": "sdss_qso", "status": "disagree",
             "note": "qso note"},
        ]}))
        head = cl.notes_head("sdss_qso", 2)
        assert head and head[0].startswith("(disagree) qso note")


def test_lens_counts_verdict_changes_after_notes():
    verdicts = [
        _verdict("flip claim", ds="sdss_qso", status="known", ts="2026-08-10T00:00:00"),
        _verdict("flip claim", ds="sdss_qso", status="novel", ts="2026-08-28T00:00:00"),
        _verdict("no-note flip", ds="wise_midir", status="known", ts="2026-08-10T00:00:00"),
        _verdict("no-note flip", ds="wise_midir", status="novel", ts="2026-08-28T00:00:00"),
    ]
    with _Isolated(verdict_lines=verdicts):
        cl.NOTES.write_text(json.dumps({"notes": [
            {"ts": "2026-08-20T00:00:00", "dataset": "sdss_qso", "status": "disagree",
             "note": "qso note"}]}))
        out = cl.verdicts_changed_by_notes()
        assert out["verdicts_changed_by_note"] == 1, out
        assert out["details"][0]["claim"] == "flip claim"


def test_task_system_delivers_calibration_notes(monkeypatch):
    from astra_core.scientific_discovery.evolved_analysis import data_lake as dl
    with _Isolated():
        cl.NOTES.write_text(json.dumps({"notes": [
            {"ts": "2026-08-29", "dataset": "sdss_qso", "status": "disagree",
             "note": "FakeModel disagrees by 141 sigma"}]}))
        monkeypatch.setattr(dl, "correlation_seeds", lambda name: [])
        monkeypatch.setattr(dl, "explored_themes", lambda name, n=6: [])
        monkeypatch.setattr(dl, "unsolved_register_head", lambda name, n=5: [])
        ts = dl.task_system_for("sdss_qso")
        assert ts and "CALIBRATION NOTES" in ts and "141 sigma" in ts


# --------------------------------------------------------------------------- #
# novelty_gate live-source check                                               #
# --------------------------------------------------------------------------- #

def _patch_ng(monkeypatch, tmp, papers_result):
    from astra_core.scientific_discovery.evolved_analysis import novelty_gate as ng
    cache = tmp / "novelty_cache.json"
    monkeypatch.setattr(ng, "CACHE_PATH", cache)
    calls = {"n": 0}

    def fake_retrieve(query, use_s2=True, max_results=5):
        calls["n"] += 1
        return list(papers_result)
    monkeypatch.setattr(ng, "_retrieve_papers", fake_retrieve)
    return ng, cache, calls


def _paper(title="A known result"):
    class P:
        pass
    p = P()
    p.title = title
    p.summary = "summary"
    p.authors = "a"
    p.year = 2020
    p.url = "https://arxiv.org/x"
    p.source = "arxiv"
    return p


def test_live_check_downgrades_cached_known_without_papers(monkeypatch):
    import tempfile as tf
    from astra_core.scientific_discovery.evolved_analysis import novelty_gate as ng
    tmp = Path(tf.mkdtemp(prefix="ng_test_"))
    ng2, cache, calls = _patch_ng(monkeypatch, tmp, papers_result=[])
    with _Isolated():
        # seed the cache with a stale known-verdict (no live_checked_ts)
        cache.write_text(json.dumps(
            {ng2._cache_key("the claim"): {"novel": False, "status": "known",
                                           "n_retrieved": 5, "reasoning": "r"}}))
        res = ng2.check_novelty("the claim")
        assert res.status == "known-cache-only", res.status
        # the downgrade is transient: not cached
        cached = json.loads(cache.read_text())
        assert ng2._cache_key("the claim") in cached
        assert cached[ng2._cache_key("the claim")]["status"] == "known"
        assert calls["n"] == 1  # the live check was attempted


def test_live_check_confirms_cached_known_with_papers(monkeypatch):
    import tempfile as tf
    from astra_core.scientific_discovery.evolved_analysis import novelty_gate as ng
    tmp = Path(tf.mkdtemp(prefix="ng_test_"))
    ng2, cache, calls = _patch_ng(monkeypatch, tmp, papers_result=[_paper()])
    with _Isolated():
        cache.write_text(json.dumps(
            {ng2._cache_key("the claim"): {"novel": False, "status": "known",
                                           "n_retrieved": 5, "reasoning": "r"}}))
        res = ng2.check_novelty("the claim")
        assert res.status == "known"
        cached = json.loads(cache.read_text())[ng2._cache_key("the claim")]
        assert cached.get("live_checked_ts", 0) > 0
        assert cached.get("live_checked_n") == 1
        # within the TTL no re-retrieval happens
        res2 = ng2.check_novelty("the claim")
        assert res2.status == "known" and calls["n"] == 1


def test_known_cache_only_enters_register_stream():
    verdicts = [_verdict("open-again", status="known-cache-only")]
    with _Isolated(verdict_lines=verdicts):
        entries = el.build_register(write=False)
        streams = {e["stream"] for e in entries
                   if (e.get("context") or {}).get("claim") == "open-again"}
        assert streams == {"narrow-gate-failure"}, streams


# --------------------------------------------------------------------------- #
# F4 prior-art sweep at promotion (2026-09-08): a cached NOVEL verdict that     #
# authorizes a finding may not stand on memory alone either — the mirror of     #
# the cached-known live-source check above.                                    #
# --------------------------------------------------------------------------- #

def _patch_ng_fresh(monkeypatch, tmp):
    """_patch_ng plus the fresh-path dependencies stubbed: real dataclass
    Papers, a deterministic judge, and no MiniLM load / precheck file write."""
    import time as _t
    from astra_core.scientific_discovery.evolved_analysis import novelty_gate as ng
    from astra_core.scientific_discovery.evolved_analysis import novelty_precheck as pc
    papers = [ng.Paper("arxiv", "An unrelated measurement paper", "abstract text",
                       "1234.5678", "2021")]
    ng2, cache, calls = _patch_ng(monkeypatch, tmp, papers_result=papers)
    monkeypatch.setattr(pc, "precheck_features", lambda c, p: {})
    monkeypatch.setattr(pc, "should_auto_known", lambda f: False)
    monkeypatch.setattr(pc, "log_precheck", lambda *a, **kw: None)
    judge_calls = {"n": 0}

    def fake_judge(claim, papers):
        judge_calls["n"] += 1
        return False, None, "novel", "re-judged novel on live retrieval", 0.75
    monkeypatch.setattr(ng2, "_judge_known", fake_judge)
    return ng2, cache, calls, judge_calls, _t


def test_stale_cached_novel_is_reverified_live(monkeypatch):
    """A cached novel verdict older than LIVE_CHECK_TTL falls through to the
    fresh path: live retrieval + re-judge, revision bumped, prior verdict
    archived in history, live-check re-stamped."""
    import tempfile as tf
    tmp = Path(tf.mkdtemp(prefix="ng_test_"))
    ng2, cache, calls, judge_calls, _t = _patch_ng_fresh(monkeypatch, tmp)
    with _Isolated():
        key = ng2._cache_key("the claim")
        stale = _t.time() - 2 * ng2.LIVE_CHECK_TTL
        cache.write_text(json.dumps(
            {key: {"novel": True, "status": "novel", "n_retrieved": 5,
                   "reasoning": "r", "live_checked_ts": stale,
                   "revision": 0}}))
        res = ng2.check_novelty("the claim")
        assert res.status == "novel"
        assert res.from_cache is False, "stale cached novel must not be trusted"
        assert calls["n"] >= 1, "no live retrieval on the fall-through"
        assert judge_calls["n"] == 1, "the fresh path must re-judge"
        cached = json.loads(cache.read_text())[key]
        assert cached["live_checked_ts"] > stale
        assert cached.get("revision", 0) >= 1, "re-verification not recorded"
        assert cached.get("history"), "prior verdict not archived"
        assert "from_cache" not in res.to_dict(), "runtime flag leaked into cache schema"


def test_fresh_cached_novel_within_ttl_stands(monkeypatch):
    """Within the TTL the cached novel verdict stands — returned marked
    from_cache=True, zero retrieval, zero judge spend."""
    import tempfile as tf
    tmp = Path(tf.mkdtemp(prefix="ng_test_"))
    ng2, cache, calls, judge_calls, _t = _patch_ng_fresh(monkeypatch, tmp)
    with _Isolated():
        key = ng2._cache_key("the claim")
        cache.write_text(json.dumps(
            {key: {"novel": True, "status": "novel", "n_retrieved": 5,
                   "reasoning": "r",
                   "live_checked_ts": _t.time() - 60}}))
        res = ng2.check_novelty("the claim")
        assert res.status == "novel" and res.novel is True
        assert res.from_cache is True
        assert calls["n"] == 0 and judge_calls["n"] == 0


# --------------------------------------------------------------------------- #
# review surface                                                               #
# --------------------------------------------------------------------------- #

def test_review_label_escalated_with_survived_attack():
    from astra_core.scientific_discovery.evolved_analysis import discovery_review as dr
    v = {"gate": {"gate1_real_data": "pass", "gate2_novelty": "novel",
                  "triviality": "pass", "consistency": "pass", "holdout": "pass"},
         "fresh_attacker": {"disposition": "survived", "detail": "ok"}}
    assert dr._rule_label(v) == "escalated"
    v2 = dict(v)
    v2["fresh_attacker"] = {"disposition": "killed", "detail": "x"}
    assert dr._rule_label(v2) == "independently-reviewed"


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


if __name__ == "__main__":
    import inspect
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        kwargs = {}
        if "monkeypatch" in inspect.signature(fn).parameters:
            kwargs["monkeypatch"] = _SimpleMonkey()
        try:
            fn(**kwargs)
        except AssertionError as ex:
            failed += 1
            print(f"FAIL {fn.__name__}: {ex}")
        except Exception as ex:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(ex).__name__}: {ex}")
        else:
            print(f"PASS {fn.__name__}")
        finally:
            if kwargs:
                kwargs["monkeypatch"].undo()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
