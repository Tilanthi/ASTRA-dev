"""
ASTRA Live — Adaptive Strategist
Chooses investigation methods, test parameters, and exploration direction
based on historical performance from the discovery memory.

This replaces the hardcoded name-matching dispatch with data-driven strategy.
"""
import numpy as np
from typing import Optional, List, Dict, Tuple
from .discovery_memory import DiscoveryMemory


# Maps hypothesis characteristics to available investigation methods
_METHOD_REGISTRY = {
    "hubble": {
        "methods": ["_investigate_hubble", "run_causal_discovery",
                     "run_model_comparison", "run_scaling_discovery"],
        "data_source": "pantheon",
        "primary_vars": ["zHD", "m_b"],
    },
    "galaxy": {
        "methods": ["_investigate_galaxy", "run_causal_discovery",
                     "run_knowledge_isolation", "run_scaling_discovery"],
        "data_source": "sdss",
        "primary_vars": ["redshift", "u_g", "g_r"],
    },
    "exoplanet": {
        "methods": ["_investigate_exoplanets", "run_scaling_discovery",
                     "run_model_comparison", "run_dimensional_analysis"],
        "data_source": "exoplanets",
        "primary_vars": ["period", "mass", "radius"],
    },
    "stellar": {
        "methods": ["_investigate_stellar", "run_scaling_discovery",
                     "run_knowledge_isolation"],
        "data_source": "gaia",
        "primary_vars": ["gmag", "bp_rp", "parallax"],
    },
    "star_formation": {
        "methods": ["_investigate_star_formation", "run_causal_discovery",
                     "run_knowledge_isolation"],
        "data_source": "sdss",
        "primary_vars": ["u", "r", "redshift"],
    },
    "gravitational_waves": {
        "methods": ["_investigate_gw_events", "run_scaling_discovery",
                     "run_model_comparison", "run_knowledge_isolation"],
        "data_source": "gw_events",
        "primary_vars": ["chirp_mass", "total_mass", "mass_ratio"],
    },
    "cmb": {
        "methods": ["_investigate_cmb", "run_model_comparison",
                     "run_scaling_discovery"],
        "data_source": "planck_cmb",
        "primary_vars": ["ell", "cl"],
    },
    "transients": {
        "methods": ["_investigate_transients", "run_knowledge_isolation",
                     "run_causal_discovery"],
        "data_source": "ztf_transients",
        "primary_vars": ["mean_mag", "delta_mag", "ndet"],
    },
    "time_domain": {
        "methods": ["_investigate_time_domain", "run_scaling_discovery",
                     "run_knowledge_isolation"],
        "data_source": "tess_mast",
        "primary_vars": ["teff", "radius", "mass"],
    },
    "economics": {
        "methods": ["_investigate_economics", "run_causal_discovery",
                     "run_scaling_discovery"],
        "data_source": "world_bank",
        "primary_vars": ["gdp_per_capita", "year", "country"],
    },
    "climate": {
        "methods": ["_investigate_climate", "run_causal_discovery",
                     "run_scaling_discovery"],
        "data_source": "gistemp",
        "primary_vars": ["year", "temp_anomaly"],
    },
    "epidemiology": {
        "methods": ["_investigate_epidemiology", "run_causal_discovery",
                     "run_scaling_discovery"],
        "data_source": "who_gho",
        "primary_vars": ["life_expectancy", "year", "country"],
    },
    "generic": {
        "methods": ["_investigate_generic", "run_scaling_discovery",
                     "run_causal_discovery", "run_model_comparison"],
        "data_source": "gaia",
        "primary_vars": ["gmag"],
    },
}


class AdaptiveStrategist:
    """
    Selects investigation strategy based on:
    1. Historical method effectiveness (from memory)
    2. Hypothesis characteristics (domain, data source, variables)
    3. Exploration coverage (what's been tried)
    4. Novelty signals (where surprises are happening)
    """

    def __init__(self, memory: DiscoveryMemory):
        self.memory = memory
        self._exploration_bonus = 0.3  # weight for trying unexplored methods

    def classify_hypothesis(self, h) -> str:
        """Classify a hypothesis into a category for method selection."""
        name_lower = h.name.lower()
        if "hubble" in name_lower or "h0" in name_lower or "dark energy" in name_lower:
            return "hubble"
        elif "galaxy" in name_lower or "morphology" in name_lower or "sdss" in name_lower:
            return "galaxy"
        elif "exoplanet" in name_lower or "transit" in name_lower or "period" in name_lower:
            return "exoplanet"
        elif "hr" in name_lower or ("star" in name_lower and "formation" not in name_lower):
            return "stellar"
        elif "star formation" in name_lower or "scaling" in name_lower:
            return "star_formation"
        elif "gravitational" in name_lower or "gw" in name_lower or "merger" in name_lower or "black hole" in name_lower:
            return "gravitational_waves"
        elif "cmb" in name_lower or "cosmic microwave" in name_lower or "planck" in name_lower or "power spectrum" in name_lower:
            return "cmb"
        elif "transient" in name_lower or "supernova" in name_lower or "sn " in name_lower or "variable" in name_lower:
            return "transients"
        elif "tess" in name_lower or "kepler" in name_lower or "light curve" in name_lower:
            return "time_domain"
        elif "cluster" in name_lower or "richness" in name_lower:
            return "galaxy"
        elif "gdp" in name_lower or "trade" in name_lower or "inflation" in name_lower or "inequality" in name_lower or "nexus" in name_lower:
            return "economics"
        elif "co2" in name_lower or "temperature" in name_lower or "climate" in name_lower or "sea level" in name_lower or "weather" in name_lower or "extreme" in name_lower:
            return "climate"
        elif "vaccination" in name_lower or "mortality" in name_lower or "disease" in name_lower or "health" in name_lower or "preston" in name_lower or "burden" in name_lower or "life expectancy" in name_lower or "epidem" in name_lower:
            return "epidemiology"
        elif "econ" in name_lower or "funding" in name_lower:
            return "crossdomain"
        else:
            return "generic"

    def select_investigation_methods(self, h, cycle: int) -> List[str]:
        """
        Select which investigation methods to run for this hypothesis.

        Returns ordered list of method names, best-first.
        """
        category = self.classify_hypothesis(h)
        registry = _METHOD_REGISTRY.get(category, _METHOD_REGISTRY["generic"])

        methods = registry["methods"]

        # Get historical effectiveness for this domain
        best_methods = self.memory.get_best_methods(domain=h.domain)
        method_scores = {name: score for name, score in best_methods}

        # Score each available method
        scored = []
        for method in methods:
            base_score = method_scores.get(method, 0.5)  # default 0.5 for untested

            # Exploration bonus: prefer methods not yet tried on this hypothesis
            tried = any(
                m.method_name == method and m.hypothesis_id == h.id
                for m in self.memory.method_outcomes
            )
            if not tried:
                base_score += self._exploration_bonus

            # Recency penalty: slightly prefer methods not used in last few cycles
            recent_use = sum(
                1 for m in self.memory.method_outcomes
                if m.method_name == method and cycle - m.cycle < 5
            )
            base_score -= recent_use * 0.05

            scored.append((method, base_score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top 2-3 methods (based on hypothesis phase)
        if hasattr(h, 'phase') and str(h.phase).lower() in ('testing', 'validated'):
            max_methods = 3
        else:
            max_methods = 2

        return [m for m, _ in scored[:max_methods]]

    def select_test_parameters(self, h, method: str) -> Dict:
        """
        Select test parameters based on historical performance.
        Adjusts alpha, sample sizes, etc. based on what's worked.
        """
        params = {}

        category = self.classify_hypothesis(h)
        registry = _METHOD_REGISTRY.get(category, {})

        # Adaptive alpha: if many tests are marginal (0.01 < p < 0.1), tighten
        if hasattr(h, 'test_results') and h.test_results:
            marginal = sum(1 for t in h.test_results
                          if isinstance(t, dict) and 0.01 < t.get('p_value', 1.0) < 0.1)
            total = len(h.test_results)
            if marginal / max(total, 1) > 0.5:
                params["alpha"] = 0.01  # Tighten threshold
            else:
                params["alpha"] = 0.05
        else:
            params["alpha"] = 0.05

        # Variable selection: use memory to pick most promising variables
        if registry.get("primary_vars"):
            params["variables"] = registry["primary_vars"]

        # Data source hint
        if registry.get("data_source"):
            params["data_source"] = registry["data_source"]

        return params

    def should_explore_new_area(self, cycle: int) -> Tuple[bool, Optional[str]]:
        """
        Decide whether to explore a new data source or variable combination.
        Returns (should_explore, suggested_source).
        """
        # Check exploration coverage
        sources = ["exoplanets", "sdss", "gaia", "pantheon"]
        source_scores = []

        for source in sources:
            es = self.memory.exploration.get(source)
            if es is None:
                # Never explored — high priority
                source_scores.append((source, 1.0))
            else:
                # Score: freshness (how long since last explore) × inverse novelty rate
                age_hours = (cycle - es.last_explored) / 3600 if es.last_explored > 0 else 100
                freshness = min(1.0, age_hours / 24.0)
                novelty = es.novelty_rate
                score = 0.5 * freshness + 0.3 * novelty + 0.2 * (1.0 / max(es.total_explorations, 1))
                source_scores.append((source, score))

        source_scores.sort(key=lambda x: x[1], reverse=True)
        best_source, best_score = source_scores[0]

        return best_score > 0.4, best_source

    def get_strategy_summary(self) -> Dict:
        """Current strategy state for API/debugging."""
        return {
            "method_rankings": {
                domain: self.memory.get_best_methods(domain)
                for domain in ["Astrophysics", "Economics", "Climate"]
            },
            "hot_domains": self.memory.get_hot_domains(),
            "exploration_coverage": {
                source: {
                    "explored": es.total_explorations,
                    "novelty_rate": round(es.novelty_rate, 3),
                } for source, es in self.memory.exploration.items()
            },
        }
