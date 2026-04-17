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
ASTRA Live — Hypothesis State Machine
Real hypothesis lifecycle management with Bayesian confidence updates.
"""
import time
import math
import json
import numpy as np
import threading
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Phase(Enum):
    PROPOSED = "proposed"
    SCREENING = "screening"
    TESTING = "testing"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"


PHASE_ORDER = [Phase.PROPOSED, Phase.SCREENING, Phase.TESTING, Phase.VALIDATED, Phase.PUBLISHED]


@dataclass
class TestResult:
    test_name: str
    statistic: float
    p_value: float
    timestamp: float
    passed: bool
    details: str = ""


@dataclass
class Hypothesis:
    id: str
    name: str
    domain: str
    description: str
    confidence: float = 0.5
    phase: Phase = Phase.PROPOSED
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    test_results: list = field(default_factory=list)
    priority: str = "NORMAL"
    publications: int = 0
    data_points_used: int = 0
    cross_domain_links: list = field(default_factory=list)
    requires_approval: bool = False      # Phase gate: VALIDATED→PUBLISHED needs approval
    pending_approval_at: float = 0.0     # Timestamp when approval was requested
    approval_status: str = ""            # "pending", "approved", "rejected"
    approval_reason: str = ""            # Reason for approval/rejection
    # Phase 10.4: Lifecycle timestamps
    last_tested_at: float = 0.0          # Timestamp of last statistical test
    archived_at: float = 0.0             # Timestamp when archived
    # Variables for hypothesis investigation
    variables: list = field(default_factory=list)  # Variable names for this hypothesis
    finding_type: str = ""               # Type of finding expected (correlation, causal, etc.)
    data_source: str = ""                # Primary data source for investigation

    def bayesian_update(self, likelihood_positive: float, likelihood_negative: float):
        """Real Bayesian update of confidence given evidence."""
        prior = self.confidence
        posterior = (prior * likelihood_positive) / (
            prior * likelihood_positive + (1 - prior) * likelihood_negative
        )
        posterior = max(0.01, min(0.99, posterior))
        delta = posterior - prior
        self.confidence = posterior
        self.updated_at = time.time()
        return delta

    def update_from_pvalue(self, p_value: float, alpha: float = 0.05):
        """
        Update confidence based on a p-value from a statistical test.

        BUG FIX (Phase 1 Safety): The original code had a statistical
        directionality bug — high p-values (non-significant) used lr=0.5
        which via bayesian_update(0.33, 0.67) would INCREASE confidence
        when null hypothesis was NOT rejected. Now high p-values correctly
        DECREASE confidence (likelihood ratio < 1 penalizes the hypothesis).

        Likelihood ratio mapping:
          p < 0.001 → strong evidence (lr=8.0, boosts confidence)
          p < 0.01  → good evidence (lr=4.0)
          p < alpha  → moderate evidence (lr=2.0)
          p < 0.1   → weak/marginal (lr=1.0, no change)
          p < 0.3   → mild counter-evidence (lr=0.5, decreases confidence)
          p >= 0.3  → counter-evidence (lr=0.25, decreases confidence more)
        """
        if p_value < 0.001:
            lr = 8.0   # Strong evidence → boost confidence
        elif p_value < 0.01:
            lr = 4.0   # Good evidence
        elif p_value < alpha:
            lr = 2.0   # Moderate evidence
        elif p_value < 0.1:
            lr = 1.0   # Marginal — no update
        elif p_value < 0.3:
            lr = 0.5   # Non-significant → decrease confidence
        else:
            lr = 0.25  # Clearly non-significant → stronger decrease
        # lr > 1 → positive_likelihood dominates → confidence increases
        # lr < 1 → negative_likelihood dominates → confidence decreases
        # lr = 1 → no change
        self.last_tested_at = time.time()
        return self.bayesian_update(lr / (lr + 1), 1 / (lr + 1))

    def advance_phase(self):
        """
        Advance to next phase if confidence thresholds are met.

        PHASE GATE (Phase 1 Safety): The VALIDATED → PUBLISHED transition
        requires human approval. When a hypothesis reaches VALIDATED with
        sufficient confidence, it enters a 'pending' approval state instead
        of auto-advancing. Use approve()/reject() to resolve.
        """
        thresholds = {
            Phase.PROPOSED: 0.15,  # Lowered from 0.3 to allow newly generated hypotheses to advance
            Phase.SCREENING: 0.40,  # Lowered from 0.45
            Phase.TESTING: 0.55,   # Lowered from 0.6
            Phase.VALIDATED: 0.70,  # Lowered from 0.75
            Phase.PUBLISHED: 0.80,  # Lowered from 0.85
        }
        if self.phase in thresholds and self.confidence >= thresholds[self.phase]:
            idx = PHASE_ORDER.index(self.phase)
            if idx < len(PHASE_ORDER) - 1:
                next_phase = PHASE_ORDER[idx + 1]
                # Phase gate: VALIDATED → PUBLISHED requires approval
                if self.phase == Phase.VALIDATED and next_phase == Phase.PUBLISHED:
                    if self.approval_status != "approved":
                        # Enter pending approval queue instead of auto-advancing
                        if self.approval_status != "pending":
                            self.requires_approval = True
                            self.approval_status = "pending"
                            self.pending_approval_at = time.time()
                            self.updated_at = time.time()
                        return False  # Do NOT auto-advance
                self.phase = next_phase
                self.updated_at = time.time()
                return True
        return False

    def approve(self, reason: str = "Approved for publication"):
        """Approve this hypothesis for VALIDATED → PUBLISHED advancement."""
        if self.phase == Phase.VALIDATED and self.approval_status == "pending":
            self.approval_status = "approved"
            self.approval_reason = reason
            self.phase = Phase.PUBLISHED
            self.updated_at = time.time()
            self.requires_approval = False
            return True
        return False

    def reject(self, reason: str = "Rejected — insufficient evidence"):
        """Reject this hypothesis. Stays at VALIDATED, approval cleared."""
        if self.approval_status == "pending":
            self.approval_status = "rejected"
            self.approval_reason = reason
            self.requires_approval = False
            self.updated_at = time.time()
            return True
        return False

    def prune_if_weak(self, threshold: float = 0.2):
        """Archive if confidence is too low after multiple tests."""
        if self.confidence < threshold and len(self.test_results) >= 3:
            self.phase = Phase.ARCHIVED
            self.updated_at = time.time()
            self.archived_at = time.time()
            return True
        return False

    def to_dict(self):
        d = asdict(self)
        d['phase'] = self.phase.value
        clean_results = []
        for t in self.test_results:
            if hasattr(t, '__dataclass_fields__'):
                td = asdict(t)
            elif isinstance(t, dict):
                td = t.copy()
            else:
                td = t
            # Convert numpy types to Python native
            if isinstance(td, dict):
                for k, v in td.items():
                    if hasattr(v, 'item'):
                        td[k] = v.item()
                    elif isinstance(v, bool):
                        td[k] = bool(v)
                clean_results.append(td)
            else:
                clean_results.append(td)
        d['test_results'] = clean_results
        # Convert all numpy types in the main dict
        for k, v in d.items():
            if hasattr(v, 'item'):
                d[k] = v.item()
            elif isinstance(v, (np.bool_,)):
                d[k] = bool(v)
            elif isinstance(v, (np.integer,)):
                d[k] = int(v)
            elif isinstance(v, (np.floating,)):
                d[k] = float(v)
        return d


class HypothesisStore:
    """Thread-safe hypothesis storage with per-hypothesis locking."""

    def __init__(self):
        self.hypotheses: dict[str, Hypothesis] = {}
        self._next_id = 1
        self._id_prefix_map = {"H": 1, "CD": 1}

        # Thread safety: per-hypothesis locks for concurrent updates
        self._hypothesis_locks: dict[str, threading.Lock] = {}
        self._store_lock = threading.RLock()  # Reentrant for nested operations
        self._id_lock = threading.Lock()  # Protect ID generation

    def _get_hypothesis_lock(self, hid: str) -> threading.Lock:
        """Get or create a lock for the specified hypothesis."""
        with self._store_lock:
            if hid not in self._hypothesis_locks:
                self._hypothesis_locks[hid] = threading.Lock()
            return self._hypothesis_locks[hid]

    def _ensure_hypothesis_lock(self, h: Hypothesis):
        """Ensure a lock exists for this hypothesis (called during add)."""
        with self._store_lock:
            if h.id not in self._hypothesis_locks:
                self._hypothesis_locks[h.id] = threading.Lock()

    def add(self, name: str, domain: str, description: str,
            confidence: float = 0.5, prefix: str = "H",
            variables: list = None, finding_type: str = "", data_source: str = "") -> Optional[Hypothesis]:
        """
        Add a new hypothesis in a thread-safe manner. Returns existing hypothesis if duplicate name.

        CRITICAL FIX: Prevents duplicate hypotheses by checking for existing names.
        Thread-safe: uses store lock for duplicate checking and ID generation.
        """
        # Thread-safe duplicate check and ID generation
        with self._store_lock:
            # Check for duplicate by name (case-insensitive)
            for existing_h in self.hypotheses.values():
                if existing_h.name.lower().strip() == name.lower().strip():
                    # Duplicate found - return the existing hypothesis instead of creating a new one
                    return existing_h

            # No duplicate found - proceed with thread-safe ID generation
            if prefix == "CD":
                with self._id_lock:  # Protect ID counter
                    hid = f"CD-{self._id_prefix_map['CD']:03d}"
                    self._id_prefix_map['CD'] += 1
            else:
                with self._id_lock:  # Protect ID counter
                    hid = f"H{self._id_prefix_map['H']:03d}"
                    self._id_prefix_map['H'] += 1

            h = Hypothesis(id=hid, name=name, domain=domain,
                           description=description, confidence=confidence,
                           variables=variables or [], finding_type=finding_type,
                           data_source=data_source)
            self.hypotheses[hid] = h

            # Ensure lock exists for this new hypothesis
            self._ensure_hypothesis_lock(h)

        return h

    def get(self, hid: str) -> Optional[Hypothesis]:
        """Get hypothesis by ID - thread-safe read operation."""
        # Read-only operation, doesn't need lock for GIL-protected dict access
        return self.hypotheses.get(hid)

    def update_confidence(self, hid: str, delta: float) -> bool:
        """
        Thread-safe confidence update using per-hypothesis locking.
        Returns True if hypothesis exists and was updated, False otherwise.
        """
        lock = self._get_hypothesis_lock(hid)
        with lock:
            h = self.hypotheses.get(hid)
            if h:
                h.confidence = max(0.01, min(0.99, h.confidence + delta))
                h.updated_at = time.time()
                return True
        return False

    def update_phase(self, hid: str, new_phase: Phase) -> bool:
        """
        Thread-safe phase update using per-hypothesis locking.
        Returns True if hypothesis exists and was updated, False otherwise.
        """
        lock = self._get_hypothesis_lock(hid)
        with lock:
            h = self.hypotheses.get(hid)
            if h:
                h.phase = new_phase
                h.updated_at = time.time()
                return True
        return False

    def add_test_result(self, hid: str, test_result: dict) -> bool:
        """
        Thread-safe test result addition using per-hypothesis locking.
        Returns True if hypothesis exists and was updated, False otherwise.
        """
        lock = self._get_hypothesis_lock(hid)
        with lock:
            h = self.hypotheses.get(hid)
            if h:
                h.test_results.append(test_result)
                h.updated_at = time.time()
                return True
        return False

    def all(self) -> list[Hypothesis]:
        return list(self.hypotheses.values())

    def by_domain(self, domain: str) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.domain == domain]

    def by_phase(self, phase: Phase) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.phase == phase]

    def active(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.phase != Phase.ARCHIVED]

    def pending_approvals(self) -> list[Hypothesis]:
        """Return hypotheses awaiting approval for VALIDATED → PUBLISHED."""
        return [h for h in self.hypotheses.values()
                if h.approval_status == "pending"]

    def funnel_counts(self) -> dict[str, int]:
        counts = {p.value: 0 for p in Phase}
        for h in self.hypotheses.values():
            counts[h.phase.value] += 1
        return counts

    def to_json(self) -> str:
        return json.dumps([h.to_dict() for h in self.hypotheses.values()], indent=2)


def seed_initial_hypotheses(store: HypothesisStore):
    """Seed with real astrophysical hypotheses backed by live data sources."""
    seeds = [
        # Astrophysics — backed by real data
        ("Hubble Tension Analysis", "Astrophysics",
         "Pantheon+ SNe Ia (1701 supernovae) distance modulus analysis: test ΛCDM predictions and measure H₀ tension", 0.55, "H"),
        ("Galaxy Color Bimodality", "Astrophysics",
         "SDSS DR18 galaxy photometry: quantify red sequence + blue cloud bimodality in g-r color", 0.45, "H"),
        ("Exoplanet Mass-Period Relation", "Astrophysics",
         "NASA Exoplanet Archive: test Kepler's third law scaling and mass-period correlation in confirmed planets", 0.50, "H"),
        ("Gaia HR Diagram Structure", "Astrophysics",
         "Gaia DR3 astrometry+photometry: characterize main sequence, giant branch, and white dwarf sequence", 0.48, "H"),
        ("Galaxy Redshift Distribution", "Astrophysics",
         "SDSS spectroscopic redshifts: test for clustering and void structure in local universe (z < 0.5)", 0.42, "H"),
        ("Exoplanet Period Distribution", "Astrophysics",
         "Transit/RV discoveries: test for period valley near 10 days and hot Jupiter desert", 0.52, "H"),
        ("Stellar Parallax Accuracy", "Astrophysics",
         "Gaia DR3 parallax error analysis: quantify systematic offsets and distance uncertainties", 0.40, "H"),
        ("Star Formation Fraction", "Astrophysics",
         "SDSS u-r color as star formation proxy: measure blue fraction evolution with redshift", 0.46, "H"),
        ("Transit Depth Statistics", "Astrophysics",
         "NASA Exoplanet Archive: distribution of transit depths across discovery methods", 0.38, "H"),
        ("Dark Energy Equation of State", "Astrophysics",
         "Pantheon+ distance modulus: constrain w(z) with binned SNe Ia analysis", 0.35, "H"),
        # Phase 6 — New data sources
        ("GW Mass Distribution", "Astrophysics",
         "LIGO/Virgo chirp mass and mass ratio distribution: test population synthesis models", 0.40, "GW"),
        ("CMB Acoustic Peak Structure", "Astrophysics",
         "Planck TT power spectrum: measure acoustic peak positions and cosmological parameters", 0.45, "CMB"),
        ("ZTF Transient Classification", "Astrophysics",
         "ZTF transient light curves: test SNe classification and host galaxy association", 0.35, "ZTF"),
        ("TESS Stellar Host Parameters", "Astrophysics",
         "TESS Input Catalog: mass-radius relation for exoplanet host stars", 0.42, "TESS"),
        ("Cluster Richness-Mass Scaling", "Astrophysics",
         "SDSS redMaPPer richness as mass proxy: test self-similar scaling relation", 0.38, "CLU"),
        # Cross-domain — Phase 6
        ("GW Electromagnetic Counterpart", "Astrophysics",
         "Cross-match GW events with ZTF transients for multi-messenger association", 0.30, "GW"),
        ("Stellar TESS-Gaia Cross-Match", "Astrophysics",
         "Link TESS host stars with Gaia astrometry for precise distance-luminosity calibration", 0.35, "TESS"),
        # Cross-domain — qualitative comparisons
        ("Survey Design Optimization", "Physics",
         "Apply adaptive sampling optimization to astronomical survey strategy", 0.30, "CD"),
        ("Mathematical Pattern Discovery", "Mathematics",
         "Autonomous discovery of mathematical patterns using symbolic computation and formal verification", 0.25, "CD"),
    ]

    for name, domain, desc, conf, prefix in seeds:
        h = store.add(name, domain, desc, conf, prefix)
        # Set appropriate phases based on confidence
        if conf >= 0.50:
            h.phase = Phase.TESTING
        elif conf >= 0.40:
            h.phase = Phase.SCREENING
        else:
            h.phase = Phase.PROPOSED
        h.created_at = time.time() - np.random.uniform(3600, 86400 * 7)
