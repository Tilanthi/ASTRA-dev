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
ASTRA Live — Abductive Reasoning Engine
Given a surprising observation that contradicts a known theory, find the minimal
modification to existing theory that restores consistency.

Abduction is the primary mode of genuine theoretical discovery:
  anomaly + existing_theory → minimal_modification → new_predictions

As described in White & Dey (2026), Section 3: Theoretical Framework Layer.

References:
- Peirce, C. S. (1903) "Pragmatism as a principle and method of right thinking"
- Rissanen (1978) "Modeling by shortest data description" — MDL/simplicity scoring
- Harman (1965) "The inference to the best explanation"
"""
import time
import uuid
import math
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class AbductiveExplanation:
    """A candidate minimal modification to theory that explains an anomaly."""
    id: str
    anomaly_description: str           # The observation that triggered this
    source_hypothesis_ids: List[str]   # Which validated results are anomalous
    existing_theory_violated: str      # Which theoretical principle is challenged
    proposed_modification: str         # The minimal change to restore consistency
    modification_type: str             # "extension", "replacement", "restriction", "generalisation"
    axioms_changed: List[str]          # Which axioms are modified
    new_predictions: List[str]         # Novel testable predictions from the modification
    simplicity_score: float            # MDL/Occam score (0=very complex, 1=very simple)
    explanatory_power: float           # How much of the anomaly this explains (0-1)
    testability_score: float           # How directly testable the new predictions are (0-1)
    generated_at: float

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def composite_score(self) -> float:
        """Weighted composite of simplicity × explanatory_power × testability."""
        return 0.35 * self.simplicity_score + 0.40 * self.explanatory_power + 0.25 * self.testability_score


# ---------------------------------------------------------------------------
# Abduction knowledge tables
# ---------------------------------------------------------------------------

# Mapping: principle_key → (description, domain, typical_violation_keywords)
_PRINCIPLES: Dict[str, Tuple[str, str, List[str]]] = {
    "energy_conservation": (
        "Total energy is conserved in isolated systems",
        "fundamental",
        ["energy", "luminosity", "power", "erg", "flux", "radiation"],
    ),
    "momentum_conservation": (
        "Total momentum is conserved",
        "fundamental",
        ["momentum", "velocity", "kick", "jet", "outflow", "recoil"],
    ),
    "causality": (
        "Effects cannot precede causes",
        "fundamental",
        ["precede", "before", "time", "delay", "propagation"],
    ),
    "second_law": (
        "Entropy of an isolated system never decreases",
        "thermodynamics",
        ["entropy", "temperature", "heat", "cooling", "thermodynamic", "disorder"],
    ),
    "equivalence_principle": (
        "Gravitational and inertial mass are equivalent",
        "gravity",
        ["mass", "gravity", "acceleration", "free fall", "geodesic"],
    ),
    "uncertainty_principle": (
        "ΔxΔp ≥ ℏ/2",
        "quantum",
        ["quantum", "uncertainty", "photon", "electron", "wave"],
    ),
    "mass_energy_equivalence": (
        "E = mc²",
        "relativity",
        ["rest mass", "annihilation", "pair", "nuclear", "fusion", "fission"],
    ),
    "hubble_expansion": (
        "Universe is expanding at rate H₀",
        "cosmology",
        ["redshift", "distance", "expansion", "hubble", "cosmological"],
    ),
    "stellar_main_sequence": (
        "Stars fuse hydrogen on the main sequence",
        "stellar",
        ["star", "luminosity", "main sequence", "HR diagram", "hydrogen", "fusion"],
    ),
    "jeans_criterion": (
        "Gravitational collapse occurs when M > M_Jeans",
        "star_formation",
        ["collapse", "jeans", "fragmentation", "cloud", "clump", "core", "filament"],
    ),
    "virial_theorem": (
        "2K + U = 0 for virialized systems",
        "dynamics",
        ["virial", "kinetic", "potential", "virialized", "cluster", "dispersion"],
    ),
    "salpeter_imf": (
        "dN/dM ∝ M^-2.35 for M > 1 Msun",
        "star_formation",
        ["IMF", "initial mass function", "stellar mass", "salpeter", "slope"],
    ),
    "kennicutt_schmidt": (
        "SFR surface density ∝ gas surface density^1.4",
        "star_formation",
        ["star formation rate", "SFR", "schmidt", "kennicutt", "gas surface", "Σ_SFR"],
    ),
}

# Modification templates per principle
# Each entry: (modification_type, template_text, axioms_affected, prediction_templates)
_MODIFICATION_TEMPLATES: Dict[str, List[Tuple[str, str, List[str], List[str]]]] = {
    "energy_conservation": [
        ("extension",
         "Introduce a previously undetected energy reservoir (e.g., dark component, hidden radiation field) that absorbs or provides the missing energy",
         ["energy_conservation"],
         ["A new spectral component at unexpected wavelengths", "Anomalous cooling/heating rates in the same class of object", "Systematic residuals in bolometric corrections"]),
        ("restriction",
         "Restrict energy conservation to hold only in the global (not local) sense, allowing transient local violations mediated by large-scale structure",
         ["energy_conservation", "locality"],
         ["Spatially correlated energy excess/deficit across connected regions", "Coherence length in energy distribution longer than expected"]),
    ],
    "momentum_conservation": [
        ("extension",
         "Postulate anisotropic radiation pressure or hidden momentum transfer (e.g., asymmetric outflow) to account for the missing momentum",
         ["momentum_conservation"],
         ["Preferential orientation of outflows relative to large-scale filaments", "Non-zero net momentum in supposedly symmetric systems"]),
        ("generalisation",
         "Generalise momentum conservation to include field momentum (electromagnetic or gravitational wave recoil) not captured by point-mass approximation",
         ["momentum_conservation", "point_mass_approximation"],
         ["Systematic velocity offsets correlated with field strength", "Recoil kicks proportional to field gradient"]),
    ],
    "second_law": [
        ("restriction",
         "Restrict 2nd-law application: the observed subsystem is not thermodynamically isolated — entropy decrease is compensated elsewhere",
         ["second_law", "system_isolation"],
         ["Entropy increase detectable in surrounding medium", "Energy inflow correlated with local ordering"]),
        ("extension",
         "Extend thermodynamics to include non-equilibrium steady states driven by external forcing, permitting locally sustained low-entropy structures",
         ["second_law", "equilibrium_assumption"],
         ["Ordered structures persist only while energy source active", "Characteristic scale set by forcing wavelength"]),
    ],
    "jeans_criterion": [
        ("extension",
         "Extend Jeans criterion to include turbulent and magnetic support terms: M_crit = M_Jeans × f(σ_turb, B)",
         ["jeans_criterion"],
         ["Correlation between fragmentation mass scale and turbulent linewidth", "Filament width anti-correlated with magnetic field strength", "Critical mass scale varies with environment"]),
        ("replacement",
         "Replace thermal Jeans criterion with magnetically-regulated collapse: collapse proceeds only when mass-to-flux ratio exceeds critical value",
         ["jeans_criterion", "thermal_support_dominance"],
         ["Collapse timescale set by ambipolar diffusion rate", "Magnetic field geometry imprinted on final stellar mass distribution"]),
        ("restriction",
         "Restrict Jeans criterion to apply only where turbulent Mach number < 1; supersonic regions require a modified threshold",
         ["jeans_criterion", "subsonic_assumption"],
         ["Bimodal fragmentation scale in turbulent vs. quiescent regions", "IMF peak shifts in highly turbulent environments"]),
    ],
    "kennicutt_schmidt": [
        ("extension",
         "Extend KS relation by adding a metallicity-dependent efficiency factor: Σ_SFR ∝ Σ_gas^1.4 × Z^α",
         ["kennicutt_schmidt"],
         ["SFR efficiency systematically lower in metal-poor galaxies at fixed Σ_gas", "Scatter in KS relation correlated with metallicity gradient"]),
        ("restriction",
         "Restrict KS relation to molecular (not atomic) gas surface density: Σ_SFR ∝ Σ_H2^1.4",
         ["kennicutt_schmidt", "total_gas_tracer"],
         ["Tighter KS relation using CO-derived molecular mass", "Atomic gas surface density decorrelated with SFR at fixed total Σ_gas"]),
        ("generalisation",
         "Generalise KS to 3D volumetric relation: ρ_SFR ∝ ρ_gas / t_ff, where t_ff is local free-fall time",
         ["kennicutt_schmidt"],
         ["SFR correlates with Σ_gas / √(Σ_gas/h) rather than Σ_gas^1.4", "Index of KS relation approaches 1 when free-fall time variation accounted for"]),
    ],
    "salpeter_imf": [
        ("extension",
         "Extend IMF with an environmentally-sensitive turnover mass: the Jeans mass at cloud formation sets characteristic stellar mass",
         ["salpeter_imf"],
         ["IMF turnover mass correlated with temperature and density of parent cloud", "Systematic IMF variation in starburst vs. quiescent environments"]),
        ("replacement",
         "Replace universal Salpeter IMF with a turbulence-regulated IMF: slope and turnover depend on Mach number",
         ["salpeter_imf", "universality_of_imf"],
         ["IMF slope steeper in low-Mach-number quiescent clumps", "Brown dwarf fraction varies with turbulent pressure"]),
    ],
    "virial_theorem": [
        ("extension",
         "Extend virial theorem to include surface pressure term: 2K + U = -3PV_surface, important for pressure-confined clouds",
         ["virial_theorem", "isolated_system"],
         ["Virial mass overestimated for clouds in high-pressure environments", "Better mass agreement when external pressure term included"]),
        ("restriction",
         "Restrict virial theorem to time-averaged quantities; instantaneous non-virial states allowed during dynamical interactions",
         ["virial_theorem", "steady_state"],
         ["Transient non-virial states detected during merger/infall events", "Oscillatory kinetic–potential energy exchange at crossing time period"]),
    ],
    "stellar_main_sequence": [
        ("extension",
         "Extend main sequence physics to include non-standard nuclear burning channels activated at anomalous core conditions",
         ["stellar_main_sequence"],
         ["Anomalous abundances of specific isotopes in photospheres", "Non-standard neutrino flux from stellar interior"]),
        ("restriction",
         "Restrict main sequence lifetime calculation: rotation-induced mixing extends main sequence beyond standard estimate",
         ["stellar_main_sequence", "non_rotating_models"],
         ["Evolved stars appear younger than isochrone age", "Surface abundance anomalies correlated with rotation rate"]),
    ],
    "hubble_expansion": [
        ("extension",
         "Extend ΛCDM by adding a dynamical dark energy component w(z) ≠ -1 to resolve Hubble tension",
         ["hubble_expansion", "cosmological_constant"],
         ["w(z) departure from -1 detectable in BAO+SN Ia joint analysis", "Anomalous growth rate of structure at intermediate redshift"]),
    ],
    "equivalence_principle": [
        ("restriction",
         "Restrict equivalence principle: local violations at quantum length scales (Planck regime) allowed",
         ["equivalence_principle"],
         ["Tiny anomalous acceleration measurable only at sub-mm scales", "CPT violation detectable in ultra-cold atom experiments"]),
    ],
}

# Default fallback templates when no specific principle match
_DEFAULT_MODIFICATIONS = [
    ("extension",
     "Introduce an additional physical process not included in the baseline model",
     ["baseline_model_completeness"],
     ["New correlation detectable in residuals after baseline subtraction", "Systematic trend with a previously ignored parameter"]),
    ("restriction",
     "Restrict the domain of applicability of the violated principle to a subset of conditions",
     ["universality_assumption"],
     ["Behaviour reverts to standard prediction outside the restricted regime", "Clear boundary in parameter space separating anomalous and normal regimes"]),
    ("generalisation",
     "Generalise the underlying law to a higher-order expression that reduces to the standard form in the limit",
     ["linear_approximation"],
     ["Non-linear departure detectable at extreme values of the key parameter", "Second-order correction term measurable with precision data"]),
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AbductionEngine:
    """
    Generates abductive explanations (minimal theory modifications) for anomalous
    validated hypotheses or contradictions between observations and known principles.
    """

    PHYSICAL_PRINCIPLES = {k: v[0] for k, v in _PRINCIPLES.items()}

    # ------------------------------------------------------------------
    def generate_explanations(
        self,
        anomaly_hypothesis,
        validated_store=None,
    ) -> List[AbductiveExplanation]:
        """
        Given an anomalous hypothesis object (or plain dict), produce a ranked list
        of minimal theory modifications that could restore consistency.

        Parameters
        ----------
        anomaly_hypothesis : Hypothesis | dict
            The validated hypothesis that appears anomalous / surprising.
        validated_store : list[Hypothesis] | None
            Full pool of validated hypotheses (used to seek shared explanations).

        Returns
        -------
        List[AbductiveExplanation]
            Ranked from highest composite_score to lowest.
        """
        if validated_store is None:
            validated_store = []

        # Extract anomaly text
        if hasattr(anomaly_hypothesis, "description"):
            anomaly_text = anomaly_hypothesis.description
            anomaly_id = getattr(anomaly_hypothesis, "id", "unknown")
        elif isinstance(anomaly_hypothesis, dict):
            anomaly_text = anomaly_hypothesis.get("description", str(anomaly_hypothesis))
            anomaly_id = anomaly_hypothesis.get("id", "unknown")
        else:
            anomaly_text = str(anomaly_hypothesis)
            anomaly_id = "unknown"

        # Step 1: identify violated principles
        violated = self._identify_violated_principles(anomaly_text)
        if not violated:
            # default to a generic anomaly
            violated = [("energy_conservation", 0.3)]

        explanations: List[AbductiveExplanation] = []

        # Step 2: generate modifications per violated principle
        for principle_key, relevance in violated:
            templates = _MODIFICATION_TEMPLATES.get(principle_key, _DEFAULT_MODIFICATIONS)
            for (mod_type, mod_text, axioms, pred_templates) in templates:
                # Enrich predictions with anomaly context
                predictions = [p for p in pred_templates]

                exp = AbductiveExplanation(
                    id=f"ABD-{uuid.uuid4().hex[:8].upper()}",
                    anomaly_description=anomaly_text[:400],
                    source_hypothesis_ids=[anomaly_id],
                    existing_theory_violated=principle_key,
                    proposed_modification=mod_text,
                    modification_type=mod_type,
                    axioms_changed=list(axioms),
                    new_predictions=predictions,
                    simplicity_score=0.0,   # filled below
                    explanatory_power=relevance * self._explanatory_factor(mod_type),
                    testability_score=self._testability_of(predictions),
                    generated_at=time.time(),
                )
                exp.simplicity_score = self._compute_simplicity(exp)
                explanations.append(exp)

        # Step 3: look for cross-anomaly explanations (shared explanations)
        if validated_store:
            shared = self._cross_anomaly_explanations(anomaly_text, anomaly_id, validated_store)
            explanations.extend(shared)

        return self.rank_by_simplicity(explanations)

    # ------------------------------------------------------------------
    def rank_by_simplicity(
        self, explanations: List[AbductiveExplanation]
    ) -> List[AbductiveExplanation]:
        """Return explanations sorted by composite_score descending."""
        return sorted(explanations, key=lambda e: e.composite_score, reverse=True)

    # ------------------------------------------------------------------
    def _compute_simplicity(self, explanation: AbductiveExplanation) -> float:
        """
        MDL-inspired simplicity score.
        Fewer axiom changes → higher score.
        Modification types have intrinsic complexity costs.
        Score ∈ [0, 1].
        """
        n_axioms = max(len(explanation.axioms_changed), 1)
        type_penalty = {
            "restriction": 0.0,    # least invasive
            "extension": 0.1,
            "generalisation": 0.2,
            "replacement": 0.4,    # most invasive
        }.get(explanation.modification_type, 0.2)

        # MDL-style: cost grows logarithmically with axiom count
        axiom_cost = math.log2(1 + n_axioms) * 0.3

        raw = 1.0 - type_penalty - axiom_cost
        return max(0.0, min(1.0, raw))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _identify_violated_principles(self, text: str) -> List[Tuple[str, float]]:
        """
        Scan anomaly text for keywords associated with each physical principle.
        Returns list of (principle_key, relevance_score) sorted by relevance desc.
        """
        text_lower = text.lower()
        hits: List[Tuple[str, float]] = []
        for key, (_, _, keywords) in _PRINCIPLES.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                normalised = min(1.0, score / max(len(keywords), 1))
                hits.append((key, normalised))
        hits.sort(key=lambda x: x[1], reverse=True)
        return hits[:4]  # top 4 most relevant principles

    @staticmethod
    def _explanatory_factor(mod_type: str) -> float:
        """How much of the anomaly a given modification type typically explains."""
        return {
            "replacement": 0.95,
            "generalisation": 0.85,
            "extension": 0.75,
            "restriction": 0.65,
        }.get(mod_type, 0.70)

    @staticmethod
    def _testability_of(predictions: List[str]) -> float:
        """
        Heuristic testability score based on prediction content.
        Predictions mentioning specific instruments/quantities score higher.
        """
        instrument_kws = ["alma", "jwst", "vla", "herschel", "lofar", "ska", "chandra",
                          "gaia", "rubin", "euclid", "vlbi", "spire", "iram"]
        quantity_kws = ["correlation", "slope", "index", "ratio", "offset", "fraction",
                        "linewidth", "flux", "temperature", "density", "mass", "luminosity"]
        if not predictions:
            return 0.3
        total = 0.0
        for pred in predictions:
            pl = pred.lower()
            hits = sum(1 for kw in instrument_kws + quantity_kws if kw in pl)
            total += min(1.0, hits * 0.15)
        return min(1.0, total / len(predictions))

    def _cross_anomaly_explanations(
        self,
        anomaly_text: str,
        anomaly_id: str,
        validated_store,
    ) -> List[AbductiveExplanation]:
        """
        Look for explanations that simultaneously account for OTHER anomalies
        in the validated store, increasing their explanatory_power bonus.
        """
        results = []
        for h in validated_store:
            h_id = getattr(h, "id", h.get("id", "?")) if not hasattr(h, "id") else h.id
            if h_id == anomaly_id:
                continue
            h_text = getattr(h, "description", "") if hasattr(h, "description") else h.get("description", "")
            # If they share violated principles, a shared explanation is plausible
            v1 = {k for k, _ in self._identify_violated_principles(anomaly_text)}
            v2 = {k for k, _ in self._identify_violated_principles(h_text)}
            shared_principles = v1 & v2
            if shared_principles:
                principle_key = next(iter(shared_principles))
                templates = _MODIFICATION_TEMPLATES.get(principle_key, _DEFAULT_MODIFICATIONS)
                if templates:
                    mod_type, mod_text, axioms, pred_templates = templates[0]
                    exp = AbductiveExplanation(
                        id=f"ABD-CROSS-{uuid.uuid4().hex[:6].upper()}",
                        anomaly_description=(
                            f"Shared explanation for: '{anomaly_text[:200]}' "
                            f"AND '{h_text[:200]}'"
                        ),
                        source_hypothesis_ids=[anomaly_id, h_id],
                        existing_theory_violated=principle_key,
                        proposed_modification=(
                            f"[Cross-anomaly] {mod_text} — explains both anomalies simultaneously"
                        ),
                        modification_type=mod_type,
                        axioms_changed=list(axioms),
                        new_predictions=pred_templates,
                        simplicity_score=0.0,
                        explanatory_power=min(1.0, self._explanatory_factor(mod_type) + 0.15),
                        testability_score=self._testability_of(pred_templates),
                        generated_at=time.time(),
                    )
                    exp.simplicity_score = self._compute_simplicity(exp)
                    results.append(exp)
        return results
