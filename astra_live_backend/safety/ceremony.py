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
ASTRA Live — Phase Commencement Ceremony Protocol
Formal procedure for autonomy level transitions.
Phase 4 of the AGI Transformation Roadmap.

Every autonomy escalation requires a formal ceremony: checklist verification,
supervisor approval, pre-flight checks, and post-transition monitoring.
"""
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional


class CeremonyState(Enum):
    PENDING = "PENDING"
    CHECKLIST = "CHECKLIST"
    APPROVAL = "APPROVAL"
    PREFLIGHT = "PREFLIGHT"
    TRANSITIONING = "TRANSITIONING"
    MONITORING = "MONITORING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    ABORTED = "ABORTED"


@dataclass
class ChecklistItem:
    id: str
    description: str
    required: bool
    verified: bool = False
    verified_by: str = ""
    verified_at: float = 0.0
    notes: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Ceremony:
    ceremony_id: str
    from_level: str
    to_level: str
    state: str
    initiated_by: str
    initiated_at: float
    checklist: List[Dict]
    approved_by: str = ""
    approved_at: float = 0.0
    completed_at: float = 0.0
    preflight_checks: List[Dict] = None
    monitoring_until: float = 0.0
    rejection_reason: str = ""

    def to_dict(self):
        d = asdict(self)
        if self.preflight_checks is None:
            d["preflight_checks"] = []
        return d


# Transition checklists — different requirements per escalation level
TRANSITION_CHECKLISTS = {
    ("SHADOW", "SUPERVISED"): [
        ("verify_safety_nominal", "Safety controller must be in NOMINAL state", True),
        ("verify_no_critical_anomalies", "No CRITICAL anomalies in last 10 cycles", True),
        ("verify_alignment_above_60", "Alignment score ≥ 0.60 across all dimensions", True),
        ("verify_supervisor_present", "Active supervisor shift must be established", True),
        ("review_shadow_proposals", "Review all shadow-mode proposals from last session", False),
        ("confirm_monitoring_plan", "Post-transition monitoring plan documented", False),
    ],
    ("SUPERVISED", "CONDITIONAL"): [
        ("verify_safety_nominal", "Safety controller must be in NOMINAL state", True),
        ("verify_no_critical_anomalies", "No CRITICAL anomalies in last 20 cycles", True),
        ("verify_alignment_above_75", "Alignment score ≥ 0.75 across all dimensions", True),
        ("verify_supervisor_admin", "Supervisor must have ADMIN certification or higher", True),
        ("verify_circuit_breakers_clear", "All circuit breakers must be clear", True),
        ("verify_audit_trail_current", "Audit trail must be current and complete", True),
        ("review_supervised_decisions", "Review all supervised decisions from current session", True),
        ("verify_ethics_clean", "No ethical violations in last 50 cycles", True),
        ("document_capability_bounds", "Document exact capability bounds for conditional mode", False),
    ],
    ("CONDITIONAL", "FULL"): [
        ("verify_safety_nominal", "Safety controller must be in NOMINAL state", True),
        ("verify_no_anomalies_50", "Zero anomalies in last 50 cycles", True),
        ("verify_alignment_above_90", "Alignment score ≥ 0.90 across all dimensions", True),
        ("verify_supervisor_super", "Supervisor must have SUPERVISOR certification", True),
        ("verify_circuit_breakers_clear", "All circuit breakers must be clear", True),
        ("verify_audit_trail_current", "Full audit trail review completed", True),
        ("verify_ethics_clean_100", "No ethical violations in last 100 cycles", True),
        ("verify_system_confidence", "System confidence ≥ 0.70", True),
        ("red_team_exercise_passed", "Adversarial test suite passed within last 24h", True),
        ("safety_case_reviewed", "Safety Case document reviewed and signed off", True),
        ("orp_checklist_complete", "Operational Readiness Plan checklist 100% complete", True),
        ("supervisor_shift_active", "Dedicated supervisor shift active with SUPERVISOR cert", True),
    ],
}

# Preflight checks — run immediately before transition
PREFLIGHT_CHECKS = [
    ("safety_state", lambda ctx: ctx.get("safety_state") == "NOMINAL"),
    ("engine_running", lambda ctx: ctx.get("engine_running", False)),
    ("no_tripped_breakers", lambda ctx: not ctx.get("circuit_breaker_tripped", False)),
    ("alignment_above_min", lambda ctx: ctx.get("alignment_score", 0) >= 0.5),
]


class CeremonyProtocol:
    """
    Manages phase commencement ceremonies for autonomy transitions.
    """

    def __init__(self):
        self._ceremonies: List[Ceremony] = []
        self._current: Optional[Ceremony] = None

    def initiate(self, from_level: str, to_level: str, supervisor_id: str) -> Dict:
        """
        Initiate a phase commencement ceremony for a transition.
        Returns the ceremony with its checklist.
        """
        if self._current and self._current.state not in (
            CeremonyState.COMPLETED.value, CeremonyState.REJECTED.value,
            CeremonyState.ABORTED.value
        ):
            return {"success": False,
                    "error": f"Ceremony {self._current.ceremony_id} already in progress",
                    "current_ceremony": self._current.to_dict()}

        key = (from_level.upper(), to_level.upper())
        checklist_items = TRANSITION_CHECKLISTS.get(key)
        if not checklist_items:
            return {"success": False,
                    "error": f"No checklist defined for {from_level} → {to_level} transition. "
                             f"Valid transitions: {list(TRANSITION_CHECKLISTS.keys())}"}

        checklist = [
            ChecklistItem(id=item_id, description=desc, required=req)
            for item_id, desc, req in checklist_items
        ]

        ceremony_id = f"ceremony-{int(time.time())}"
        ceremony = Ceremony(
            ceremony_id=ceremony_id,
            from_level=from_level.upper(),
            to_level=to_level.upper(),
            state=CeremonyState.CHECKLIST.value,
            initiated_by=supervisor_id,
            initiated_at=time.time(),
            checklist=[c.to_dict() for c in checklist],
        )
        self._ceremonies.append(ceremony)
        self._current = ceremony

        return {"success": True, "ceremony": ceremony.to_dict()}

    def verify_checklist_item(self, item_id: str, supervisor_id: str,
                              notes: str = "") -> Dict:
        """Verify a single checklist item."""
        if not self._current:
            return {"success": False, "error": "No active ceremony"}

        if self._current.state != CeremonyState.CHECKLIST.value:
            return {"success": False,
                    "error": f"Ceremony not in CHECKLIST state (current: {self._current.state})"}

        for item in self._current.checklist:
            if item["id"] == item_id:
                item["verified"] = True
                item["verified_by"] = supervisor_id
                item["verified_at"] = time.time()
                item["notes"] = notes

                # Check if all required items are verified
                all_required_done = all(
                    i["verified"] for i in self._current.checklist if i["required"]
                )
                if all_required_done:
                    self._current.state = CeremonyState.APPROVAL.value

                return {"success": True, "ceremony": self._current.to_dict()}

        return {"success": False, "error": f"Checklist item {item_id} not found"}

    def approve(self, supervisor_id: str) -> Dict:
        """Approve the ceremony after checklist completion. Runs preflight checks."""
        if not self._current:
            return {"success": False, "error": "No active ceremony"}

        if self._current.state != CeremonyState.APPROVAL.value:
            return {"success": False,
                    "error": f"Ceremony not in APPROVAL state (current: {self._current.state})"}

        # Verify all required checklist items
        required = [i for i in self._current.checklist if i["required"]]
        unverified = [i for i in required if not i["verified"]]
        if unverified:
            return {"success": False,
                    "error": f"Cannot approve — {len(unverified)} required items unverified",
                    "unverified": [i["id"] for i in unverified]}

        self._current.approved_by = supervisor_id
        self._current.approved_at = time.time()
        self._current.state = CeremonyState.PREFLIGHT.value

        return {"success": True, "ceremony": self._current.to_dict(),
                "message": "Approved — run preflight checks before transitioning"}

    def run_preflight(self, context: Dict) -> Dict:
        """Run preflight checks with current system context."""
        if not self._current:
            return {"success": False, "error": "No active ceremony"}

        if self._current.state != CeremonyState.PREFLIGHT.value:
            return {"success": False,
                    "error": f"Ceremony not in PREFLIGHT state (current: {self._current.state})"}

        results = []
        all_passed = True
        for check_id, check_fn in PREFLIGHT_CHECKS:
            try:
                passed = check_fn(context)
            except Exception as e:
                passed = False

            results.append({"id": check_id, "passed": passed})
            if not passed:
                all_passed = False

        self._current.preflight_checks = results

        if all_passed:
            self._current.state = CeremonyState.TRANSITIONING.value
            return {"success": True, "ceremony": self._current.to_dict(),
                    "preflight_passed": True, "results": results}
        else:
            self._current.state = CeremonyState.ABORTED.value
            return {"success": False, "ceremony": self._current.to_dict(),
                    "preflight_passed": False, "results": results,
                    "error": "Preflight checks failed — ceremony aborted"}

    def complete(self, monitoring_duration: float = 300.0) -> Dict:
        """Mark ceremony as transitioning to monitoring phase."""
        if not self._current:
            return {"success": False, "error": "No active ceremony"}

        if self._current.state != CeremonyState.TRANSITIONING.value:
            return {"success": False,
                    "error": f"Ceremony not in TRANSITIONING state (current: {self._current.state})"}

        self._current.state = CeremonyState.MONITORING.value
        self._current.monitoring_until = time.time() + monitoring_duration

        return {"success": True, "ceremony": self._current.to_dict(),
                "monitoring_until": self._current.monitoring_until}

    def finalize_monitoring(self) -> Dict:
        """Check if monitoring period is complete and finalize."""
        if not self._current:
            return {"success": False, "error": "No active ceremony"}

        if self._current.state != CeremonyState.MONITORING.value:
            return {"success": False,
                    "error": f"Ceremony not in MONITORING state (current: {self._current.state})"}

        if time.time() < self._current.monitoring_until:
            remaining = self._current.monitoring_until - time.time()
            return {"success": False,
                    "error": f"Monitoring period not complete — {remaining:.0f}s remaining"}

        self._current.state = CeremonyState.COMPLETED.value
        self._current.completed_at = time.time()
        completed = self._current
        self._current = None

        return {"success": True, "ceremony": completed.to_dict()}

    def reject(self, supervisor_id: str, reason: str) -> Dict:
        """Reject the ceremony."""
        if not self._current:
            return {"success": False, "error": "No active ceremony"}

        self._current.state = CeremonyState.REJECTED.value
        self._current.rejection_reason = reason
        completed = self._current
        self._current = None

        return {"success": True, "ceremony": completed.to_dict()}

    def abort(self, reason: str = "") -> Dict:
        """Abort the current ceremony."""
        if not self._current:
            return {"success": False, "error": "No active ceremony"}

        self._current.state = CeremonyState.ABORTED.value
        self._current.rejection_reason = reason or "Aborted"
        completed = self._current
        self._current = None

        return {"success": True, "ceremony": completed.to_dict()}

    def get_current(self) -> Optional[Dict]:
        if self._current:
            return self._current.to_dict()
        return None

    def get_history(self, limit: int = 20) -> List[Dict]:
        return [c.to_dict() for c in self._ceremonies[-limit:]]

    def get_status(self) -> Dict:
        return {
            "active_ceremony": self.get_current(),
            "total_ceremonies": len(self._ceremonies),
            "completed": sum(1 for c in self._ceremonies if c.state == CeremonyState.COMPLETED.value),
            "rejected": sum(1 for c in self._ceremonies if c.state == CeremonyState.REJECTED.value),
            "aborted": sum(1 for c in self._ceremonies if c.state == CeremonyState.ABORTED.value),
            "valid_transitions": list(TRANSITION_CHECKLISTS.keys()),
        }
