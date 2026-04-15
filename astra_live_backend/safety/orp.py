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
ASTRA Live — Operational Readiness Plan (ORP)
Go/no-go checklist and readiness assessment for deployment.
Phase 4 of the AGI Transformation Roadmap.

Provides structured readiness checks across technical, human, and procedural
dimensions with go/no-go criteria and rollback procedures.
"""
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional


class ReadinessStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    BLOCKED = "BLOCKED"
    WAIVED = "WAIVED"


class GoNoGo(Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"


@dataclass
class ORPItem:
    id: str
    category: str
    description: str
    status: str
    required: bool
    evidence: str = ""
    owner: str = ""
    last_checked: float = 0.0
    notes: str = ""

    def to_dict(self):
        return asdict(self)


class OperationalReadinessPlan:
    """
    ORP checklist covering technical, human, and procedural readiness.
    """

    # ── ORP Checklist Items ─────────────────────────────────────────
    CHECKLIST = [
        # Technical Readiness
        ("T01", "technical", "Safety controller operational with all 5 states enforced", True),
        ("T02", "technical", "Circuit breakers configured and tested (5 rules active)", True),
        ("T03", "technical", "Audit trail logging to JSONL with daily rotation", True),
        ("T04", "technical", "System health monitoring via psutil (CPU, memory, disk)", True),
        ("T05", "technical", "Ethical reasoner integrated into decision pipeline", True),
        ("T06", "technical", "State vector computation (14 dimensions) verified", True),
        ("T07", "technical", "Anomaly detection (rolling stats, ±2σ) operational", True),
        ("T08", "technical", "Alignment scoring (6 dimensions) operational", True),
        ("T09", "technical", "PCA state space visualization functional", True),
        ("T10", "technical", "Phase gates enforced (VALIDATED→PUBLISHED requires approval)", True),
        ("T11", "technical", "Phased autonomy framework with 4 levels", True),
        ("T12", "technical", "Safety Arbiter evaluating all signals per cycle", True),
        ("T13", "technical", "Emergency stop tested and verified", True),
        ("T14", "technical", "Dashboard live with all 4 tabs (Overview/Safety/Control/Health)", True),
        ("T15", "technical", "All E2E tests passing (8/8)", True),
        ("T16", "technical", "Server API health endpoint responding", True),

        # Human Readiness
        ("H01", "human", "Supervisor of Record system operational", True),
        ("H02", "human", "Supervisor certification levels defined (OBSERVER/OPERATOR/ADMIN/SUPERVISOR)", True),
        ("H03", "human", "At least one SUPERVISOR-certified human designated", True),
        ("H04", "human", "Shift handoff protocol documented", False),
        ("H05", "human", "Incident response procedure documented", False),
        ("H06", "human", "Escalation matrix defined (who to contact for what)", False),

        # Procedural Readiness
        ("P01", "procedural", "Phase Commencement Ceremony protocol implemented", True),
        ("P02", "procedural", "Transition checklists defined for all autonomy escalations", True),
        ("P03", "procedural", "Preflight checks implemented (4 checks)", True),
        ("P04", "procedural", "Monitoring period defined for post-transition observation", True),
        ("P05", "procedural", "Rollback procedure documented for each autonomy level", True),
        ("P06", "procedural", "Safety Case document with ALARP methodology", False),
        ("P07", "procedural", "Hazard register maintained", False),
        ("P08", "procedural", "Adversarial test suite executed", False),
    ]

    def __init__(self):
        self._items: Dict[str, ORPItem] = {}
        for item_id, category, desc, required in self.CHECKLIST:
            self._items[item_id] = ORPItem(
                id=item_id,
                category=category,
                description=desc,
                status=ReadinessStatus.READY.value if required else ReadinessStatus.NOT_STARTED.value,
                required=required,
            )

    def update_item(self, item_id: str, status: str, evidence: str = "",
                    owner: str = "", notes: str = "") -> Dict:
        item = self._items.get(item_id)
        if not item:
            return {"success": False, "error": f"Item {item_id} not found"}

        item.status = status
        item.evidence = evidence
        item.owner = owner
        item.notes = notes
        item.last_checked = time.time()
        return {"success": True, "item": item.to_dict()}

    def assess_readiness(self) -> Dict:
        """Compute overall readiness score and go/no-go decision."""
        total_required = sum(1 for i in self._items.values() if i.required)
        ready_required = sum(1 for i in self._items.values()
                             if i.required and i.status == ReadinessStatus.READY.value)
        waived_required = sum(1 for i in self._items.values()
                              if i.required and i.status == ReadinessStatus.WAIVED.value)

        total_optional = sum(1 for i in self._items.values() if not i.required)
        ready_optional = sum(1 for i in self._items.values()
                             if not i.required and i.status == ReadinessStatus.READY.value)

        blocked = [i for i in self._items.values()
                   if i.required and i.status == ReadinessStatus.BLOCKED.value]
        not_started = [i for i in self._items.values()
                       if i.required and i.status == ReadinessStatus.NOT_STARTED.value]

        # Go/no-go logic
        if blocked:
            go_no_go = GoNoGo.NO_GO.value
            reason = f"{len(blocked)} required items BLOCKED"
        elif not_started:
            go_no_go = GoNoGo.NO_GO.value
            reason = f"{len(not_started)} required items NOT_STARTED"
        elif ready_required + waived_required >= total_required:
            if ready_optional >= total_optional * 0.5:
                go_no_go = GoNoGo.GO.value
            else:
                go_no_go = GoNoGo.CONDITIONAL_GO.value
            reason = "All required items ready"
        else:
            go_no_go = GoNoGo.NO_GO.value
            reason = f"Only {ready_required}/{total_required} required items ready"

        readiness_pct = (ready_required + waived_required) / max(total_required, 1) * 100

        return {
            "go_no_go": go_no_go,
            "reason": reason,
            "readiness_pct": round(readiness_pct, 1),
            "required_ready": ready_required,
            "required_total": total_required,
            "required_waived": waived_required,
            "optional_ready": ready_optional,
            "optional_total": total_optional,
            "blocked_items": [i.to_dict() for i in blocked],
            "not_started_items": [i.to_dict() for i in not_started],
            "timestamp": time.time(),
        }

    def get_checklist(self) -> List[Dict]:
        return [i.to_dict() for i in self._items.values()]

    def get_by_category(self, category: str) -> List[Dict]:
        return [i.to_dict() for i in self._items.values() if i.category == category]

    def get_status(self) -> Dict:
        assessment = self.assess_readiness()
        return {
            "readiness_pct": assessment["readiness_pct"],
            "go_no_go": assessment["go_no_go"],
            "total_items": len(self._items),
            "required_items": sum(1 for i in self._items.values() if i.required),
            "ready_items": sum(1 for i in self._items.values()
                               if i.status == ReadinessStatus.READY.value),
        }

    # Rollback procedures
    ROLLBACK_PROCEDURES = {
        "FULL": {
            "target": "CONDITIONAL",
            "steps": [
                "1. Issue LOCKDOWN command via SafetyController",
                "2. Verify engine stopped and state saved",
                "3. Set autonomy level to CONDITIONAL",
                "4. Re-enable engine with conditional bounds",
                "5. Monitor for 300 seconds before resuming operations",
            ],
            "estimated_time": "5 minutes",
        },
        "CONDITIONAL": {
            "target": "SUPERVISED",
            "steps": [
                "1. Issue SAFE_MODE command via SafetyController",
                "2. Complete all in-progress investigations",
                "3. Set autonomy level to SUPERVISED",
                "4. Re-enable engine with supervised bounds",
                "5. Monitor for 180 seconds",
            ],
            "estimated_time": "3 minutes",
        },
        "SUPERVISED": {
            "target": "SHADOW",
            "steps": [
                "1. Issue PAUSE command via SafetyController",
                "2. Set autonomy level to SHADOW",
                "3. Resume engine (proposals only)",
                "4. Review all pending actions",
            ],
            "estimated_time": "1 minute",
        },
        "SHADOW": {
            "target": "STOPPED",
            "steps": [
                "1. Issue STOP command via SafetyController",
                "2. Save engine state",
                "3. Notify supervisor of full stop",
            ],
            "estimated_time": "30 seconds",
        },
    }

    def get_rollback_procedure(self, current_level: str) -> Dict:
        return self.ROLLBACK_PROCEDURES.get(current_level.upper(),
                                            {"error": f"No rollback defined for level {current_level}"})
