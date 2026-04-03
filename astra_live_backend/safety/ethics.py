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
