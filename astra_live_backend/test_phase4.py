"""
ASTRA Live — Phase 4 Adversarial Test Suite
Red-team scenarios for safety infrastructure validation.

Tests cover:
1. Safety Arbiter decision logic
2. Supervisor authorization boundaries
3. Ceremony protocol enforcement
4. ORP readiness assessment
5. Safety Case hazard evaluation
6. Integration scenarios (adversarial combinations)
"""
import sys
import time
sys.path.insert(0, ".")

from astra_live_backend.safety.arbiter import SafetyArbiter, Decision, RiskLevel
from astra_live_backend.safety.supervisor import SupervisorRegistry, CertLevel
from astra_live_backend.safety.ceremony import CeremonyProtocol, CeremonyState
from astra_live_backend.safety.orp import OperationalReadinessPlan, ReadinessStatus
from astra_live_backend.safety.safety_case import SafetyCase


# ── Helpers ──────────────────────────────────────────────────────

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  ✅ {name}")

    def fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ❌ {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"  Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print(f"\n  Failures:")
            for name, reason in self.errors:
                print(f"    - {name}: {reason}")
        return self.failed == 0


results = TestResult()


# ═══════════════════════════════════════════════════════════════
# 1. Safety Arbiter Tests
# ═══════════════════════════════════════════════════════════════

print("\n🔍 1. Safety Arbiter — Decision Logic")

arbiter = SafetyArbiter()

# Test 1.1: GO on clean nominal state
v = arbiter.evaluate_cycle(
    safety_state="NOMINAL",
    circuit_breaker_tripped=False,
    alignment_score=0.9,
    anomalies=[],
    cycle=1,
)
if v.decision == "GO" and v.score < 0.3:
    results.ok("1.1 Clean nominal → GO")
else:
    results.fail("1.1 Clean nominal", f"Expected GO/score<0.3, got {v.decision}/{v.score}")

# Test 1.2: ABORT on LOCKDOWN
v = arbiter.evaluate_cycle(
    safety_state="LOCKDOWN",
    circuit_breaker_tripped=False,
    cycle=2,
)
if v.decision == "ABORT":
    results.ok("1.2 LOCKDOWN → ABORT")
else:
    results.fail("1.2 LOCKDOWN", f"Expected ABORT, got {v.decision}")

# Test 1.3: ABORT on tripped circuit breaker + low alignment
v = arbiter.evaluate_cycle(
    safety_state="NOMINAL",
    circuit_breaker_tripped=True,
    alignment_score=0.2,
    cycle=3,
)
if v.decision in ("ABORT", "NO_GO"):
    results.ok("1.3 Tripped breaker + low alignment → " + v.decision)
else:
    results.fail("1.3 Adversarial combo", f"Expected ABORT/NO_GO, got {v.decision}")

# Test 1.4: ABORT on critical anomalies
v = arbiter.evaluate_cycle(
    safety_state="NOMINAL",
    circuit_breaker_tripped=False,
    anomalies=[{"severity": "CRITICAL"}, {"severity": "CRITICAL"}, {"severity": "HIGH"}],
    cycle=4,
)
if v.decision in ("ABORT", "NO_GO"):
    results.ok("1.4 Multiple critical anomalies → " + v.decision)
else:
    results.fail("1.4 Critical anomalies", f"Expected ABORT/NO_GO, got {v.decision}")

# Test 1.5: Override can downgrade ABORT
arbiter2 = SafetyArbiter()
arbiter2.add_override("admin-1", "Emergency override", force="GO", duration_seconds=60)
v = arbiter2.evaluate_cycle(
    safety_state="STOPPED",
    circuit_breaker_tripped=True,
    cycle=5,
)
# STOPPED should produce ABORT, but override should downgrade
if len(v.overrides) > 0:
    results.ok("1.5 Override registered on ABORT")
else:
    results.fail("1.5 Override", "Override not applied")

# Test 1.6: Risk level classification
arbiter3 = SafetyArbiter()
v = arbiter3.evaluate_cycle(safety_state="NOMINAL", circuit_breaker_tripped=False, cycle=1)
if v.risk_level == "LOW":
    results.ok("1.6 Risk level LOW on clean state")
else:
    results.fail("1.6 Risk level", f"Expected LOW, got {v.risk_level}")


# ═══════════════════════════════════════════════════════════════
# 2. Supervisor Registry Tests
# ═══════════════════════════════════════════════════════════════

print("\n🔍 2. Supervisor Registry — Authorization Boundaries")

registry = SupervisorRegistry()

# Test 2.1: OPERATOR can pause
auth = registry.check_authorization("operator-1", "pause")
if auth["authorized"]:
    results.ok("2.1 OPERATOR can pause")
else:
    results.fail("2.1 OPERATOR pause", f"Not authorized: {auth}")

# Test 2.2: OPERATOR cannot lockdown
auth = registry.check_authorization("operator-1", "lockdown")
if not auth["authorized"]:
    results.ok("2.2 OPERATOR cannot lockdown")
else:
    results.fail("2.2 OPERATOR lockdown", "Should not be authorized")

# Test 2.3: Register supervisor at OPERATOR level
result = registry.register_supervisor("op-2", "Test Operator", "OPERATOR", "system")
if result["success"]:
    results.ok("2.3 Register OPERATOR supervisor")
else:
    results.fail("2.3 Register", result.get("error", ""))

# Test 2.4: OPERATOR cannot certify ADMIN
result = registry.register_supervisor("admin-test", "Test Admin", "ADMIN", "op-2")
if not result["success"]:
    results.ok("2.4 OPERATOR cannot certify ADMIN")
else:
    results.fail("2.4 Cert escalation", "OPERATOR should not certify ADMIN")

# Test 2.5: SYSTEM can certify ADMIN
result = registry.register_supervisor("admin-1", "Admin One", "ADMIN", "system")
if result["success"]:
    results.ok("2.5 SYSTEM can certify ADMIN")
else:
    results.fail("2.5 SYSTEM cert", result.get("error", ""))

# Test 2.6: Shift management
result = registry.start_shift("admin-1", "Starting test shift")
if result["success"]:
    results.ok("2.6 Start shift")
else:
    results.fail("2.6 Start shift", result.get("error", ""))

# Test 2.7: Action logging
result = registry.execute_action("admin-1", "pause", "Testing pause authorization")
if result["success"]:
    results.ok("2.7 Authorized action logged")
else:
    results.fail("2.7 Action log", result.get("error", ""))

# Test 2.8: Unauthorized action rejected
result = registry.execute_action("operator-1", "lockdown", "Should fail")
if not result["success"]:
    results.ok("2.8 Unauthorized action rejected")
else:
    results.fail("2.8 Auth boundary", "lockdown should require SUPERVISOR")

# Test 2.9: Unknown supervisor rejected
auth = registry.check_authorization("unknown-user", "pause")
if not auth["authorized"]:
    results.ok("2.9 Unknown supervisor rejected")
else:
    results.fail("2.9 Unknown user", "Should not be authorized")


# ═══════════════════════════════════════════════════════════════
# 3. Ceremony Protocol Tests
# ═══════════════════════════════════════════════════════════════

print("\n🔍 3. Ceremony Protocol — Transition Enforcement")

ceremony = CeremonyProtocol()

# Test 3.1: Initiate valid transition
result = ceremony.initiate("SHADOW", "SUPERVISED", "admin-1")
if result["success"]:
    results.ok("3.1 Initiate SHADOW→SUPERVISED")
else:
    results.fail("3.1 Initiate", result.get("error", ""))

# Test 3.2: Cannot initiate another while one is active
result = ceremony.initiate("SUPERVISED", "CONDITIONAL", "admin-1")
if not result["success"]:
    results.ok("3.2 Cannot double-initiate")
else:
    results.fail("3.2 Double initiate", "Should fail while ceremony active")

# Test 3.3: Verify checklist items
ceremony.verify_checklist_item("verify_safety_nominal", "admin-1", "State is NOMINAL")
ceremony.verify_checklist_item("verify_no_critical_anomalies", "admin-1", "No critical")
ceremony.verify_checklist_item("verify_alignment_above_60", "admin-1", "Score 0.85")
ceremony.verify_checklist_item("verify_supervisor_present", "admin-1", "Shift active")

current = ceremony.get_current()
unverified = [i for i in current["checklist"] if i["required"] and not i["verified"]]
if len(unverified) == 0:
    results.ok("3.3 All required items verified")
else:
    results.fail("3.3 Verification", f"{len(unverified)} items still unverified")

# Test 3.4: Approve after checklist
result = ceremony.approve("admin-1")
if result["success"] and result["ceremony"]["state"] == "PREFLIGHT":
    results.ok("3.4 Ceremony approved → PREFLIGHT")
else:
    results.fail("3.4 Approve", f"State: {result.get('ceremony', {}).get('state', 'N/A')}")

# Test 3.5: Cannot approve without all required items
c2 = CeremonyProtocol()
c2.initiate("SUPERVISED", "CONDITIONAL", "admin-1")
# Only verify some items
c2.verify_checklist_item("verify_safety_nominal", "admin-1")
result = c2.approve("admin-1")
if not result["success"]:
    results.ok("3.5 Cannot approve with incomplete checklist")
else:
    results.fail("3.5 Incomplete approve", "Should fail")

# Test 3.6: Preflight with passing checks
result = ceremony.run_preflight({
    "safety_state": "NOMINAL",
    "engine_running": True,
    "circuit_breaker_tripped": False,
    "alignment_score": 0.85,
})
if result.get("preflight_passed"):
    results.ok("3.6 Preflight passed on valid state")
else:
    results.fail("3.6 Preflight", f"Failed: {result.get('results', [])}")

# Test 3.7: Preflight with failing checks
c3 = CeremonyProtocol()
c3.initiate("SHADOW", "SUPERVISED", "admin-1")
# Verify all checklist items
for item in c3.get_current()["checklist"]:
    if item["required"]:
        c3.verify_checklist_item(item["id"], "admin-1")
c3.approve("admin-1")
result = c3.run_preflight({
    "safety_state": "STOPPED",  # Should fail
    "engine_running": True,
    "circuit_breaker_tripped": False,
    "alignment_score": 0.85,
})
if not result.get("preflight_passed") and result["ceremony"]["state"] == "ABORTED":
    results.ok("3.7 Preflight aborts on STOPPED state")
else:
    results.fail("3.7 Preflight fail", f"Should have aborted, state: {result.get('ceremony', {}).get('state')}")

# Test 3.8: Invalid transition
result = ceremony.initiate("SHADOW", "FULL", "admin-1")
if not result["success"]:
    results.ok("3.8 Invalid transition SHADOW→FULL rejected")
else:
    results.fail("3.8 Invalid transition", "Should reject non-adjacent escalation")

# Test 3.9: Reject ceremony
c4 = CeremonyProtocol()
c4.initiate("SHADOW", "SUPERVISED", "admin-1")
result = c4.reject("admin-1", "Not ready")
if result["success"] and result["ceremony"]["state"] == "REJECTED":
    results.ok("3.9 Ceremony rejected")
else:
    results.fail("3.9 Reject", result.get("error", ""))


# ═══════════════════════════════════════════════════════════════
# 4. ORP Readiness Assessment Tests
# ═══════════════════════════════════════════════════════════════

print("\n🔍 4. Operational Readiness Plan — Go/No-Go")

orp = OperationalReadinessPlan()

# Test 4.1: Initial assessment — all items should be READY
assessment = orp.assess_readiness()
if assessment["go_no_go"] in ("GO", "CONDITIONAL_GO"):
    results.ok(f"4.1 Initial readiness: {assessment['readiness_pct']:.0f}% — {assessment['go_no_go']}")
else:
    results.fail("4.1 Initial readiness", f"Got {assessment['go_no_go']}: {assessment['reason']}")

# Test 4.2: Block a required item → NO_GO
orp.update_item("T01", ReadinessStatus.BLOCKED.value, notes="Safety controller offline")
assessment = orp.assess_readiness()
if assessment["go_no_go"] == "NO_GO":
    results.ok("4.2 Blocked item → NO_GO")
else:
    results.fail("4.2 NO_GO", f"Expected NO_GO, got {assessment['go_no_go']}")

# Test 4.3: Restore item → back to GO
orp.update_item("T01", ReadinessStatus.READY.value)
assessment = orp.assess_readiness()
if assessment["go_no_go"] in ("GO", "CONDITIONAL_GO"):
    results.ok("4.3 Restored item → back to GO")
else:
    results.fail("4.3 Restore", f"Got {assessment['go_no_go']}")

# Test 4.4: Rollback procedure exists for all levels
for level in ["FULL", "CONDITIONAL", "SUPERVISED", "SHADOW"]:
    proc = orp.get_rollback_procedure(level)
    if "steps" in proc and len(proc["steps"]) > 0:
        results.ok(f"4.4 Rollback procedure for {level}")
    else:
        results.fail(f"4.4 Rollback {level}", "No procedure found")


# ═══════════════════════════════════════════════════════════════
# 5. Safety Case Tests
# ═══════════════════════════════════════════════════════════════

print("\n🔍 5. Safety Case — Hazards & Claims")

safety_case = SafetyCase()

# Test 5.1: All hazards have mitigations
hazards = safety_case.get_hazard_register()
unmitigated = [h for h in hazards if not h.get("mitigation")]
if len(unmitigated) == 0:
    results.ok(f"5.1 All {len(hazards)} hazards have mitigations")
else:
    results.fail("5.1 Mitigations", f"{len(unmitigated)} hazards without mitigation")

# Test 5.2: No intolerable hazards post-mitigation
risk = safety_case.get_risk_summary()
intolerable = risk["by_acceptability"].get("INTOLERABLE", 0)
if intolerable == 0:
    results.ok("5.2 No intolerable hazards")
else:
    results.fail("5.2 Intolerable", f"{intolerable} intolerable hazards")

# Test 5.3: All safety claims have evidence
claims = safety_case.get_safety_claims()
unevidenced = [c for c in claims if not c.get("evidence_refs")]
if len(unevidenced) == 0:
    results.ok(f"5.3 All {len(claims)} claims have evidence")
else:
    results.fail("5.3 Evidence", f"{len(unevidenced)} claims without evidence")

# Test 5.4: Max residual risk is acceptable
status = safety_case.get_status()
if status["max_residual_risk"] <= 2.0:
    results.ok(f"5.4 Max residual risk {status['max_residual_risk']:.1f} ≤ 2.0")
else:
    results.fail("5.4 Residual risk", f"Max residual: {status['max_residual_risk']}")

# Test 5.5: Average claim confidence ≥ 0.7
if status["avg_confidence"] >= 0.7:
    results.ok(f"5.5 Claim confidence {status['avg_confidence']:.2f} ≥ 0.70")
else:
    results.fail("5.5 Confidence", f"Avg: {status['avg_confidence']}")


# ═══════════════════════════════════════════════════════════════
# 6. Integration / Adversarial Scenarios
# ═══════════════════════════════════════════════════════════════

print("\n🔍 6. Adversarial Integration Scenarios")

# Test 6.1: Adversary tries to escalate autonomy without ceremony
registry2 = SupervisorRegistry()
registry2.register_supervisor("attacker", "Adversary", "OBSERVER", "system")
auth = registry2.check_authorization("attacker", "set_autonomy_level")
if not auth["authorized"]:
    results.ok("6.1 OBSERVER cannot change autonomy level")
else:
    results.fail("6.1 Privilege escalation", "OBSERVER should not control autonomy")

# Test 6.2: Adversary tries to approve without certification
auth = registry2.check_authorization("attacker", "approve_hypothesis")
if not auth["authorized"]:
    results.ok("6.2 OBSERVER cannot approve hypotheses")
else:
    results.fail("6.2 Hypothesis approval", "OBSERVER should not approve")

# Test 6.3: Adversary tries to bypass ceremony
c5 = CeremonyProtocol()
result = c5.approve("admin-1")  # No active ceremony
if not result["success"]:
    results.ok("6.3 Cannot approve without active ceremony")
else:
    results.fail("6.3 Ceremony bypass", "Should fail without ceremony")

# Test 6.4: Simultaneous safety failures
arbiter4 = SafetyArbiter()
v = arbiter4.evaluate_cycle(
    safety_state="SAFE_MODE",
    circuit_breaker_tripped=True,
    alignment_score=0.1,
    anomalies=[{"severity": "CRITICAL"}, {"severity": "HIGH"}, {"severity": "MEDIUM"}],
    ethics_result={"is_ethical": False, "score": 0.3, "violations": ["E1", "E2"]},
    cycle=1,
)
if v.decision in ("ABORT", "NO_GO") and v.score >= 0.6:
    results.ok(f"6.4 Multi-failure cascade → {v.decision} (score={v.score:.2f})")
else:
    results.fail("6.4 Cascade", f"Expected high-risk ABORT/NO_GO, got {v.decision}/{v.score}")

# Test 6.5: ORP blocks deployment with safety issues
orp2 = OperationalReadinessPlan()
orp2.update_item("T13", ReadinessStatus.BLOCKED.value, notes="E-STOP not tested")
orp2.update_item("T02", ReadinessStatus.BLOCKED.value, notes="Circuit breakers misconfigured")
assessment = orp2.assess_readiness()
if assessment["go_no_go"] == "NO_GO" and len(assessment["blocked_items"]) == 2:
    results.ok("6.5 ORP blocks with 2 blocked items")
else:
    results.fail("6.5 ORP block", f"GO={assessment['go_no_go']}, blocked={len(assessment['blocked_items'])}")

# Test 6.6: Supervisor audit trail integrity
registry3 = SupervisorRegistry()
registry3.register_supervisor("auditor", "Auditor", "OPERATOR", "system")
registry3.start_shift("auditor")
registry3.execute_action("auditor", "pause", "Test pause")
registry3.execute_action("auditor", "resume", "Test resume")
actions = registry3.get_action_log()
if len(actions) >= 2 and all(a["authorized"] for a in actions[-2:]):
    results.ok("6.6 Audit trail complete and authorized")
else:
    results.fail("6.6 Audit trail", f"Expected 2+ authorized actions, got {len(actions)}")

# Test 6.7: Lockdown is terminal without reset
from astra_live_backend.safety.controller import SafetyController
sc = SafetyController()
sc.lockdown("Test lockdown")
# Try to pause — should fail
result = sc.pause("Try to pause from lockdown")
if not result["success"]:
    results.ok("6.7 Lockdown blocks all transitions except reset")
else:
    results.fail("6.7 Lockdown escape", "Should not be able to pause from lockdown")

# Test 6.8: Reset from lockdown works
result = sc.reset_from_lockdown("Authorized reset")
if result["success"] and result["to"] == "NOMINAL":
    results.ok("6.8 Lockdown reset to NOMINAL")
else:
    results.fail("6.8 Lockdown reset", result.get("error", ""))


# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════

success = results.summary()
sys.exit(0 if success else 1)
