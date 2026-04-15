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
ASTRA Live — Safety Arbiter
Centralized decision authority for safety-critical operations.
Phase 4 of the AGI Transformation Roadmap.

The Arbiter evaluates multiple signals (circuit breakers, alignment, anomalies,
ethical rules, autonomy level) and produces a unified GO / NO_GO / ABORT decision
for each engine cycle and each safety-critical action.
"""
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


class Decision(Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    ABORT = "ABORT"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ArbiterVerdict:
    timestamp: float
    decision: str
    risk_level: str
    score: float  # 0.0 = safe, 1.0 = maximum risk
    reasons: List[str]
    overrides: List[str]
    cycle: int

    def to_dict(self):
        return asdict(self)


class SafetyArbiter:
    """
    The Safety Arbiter sits between all safety subsystems and the engine.
    It aggregates signals from:
      - SafetyController (state machine)
      - SafetyMonitor (circuit breakers)
      - AlignmentChecker (6-dimension alignment)
      - AnomalyDetector (statistical anomalies)
      - EthicalReasoner (ethical boundaries)
      - PhasedAutonomyFramework (capability bounds)

    And produces a single GO / NO_GO / ABORT verdict for each operation.
    """

    # Risk thresholds
    GO_THRESHOLD = 0.25      # Below this: GO
    NO_GO_THRESHOLD = 0.65   # Between GO and NO_GO threshold: GO with warnings
    # Above NO_GO_THRESHOLD: ABORT

    # Weight of each signal in composite risk score
    SIGNAL_WEIGHTS = {
        "safety_state": 0.30,
        "circuit_breakers": 0.20,
        "alignment": 0.15,
        "anomalies": 0.20,
        "ethics": 0.10,
        "autonomy": 0.05,
    }

    def __init__(self):
        self._verdict_history: List[ArbiterVerdict] = []
        self._overrides: List[Dict] = []
        self._started_at = time.time()

    def evaluate_cycle(
        self,
        safety_state: str,
        circuit_breaker_tripped: bool,
        circuit_breaker_details: Optional[List[Dict]] = None,
        alignment_score: float = 1.0,
        alignment_details: Optional[Dict] = None,
        anomalies: Optional[List[Dict]] = None,
        ethics_result: Optional[Dict] = None,
        autonomy_level: str = "SUPERVISED",
        autonomy_bounds: Optional[Dict] = None,
        cycle: int = 0,
    ) -> ArbiterVerdict:
        """
        Evaluate all safety signals and produce a verdict for the upcoming cycle.

        Returns ArbiterVerdict with decision, risk_level, score, and reasons.
        """
        reasons = []
        overrides = []
        risk_components = {}

        # 1. Safety state signal
        state_risk = self._evaluate_safety_state(safety_state)
        risk_components["safety_state"] = state_risk
        if state_risk > 0.5:
            reasons.append(f"Safety state {safety_state} contributes risk {state_risk:.2f}")

        # 2. Circuit breaker signal
        cb_risk = self._evaluate_circuit_breakers(circuit_breaker_tripped, circuit_breaker_details)
        risk_components["circuit_breakers"] = cb_risk
        if circuit_breaker_tripped:
            reasons.append(f"Circuit breaker tripped — risk {cb_risk:.2f}")

        # 3. Alignment signal
        align_risk = max(0.0, 1.0 - alignment_score)
        risk_components["alignment"] = align_risk
        if alignment_score < 0.5:
            reasons.append(f"Low alignment score {alignment_score:.2f} — risk {align_risk:.2f}")

        # 4. Anomaly signal
        anomaly_risk = self._evaluate_anomalies(anomalies or [])
        risk_components["anomalies"] = anomaly_risk
        critical_anomalies = [a for a in (anomalies or []) if a.get("severity") == "CRITICAL"]
        if critical_anomalies:
            reasons.append(f"{len(critical_anomalies)} critical anomalies detected")

        # 5. Ethics signal
        ethics_risk = self._evaluate_ethics(ethics_result)
        risk_components["ethics"] = ethics_risk
        if ethics_result and not ethics_result.get("is_ethical", True):
            reasons.append(f"Ethical violations: {', '.join(ethics_result.get('violations', []))}")

        # 6. Autonomy bounds signal
        auto_risk = self._evaluate_autonomy(autonomy_level, autonomy_bounds)
        risk_components["autonomy"] = auto_risk
        if autonomy_level in ("SHADOW",):
            reasons.append("Shadow mode — proposals only, no execution")

        # Compute weighted composite risk score
        composite_score = sum(
            risk_components.get(k, 0.0) * w
            for k, w in self.SIGNAL_WEIGHTS.items()
        )
        composite_score = min(1.0, max(0.0, composite_score))

        # Hard rules: certain conditions always escalate risk
        if safety_state in ("STOPPED", "LOCKDOWN"):
            composite_score = max(composite_score, 0.85)
            reasons.insert(0, f"HARD RULE: safety state {safety_state} → forced high risk")
        if circuit_breaker_tripped:
            composite_score = max(composite_score, 0.50)
            reasons.insert(0, "HARD RULE: circuit breaker tripped → minimum risk 0.50")
        if any(a.get("severity") == "CRITICAL" for a in (anomalies or [])):
            composite_score = max(composite_score, 0.45)
            reasons.insert(0, "HARD RULE: critical anomaly present → minimum risk 0.45")

        # Determine decision
        if composite_score >= self.NO_GO_THRESHOLD:
            decision = Decision.ABORT
            reasons.insert(0, f"ABORT: composite risk {composite_score:.2f} exceeds threshold {self.NO_GO_THRESHOLD}")
        elif composite_score >= self.GO_THRESHOLD:
            decision = Decision.NO_GO
            reasons.insert(0, f"NO_GO: composite risk {composite_score:.2f} above GO threshold {self.GO_THRESHOLD}")
        else:
            decision = Decision.GO

        # Determine risk level
        if composite_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif composite_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif composite_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Check for supervisor overrides
        active_overrides = [o for o in self._overrides if o.get("expires", float("inf")) > time.time()]
        for override in active_overrides:
            overrides.append(f"Override by {override['supervisor']}: {override['reason']}")

        # If override forces GO, downgrade
        if decision == Decision.ABORT and any(o.get("force") == "GO" for o in active_overrides):
            decision = Decision.NO_GO
            overrides.append("ABORT downgraded to NO_GO by supervisor override")

        verdict = ArbiterVerdict(
            timestamp=time.time(),
            decision=decision.value,
            risk_level=risk_level.value,
            score=round(composite_score, 4),
            reasons=reasons,
            overrides=overrides,
            cycle=cycle,
        )
        self._verdict_history.append(verdict)

        # Keep bounded
        if len(self._verdict_history) > 500:
            self._verdict_history = self._verdict_history[-250:]

        return verdict

    def add_override(self, supervisor_id: str, reason: str, force: str = "GO",
                     duration_seconds: float = 300.0) -> Dict:
        """
        Add a supervisor override. Supervisor can force GO for a limited time.
        Only applies to non-LOCKDOWN states.
        """
        override = {
            "supervisor": supervisor_id,
            "reason": reason,
            "force": force.upper(),
            "created": time.time(),
            "expires": time.time() + duration_seconds,
        }
        self._overrides.append(override)
        return {"success": True, "override": override}

    def clear_overrides(self):
        self._overrides.clear()

    def get_status(self) -> Dict:
        """Return arbiter status and recent verdicts."""
        recent = self._verdict_history[-10:] if self._verdict_history else []
        active_overrides = [o for o in self._overrides if o.get("expires", float("inf")) > time.time()]
        return {
            "uptime_seconds": time.time() - self._started_at,
            "total_verdicts": len(self._verdict_history),
            "active_overrides": len(active_overrides),
            "recent_verdicts": [v.to_dict() for v in recent],
            "go_threshold": self.GO_THRESHOLD,
            "no_go_threshold": self.NO_GO_THRESHOLD,
        }

    def get_verdict_history(self, limit: int = 50) -> List[Dict]:
        entries = self._verdict_history[-limit:]
        return [v.to_dict() for v in entries]

    # ── Signal Evaluators ──────────────────────────────────────────

    @staticmethod
    def _evaluate_safety_state(state: str) -> float:
        risk_map = {
            "NOMINAL": 0.0,
            "PAUSED": 0.3,
            "SAFE_MODE": 0.5,
            "STOPPED": 0.9,
            "LOCKDOWN": 1.0,
        }
        return risk_map.get(state, 0.5)

    @staticmethod
    def _evaluate_circuit_breakers(tripped: bool, details: Optional[List[Dict]] = None) -> float:
        if not tripped:
            return 0.0
        if details:
            max_severity = max((d.get("severity_score", 0.5) for d in details), default=0.5)
            return min(1.0, max_severity)
        return 0.7  # Default high risk if tripped without details

    @staticmethod
    def _evaluate_anomalies(anomalies: List[Dict]) -> float:
        if not anomalies:
            return 0.0
        critical = sum(1 for a in anomalies if a.get("severity") == "CRITICAL")
        high = sum(1 for a in anomalies if a.get("severity") == "HIGH")
        medium = sum(1 for a in anomalies if a.get("severity") == "MEDIUM")
        score = critical * 0.4 + high * 0.2 + medium * 0.1
        return min(1.0, score)

    @staticmethod
    def _evaluate_ethics(result: Optional[Dict]) -> float:
        if result is None:
            return 0.0
        if result.get("is_ethical", True):
            return 0.0
        score = result.get("score", 1.0)
        return max(0.0, 1.0 - score)

    @staticmethod
    def _evaluate_autonomy(level: str, bounds: Optional[Dict]) -> float:
        risk_map = {
            "SHADOW": 0.1,
            "SUPERVISED": 0.3,
            "CONDITIONAL": 0.5,
            "FULL": 0.7,
        }
        base = risk_map.get(level.upper(), 0.5)
        if bounds and not bounds.get("can_modify_state", True):
            base *= 0.5  # Reduced risk if can't modify state
        return base
