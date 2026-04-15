# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tests for Phase 9.5 — Auto Paper Draft Generation.
"""
import sys
import os
import time

# Ensure the parent directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astra_live_backend.hypotheses import Hypothesis, Phase, TestResult
from astra_live_backend.paper_generator import PaperDraftGenerator, PaperDraft


def _make_hypothesis(
    hid="H099",
    name="Test Hypothesis",
    domain="Astrophysics",
    description="A test hypothesis for unit testing.",
    confidence=0.97,
    phase=Phase.VALIDATED,
    n_tests=4,
    data_points=5000,
):
    """Create a hypothesis with realistic test results."""
    h = Hypothesis(
        id=hid,
        name=name,
        domain=domain,
        description=description,
        confidence=confidence,
        phase=phase,
        data_points_used=data_points,
    )
    for i in range(n_tests):
        h.test_results.append({
            "test_name": ["chi_squared", "kolmogorov_smirnov", "bayesian_t_test", "pearson_correlation"][i % 4],
            "statistic": 15.3 + i * 2.1,
            "p_value": 0.001 * (i + 1),
            "passed": True,
            "timestamp": time.time(),
            "details": f"Test {i+1} result",
        })
    return h


def test_generate_abstract():
    """Test abstract generation produces non-empty text with key elements."""
    gen = PaperDraftGenerator()
    h = _make_hypothesis()
    abstract = gen.generate_abstract(h)

    assert len(abstract) > 100, f"Abstract too short: {len(abstract)} chars"
    assert h.name in abstract, "Hypothesis name should appear in abstract"
    assert "0.97" in abstract or "97%" in abstract, "Confidence should appear in abstract"
    assert "5,000" in abstract or "5000" in abstract, "Data points should appear"
    print(f"  ✓ Abstract generated: {len(abstract)} chars")


def test_generate_methods():
    """Test methods section includes statistical test descriptions."""
    gen = PaperDraftGenerator()
    h = _make_hypothesis()
    methods = gen.generate_methods(h)

    assert "chi_squared" in methods or "Chi" in methods, "Should mention chi-squared test"
    assert "Benjamini-Hochberg" in methods, "Should mention FDR correction"
    assert "Data Selection" in methods, "Should have data selection subsection"
    assert "Statistical Analysis" in methods, "Should have statistical analysis subsection"
    print(f"  ✓ Methods generated: {len(methods)} chars")


def test_generate_results():
    """Test results section includes table of test results."""
    gen = PaperDraftGenerator()
    h = _make_hypothesis()
    results = gen.generate_results(h)

    assert "| Test" in results, "Should contain results table header"
    assert "✓ Pass" in results, "Should show passing tests"
    assert "0.97" in results or "0.9700" in results, "Should show confidence value"
    assert "Bayesian" in results, "Should discuss Bayesian confidence"
    print(f"  ✓ Results generated: {len(results)} chars")


def test_generate_full_draft():
    """Test full draft generation produces all sections."""
    gen = PaperDraftGenerator()
    h = _make_hypothesis()
    draft = gen.generate_full_draft(h)

    assert isinstance(draft, PaperDraft)
    assert draft.hypothesis_id == "H099"
    assert draft.title, "Title should not be empty"
    assert draft.abstract, "Abstract should not be empty"
    assert draft.methods, "Methods should not be empty"
    assert draft.results, "Results should not be empty"
    assert draft.conclusion, "Conclusion should not be empty"
    assert draft.domain == "Astrophysics"
    assert draft.confidence == 0.97
    assert draft.version == 1

    # Test full_text concatenation
    full = draft.full_text()
    assert "# " in full, "Full text should have markdown headings"
    assert "Abstract" in full
    assert "Methods" in full
    assert "Results" in full
    assert "Conclusion" in full
    print(f"  ✓ Full draft generated: {len(full)} chars, title: {draft.title}")


def test_domain_templates():
    """Test that different domains produce different content."""
    gen = PaperDraftGenerator()

    domains = ["Astrophysics", "Cosmology", "Exoplanets", "Stellar Physics", "Economics"]
    abstracts = {}
    for domain in domains:
        h = _make_hypothesis(domain=domain, name=f"{domain} Test")
        abstract = gen.generate_abstract(h)
        abstracts[domain] = abstract

    # Verify domain-specific content
    assert "astronomical surveys" in abstracts["Astrophysics"], "Astrophysics should mention surveys"
    assert "cosmological" in abstracts["Cosmology"].lower(), "Cosmology should mention cosmological"
    assert "exoplanet" in abstracts["Exoplanets"].lower(), "Exoplanets should mention exoplanet"
    assert "stellar" in abstracts["Stellar Physics"].lower(), "Stellar Physics should mention stellar"
    print(f"  ✓ Domain-specific templates work for {len(domains)} domains")


def test_regeneration_bumps_version():
    """Test that regenerating a draft increments the version."""
    gen = PaperDraftGenerator()
    h = _make_hypothesis()

    draft1 = gen.generate_full_draft(h)
    assert draft1.version == 1

    draft2 = gen.generate_full_draft(h)
    assert draft2.version == 2

    draft3 = gen.generate_full_draft(h)
    assert draft3.version == 3
    print("  ✓ Regeneration increments version correctly")


def test_storage_and_retrieval():
    """Test draft storage and retrieval."""
    gen = PaperDraftGenerator()
    h1 = _make_hypothesis(hid="H001")
    h2 = _make_hypothesis(hid="H002", domain="Cosmology")

    gen.generate_full_draft(h1)
    gen.generate_full_draft(h2)

    assert gen.draft_count == 2
    assert gen.get_draft("H001") is not None
    assert gen.get_draft("H002") is not None
    assert gen.get_draft("H999") is None

    all_drafts = gen.get_all_drafts()
    assert len(all_drafts) == 2
    assert all(isinstance(d, dict) for d in all_drafts)
    print(f"  ✓ Storage and retrieval works: {gen.draft_count} drafts")


def test_to_dict_serialization():
    """Test that PaperDraft.to_dict produces valid JSON-serializable dict."""
    import json
    gen = PaperDraftGenerator()
    h = _make_hypothesis()
    draft = gen.generate_full_draft(h)

    d = draft.to_dict()
    # Should be JSON-serializable
    json_str = json.dumps(d)
    assert len(json_str) > 100
    parsed = json.loads(json_str)
    assert parsed["hypothesis_id"] == "H099"
    assert parsed["version"] == 1

    # Generator summary
    summary = gen.to_dict()
    json.dumps(summary)  # Should not raise
    assert summary["draft_count"] == 1
    print("  ✓ Serialization works correctly")


def test_empty_hypothesis():
    """Test graceful handling of hypothesis with no test results."""
    gen = PaperDraftGenerator()
    h = Hypothesis(
        id="H000",
        name="Empty Hypothesis",
        domain="Unknown",
        description="A hypothesis with no data.",
        confidence=0.5,
    )
    draft = gen.generate_full_draft(h)
    assert draft.title, "Should still generate a title"
    assert draft.abstract, "Should still generate an abstract"
    assert "No individual test results" in draft.results, "Should note missing results"
    print("  ✓ Handles empty hypothesis gracefully")


if __name__ == "__main__":
    tests = [
        test_generate_abstract,
        test_generate_methods,
        test_generate_results,
        test_generate_full_draft,
        test_domain_templates,
        test_regeneration_bumps_version,
        test_storage_and_retrieval,
        test_to_dict_serialization,
        test_empty_hypothesis,
    ]
    passed = 0
    failed = 0
    for test_fn in tests:
        name = test_fn.__name__
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            import traceback
            print(f"  ✗ {name} FAILED: {e}")
            traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"Phase 9.5 Paper Generator Tests: {passed}/{passed+failed} passed")
    if failed:
        print(f"  {failed} test(s) FAILED")
        sys.exit(1)
    else:
        print("  All tests passed! ✓")
