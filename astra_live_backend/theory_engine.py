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
ASTRA Live — Theory Engine
Orchestrates all theoretical framework infrastructure (Phases 1–3).

Integrates:
  Phase 1: Theory objects, Contradiction detection, Symbolic dimensional analysis
  Phase 2: Abstraction (hypothesis → theory), Cross-domain analogy, Symmetry/universality
  Phase 3: Abductive reasoning, Active experiment design, Theory self-consistency

Called from the main DiscoveryEngine every N cycles.
Results are available via the /api/theory/* endpoints.
"""
import time
import threading
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

# ── Phase 1 imports ────────────────────────────────────────────
try:
    from .theory import Theory, TheoryStore, TheoryPhase
    from .contradiction import ContradictionDetector, Contradiction
    from .symbolic_dimensional import (
        BuckinghamPiGenerator, UniversalExponentMatcher,
        CandidateEquationSet, ScalingRelationGenerator
    )
    _phase1_ok = True
except ImportError as e:
    logger.warning(f"Phase 1 imports failed: {e}")
    _phase1_ok = False

# ── Phase 2 imports ────────────────────────────────────────────
try:
    from .abstraction_engine import AbstractionEngine
    from .analogy_engine import AnalogyEngine, Analogy
    from .symmetry_scanner import SymmetryScanner, SymmetryReport
    _phase2_ok = True
except ImportError as e:
    logger.warning(f"Phase 2 imports failed: {e}")
    _phase2_ok = False

# ── Phase 3 imports ────────────────────────────────────────────
try:
    from .abduction import AbductionEngine, AbductiveExplanation
    from .experiment_designer import ExperimentDesigner, CriticalExperiment
    from .theory_consistency import TheoryConsistencyChecker, ConsistencyCheck
    _phase3_ok = True
except ImportError as e:
    logger.warning(f"Phase 3 imports failed: {e}")
    _phase3_ok = False


@dataclass
class TheoryEngineStatus:
    """Snapshot of the theory engine's current state."""
    phase1_ok: bool
    phase2_ok: bool
    phase3_ok: bool
    theories_count: int
    theories_validated: int
    contradictions_count: int
    contradictions_unresolved: int
    analogies_count: int
    analogies_novel: int
    abductive_explanations: int
    critical_experiments: int
    symmetry_findings: int
    last_cycle_at: Optional[float]
    last_cycle_duration: float
    total_cycles: int

    def to_dict(self) -> Dict:
        return asdict(self)


class TheoryEngine:
    """
    Central orchestrator for theoretical framework generation.

    Runs asynchronously alongside the main DiscoveryEngine.
    Every `cycle_interval` engine cycles, it:
      1. Scans for contradictions in the hypothesis store
      2. Runs abstraction over validated hypotheses → proposes new theories
      3. Detects cross-domain analogies
      4. Scans for symmetries/universality
      5. Generates abductive explanations for anomalies
      6. Designs critical discriminating experiments
      7. Checks all active theories for self-consistency
    """

    def __init__(self, cycle_interval: int = 5):
        """
        Args:
            cycle_interval: Run one theory cycle every N discovery engine cycles.
        """
        self.cycle_interval = cycle_interval
        self._lock = threading.Lock()
        self._cycle_count = 0

        # Phase 1
        self.theory_store: Optional[TheoryStore] = TheoryStore() if _phase1_ok else None
        self.contradiction_detector: Optional[ContradictionDetector] = (
            ContradictionDetector() if _phase1_ok else None
        )
        self.exponent_matcher: Optional[UniversalExponentMatcher] = (
            UniversalExponentMatcher() if _phase1_ok else None
        )

        # Phase 2
        self.abstraction_engine: Optional[AbstractionEngine] = (
            AbstractionEngine() if _phase2_ok else None
        )
        self.analogy_engine: Optional[AnalogyEngine] = (
            AnalogyEngine() if _phase2_ok else None
        )
        self.symmetry_scanner: Optional[SymmetryScanner] = (
            SymmetryScanner() if _phase2_ok else None
        )

        # Phase 3
        self.abduction_engine: Optional[AbductionEngine] = (
            AbductionEngine() if _phase3_ok else None
        )
        self.experiment_designer: Optional[ExperimentDesigner] = (
            ExperimentDesigner() if _phase3_ok else None
        )
        self.consistency_checker: Optional[TheoryConsistencyChecker] = (
            TheoryConsistencyChecker() if _phase3_ok else None
        )

        # Result caches
        self._contradictions: List = []
        self._analogies: List = []
        self._symmetry_findings: List = []
        self._abductive_explanations: List = []
        self._critical_experiments: List = []
        self._consistency_reports: Dict[str, List] = {}  # theory_id → checks

        # Timing
        self._last_cycle_at: Optional[float] = None
        self._last_cycle_duration: float = 0.0
        self._total_cycles: int = 0

        logger.info(
            f"TheoryEngine initialised — "
            f"Phase1={'OK' if _phase1_ok else 'FAIL'} "
            f"Phase2={'OK' if _phase2_ok else 'FAIL'} "
            f"Phase3={'OK' if _phase3_ok else 'FAIL'}"
        )

    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────

    def tick(self, hypothesis_store, engine_cycle: int) -> bool:
        """
        Called by the DiscoveryEngine on every cycle.
        Only does real work every `cycle_interval` cycles.
        Returns True if a full theory cycle was executed.
        """
        if engine_cycle % self.cycle_interval != 0:
            return False
        threading.Thread(
            target=self._run_cycle,
            args=(hypothesis_store,),
            daemon=True
        ).start()
        return True

    def run_cycle_sync(self, hypothesis_store) -> Dict:
        """Run a full theory cycle synchronously. Used for API calls."""
        return self._run_cycle(hypothesis_store)

    def status(self) -> TheoryEngineStatus:
        with self._lock:
            theories = self.theory_store.all() if self.theory_store else []
            validated = [t for t in theories if getattr(t, 'status', '') == 'validated']
            unresolved = [c for c in self._contradictions
                          if not getattr(c, 'resolved', False)]
            novel_analogies = [a for a in self._analogies
                               if getattr(a, 'novel', False)]
            return TheoryEngineStatus(
                phase1_ok=_phase1_ok,
                phase2_ok=_phase2_ok,
                phase3_ok=_phase3_ok,
                theories_count=len(theories),
                theories_validated=len(validated),
                contradictions_count=len(self._contradictions),
                contradictions_unresolved=len(unresolved),
                analogies_count=len(self._analogies),
                analogies_novel=len(novel_analogies),
                abductive_explanations=len(self._abductive_explanations),
                critical_experiments=len(self._critical_experiments),
                symmetry_findings=len(self._symmetry_findings),
                last_cycle_at=self._last_cycle_at,
                last_cycle_duration=self._last_cycle_duration,
                total_cycles=self._total_cycles,
            )

    def get_theories(self) -> List[Dict]:
        if not self.theory_store:
            return []
        with self._lock:
            return [t.to_dict() for t in self.theory_store.all()]

    def get_contradictions(self) -> List[Dict]:
        with self._lock:
            result = []
            for c in self._contradictions:
                try:
                    result.append(c.to_dict() if hasattr(c, 'to_dict') else asdict(c))
                except Exception:
                    result.append({"error": str(c)})
            return result

    def get_analogies(self) -> List[Dict]:
        with self._lock:
            result = []
            for a in self._analogies:
                try:
                    result.append(a.to_dict() if hasattr(a, 'to_dict') else asdict(a))
                except Exception:
                    result.append({"error": str(a)})
            return result

    def get_symmetry_findings(self) -> List[Dict]:
        with self._lock:
            result = []
            for s in self._symmetry_findings:
                try:
                    result.append(s.to_dict() if hasattr(s, 'to_dict') else asdict(s))
                except Exception:
                    result.append({"error": str(s)})
            return result

    def get_abductive_explanations(self) -> List[Dict]:
        with self._lock:
            result = []
            for e in self._abductive_explanations:
                try:
                    result.append(e.to_dict() if hasattr(e, 'to_dict') else asdict(e))
                except Exception:
                    result.append({"error": str(e)})
            return result

    def get_critical_experiments(self) -> List[Dict]:
        with self._lock:
            result = []
            for ex in self._critical_experiments:
                try:
                    result.append(ex.to_dict() if hasattr(ex, 'to_dict') else asdict(ex))
                except Exception:
                    result.append({"error": str(ex)})
            return result

    def get_consistency_reports(self) -> Dict[str, List[Dict]]:
        with self._lock:
            out = {}
            for tid, checks in self._consistency_reports.items():
                out[tid] = []
                for c in checks:
                    try:
                        out[tid].append(c.to_dict() if hasattr(c, 'to_dict') else asdict(c))
                    except Exception:
                        out[tid].append({"error": str(c)})
            return out

    def resolve_contradiction(self, cid: str) -> bool:
        if self.contradiction_detector:
            self.contradiction_detector.mark_resolved(cid)
            return True
        return False

    def full_summary(self) -> Dict:
        """Complete theory engine state for the dashboard snapshot."""
        return {
            "status": self.status().to_dict(),
            "theories": self.get_theories(),
            "contradictions": self.get_contradictions(),
            "analogies": self.get_analogies(),
            "symmetry_findings": self.get_symmetry_findings(),
            "abductive_explanations": self.get_abductive_explanations(),
            "critical_experiments": self.get_critical_experiments(),
            "consistency_reports": self.get_consistency_reports(),
        }

    # ──────────────────────────────────────────────────────────
    # Internal cycle
    # ──────────────────────────────────────────────────────────

    def _run_cycle(self, hypothesis_store) -> Dict:
        t0 = time.time()
        results = {"phases_run": [], "errors": []}

        # ── Phase 1 ──────────────────────────────────────────
        if _phase1_ok and self.contradiction_detector:
            try:
                new_contradictions = self.contradiction_detector.scan(hypothesis_store)
                with self._lock:
                    existing_ids = {getattr(c, 'id', '') for c in self._contradictions}
                    for c in new_contradictions:
                        if getattr(c, 'id', '') not in existing_ids:
                            self._contradictions.append(c)
                results["phases_run"].append("phase1_contradiction")
                results["new_contradictions"] = len(new_contradictions)
                logger.info(f"ContradictionDetector: {len(new_contradictions)} found")
            except Exception as e:
                results["errors"].append(f"contradiction: {e}")
                logger.error(f"ContradictionDetector error: {e}")

        # ── Phase 2a — Abstraction ────────────────────────────
        if _phase2_ok and _phase1_ok and self.abstraction_engine and self.theory_store:
            try:
                existing = self.theory_store.all()
                new_theories = self.abstraction_engine.run(hypothesis_store, existing)
                with self._lock:
                    for t in new_theories:
                        tid = getattr(t, 'id', None)
                        if tid and not self.theory_store.get(tid):
                            self.theory_store.theories[tid] = t
                results["phases_run"].append("phase2_abstraction")
                results["new_theories"] = len(new_theories)
                logger.info(f"AbstractionEngine: {len(new_theories)} theories proposed")
            except Exception as e:
                results["errors"].append(f"abstraction: {e}")
                logger.error(f"AbstractionEngine error: {e}")

        # ── Phase 2b — Analogy ────────────────────────────────
        if _phase2_ok and self.analogy_engine:
            try:
                new_analogies = self.analogy_engine.scan(hypothesis_store)
                with self._lock:
                    existing_ids = {getattr(a, 'id', '') for a in self._analogies}
                    for a in new_analogies:
                        if getattr(a, 'id', '') not in existing_ids:
                            self._analogies.append(a)
                results["phases_run"].append("phase2_analogy")
                results["new_analogies"] = len(new_analogies)
                logger.info(f"AnalogyEngine: {len(new_analogies)} analogies found")
            except Exception as e:
                results["errors"].append(f"analogy: {e}")
                logger.error(f"AnalogyEngine error: {e}")

        # ── Phase 2c — Symmetry ───────────────────────────────
        if _phase2_ok and self.symmetry_scanner:
            try:
                findings = self.symmetry_scanner.full_scan(hypothesis_store)
                with self._lock:
                    existing_sigs = {
                        (getattr(f, 'symmetry_type', ''), getattr(f, 'variable', ''))
                        for f in self._symmetry_findings
                    }
                    for f in findings:
                        sig = (getattr(f, 'symmetry_type', ''), getattr(f, 'variable', ''))
                        if sig not in existing_sigs:
                            self._symmetry_findings.append(f)
                results["phases_run"].append("phase2_symmetry")
                results["symmetry_findings"] = len(findings)
                logger.info(f"SymmetryScanner: {len(findings)} findings")
            except Exception as e:
                results["errors"].append(f"symmetry: {e}")
                logger.error(f"SymmetryScanner error: {e}")

        # ── Phase 3a — Abduction ──────────────────────────────
        if _phase3_ok and self.abduction_engine:
            try:
                # Identify anomalous hypotheses (validated but contradicted)
                anomalies = self._find_anomalous_hypotheses(hypothesis_store)
                new_explanations = []
                validated_list = (
                    hypothesis_store.all()
                    if hasattr(hypothesis_store, 'all') else list(hypothesis_store)
                )
                for anomaly in anomalies[:3]:  # limit per cycle
                    exps = self.abduction_engine.generate_explanations(
                        anomaly, validated_list
                    )
                    new_explanations.extend(exps)
                with self._lock:
                    existing_ids = {getattr(e, 'id', '') for e in self._abductive_explanations}
                    for ex in new_explanations:
                        if getattr(ex, 'id', '') not in existing_ids:
                            self._abductive_explanations.append(ex)
                results["phases_run"].append("phase3_abduction")
                results["abductive_explanations"] = len(new_explanations)
                logger.info(f"AbductionEngine: {len(new_explanations)} explanations")
            except Exception as e:
                results["errors"].append(f"abduction: {e}")
                logger.error(f"AbductionEngine error: {e}")

        # ── Phase 3b — Experiment Design ─────────────────────
        if _phase3_ok and self.experiment_designer and self._contradictions:
            try:
                theories = self.theory_store.all() if self.theory_store else []
                unresolved = [c for c in self._contradictions
                              if not getattr(c, 'resolved', False)]
                new_experiments = self.experiment_designer.prioritised_experiment_list(
                    unresolved, theories
                )
                with self._lock:
                    existing_ids = {getattr(e, 'id', '') for e in self._critical_experiments}
                    for ex in new_experiments:
                        if getattr(ex, 'id', '') not in existing_ids:
                            self._critical_experiments.append(ex)
                results["phases_run"].append("phase3_experiments")
                results["critical_experiments"] = len(new_experiments)
                logger.info(f"ExperimentDesigner: {len(new_experiments)} experiments")
            except Exception as e:
                results["errors"].append(f"experiment_design: {e}")
                logger.error(f"ExperimentDesigner error: {e}")

        # ── Phase 3c — Consistency Check ─────────────────────
        if _phase3_ok and self.consistency_checker and self.theory_store:
            try:
                theories = self.theory_store.active()
                validated_hyps = (
                    hypothesis_store.all()
                    if hasattr(hypothesis_store, 'all') else []
                )
                new_reports = {}
                for theory in theories[:5]:  # limit per cycle
                    tid = getattr(theory, 'id', str(id(theory)))
                    checks = self.consistency_checker.check_theory(theory)
                    new_reports[tid] = checks
                    score = self.consistency_checker.overall_score(checks)
                    # Auto-falsify theories with fatal inconsistencies
                    if score < 0.2 and hasattr(theory, 'falsify'):
                        theory.falsify("Fatal consistency check failure")
                with self._lock:
                    self._consistency_reports.update(new_reports)
                results["phases_run"].append("phase3_consistency")
                results["theories_checked"] = len(new_reports)
                logger.info(f"ConsistencyChecker: {len(new_reports)} theories checked")
            except Exception as e:
                results["errors"].append(f"consistency: {e}")
                logger.error(f"ConsistencyChecker error: {e}")

        # ── Finalise ─────────────────────────────────────────
        elapsed = time.time() - t0
        with self._lock:
            self._last_cycle_at = t0
            self._last_cycle_duration = elapsed
            self._total_cycles += 1
            self._cycle_count += 1

        results["duration_s"] = round(elapsed, 3)
        results["cycle"] = self._total_cycles
        logger.info(f"TheoryEngine cycle {self._total_cycles} complete in {elapsed:.2f}s")
        return results

    def _find_anomalous_hypotheses(self, hypothesis_store) -> List:
        """
        Find hypotheses that are anomalous — validated but in tension
        with the known physics principles. These are candidates for abduction.
        """
        if not hasattr(hypothesis_store, 'all'):
            return []
        anomalies = []
        anomaly_keywords = [
            "anomal", "unexpected", "unusual", "tension", "discrepan",
            "inconsist", "violat", "exceed", "deficien", "surplus",
            "puzzl", "curious", "excess", "depart"
        ]
        for h in hypothesis_store.all():
            phase_val = getattr(h.phase, 'value', str(h.phase)) if hasattr(h, 'phase') else ''
            if phase_val in ('validated', 'testing') and h.confidence > 0.6:
                desc_lower = h.description.lower()
                if any(kw in desc_lower for kw in anomaly_keywords):
                    anomalies.append(h)
        return anomalies


# Module-level singleton — shared across the application
_theory_engine: Optional[TheoryEngine] = None


def get_theory_engine(cycle_interval: int = 5) -> TheoryEngine:
    """Get or create the global TheoryEngine singleton."""
    global _theory_engine
    if _theory_engine is None:
        _theory_engine = TheoryEngine(cycle_interval=cycle_interval)
    return _theory_engine
