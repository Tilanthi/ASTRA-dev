import pytest
from astra_live_backend.safety import SafetyController, SafetyState, SafetyAction, PhasedAutonomyFramework, AutonomyLevel, EthicalReasoner

def test_phased_autonomy():
    """Verify phase transitions & ability locking logic"""
    pa = PhasedAutonomyFramework()
    assert pa.level == AutonomyLevel.SUPERVISED
    assert pa.can_investigate() == True
    assert pa.can_modify_state() == False
    assert pa.requires_approval_publish() == True
    
    # Check conditional
    pa.set_level(AutonomyLevel.CONDITIONAL, "ADMIN", "Testing Conditional")
    assert pa.can_modify_state() == True
    
def test_ethical_reasoner():
    """Verify ethical rules execute per boundary checks."""
    reasoner = EthicalReasoner()
    
    # Try publishing low conf
    eval_publish = reasoner.evaluate_action("publish_hypothesis", {"confidence": 0.8})
    assert eval_publish["is_ethical"] == False
    assert len(eval_publish["violations"]) > 0
    
    # Try publishing high conf
    eval_publish2 = reasoner.evaluate_action("publish_hypothesis", {"confidence": 0.98})
    assert eval_publish2["is_ethical"] == True
    assert len(eval_publish2["violations"]) == 0
