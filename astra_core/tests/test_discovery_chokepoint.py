"""Regression tests for the discovery-store trust boundary and the anti-fiction
invariant.

These exist because ASTRA's idle-time loop historically wrote fictional
discoveries (hardcoded STAN strings, template queries, a hardcoded 0.6
confidence) into the genuine store — a prime-directive violation. The fix is
structural: a single write chokepoint that rejects any record lacking a machine
``verification`` block, plus a disabled fiction-generation path. These tests
pin that invariant so it cannot silently regress.

Run: python3 astra_core/tests/test_discovery_chokepoint.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.discovery_store import (  # noqa: E402
    has_machine_verification, append_verified, dedup_verified,
    purge_file, load_records, save_bucket,
)


def _tmp_store(records):
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    save_bucket(Path(path), records)
    return Path(path)


def test_fiction_has_no_verification():
    """The actual fictional records that polluted the store must be rejected."""
    fakes = [
        {"title": "STAN system initialized. For full query processing, use "
                  "EnhancedUnifiedSTANSystem.",
         "abstract": "STAN system initialized.", "validation": {"quality": "INCREMENTAL"}},
        {"title": "Astronomical Discovery", "abstract": "CMB is relic radiation...",
         "validation": {"quality": "INCREMENTAL", "confidence": 0.6}},
        {"title": "Interstellar Medium Analysis", "validation": {"quality": "TEXTBOOK"}},
    ]
    for f in fakes:
        assert has_machine_verification(f) is False, f"fake not rejected: {f['title'][:40]}"


def test_real_record_has_verification():
    real = {"title": "Evolved photoz pipeline", "verification": {
        "program_hash": "abc123", "metric_name": "sigma_nmad",
        "held_out_test_value": 0.0199}}
    assert has_machine_verification(real) is True


def test_append_rejects_fiction_accepts_real():
    path = _tmp_store([])
    # fiction rejected
    assert append_verified(path, {"title": "fake", "validation": {}}) is False
    assert len(load_records(path)) == 0
    # real accepted
    real = {"title": "real", "verification": {"program_hash": "h1",
            "metric_name": "sigma_nmad"}}
    assert append_verified(path, real) is True
    # duplicate rejected (idempotent)
    assert append_verified(path, dict(real)) is False
    assert len(load_records(path)) == 1
    os.unlink(path)


def test_dedup_collapses_duplicates():
    recs = [
        {"verification": {"program_hash": "h1"}, "title": "a"},
        {"verification": {"program_hash": "h1"}, "title": "a-dup"},
        {"verification": {"program_hash": "h2"}, "title": "b"},
    ]
    kept, dropped = dedup_verified(recs)
    assert len(kept) == 2 and dropped == 1


def test_dedup_collapses_same_claim_different_hash():
    """Regenerated duplicates — different program_hash, SAME claim + effect — collapse."""
    def rec(ph):
        claim = ("Among galaxies with high concentration the residual of r-i after "
                 "removing the redshift trend correlates with mass")
        return {"abstract": claim,
                "verification": {"program_hash": ph, "effect": 0.352, "pvalue": 4e-13,
                                 "claim": claim,
                                 "gate": {"gate1_real_data": "pass",
                                          "gate2_novelty": "novel"}}}
    kept, dropped = dedup_verified([rec("h1"), rec("h2"), rec("h3")])
    assert len(kept) == 1 and dropped == 2


def test_purge_removes_fiction_and_dups():
    path = _tmp_store([
        {"title": "real", "verification": {"program_hash": "h1"}},
        {"title": "real-dup", "verification": {"program_hash": "h1"}},
        {"title": "fake1", "validation": {"quality": "INCREMENTAL"}},
        {"title": "fake2", "validation": {"quality": "TEXTBOOK"}},
    ])
    counts = purge_file(path, dry_run=False)
    assert counts["before"] == 4
    assert counts["dropped_unverified"] == 2
    assert counts["dropped_dup"] == 1
    assert counts["after"] == 1
    assert all(has_machine_verification(r) for r in load_records(path))
    os.unlink(path)


def test_v2_fiction_path_disabled():
    """The legacy FixedGenuineDiscoverySystem must not emit discoveries via the
    STAN answer() path, and its save must reject unverified records."""
    from astra_core.autonomous_startup_discovery_v2 import (
        FixedGenuineDiscoverySystem, DiscoveryConfig)
    store = _tmp_store([{"title": "real", "verification": {"program_hash": "h1",
                          "metric_name": "sigma_nmad"}}])
    sys_obj = FixedGenuineDiscoverySystem(
        config=DiscoveryConfig(discoverystore_path=str(store)))
    # the fiction generator must return None
    assert sys_obj._call_astra_with_timeout("any template query") is None
    # inject fiction into the in-memory store; save must NOT persist it
    sys_obj.genuine_discoveries.append({"title": "STAN system initialized.",
                                        "validation": {"quality": "GENCREMENTAL"}})
    sys_obj._save_discovery_store()
    recs = load_records(store)
    assert len(recs) == 1, f"expected 1 record after save, got {len(recs)}"
    assert all(has_machine_verification(r) for r in recs), "fiction reached disk"
    os.unlink(store)


def test_supervisor_no_fiction_to_disk():
    """The supervisor's ingest+persist must never write unverified records."""
    from astra_core.autonomous_discovery_supervisor import AutonomousDiscoverySupervisor
    store = _tmp_store([{"title": "real", "verification": {"program_hash": "h1",
                          "metric_name": "sigma_nmad"}}])
    sup = AutonomousDiscoverySupervisor(cycle_seconds=60)
    sup.discoverystore_path = store
    sup.genuine_discoveries = []
    sup._hydrate()
    sup.genuine_discoveries.append({"title": "injected fiction",
                                    "validation": {"quality": "GENUINE"}})
    sup._persist()
    recs = load_records(store)
    assert all(has_machine_verification(r) for r in recs), "supervisor wrote fiction"
    os.unlink(store)


def test_user_active_heartbeat():
    from astra_core.autonomous_discovery_supervisor import (
        is_user_active, touch_user_active, USER_ACTIVE_FILE)
    if USER_ACTIVE_FILE.exists():
        USER_ACTIVE_FILE.unlink()
    try:
        assert is_user_active() is False
        touch_user_active()
        assert is_user_active() is True
        assert is_user_active(window_seconds=0) is False  # zero window -> inactive
    finally:
        if USER_ACTIVE_FILE.exists():
            USER_ACTIVE_FILE.unlink()


def test_claim_parse_handles_apostrophes():
    """CLAIM strings often contain apostrophes ("galaxy's"); the parser must not
    truncate at them (truncation fed Gate 2 an incomplete fragment → false novel)."""
    from astra_core.scientific_discovery.evolved_analysis.claim_task import (
        parse_claim, NAIVE_CLAIM_SEED)
    claim = parse_claim(NAIVE_CLAIM_SEED)
    assert claim and "galaxy" in claim and "redshift" in claim, \
        f"claim truncated: {claim!r}"
    # the apostrophe-bearing claim must include content PAST the apostrophe
    assert "g-r" in claim or "color" in claim, f"lost content after apostrophe: {claim!r}"


def test_gate1_significance_logic():
    """Gate 1 must pass a strong effect and reject a weak/no-effect result."""
    from astra_core.scientific_discovery.evolved_analysis.claim_task import (
        gate1_significant)
    ok, _ = gate1_significant({"effect": 0.55, "pvalue": 1e-12})
    assert ok is True
    ok, _ = gate1_significant({"effect": 0.02, "pvalue": 0.4})
    assert ok is False
    ok, _ = gate1_significant({"effect": 0.9, "pvalue": 0.01})  # effect ok, p too big
    assert ok is False
    ok, _ = gate1_significant({"error": "blocked:open"})        # blocked code
    assert ok is False


def test_two_gate_emit_only_on_both_pass():
    """_emit must be a no-op unless both gates pass (anti-fiction + anti-textbook)."""
    import inspect
    from astra_core.scientific_discovery.evolved_analysis import run_claim_search
    src = inspect.getsource(run_claim_search._emit)
    assert "both_pass" in src, "_emit must guard on both_pass"


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(_run())
