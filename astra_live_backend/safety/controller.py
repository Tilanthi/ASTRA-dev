"""
ASTRA Live — Safety Controller
Unified safety bus for the discovery engine.
Phase 1 of the AGI Transformation Roadmap.

Safety States:
  NOMINAL   — engine running normally
  PAUSED    — OODA cycle paused, state preserved
  SAFE_MODE — read-only analysis only, no hypothesis advancement
  STOPPED   — emergency stop, engine halted, state saved
  LOCKDOWN  — full lockdown, no operations permitted
"""
import time
import threading
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
from astra_live_backend.safety.audit import AuditLogger


class SafetyState(Enum):
    NOMINAL = "NOMINAL"
    PAUSED = "PAUSED"
    SAFE_MODE = "SAFE_MODE"
    STOPPED = "STOPPED"
    LOCKDOWN = "LOCKDOWN"


class SafetyAction(Enum):
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    STOP = "STOP"
    SAFE_MODE = "SAFE_MODE"
    LOCKDOWN = "LOCKDOWN"
    RESET = "RESET"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    STATE_CHANGE = "STATE_CHANGE"


class SafetySeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEntry:
    timestamp: float
    action: str
    from_state: str
    to_state: str
    reason: str
    operator: str = "system"

    def to_dict(self):
        return asdict(self)


# Valid state transitions — enforced to prevent illegal transitions
VALID_TRANSITIONS = {
    SafetyState.NOMINAL: {SafetyState.PAUSED, SafetyState.SAFE_MODE, SafetyState.STOPPED, SafetyState.LOCKDOWN},
    SafetyState.PAUSED: {SafetyState.NOMINAL, SafetyState.SAFE_MODE, SafetyState.STOPPED, SafetyState.LOCKDOWN},
    SafetyState.SAFE_MODE: {SafetyState.NOMINAL, SafetyState.PAUSED, SafetyState.STOPPED, SafetyState.LOCKDOWN},
    SafetyState.STOPPED: {SafetyState.NOMINAL, SafetyState.LOCKDOWN},
    SafetyState.LOCKDOWN: set(),  # Cannot leave lockdown without reset
}


class SafetyController:
    """
    Singleton safety controller — the unified safety bus for ASTRA.

    All safety-critical operations route through this controller.
    It owns the safety state, enforces transitions, and maintains the audit log.
    """
    _instance: Optional['SafetyController'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._state = SafetyState.NOMINAL
        self._state_lock = threading.Lock()
        self._audit_log: list[AuditEntry] = []
        self._engine_ref = None  # Set by engine on init
        self._started_at = time.time()
        self._logger = AuditLogger()

        self._audit(SafetyAction.STATE_CHANGE, SafetyState.NOMINAL, SafetyState.NOMINAL,
                    "Safety controller initialized")

    @property
    def state(self) -> SafetyState:
        return self._state

    def bind_engine(self, engine):
        """Bind the discovery engine to this controller. Called once at engine init."""
        self._engine_ref = engine
        self._audit(SafetyAction.STATE_CHANGE, self._state, self._state,
                    f"Engine bound to safety controller (cycle={getattr(engine, 'cycle_count', 0)})")

    def _audit(self, action: SafetyAction, from_state: SafetyState, to_state: SafetyState,
               reason: str, operator: str = "system"):
        entry = AuditEntry(
            timestamp=time.time(),
            action=action.value,
            from_state=from_state.value,
            to_state=to_state.value,
            reason=reason,
            operator=operator,
        )
        self._audit_log.append(entry)
        # Keep audit log bounded
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-500:]

            # Sync to AuditLogger if configured
            if hasattr(self, '_logger') and self._logger:
                self._logger.log_event("SafetyController", action.value, {
                    "from_state": from_state.value,
                    "to_state": to_state.value,
                    "reason": reason
                }, operator)

    def _transition(self, target: SafetyState, action: SafetyAction,
                    reason: str, operator: str = "api") -> dict:
        """Attempt a state transition. Returns result dict."""
        with self._state_lock:
            old = self._state

            # Validate transition
            if target not in VALID_TRANSITIONS.get(old, set()):
                msg = f"Invalid transition: {old.value} → {target.value}"
                self._audit(action, old, old, f"REJECTED: {msg}", operator)
                return {"success": False, "error": msg, "state": old.value}

            self._state = target
            self._audit(action, old, target, reason, operator)

            return {"success": True, "from": old.value, "to": target.value, "reason": reason}

    # ── Public API ─────────────────────────────────────────────────

    def pause(self, reason: str = "Manual pause", operator: str = "api") -> dict:
        """Pause the OODA cycle, preserving state."""
        result = self._transition(SafetyState.PAUSED, SafetyAction.PAUSE, reason, operator)
        if result["success"] and self._engine_ref:
            self._engine_ref.running = False
        return result

    def resume(self, reason: str = "Manual resume", operator: str = "api") -> dict:
        """Resume from PAUSED or SAFE_MODE to NOMINAL."""
        result = self._transition(SafetyState.NOMINAL, SafetyAction.RESUME, reason, operator)
        if result["success"] and self._engine_ref:
            # Re-start the engine loop if it was running before
            if not self._engine_ref.running:
                self._engine_ref.start(interval=20.0)
        return result

    def emergency_stop(self, reason: str = "Emergency stop", operator: str = "api") -> dict:
        """Emergency stop: halt engine, save state, full stop."""
        result = self._transition(SafetyState.STOPPED, SafetyAction.STOP, reason, operator)
        if result["success"] and self._engine_ref:
            self._engine_ref.running = False
            # Save state snapshot
            try:
                import json
                state = self._engine_ref.get_state()
                state['_emergency_stop_time'] = time.time()
                state['_emergency_stop_reason'] = reason
                with open('/tmp/astra_emergency_state.json', 'w') as f:
                    json.dump(state, f, default=str)
            except Exception:
                pass  # Don't let state saving prevent the stop
        return result

    def safe_mode(self, reason: str = "Switched to safe mode", operator: str = "api") -> dict:
        """Switch to read-only analysis mode. No hypothesis advancement."""
        return self._transition(SafetyState.SAFE_MODE, SafetyAction.SAFE_MODE, reason, operator)

    def lockdown(self, reason: str = "Lockdown initiated", operator: str = "api") -> dict:
        """Full lockdown — no operations permitted. Requires code-level reset."""
        result = self._transition(SafetyState.LOCKDOWN, SafetyAction.LOCKDOWN, reason, operator)
        if result["success"] and self._engine_ref:
            self._engine_ref.running = False
        return result

    def reset_from_lockdown(self, reason: str = "Reset from lockdown", operator: str = "api") -> dict:
        """Reset from LOCKDOWN to NOMINAL. This is the only way out of lockdown."""
        with self._state_lock:
            old = self._state
            if old != SafetyState.LOCKDOWN:
                return {"success": False, "error": f"Not in LOCKDOWN (current: {old.value})", "state": old.value}
            self._state = SafetyState.NOMINAL
            self._audit(SafetyAction.RESET, old, SafetyState.NOMINAL, reason, operator)
            return {"success": True, "from": old.value, "to": SafetyState.NOMINAL.value, "reason": reason}

    # ── Safety Checks (called by engine before operations) ─────────

    def can_advance_hypotheses(self) -> bool:
        """Check if hypothesis advancement is allowed in the current state."""
        return self._state in (SafetyState.NOMINAL,)

    def can_run_cycle(self) -> bool:
        """Check if a discovery cycle is allowed."""
        return self._state in (SafetyState.NOMINAL,)

    def can_investigate(self) -> bool:
        """Check if investigation (data generation, analysis) is allowed."""
        return self._state in (SafetyState.NOMINAL, SafetyState.SAFE_MODE)

    def can_modify_state(self) -> bool:
        """Check if state-modifying operations are allowed."""
        return self._state in (SafetyState.NOMINAL,)

    # ── Status & Audit ─────────────────────────────────────────────

    def get_status(self) -> dict:
        """Return current safety state with metadata."""
        return {
            "state": self._state.value,
            "uptime_seconds": time.time() - self._started_at,
            "can_advance_hypotheses": self.can_advance_hypotheses(),
            "can_run_cycle": self.can_run_cycle(),
            "can_investigate": self.can_investigate(),
            "can_modify_state": self.can_modify_state(),
            "audit_log_size": len(self._audit_log),
            "timestamp": time.time(),
        }

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        """Return recent audit log entries."""
        entries = self._audit_log[-limit:]
        return [e.to_dict() for e in entries]

    def get_full_status(self) -> dict:
        """Return full safety status including audit log."""
        status = self.get_status()
        status["audit_log"] = self.get_audit_log(50)
        return status
