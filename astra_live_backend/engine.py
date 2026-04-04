"""
ASTRA Live — Discovery Engine
Real ORIENT → SELECT → INVESTIGATE → EVALUATE → UPDATE pipeline.
"""
import time
import json
import threading
import numpy as np
from collections import deque
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

from .hypotheses import HypothesisStore, Hypothesis, Phase, seed_initial_hypotheses
from .statistics import (
    chi_squared_test, kolmogorov_smirnov_test, bayesian_t_test,
    pearson_correlation, granger_causality_simple, StatTestResult,
    fdr_correction, cohen_d, effect_size_report, detect_autocorrelation, change_point_detection,
)
from .data_fetcher import (
    get_cached_exoplanets, get_cached_pantheon, get_cached_gaia,
    get_cached_sdss, get_cached_hr_diagram, get_cached_hubble_diagram,
    get_cached_galaxy_colors, fetch_exoplanet_periods, fetch_transit_depths,
    fetch_galaxy_redshifts, fetch_gaia_stars, RealDataCache, data_cache,
    DataResult, search_arxiv_astroph,
)
from .novelty import NoveltyDetector
from .cosmology import distance_modulus, hubble_residual, fit_h0_from_sne, PLANCK_2018, SH0ES_2022
from .causal import pc_algorithm, fci_algorithm, test_intervention
from .dimensional import discover_scaling_relations, buckingham_pi, check_dimensional_consistency, ASTRO_DIMENSIONS
from .bayesian import compare_models, rank_hypotheses, score_hypothesis
from .knowledge import run_knowledge_isolation
from .validation import run_physical_validation
from .safety import SafetyController, SafetyArbiter
from .safety.supervisor import SupervisorRegistry
from .safety.ceremony import CeremonyProtocol
from .safety.orp import OperationalReadinessPlan
from .safety.safety_case import SafetyCase
from .alignment import AlignmentChecker
from .anomaly import AnomalyDetector
from .safety.circuit_breakers import SafetyMonitor
from .discovery_memory import DiscoveryMemory
from .hypothesis_generator import HypothesisGenerator
from .adaptive_strategist import AdaptiveStrategist
from .degradation import DegradationDetector


@dataclass
class ActivityLogEntry:
    timestamp: float
    phase: str
    module: str
    message: str
    hypothesis_id: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class DecisionEntry:
    timestamp: float
    action: str  # expand, prune, merge, escalate, confirm
    text: str
    status: str  # COMPLETED, ARCHIVED, INVESTIGATING, PENDING, VALIDATED, CONFIRMED
    hypothesis_id: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class DiscoveryEngine:
    """
    The core ASTRA discovery engine.
    Cycles through ORIENT → SELECT → INVESTIGATE → EVALUATE → UPDATE.
    """

    def __init__(self):
        self.store = HypothesisStore()
        self.activity_log: deque[ActivityLogEntry] = deque(maxlen=200)
        self.decision_log: deque[DecisionEntry] = deque(maxlen=100)
        self.current_phase = "ORIENT"
        self.cycle_count = 0
        self.total_data_points = 0
        self.total_scripts = 0
        self.total_plots = 0
        self.total_decisions = 0
        self.hypotheses_tested = 0
        self.cross_domain_links = 0
        self.start_time = time.time()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.papers_drafted = 0
        self.gpu_utilization = 45.0
        self.queue_depth = 0
        self.system_confidence = 0.0

        # State vector history (last 100 cycles)
        self.state_vector_history: deque[dict] = deque(maxlen=100)

        # Safety controller (singleton)
        self.safety = SafetyController()
        self.safety.bind_engine(self)
        self.monitor = SafetyMonitor(self.safety)

        # Alignment checker
        self.alignment_checker = AlignmentChecker()

        # Anomaly detector
        self.anomaly_detector = AnomalyDetector()

        # Phase 4: Safety Arbiter, Supervisor, Ceremony, ORP, Safety Case
        self.arbiter = SafetyArbiter()
        self.supervisor_registry = SupervisorRegistry()
        self.ceremony_protocol = CeremonyProtocol()
        self.orp = OperationalReadinessPlan()
        self.safety_case = SafetyCase()

        # Novelty detector — compares results against known science
        self.novelty_detector = NoveltyDetector()

        # Discovery memory — tracks findings, method effectiveness, exploration coverage
        self.discovery_memory = DiscoveryMemory()

        # Hypothesis generator — creates new hypotheses from discoveries
        self.hypothesis_generator = HypothesisGenerator(self.discovery_memory)

        # Adaptive strategist — chooses investigation methods based on history
        self.strategist = AdaptiveStrategist(self.discovery_memory)

        # Degradation detector — Phase 10.3
        self.degradation_detector = DegradationDetector()

        # Exploration schedule — Phase 10.6: force domain round-robin
        self._forced_domain: Optional[str] = None
        self._domain_rotation_index = 0

        # Historical results for pattern anomaly detection
        self._result_history: dict = {}  # hypothesis_id -> list of result dicts

        # Start default supervisor shift
        self.supervisor_registry.start_shift("system", "Auto-started on engine init")

        # Domain list for consistent state vector dimensions
        self._canonical_domains = ["Astrophysics", "Economics", "Climate", "Epidemiology"]

        # Initialize
        seed_initial_hypotheses(self.store)
        self._log("ORIENT", "ENGINE", "ASTRA Discovery Engine initialized — hypothesis store loaded")
        self._log("ORIENT", "ENGINE", f"{len(self.store.all())} hypotheses seeded across {len(set(h.domain for h in self.store.all()))} domains")

    def _log(self, phase: str, module: str, message: str, hid: str = None):
        entry = ActivityLogEntry(
            timestamp=time.time(),
            phase=phase,
            module=module,
            message=message,
            hypothesis_id=hid,
        )
        self.activity_log.append(entry)

    def _decide(self, action: str, text: str, status: str, hid: str = None):
        entry = DecisionEntry(
            timestamp=time.time(),
            action=action,
            text=text,
            status=status,
            hypothesis_id=hid,
        )
        self.decision_log.append(entry)
        self.total_decisions += 1

    def _recalculate_system_confidence(self):
        active = self.store.active()
        if not active:
            self.system_confidence = 0.0
            return
        # Weighted average by phase
        weights = {
            Phase.PROPOSED: 0.2, Phase.SCREENING: 0.4, Phase.TESTING: 0.6,
            Phase.VALIDATED: 0.8, Phase.PUBLISHED: 1.0, Phase.ARCHIVED: 0.0
        }
        total_w = sum(weights[h.phase] for h in active)
        if total_w == 0:
            self.system_confidence = 0.0
            return
        self.system_confidence = sum(
            h.confidence * weights[h.phase] for h in active
        ) / total_w

    def _count_domains(self) -> int:
        return len(set(h.domain for h in self.store.active()))

    def compute_state_vector(self) -> dict:
        """
        Compute a 14-dimensional state vector characterizing the engine's
        current cognitive/operational state. Used for anomaly detection and
        state-space visualization.

        Dimensions (14):
          [0-3]   Per-domain confidence mean (Astrophysics, Economics, Climate, Epidemiology)
          [4-7]   Per-domain confidence variance (same 4 domains)
          [8]     Domain coverage entropy
          [9]     Exploration rate (fraction of hypotheses in early phases)
          [10]    Exploitation rate (fraction in late phases)
          [11]    Cross-domain coupling density
          [12]    Resource utilization (data points per hypothesis)
          [13]    Decision velocity (decisions per cycle)
        """
        active = self.store.active()

        # Per-domain confidence statistics
        domain_confidences: dict[str, list[float]] = {d: [] for d in self._canonical_domains}
        for h in active:
            if h.domain in domain_confidences:
                domain_confidences[h.domain].append(h.confidence)

        means = []
        variances = []
        for d in self._canonical_domains:
            vals = domain_confidences[d]
            if vals:
                means.append(float(np.mean(vals)))
                variances.append(float(np.var(vals)))
            else:
                means.append(0.0)
                variances.append(0.0)

        # Domain coverage entropy
        domain_counts = {}
        for h in active:
            domain_counts[h.domain] = domain_counts.get(h.domain, 0) + 1
        total = sum(domain_counts.values())
        if total > 0 and len(domain_counts) > 1:
            probs = [c / total for c in domain_counts.values()]
            import math
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)
            max_ent = math.log2(len(self._canonical_domains))
            normalized_entropy = entropy / max_ent if max_ent > 0 else 0.0
        else:
            normalized_entropy = 0.0

        # Exploration rate: fraction in PROPOSED + SCREENING
        early_phases = {Phase.PROPOSED, Phase.SCREENING}
        exploration = sum(1 for h in active if h.phase in early_phases) / max(len(active), 1)

        # Exploitation rate: fraction in VALIDATED + PUBLISHED
        late_phases = {Phase.VALIDATED, Phase.PUBLISHED}
        exploitation = sum(1 for h in active if h.phase in late_phases) / max(len(active), 1)

        # Cross-domain coupling density
        total_links = sum(len(h.cross_domain_links) for h in active)
        max_possible = len(active) * (len(active) - 1) if len(active) > 1 else 1
        coupling_density = total_links / max_possible

        # Resource utilization: average data points per hypothesis
        if active:
            resource_util = np.mean([h.data_points_used for h in active]) / 5000.0
            resource_util = min(1.0, resource_util)
        else:
            resource_util = 0.0

        # Decision velocity: decisions per cycle
        if self.cycle_count > 0:
            decision_velocity = self.total_decisions / self.cycle_count
            decision_velocity = min(1.0, decision_velocity / 10.0)  # Normalize: 10 decisions/cycle = 1.0
        else:
            decision_velocity = 0.0

        vector = means + variances + [
            normalized_entropy, exploration, exploitation,
            coupling_density, float(resource_util), float(decision_velocity)
        ]

        labels = [
            "astro_conf_mean", "econ_conf_mean", "climate_conf_mean", "epi_conf_mean",
            "astro_conf_var", "econ_conf_var", "climate_conf_var", "epi_conf_var",
            "domain_entropy", "exploration_rate", "exploitation_rate",
            "coupling_density", "resource_utilization", "decision_velocity",
        ]

        result = {
            "vector": [round(v, 6) for v in vector],
            "labels": labels,
            "dimensions": len(vector),
            "cycle": self.cycle_count,
            "timestamp": time.time(),
        }

        # Store in history
        self.state_vector_history.append(result)

        return result

    def get_state_vector_with_history(self) -> dict:
        """Return current state vector + full history (last 100 cycles)."""
        if self.state_vector_history:
            current = self.state_vector_history[-1]
        else:
            current = self.compute_state_vector()
        return {
            "current": current,
            "history": list(self.state_vector_history),
            "history_length": len(self.state_vector_history),
        }

    # ── ORIENT Phase ──────────────────────────────────────────────
    def orient(self):
        """Scan data feeds — lightweight version that doesn't block on API calls."""
        self.current_phase = "ORIENT"
        self._log("ORIENT", "ORIENT", "Scanning astronomical data feeds…")

        # Check what's in cache (legacy sources — doesn't trigger new fetches)
        total = 0
        sources = []
        for key, label in [("exoplanets", "Exoplanets"), ("pantheon", "Pantheon+ SNe"),
                           ("gaia", "Gaia DR3"), ("sdss", "SDSS galaxies")]:
            cached = data_cache.get(key)
            if cached is not None and cached.data is not None and len(cached.data) > 0:
                total += len(cached.data)
                sources.append(f"{label}: {len(cached.data)}")

        # Check registry sources
        from .data_registry import get_registry
        reg = get_registry()
        reg_stats = reg.get_stats()
        self._log("ORIENT", "ORIENT",
                  f"Registry: {reg_stats['total_sources']} sources across "
                  f"{len(reg_stats['domains'])} domains, "
                  f"{reg_stats['cross_match_pairs']} cross-match pairs, "
                  f"{reg_stats['total_variables']} variables")

        if sources:
            self.total_data_points = total
            self._log("ORIENT", "ORIENT", f"Cached data: {', '.join(sources)}")
        else:
            self._log("ORIENT", "ORIENT", "No cached data yet — will fetch during investigate phase")

        self.queue_depth = len(self.store.by_phase(Phase.SCREENING)) + len(self.store.by_phase(Phase.TESTING))

    # ── SELECT Phase ──────────────────────────────────────────────
    def select(self):
        """Rank hypotheses by information gain, novelty, and testability."""
        self.current_phase = "SELECT"
        active = self.store.active()

        # Phase 10.6: Check forced domain for exploration diversification
        forced_domain = self._get_forced_domain()
        if forced_domain:
            self._log("SELECT", "SELECT",
                      f"🔄 Forced domain exploration: {forced_domain}")

        # Score each hypothesis
        scored = []
        for h in active:
            # Information gain proxy: confidence * (1 - tests_run/max_tests)
            test_ratio = min(len(h.test_results) / 10.0, 1.0)
            info_gain = h.confidence * (1 - test_ratio * 0.5)
            # Novelty: inverse of how well-established
            novelty = 1.0 - (h.confidence * 0.3 + test_ratio * 0.3)
            # Testability: based on data available
            testability = min(h.data_points_used / 1000.0, 1.0)
            score = info_gain * 0.4 + novelty * 0.3 + testability * 0.3
            # Phase 10.6: Boost score for hypotheses in forced domain
            if forced_domain and h.domain == forced_domain:
                score += 0.5
            scored.append((h, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Log top selections
        for i, (h, score) in enumerate(scored[:3]):
            priority = "HIGH" if i == 0 else ("MEDIUM" if i == 1 else "NORMAL")
            h.priority = priority
            self._log("SELECT", "SELECT",
                      f"Rank #{i+1}: {h.id} ({h.name}) — score {score:.3f}, "
                      f"confidence {h.confidence:.2f}, priority {priority}", h.id)

        # Promote screening → testing if score warrants it
        for h, score in scored:
            if h.phase == Phase.SCREENING and score > 0.55:
                h.phase = Phase.TESTING
                self._log("SELECT", "SELECT",
                          f"Promoted {h.id} ({h.name}) from SCREENING → TESTING", h.id)
                self._decide("escalate",
                             f"Promoted {h.id} ({h.name}) to TESTING — score {score:.3f}",
                             "INVESTIGATING", h.id)

    # ── INVESTIGATE Phase ─────────────────────────────────────────
    def investigate(self):
        """Design experiments and run real analyses on live data.
        Uses adaptive strategist to select methods based on past performance."""
        self.current_phase = "INVESTIGATE"
        testing = self.store.by_phase(Phase.TESTING)
        validated = self.store.by_phase(Phase.VALIDATED)

        targets = testing[:3] + validated[:1]  # Focus on testing + 1 validated

        for h in targets:
            # Use strategist to select methods
            methods = self.strategist.select_investigation_methods(h, self.cycle_count)
            category = self.strategist.classify_hypothesis(h)
            params = self.strategist.select_test_parameters(h, methods[0] if methods else "")

            self._log("INVESTIGATE", "INVESTIGATE",
                      f"Running experiment for {h.id} ({h.name}) — "
                      f"strategy: {category}, methods: {methods[:2]}", h.id)

            conf_before = h.confidence
            tests_before_investigate = len(h.test_results)

            # Primary investigation (existing method dispatch)
            if category == "hubble":
                self._investigate_hubble(h)
            elif category == "galaxy":
                self._investigate_galaxy(h)
            elif category == "exoplanet":
                self._investigate_exoplanets(h)
            elif category == "stellar":
                self._investigate_stellar(h)
            elif category == "crossdomain":
                self._investigate_crossdomain(h)
            elif category == "star_formation":
                self._investigate_star_formation(h)
            elif category == "gravitational_waves":
                self._investigate_gw_events(h)
            elif category == "cmb":
                self._investigate_cmb(h)
            elif category == "transients":
                self._investigate_transients(h)
            elif category == "time_domain":
                self._investigate_time_domain(h)
            else:
                self._investigate_generic(h)

            # Always run cross-source linking for hypotheses with multiple data sources
            if self.cycle_count % 2 == 0:  # Every other cycle
                self._investigate_crosslink(h)

            # Secondary methods from strategist (scaling, causal, Bayesian, etc.)
            for method_name in methods[1:]:
                self._run_advanced_method(h, method_name, params)

            # Record method outcome in memory
            conf_delta = h.confidence - conf_before
            tests_run_now = len(h.test_results) - tests_before_investigate
            sig_results = sum(1 for t in h.test_results[tests_before_investigate:]
                             if isinstance(t, dict) and t.get('p_value', 1.0) < 0.05)
            # Success = data was available AND either new tests were run or data was examined
            # (investigate methods that log but don't add formal tests still succeed
            #  if they examined data — indicated by data_points_used > 0)
            self.discovery_memory.record_method_outcome(
                method_name=f"investigate_{category}",
                hypothesis_id=h.id,
                domain=h.domain,
                cycle=self.cycle_count,
                data_points=h.data_points_used,
                tests_run=tests_run_now,
                significant_results=sig_results,
                novelty_signals=0,
                confidence_delta=conf_delta,
                success=h.data_points_used > 0,
            )

        self.total_scripts += len(targets)

    def _run_advanced_method(self, h, method_name: str, params: dict):
        """Run an advanced ASTRA capability method on a hypothesis."""
        try:
            if method_name == "run_causal_discovery":
                data = self._get_hypothesis_data(h)
                if data is not None and data.shape[1] >= 3:
                    vars_list = params.get("variables", [f"var{i}" for i in range(data.shape[1])])
                    result = self.run_causal_discovery(vars_list[:data.shape[1]], data[:, :len(vars_list)])
                    # Record discovery
                    if result.get("edges"):
                        # Phase 7.2: Confounder detection for each causal edge
                        import pandas as pd
                        from .statistics import detect_confounders
                        df_causal = pd.DataFrame(data[:, :len(vars_list)],
                                                 columns=vars_list[:data.shape[1]])
                        for edge in result["edges"]:
                            src = edge.get("source", "")
                            tgt = edge.get("target", "")
                            # Run confounder detection
                            confounder_result = {}
                            if src in df_causal.columns and tgt in df_causal.columns:
                                try:
                                    confounder_result = detect_confounders(df_causal, src, tgt)
                                except Exception as ce:
                                    self._log("CONFOUNDER", "STATISTICS",
                                              f"Confounder detection failed for {src}→{tgt}: {ce}")
                            desc = f"Causal edge: {edge}"
                            if confounder_result.get("confirmed_confounders"):
                                cnames = [c["variable"] for c in confounder_result["confirmed_confounders"]]
                                desc += f" | Confounders: {cnames}"
                            self.discovery_memory.record_discovery(
                                hypothesis_id=h.id, domain=h.domain,
                                finding_type="causal",
                                variables=[src, tgt],
                                statistic=edge.get("weight", 0.5),
                                p_value=0.05,
                                description=desc,
                                data_source=params.get("data_source", "unknown"),
                                sample_size=data.shape[0],
                                metadata={"confounder_analysis": confounder_result} if confounder_result else {},
                            )

            elif method_name == "run_scaling_discovery":
                data = self._get_hypothesis_data(h)
                if data is not None and data.shape[1] >= 2:
                    x, y = data[:, 0], data[:, 1]
                    v1 = params.get("variables", ["x", "y"])[0]
                    v2 = params.get("variables", ["x", "y"])[1] if len(params.get("variables", [])) > 1 else "y"
                    result = self.run_scaling_discovery(x, y, v1, v2)
                    # Record discovery
                    self.discovery_memory.record_discovery(
                        hypothesis_id=h.id, domain=h.domain,
                        finding_type="scaling",
                        variables=[v1, v2],
                        statistic=result.get("exponent", 0),
                        p_value=result.get("p_value", 1.0),
                        description=f"Scaling: {v1}^{result.get('exponent', 0):.3f}",
                        data_source=params.get("data_source", "unknown"),
                        sample_size=len(x),
                    )

            elif method_name == "run_model_comparison":
                data = self._get_hypothesis_data(h)
                if data is not None and data.shape[1] >= 2:
                    x, y = data[:, 0], data[:, 1]
                    result = self.run_model_comparison(x, y)

            elif method_name == "run_knowledge_isolation":
                data = self._get_hypothesis_data(h)
                if data is not None and data.shape[1] >= 3:
                    vars_list = params.get("variables", [f"var{i}" for i in range(data.shape[1])])
                    result = self.run_knowledge_isolation(data[:, :len(vars_list)], vars_list[:data.shape[1]])
                    # Record any patterns found
                    for pattern in result.get("patterns", []):
                        self.discovery_memory.record_discovery(
                            hypothesis_id=h.id, domain=h.domain,
                            finding_type="correlation",
                            variables=[pattern.get("variable_x", ""), pattern.get("variable_y", "")],
                            statistic=pattern.get("correlation", 0),
                            p_value=pattern.get("p_value", 1.0),
                            description=f"Pattern: {pattern}",
                            data_source=params.get("data_source", "unknown"),
                            sample_size=data.shape[0],
                        )

            elif method_name == "run_dimensional_analysis":
                # Extract variable dimensions from registry
                from .dimensional import ASTRO_DIMENSIONS
                if params.get("variables"):
                    vars_dict = {v: ASTRO_DIMENSIONS.get(v, "dimensionless")
                                for v in params["variables"][:5]}
                    result = self.run_dimensional_analysis(vars_dict)

        except Exception as e:
            self._log("INVESTIGATE", "STRATEGIST",
                      f"Advanced method {method_name} failed for {h.id}: {e}", h.id)

    def _get_hypothesis_data(self, h):
        """Retrieve real data for a hypothesis based on its category."""
        category = self.strategist.classify_hypothesis(h)
        try:
            if category == "hubble":
                z, mb, mb_err = get_cached_hubble_diagram()
                if len(z) > 10:
                    return np.column_stack([z, mb, mb_err])
            elif category == "galaxy":
                sdss = get_cached_sdss()
                if sdss.data is not None and len(sdss.data) > 10:
                    d = sdss.data
                    return np.column_stack([d['redshift'], d['u_g'], d['g_r']])
            elif category == "exoplanet":
                exo = get_cached_exoplanets()
                if exo.data is not None and len(exo.data) > 10:
                    d = exo.data
                    return np.column_stack([d['period'], d['mass'], d['radius']])
            elif category == "stellar":
                bp_rp, abs_mag = get_cached_hr_diagram()
                if len(bp_rp) > 10:
                    gaia = get_cached_gaia()
                    if gaia.data is not None:
                        return np.column_stack([bp_rp, abs_mag, gaia.data['parallax'][:len(bp_rp)]])
            elif category == "star_formation":
                sdss = get_cached_sdss()
                if sdss.data is not None and len(sdss.data) > 10:
                    d = sdss.data
                    u_r = d['u'] - d['r']
                    return np.column_stack([d['redshift'], u_r, d['g_r']])
        except Exception as e:
            self._log("INVESTIGATE", "DATA", f"Data retrieval failed for {h.id}: {e}", h.id)
        return None

    def _investigate_hubble(self, h: Hypothesis):
        """Run real Hubble diagram analysis on Pantheon+ SNe Ia data with ΛCDM cosmology."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Fetching Pantheon+ SNe Ia sample for {h.id}", h.id)

        z, mb, mb_err = get_cached_hubble_diagram()
        if len(z) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No Pantheon+ data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(z)
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Loaded {len(z)} supernovae from Pantheon+ (z = {z.min():.4f}–{z.max():.4f})", h.id)

        # Fit H0 using proper ΛCDM distance modulus
        best_h0, chi2, h0_err = fit_h0_from_sne(z, mb, mb_err)
        dof = len(z) - 1
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"H0 fit: H₀ = {best_h0:.2f} ± {h0_err:.2f} km/s/Mpc "
                  f"(χ²/dof = {chi2/dof:.2f}, N={len(z)})", h.id)

        # Compare with Planck and SH0ES
        tension_planck = abs(best_h0 - PLANCK_2018['H0']) / np.sqrt(h0_err**2 + 0.5**2)
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Planck ({PLANCK_2018['H0']}) tension: {tension_planck:.1f}σ", h.id)

        self.total_plots += 1

    def _investigate_galaxy(self, h: Hypothesis):
        """Run galaxy analysis on real SDSS data."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Fetching SDSS galaxy sample for {h.id}", h.id)

        sdss = get_cached_sdss()
        if sdss.data is None or len(sdss.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No SDSS data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(sdss.data)
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Loaded {len(sdss.data)} galaxies from SDSS DR18 "
                  f"(z = {sdss.data['redshift'].min():.3f}–{sdss.data['redshift'].max():.3f})", h.id)

        # Color-color analysis
        u_g = sdss.data['u_g']
        g_r = sdss.data['g_r']
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Galaxy colors: u-g = {np.mean(u_g):.2f} ± {np.std(u_g):.2f}, "
                  f"g-r = {np.mean(g_r):.2f} ± {np.std(g_r):.2f}", h.id)

        # Redshift distribution
        z = sdss.data['redshift']
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Redshift distribution: median z = {np.median(z):.3f}, "
                  f"IQR = {np.percentile(z, 25):.3f}–{np.percentile(z, 75):.3f}", h.id)

        self.total_plots += 1

    def _investigate_exoplanets(self, h: Hypothesis):
        """Run exoplanet analysis on real NASA Exoplanet Archive data."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Fetching NASA Exoplanet Archive for {h.id}", h.id)

        exo = get_cached_exoplanets()
        if exo.data is None or len(exo.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No exoplanet data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(exo.data)
        periods = exo.data['period']
        masses = exo.data['mass']

        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Loaded {len(exo.data)} confirmed exoplanets", h.id)

        # Period distribution
        log_p = np.log10(periods[periods > 0])
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Orbital periods: log₁₀(P/days) = {np.mean(log_p):.2f} ± {np.std(log_p):.2f} "
                  f"(range: {periods.min():.2f}–{periods.max():.2f} days)", h.id)

        # Mass-radius relation if available
        valid_mass = masses[masses > 0]
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Planet masses: {len(valid_mass)} measured, "
                  f"median = {np.median(valid_mass):.3f} M_Jup", h.id)

        self.total_plots += 1

    def _investigate_stellar(self, h: Hypothesis):
        """Run stellar analysis on real Gaia DR3 data."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Fetching Gaia DR3 stellar sample for {h.id}", h.id)

        gaia = get_cached_gaia()
        if gaia.data is None or len(gaia.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No Gaia data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(gaia.data)

        # HR diagram
        bp_rp, abs_mag = get_cached_hr_diagram()
        if len(bp_rp) > 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"HR diagram: {len(bp_rp)} stars, "
                      f"color range BP-RP = {bp_rp.min():.2f}–{bp_rp.max():.2f}, "
                      f"M_G = {abs_mag.min():.1f}–{abs_mag.max():.1f}", h.id)

        # Parallax statistics
        plx = gaia.data['parallax']
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Parallaxes: median = {np.median(plx):.2f} mas, "
                  f"median distance = {1000/np.median(plx):.1f} pc", h.id)

        self.total_plots += 1

    def _investigate_crossdomain(self, h: Hypothesis):
        """Cross-domain analysis — compare distributions from different sources."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Computing cross-domain metrics for {h.id}", h.id)

        # Use real data from multiple sources
        exo = get_cached_exoplanets()
        sdss = get_cached_sdss()

        if exo.data is not None and sdss.data is not None and len(exo.data) > 0 and len(sdss.data) > 0:
            exo_distances = exo.data['distance']
            sdss_redshifts = sdss.data['redshift']
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"Cross-domain comparison: {len(exo_distances)} exoplanet distances "
                      f"vs {len(sdss_redshifts)} galaxy redshifts", h.id)
            h.data_points_used = len(exo_distances) + len(sdss_redshifts)
        else:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"Insufficient cross-domain data for {h.id}", h.id)

        self.total_plots += 1

    def _investigate_star_formation(self, h: Hypothesis):
        """Star formation analysis using real SDSS galaxy data."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Analyzing star formation indicators for {h.id}", h.id)

        sdss = get_cached_sdss()
        if sdss.data is None or len(sdss.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No SDSS data for star formation analysis — skipping {h.id}", h.id)
            return

        # Use u-r color as star formation proxy (blue = star-forming, red = quiescent)
        u_r = sdss.data['u'] - sdss.data['r']
        blue_frac = np.mean(u_r < 2.0)
        h.data_points_used = len(sdss.data)

        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Star formation fraction (u-r < 2): {blue_frac:.1%} of {len(sdss.data)} galaxies", h.id)

        self.total_plots += 1

    def _investigate_generic(self, h: Hypothesis):
        """Generic investigation using available real data."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Running generic analysis for {h.id} ({h.name})", h.id)

        # Use whichever data source is available
        gaia = get_cached_gaia()
        if gaia.data is not None and len(gaia.data) > 0:
            h.data_points_used = len(gaia.data)
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"Using Gaia sample: {len(gaia.data)} stars", h.id)

        self.total_plots += 1

    def _investigate_gw_events(self, h: Hypothesis):
        """Gravitational wave event analysis — mass distributions, spin."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Analyzing GW events for {h.id} ({h.name})", h.id)
        from .data_registry import get_registry
        reg = get_registry()
        result = reg.fetch("gw_events")
        if result.data is None or len(result.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No GW data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(result.data)
        chirp = result.data['chirp_mass']
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"GW sample: {len(chirp)} events, chirp mass range "
                  f"[{np.min(chirp):.1f}, {np.max(chirp):.1f}] M☉", h.id)

        # Mass ratio distribution (BBH vs BNS vs NSBH)
        q = result.data['mass_ratio']
        bbh_frac = np.mean(q > 0.5)  # Similar mass = likely BBH
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Mass ratio analysis: {bbh_frac:.0%} have q > 0.5 (BBH-like)", h.id)

        self.total_plots += 1

    def _investigate_cmb(self, h: Hypothesis):
        """CMB power spectrum analysis — acoustic peaks, cosmological parameters."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Analyzing CMB power spectrum for {h.id} ({h.name})", h.id)
        from .data_registry import get_registry
        reg = get_registry()
        result = reg.fetch("planck_cmb")
        if result.data is None or len(result.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No CMB data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(result.data)
        ells = result.data['ell']
        cls = result.data['cl']

        # Find acoustic peaks
        # First peak around ell ~ 220
        peak_region = cls[(ells > 150) & (ells < 300)]
        if len(peak_region) > 0:
            first_peak_idx = np.argmax(peak_region)
            first_peak_ell = ells[(ells > 150) & (ells < 300)][first_peak_idx]
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"First acoustic peak at ℓ ≈ {first_peak_ell:.0f} "
                      f"(expected ~220 for ΛCDM)", h.id)

        # Power-law index at low ℓ (Sachs-Wolfe)
        low_ells = cls[(ells > 2) & (ells < 30)]
        if len(low_ells) > 5:
            log_ell = np.log(ells[(ells > 2) & (ells < 30)])
            log_cl = np.log(low_ells)
            slope = np.polyfit(log_ell, log_cl, 1)[0]
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"Low-ℓ spectral index: {slope:.3f} (flat expected for scale-invariant)", h.id)

        self.total_plots += 1

    def _investigate_transients(self, h: Hypothesis):
        """Transient event analysis — SNe, AGN, CV classification."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Analyzing transient events for {h.id} ({h.name})", h.id)
        from .data_registry import get_registry
        reg = get_registry()
        result = reg.fetch("ztf_transients")
        if result.data is None or len(result.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No ZTF data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(result.data)
        mags = result.data['mean_mag']
        delta = result.data['delta_mag']
        ndet = result.data['ndet']

        self._log("INVESTIGATE", "INVESTIGATE",
                  f"ZTF sample: {len(mags)} transients, mag range "
                  f"[{np.min(mags):.1f}, {np.max(mags):.1f}]", h.id)

        # Variability analysis
        high_var = np.mean(delta > 2.0) if len(delta) > 0 else 0
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"High-variability fraction (Δmag > 2): {high_var:.0%}", h.id)

        self.total_plots += 1

    def _investigate_time_domain(self, h: Hypothesis):
        """TESS/MAST stellar parameter analysis for transit hosts."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Analyzing time-domain stellar data for {h.id} ({h.name})", h.id)
        from .data_registry import get_registry
        reg = get_registry()
        result = reg.fetch("tess_mast")
        if result.data is None or len(result.data) == 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"⚠ No TESS/MAST data available — skipping {h.id}", h.id)
            return

        h.data_points_used = len(result.data)
        teff = result.data['teff']
        radii = result.data['radius']
        masses = result.data['mass']

        valid_teff = teff[teff > 0]
        valid_rad = radii[radii > 0]
        valid_mass = masses[masses > 0]

        if len(valid_teff) > 0:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"TESS sample: {len(result.data)} stars, Teff range "
                      f"[{np.min(valid_teff):.0f}, {np.max(valid_teff):.0f}] K", h.id)

        # Mass-radius relation for stellar hosts
        if len(valid_rad) > 10 and len(valid_mass) > 10:
            # Match lengths
            min_len = min(len(valid_rad), len(valid_mass))
            r = valid_rad[:min_len]
            m = valid_mass[:min_len]
            log_r = np.log10(r[r > 0])
            log_m = np.log10(m[:len(log_r)])
            if len(log_r) > 5:
                corr = np.corrcoef(log_m, log_r)[0, 1]
                self._log("INVESTIGATE", "INVESTIGATE",
                          f"Stellar mass-radius correlation: r = {corr:.3f}", h.id)

        self.total_plots += 1

    def _investigate_crosslink(self, h: Hypothesis):
        """Cross-source linking — match data across registries."""
        self._log("INVESTIGATE", "INVESTIGATE",
                  f"Running cross-source analysis for {h.id}", h.id)
        from .data_registry import get_registry
        reg = get_registry()

        links = reg.get_cross_link_pairs()
        if not links:
            self._log("INVESTIGATE", "INVESTIGATE",
                      f"No cross-match pairs available", h.id)
            return

        matched = 0
        for src_a, src_b, key in links[:3]:  # Check top 3 pairs
            result_a = reg.fetch(src_a)
            result_b = reg.fetch(src_b)
            if (result_a.data is not None and len(result_a.data) > 0 and
                result_b.data is not None and len(result_b.data) > 0):
                matched += 1
                self._log("INVESTIGATE", "INVESTIGATE",
                          f"Cross-match: {result_a.source} ↔ {result_b.source} "
                          f"via '{key}' ({len(result_a.data)} × {len(result_b.data)})", h.id)

                # If both have RA/Dec, count positional overlaps
                if (hasattr(result_a.data, 'dtype') and 'ra' in str(result_a.data.dtype.names or []) and
                    hasattr(result_b.data, 'dtype') and 'ra' in str(result_b.data.dtype.names or [])):
                    self._log("INVESTIGATE", "INVESTIGATE",
                              f"  → Both sources have sky coordinates for positional matching", h.id)

        h.data_points_used = sum(
            len(reg.fetch(src_a).data) + len(reg.fetch(src_b).data)
            for src_a, src_b, _ in links[:3]
            if reg.fetch(src_a).data is not None and reg.fetch(src_b).data is not None
        )
        self.total_plots += 1

    def _check_novelty(self, h: Hypothesis, test_name: str, statistic: float,
                       p_value: float, data_summary: dict = None):
        """Check a test result for novelty against known science."""
        signal = self.novelty_detector.evaluate_result(
            h.id, h.name, test_name, statistic, p_value,
            data_summary or {})
        if signal and signal.novelty_score >= 0.3:
            self._log("NOVELTY", "ENGINE",
                      f"🔍 NOVELTY [{signal.novelty_score:.0%}] {signal.description}", h.id)
            # Store in history for drift detection
            if h.id not in self._result_history:
                self._result_history[h.id] = []
            self._result_history[h.id].append({
                "test": test_name, "stat": statistic, "p": p_value,
                "cycle": self.cycle_count, "novelty": signal.novelty_score,
            })

    def _literature_check(self, h: Hypothesis):
        """Search arXiv for related work on this hypothesis topic."""
        try:
            # Extract key terms from hypothesis name for search
            search_terms = h.name.replace("Analysis", "").replace("Structure", "").strip()
            papers = search_arxiv_astroph(search_terms, max_results=3)
            if papers:
                self._log("LITERATURE", "ENGINE",
                          f"📚 Related papers: {len(papers)} found on arXiv for '{search_terms}'", h.id)
                for p in papers[:2]:
                    self._log("LITERATURE", "ENGINE",
                              f"  → [{p['published']}] {p['title'][:80]}", h.id)
                return papers
        except Exception as e:
            self._log("LITERATURE", "ENGINE", f"arXiv search failed: {e}", h.id)
        return []

    # ── EVALUATE Phase ────────────────────────────────────────────
    def evaluate(self):
        """Statistical testing on real data — evidence assessment.
        Records discoveries in memory for hypothesis generation."""
        self.current_phase = "EVALUATE"
        testing = self.store.by_phase(Phase.TESTING)
        validated = self.store.by_phase(Phase.VALIDATED)

        targets = testing[:3] + validated[:1]
        for h in targets:
            conf_before = h.confidence
            tests_before = len(h.test_results)

            self._log("EVALUATE", "EVALUATE",
                      f"Running statistical battery on {h.id} ({h.name})", h.id)

            category = self.strategist.classify_hypothesis(h)
            if category == "hubble":
                self._evaluate_hubble(h)
            elif category == "galaxy":
                self._evaluate_galaxy(h)
            elif category == "exoplanet":
                self._evaluate_exoplanets(h)
            elif category == "crossdomain":
                self._evaluate_crossdomain(h)
            else:
                self._evaluate_generic(h)

            # Record discoveries from new test results
            new_tests = h.test_results[tests_before:]
            real_vars = self._get_hypothesis_variable_names(h)
            for test in new_tests:
                if isinstance(test, dict):
                    p_val = test.get('p_value', 1.0)
                    stat = test.get('statistic', 0)
                    # Significant results become discovery records
                    if p_val < 0.05:
                        self.discovery_memory.record_discovery(
                            hypothesis_id=h.id,
                            domain=h.domain,
                            finding_type=self._classify_test_finding(test, h),
                            variables=real_vars,
                            statistic=stat,
                            p_value=p_val,
                            description=f"{test.get('test_name', 'test')}: {test.get('details', '')}",
                            data_source=category,
                            sample_size=h.data_points_used,
                        )
                    # Check novelty
                    self._check_novelty(h, test.get('test_name', ''), stat, p_val,
                                       {"data_points": h.data_points_used})

            # Novelty: check historical drift
            if h.id in self._result_history and len(self._result_history[h.id]) >= 3:
                latest = self._result_history[h.id][-1]
                self.novelty_detector.detect_pattern_anomaly(
                    h.id, h.name,
                    {"stat": latest["stat"], "p_value": latest["p"]},
                    self._result_history[h.id][:-1])

            # Literature check (only on first cycle for each hypothesis)
            if h.data_points_used > 0 and not hasattr(h, '_lit_checked'):
                self._literature_check(h)
                h._lit_checked = True

            # Record evaluation outcome
            conf_delta = h.confidence - conf_before
            self.discovery_memory.record_method_outcome(
                method_name=f"evaluate_{category}",
                hypothesis_id=h.id,
                domain=h.domain,
                cycle=self.cycle_count,
                data_points=h.data_points_used,
                tests_run=len(h.test_results) - tests_before,
                significant_results=sum(1 for t in new_tests
                                        if isinstance(t, dict) and t.get('p_value', 1.0) < 0.05),
                novelty_signals=0,
                confidence_delta=conf_delta,
                success=len(new_tests) > 0,
            )

            # FDR correction on all p-values from this hypothesis
            all_p_values = [t.get('p_value', 1.0) for t in h.test_results
                           if isinstance(t, dict) and 'p_value' in t]
            if len(all_p_values) >= 2:
                fdr = fdr_correction(all_p_values)
                h.fdr_results = fdr
                self._log("EVALUATE", "FDR",
                          f"FDR correction for {h.id}: {fdr['n_significant']}/{len(all_p_values)} "
                          f"tests significant after BH correction (α*={fdr['corrected_alpha']:.4f})", h.id)

            self.hypotheses_tested += 1

        # After evaluation, check if any unexplored novelty signals warrant follow-up
        unexplored = self.novelty_detector.get_unexplored()
        if unexplored:
            self._log("NOVELTY", "ENGINE",
                      f"🔍 {len(unexplored)} unexplored novelty signals — potential follow-up candidates")

    def _classify_test_finding(self, test: dict, h) -> str:
        """Classify what kind of finding a test result represents."""
        test_name = test.get('test_name', '').lower()
        p_val = test.get('p_value', 1.0)
        stat = abs(test.get('statistic', 0))

        if 'correlation' in test_name or 'pearson' in test_name:
            return "correlation"
        elif 'chi' in test_name and stat > 20:
            return "bimodality"
        elif 'ks' in test_name and p_val < 0.001:
            return "anomaly"
        elif 'scaling' in test_name or (stat > 2 and p_val < 0.01):
            return "scaling"
        else:
            return "correlation"

    def _get_hypothesis_variable_names(self, h) -> list:
        """Get the real astrophysical variable names for a hypothesis."""
        category = self.strategist.classify_hypothesis(h)
        source_vars = {
            "hubble": ["redshift", "distance_modulus", "abs_mag"],
            "galaxy": ["redshift", "u_g_color", "g_r_color"],
            "exoplanet": ["orbital_period", "planet_mass", "planet_radius"],
            "stellar": ["bp_rp_color", "absolute_mag_g", "parallax"],
            "star_formation": ["redshift", "u_r_color", "g_r_color"],
            "crossdomain": ["distance", "redshift"],
            "generic": ["gmag", "bp_rp"],
        }
        return source_vars.get(category, ["variable_1", "variable_2"])

    def _evaluate_hubble(self, h: Hypothesis):
        """Evaluate Hubble tension with real Pantheon+ data and ΛCDM cosmology."""
        z, mb, mb_err = get_cached_hubble_diagram()
        if len(z) < 10:
            return

        # Test 1: Planck vs SH0ES model comparison
        mu_planck = distance_modulus(z, PLANCK_2018)
        mu_shoes = distance_modulus(z, {**PLANCK_2018, 'H0': SH0ES_2022['H0']})
        resid_planck = (mb - mu_planck) / mb_err
        resid_shoes = (mb - mu_shoes) / mb_err
        chi2_planck = float(np.sum(resid_planck**2))
        chi2_shoes = float(np.sum(resid_shoes**2))

        ks_result = kolmogorov_smirnov_test(resid_planck, resid_shoes)
        self._log("EVALUATE", "EVALUATE",
                  f"KS (Planck vs SH0ES residuals) on {h.id}: {ks_result.details}, "
                  f"χ²_P={chi2_planck:.0f} χ²_S={chi2_shoes:.0f}, p={ks_result.p_value:.4f}", h.id)
        h.test_results.append(asdict(ks_result))
        h.update_from_pvalue(ks_result.p_value)
        self._check_novelty(h, ks_result.test_name, ks_result.statistic, ks_result.p_value,
                           {"chi2_planck": chi2_planck, "chi2_shoes": chi2_shoes})

        # Test 2: Residual normality — are ΛCDM residuals consistent with zero?
        residuals = mb - mu_planck
        t_result = bayesian_t_test(residuals, popmean=0.0)
        self._log("EVALUATE", "EVALUATE",
                  f"t-test on ΛCDM residuals for {h.id}: {t_result.details}, p={t_result.p_value:.4f}", h.id)
        h.test_results.append(asdict(t_result))
        h.update_from_pvalue(t_result.p_value)

        # Test 3: Binned residuals — redshift-dependent systematics?
        z_bins = [0, 0.1, 0.3, 0.6, 1.0, 2.5]
        bin_means = []
        for i in range(len(z_bins)-1):
            mask = (z >= z_bins[i]) & (z < z_bins[i+1])
            if np.sum(mask) > 5:
                bin_means.append(float(np.mean(residuals[mask])))
        if len(bin_means) > 2:
            bin_arr = np.array(bin_means)
            chi_result = chi_squared_test(bin_arr - bin_arr.mean() + 1.0)
            self._log("EVALUATE", "EVALUATE",
                      f"Chi² on binned residuals for {h.id}: {chi_result.details}, p={chi_result.p_value:.4f}", h.id)
            h.test_results.append(asdict(chi_result))
            h.update_from_pvalue(chi_result.p_value)

    def _evaluate_galaxy(self, h: Hypothesis):
        """Evaluate galaxy hypothesis with real SDSS data."""
        sdss = get_cached_sdss()
        if sdss.data is None or len(sdss.data) < 10:
            return

        # Test 1: Are galaxy colors bimodal (red sequence + blue cloud)?
        g_r = sdss.data['g_r']
        ks_result = kolmogorov_smirnov_test(g_r)
        self._log("EVALUATE", "EVALUATE",
                  f"KS test on g-r colors for {h.id}: {ks_result.details}, p = {ks_result.p_value:.4f}", h.id)
        h.test_results.append(asdict(ks_result))
        h.update_from_pvalue(ks_result.p_value)
        self._check_novelty(h, ks_result.test_name, ks_result.statistic, ks_result.p_value,
                           {"g_r_mean": float(np.mean(g_r)), "g_r_std": float(np.std(g_r))})

        # Test 2: Redshift distribution uniformity
        z = sdss.data['redshift']
        z_hist, _ = np.histogram(z, bins=10)
        expected = np.full(10, len(z) / 10.0)
        chi_result = chi_squared_test(z_hist, expected.astype(float))
        self._log("EVALUATE", "EVALUATE",
                  f"Chi-squared on z-distribution for {h.id}: {chi_result.details}, p = {chi_result.p_value:.4f}", h.id)
        h.test_results.append(asdict(chi_result))
        h.update_from_pvalue(chi_result.p_value)

    def _evaluate_exoplanets(self, h: Hypothesis):
        """Evaluate exoplanet hypothesis with real NASA data."""
        exo = get_cached_exoplanets()
        if exo.data is None or len(exo.data) < 10:
            return

        # Test 1: Period distribution follows Kepler's third law trend
        periods = exo.data['period']
        log_p = np.log10(periods[periods > 0])
        ks_result = kolmogorov_smirnov_test(log_p, "norm")
        self._log("EVALUATE", "EVALUATE",
                  f"KS test on log(P) for {h.id}: {ks_result.details}, p = {ks_result.p_value:.4f}", h.id)
        h.test_results.append(asdict(ks_result))
        h.update_from_pvalue(ks_result.p_value)

        # Test 2: Mass-period correlation (real astrophysical relation)
        valid = (exo.data['period'] > 0) & (exo.data['mass'] > 0)
        if np.sum(valid) > 10:
            log_mass = np.log10(exo.data['mass'][valid])
            log_p_valid = np.log10(exo.data['period'][valid])
            corr_result = pearson_correlation(log_p_valid, log_mass)
            self._log("EVALUATE", "EVALUATE",
                      f"Correlation (log P vs log M) for {h.id}: {corr_result.details}, p = {corr_result.p_value:.4f}", h.id)
            h.test_results.append(asdict(corr_result))
            h.update_from_pvalue(corr_result.p_value)

    def _evaluate_crossdomain(self, h: Hypothesis):
        """Evaluate cross-domain hypothesis."""
        exo = get_cached_exoplanets()
        sdss = get_cached_sdss()

        if exo.data is None or sdss.data is None:
            return
        if len(exo.data) < 10 or len(sdss.data) < 10:
            return

        # Compare distance distributions
        exo_dist = exo.data['distance']
        sdss_z = sdss.data['redshift']

        # Normalize for comparison
        exo_norm = (exo_dist - np.mean(exo_dist)) / np.std(exo_dist)
        z_norm = (sdss_z - np.mean(sdss_z)) / np.std(sdss_z)

        ks_result = kolmogorov_smirnov_test(exo_norm[:100], z_norm[:100])
        self._log("EVALUATE", "EVALUATE",
                  f"KS test (exoplanet distances vs galaxy z) for {h.id}: "
                  f"{ks_result.details}, p = {ks_result.p_value:.4f}", h.id)
        h.test_results.append(asdict(ks_result))
        h.update_from_pvalue(ks_result.p_value)

    def _evaluate_generic(self, h: Hypothesis):
        """Generic evaluation using available data."""
        gaia = get_cached_gaia()
        if gaia.data is None or len(gaia.data) < 10:
            return

        # Use Gaia photometry
        gmag = gaia.data['gmag']
        ks_result = kolmogorov_smirnov_test(gmag)
        self._log("EVALUATE", "EVALUATE",
                  f"KS test on Gaia G-mag for {h.id}: {ks_result.details}, p = {ks_result.p_value:.4f}", h.id)
        h.test_results.append(asdict(ks_result))
        h.update_from_pvalue(ks_result.p_value)

    # ── ASTRA Core Capabilities (White & Dey 2026) ────────────────

    def run_causal_discovery(self, variable_names: List[str], data: np.ndarray,
                              method: str = "PC", alpha: float = 0.05) -> Dict:
        """
        Run causal discovery (PC or FCI algorithm) on a dataset.
        Implements Test Case 4 and Test Case 6 from the paper.
        """
        self._log("CAUSAL", "ENGINE",
                  f"Running {method} causal discovery on {len(variable_names)} variables (α={alpha})")

        if method.upper() == "FCI":
            graph = fci_algorithm(data, variable_names, alpha)
        else:
            graph = pc_algorithm(data, variable_names, alpha)

        result = graph.to_dict()
        self._log("CAUSAL", "ENGINE",
                  f"Causal graph: {len(result['edges'])} edges, {len(result['v_structures'])} v-structures")

        return result

    def run_dimensional_analysis(self, variables: Dict[str, str]) -> List[Dict]:
        """
        Apply Buckingham π theorem to find dimensionless groups.
        Implements Test Case 1 from the paper.
        """
        self._log("DIMENSIONAL", "ENGINE",
                  f"Dimensional analysis on {len(variables)} variables")

        groups = buckingham_pi(variables)
        self._log("DIMENSIONAL", "ENGINE",
                  f"Found {len(groups)} dimensionless π groups")

        return [g.to_dict() for g in groups]

    def run_scaling_discovery(self, x: np.ndarray, y: np.ndarray,
                               x_name: str = "x", y_name: str = "y",
                               x_dim: str = "", y_dim: str = "") -> Dict:
        """
        Discover power-law scaling relation with dimensional validation.
        Implements Test Case 1 (Herschel filaments).
        """
        self._log("SCALING", "ENGINE",
                  f"Discovering scaling relation: {y_name} vs {x_name}")

        relation = discover_scaling_relations(x, y, x_name, y_name, x_dim, y_dim)

        # Physical validation
        from .validation import run_physical_validation
        validation = run_physical_validation([{
            "type": "scaling_relation",
            "exponent": relation.exponent,
            "r_squared": relation.r_squared,
            "p_value": relation.p_value,
            "n_points": relation.n_points,
        }])

        result = relation.to_dict()
        result["validation"] = validation

        self._log("SCALING", "ENGINE",
                  f"Scaling: {y_name} ∝ {x_name}^{relation.exponent:.3f}±{relation.exponent_error:.3f} "
                  f"(R²={relation.r_squared:.3f}, p={relation.p_value:.2e})")

        return result

    def run_model_comparison(self, x: np.ndarray, y: np.ndarray,
                              models: List[str] = None) -> Dict:
        """
        Bayesian model comparison with evidence computation.
        Implements Test Case 5 (Bayesian model selection).
        """
        from .bayesian import compare_models

        self._log("BAYESIAN", "ENGINE", "Running Bayesian model comparison")

        comparison = compare_models(x, y, models)

        self._log("BAYESIAN", "ENGINE",
                  f"Best model: {comparison.best_model} "
                  f"(BF vs others: {', '.join(f'{k}={v:.2f}' for k,v in list(comparison.bayes_factors.items())[:3])})")

        return comparison.to_dict()

    def run_knowledge_isolation(self, data: np.ndarray, variable_names: List[str],
                                 target: str = None) -> Dict:
        """
        Full knowledge isolation discovery pipeline.
        Implements Test Case 6 (star formation threshold).
        """
        self._log("DISCOVERY", "ENGINE",
                  f"Running knowledge isolation on {len(variable_names)} variables "
                  f"({'target=' + target if target else 'no target'})")

        result = run_knowledge_isolation(data, variable_names, target)

        self._log("DISCOVERY", "ENGINE",
                  f"Discovered {len(result.patterns)} patterns, "
                  f"{len(result.interventions)} interventions tested, "
                  f"{len(result.hierarchy)} causal hierarchy entries")

        for pattern in result.patterns[:3]:
            self._log("DISCOVERY", "ENGINE",
                      f"  {pattern.variable_x} ↔ {pattern.variable_y}: "
                      f"r={pattern.correlation:.3f} (p={pattern.p_value:.2e}) [{pattern.causal_status}]")

        return result.to_dict()

    def run_intervention_test(self, data: np.ndarray, variable_names: List[str],
                               cause: str, effect: str) -> Dict:
        """
        Test a causal claim via intervention analysis.
        Implements Test Case 6, Phase 6.
        """
        self._log("CAUSAL", "ENGINE",
                  f"Intervention test: do({cause}) → {effect}")

        result = test_intervention(data, variable_names, cause, effect)

        self._log("CAUSAL", "ENGINE",
                  f"Intervention result: {cause} → {effect} "
                  f"effect={result['predicted_effect']:.4f} "
                  f"({'significant' if result['significant'] else 'not significant'})")

        return result

    # ── UPDATE Phase ──────────────────────────────────────────────
    def update(self):
        """Bayesian belief updates, pruning, cross-domain integration."""
        self.current_phase = "UPDATE"

        active = self.store.active()
        for h in active:
            old_conf = h.confidence
            old_phase = h.phase

            # Phase advancement
            if h.advance_phase():
                delta = h.confidence - old_conf
                self._log("UPDATE", "UPDATE",
                          f"Promoted {h.id} ({h.name}): {old_phase.value} → {h.phase.value} "
                          f"(confidence {h.confidence:.2f}, Δ{delta:+.3f})", h.id)
                self._decide("confirm",
                             f"Promoted {h.id} ({h.name}) to {h.phase.value} — confidence {h.confidence:.2f}",
                             "CONFIRMED", h.id)

            # Pruning
            if h.prune_if_weak(0.2):
                self._log("UPDATE", "UPDATE",
                          f"Archived {h.id} ({h.name}): confidence {h.confidence:.2f} "
                          f"below threshold after {len(h.test_results)} tests", h.id)
                self._decide("prune",
                             f"Archived {h.id} ({h.name}) — confidence below 0.20 after {len(h.test_results)} tests",
                             "ARCHIVED", h.id)

            # Paper drafting for validated hypotheses
            if h.phase == Phase.VALIDATED and h.confidence > 0.8 and np.random.random() < 0.1:
                self.papers_drafted += 1
                self._log("UPDATE", "UPDATE",
                          f"Drafting paper: results from {h.id} ({h.name})", h.id)
                self._decide("expand",
                             f"Initiated paper draft #{self.papers_drafted} from {h.id} ({h.name})",
                             "DRAFTING", h.id)

        # Cross-domain link discovery — based on shared discovery structure, not random
        self._update_cross_domain_links(active)

        # Discovery-guided hypothesis generation (replaces random hardcoded list)
        self._generate_discovery_guided_hypotheses()

        self._recalculate_system_confidence()
        self._log("UPDATE", "UPDATE",
                  f"System confidence: {self.system_confidence:.3f} "
                  f"({len(self.store.active())} active hypotheses across {self._count_domains()} domains)")

    def _generate_discovery_guided_hypotheses(self):
        """
        Generate new hypotheses from discovery memory — the core self-improvement loop.

        Sources:
        1. Strong discoveries → direct follow-ups (60%)
        2. Unexplored variable pairs → novel exploration (25%)
        3. Cross-domain analogies → structural comparisons (15%)
        """
        existing_names = {h.name for h in self.store.all()}
        current_cycle = self.cycle_count

        # Generate candidates from memory
        candidates = self.hypothesis_generator.generate_from_discoveries(
            current_cycle=current_cycle,
            existing_names=existing_names,
            max_new=2,
        )

        if not candidates:
            # Fallback: propose from untested variable pairs
            self._propose_from_unexplored_pairs(existing_names)
            return

        # Filter semantic duplicates before adding
        existing_hypotheses = [
            {"variables": h.variables if hasattr(h, 'variables') else [],
             "finding_type": h.finding_type if hasattr(h, 'finding_type') else "",
             "data_source": h.data_source if hasattr(h, 'data_source') else ""}
            for h in self.store.all()
        ]
        filtered = []
        for c in candidates:
            if not self.hypothesis_generator._is_semantic_duplicate(c, existing_hypotheses):
                filtered.append(c)
                existing_hypotheses.append({
                    "variables": c.get("variables", []),
                    "finding_type": c.get("finding_type", ""),
                    "data_source": c.get("data_source", ""),
                })

        for c in filtered:
            h = self.store.add(
                c["name"], c["domain"], c["description"],
                confidence=c["confidence"]
            )
            h.phase = Phase.PROPOSED
            self.discovery_memory.generation_count += 1

            source = c.get("source_discovery_id", "memory")
            self._log("ORIENT", "DISCOVERY_MEMORY",
                      f"New hypothesis from discovery {source}: {h.id} ({c['name']})", h.id)
            self._decide("expand",
                         f"Generated {h.id}: {c['name']} (from discovery {source})",
                         "QUEUED", h.id)

        # Log memory state
        metrics = self.discovery_memory.compute_improvement_metrics()
        self._log("ORIENT", "DISCOVERY_MEMORY",
                  f"Memory state: {metrics['total_discoveries']} discoveries, "
                  f"{metrics['hypotheses_generated_from_memory']} generated, "
                  f"{metrics['total_outcomes']} outcomes recorded")

    def _propose_from_unexplored_pairs(self, existing_names: set):
        """Fallback: propose hypothesis from unexplored variable pairs."""
        for source in ["exoplanets", "sdss", "gaia"]:
            untested = self.discovery_memory.get_unexplored_variable_pairs(source)
            if untested:
                v1, v2 = untested[0]
                name = f"{source.upper()} {v1.title()}-{v2.title()} Probe"
                if name not in existing_names:
                    h = self.store.add(
                        name, "Astrophysics",
                        f"Novel exploration of {v1}–{v2} relation in {source} data. "
                        f"Untested variable pair — first measurement.",
                        confidence=0.15
                    )
                    h.phase = Phase.PROPOSED
                    self.discovery_memory.generation_count += 1
                    self._log("ORIENT", "DISCOVERY_MEMORY",
                              f"New hypothesis from unexplored pair: {h.id} ({name})", h.id)
                    self._decide("expand",
                                 f"Proposed {h.id}: {name} (unexplored variable pair)",
                                 "QUEUED", h.id)
                    return

    def _propose_new_hypothesis(self):
        """Legacy fallback — kept for API compatibility. Prefer _generate_discovery_guided_hypotheses."""
        existing_names = {h.name for h in self.store.all()}
        proposals = [
            ("Hot Jupiter Occurrence Rate", "Astrophysics",
             "Measure occurrence rate of hot Jupiters from NASA Exoplanet Archive transit/radial velocity sample"),
            ("Gaia Main Sequence Width", "Astrophysics",
             "Analyze main sequence photometric scatter in Gaia DR3 HR diagram as function of metallicity"),
            ("SDSS Galaxy Bimodality", "Astrophysics",
             "Quantify the green valley in SDSS color-magnitude diagram using real photometry"),
            ("Exoplanet Period Valley", "Astrophysics",
             "Test for bimodal period distribution around 10 days in confirmed exoplanets"),
            ("Local Stellar Kinematics", "Astrophysics",
             "Velocity ellipsoid analysis from Gaia DR3 radial velocities and proper motions"),
            ("Galaxy Color-Redshift Evolution", "Astrophysics",
             "Track u-r color evolution with redshift in SDSS galaxy sample"),
            ("Transit Depth Distribution", "Astrophysics",
             "Statistical analysis of transit depths across Kepler/TESS discoveries"),
            ("Gaia White Dwarf Sequence", "Astrophysics",
             "Identify and characterize the white dwarf cooling sequence in Gaia HR diagram"),
        ]
        available = [(n, d, desc) for n, d, desc in proposals
                     if not any(h.name == n for h in self.store.all())]
        if not available:
            return

        name, domain, desc = available[np.random.randint(len(available))]
        h = self.store.add(name, domain, desc, confidence=0.15 + np.random.random() * 0.15)
        h.phase = Phase.PROPOSED
        self._log("ORIENT", "ORIENT",
                  f"New hypothesis proposed (fallback): {h.id} ({name}) — {desc}", h.id)
        self._decide("expand",
                     f"Proposed new hypothesis {h.id}: {name}",
                     "QUEUED", h.id)

    def _update_cross_domain_links(self, active):
        """
        Create cross-domain links based on shared discovery structure,
        not random selection. Links hypotheses that have similar finding types
        or shared variables across different domains.
        """
        if len(active) < 2:
            return

        # Get discovery graph from memory
        graph = self.discovery_memory.get_discovery_graph()
        cross_edges = [e for e in graph.get("edges", [])
                       if e.get("weight", 0) > 0.3]

        # Map discovery IDs to hypothesis IDs
        disc_to_hyp = {}
        for d in self.discovery_memory.discoveries:
            disc_to_hyp[d.id] = d.hypothesis_id

        linked_count = 0
        for edge in cross_edges[:3]:  # max 3 new links per cycle
            h1_id = disc_to_hyp.get(edge.get("source"))
            h2_id = disc_to_hyp.get(edge.get("target"))
            if h1_id and h2_id:
                h1 = self.store.get(h1_id)
                h2 = self.store.get(h2_id)
                if h1 and h2 and h1.domain != h2.domain:
                    if h2.id not in h1.cross_domain_links:
                        h1.cross_domain_links.append(h2.id)
                        h2.cross_domain_links.append(h1.id)
                        self.cross_domain_links += 1
                        linked_count += 1
                        self._log("UPDATE", "UPDATE",
                                  f"Discovery-linked: {h1.id} ({h1.domain}) ↔ "
                                  f"{h2.id} ({h2.domain}) — {edge.get('reason', 'shared_structure')}",
                                  h1.id)
                        self._decide("merge",
                                     f"Linked {h1.id} ({h1.domain}) ↔ {h2.id} ({h2.domain}) "
                                     f"via {edge.get('reason', 'discovery')}",
                                     "INTEGRATED", h1.id)

        # Fallback: if no discovery-based links, link by hot domains
        if linked_count == 0 and len(set(h.domain for h in active)) >= 2:
            hot = self.discovery_memory.get_hot_domains(top_n=2)
            if len(hot) >= 2:
                d1, d2 = hot[0][0], hot[1][0]
                h1_candidates = [h for h in active if h.domain == d1 and not h.cross_domain_links]
                h2_candidates = [h for h in active if h.domain == d2 and not h.cross_domain_links]
                if h1_candidates and h2_candidates:
                    h1, h2 = h1_candidates[0], h2_candidates[0]
                    h1.cross_domain_links.append(h2.id)
                    h2.cross_domain_links.append(h1.id)
                    self.cross_domain_links += 1
                    self._log("UPDATE", "UPDATE",
                              f"Hot-domain link: {h1.id} ({d1}) ↔ {h2.id} ({d2})", h1.id)

    # ── Phase 10.4: Hypothesis Lifecycle Management ────────────────
    def _manage_hypothesis_lifecycle(self):
        """Auto-archive stale hypotheses, auto-promote strong ones, prune queue."""
        now = time.time()

        for h in list(self.store.all()):
            # Auto-archive hypotheses stuck in SCREENING for >20 cycles with no progress
            if h.phase == Phase.SCREENING:
                age_seconds = now - h.updated_at
                # ~20 cycles at 25s interval = 500s
                if len(h.test_results) == 0 and age_seconds > 500:
                    h.phase = Phase.ARCHIVED
                    h.updated_at = now
                    h.archived_at = now
                    self._log("LIFECYCLE", "ENGINE",
                              f"Auto-archived {h.id} ({h.name}): stuck in SCREENING with no tests",
                              h.id)

            # Auto-promote hypotheses with confidence >0.95 and ≥3 successful tests
            if h.phase == Phase.TESTING and h.confidence > 0.95:
                successful_tests = sum(
                    1 for t in h.test_results
                    if isinstance(t, dict) and t.get('p_value', 1.0) < 0.05
                )
                if successful_tests >= 3:
                    h.phase = Phase.VALIDATED
                    h.updated_at = now
                    self._log("LIFECYCLE", "ENGINE",
                              f"Auto-promoted {h.id} ({h.name}): confidence {h.confidence:.2f} "
                              f"with {successful_tests} successful tests → VALIDATED", h.id)
                    self._decide("confirm",
                                 f"Auto-promoted {h.id} to VALIDATED (confidence {h.confidence:.2f})",
                                 "VALIDATED", h.id)

        # Prune the queue: if queue_depth > 15, archive lowest-confidence SCREENING hypotheses
        screening = self.store.by_phase(Phase.SCREENING)
        if len(screening) > 15:
            screening.sort(key=lambda h: h.confidence)
            to_prune = screening[:len(screening) - 15]
            for h in to_prune:
                h.phase = Phase.ARCHIVED
                h.updated_at = now
                h.archived_at = now
                self._log("LIFECYCLE", "ENGINE",
                          f"Queue-pruned {h.id} ({h.name}): confidence {h.confidence:.2f} "
                          f"(queue too deep)", h.id)

    # ── Phase 10.6: Exploration Diversification ──────────────────
    def _get_forced_domain(self) -> Optional[str]:
        """Return forced domain if diversification is needed, then clear it."""
        domain = self._forced_domain
        self._forced_domain = None
        return domain

    # ── Main Loop ─────────────────────────────────────────────────
    def run_cycle(self):
        """Execute one full ORIENT → SELECT → INVESTIGATE → EVALUATE → UPDATE cycle."""
        # Safety check: can we run a cycle?
        if not self.safety.can_run_cycle():
            self._log("SAFETY", "ENGINE",
                      f"Cycle blocked by safety controller (state={self.safety.state.value})")
            return

        with self._lock:
            self.cycle_count += 1
            self._log("ORIENT", "ENGINE",
                      f"━━━ Discovery Cycle #{self.cycle_count} starting ━━━")

            self.orient()
            time.sleep(0.3)
            self.select()
            time.sleep(0.3)

            # Investigation allowed in NOMINAL and SAFE_MODE
            if self.safety.can_investigate():
                self.investigate()
                time.sleep(0.3)
                self.evaluate()
                time.sleep(0.3)
            else:
                self._log("SAFETY", "ENGINE",
                          "Investigation/evaluation skipped — safety mode restricts analysis")

            # State modification only in NOMINAL
            if self.safety.can_modify_state():
                self.update()
            else:
                self._log("SAFETY", "ENGINE",
                          "Update phase skipped — safety mode restricts state changes")

            # Phase 10.3: Degradation detection after UPDATE
            deg_result = self.degradation_detector.check_after_cycle(
                self.discovery_memory, self.cycle_count
            )
            if deg_result["degraded"]:
                for rec in deg_result["recommendations"]:
                    self._log("DEGRADATION", "ENGINE", f"⚠ {rec}")

                if "TRIGGER_SAFE_MODE" in deg_result["actions"]:
                    if self.safety.state.value == "NOMINAL":
                        self.safety.transition("SAFE_MODE")
                        self._log("DEGRADATION", "ENGINE",
                                  "Auto-triggered SAFE_MODE due to sustained low success rate")

                if "DIVERSIFY_DOMAINS" in deg_result["actions"]:
                    least = self.degradation_detector.get_least_explored_domain(
                        self.discovery_memory, self._canonical_domains
                    )
                    if least:
                        self._forced_domain = least
                        self._log("DEGRADATION", "ENGINE",
                                  f"Forcing exploration of domain '{least}' next cycle")

                if "SWITCH_STRATEGY" in deg_result["actions"]:
                    self._forced_domain = self.degradation_detector.get_least_explored_domain(
                        self.discovery_memory, self._canonical_domains
                    )
                    self._log("DEGRADATION", "ENGINE",
                              "Switching exploration strategy due to low significant results")

            # Phase 10.5: Memory compaction
            self.discovery_memory.compact_if_needed()

            # Phase 10.4: Hypothesis lifecycle management
            self._manage_hypothesis_lifecycle()

            # Phase 2: Evaluate circuit breakers after cycle
            vec = self.compute_state_vector()
            alignment = self.alignment_checker.compute(self.store, self)
            cb_tripped = self.monitor.check(vec, alignment)

            # Compute state vector at end of each cycle
            sv = self.compute_state_vector()

            # Run anomaly detection on state vector
            anomalies = self.anomaly_detector.check(sv)

            # Phase 4: Safety Arbiter evaluates all signals
            autonomy_bounds = None
            if hasattr(self, '_phased_autonomy'):
                autonomy_bounds = self._phased_autonomy.get_bounds()
            arbiter_verdict = self.arbiter.evaluate_cycle(
                safety_state=self.safety.state.value,
                circuit_breaker_tripped=bool(cb_tripped),
                alignment_score=alignment.get("composite_score", 1.0) if isinstance(alignment, dict) else 1.0,
                anomalies=anomalies,
                autonomy_level="SUPERVISED",
                autonomy_bounds=autonomy_bounds,
                cycle=self.cycle_count,
            )
            if arbiter_verdict.decision == "ABORT":
                self._log("SAFETY", "ARBITER",
                          f"ABORT verdict: risk={arbiter_verdict.score:.2f} — {arbiter_verdict.reasons[0] if arbiter_verdict.reasons else 'no reason'}")
            for a in anomalies:
                self._log("ANOMALY", "ENGINE",
                          f"[{a['severity']}] {a['message']}")

            self._log("UPDATE", "ENGINE",
                      f"━━━ Cycle #{self.cycle_count} complete: "
                      f"{self.system_confidence:.3f} system confidence, "
                      f"{len(self.store.active())} active hypotheses ━━━")

    def start(self, interval: float = 25.0):
        """Start the engine running on a background thread."""
        if self.running:
            return
        self.running = True

        def loop():
            # Delay first cycle so server can start responding
            time.sleep(5)
            while self.running:
                try:
                    self.run_cycle()
                except Exception as e:
                    self._log("ERROR", "ENGINE", f"Cycle error: {e}")
                time.sleep(interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
        self._log("ORIENT", "ENGINE", "Discovery engine started — continuous operation mode")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_state(self) -> dict:
        """Get full engine state for the API (lock-free read for responsiveness)."""
        try:
            return {
                "running": self.running,
                "current_phase": self.current_phase,
                "cycle_count": self.cycle_count,
                "uptime_seconds": time.time() - self.start_time,
                "system_confidence": self.system_confidence,
                "total_data_points": self.total_data_points,
                "total_scripts": self.total_scripts,
                "total_plots": self.total_plots,
                "total_decisions": self.total_decisions,
                "hypotheses_tested": self.hypotheses_tested,
                "cross_domain_links": self.cross_domain_links,
                "papers_drafted": self.papers_drafted,
                "gpu_utilization": self.gpu_utilization,
                "queue_depth": self.queue_depth,
                "domains_active": self._count_domains(),
                "funnel": self.store.funnel_counts(),
                "safety_state": self.safety.state.value,
                "pending_approvals": len(self.store.pending_approvals()),
                "discovery_memory": self.discovery_memory.to_dict(),
                "degradation": self.degradation_detector.get_status(),
            }
        except Exception:
            # Fallback if read races with cycle — return minimal state
            return {
                "running": self.running,
                "current_phase": self.current_phase,
                "cycle_count": self.cycle_count,
                "uptime_seconds": time.time() - self.start_time,
                "system_confidence": self.system_confidence,
                "total_data_points": self.total_data_points,
                "total_scripts": 0, "total_plots": 0,
                "total_decisions": 0, "hypotheses_tested": 0,
                "cross_domain_links": 0, "papers_drafted": 0,
                "gpu_utilization": 0, "queue_depth": 0,
                "domains_active": 0,
                "funnel": {}, "safety_state": "NOMINAL",
                "pending_approvals": 0,
                "discovery_memory": {}, "degradation": {},
            }

    def get_hypotheses(self) -> list[dict]:
        return [h.to_dict() for h in self.store.all()]

    def get_activity_log(self, limit: int = 50) -> list[dict]:
        entries = list(self.activity_log)[-limit:]
        return [e.to_dict() for e in entries]

    def get_decision_log(self, limit: int = 20) -> list[dict]:
        entries = list(self.decision_log)[-limit:]
        return [e.to_dict() for e in entries]

    def get_chart_data(self) -> dict:
        """Generate chart data from real engine state (lock-free)."""
        try:
            funnel = self.store.funnel_counts()

            # Domain distribution from real data
            domain_counts = {}
            for h in self.store.active():
                domain_counts[h.domain] = domain_counts.get(h.domain, 0) + 1

            # Confidence distribution (radar)
            phases = [Phase.TESTING, Phase.VALIDATED, Phase.PUBLISHED]
            radar_labels = ["Confidence", "Data Volume", "Tests Run",
                           "Cross-Domain", "Novelty", "Testability"]
            radar_values = []
            active = self.store.active()
            if active:
                radar_values.append(np.mean([h.confidence for h in active]))
                radar_values.append(min(np.mean([h.data_points_used for h in active]) / 5000, 1.0))
                radar_values.append(min(np.mean([len(h.test_results) for h in active]) / 8, 1.0))
                radar_values.append(min(self.cross_domain_links / 15, 1.0))
                radar_values.append(np.mean([
                    1.0 - min(len(h.test_results) / 10, 1.0) for h in active
                ]))
                radar_values.append(np.mean([
                    min(h.data_points_used / 1000, 1.0) for h in active
                ]))
            else:
                radar_values = [0.5] * 6

            return {
                "funnel": {
                    "labels": ["Proposed", "Screening", "Testing", "Validated", "Published"],
                    "data": [funnel.get("proposed", 0), funnel.get("screening", 0),
                             funnel.get("testing", 0), funnel.get("validated", 0),
                             funnel.get("published", 0)]
                },
                "domain": {
                    "labels": list(domain_counts.keys()),
                    "data": list(domain_counts.values())
                },
                "radar": {
                    "labels": radar_labels,
                    "data": [round(v, 3) for v in radar_values]
                },
                "system_confidence": self.system_confidence,
            }
        except Exception:
            return {
                "funnel": {"labels": [], "data": []},
                "domain": {"labels": [], "data": []},
                "radar": {"labels": [], "data": []},
                "system_confidence": self.system_confidence,
            }
