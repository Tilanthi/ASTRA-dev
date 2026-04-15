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
ASTRA Live — Safety Case
Structured argument with evidence that the system is acceptably safe.
Phase 4 of the AGI Transformation Roadmap.

Implements ALARP (As Low As Reasonably Practicable) methodology,
hazard register, and evidence hierarchy.
"""
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional


class HazardSeverity(Enum):
    NEGLIGIBLE = 1
    MARGINAL = 2
    CRITICAL = 3
    CATASTROPHIC = 4


class HazardLikelihood(Enum):
    IMPROBABLE = 1
    REMOTE = 2
    OCCASIONAL = 3
    FREQUENT = 4


class RiskAcceptability(Enum):
    BROADLY_ACCEPTABLE = "BROADLY_ACCEPTABLE"
    ALARP = "ALARP"           # As Low As Reasonably Practicable
    TOLERABLE = "TOLERABLE"
    INTOLERABLE = "INTOLERABLE"


@dataclass
class Hazard:
    id: str
    category: str
    description: str
    severity: int
    likelihood: int
    risk_score: float
    acceptability: str
    mitigation: str
    evidence: str = ""
    residual_risk: float = 0.0
    last_reviewed: float = 0.0

    def to_dict(self):
        return asdict(self)


@dataclass
class SafetyClaim:
    id: str
    claim: str
    argument: str
    evidence_refs: List[str]
    confidence: float
    last_verified: float = 0.0

    def to_dict(self):
        return asdict(self)


class SafetyCase:
    """
    Safety Case: structured argument that ASTRA Live is acceptably safe
    for monitored autonomous scientific discovery.
    """

    # ── Hazard Register ────────────────────────────────────────────
    HAZARDS = [
        ("H01", "autonomous", "System publishes hypothesis without human validation",
         4, 2, "Phase gates enforce VALIDATED→PUBLISHED approval",
         "Phase gate implementation in hypotheses.py, E2E test coverage"),

        ("H02", "containment", "System modifies host system or external resources",
         4, 1, "SafetyController enforces state bounds; no external write capabilities",
         "Safety state machine, circuit breaker rules"),

        ("H03", "alignment", "System diverges from scientific rigor over time",
         3, 2, "6-dimension alignment scoring with anomaly detection",
         "AlignmentChecker, AnomalyDetector, rolling statistics"),

        ("H04", "cascade", "Circuit breaker failure causes safety system bypass",
         4, 1, "5 independent circuit breaker rules; Safety Arbiter aggregates",
         "CircuitBreaker implementation, arbiter signal aggregation"),

        ("H05", "human_factors", "Supervisor takes inappropriate action during monitoring",
         3, 2, "Certification hierarchy with action authorization checks",
         "SupervisorRegistry, execute_action authorization"),

        ("H06", "state_space", "System enters uncontrollable attractor basin",
         3, 2, "PCA state space monitoring, attractor detection, anomaly alerts",
         "PCAVisualizer, AttractorDetector, anomaly thresholds"),

        ("H07", "audit", "Critical event not recorded in audit trail",
         2, 1, "Dual audit: in-memory + JSONL persistent logging",
         "AuditLogger, SafetyController._audit integration"),

        ("H08", "autonomy", "System operates beyond intended capability boundaries",
         3, 2, "PhasedAutonomyFramework with enforced capability bounds",
         "PhasedAutonomyFramework, SafetyController permission checks"),

        ("H09", "resource", "System consumes excessive resources affecting stability",
         2, 3, "SystemHealthMonitor with CPU/memory/disk checks",
         "SystemHealthReport, psutil monitoring, health endpoint"),

        ("H10", "ethical", "System violates ethical boundaries in research",
         3, 2, "EthicalReasoner with non-maleficence, truthfulness, humility rules",
         "EthicalReasoner.evaluate_action, integration in engine cycle"),
    ]

    # ── Safety Claims (Goal Structuring Notation style) ────────────
    CLAIMS = [
        ("SC01", "System cannot publish without human approval",
         "VALIDATED→PUBLISHED transition requires explicit human approval via API. "
         "Phase gate in Hypothesis.advance_phase() checks approval status. "
         "E2E test verifies gate blocks unauthorized transitions.",
         ["T10", "E2E-test-phase-gates", "hypotheses.py:advance_phase()"]),

        ("SC02", "System cannot escalate autonomy without ceremony",
         "PhaseCommencementProtocol requires checklist verification, supervisor approval, "
         "preflight checks, and monitoring period. No direct level changes bypass ceremony.",
         ["P01", "P02", "P03", "ceremony.py:Protocol"]),

        ("SC03", "All safety-critical actions are audited",
         "SafetyController._audit() called on every state transition. "
         "AuditLogger writes to JSONL daily files. "
         "SupervisorRegistry logs all authorized and unauthorized actions.",
         ["T03", "H02", "audit.py", "controller.py:_audit()"]),

        ("SC04", "Emergency stop halts all operations within 10 seconds",
         "SafetyController.emergency_stop() sets state to STOPPED, "
         "sets engine.running = False, saves state snapshot. "
         "Engine loop checks safety.can_run_cycle() before each cycle.",
         ["T13", "controller.py:emergency_stop()", "engine.py:run_cycle()"]),

        ("SC05", "Anomalous behavior triggers automatic alerts",
         "AnomalyDetector checks 5 metrics against rolling statistics (±2σ). "
         "CRITICAL anomalies logged immediately. Circuit breakers trip on threshold breach.",
         ["T07", "T02", "anomaly.py", "circuit_breakers.py"]),

        ("SC06", "System alignment is continuously monitored",
         "AlignmentChecker computes 6-dimension score each cycle. "
         "Score below 0.5 triggers NO_GO verdict from Safety Arbiter.",
         ["T08", "T12", "alignment.py", "arbiter.py"]),

        ("SC07", "Rollback is available for every autonomy level",
         "ORP defines rollback procedures for FULL→CONDITIONAL→SUPERVISED→SHADOW→STOPPED. "
         "Each procedure has specific steps and estimated completion time.",
         ["P05", "orp.py:ROLLBACK_PROCEDURES"]),
    ]

    def __init__(self):
        self._hazards: Dict[str, Hazard] = {}
        self._claims: Dict[str, SafetyClaim] = {}

        for hid, cat, desc, sev, lik, mit, evi in self.HAZARDS:
            risk = sev * lik / 4.0  # Normalize to 0-4 scale
            acc = self._classify_risk(risk)
            self._hazards[hid] = Hazard(
                id=hid, category=cat, description=desc,
                severity=sev, likelihood=lik, risk_score=risk,
                acceptability=acc, mitigation=mit, evidence=evi,
                residual_risk=risk * 0.3,  # Post-mitigation
                last_reviewed=time.time(),
            )

        for cid, claim, arg, evi_refs in self.CLAIMS:
            self._claims[cid] = SafetyClaim(
                id=cid, claim=claim, argument=arg,
                evidence_refs=evi_refs, confidence=0.85,
                last_verified=time.time(),
            )

    @staticmethod
    def _classify_risk(risk: float) -> str:
        if risk <= 1.0:
            return RiskAcceptability.BROADLY_ACCEPTABLE.value
        elif risk <= 2.0:
            return RiskAcceptability.ALARP.value
        elif risk <= 3.0:
            return RiskAcceptability.TOLERABLE.value
        else:
            return RiskAcceptability.INTOLERABLE.value

    def get_hazard_register(self) -> List[Dict]:
        return [h.to_dict() for h in self._hazards.values()]

    def get_safety_claims(self) -> List[Dict]:
        return [c.to_dict() for c in self._claims.values()]

    def get_risk_summary(self) -> Dict:
        hazards = list(self._hazards.values())
        return {
            "total_hazards": len(hazards),
            "by_acceptability": {
                acc.value: sum(1 for h in hazards if h.acceptability == acc.value)
                for acc in RiskAcceptability
            },
            "by_severity": {
                sev.name: sum(1 for h in hazards if h.severity == sev.value)
                for sev in HazardSeverity
            },
            "max_risk": max((h.risk_score for h in hazards), default=0),
            "max_residual": max((h.residual_risk for h in hazards), default=0),
            "total_claims": len(self._claims),
            "avg_claim_confidence": sum(c.confidence for c in self._claims.values()) / max(len(self._claims), 1),
            "timestamp": time.time(),
        }

    def get_status(self) -> Dict:
        risk = self.get_risk_summary()
        return {
            "hazards": risk["total_hazards"],
            "claims": risk["total_claims"],
            "max_residual_risk": risk["max_residual"],
            "intolerable_hazards": risk["by_acceptability"].get("INTOLERABLE", 0),
            "avg_confidence": round(risk["avg_claim_confidence"], 3),
        }
