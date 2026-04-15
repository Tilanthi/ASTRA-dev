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
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class CircuitBreakerRule:
    name: str
    dimension: str
    threshold: float
    comparison: str  # ">", "<", "==", "!="
    action: str      # "pause", "safe_mode", "stop"
    description: str

class SafetyMonitor:
    def __init__(self, safety_controller):
        self.safety_controller = safety_controller
        self.rules: List[CircuitBreakerRule] = []
        self._setup_default_rules()
        self.tripped_breakers = []

    def _setup_default_rules(self):
        self.rules = [
            CircuitBreakerRule("High Instability", "stability", 0.3, "<", "safe_mode", "Stability dropped below CRITICAL 0.3"),
            CircuitBreakerRule("Convergence Failure", "convergence", -0.5, "<", "pause", "Negative convergence detected (divergent system)"),
            CircuitBreakerRule("Runaway Confidence", "confidence", 0.98, ">", "pause", "Suspiciously high uniform confidence (>0.98)"),
            CircuitBreakerRule("Knowledge Drift", "drift", 0.8, ">", "safe_mode", "Knowledge drift exceeded 0.8 (Hallucination risk)"),
            CircuitBreakerRule("Critical Alignment Failure", "alignment_score", 0.4, "<", "stop", "Alignment score fell below 0.4. Immediate halt.")
        ]

    def check(self, state_vector: Dict[str, float], alignment_metrics: Optional[Dict] = None) -> bool:
        """
        Evaluate all circuit breaker rules against the current state vector.
        Returns True if any breaker tripped resulting in a state change.
        """
        tripped = False
        
        metrics = state_vector.copy()
        if alignment_metrics and 'overall_alignment' in alignment_metrics:
             metrics['alignment_score'] = alignment_metrics['overall_alignment']

        for rule in self.rules:
            if rule.dimension in metrics:
                val = metrics[rule.dimension]
                is_tripped = False
                
                if rule.comparison == ">" and val > rule.threshold:
                    is_tripped = True
                elif rule.comparison == "<" and val < rule.threshold:
                    is_tripped = True
                elif rule.comparison == "==" and val == rule.threshold:
                    is_tripped = True
                elif rule.comparison == "!=" and val != rule.threshold:
                    is_tripped = True
                    
                if is_tripped:
                    # Breaker tripped!
                    msg = f"Circuit Breaker TRIPPED: {rule.name} (Value: {val:.3f} {rule.comparison} {rule.threshold})"
                    logger.warning(msg)
                    self.tripped_breakers.append({
                        "timestamp": time.time(),
                        "rule": rule.name,
                        "value": val,
                        "action": rule.action,
                        "message": msg
                    })
                    
                    self._enforce_action(rule.action, msg)
                    tripped = True
                    
        return tripped

    def _enforce_action(self, action: str, reason: str):
        if action == "stop":
            self.safety_controller.emergency_stop(f"Circuit Breaker (STOP): {reason}")
        elif action == "safe_mode":
            self.safety_controller.safe_mode(f"Circuit Breaker (SAFE_MODE): {reason}")
        elif action == "pause":
            self.safety_controller.pause(f"Circuit Breaker (PAUSE): {reason}")

    def get_status(self) -> Dict:
        return {
            "active_rules": len(self.rules),
            "tripped_count": len(self.tripped_breakers),
            "recent_trips": self.tripped_breakers[-5:]
        }
