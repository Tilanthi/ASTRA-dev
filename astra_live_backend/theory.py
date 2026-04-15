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
ASTRA Live — Theory Object and TheoryStore
Manages formal theoretical frameworks: collections of validated hypotheses
unified under a common mathematical and physical structure.

A Theory is NOT a hypothesis. It is a higher-order explanatory structure
with explicit axioms, falsification conditions, and a domain of validity.
Theories emerge from the synthesis of multiple validated hypotheses.

As described in White & Dey (2026), Section 3: Theoretical Framework Layer.
"""
import time
import json
import numpy as np
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, List


class TheoryPhase(Enum):
    PROPOSED   = "proposed"
    ACTIVE     = "active"
    VALIDATED  = "validated"
    FALSIFIED  = "falsified"
    SUPERSEDED = "superseded"


# Confidence thresholds for phase transitions
THEORY_PHASE_THRESHOLDS = {
    TheoryPhase.PROPOSED:   0.35,   # → ACTIVE
    TheoryPhase.ACTIVE:     0.60,   # → VALIDATED
    TheoryPhase.VALIDATED:  0.80,   # (terminal positive state)
}

THEORY_PHASE_ORDER = [
    TheoryPhase.PROPOSED,
    TheoryPhase.ACTIVE,
    TheoryPhase.VALIDATED,
]


@dataclass
class Theory:
    """
    A formal theoretical framework synthesised from validated hypotheses.

    Fields
    ------
    id : str
        Unique identifier, e.g. "T001".
    name : str
        Human-readable name of the theory.
    domain : str
        Scientific domain (e.g. "Astrophysics", "Climate", "Cryptography").
    axioms : List[str]
        Formal assumptions on which the theory rests.
    derived_predictions : List[str]
        Testable predictions that follow mathematically from the axioms.
    domain_of_validity : Dict
        Explicit scope of applicability, e.g. {"mass_range": "1e6-1e12 Msun"}.
    falsification_conditions : List[str]
        Observable outcomes that would definitively disprove the theory.
    supporting_hypothesis_ids : List[str]
        IDs of validated hypotheses this theory explains or unifies.
    competing_theory_ids : List[str]
        IDs of mutually exclusive competing theories.
    mathematical_core : str
        Key equation(s) as a string, SymPy-compatible if possible.
    confidence : float
        Bayesian confidence estimate [0, 1].
    status : str
        Mirrors TheoryPhase.value for JSON-serialisable storage.
    novelty_score : float
        0–1 measure of how novel the theory is vs. existing literature.
    unification_count : int
        Number of distinct hypotheses unified under this theory.
    predictive_economy : float
        Ratio: number_of_predictions / number_of_free_parameters.
    created_at : float
        Unix timestamp of creation.
    updated_at : float
        Unix timestamp of last update.
    provenance : List[str]
        Audit trail of how this theory was generated/promoted.
    test_results : List[Dict]
        Structured test records (same pattern as Hypothesis.test_results).
    """
    id: str
    name: str
    domain: str
    axioms: List[str]
    derived_predictions: List[str]
    domain_of_validity: Dict
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
    test_results: List[Dict] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    @property
    def phase(self) -> TheoryPhase:
        """Return current TheoryPhase from status string."""
        try:
            return TheoryPhase(self.status)
        except ValueError:
            return TheoryPhase.PROPOSED

    def promote(self) -> bool:
        """
        Advance phase if confidence threshold is met.

        Returns True if phase was advanced, False otherwise.
        Theories can only be falsified or superseded externally
        (call falsify() / supersede() directly).
        """
        current = self.phase
        if current in THEORY_PHASE_THRESHOLDS and self.confidence >= THEORY_PHASE_THRESHOLDS[current]:
            idx = THEORY_PHASE_ORDER.index(current)
            if idx < len(THEORY_PHASE_ORDER) - 1:
                next_phase = THEORY_PHASE_ORDER[idx + 1]
                self.status = next_phase.value
                self.updated_at = time.time()
                self.provenance.append(
                    f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] "
                    f"Phase promoted: {current.value} → {next_phase.value} "
                    f"(confidence={self.confidence:.3f})"
                )
                return True
        return False

    def falsify(self, reason: str = ""):
        """Mark theory as falsified."""
        self.status = TheoryPhase.FALSIFIED.value
        self.updated_at = time.time()
        self.provenance.append(
            f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] "
            f"Falsified. {reason}"
        )

    def supersede(self, successor_id: str, reason: str = ""):
        """Mark theory as superseded by another theory."""
        self.status = TheoryPhase.SUPERSEDED.value
        self.updated_at = time.time()
        self.provenance.append(
            f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] "
            f"Superseded by {successor_id}. {reason}"
        )

    def bayesian_update(self, likelihood_positive: float, likelihood_negative: float) -> float:
        """Bayesian update of theory confidence given new evidence."""
        prior = self.confidence
        posterior = (prior * likelihood_positive) / (
            prior * likelihood_positive + (1 - prior) * likelihood_negative
        )
        posterior = max(0.01, min(0.99, posterior))
        delta = posterior - prior
        self.confidence = posterior
        self.updated_at = time.time()
        return delta

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict:
        """Serialise to plain dict, handling numpy types."""
        d = asdict(self)
        # Sanitise test_results
        clean_results = []
        for t in self.test_results:
            if hasattr(t, '__dataclass_fields__'):
                td = asdict(t)
            elif isinstance(t, dict):
                td = t.copy()
            else:
                td = t
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
        # Convert top-level numpy types
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


# ---------------------------------------------------------------------------
# TheoryStore
# ---------------------------------------------------------------------------

class TheoryStore:
    """Thread-safe theory storage.

    Follows the same patterns as HypothesisStore in hypotheses.py.
    """

    def __init__(self):
        self.theories: Dict[str, Theory] = {}
        self._next_id: int = 1

    def add(
        self,
        name: str,
        domain: str,
        axioms: List[str] = None,
        derived_predictions: List[str] = None,
        domain_of_validity: Dict = None,
        falsification_conditions: List[str] = None,
        supporting_hypothesis_ids: List[str] = None,
        competing_theory_ids: List[str] = None,
        mathematical_core: str = "",
        confidence: float = 0.5,
        novelty_score: float = 0.0,
        predictive_economy: float = 0.0,
        provenance: List[str] = None,
    ) -> Theory:
        """Create and store a new Theory, returning the Theory object."""
        tid = f"T{self._next_id:03d}"
        self._next_id += 1

        now = time.time()
        t = Theory(
            id=tid,
            name=name,
            domain=domain,
            axioms=axioms or [],
            derived_predictions=derived_predictions or [],
            domain_of_validity=domain_of_validity or {},
            falsification_conditions=falsification_conditions or [],
            supporting_hypothesis_ids=supporting_hypothesis_ids or [],
            competing_theory_ids=competing_theory_ids or [],
            mathematical_core=mathematical_core,
            confidence=confidence,
            status=TheoryPhase.PROPOSED.value,
            novelty_score=novelty_score,
            unification_count=len(supporting_hypothesis_ids) if supporting_hypothesis_ids else 0,
            predictive_economy=predictive_economy,
            created_at=now,
            updated_at=now,
            provenance=provenance or [
                f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}] Theory created."
            ],
            test_results=[],
        )
        self.theories[tid] = t
        return t

    def get(self, tid: str) -> Optional[Theory]:
        """Retrieve a Theory by ID."""
        return self.theories.get(tid)

    def all(self) -> List[Theory]:
        """Return all theories."""
        return list(self.theories.values())

    def by_domain(self, domain: str) -> List[Theory]:
        """Return theories in a specific domain."""
        return [t for t in self.theories.values() if t.domain == domain]

    def by_status(self, status: str) -> List[Theory]:
        """Return theories with a specific status string."""
        return [t for t in self.theories.values() if t.status == status]

    def active(self) -> List[Theory]:
        """Return all non-falsified, non-superseded theories."""
        terminal = {TheoryPhase.FALSIFIED.value, TheoryPhase.SUPERSEDED.value}
        return [t for t in self.theories.values() if t.status not in terminal]

    def to_dict(self) -> List[Dict]:
        """Return list of serialised theory dicts."""
        return [t.to_dict() for t in self.theories.values()]

    def to_json(self) -> str:
        """Serialise all theories to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def funnel_counts(self) -> Dict[str, int]:
        """Count theories by status."""
        counts = {phase.value: 0 for phase in TheoryPhase}
        for t in self.theories.values():
            counts[t.status] = counts.get(t.status, 0) + 1
        return counts
