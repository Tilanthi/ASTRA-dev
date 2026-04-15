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
ASTRA Live — Auto Paper Draft Generation (Phase 9.5)
Template-based paper draft generation for validated hypotheses.
"""
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Paper Draft Data Class
# ═══════════════════════════════════════════════════════════════

@dataclass
class PaperDraft:
    """A generated paper draft for a validated hypothesis."""
    hypothesis_id: str
    title: str
    abstract: str
    methods: str
    results: str
    conclusion: str
    domain: str
    confidence: float
    novelty_score: float = 0.5
    generated_at: float = field(default_factory=time.time)
    version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    def full_text(self) -> str:
        """Return concatenated full paper draft."""
        sections = [
            f"# {self.title}\n",
            "## Abstract\n",
            self.abstract + "\n",
            "## 1. Introduction\n",
            self._intro_from_abstract() + "\n",
            "## 2. Methods\n",
            self.methods + "\n",
            "## 3. Results\n",
            self.results + "\n",
            "## 4. Discussion and Conclusion\n",
            self.conclusion + "\n",
        ]
        return "\n".join(sections)

    def _intro_from_abstract(self) -> str:
        """Generate a brief introduction stub from abstract context."""
        return (
            f"This paper presents results from the ASTRA autonomous discovery engine "
            f"in the domain of {self.domain}. The analysis was conducted using real "
            f"observational data and rigorous statistical methods. "
            f"The hypothesis was validated with a Bayesian posterior confidence of "
            f"{self.confidence:.2f}, meeting the threshold for automated reporting."
        )


# ═══════════════════════════════════════════════════════════════
# Domain-Specific Templates
# ═══════════════════════════════════════════════════════════════

_DOMAIN_TEMPLATES: Dict[str, Dict[str, str]] = {
    "Astrophysics": {
        "abstract_prefix": (
            "We present an automated analysis of {name} using data from "
            "astronomical surveys. "
        ),
        "methods_header": (
            "Observational data were obtained from public astronomical archives "
            "including the NASA Exoplanet Archive, SDSS DR18, Gaia DR3, and "
            "Pantheon+ supernova compilations. "
        ),
        "results_header": (
            "Our statistical analysis of {n_data} data points yields the following "
            "key findings. "
        ),
        "conclusion_header": (
            "The ASTRA discovery engine has autonomously identified and validated "
            "this result with {confidence:.0%} Bayesian posterior confidence. "
        ),
    },
    "Cosmology": {
        "abstract_prefix": (
            "We report an autonomous cosmological analysis of {name} "
            "using standardizable candle data and distance ladder techniques. "
        ),
        "methods_header": (
            "Distance modulus measurements were obtained from the Pantheon+ "
            "compilation of 1701 Type Ia supernovae, supplemented by Planck CMB "
            "constraints where applicable. Bayesian inference was performed using "
            "flat ΛCDM and extended cosmological models. "
        ),
        "results_header": (
            "Cosmological parameter estimation from {n_data} data points "
            "yields the following constraints. "
        ),
        "conclusion_header": (
            "This cosmological analysis, conducted autonomously by the ASTRA "
            "discovery engine, achieves {confidence:.0%} posterior confidence. "
        ),
    },
    "Exoplanets": {
        "abstract_prefix": (
            "We present a statistical analysis of {name} using confirmed "
            "exoplanet data from the NASA Exoplanet Archive. "
        ),
        "methods_header": (
            "Our sample comprises confirmed exoplanets from the NASA Exoplanet "
            "Archive with measured orbital periods, planetary masses, and radii "
            "where available. Transit and radial velocity discoveries are analyzed "
            "both jointly and separately to control for detection biases. "
        ),
        "results_header": (
            "Statistical analysis of {n_data} confirmed exoplanets reveals "
            "the following patterns. "
        ),
        "conclusion_header": (
            "This exoplanet population study, performed autonomously by ASTRA, "
            "validates the hypothesis with {confidence:.0%} confidence. "
        ),
    },
    "Stellar Physics": {
        "abstract_prefix": (
            "We report an automated stellar population analysis of {name} "
            "using Gaia DR3 astrometry and photometry. "
        ),
        "methods_header": (
            "Stellar data were obtained from Gaia Data Release 3, providing "
            "high-precision parallaxes, proper motions, and broad-band photometry. "
            "Absolute magnitudes were computed using parallax-based distances with "
            "quality cuts on parallax_over_error > 10. "
        ),
        "results_header": (
            "Analysis of {n_data} stellar sources in our quality-selected sample "
            "yields the following results. "
        ),
        "conclusion_header": (
            "This stellar physics result was discovered and validated by ASTRA "
            "with {confidence:.0%} Bayesian posterior confidence. "
        ),
    },
}

_DEFAULT_TEMPLATE = {
    "abstract_prefix": (
        "We present an automated scientific analysis of {name} "
        "conducted by the ASTRA autonomous discovery engine. "
    ),
    "methods_header": (
        "Data were obtained from publicly available scientific archives "
        "and analyzed using standard statistical methods including "
        "Kolmogorov-Smirnov tests, chi-squared tests, Bayesian t-tests, "
        "and Pearson correlation analysis. "
    ),
    "results_header": (
        "Our analysis of {n_data} data points yields the following results. "
    ),
    "conclusion_header": (
        "This result was autonomously discovered and validated by the ASTRA "
        "engine with {confidence:.0%} posterior confidence. "
    ),
}


def _get_template(domain: str) -> Dict[str, str]:
    """Get domain-specific template, falling back to default."""
    # Try exact match first, then prefix match
    if domain in _DOMAIN_TEMPLATES:
        return _DOMAIN_TEMPLATES[domain]
    for key in _DOMAIN_TEMPLATES:
        if key.lower() in domain.lower() or domain.lower() in key.lower():
            return _DOMAIN_TEMPLATES[key]
    return _DEFAULT_TEMPLATE


# ═══════════════════════════════════════════════════════════════
# Paper Draft Generator
# ═══════════════════════════════════════════════════════════════

class PaperDraftGenerator:
    """
    Generates template-based paper drafts for validated hypotheses.
    Uses hypothesis metadata (test results, confidence, data points, domain)
    to fill domain-specific templates.
    """

    def __init__(self):
        self._drafts: Dict[str, PaperDraft] = {}  # hypothesis_id -> PaperDraft

    # ── Section generators ────────────────────────────────────────

    def generate_abstract(self, hypothesis) -> str:
        """Generate ~200-word abstract from hypothesis metadata."""
        tmpl = _get_template(hypothesis.domain)
        n_tests = len(hypothesis.test_results)
        n_data = hypothesis.data_points_used or 0

        # Summarize test results
        passed = sum(
            1 for t in hypothesis.test_results
            if (isinstance(t, dict) and t.get("passed", False))
            or (hasattr(t, "passed") and t.passed)
        )
        best_p = _best_pvalue(hypothesis.test_results)
        test_names = _unique_test_names(hypothesis.test_results)

        abstract = tmpl["abstract_prefix"].format(
            name=hypothesis.name,
            n_data=n_data,
            confidence=hypothesis.confidence,
        )
        abstract += (
            f"{hypothesis.description} "
            f"Using {n_data:,} data points, we apply {n_tests} statistical tests "
            f"({', '.join(test_names) if test_names else 'multiple methods'}) "
            f"to evaluate this hypothesis. "
        )
        if best_p is not None:
            abstract += (
                f"The most significant result yields p = {best_p:.2e}, "
                f"with {passed}/{n_tests} tests supporting the hypothesis. "
            )
        abstract += (
            f"Bayesian updating produces a posterior confidence of "
            f"{hypothesis.confidence:.2f}. "
        )
        # Novelty statement
        novelty = self._get_novelty(hypothesis)
        if novelty >= 0.7:
            abstract += "This finding represents a novel contribution with limited precedent in the literature."
        elif novelty >= 0.4:
            abstract += "This result is consistent with and extends existing literature in this area."
        else:
            abstract += "This result confirms and quantifies a well-established phenomenon."

        return abstract

    def generate_methods(self, hypothesis) -> str:
        """Generate methods section from hypothesis metadata."""
        tmpl = _get_template(hypothesis.domain)
        n_data = hypothesis.data_points_used or 0
        test_names = _unique_test_names(hypothesis.test_results)

        methods = tmpl["methods_header"].format(
            name=hypothesis.name,
            n_data=n_data,
            confidence=hypothesis.confidence,
        )
        methods += "\n\n### 2.1 Data Selection\n\n"
        methods += (
            f"A total of {n_data:,} data points were used in this analysis. "
            f"Data quality cuts were applied following standard practices for "
            f"the {hypothesis.domain} domain.\n\n"
        )
        methods += "### 2.2 Statistical Analysis\n\n"
        if test_names:
            methods += "The following statistical tests were applied:\n\n"
            for i, name in enumerate(test_names, 1):
                methods += f"  {i}. **{name}** — "
                methods += _describe_test(name) + "\n"
        methods += (
            f"\nAll p-values were evaluated at the α = 0.05 significance level. "
            f"False discovery rate (FDR) correction was applied using the "
            f"Benjamini-Hochberg procedure where multiple comparisons were involved. "
            f"Bayesian confidence was updated sequentially using likelihood ratios "
            f"derived from p-value thresholds.\n"
        )
        return methods

    def generate_results(self, hypothesis) -> str:
        """Generate results section from test results."""
        tmpl = _get_template(hypothesis.domain)
        n_data = hypothesis.data_points_used or 0

        results = tmpl["results_header"].format(
            name=hypothesis.name,
            n_data=n_data,
            confidence=hypothesis.confidence,
        )
        results += "\n\n### 3.1 Statistical Test Results\n\n"

        if hypothesis.test_results:
            results += "| Test | Statistic | p-value | Result |\n"
            results += "|------|-----------|---------|--------|\n"
            for t in hypothesis.test_results:
                t_dict = t if isinstance(t, dict) else asdict(t) if hasattr(t, '__dataclass_fields__') else {}
                name = t_dict.get("test_name", "Unknown")
                stat = t_dict.get("statistic", 0)
                p = t_dict.get("p_value", 1.0)
                passed = t_dict.get("passed", False)
                results += f"| {name} | {stat:.4f} | {p:.2e} | {'✓ Pass' if passed else '✗ Fail'} |\n"
        else:
            results += "*No individual test results recorded.*\n"

        results += f"\n### 3.2 Bayesian Confidence\n\n"
        results += (
            f"Sequential Bayesian updating across all test results yields a "
            f"posterior confidence of **{hypothesis.confidence:.4f}** "
            f"(prior: 0.50). "
        )
        if hypothesis.confidence > 0.95:
            results += "This exceeds the 0.95 threshold for high-confidence validation.\n"
        elif hypothesis.confidence > 0.75:
            results += "This exceeds the 0.75 threshold for validation.\n"
        else:
            results += f"The current confidence is {hypothesis.confidence:.2f}.\n"

        # Cross-domain links
        if hypothesis.cross_domain_links:
            results += f"\n### 3.3 Cross-Domain Connections\n\n"
            results += (
                f"This hypothesis has {len(hypothesis.cross_domain_links)} "
                f"cross-domain link(s): {', '.join(hypothesis.cross_domain_links)}.\n"
            )

        return results

    def generate_conclusion(self, hypothesis) -> str:
        """Generate conclusion section."""
        tmpl = _get_template(hypothesis.domain)
        conclusion = tmpl["conclusion_header"].format(
            name=hypothesis.name,
            n_data=hypothesis.data_points_used or 0,
            confidence=hypothesis.confidence,
        )
        n_tests = len(hypothesis.test_results)
        passed = sum(
            1 for t in hypothesis.test_results
            if (isinstance(t, dict) and t.get("passed", False))
            or (hasattr(t, "passed") and t.passed)
        )
        conclusion += (
            f"Of {n_tests} statistical tests applied, {passed} support the hypothesis "
            f"at the α = 0.05 level. "
        )
        novelty = self._get_novelty(hypothesis)
        if novelty >= 0.7:
            conclusion += (
                f"With a literature novelty score of {novelty:.2f}, this finding "
                f"warrants further investigation and independent confirmation. "
            )
        elif novelty >= 0.4:
            conclusion += (
                f"The literature novelty score of {novelty:.2f} suggests this result "
                f"extends current knowledge incrementally. "
            )
        else:
            conclusion += (
                f"The literature novelty score of {novelty:.2f} indicates this is "
                f"a well-established result that ASTRA has independently recovered. "
            )

        conclusion += (
            "\n\nThis draft was generated automatically by the ASTRA autonomous "
            "scientific discovery engine. It should be reviewed by domain experts "
            "before any formal submission."
        )
        return conclusion

    # ── Full draft generation ─────────────────────────────────────

    def generate_full_draft(self, hypothesis) -> PaperDraft:
        """Generate a complete paper draft for a hypothesis."""
        title = self._generate_title(hypothesis)
        abstract = self.generate_abstract(hypothesis)
        methods = self.generate_methods(hypothesis)
        results = self.generate_results(hypothesis)
        conclusion = self.generate_conclusion(hypothesis)
        novelty = self._get_novelty(hypothesis)

        # Bump version if re-generating
        version = 1
        if hypothesis.id in self._drafts:
            version = self._drafts[hypothesis.id].version + 1

        draft = PaperDraft(
            hypothesis_id=hypothesis.id,
            title=title,
            abstract=abstract,
            methods=methods,
            results=results,
            conclusion=conclusion,
            domain=hypothesis.domain,
            confidence=hypothesis.confidence,
            novelty_score=novelty,
            version=version,
        )
        self._drafts[hypothesis.id] = draft
        logger.info(f"Generated paper draft v{version} for {hypothesis.id}: {title}")
        return draft

    # ── Storage ───────────────────────────────────────────────────

    def get_draft(self, hypothesis_id: str) -> Optional[PaperDraft]:
        """Get a stored draft by hypothesis ID."""
        return self._drafts.get(hypothesis_id)

    def get_all_drafts(self) -> List[dict]:
        """Return all drafts as dicts, sorted by generation time (newest first)."""
        drafts = sorted(
            self._drafts.values(),
            key=lambda d: d.generated_at,
            reverse=True,
        )
        return [d.to_dict() for d in drafts]

    @property
    def draft_count(self) -> int:
        return len(self._drafts)

    # ── Helpers ───────────────────────────────────────────────────

    def _generate_title(self, hypothesis) -> str:
        """Generate a paper title from hypothesis metadata."""
        domain = hypothesis.domain
        name = hypothesis.name

        # Domain-specific title patterns
        prefixes = {
            "Astrophysics": "Automated Discovery:",
            "Cosmology": "Cosmological Constraints on",
            "Exoplanets": "Statistical Analysis of",
            "Stellar Physics": "Stellar Population Study:",
            "Economics": "Cross-Domain Analysis:",
            "Climate": "Climate-Astronomical Correlation:",
            "Epidemiology": "Methodological Transfer:",
        }
        prefix = prefixes.get(domain, "Autonomous Analysis of")

        n_data = hypothesis.data_points_used or 0
        if n_data > 1000:
            suffix = f"from {n_data:,} Observations"
        elif n_data > 0:
            suffix = f"using {n_data:,} Data Points"
        else:
            suffix = "with the ASTRA Discovery Engine"

        return f"{prefix} {name} {suffix}"

    def _get_novelty(self, hypothesis) -> float:
        """Get novelty score for hypothesis from literature store."""
        try:
            from .literature import get_literature_store
            store = get_literature_store()
            text = f"{hypothesis.name} {hypothesis.description}"
            return store.compute_novelty_score(text)
        except Exception:
            return 0.5  # Unknown if literature store unavailable

    def to_dict(self) -> dict:
        """Serializable summary."""
        return {
            "draft_count": self.draft_count,
            "drafts": [
                {
                    "hypothesis_id": d.hypothesis_id,
                    "title": d.title,
                    "domain": d.domain,
                    "confidence": d.confidence,
                    "novelty_score": d.novelty_score,
                    "version": d.version,
                    "generated_at": d.generated_at,
                }
                for d in self._drafts.values()
            ],
        }


# ═══════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════

def _best_pvalue(test_results: list) -> Optional[float]:
    """Extract the lowest (most significant) p-value from test results."""
    pvals = []
    for t in test_results:
        if isinstance(t, dict):
            p = t.get("p_value")
        elif hasattr(t, "p_value"):
            p = t.p_value
        else:
            continue
        if p is not None:
            pvals.append(float(p))
    return min(pvals) if pvals else None


def _unique_test_names(test_results: list) -> List[str]:
    """Extract unique test names from test results, preserving order."""
    seen = set()
    names = []
    for t in test_results:
        if isinstance(t, dict):
            name = t.get("test_name", "")
        elif hasattr(t, "test_name"):
            name = t.test_name
        else:
            continue
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _describe_test(test_name: str) -> str:
    """Return a brief description of a statistical test."""
    descriptions = {
        "chi_squared": "Tests for significant deviation from expected frequency distributions.",
        "kolmogorov_smirnov": "Non-parametric test for distributional differences between samples.",
        "ks_test": "Non-parametric test for distributional differences between samples.",
        "bayesian_t_test": "Bayesian alternative to Student's t-test with posterior probability estimation.",
        "pearson_correlation": "Measures linear correlation between two continuous variables.",
        "granger_causality": "Tests whether one time series helps predict another.",
        "anderson_darling": "Tests whether a sample comes from a specified distribution.",
        "mann_whitney": "Non-parametric test for differences between two independent samples.",
        "spearman_correlation": "Rank-based correlation coefficient for monotonic relationships.",
        "linear_regression": "Ordinary least squares regression to model linear relationships.",
    }
    # Try exact match, then substring match
    lower_name = test_name.lower().replace("-", "_").replace(" ", "_")
    for key, desc in descriptions.items():
        if key in lower_name or lower_name in key:
            return desc
    return "Standard statistical test for hypothesis evaluation."


# ═══════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════

_generator: Optional[PaperDraftGenerator] = None


def get_paper_generator() -> PaperDraftGenerator:
    """Get or create the singleton PaperDraftGenerator."""
    global _generator
    if _generator is None:
        _generator = PaperDraftGenerator()
    return _generator
