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
Tests for ASTRA Literature Integration (Phase 9.1+9.2).
"""
import pytest
from astra_live_backend.literature import (
    LiteratureStore, Paper, _tokenize, _cosine_similarity_dicts,
    _build_tfidf_matrix, _interpret_novelty, get_literature_store,
)


# ── Fixtures ──────────────────────────────────────────────────────

SAMPLE_PAPERS = [
    {
        "title": "Observational evidence for dark energy from Type Ia supernovae",
        "abstract": "We present observational evidence for an accelerating universe using Type Ia "
                     "supernovae as standardizable candles. The Hubble diagram of distant supernovae "
                     "implies a cosmological constant or dark energy component dominating the energy "
                     "density of the universe at the present epoch.",
        "authors": ["A. Riess", "S. Perlmutter"],
        "arxiv_id": "astro-ph/9805201",
        "published": "1998-05-15",
    },
    {
        "title": "Detection of exoplanets by the radial velocity method",
        "abstract": "We review the radial velocity technique for detecting extrasolar planets. "
                     "The method relies on Doppler shifts in stellar spectra induced by the "
                     "gravitational tug of orbiting planets. We discuss selection effects, "
                     "mass-period distributions, and detection limits.",
        "authors": ["M. Mayor", "D. Queloz"],
        "arxiv_id": "astro-ph/9901001",
        "published": "1999-01-01",
    },
    {
        "title": "Galaxy bimodality in the SDSS color-magnitude diagram",
        "abstract": "We analyze the distribution of galaxy colors in the Sloan Digital Sky Survey. "
                     "The color-magnitude diagram reveals a clear bimodal distribution with a red "
                     "sequence of early-type galaxies and a blue cloud of late-type star-forming "
                     "galaxies separated by a green valley.",
        "authors": ["K. Baldry", "M. Balogh"],
        "arxiv_id": "astro-ph/0403042",
        "published": "2004-03-01",
    },
    {
        "title": "Gravitational wave detection from binary black hole mergers",
        "abstract": "We report the first direct detection of gravitational waves from the merger "
                     "of two stellar-mass black holes. The signal matches general relativity "
                     "predictions for binary black hole inspiral, merger, and ringdown phases.",
        "authors": ["LIGO Collaboration"],
        "arxiv_id": "gr-qc/1602.03837",
        "published": "2016-02-11",
    },
    {
        "title": "The Hubble tension: a review of current measurements",
        "abstract": "We review the current discrepancy between early-universe and late-universe "
                     "measurements of the Hubble constant H0. The tension between Planck CMB "
                     "observations and SH0ES distance ladder measurements now exceeds 5 sigma, "
                     "suggesting either systematic errors or new physics beyond LCDM.",
        "authors": ["W. Freedman", "B. Madore"],
        "arxiv_id": "astro-ph/2106.15656",
        "published": "2021-06-29",
    },
]


@pytest.fixture
def store():
    """Create a fresh LiteratureStore with sample papers."""
    s = LiteratureStore()
    s.add_papers_from_arxiv(SAMPLE_PAPERS)
    return s


@pytest.fixture
def empty_store():
    return LiteratureStore()


# ── Tests ─────────────────────────────────────────────────────────

class TestTokenize:
    def test_basic(self):
        tokens = _tokenize("The dark energy of the universe")
        assert "dark" in tokens
        assert "energy" in tokens
        assert "universe" in tokens
        # Stop words removed
        assert "the" not in tokens
        assert "of" not in tokens

    def test_lowercases(self):
        tokens = _tokenize("HUBBLE Constant Tension")
        assert "hubble" in tokens
        assert "constant" in tokens


class TestLiteratureStore:
    def test_add_paper(self, empty_store):
        paper = empty_store.add_paper("Test Title", "Test abstract", arxiv_id="test-001")
        assert isinstance(paper, Paper)
        assert empty_store.paper_count == 1

    def test_deduplication(self, empty_store):
        empty_store.add_paper("Title", "Abstract", arxiv_id="dup-001")
        empty_store.add_paper("Title", "Abstract", arxiv_id="dup-001")
        assert empty_store.paper_count == 1

    def test_bulk_add(self, empty_store):
        added = empty_store.add_papers_from_arxiv(SAMPLE_PAPERS)
        assert added == 5
        assert empty_store.paper_count == 5

    def test_bulk_add_idempotent(self, store):
        added = store.add_papers_from_arxiv(SAMPLE_PAPERS)
        assert added == 0
        assert store.paper_count == 5

    def test_get_papers(self, store):
        papers = store.get_papers()
        assert len(papers) == 5
        assert all("title" in p for p in papers)
        assert all("abstract" in p for p in papers)
        assert all("authors" in p for p in papers)


class TestSimilaritySearch:
    def test_find_related_dark_energy(self, store):
        results = store.find_related_papers("dark energy cosmological constant supernova", top_k=3)
        assert len(results) > 0
        assert all("similarity" in r for r in results)
        # The dark energy paper should be most similar
        assert "dark energy" in results[0]["title"].lower() or "supernova" in results[0]["abstract"].lower()

    def test_find_related_exoplanets(self, store):
        results = store.find_related_papers("exoplanet radial velocity detection mass period", top_k=3)
        assert len(results) > 0
        # The exoplanet paper should score high
        titles = [r["title"].lower() for r in results]
        assert any("exoplanet" in t or "radial velocity" in t for t in titles)

    def test_find_related_empty(self, empty_store):
        results = empty_store.find_related_papers("anything", top_k=5)
        assert results == []

    def test_similarity_scores_sorted(self, store):
        results = store.find_related_papers("galaxy color bimodality SDSS", top_k=5)
        scores = [r["similarity"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_respected(self, store):
        results = store.find_related_papers("dark energy", top_k=2)
        assert len(results) <= 2


class TestNoveltyScoring:
    def test_novelty_known_topic(self, store):
        # A query very similar to existing papers should have LOW novelty (closer to 0)
        score = store.compute_novelty_score(
            "dark energy Type Ia supernovae cosmological constant accelerating universe Hubble diagram"
        )
        assert 0.0 <= score <= 1.0
        assert score < 0.7  # Should be somewhat established

    def test_novelty_novel_topic(self, store):
        # A very different topic should have HIGH novelty
        score = store.compute_novelty_score(
            "CRISPR gene editing therapeutic applications oncology precision medicine"
        )
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be relatively novel vs astro corpus

    def test_novelty_empty_corpus(self, empty_store):
        score = empty_store.compute_novelty_score("anything")
        assert score == 0.5  # Unknown

    def test_novelty_report(self, store):
        report = store.novelty_report("Hubble tension H0 measurement discrepancy")
        assert "novelty_score" in report
        assert "max_similarity" in report
        assert "related_papers" in report
        assert "corpus_size" in report
        assert "interpretation" in report
        assert report["corpus_size"] == 5

    def test_novelty_score_range(self, store):
        for text in ["dark energy", "exoplanets", "quantum computing"]:
            score = store.compute_novelty_score(text)
            assert 0.0 <= score <= 1.0


class TestInterpretNovelty:
    def test_interpretations(self):
        assert "Highly novel" in _interpret_novelty(0.95)
        assert "Novel" in _interpret_novelty(0.75)
        assert "Moderately" in _interpret_novelty(0.55)
        assert "Incremental" in _interpret_novelty(0.35)
        assert "Well-established" in _interpret_novelty(0.15)


class TestCustomTFIDF:
    def test_build_matrix(self):
        docs = ["the cat sat on the mat", "the dog chased the cat"]
        vectors, idf = _build_tfidf_matrix(docs)
        assert len(vectors) == 2
        assert isinstance(idf, dict)
        assert len(idf) > 0

    def test_cosine_similarity(self):
        a = {"cat": 1.0, "dog": 0.5}
        b = {"cat": 1.0, "dog": 0.5}
        assert abs(_cosine_similarity_dicts(a, b) - 1.0) < 1e-6

        c = {"fish": 1.0, "bird": 0.5}
        assert _cosine_similarity_dicts(a, c) == 0.0


class TestSingleton:
    def test_get_literature_store(self):
        s1 = get_literature_store()
        s2 = get_literature_store()
        assert s1 is s2


# ═══════════════════════════════════════════════════════════════
# Citation Graph (Phase 9.4)
# ═══════════════════════════════════════════════════════════════

from astra_live_backend.literature import CitationGraph, get_citation_graph


class TestCitationGraph:
    @pytest.fixture
    def graph(self):
        g = CitationGraph()
        g.add_citation("paper-A", "paper-B")
        g.add_citation("paper-A", "paper-C")
        g.add_citation("paper-B", "paper-C")
        g.add_citation("paper-D", "paper-C")
        return g

    def test_add_citation(self, graph):
        assert "paper-B" in graph.references("paper-A")
        assert "paper-A" in graph.cited_by("paper-B")

    def test_citation_count(self, graph):
        assert graph.citation_count("paper-C") == 3  # cited by A, B, D
        assert graph.citation_count("paper-B") == 1  # cited by A only

    def test_most_cited(self, graph):
        top = graph.most_cited(2)
        assert top[0] == ("paper-C", 3)

    def test_network_stats(self, graph):
        stats = graph.network_stats()
        assert stats["node_count"] == 4
        assert stats["edge_count"] == 4

    def test_h_index(self, graph):
        h = graph.h_index()
        assert isinstance(h, int)
        assert h >= 0

    def test_citation_chains(self, graph):
        chains = graph.find_citation_chains("paper-A", max_depth=3)
        assert isinstance(chains, list)
        assert len(chains) > 0

    def test_to_graph_json(self, graph):
        gj = graph.to_graph_json()
        assert "nodes" in gj
        assert "edges" in gj
        assert len(gj["nodes"]) == 4
        assert len(gj["edges"]) == 4

    def test_build_from_store(self):
        store = LiteratureStore()
        # Add papers that reference each other via arXiv IDs in abstracts
        store.add_paper(
            title="Paper Alpha",
            abstract="We extend the results of astro-ph/9805201 to higher redshifts.",
            arxiv_id="2301.00001",
        )
        store.add_paper(
            title="Paper Beta",
            abstract="Original dark energy observations.",
            arxiv_id="astro-ph/9805201",
        )
        g = CitationGraph()
        g.build_from_literature_store(store)
        stats = g.network_stats()
        assert stats["node_count"] >= 2
        assert stats["edge_count"] >= 1
        assert "astro-ph/9805201" in g.references("2301.00001")

    def test_self_citation_ignored(self):
        g = CitationGraph()
        g.add_citation("paper-A", "paper-A")
        assert g.citation_count("paper-A") == 0

    def test_get_citation_graph_singleton(self):
        g1 = get_citation_graph()
        g2 = get_citation_graph()
        assert g1 is g2
