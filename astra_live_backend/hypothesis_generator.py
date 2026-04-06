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

    # Domains the engine should actively explore
    ALL_DOMAINS = ["Astrophysics", "Economics", "Climate", "Epidemiology", "Cross-Domain"]

    # Multi-domain exploration templates (non-astrophysics)
    _DOMAIN_EXPLORATION_TEMPLATES = {
        "Economics": [
            ("GDP-Inequality Nexus", "Economics",
             "Test Kuznets curve and Gini-GDP relationship across countries. "
             "Bayesian model comparison for linear vs inverted-U vs no relationship."),
            ("Trade Network Structure", "Economics",
             "Analyze global trade network topology. Test scale-free properties, "
             "hub-and-spoke structure, and trade flow power laws."),
            ("Inflation-Growth Dynamics", "Economics",
             "Investigate nonlinear inflation–growth relationship across economies. "
             "Threshold regression to find optimal inflation ranges."),
        ],
        "Climate": [
            ("CO2-Temperature Attribution", "Climate",
             "Quantify CO2 forcing contribution to observed warming using Granger "
             "causality and attribution analysis on instrumental records."),
            ("Extreme Weather Trends", "Climate",
             "Statistical analysis of extreme weather event frequency trends. "
             "Fit GEV distributions, test for changing return periods."),
            ("Sea Level Acceleration", "Climate",
             "Test for acceleration in sea level rise using tide gauge + satellite "
             "altimetry data. Quadratic vs linear trend comparison."),
        ],
        "Epidemiology": [
            ("Vaccination-Mortality Reduction", "Epidemiology",
             "Quantify causal effect of DPT/measles vaccination coverage on under-5 "
             "mortality rates. Instrumental variable + panel data approach."),
            ("Preston Curve Evolution", "Epidemiology",
             "Test whether the Preston curve (income vs life expectancy) has shifted "
             "upward over decades. Time-varying coefficient analysis."),
            ("Disease Burden Inequality", "Epidemiology",
             "Analyze concentration of disease burden by income quintile. "
             "Gini-like health inequality metrics across countries and time."),
        ],
        "Cross-Domain": [
            ("Wealth-Health-Climate Triad", "Cross-Domain",
             "Three-way interaction: GDP per capita, life expectancy, and CO2 emissions. "
             "Test Environmental Kuznets Curve with health co-benefits."),
            ("Urbanization Cascade", "Cross-Domain",
             "Urbanization → economic growth → emissions → health impacts causal chain. "
             "Structural equation modeling across 150+ countries."),
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

        # --- Domain diversification check ---
        # Count domain distribution in existing hypotheses (from hot_domains)
        hot = self.memory.get_hot_domains(top_n=5)
        dominant_domain = hot[0][0] if hot else "Astrophysics"
        dominant_weight = hot[0][1] if hot else 0
        total_weight = sum(w for _, w in hot) if hot else 1
        concentration = dominant_weight / max(total_weight, 1e-6)

        # If >80% concentration in one domain, force diversification
        force_diversify = concentration > 0.8

        if force_diversify:
            # Prioritize underrepresented domains
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
                            "_weight": 0.9,  # High weight to beat Astro follow-ups
                            "source_discovery_id": None,
                        })

        # 1. Direct follow-ups from strong discoveries (60% weight)
        # But skip the dominant domain if forced to diversify
        strong = self.memory.get_strong_discoveries(
            min_strength=0.4, max_age_cycles=100, current_cycle=current_cycle)
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

        # 3. Cross-domain analogies (15% weight)
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
        c_vars = set(candidate.get("variables", []))
        c_ft = candidate.get("finding_type", "")
        c_src = candidate.get("data_source", "")

        for existing in existing_hypotheses:
            e_vars = set(existing.get("variables", []))
            e_ft = existing.get("finding_type", "")
            e_src = existing.get("data_source", "")

            # Same finding type + same data source + >50% variable overlap = duplicate
            if c_ft == e_ft and c_src == e_src and c_vars and e_vars:
                overlap = len(c_vars & e_vars) / max(len(c_vars | e_vars), 1)
                if overlap >= 0.5:
                    return True
        return False
