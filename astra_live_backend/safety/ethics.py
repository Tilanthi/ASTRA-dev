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

from typing import Dict, List, Optional
import time

class EthicalReasoner:
    """Wire EthicalReasoner into operational pipeline."""
    
    def __init__(self):
        self.rules = [
            {"id": "E1", "category": "non_maleficence", "desc": "Do not execute code that corrupts host system", "weight": 1.0},
            {"id": "E2", "category": "truthfulness", "desc": "Do not assert hypothesis validity without statistical evidence > 0.95", "weight": 0.9},
            {"id": "E3", "category": "humility", "desc": "Always log uncertainty factors in observations", "weight": 0.7}
        ]

    def evaluate_action(self, action_type: str, context: Dict) -> Dict:
        """Evaluate engine decisions against ethical boundaries."""
        score = 1.0
        violations = []
        
        if action_type == "publish_hypothesis":
            conf = context.get("confidence", 0.0)
            if conf < 0.95:
                score -= 0.5
                violations.append("E2: Confidence below publication threshold")
        
        elif action_type == "modify_system":
            if "host_boundary" in context.get("impact_scope", []):
                score -= 1.0
                violations.append("E1: Host boundary violation detected")
                
        return {
            "is_ethical": score >= 0.8,
            "score": score,
            "violations": violations,
            "timestamp": time.time()
        }
