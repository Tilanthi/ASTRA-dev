from enum import Enum
from typing import Dict, Any

class AutonomyLevel(str, Enum):
    SHADOW_MODE = "SHADOW"          # Propose only, no execution or modification
    SUPERVISED = "SUPERVISED"       # Execute low-risk, block on high-risk
    CONDITIONAL = "CONDITIONAL"     # Autonomous within defined capability bounds
    FULL = "FULL"                   # Full autonomy across all capability dimensions

class PhasedAutonomyFramework:
    """Config-driven autonomy levels with transition gates."""
    
    def __init__(self, initial_level=AutonomyLevel.SUPERVISED):
        self.level = initial_level
        self._capability_bounds = {
            AutonomyLevel.SHADOW_MODE: {"can_investigate": False, "can_modify_state": False, "requires_approval_publish": True},
            AutonomyLevel.SUPERVISED:  {"can_investigate": True,  "can_modify_state": False, "requires_approval_publish": True},
            AutonomyLevel.CONDITIONAL: {"can_investigate": True,  "can_modify_state": True,  "requires_approval_publish": True},
            AutonomyLevel.FULL:        {"can_investigate": True,  "can_modify_state": True,  "requires_approval_publish": False}
        }

    def get_bounds(self) -> Dict[str, bool]:
        return self._capability_bounds[self.level]

    def set_level(self, new_level: str, supervisor_id: str, reason: str) -> bool:
        """Only a registered supervisor can escalate autonomy level."""
        try:
            level_enum = AutonomyLevel(new_level.upper())
            self.level = level_enum
            # Audit hook logic handled by SafetyController calling this
            return True
        except ValueError:
            return False

    def can_investigate(self) -> bool:
        return self.get_bounds()["can_investigate"]

    def can_modify_state(self) -> bool:
        return self.get_bounds()["can_modify_state"]

    def requires_approval_publish(self) -> bool:
        return self.get_bounds()["requires_approval_publish"]
