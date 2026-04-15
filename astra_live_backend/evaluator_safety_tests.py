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
