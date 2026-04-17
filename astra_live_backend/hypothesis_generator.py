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
ASTRA Live — Hypothesis Generator
Generates new hypotheses from discovery memory, not from a hardcoded list.

The generator creates three types of follow-ups:
1. **Direct follow-up**: Test the same relation with different data/methods
2. **Causal probe**: Is the correlation causal? Run intervention analysis
3. **Cross-domain analog**: Does this pattern appear in another dataset?
"""
import time
import numpy as np
from typing import Optional, List, Dict, Tuple
from .graphpalace_memory import DiscoveryRecord, GraphPalaceMemory as DiscoveryMemory


# Template hypothesis descriptions by finding type and data source
_HYPOTHESIS_TEMPLATES = {
    ("scaling", "exoplanets"): [
        ("Exoplanet {v1}-{v2} Scaling Relation", "Astrophysics",
         "Test power-law scaling between {v1} and {v2} in confirmed exoplanets: "
         "{desc}. Derive scaling exponent and compare with theoretical predictions."),
    ],
    ("correlation", "sdss"): [
        ("SDSS {v1}-{v2} Correlation Structure", "Astrophysics",
         "Quantify the {v1}–{v2} correlation in SDSS DR18 galaxies: "
         "{desc}. Test for redshift dependence and morphological splitting."),
    ],
    ("bimodality", "sdss"): [
        ("Galaxy {v1} Bimodality Deep Dive", "Astrophysics",
         "Characterize bimodal {v1} distribution in SDSS: "
         "{desc}. Fit Gaussian mixture, identify green valley, track with redshift."),
    ],
    ("anomaly", "gaia"): [
        ("Gaia {v1} Anomaly Investigation", "Astrophysics",
         "Follow up on anomalous {v1} structure in Gaia DR3: "
         "{desc}. Quantify deviation from expected distribution."),
    ],
    ("causal", "sdss"): [
        ("Causal Structure: {v1} → {v2}", "Astrophysics",
         "Test causal direction between {v1} and {v2} in SDSS galaxies: "
         "{desc}. Use PC algorithm + intervention analysis."),
    ],
    ("correlation", "exoplanets"): [
        ("Exoplanet {v1}-{v2} Relation", "Astrophysics",
         "Investigate {v1}–{v2} correlation in exoplanets: "
         "{desc}. Bayesian model comparison for functional form."),
    ],
    ("correlation", "gaia"): [
        ("Gaia Stellar {v1}-{v2} Relation", "Astrophysics",
         "Characterize {v1}–{v2} relation in Gaia DR3: "
         "{desc}. Check for population-dependent slopes."),
    ],
    ("scaling", "sdss"): [
        ("Galaxy {v1}-{v2} Scaling", "Astrophysics",
         "Power-law scaling between {v1} and {v2} in galaxies: "
         "{desc}. Dimensional analysis + physical validation."),
    ],
    ("anomaly", "sdss"): [
        ("SDSS {v1} Anomaly Follow-up", "Astrophysics",
         "Investigate anomalous {v1} pattern in SDSS: "
         "{desc}. Statistical characterization of the deviation."),
    ],
    ("intervention", "sdss"): [
        ("Intervention Test: {v1}→{v2}", "Astrophysics",
         "Test causal claim do({v1})→{v2} in galaxy data: "
         "{desc}. do-calculus + FCI algorithm."),
    ],
    # Cross-domain templates
    ("correlation", "pantheon"): [
        ("Supernova {v1}-{v2} Relation", "Astrophysics",
         "Test {v1}–{v2} relation in Pantheon+ SNe Ia: "
         "{desc}. Cosmological implications."),
    ],
    ("scaling", "gaia"): [
        ("Stellar {v1}-{v2} Scaling Law", "Astrophysics",
         "Power-law scaling between {v1} and {v2} in Gaia stars: "
         "{desc}. Compare with stellar evolution models."),
    ],
}

# Generic fallback templates (astrophysics-focused)
_GENERIC_TEMPLATES = [
    ("Astronomy: {v1} Pattern in {source}", "Astrophysics",
     "Test whether the {v1} pattern observed in {desc_context} "
     "also appears in {source} data. Cross-dataset structural comparison."),
    ("Follow-up: {finding_type} in {source}", "Astrophysics",
     "Systematic follow-up of {finding_type} signal: {desc}. "
     "Extended statistical characterization with larger sample and improved controls."),
    ("Causal Probe: {v1} Mechanism", "Astrophysics",
     "Test causal mechanism behind {v1} relationship: {desc}. "
     "Intervention analysis + physical constraint checking + theoretical modeling."),
    ("Physics Interpretation: {v1}", "Physics",
     "Interpret {v1} phenomenon in terms of fundamental physics: {desc}. "
     "Test theoretical predictions against observational constraints."),
]

# Continuous exploration templates for self-evolutionary hypothesis generation
# These are used when the system needs to maintain a continuous stream of new hypotheses
_CONTINUOUS_EXPLORATION_TEMPLATES = [
    # Astrophysics exploratory hypotheses
    ("{source} {v1}-{v2} Cross-Correlation Analysis", "Astrophysics",
     "Explore potential cross-correlation between {v1} and {v2} in {source} data. "
     "Novel relationship investigation with multi-scale analysis techniques."),
    ("{source} {v1} Temporal Evolution Study", "Astrophysics",
     "Investigate temporal evolution of {v1} properties in {source} dataset. "
     "Time-series analysis + trend detection + correlation with external variables."),
    ("{source} {v1} Phase-Space Analysis", "Astrophysics",
     "Analyze {v1} distribution in multi-dimensional phase space using {source} data. "
     "Clustering analysis + manifold learning + density estimation techniques."),
    ("{source} {v1}-{v2} Non-Linear Relationship Test", "Astrophysics",
     "Test for non-linear relationships between {v1} and {v2} in {source} data. "
     "Polynomial regression + spline fitting + non-parametric correlation tests."),
    ("{source} {v1} Subgroup Discovery", "Astrophysics",
     "Discover meaningful subgroups within {v1} distribution using {source} data. "
     "Unsupervised clustering + feature importance analysis + subgroup characterization."),
    ("{source} Multi-Variable {v1} Model", "Astrophysics",
     "Build multi-variable predictive model for {v1} using {source} dataset. "
     "Feature selection + model comparison + validation with held-out data."),
    ("{source} {v1} Outlier Detection", "Astrophysics",
     "Identify and characterize outliers in {v1} distribution from {source} data. "
     "Statistical outlier detection + follow-up investigation + physical interpretation."),
    ("{source} {v1}-{v2} Conditional Analysis", "Astrophysics",
     "Analyze {v1}-{v2} relationship conditional on other variables in {source} data. "
     "Stratified analysis + interaction effects + confounder adjustment."),
    ("{source} {v1} Distribution Fitting", "Astrophysics",
     "Fit theoretical distributions to {v1} data from {source} dataset. "
     "Goodness-of-fit tests + parameter estimation + model comparison."),
    ("{source} {v1}-{v2} Causality Investigation", "Astrophysics",
     "Investigate potential causal relationship between {v1} and {v2} in {source} data. "
     "Causal inference algorithms + sensitivity analysis + robustness checks."),
]


class HypothesisGenerator:
    """
    Generates new hypotheses from the discovery memory.

    Strategy:
    - 60% of new hypotheses: follow-ups from strong discoveries
    - 25%: explore untested variable pairs
    - 15%: cross-domain structural analogies
    """

    def __init__(self, memory: DiscoveryMemory):
        self.memory = memory
        self._name_counter = {}  # avoid duplicate names

    # Domains the engine should actively explore (astrophysics-focused)
    ALL_DOMAINS = ["Astrophysics", "Physics", "Cosmology", "Mathematics"]

    # Astrophysics sub-domain exploration templates
    _DOMAIN_EXPLORATION_TEMPLATES = {
        "Astrophysics": [
            ("Stellar Evolution Calibrations", "Astrophysics",
             "Test stellar evolution model predictions against Gaia DR3 observations. "
             "Compare main sequence lifetimes, giant branch transitions, and white dwarf cooling tracks."),
            ("Galaxy Formation Scaling Laws", "Astrophysics",
             "Investigate galaxy scaling relations across mass, size, and metallicity. "
             "Test whether scaling exponents vary with redshift and environment."),
            ("Exoplanet Atmospheric Trends", "Astrophysics",
             "Search for correlations between exoplanet atmospheric properties and host star parameters. "
             "Test irradiation-mass-loss relationships and composition trends."),
        ],
        "Cosmology": [
            ("Hubble Constant Consistency Tests", "Cosmology",
             "Test H0 consistency across different distance ladders and methods. "
             "Compare CMB, SNe Ia, and strong lensing measurements for systematic offsets."),
            ("Growth Rate of Structure", "Cosmology",
             "Measure the growth rate of cosmic structure using redshift-space distortions. "
             "Test GR predictions against modified gravity alternatives."),
            ("Dark Energy Equation of State", "Cosmology",
             "Constrain w(a) parameterization using combined distance and growth rate data. "
             "Test consistency with ΛCDM w = -1 prediction."),
        ],
        "Physics": [
            ("Fundamental Constants Stability", "Physics",
             "Test temporal variation of fundamental constants using quasar absorption spectra. "
             "Search for variations in α, μ, and me/mp over cosmic time."),
            ("Lorentz Invariance Violation", "Physics",
             "Test Lorentz symmetry using high-energy astrophysical observations. "
             "Search for energy-dependent speed of light effects in GRB and AGN data."),
        ],
        "Mathematics": [
            ("Number Theory Pattern Discovery", "Mathematics",
             "Discover novel patterns in prime number distributions and arithmetic functions. "
             "Test conjectures using computational verification against large datasets."),
            ("Geometric Topology Invariants", "Mathematics",
             "Explore topological invariants of manifolds using computational algebraic topology. "
             "Search for relationships between Betti numbers and geometric properties."),
        ],
    }

    def generate_from_discoveries(self, current_cycle: int,
                                   existing_names: set,
                                   max_new: int = 3) -> List[Dict]:
        """
        Generate new hypotheses from recent discoveries.
        Enforces domain diversification to prevent single-domain concentration.

        Returns list of {name, domain, description, confidence, source_discovery_id}
        """
        candidates = []

        # --- Astrophysics sub-domain diversification check ---
        # Count domain distribution in existing hypotheses (from hot_domains)
        hot = self.memory.get_hot_domains(top_n=5)
        dominant_domain = hot[0][0] if hot else "Astrophysics"
        dominant_weight = hot[0][1] if hot else 0
        total_weight = sum(w for _, w in hot) if hot else 1
        concentration = dominant_weight / max(total_weight, 1e-6)

        # If >80% concentration in one sub-domain, force diversification within astrophysics
        force_diversify = concentration > 0.8

        if force_diversify:
            # Prioritize underrepresented astrophysics sub-domains
            represented = {d for d, _ in hot}
            missing_domains = [d for d in self.ALL_DOMAINS if d != dominant_domain]
            for domain in missing_domains:
                templates = self._DOMAIN_EXPLORATION_TEMPLATES.get(domain, [])
                for name, dom, desc in templates:
                    if name not in existing_names:
                        candidates.append({
                            "name": name,
                            "domain": dom,
                            "description": desc,
                            "confidence": 0.20,
                            "finding_type": "exploration",
                            "data_source": "multi",
                            "variables": [],
                            "_weight": 0.9,  # High weight to beat follow-ups
                            "source_discovery_id": None,
                        })

        # 1. Direct follow-ups from strong discoveries (60% weight)
        # But skip the dominant domain if forced to diversify
        strong = self.memory.get_strong_discoveries(
            min_strength=0.4, limit=20)
        for disc in strong[:5]:
            if force_diversify and disc.domain == dominant_domain:
                continue  # Skip dominant domain when diversifying
            hypotheses = self._generate_follow_up(disc, existing_names)
            for h in hypotheses:
                h["_weight"] = 0.6 * disc.strength
                h["source_discovery_id"] = disc.id
            candidates.extend(hypotheses)

        # 2. Explore untested variable pairs (25% weight)
        for source in ["exoplanets", "sdss", "gaia"]:
            if force_diversify:
                continue  # Skip astro exploration when diversifying
            untested = self.memory.get_unexplored_variable_pairs(source)
            if untested:
                scored = []
                for v1, v2 in untested[:20]:
                    score = (self.memory._variable_affinity.get(v1, 0) +
                             self.memory._variable_affinity.get(v2, 0))
                    scored.append((v1, v2, score))
                scored.sort(key=lambda x: x[2], reverse=True)

                for v1, v2, score in scored[:2]:
                    name = f"{source.upper()} {v1.title()}-{v2.title()} Exploration"
                    if name not in existing_names:
                        candidates.append({
                            "name": name,
                            "domain": "Astrophysics",
                            "description": (
                                f"Unexplored {v1}–{v2} relation in {source} data. "
                                f"Novel variable pair — no prior tests. "
                                f"Correlation analysis + physical interpretation."
                            ),
                            "confidence": 0.15 + min(0.2, score * 0.1),
                            "finding_type": "exploration",
                            "data_source": source,
                            "variables": [v1, v2],
                            "_weight": 0.25 * min(1.0, score + 0.3),
                            "source_discovery_id": None,
                        })

        # 3. Cross-dataset analogies (15% weight) - astrophysics only
        if len(hot) >= 2:
            d1, d2 = hot[0][0], hot[1][0]
            # Only generate analogies within astrophysics/physics/cosmology
            if d1 in self.ALL_DOMAINS and d2 in self.ALL_DOMAINS:
                d1_discoveries = [d for d in self.memory.discoveries if d.domain == d1]
                if d1_discoveries:
                    latest = d1_discoveries[-1]
                    name = f"Cross-Dataset: {latest.finding_type.title()} from {d1}→{d2}"
                    if name not in existing_names:
                        candidates.append({
                            "name": name,
                            "domain": d2,
                            "description": (
                                f"Does the {latest.finding_type} pattern observed in {d1} "
                                f"({latest.description[:80]}) have an analog in {d2}? "
                                f"Structural comparison across astrophysical datasets."
                            ),
                            "confidence": 0.12,
                            "finding_type": "cross_dataset",
                            "data_source": latest.data_source,
                            "variables": latest.variables,
                            "_weight": 0.15,
                            "source_discovery_id": latest.id,
                        })

        # Sort by weight and take top N
        candidates.sort(key=lambda c: c.get("_weight", 0), reverse=True)

        # Deduplicate by name AND semantic similarity
        result = []
        seen_names = set(existing_names)
        for c in candidates[:max_new * 3]:  # Check more candidates for dedup
            if len(result) >= max_new:
                break
            if c["name"] in seen_names:
                continue
            # Check semantic duplication against both existing and selected
            all_existing = list(result)  # already selected this round
            if self._is_semantic_duplicate(c, all_existing):
                continue
            seen_names.add(c["name"])
            c.pop("_weight", None)
            result.append(c)

        return result

    def _generate_follow_up(self, disc: DiscoveryRecord,
                             existing_names: set) -> List[Dict]:
        """Generate follow-up hypotheses from a single discovery."""
        results = []

        # Look for matching templates — try finding_type + data_source first
        key = (disc.finding_type, disc.data_source)
        templates = _HYPOTHESIS_TEMPLATES.get(key, [])

        if not templates:
            # Fall back to any template for this finding type
            for (ft, ds), tmpls in _HYPOTHESIS_TEMPLATES.items():
                if ft == disc.finding_type:
                    templates = tmpls
                    break

        if not templates:
            templates = _GENERIC_TEMPLATES

        v1 = disc.variables[0] if disc.variables else "unknown"
        v2 = disc.variables[1] if len(disc.variables) > 1 else "value"

        # Ensure data_source is one of the known sources for proper variable mapping
        source_labels = {
            "hubble": "Pantheon+", "galaxy": "SDSS", "exoplanet": "NASA Exoplanet",
            "stellar": "Gaia", "star_formation": "SDSS", "sdss": "SDSS",
            "exoplanets": "NASA Exoplanet", "gaia": "Gaia", "pantheon": "Pantheon+",
        }
        source_label = source_labels.get(disc.data_source, disc.data_source.upper())

        for name_t, domain_t, desc_t in templates:
            name = name_t.format(v1=v1.title(), v2=v2.title(),
                                 source=source_label,
                                 finding_type=disc.finding_type.title())
            desc = desc_t.format(v1=v1, v2=v2, desc=disc.description[:100],
                                 source=disc.data_source,
                                 finding_type=disc.finding_type,
                                 desc_context=disc.description[:60])

            # Avoid exact name duplicates — but cap at v2, no infinite versioning
            if name in existing_names:
                v2_name = f"{name} (v2)"
                if v2_name in existing_names:
                    continue  # Already have v1 and v2 — skip, don't create v3+
                name = v2_name

            results.append({
                "name": name,
                "domain": disc.domain,
                "description": desc,
                "confidence": min(0.4, disc.strength * 0.5),
                "finding_type": disc.finding_type,
                "data_source": disc.data_source,
                "variables": disc.variables,
            })

        return results

    def _get_version(self, base_name: str, existing: set) -> int:
        """Find next available version number for a hypothesis name."""
        for i in range(2, 20):
            candidate = f"{base_name} (v{i})"
            if candidate not in existing:
                return i
        return 2

    def _is_semantic_duplicate(self, candidate: Dict, existing_hypotheses: List[Dict]) -> bool:
        """
        Check if a candidate hypothesis is semantically too similar to existing ones.
        Prevents the v1-v12 duplication problem by checking variable overlap + finding_type.
        """
        c_name = candidate.get("name", "").lower()
        c_vars = set(candidate.get("variables", []))
        c_ft = candidate.get("finding_type", "")
        c_src = candidate.get("data_source", "")

        for existing in existing_hypotheses:
            e_name = existing.get("name", "").lower()
            e_vars = set(existing.get("variables", []))
            e_ft = existing.get("finding_type", "")
            e_src = existing.get("data_source", "")

            # CRITICAL FIX: Check for exact or near-exact name match FIRST
            # This catches theoretical hypotheses that have empty variables
            if c_name and e_name:
                # Exact match
                if c_name == e_name:
                    return True
                # Contains match (handles cases where one is substring of another)
                if c_name in e_name or e_name in c_name:
                    return True

            # For hypotheses with variables, use the original overlap check
            # Same finding type + same data source + >50% variable overlap = duplicate
            if c_ft == e_ft and c_src == e_src:
                # Handle case where both have variables
                if c_vars and e_vars:
                    overlap = len(c_vars & e_vars) / max(len(c_vars | e_vars), 1)
                    if overlap >= 0.5:
                        return True
                # Handle case where both have NO variables (exploration/theoretical)
                elif not c_vars and not e_vars:
                    # Same finding_type and data_source with no variables = likely duplicate
                    return True

        return False

    def generate_diversification_hypotheses(self, current_cycle: int,
                                          existing_names: set,
                                          max_new: int = 5) -> List[Dict]:
        """
        Generate hypotheses specifically for domain diversification.

        When one domain dominates (>70% of discoveries), this method
        generates hypotheses in underrepresented domains to balance
        the exploration.

        Returns list of {name, domain, description, confidence, source_discovery_id}
        """
        candidates = []

        # Get domain distribution
        hot = self.memory.get_hot_domains(top_n=10)
        if not hot:
            return candidates

        dominant_domain = hot[0][0] if hot else "Astrophysics"
        dominant_weight = hot[0][1] if hot else 0
        total_weight = sum(w for _, w in hot) if hot else 1
        concentration = dominant_weight / max(total_weight, 1e-6)

        # Only generate diversification hypotheses if concentration > 70%
        if concentration < 0.7:
            return candidates

        # Underrepresented domains
        represented = {d for d, _ in hot}
        underrepresented = [d for d in self.ALL_DOMAINS if d not in represented or d != dominant_domain]

        # Enhanced templates for Physics and Cosmology
        _PHYSICS_TEMPLATES = [
            ("Fundamental Constants Variation Test", "Physics",
             "Test whether fundamental constants (α, μ, me/mp) vary over cosmic time. "
             "Use quasar absorption spectra to measure fine-structure constant at high redshift."),
            ("Quantum Gravity Signatures", "Physics",
             "Search for quantum gravity effects in high-energy astrophysical phenomena. "
             "Test energy-dependent speed of light in GRB light curves and AGN variability."),
            ("Dark Matter Direct Detection", "Physics",
             "Analyze experimental constraints on WIMP dark matter cross-sections. "
             "Compare null results with theoretical predictions and identify allowed parameter space."),
            ("Neutrino Physics Constraints", "Physics",
             "Use neutrino oscillation data from IceCube and Super-Kamiokande to test "
             "mass hierarchy and CP violation in the lepton sector."),
            ("Modified Gravity Tests", "Physics",
             "Test deviations from General Relativity using strong-field gravity regimes. "
             "Analyzing pulsar timing and binary black hole mergers for GR violations."),
        ]

        _COSMOLOGY_TEMPLATES = [
            ("H0 Tension Resolution", "Cosmology",
             "Investigate systematic effects in Hubble constant measurements. "
             "Compare Cepheid, TRGB, and maser distance ladder methods for unaccounted systematics."),
            ("Early Universe Inflation", "Cosmology",
             "Test inflationary model predictions against CMB B-mode polarization data. "
             "Constrain tensor-to-scalar ratio and inflation energy scale."),
            ("Dark Energy Evolution", "Cosmology",
             "Test time-varying dark energy equation of state w(a). "
             "Use combined SN Ia, BAO, and cosmic chronometer data to break degeneracies."),
            ("Primordial Non-Gaussianity", "Cosmology",
             "Search for deviations from Gaussian initial conditions in CMB data. "
             "Constrain f_NL parameters to test single-field vs multi-field inflation."),
            ("Reionization History", "Cosmology",
             "Use high-redshift quasar spectra and CMB optical depth to constrain "
             "hydrogen reionization history and helium reionization timing."),
        ]

        # Combine templates
        diversification_templates = []
        for domain in underrepresented:
            if domain == "Physics":
                diversification_templates.extend(_PHYSICS_TEMPLATES)
            elif domain == "Cosmology":
                diversification_templates.extend(_COSMOLOGY_TEMPLATES)

        # Generate candidates with high weight
        for name, domain, desc in diversification_templates:
            if name not in existing_names:
                candidates.append({
                    "name": name,
                    "domain": domain,
                    "description": desc,
                    "confidence": 0.25,  # Higher confidence for exploratory
                    "finding_type": "exploration",
                    "data_source": "multi",
                    "variables": [],
                    "_weight": 1.0,  # Very high weight to override normal follow-ups
                    "source_discovery_id": None,
                })

        # Sort and return top candidates
        candidates.sort(key=lambda c: c.get("_weight", 0), reverse=True)
        result = []
        seen_names = set(existing_names)

        for c in candidates[:max_new]:
            if c["name"] in seen_names:
                continue
            c.pop("_weight", None)
            result.append(c)
            seen_names.add(c["name"])

        return result

    def generate_continuous_exploration(self, current_cycle: int,
                                       existing_names: set,
                                       max_new: int = 10) -> List[Dict]:
        """
        Generate hypotheses for continuous exploration - ensures ongoing hypothesis supply.

        This method is designed to maintain a continuous stream of new hypotheses even when
        discovery patterns are exhausted. It uses exploratory templates and creative combinations
        to ensure the system always has new hypotheses to investigate.

        Returns list of {name, domain, description, confidence, source_discovery_id}
        """
        candidates = []

        # Get recent discoveries to inspire exploration
        strong_discoveries = self.memory.get_strong_discoveries(min_strength=0.3, limit=10)

        # Get all data sources with available variables
        data_sources = ["sdss", "exoplanets", "gaia", "pantheon", "ligo", "cmb"]

        import random

        # Strategy 1: Generate from unexplored variable pairs
        for source in data_sources:
            if len(candidates) >= max_new:
                break

            # Get unexplored variable pairs for this source
            untested = self.memory.get_unexplored_variable_pairs(source)
            if not untested:
                continue

            # Use continuous exploration templates with variable pairs
            for v1, v2 in untested[:5]:  # Take first 5 untested pairs
                if len(candidates) >= max_new:
                    break

                # Select a template randomly
                template_idx = random.randint(0, len(_CONTINUOUS_EXPLORATION_TEMPLATES) - 1)
                name_t, domain_t, desc_t = _CONTINUOUS_EXPLORATION_TEMPLATES[template_idx]

                # Format the template
                source_labels = {
                    "sdss": "SDSS", "exoplanets": "NASA Exoplanet", "gaia": "Gaia",
                    "pantheon": "Pantheon+", "ligo": "LIGO", "cmb": "Planck CMB"
                }
                source_label = source_labels.get(source, source.upper())

                name = name_t.format(source=source_label, v1=v1.title(), v2=v2.title())
                desc = desc_t.format(source=source_label, v1=v1, v2=v2,
                                    desc_context=f"{source_label} dataset")

                # Check for exact name duplicates
                if name in existing_names:
                    # Try adding a version number
                    for i in range(2, 5):
                        versioned_name = f"{name} (v{i})"
                        if versioned_name not in existing_names:
                            name = versioned_name
                            break
                    else:
                        continue  # Skip if all versions exist

                candidates.append({
                    "name": name,
                    "domain": domain_t,
                    "description": desc,
                    "confidence": 0.15,  # Lower confidence for exploratory
                    "finding_type": "exploration",
                    "data_source": source,
                    "variables": [v1, v2],
                    "_weight": 0.5,  # Medium weight
                    "source_discovery_id": None,
                })

        # Strategy 2: If still not enough, generate from existing discoveries with new angles
        if len(candidates) < max_new and strong_discoveries:
            for disc in strong_discoveries[:5]:
                if len(candidates) >= max_new:
                    break

                # Generate creative follow-ups with new analysis angles
                analysis_angles = [
                    "Multi-Scale Analysis", "Cross-Correlation Study", "Phase-Space Exploration",
                    "Non-Linear Dynamics Test", "Information-Theoretic Analysis",
                    "Machine Learning Classification", "Causal Network Reconstruction",
                    "Temporal Evolution Tracking", "Subgroup Discovery", "Ensemble Modeling"
                ]

                angle = random.choice(analysis_angles)
                source_labels = {
                    "hubble": "Pantheon+", "galaxy": "SDSS", "exoplanet": "NASA Exoplanet",
                    "stellar": "Gaia", "star_formation": "SDSS", "sdss": "SDSS",
                    "exoplanets": "NASA Exoplanet", "gaia": "Gaia", "pantheon": "Pantheon+",
                }
                source_label = source_labels.get(disc.data_source, disc.data_source.upper())

                v1 = disc.variables[0] if disc.variables else "pattern"
                v2 = disc.variables[1] if len(disc.variables) > 1 else "property"

                name = f"{source_label} {v1.title()}-{v2.title()} {angle}"
                desc = (f"Apply {angle.lower()} to investigate {v1}-{v2} relationship in {source_label} data. "
                       f"Novel analytical approach to {disc.finding_type} pattern: {disc.description[:80]}...")

                # Check for duplicates
                if name in existing_names:
                    continue

                candidates.append({
                    "name": name,
                    "domain": disc.domain,
                    "description": desc,
                    "confidence": 0.12,  # Even lower for creative exploration
                    "finding_type": "exploration",
                    "data_source": disc.data_source,
                    "variables": disc.variables,
                    "_weight": 0.3,  # Lower weight for creative exploration
                    "source_discovery_id": disc.id,
                })

        # Strategy 3: Generate domain-specific exploratory hypotheses
        if len(candidates) < max_new:
            exploratory_templates = [
                ("{source} Deep Field Survey Analysis", "Astrophysics",
                 "Conduct deep analysis of {source} survey data to detect faint, rare objects. "
                 "Stacking analysis + sensitivity limits + completeness correction."),
                ("{source} Variability Study", "Astrophysics",
                 "Characterize variability properties in {source} time-domain data. "
                 "Period detection + variability classification + physical interpretation."),
                ("{source} Systematic Error Analysis", "Astrophysics",
                 "Investigate systematic errors and biases in {source} measurements. "
                 "Calibration analysis + uncertainty quantification + mitigation strategies."),
                ("{source} Population Synthesis Modeling", "Astrophysics",
                 "Build population synthesis models to explain {source} observations. "
                 "Bayesian inference + model comparison + parameter estimation."),
                ("{source} Machine Learning Classification", "Astrophysics",
                 "Apply machine learning algorithms to classify objects in {source} dataset. "
                 "Feature engineering + model training + validation + interpretation."),
            ]

            for source in data_sources[:3]:  # Limit to first 3 sources
                if len(candidates) >= max_new:
                    break

                source_labels = {
                    "sdss": "SDSS", "exoplanets": "NASA Exoplanet", "gaia": "Gaia",
                    "pantheon": "Pantheon+", "ligo": "LIGO", "cmb": "Planck CMB"
                }
                source_label = source_labels.get(source, source.upper())

                template_idx = random.randint(0, len(exploratory_templates) - 1)
                name_t, domain_t, desc_t = exploratory_templates[template_idx]

                name = name_t.format(source=source_label)
                desc = desc_t.format(source=source_label)

                # Check for duplicates
                if name in existing_names:
                    # Try adding a version number
                    for i in range(2, 5):
                        versioned_name = f"{name} (v{i})"
                        if versioned_name not in existing_names:
                            name = versioned_name
                            break
                    else:
                        continue

                candidates.append({
                    "name": name,
                    "domain": domain_t,
                    "description": desc,
                    "confidence": 0.10,  # Lowest for general exploration
                    "finding_type": "exploration",
                    "data_source": source,
                    "variables": [],
                    "_weight": 0.2,  # Lowest weight
                    "source_discovery_id": None,
                })

        # Sort by weight and return top candidates
        candidates.sort(key=lambda c: c.get("_weight", 0), reverse=True)
        result = []
        seen_names = set(existing_names)

        for c in candidates[:max_new]:
            if c["name"] in seen_names:
                continue
            c.pop("_weight", None)
            result.append(c)
            seen_names.add(c["name"])

        return result
