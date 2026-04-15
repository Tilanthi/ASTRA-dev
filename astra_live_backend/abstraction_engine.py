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
ASTRA Live — Abstraction Engine
Observes validated hypotheses and proposes unifying theoretical frameworks.

Phase 2 of the ASTRA theoretical framework infrastructure.
As described in White & Dey (2026), Section 5 (Theory Synthesis).
"""
import re
import time
import uuid
import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

try:
    from .theory import Theory
except ImportError:
    # theory.py being written in parallel — minimal fallback matching real API
    @dataclass
    class Theory:  # type: ignore[no-redef]
        id: str
        name: str
        domain: str
        axioms: List[str]
        derived_predictions: List[str]
        domain_of_validity: Dict[str, Any]
        falsification_conditions: List[str]
        supporting_hypothesis_ids: List[str]
        competing_theory_ids: List[str]
        mathematical_core: str
        confidence: float = 0.5
        status: str = "proposed"
        novelty_score: float = 0.0
        unification_count: int = 0
        predictive_economy: float = 0.0
        created_at: float = field(default_factory=time.time)
        updated_at: float = field(default_factory=time.time)
        provenance: List[str] = field(default_factory=list)
        test_results: List[Dict[str, Any]] = field(default_factory=list)

        def to_dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items()}


# ─── Mathematical Form Patterns ──────────────────────────────────────────────

_FORM_PATTERNS: List[tuple] = [
    # (form_name, regex_list)
    ("power_law",     [r"power.law", r"power law", r"scaling\s+law", r"exponent",
                       r"index\s*=\s*[-\d]", r"α\s*=", r"β\s*=", r"\bscale\b.*\brelation\b"]),
    ("exponential",   [r"exponential", r"e\^", r"exp\(", r"e-folding",
                       r"decay\s+time", r"e-fold"]),
    ("linear",        [r"linear\s+relation", r"linearly\s+correl", r"proportional",
                       r"slope\s*=", r"constant\s+fraction"]),
    ("bimodal",       [r"bimodal", r"two.peak", r"double.gaussian", r"red\s+sequence",
                       r"blue\s+cloud", r"bimodality", r"two\s+population"]),
    ("causal_chain",  [r"causal", r"trigger", r"feedback", r"chain", r"cascade",
                       r"drives\b", r"leads\s+to", r"causes\b"]),
    ("lognormal",     [r"log.normal", r"lognormal", r"log-normal"]),
    ("periodic",      [r"period", r"oscillat", r"cycl", r"sinusoid"]),
]


def _classify_form(description: str) -> str:
    """Classify hypothesis mathematical form from its description text."""
    desc_lower = description.lower()
    for form, patterns in _FORM_PATTERNS:
        for pat in patterns:
            if re.search(pat, desc_lower):
                return form
    return "unknown"


def _extract_variables(description: str) -> List[str]:
    """Extract variable/quantity names from hypothesis description."""
    # Match words in Greek + English that look like physical variables
    greek = r"α|β|γ|δ|ε|ζ|η|θ|λ|μ|ν|ξ|π|ρ|σ|τ|φ|χ|ψ|ω|Γ|Δ|Λ|Σ|Ω|Φ"
    candidates = re.findall(
        rf"(?:{greek}|\b[A-Z][a-z]{{0,2}}\b|\b(?:mass|luminosity|radius|temperature|"
        r"velocity|flux|density|pressure|entropy|metallicity|redshift|period|"
        r"frequency|energy|color|distance|parallax|magnitude|SFR|sSFR|H0|sigma|"
        r"IMF|SFE|N_H|T_dust|T_eff|L_X|M_BH|M_halo)\b)",
        description,
    )
    # Deduplicate while preserving order
    seen: set = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


# ─── AbstractionEngine ────────────────────────────────────────────────────────

class AbstractionEngine:
    """
    Observes validated (and high-confidence) hypotheses, clusters them by
    mathematical form and shared variables, and proposes unifying Theory objects.
    """

    KNOWN_FRAMEWORKS: List[str] = [
        "Tully-Fisher relation",
        "Faber-Jackson relation",
        "Stefan-Boltzmann law",
        "Kennicutt-Schmidt relation",
        "M-sigma relation",
        "Salpeter IMF",
        "Press-Schechter formalism",
        "ΛCDM concordance model",
        "Hubble law",
        "Kepler laws",
        "virial theorem",
        "free-fall collapse",
        "Jeans instability",
        "stellar main sequence",
        "galaxy main sequence",
        "mass-metallicity relation",
        "Fundamental Plane",
        "planetary mass-radius relation",
        "SNe Ia standard candle",
        "CMB acoustic oscillations",
    ]

    # Minimum hypotheses in a cluster to propose a theory
    MIN_CLUSTER_SIZE = 2
    # Minimum average confidence in cluster
    MIN_AVG_CONFIDENCE = 0.55

    def __init__(self):
        self._proposed_theories: List[Theory] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def run(
        self,
        hypothesis_store,
        existing_theories: Optional[List[Theory]] = None,
    ) -> List[Theory]:
        """
        Scan hypothesis_store for validated/high-confidence hypotheses,
        cluster by mathematical form and shared variables, and return
        a list of proposed Theory objects.
        """
        existing_theories = existing_theories or []

        # Gather candidates: validated or confidence > threshold
        from .hypotheses import Phase  # type: ignore[attr-defined]
        candidates = [
            h for h in hypothesis_store.all()
            if h.phase in (Phase.VALIDATED, Phase.PUBLISHED)
            or h.confidence >= 0.65
        ]

        if len(candidates) < self.MIN_CLUSTER_SIZE:
            return []

        clusters = self._cluster_hypotheses(candidates)
        theories: List[Theory] = []

        existing_names = {t.name for t in existing_theories}

        for cluster in clusters:
            if len(cluster) < self.MIN_CLUSTER_SIZE:
                continue
            avg_conf = sum(h.confidence for h in cluster) / len(cluster)
            if avg_conf < self.MIN_AVG_CONFIDENCE:
                continue
            theory = self._propose_theory(cluster)
            if theory is None:
                continue
            if theory.name in existing_names:
                continue
            theory.novelty_score = self._score_novelty(theory)
            theories.append(theory)
            existing_names.add(theory.name)

        self._proposed_theories = theories
        return theories

    def get_proposed_theories(self) -> List[Theory]:
        return list(self._proposed_theories)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _cluster_hypotheses(self, hypotheses) -> List[List]:
        """
        Group hypotheses by (mathematical_form, shared_variable_set).
        Returns list of clusters (each cluster is a list of hypotheses).
        """
        # Build fingerprints
        fingerprints: Dict[str, Dict] = {}
        for h in hypotheses:
            fingerprints[h.id] = {
                "form": _classify_form(h.description),
                "variables": set(_extract_variables(h.description)),
                "domain": h.domain,
            }

        # Simple greedy clustering: same form + at least one shared variable
        used = set()
        clusters: List[List] = []

        for i, h in enumerate(hypotheses):
            if h.id in used:
                continue
            fp_i = fingerprints[h.id]
            cluster = [h]
            used.add(h.id)

            for j, h2 in enumerate(hypotheses):
                if j <= i or h2.id in used:
                    continue
                fp_j = fingerprints[h2.id]
                # Same form (or one is "unknown") AND shared variables
                form_match = (
                    fp_i["form"] == fp_j["form"]
                    or "unknown" in (fp_i["form"], fp_j["form"])
                )
                var_overlap = fp_i["variables"] & fp_j["variables"]
                if form_match and len(var_overlap) >= 1:
                    cluster.append(h2)
                    used.add(h2.id)

            clusters.append(cluster)

        return clusters

    def _propose_theory(self, cluster: List) -> Optional[Theory]:
        """Synthesise a Theory from a cluster of structurally similar hypotheses."""
        # Determine dominant form
        forms = [_classify_form(h.description) for h in cluster]
        dominant_form = max(set(forms), key=forms.count)

        # Collect all variables mentioned across cluster
        all_vars: set = set()
        for h in cluster:
            all_vars |= set(_extract_variables(h.description))

        # Build axioms from cluster patterns
        axioms = self._derive_axioms(cluster, dominant_form, all_vars)

        # Derive predictions beyond the individual hypotheses
        predictions = self._derive_predictions(cluster, dominant_form, all_vars)

        # Estimate free parameters: one per unique variable pair relationship
        n_vars = max(len(all_vars), 1)
        free_params = max(1, n_vars - 1)

        predictive_economy = len(predictions) / free_params

        # Name the theory
        domains = list({h.domain for h in cluster})
        domain_str = " & ".join(sorted(domains)[:2])
        form_label = dominant_form.replace("_", "-").title()
        theory_name = f"Unified {form_label} Framework ({domain_str})"

        # Build falsification conditions from the theory form
        falsification = [
            f"Observations inconsistent with {dominant_form.replace('_',' ')} "
            f"scaling across ≥2 independent datasets would falsify this framework.",
            "Discovery of a counter-example hypothesis with confidence > 0.80 "
            "and the same variable set but different scaling would falsify.",
        ]

        theory = Theory(
            id=f"TH-{uuid.uuid4().hex[:8].upper()}",
            name=theory_name,
            domain=domain_str,
            axioms=axioms,
            derived_predictions=predictions,
            domain_of_validity={
                "domains": list({h.domain for h in cluster}),
                "n_supporting_hypotheses": len(cluster),
                "avg_confidence": round(sum(h.confidence for h in cluster) / len(cluster), 3),
                "variables": list(all_vars)[:8],
            },
            falsification_conditions=falsification,
            supporting_hypothesis_ids=[h.id for h in cluster],
            competing_theory_ids=[],
            mathematical_core=(
                f"{dominant_form.replace('_',' ').title()} scaling: "
                f"f({', '.join(list(all_vars)[:3])}) = const."
            ),
            confidence=min(0.95, sum(h.confidence for h in cluster) / len(cluster)),
            novelty_score=0.5,  # placeholder; overwritten by _score_novelty
            unification_count=len(cluster),
            predictive_economy=round(predictive_economy, 3),
            created_at=time.time(),
            provenance=[
                f"AbstractionEngine: clustered {len(cluster)} hypotheses "
                f"by form='{dominant_form}'",
            ],
        )
        return theory

    def _derive_axioms(
        self,
        cluster: List,
        dominant_form: str,
        variables: set,
    ) -> List[str]:
        """Generate axiom statements for the proposed theory."""
        axioms: List[str] = []
        var_list = list(variables)[:4]

        form_axioms: Dict[str, List[str]] = {
            "power_law": [
                f"Observable quantities ({', '.join(var_list)}) obey power-law scaling relations.",
                "The scaling exponent is constant across the parameter space covered by the cluster.",
            ],
            "exponential": [
                f"Variables ({', '.join(var_list)}) exhibit exponential growth or decay.",
                "The characteristic e-folding scale is a physical invariant.",
            ],
            "linear": [
                f"A linear proportionality holds among ({', '.join(var_list)}).",
                "The proportionality constant is determined by underlying physics, not initial conditions.",
            ],
            "bimodal": [
                f"The distribution of ({', '.join(var_list)}) is intrinsically bimodal.",
                "Two distinct physical regimes produce the observed populations.",
            ],
            "causal_chain": [
                f"Causal ordering exists among ({', '.join(var_list)}).",
                "Feedback loops modulate the causal chain but do not break it.",
            ],
        }

        axioms = form_axioms.get(dominant_form, [
            f"A unifying mathematical structure relates ({', '.join(var_list)}).",
            "The relationship is physically motivated and dimensionally consistent.",
        ])

        # Add a cluster-size axiom
        axioms.append(
            f"Supported by {len(cluster)} independent validated hypotheses "
            f"(mean confidence {sum(h.confidence for h in cluster)/len(cluster):.2f})."
        )
        return axioms

    def _derive_predictions(
        self,
        cluster: List,
        dominant_form: str,
        variables: set,
    ) -> List[str]:
        """Generate testable predictions extending beyond the cluster."""
        preds: List[str] = []
        var_list = list(variables)[:4]

        if dominant_form == "power_law":
            preds = [
                f"The power-law index should be universal across {cluster[0].domain} sub-samples.",
                f"A log-log plot of ({var_list[0] if var_list else 'X'}) vs ({var_list[1] if len(var_list) > 1 else 'Y'}) "
                "should show <0.05 scatter around best-fit slope.",
                "The relation should hold at higher redshift with measurable evolution parameter.",
                f"Outliers should cluster near physical transitions (e.g., phase change, regime boundary).",
            ]
        elif dominant_form == "exponential":
            preds = [
                f"The e-folding timescale should be recoverable from independent observations.",
                "Stacking analysis should reveal consistent decay/growth constant.",
                "Extreme outliers should follow a Lévy tail rather than normal residuals.",
            ]
        elif dominant_form == "linear":
            preds = [
                "The linear slope should be recoverable via orthogonal regression with no intercept offset.",
                "Sub-populations identified by secondary variables should scatter around the same relation.",
                "The relation should be stable across 3–5 orders of magnitude in the independent variable.",
            ]
        elif dominant_form == "bimodal":
            preds = [
                "A transitional 'green valley' or intermediate population should exist between peaks.",
                "The peak separation should evolve monotonically with redshift or environment.",
                "Dynamical indicators should discriminate the two populations.",
            ]
        elif dominant_form == "causal_chain":
            preds = [
                "Intervening on the upstream variable should propagate measurably to downstream observables.",
                "Partial correlation after controlling for chain intermediates should approach zero.",
                "Timescale ordering of variables should match the inferred causal sequence.",
            ]
        else:
            preds = [
                "Independent observations in a new parameter regime should conform to the proposed framework.",
                "Dimensionless combinations of the involved variables should remain invariant.",
            ]

        return preds

    def _score_novelty(self, theory: Theory) -> float:
        """
        Compare theory against KNOWN_FRAMEWORKS.
        Returns 0.0 for known frameworks, 1.0 for completely novel.
        """
        domain_hint = theory.domain.lower() if hasattr(theory, "domain") else ""
        theory_lower = theory.name.lower() + " " + domain_hint
        max_overlap = 0.0

        for known in self.KNOWN_FRAMEWORKS:
            # Token overlap score
            known_tokens = set(known.lower().split())
            theory_tokens = set(theory_lower.split())
            if not known_tokens:
                continue
            overlap = len(known_tokens & theory_tokens) / len(known_tokens)
            max_overlap = max(max_overlap, overlap)

        return round(1.0 - max_overlap, 3)
