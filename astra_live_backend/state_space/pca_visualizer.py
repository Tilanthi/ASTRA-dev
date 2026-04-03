import numpy as np
import json
from sklearn.decomposition import PCA
from typing import List, Dict

class StateSpaceVisualizer:
    def __init__(self, target_dimensions=3):
        self.target_dimensions = target_dimensions
        self.pca = PCA(n_components=target_dimensions)
        self.is_fitted = False
        self.history_buffer = []

    def fit_transform(self, state_history: List[Dict]):
        if len(state_history) < self.target_dimensions:
            return None # Not enough history
            
        # extract numeric dimensions from the dict 
        # usually 14 dimensional
        vectors = []
        for state in state_history:
            vec = []
            for k, v in sorted(state.items()):
                if isinstance(v, (int, float)):
                    vec.append(v)
            vectors.append(vec)
            
        X = np.array(vectors)
        
        # Fit or transform
        transformed = self.pca.fit_transform(X)
        self.is_fitted = True
        
        # Format for D3
        result = []
        for i, proj in enumerate(transformed):
            result.append({
                "cycle": i,
                "x": float(proj[0]),
                "y": float(proj[1]),
                "z": float(proj[2]) if self.target_dimensions > 2 else 0.0,
                "original": state_history[i]
            })
            
        return result
