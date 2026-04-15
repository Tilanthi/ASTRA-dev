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
ASTRA Live — Supervisor of Record System
Named human oversight with certification, shift logging, and action audit.
Phase 4 of the AGI Transformation Roadmap.

Tracks who is supervising the system, their certification level,
what actions they take, and maintains shift handoff records.
"""
import time
import json
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional
from pathlib import Path


class CertLevel(Enum):
    OBSERVER = "OBSERVER"         # Can view status, no control actions
    OPERATOR = "OPERATOR"         # Can pause/resume, approve/reject hypotheses
    ADMIN = "ADMIN"               # Can change autonomy level, override circuit breakers
    SUPERVISOR = "SUPERVISOR"     # Full authority including lockdown/unlock


CERT_HIERARCHY = {
    CertLevel.OBSERVER: 0,
    CertLevel.OPERATOR: 1,
    CertLevel.ADMIN: 2,
    CertLevel.SUPERVISOR: 3,
}

# Minimum cert level required for each action
ACTION_REQUIREMENTS = {
    "view_status": CertLevel.OBSERVER,
    "view_audit": CertLevel.OBSERVER,
    "pause": CertLevel.OPERATOR,
    "resume": CertLevel.OPERATOR,
    "approve_hypothesis": CertLevel.OPERATOR,
    "reject_hypothesis": CertLevel.OPERATOR,
    "set_autonomy_level": CertLevel.ADMIN,
    "override_circuit_breaker": CertLevel.ADMIN,
    "lockdown": CertLevel.SUPERVISOR,
    "unlock": CertLevel.SUPERVISOR,
    "certify_supervisor": CertLevel.SUPERVISOR,
}


@dataclass
class SupervisorEntry:
    supervisor_id: str
    name: str
    cert_level: str
    certified_by: str
    certified_at: float
    active: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class ShiftRecord:
    shift_id: str
    supervisor_id: str
    supervisor_name: str
    started_at: float
    ended_at: Optional[float] = None
    actions_count: int = 0
    incidents: int = 0
    handoff_notes: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ActionRecord:
    timestamp: float
    supervisor_id: str
    action: str
    details: str
    authorized: bool
    cert_level: str

    def to_dict(self):
        return asdict(self)


class SupervisorRegistry:
    """
    Manages supervisor certification, active shifts, and action logging.
    """

    STORAGE_PATH = Path("/tmp/astra_supervisors.json")

    def __init__(self):
        self._supervisors: Dict[str, SupervisorEntry] = {}
        self._shifts: List[ShiftRecord] = []
        self._actions: List[ActionRecord] = []
        self._active_shift: Optional[ShiftRecord] = None

        # Initialize with a default admin supervisor
        self._register_default_supervisors()

    def _register_default_supervisors(self):
        """Seed with default supervisors for bootstrap."""
        defaults = [
            ("system", "System Auto-Supervisor", CertLevel.SUPERVISOR, "bootstrap"),
            ("operator-1", "Default Operator", CertLevel.OPERATOR, "system"),
        ]
        for sid, name, cert, by in defaults:
            self._supervisors[sid] = SupervisorEntry(
                supervisor_id=sid,
                name=name,
                cert_level=cert.value,
                certified_by=by,
                certified_at=time.time(),
                active=True,
            )

    def register_supervisor(self, supervisor_id: str, name: str,
                            cert_level: str, certified_by: str) -> Dict:
        """Register a new supervisor. Requires SUPERVISOR cert to certify others."""
        # Check certifier authority
        certifier = self._supervisors.get(certified_by)
        if not certifier:
            return {"success": False, "error": f"Certifier {certified_by} not found"}

        try:
            target_level = CertLevel(cert_level.upper())
        except ValueError:
            return {"success": False, "error": f"Invalid cert level: {cert_level}"}

        certifier_level = CertLevel(certifier.cert_level)
        if CERT_HIERARCHY[certifier_level] < CERT_HIERARCHY[target_level]:
            return {"success": False,
                    "error": f"Certifier {certified_by} ({certifier.cert_level}) "
                             f"cannot certify at {cert_level} level"}

        entry = SupervisorEntry(
            supervisor_id=supervisor_id,
            name=name,
            cert_level=target_level.value,
            certified_by=certified_by,
            certified_at=time.time(),
            active=True,
        )
        self._supervisors[supervisor_id] = entry
        self._log_action(certified_by, "certify_supervisor",
                         f"Certified {name} ({supervisor_id}) at {cert_level}", True, certifier.cert_level)
        return {"success": True, "supervisor": entry.to_dict()}

    def check_authorization(self, supervisor_id: str, action: str) -> Dict:
        """Check if a supervisor is authorized for a given action."""
        sup = self._supervisors.get(supervisor_id)
        if not sup:
            return {"authorized": False, "error": f"Supervisor {supervisor_id} not found"}
        if not sup.active:
            return {"authorized": False, "error": f"Supervisor {supervisor_id} is inactive"}

        required_level = ACTION_REQUIREMENTS.get(action)
        if required_level is None:
            return {"authorized": False, "error": f"Unknown action: {action}"}

        sup_level = CertLevel(sup.cert_level)
        authorized = CERT_HIERARCHY[sup_level] >= CERT_HIERARCHY[required_level]

        return {
            "authorized": authorized,
            "supervisor_id": supervisor_id,
            "supervisor_level": sup.cert_level,
            "required_level": required_level.value,
            "action": action,
        }

    def execute_action(self, supervisor_id: str, action: str, details: str = "") -> Dict:
        """Authorize and log an action by a supervisor."""
        auth = self.check_authorization(supervisor_id, action)
        sup = self._supervisors.get(supervisor_id)

        record = ActionRecord(
            timestamp=time.time(),
            supervisor_id=supervisor_id,
            action=action,
            details=details,
            authorized=auth["authorized"],
            cert_level=sup.cert_level if sup else "UNKNOWN",
        )
        self._actions.append(record)

        # Update active shift
        if self._active_shift and self._active_shift.supervisor_id == supervisor_id:
            self._active_shift.actions_count += 1
            if not auth["authorized"]:
                self._active_shift.incidents += 1

        # Keep bounded
        if len(self._actions) > 1000:
            self._actions = self._actions[-500:]

        if not auth["authorized"]:
            return {"success": False, "error": auth.get("error", "Not authorized"),
                    "action_record": record.to_dict()}

        return {"success": True, "action_record": record.to_dict()}

    def start_shift(self, supervisor_id: str, handoff_notes: str = "") -> Dict:
        """Start a new supervisor shift. Ends any current shift."""
        sup = self._supervisors.get(supervisor_id)
        if not sup:
            return {"success": False, "error": f"Supervisor {supervisor_id} not found"}
        if not sup.active:
            return {"success": False, "error": f"Supervisor {supervisor_id} is inactive"}

        # End current shift
        if self._active_shift:
            self._active_shift.ended_at = time.time()
            self._active_shift.handoff_notes = handoff_notes or "Shift ended — no handoff notes"

        shift_id = f"shift-{int(time.time())}"
        shift = ShiftRecord(
            shift_id=shift_id,
            supervisor_id=supervisor_id,
            supervisor_name=sup.name,
            started_at=time.time(),
            handoff_notes=handoff_notes,
        )
        self._shifts.append(shift)
        self._active_shift = shift

        self._log_action(supervisor_id, "start_shift",
                         f"Shift {shift_id} started by {sup.name}", True, sup.cert_level)
        return {"success": True, "shift": shift.to_dict()}

    def end_shift(self, supervisor_id: str, handoff_notes: str = "") -> Dict:
        """End the current shift."""
        if not self._active_shift:
            return {"success": False, "error": "No active shift"}

        if self._active_shift.supervisor_id != supervisor_id:
            return {"success": False,
                    "error": f"Active shift belongs to {self._active_shift.supervisor_id}, not {supervisor_id}"}

        self._active_shift.ended_at = time.time()
        self._active_shift.handoff_notes = handoff_notes

        sup = self._supervisors.get(supervisor_id)
        self._log_action(supervisor_id, "end_shift",
                         f"Shift {self._active_shift.shift_id} ended", True,
                         sup.cert_level if sup else "UNKNOWN")
        completed = self._active_shift
        self._active_shift = None
        return {"success": True, "shift": completed.to_dict()}

    def get_active_shift(self) -> Optional[Dict]:
        if self._active_shift:
            return self._active_shift.to_dict()
        return None

    def get_supervisors(self) -> List[Dict]:
        return [s.to_dict() for s in self._supervisors.values()]

    def get_action_log(self, limit: int = 50) -> List[Dict]:
        return [a.to_dict() for a in self._actions[-limit:]]

    def get_shift_history(self, limit: int = 20) -> List[Dict]:
        return [s.to_dict() for s in self._shifts[-limit:]]

    def get_status(self) -> Dict:
        return {
            "total_supervisors": len(self._supervisors),
            "active_supervisors": sum(1 for s in self._supervisors.values() if s.active),
            "active_shift": self.get_active_shift(),
            "total_shifts": len(self._shifts),
            "total_actions": len(self._actions),
            "recent_actions": self.get_action_log(10),
        }

    def _log_action(self, supervisor_id: str, action: str, details: str,
                    authorized: bool, cert_level: str):
        record = ActionRecord(
            timestamp=time.time(),
            supervisor_id=supervisor_id,
            action=action,
            details=details,
            authorized=authorized,
            cert_level=cert_level,
        )
        self._actions.append(record)
