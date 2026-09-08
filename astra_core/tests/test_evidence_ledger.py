"""Tests for the Phase-0 evidence ledger (Eureka plan, 2026-08-29).

Pins the four jobs of the one record:
  * append-only ledger core — one JSONL line per flagged observation, lifetime
    count stamped on entries that carry a p-value;
  * lifetime trial count — verdict-log trials counted IN PLACE (never copied),
    ledger trials added on top, no double counting;
  * lifetime significance correction and the last-hundred recompute;
  * the register of unsolved problems, enumerated from the three discard
    streams (quarantined near-misses, narrow gate-2 failures where the
    statistics passed but the literature gate could not judge, unexplained
    anomalies) — enumerated, never remembered, and removable only by an
    explicit explained/refuted ledger entry;
  * formal abstention with a mandatory escalation template;
  * rule-based confidence labels (never freehand);
  * the conduct log.

All tests run against a tempdir: the real ~/.astra_persistent stores are never
touched.

Run: python3 astra_core/tests/test_evidence_ledger.py
"""
import json
import math
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import evidence_ledger as el  # noqa: E402


# --------------------------------------------------------------------------- #
# Isolation: every path the module touches, redirected to a tempdir           #
# --------------------------------------------------------------------------- #

class _Isolated:
    """Redirect all store paths to a fresh tempdir for the duration."""

    def __init__(self, verdict_lines=None, quarantine=None, ledger_lines=None):
        self.tmp = Path(tempfile.mkdtemp(prefix="evidence_ledger_test_"))
        self.paths = {
            "EVOLVED_PROGRAMS": self.tmp,
            "LEDGER": self.tmp / "evidence_ledger.jsonl",
            "VERDICT_LOG": self.tmp / "claim_verdicts.jsonl",
            "CONDUCT_LOG": self.tmp / "conduct_log.jsonl",
            "QUARANTINE": self.tmp / "quarantined_discoveries.json",
            "REGISTER": self.tmp / "unsolved_register.json",
            "CORRECTION_REPORT": self.tmp / "lifetime_correction_report.json",
        }
        self.orig = {k: getattr(el, k) for k in self.paths}
        if verdict_lines is not None:
            self.paths["VERDICT_LOG"].write_text(
                "".join(json.dumps(v) + "\n" for v in verdict_lines))
        if quarantine is not None:
            self.paths["QUARANTINE"].write_text(json.dumps(quarantine))
        if ledger_lines is not None:
            self.paths["LEDGER"].write_text(
                "".join(json.dumps(v) + "\n" for v in ledger_lines))

    def __enter__(self):
        for k, v in self.paths.items():
            setattr(el, k, v)
        return self

    def __exit__(self, *exc):
        for k, v in self.orig.items():
            setattr(el, k, v)
        return False


def _verdict(claim, p=1e-9, gate1_pass=True, g2_status=None, g2_pass=None,
             triviality=True, consistency=True, holdout=True, dataset="sdss"):
    return {
        "ts": "2026-08-29T00:00:00",
        "label": "seed",
        "claim": claim,
        "program_hash": "h" + claim[:6],
        "both_pass": g2_status == "novel" and gate1_pass,
        "dataset": dataset,
        "gate1": {"pass": gate1_pass, "effect": 0.5, "pvalue": p if gate1_pass else 1.0,
                  "reason": "gate1-pass"},
        "triviality": triviality,
        "consistency": consistency,
        "holdout": holdout,
        "gate2": {"status": g2_status, "pass": g2_pass, "n_retrieved": 5, "reasoning": "r"},
    }


QUARANTINE_FIXTURE = [
    {"gate_failed": "no_source", "reason": "no persisted program_source",
     "quarantined_at": "2026-07-13T21:31:49", "program_hash": "abc",
     "original_record": {"title": "In-sample claim", "abstract": "full context kept"}},
    {"gate_failed": "holdout", "reason": "holdout:reject effect=0.38",
     "quarantined_at": "2026-07-13T21:32:04", "program_hash": "def",
     "original_record": {"title": "Holdout near-miss", "abstract": "full context kept"}},
]


# --------------------------------------------------------------------------- #
# Ledger core                                                                  #
# --------------------------------------------------------------------------- #

def test_append_writes_one_line_with_lifetime_stamp():
    with _Isolated(verdict_lines=[_verdict("c1")]):
        e = el.append("anomaly", "unexplained", dataset="sdss", statistic="spearman_rho",
                      value=0.42, pvalue=0.01, claim="c1", detail="odd residual")
        lines = el.LEDGER.read_text().splitlines()
        assert len(lines) == 1
        stored = json.loads(lines[0])
        assert stored["kind"] == "anomaly" and stored["disposition"] == "unexplained"
        # verdict log has 1 trial; a non-trial entry stamps the count as-is
        assert stored["n_trials_lifetime"] == 1
        assert math.isclose(stored["pvalue_lifetime"], 0.01)
        assert stored["code_version"] == el.CODE_VERSION


def test_append_rejects_unknown_kind():
    with _Isolated():
        try:
            el.append("telepathy", "x")
        except ValueError:
            pass
        else:
            raise AssertionError("unknown kind must raise")
        assert not el.LEDGER.exists()


def test_append_trial_counts_itself_in_the_stamp():
    with _Isolated(verdict_lines=[_verdict("c1"), _verdict("c2")]):
        e = el.append("trial", "flagged", pvalue=0.05)
        # 2 verdict trials + this trial itself = 3
        assert e["n_trials_lifetime"] == 3
        assert math.isclose(e["pvalue_lifetime"], 0.15)


def test_read_ledger_skips_malformed_lines():
    with _Isolated():
        el.LEDGER.write_text('{"kind": "note", "disposition": "ok"}\nnot json\n\n')
        entries = list(el.read_ledger())
        assert len(entries) == 1


# --------------------------------------------------------------------------- #
# Lifetime trial count + significance correction                               #
# --------------------------------------------------------------------------- #

def test_lifetime_trials_no_double_counting():
    verdicts = [_verdict(f"claim-{i}") for i in range(7)]
    with _Isolated(verdict_lines=verdicts,
                   ledger_lines=[{"kind": "trial", "disposition": "flagged"},
                                 {"kind": "anomaly", "disposition": "unexplained"},
                                 {"kind": "trial", "disposition": "gate1-failed"},
                                 {"kind": "note", "disposition": "ctx"}]):
        # 7 verdict + 2 ledger trials + 1 flagged anomaly (an anomalous look is
        # still a look); the note is not a trial and is not counted
        assert el.lifetime_trials() == 10


def test_distinct_claims_dedupes_verdict_log():
    verdicts = [_verdict("same claim"), _verdict("same claim"), _verdict("other claim")]
    with _Isolated(verdict_lines=verdicts,
                   ledger_lines=[{"kind": "trial", "claim": "same claim"}]):
        assert el.distinct_claims() == 2


def test_correct_pvalue_bounded_at_one():
    with _Isolated(verdict_lines=[_verdict("c") for _ in range(200)]):
        assert el.correct_pvalue(0.01) == 1.0          # 0.01 * 200 -> capped
        assert math.isclose(el.correct_pvalue(1e-9), 2.0e-7, rel_tol=1e-9)  # 1e-9 * 200
        assert el.correct_pvalue(None) is None


def test_recompute_only_examines_reported_significances():
    verdicts = [
        _verdict("promoted-1", p=1e-12, g2_status="novel", g2_pass=True),   # reported
        _verdict("promoted-2", p=3.5e-8, g2_status="novel", g2_pass=True),  # reported
        _verdict("known-claim", p=1e-20, g2_status="known", g2_pass=False), # not reported
        _verdict("failed-claim", p=1e-20, gate1_pass=False, g2_status=None),# not reported
    ]
    with _Isolated(verdict_lines=verdicts):
        r = el.recompute_reported()
        assert r["n_reported_significances_examined"] == 2
        assert r["n_lifetime_trials"] == 4
        by_claim = {row["claim"]: row for row in r["rows"]}
        # 3.5e-8 * 4 = 1.4e-7: value changed, still far below the bar
        assert math.isclose(by_claim["promoted-2"]["pvalue_lifetime"], 1.4e-7, rel_tol=1e-9)
        assert by_claim["promoted-2"]["still_below_1e-3_bar"] is True
        assert "known-claim" not in by_claim and "failed-claim" not in by_claim
        assert el.CORRECTION_REPORT.exists()  # published


# --------------------------------------------------------------------------- #
# Register of unsolved problems                                                #
# --------------------------------------------------------------------------- #

def test_register_three_streams():
    verdicts = [
        # narrow gate-2 failure: all statistics passed, machine could not judge
        _verdict("narrow-a", g2_status="retrieval-failed", g2_pass=None),
        _verdict("narrow-b", g2_status="judge-failed", g2_pass=None),
        # judge RAN and found it known -> resolved, not unsolved
        _verdict("known-one", g2_status="known", g2_pass=False),
        # statistics failed -> not a near-miss
        _verdict("weak-one", gate1_pass=False, g2_status=None),
        # triviality failed -> not a near-miss
        _verdict("trivial-one", triviality=False, g2_status="retrieval-failed"),
    ]
    anomalies = [
        {"kind": "anomaly", "disposition": "unexplained", "claim": "odd-residual",
         "dataset": "sdss", "detail": "residual map shows a band"},
        {"kind": "visual", "disposition": "flagged", "claim": "phase-space-tail",
         "detail": "what is odd here"},
    ]
    with _Isolated(verdict_lines=verdicts, quarantine=QUARANTINE_FIXTURE,
                   ledger_lines=anomalies):
        entries = el.build_register()
        streams = {}
        for e in entries:
            streams.setdefault(e["stream"], []).append(e)
        assert len(streams["quarantined-near-miss"]) == 2
        assert {e["context"]["claim"] for e in streams["narrow-gate-failure"]} == {"narrow-a", "narrow-b"}
        assert {e["context"]["claim"] for e in streams["unexplained-anomaly"]} == {"odd-residual", "phase-space-tail"}
        # full context attached
        q = streams["quarantined-near-miss"][0]
        assert q["context"]["title"] == "In-sample claim"
        assert el.REGISTER.exists()


def test_register_resolution_removes_entry():
    verdicts = [_verdict("narrow-a", g2_status="judge-failed", g2_pass=None)]
    with _Isolated(verdict_lines=verdicts):
        assert any((e.get("context") or {}).get("claim") == "narrow-a" for e in el.build_register())
        el.append("register", "refuted", claim="narrow-a", detail="retracted: band identity")
        remaining = [e for e in el.build_register()
                     if (e.get("context") or {}).get("claim") == "narrow-a"]
        assert remaining == []


def test_register_dedupes_retried_claims():
    verdicts = [_verdict("same-narrow", g2_status="judge-failed") for _ in range(5)]
    with _Isolated(verdict_lines=verdicts):
        entries = el.build_register()
        narrow = [e for e in entries if e["stream"] == "narrow-gate-failure"]
        assert len(narrow) == 1


# --------------------------------------------------------------------------- #
# F3(b) (2026-09-08): the blocked-at-promotion stream (attacks first)          #
# --------------------------------------------------------------------------- #

def test_register_blocked_at_promotion_stream():
    """kind=attack ledger lines with killing dispositions become register
    entries; survived/suspect markings do not; and the attack entry wins both
    the claim-key dedup and the head position over a narrow-gate-failure
    reading of the same claim."""
    attacks = [
        {"kind": "attack", "disposition": "killed", "claim": "killed-one",
         "dataset": "sdss", "detail": "re-split seed 1337 failed"},
        {"kind": "attack", "disposition": "not-runnable", "claim": "broken-one",
         "dataset": "sdss", "detail": "worker timeout"},
        {"kind": "attack", "disposition": "second-judge-known",
         "claim": "entailed-one", "dataset": "sdss",
         "detail": "second-family judge marked known-entailed"},
        {"kind": "attack", "disposition": "survived", "claim": "fine-one",
         "dataset": "sdss", "detail": "all re-splits reproduce"},
        {"kind": "attack", "disposition": "suspect", "claim": "sus-one",
         "dataset": "sdss", "detail": "effect survives permutation"},
    ]
    # killed-one is ALSO readable as a narrow-gate-failure from the verdict
    # log: the attack stream's entry must win (attacks concatenated first)
    verdicts = [_verdict("killed-one", g2_status="judge-failed", g2_pass=None)]
    with _Isolated(verdict_lines=verdicts, ledger_lines=attacks):
        entries = el.build_register()
        blocked = [e for e in entries if e["stream"] == "blocked-at-promotion"]
        assert {e["context"]["claim"] for e in blocked} == {
            "killed-one", "broken-one", "entailed-one"}
        # survived/suspect are markings, not blocks: nothing about them enters
        assert not any((e.get("context") or {}).get("claim")
                       in ("fine-one", "sus-one") for e in entries)
        # killed-one appears exactly once, as the attack entry, and LEADS
        killed = [e for e in entries
                  if (e.get("context") or {}).get("claim") == "killed-one"]
        assert len(killed) == 1
        assert killed[0]["stream"] == "blocked-at-promotion"
        assert killed[0]["gate_failed"] == "attack:killed"
        assert entries[0]["stream"] == "blocked-at-promotion"


def test_register_attack_resolution_removes_entry():
    """A blocked-at-promotion entry leaves by explanation like any other —
    recurrence prevention, not punishment."""
    attacks = [{"kind": "attack", "disposition": "killed",
                "claim": "later-explained", "dataset": "sdss", "detail": "d"}]
    with _Isolated(ledger_lines=attacks):
        assert any((e.get("context") or {}).get("claim") == "later-explained"
                   for e in el.build_register())
        el.append("register", "explained", claim="later-explained",
                  detail="the re-split failure was a NaN in one band")
        assert not any((e.get("context") or {}).get("claim") == "later-explained"
                       for e in el.build_register())


def test_gate2_error_enters_narrow_stream():
    """A gate-2 that raised outright used to vanish without a register trace;
    since 2026-09-08 it lands in the narrow-gate-failure stream."""
    verdicts = [_verdict("gate2-crash", g2_status="gate2-error", g2_pass=None)]
    with _Isolated(verdict_lines=verdicts):
        entries = el.build_register()
        streams = {e["stream"] for e in entries
                   if (e.get("context") or {}).get("claim") == "gate2-crash"}
        assert streams == {"narrow-gate-failure"}, streams


def test_recompute_skips_promotion_blocked_rows():
    """A both-gate 'novel' row that was blocked at the chokepoint (emitted
    False) is NOT a reported significance — the lifetime correction must not
    count claims nobody heard. Historical null-field rows still count."""
    promoted = _verdict("promoted-1", p=1e-12, g2_status="novel", g2_pass=True)
    blocked = dict(_verdict("blocked-1", p=1e-12, g2_status="novel", g2_pass=True),
                   emitted=False, emit_reason="second-judge-known")
    legacy = _verdict("legacy-1", p=1e-12, g2_status="novel", g2_pass=True)
    with _Isolated(verdict_lines=[promoted, blocked, legacy]):
        r = el.recompute_reported()
        by_claim = {row["claim"]: row for row in r["rows"]}
        assert set(by_claim) == {"promoted-1", "legacy-1"}, set(by_claim)


# --------------------------------------------------------------------------- #
# Abstention + rule-based labels                                               #
# --------------------------------------------------------------------------- #

def test_abstention_requires_full_template():
    with _Isolated():
        try:
            el.abstain("is this real?", {"abstained_because": "no data"})
        except ValueError as ex:
            assert "template incomplete" in str(ex) or "missing" in str(ex)
        else:
            raise AssertionError("partial template must raise")
        full = {k: "x" for k in el.ESCALATION_TEMPLATE}
        e = el.abstain("is this real?", full, dataset="sdss", claim="c")
        stored = json.loads(el.LEDGER.read_text().splitlines()[0])
        assert stored["kind"] == "abstention"
        assert stored["disposition"] == el.ABSTAIN == "not-enough-evidence"
        assert stored["escalation"]["who_can_obtain_it"] == "x"


def test_confidence_label_is_rule_based():
    assert el.confidence_label({"gate1"}) == "routine"
    assert el.confidence_label({"gate1", "triviality"}) == "routine"  # incomplete family
    assert el.confidence_label({"gate1", "triviality", "consistency", "holdout"}) == "flagged"
    assert el.confidence_label({"gate1", "triviality", "consistency", "holdout", "gate2"}) == "independently-reviewed"
    everything = {"gate1", "triviality", "consistency", "holdout", "gate2", "fresh-attacker"}
    assert el.confidence_label(everything) == "escalated"
    assert el.confidence_label(set()) == "unverified"
    assert el.confidence_label({"gate2"}) == "unverified"  # no gate1 -> nothing holds


def test_verdict_checks_extracts_passed():
    v = _verdict("c", g2_status="novel", g2_pass=True)
    assert el.verdict_checks(v) == {"gate1", "triviality", "consistency", "holdout", "gate2"}
    v2 = _verdict("c", g2_status="known", g2_pass=False)
    assert "gate2" not in el.verdict_checks(v2)


# --------------------------------------------------------------------------- #
# Conduct log                                                                  #
# --------------------------------------------------------------------------- #

def test_conduct_log_validates_rule_and_mirrors_to_ledger():
    with _Isolated():
        e = el.conduct("weirdest-reading-first",
                       "stated the band-identity reading before the lensing one")
        conduct_lines = el.CONDUCT_LOG.read_text().splitlines()
        assert len(conduct_lines) == 1
        assert json.loads(conduct_lines[0])["rule"] == "weirdest-reading-first"
        # mirrored into the ledger so conduct is queryable with everything else
        ledger = json.loads(el.LEDGER.read_text().splitlines()[0])
        assert ledger["kind"] == "conduct" and ledger["disposition"] == "weirdest-reading-first"
        try:
            el.conduct("be-excellent-to-each-other", "x")
        except ValueError:
            pass
        else:
            raise AssertionError("unknown conduct rule must raise")


def test_conduct_read_roundtrip():
    with _Isolated():
        el.conduct("one-problem-held-open", "W2-excess residual carried open")
        entries = list(el.read_conduct())
        assert len(entries) == 1 and entries[0]["rule"] == "one-problem-held-open"


# --------------------------------------------------------------------------- #
# Phase 1: register injection into the proposer session (data_lake)           #
# --------------------------------------------------------------------------- #

def test_register_head_orders_matched_dataset_first_then_claims():
    """Dataset-matched entries lead; then scientific claims (anomalies, stalled
    claims) from any dataset — arranged collisions — before quarantine reasons."""
    from astra_core.scientific_discovery.evolved_analysis import data_lake as dl
    verdicts = [
        _verdict("matched-stalled-claim", g2_status="judge-failed", dataset="sdss_stars"),
    ]
    ledger_lines = [
        {"kind": "anomaly", "disposition": "unexplained", "claim": "cross-dataset anomaly",
         "dataset": "wise_midir", "detail": "unexplained residual"},
    ]
    with _Isolated(verdict_lines=verdicts, quarantine=QUARANTINE_FIXTURE,
                   ledger_lines=ledger_lines):
        head_stars = dl.unsolved_register_head("sdss_stars", 3)
        assert head_stars[0].startswith('"matched-stalled-claim"')
        # for another dataset the anomaly (a real problem) outranks quarantine
        # bookkeeping even though both are unmatched
        head_qso = dl.unsolved_register_head("sdss_qso", 3)
        assert head_qso[0].startswith('"cross-dataset anomaly"')


def test_task_system_injects_register_with_varied_framing():
    """The proposer session prompt carries the register head, and the framing
    varies across sessions so no single presentation ossifies."""
    from astra_core.scientific_discovery.evolved_analysis import data_lake as dl
    verdicts = [_verdict("stalled-claim-injection", g2_status="judge-failed",
                         dataset="sdss_qso")]
    openers = ("UNSOLVED PROBLEMS", "OPEN ANOMALIES", "LEFTOVERS")
    with _Isolated(verdict_lines=verdicts):
        seen = set()
        for _ in range(20):
            ts = dl.task_system_for("sdss_qso")
            if ts is None:
                raise AssertionError("task_system_for(sdss_qso) unexpectedly None")
            hit = [o for o in openers if o in ts]
            assert hit, "no register framing found in proposer prompt"
            assert "stalled-claim-injection" in ts
            seen.add(hit[0])
        assert len(seen) >= 2, "framing must vary across sessions"


def test_register_head_silent_when_ledger_fails():
    """A ledger failure must never break proposer prompt assembly."""
    from astra_core.scientific_discovery.evolved_analysis import data_lake as dl
    orig = el.build_register
    el.build_register = lambda write=False: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        assert dl.unsolved_register_head("sdss_qso") == []
    finally:
        el.build_register = orig


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as ex:
            failed += 1
            print(f"FAIL {fn.__name__}: {ex}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
