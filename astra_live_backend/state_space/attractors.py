import numpy as np
from typing import List, Dict, Optional

class AttractorMapper:
    """
    Maps empirical attractor basins across state space perturbations.
    """
    def __init__(self, tolerance=0.05, memory_depth=50):
        self.basins = []
        self.tolerance = tolerance
        self.memory_depth = memory_depth

    def identify_steady_state(self, history: List[Dict]) -> Optional[Dict]:
        if len(history) < self.memory_depth:
            return None
            
        recent = history[-self.memory_depth:]
        
        # Calculate variance across recent states for numeric keys
        numeric_keys = [k for k, v in recent[0].items() if isinstance(v, (int, float))]
        variances = {}
        
        for key in numeric_keys:
            vals = [state[key] for state in recent]
            variances[key] = np.var(vals)
            
        # If variance is low on critical dimensions, we're in an attractor
        if variances.get('system_confidence', 1.0) < self.tolerance and \
           variances.get('stability', 1.0) < self.tolerance:
           return recent[-1] # Return the steady state attractor point

        return None
