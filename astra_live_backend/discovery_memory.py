"""
ASTRA Live — Discovery Memory
Persistent learning memory that tracks what works, what's been found,
and guides future discovery directions. This is the core of self-improvement.

Every cycle the engine writes outcome signals here. On future cycles,
the memory feeds back into hypothesis generation, method selection, and
exploration strategy.
"""
import time
import json
import math
import numpy as np
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from typing import Optional, List, Dict, Tuple


@dataclass
class DiscoveryRecord:
    """A single scientific finding — used to seed new hypotheses."""
    id: str
    timestamp: float
    cycle: int
    hypothesis_id: str
    domain: str
    finding_type: str  # "scaling", "correlation", "bimodality", "anomaly", "causal", "intervention"
    variables: list  # e.g., ["log_period", "log_sma"]
    statistic: float
    p_value: float
    description: str
    data_source: str  # "exoplanets", "sdss", "gaia", "pantheon"
    strength: float  # 0-1, composite of significance, effect size, sample size
    follow_ups_generated: int = 0  # track how many hypotheses this spawned
    verified: bool = False  # did follow-up confirm?


@dataclass
class MethodOutcome:
    """Tracks the effectiveness of an investigation method."""
    method_name: str  # "_investigate_hubble", "run_causal_discovery", etc.
    hypothesis_id: str
    domain: str
    timestamp: float
    cycle: int
    data_points: int
    tests_run: int
    significant_results: int
    novelty_signals: int
    confidence_delta: float  # change in hypothesis confidence after evaluation
    success: bool  # did it produce actionable results?


@dataclass
class ExplorationState:
    """Tracks which data sources and variable combinations have been explored."""
    data_source: str
    variable_pairs_tested: dict  # "var1_var2" -> count
    last_explored: float
    total_explorations: int
    novelty_rate: float  # fraction of explorations that yielded novelty


class DiscoveryMemory:
    """
    Long-lived memory that enables self-improvement.

    Three feedback loops:
    1. Discovery → Hypothesis: Strong findings generate new hypotheses
    2. Method → Strategy: Track which investigation methods produce results
    3. Exploration → Coverage: Track what's been tried, prioritize unexplored
    """

    def __init__(self, max_records: int = 500):
        self.discoveries: deque[DiscoveryRecord] = deque(maxlen=max_records)
        self.method_outcomes: deque[MethodOutcome] = deque(maxlen=500)
        self.exploration: dict[str, ExplorationState] = {}
        self.generation_count = 0  # hypotheses generated from memory
        self._next_discovery_id = 1

        # Derived knowledge: which variable pairs tend to yield results
        self._variable_affinity: dict[str, float] = defaultdict(float)
        # Domain momentum: which domains are currently "hot"
        self._domain_momentum: dict[str, float] = defaultdict(float)

    # ── Recording ────────────────────────────────────────────────────

    def record_discovery(self, hypothesis_id: str, domain: str, finding_type: str,
                         variables: list, statistic: float, p_value: float,
                         description: str, data_source: str,
                         sample_size: int = 0) -> DiscoveryRecord:
        """Record a scientific finding for future hypothesis generation."""
        # Composite strength: significance × effect size proxy × log sample size
        sig_score = max(0, 1 - p_value) if p_value <= 1 else 0
        effect_score = min(1.0, abs(statistic) / 10.0)
        sample_score = min(1.0, math.log10(max(sample_size, 1)) / 4.0)  # log10(10000)=4
        strength = 0.4 * sig_score + 0.35 * effect_score + 0.25 * sample_score

        rec = DiscoveryRecord(
            id=f"D{self._next_discovery_id:04d}",
            timestamp=time.time(),
            cycle=0,  # set by caller
            hypothesis_id=hypothesis_id,
            domain=domain,
            finding_type=finding_type,
            variables=variables,
            statistic=statistic,
            p_value=p_value,
            description=description,
            data_source=data_source,
            strength=strength,
        )
        self._next_discovery_id += 1
        self.discoveries.append(rec)

        # Update variable affinity
        for v in variables:
            self._variable_affinity[v] += strength * 0.3

        # Update domain momentum
        self._domain_momentum[domain] += strength * 0.2

        # Update exploration state
        key = data_source
        if key not in self.exploration:
            self.exploration[key] = ExplorationState(
                data_source=key, variable_pairs_tested={},
                last_explored=time.time(), total_explorations=0, novelty_rate=0)
        es = self.exploration[key]
        es.total_explorations += 1
        es.last_explored = time.time()
        if strength > 0.5:
            es.novelty_rate = (es.novelty_rate * (es.total_explorations - 1) + 1) / es.total_explorations
        else:
            es.novelty_rate = (es.novelty_rate * (es.total_explorations - 1)) / es.total_explorations

        return rec

    def record_method_outcome(self, method_name: str, hypothesis_id: str, domain: str,
                               cycle: int, data_points: int, tests_run: int,
                               significant_results: int, novelty_signals: int,
                               confidence_delta: float, success: bool):
        """Record how well an investigation method performed."""
        self.method_outcomes.append(MethodOutcome(
            method_name=method_name,
            hypothesis_id=hypothesis_id,
            domain=domain,
            timestamp=time.time(),
            cycle=cycle,
            data_points=data_points,
            tests_run=tests_run,
            significant_results=significant_results,
            novelty_signals=novelty_signals,
            confidence_delta=confidence_delta,
            success=success,
        ))

    # ── Querying for hypothesis generation ───────────────────────────

    def get_strong_discoveries(self, min_strength: float = 0.5,
                                max_age_cycles: int = 50,
                                current_cycle: int = 0) -> List[DiscoveryRecord]:
        """Get discoveries strong enough to generate follow-up hypotheses."""
        results = []
        for d in self.discoveries:
            age = current_cycle - d.cycle
            if d.strength >= min_strength and age <= max_age_cycles:
                if d.follow_ups_generated < 3:  # cap follow-ups per discovery
                    results.append(d)
        results.sort(key=lambda d: d.strength, reverse=True)
        return results

    def get_unexplored_variable_pairs(self, data_source: str) -> List[Tuple[str, str]]:
        """
        Suggest variable pairs that haven't been tested together.
        This drives genuine exploration rather than re-testing known pairs.
        """
        source_vars = {
            "exoplanets": ["period", "mass", "radius", "distance", "eccentricity",
                           "stellar_mass", "stellar_radius", "metallicity", "transit_depth"],
            "sdss": ["redshift", "u_g", "g_r", "r_i", "u", "g", "r", "i", "z",
                     "petroRad_r", "absMag_u", "absMag_r"],
            "gaia": ["parallax", "gmag", "bp_rp", "bp_g", "g_rp", "pmra", "pmdec",
                     "radial_velocity", "teff_val", "logg_val"],
            "pantheon": ["zHD", "m_b", "m_b_err", "biasCor", "is_calibrator"],
        }
        vars_available = source_vars.get(data_source, [])
        if not vars_available:
            return []

        es = self.exploration.get(data_source)
        tested = set()
        if es:
            for pair_key in es.variable_pairs_tested:
                parts = pair_key.split("__")
                if len(parts) == 2:
                    tested.add((parts[0], parts[1]))
                    tested.add((parts[1], parts[0]))

        untested = []
        for i, v1 in enumerate(vars_available):
            for v2 in vars_available[i+1:]:
                if (v1, v2) not in tested:
                    untested.append((v1, v2))
        return untested

    def get_best_methods(self, domain: str = None) -> List[Tuple[str, float]]:
        """
        Rank investigation methods by their historical success rate.
        Used to prioritize method selection in the INVESTIGATE phase.
        """
        method_scores = defaultdict(lambda: {"successes": 0, "total": 0, "avg_delta": 0.0})
        for m in self.method_outcomes:
            if domain and m.domain != domain:
                continue
            key = m.method_name
            s = method_scores[key]
            s["total"] += 1
            if m.success:
                s["successes"] += 1
            s["avg_delta"] += m.confidence_delta

        ranked = []
        for method, stats in method_scores.items():
            if stats["total"] < 2:
                continue
            success_rate = stats["successes"] / stats["total"]
            avg_delta = stats["avg_delta"] / stats["total"]
            score = 0.6 * success_rate + 0.4 * min(1.0, max(0, avg_delta * 5))
            ranked.append((method, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def get_hot_domains(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Which domains have the most discovery momentum right now."""
        decayed = {}
        now = time.time()
        for domain, momentum in self._domain_momentum.items():
            # Decay by recent discoveries only
            recent = [d for d in self.discoveries
                      if d.domain == domain and now - d.timestamp < 3600 * 6]
            decayed[domain] = sum(d.strength for d in recent) if recent else momentum * 0.5
            self._domain_momentum[domain] = decayed[domain]

        ranked = sorted(decayed.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]

    def get_discovery_graph(self) -> Dict:
        """
        Build a graph of how discoveries relate to each other.
        Used for cross-domain linking based on shared structure, not randomness.
        """
        if len(self.discoveries) < 2:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []
        discoveries = list(self.discoveries)

        for d in discoveries[-50:]:  # last 50
            nodes.append({
                "id": d.id, "domain": d.domain, "type": d.finding_type,
                "strength": d.strength, "variables": d.variables,
            })

        # Connect discoveries that share variables or finding types
        for i, d1 in enumerate(discoveries[-50:]):
            for d2 in discoveries[-50:][i+1:]:
                shared_vars = set(d1.variables) & set(d2.variables)
                shared_type = d1.finding_type == d2.finding_type
                cross_domain = d1.domain != d2.domain

                if shared_vars or (shared_type and cross_domain):
                    weight = len(shared_vars) * 0.3 + (0.2 if shared_type else 0) + (0.3 if cross_domain else 0)
                    if weight > 0.2:
                        edges.append({
                            "source": d1.id, "target": d2.id,
                            "weight": round(weight, 3),
                            "reason": "shared_vars" if shared_vars else "shared_type_cross_domain",
                        })

        return {"nodes": nodes, "edges": edges}

    # ── Self-improvement metrics ─────────────────────────────────────

    def compute_improvement_metrics(self) -> Dict:
        """
        Meta-analysis: how well is the system improving over time?
        Compare early vs recent performance.
        """
        if len(self.method_outcomes) < 10:
            return {"status": "insufficient_data", "total_outcomes": len(self.method_outcomes)}

        outcomes = list(self.method_outcomes)
        mid = len(outcomes) // 2
        early = outcomes[:mid]
        recent = outcomes[mid:]

        def metrics_batch(batch):
            success_rate = sum(1 for m in batch if m.success) / max(len(batch), 1)
            avg_sig = sum(m.significant_results for m in batch) / max(len(batch), 1)
            avg_novelty = sum(m.novelty_signals for m in batch) / max(len(batch), 1)
            avg_delta = sum(m.confidence_delta for m in batch) / max(len(batch), 1)
            return {
                "success_rate": round(success_rate, 3),
                "avg_significant_results": round(avg_sig, 2),
                "avg_novelty_signals": round(avg_novelty, 2),
                "avg_confidence_delta": round(avg_delta, 4),
            }

        early_m = metrics_batch(early)
        recent_m = metrics_batch(recent)

        improvement = {}
        for key in early_m:
            delta = recent_m[key] - early_m[key]
            improvement[key] = {
                "early": early_m[key],
                "recent": recent_m[key],
                "delta": round(delta, 4),
                "improving": delta > 0,
            }

        return {
            "status": "ok",
            "total_discoveries": len(self.discoveries),
            "total_outcomes": len(self.method_outcomes),
            "hypotheses_generated_from_memory": self.generation_count,
            "metrics": improvement,
        }

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "discovery_count": len(self.discoveries),
            "method_outcome_count": len(self.method_outcomes),
            "exploration_sources": list(self.exploration.keys()),
            "generation_count": self.generation_count,
            "hot_domains": self.get_hot_domains(),
            "improvement": self.compute_improvement_metrics(),
            "top_variable_affinities": dict(sorted(
                self._variable_affinity.items(), key=lambda x: x[1], reverse=True
            )[:10]),
        }
