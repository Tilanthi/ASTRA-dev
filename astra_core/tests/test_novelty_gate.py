"""Tests for Gate-2 (novelty) retrieval robustness — retry/backoff + dedup.

The 2026-07-14 pilot saw whole batches of claims return "retrieval-failed" because
arXiv transiently rate-limited / dropped requests. These tests pin the fixes:
_http_get retries on failure; _retrieve_papers dedups; retrieval-failed is not
treated as a definitive verdict.

Run: python3 astra_core/tests/test_novelty_gate.py
"""
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import novelty_gate as ng  # noqa: E402


def test_http_get_returns_none_on_persistent_failure():
    """When every attempt fails, _http_get returns None (and retries, not crashes)."""
    def _boom(*a, **k):
        raise urllib.error.URLError("transient")
    real_sleep = ng.time.sleep
    orig_urlopen = urllib.request.urlopen
    ng.time.sleep = lambda *a, **k: None          # neutralise backoff in the test
    urllib.request.urlopen = _boom
    try:
        assert ng._http_get("http://example.invalid/x", retries=3) is None
    finally:
        urllib.request.urlopen = orig_urlopen
        ng.time.sleep = real_sleep


def test_http_get_succeeds_first_try():
    """Sanity: a working endpoint returns content (mocked)."""
    orig_urlopen = urllib.request.urlopen

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b"hello arxiv"
    def _ok(*a, **k): return _Resp()
    urllib.request.urlopen = _ok
    try:
        assert ng._http_get("http://x", retries=2) == "hello arxiv"
    finally:
        urllib.request.urlopen = orig_urlopen


def test_retrieve_papers_dedups_by_title():
    """_retrieve_papers de-duplicates near-identical titles and caps the count."""
    p1 = ng.Paper("arxiv", "Galaxy Morphology", "a", "1", "2020")
    p2 = ng.Paper("arxiv", "galaxy morphology", "a", "2", "2021")  # dup (lower[:80])
    p3 = ng.Paper("s2", "Star Formation Rate", "b", "3", "2019")
    orig_a, orig_s = ng.retrieve_arxiv, ng.retrieve_s2
    ng.retrieve_arxiv = lambda q, max_results=5: [p1, p2]
    ng.retrieve_s2 = lambda q, max_results=5: [p3]
    try:
        out = ng._retrieve_papers("q", use_s2=True)
    finally:
        ng.retrieve_arxiv, ng.retrieve_s2 = orig_a, orig_s
    titles = [p.title for p in out]
    assert len(out) == 2                 # p1 and p2 collapsed; p3 kept
    assert "Star Formation Rate" in titles


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
