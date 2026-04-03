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
from .discovery_memory import DiscoveryRecord, DiscoveryMemory


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

# Generic fallback templates
_GENERIC_TEMPLATES = [
    ("Cross-Domain: {v1} Pattern in {source}", "Astrophysics",
     "Test whether the {v1} pattern observed in {desc_context} "
     "also appears in {source} data. Structural comparison."),
    ("Follow-up: {finding_type} in {source}", "Astrophysics",
     "Systematic follow-up of {finding_type} signal: {desc}. "
     "Extended statistical characterization with larger sample."),
    ("Causal Probe: {v1} Mechanism", "Astrophysics",
     "Test causal mechanism behind {v1} relationship: {desc}. "
     "Intervention analysis + physical constraint checking."),
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

    def generate_from_discoveries(self, current_cycle: int,
                                   existing_names: set,
                                   max_new: int = 3) -> List[Dict]:
        """
        Generate new hypotheses from recent discoveries.

        Returns list of {name, domain, description, confidence, source_discovery_id}
        """
        candidates = []

        # 1. Direct follow-ups from strong discoveries (60% weight)
        strong = self.memory.get_strong_discoveries(
            min_strength=0.4, max_age_cycles=100, current_cycle=current_cycle)
        for disc in strong[:5]:
            hypotheses = self._generate_follow_up(disc, existing_names)
            for h in hypotheses:
                h["_weight"] = 0.6 * disc.strength
                h["source_discovery_id"] = disc.id
            candidates.extend(hypotheses)

        # 2. Explore untested variable pairs (25% weight)
        for source in ["exoplanets", "sdss", "gaia"]:
            untested = self.memory.get_unexplored_variable_pairs(source)
            if untested:
                # Pick the pair with highest individual variable affinity
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

        # 3. Cross-domain analogies (15% weight)
        hot = self.memory.get_hot_domains(top_n=2)
        if len(hot) >= 2:
            d1, d2 = hot[0][0], hot[1][0]
            d1_discoveries = [d for d in self.memory.discoveries if d.domain == d1]
            if d1_discoveries:
                latest = d1_discoveries[-1]
                name = f"Cross-Domain: {latest.finding_type.title()} from {d1}→{d2}"
                if name not in existing_names:
                    candidates.append({
                        "name": name,
                        "domain": d2,
                        "description": (
                            f"Does the {latest.finding_type} pattern observed in {d1} "
                            f"({latest.description[:80]}) have an analog in {d2}? "
                            f"Structural comparison across domains."
                        ),
                        "confidence": 0.12,
                        "finding_type": "cross_domain",
                        "data_source": latest.data_source,
                        "variables": latest.variables,
                        "_weight": 0.15,
                        "source_discovery_id": latest.id,
                    })

        # Sort by weight and take top N
        candidates.sort(key=lambda c: c.get("_weight", 0), reverse=True)

        # Deduplicate by name
        result = []
        seen_names = set(existing_names)
        for c in candidates[:max_new]:
            if c["name"] not in seen_names:
                seen_names.add(c["name"])
                # Clean internal fields
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

            # Avoid exact name duplicates
            if name in existing_names:
                name = f"{name} (v{self._get_version(name, existing_names)})"

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
