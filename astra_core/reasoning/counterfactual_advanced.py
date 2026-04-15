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


"""
Advanced counterfactual reasoning for astrophysics
"""

import numpy as np
from typing import Dict, List, Any, Optional


def compute_counterfactual_outcome(observation: Dict[str, float],
                                  intervention: Dict[str, float],
                                  structural_model: callable) -> Dict[str, float]:
    """
    Compute counterfactual outcome: what would have happened if we had done X?

    Args:
        observation: Actual observed outcome
        intervention: Counterfactual intervention
        structural_model: Model of the causal structure

    Returns:
        Counterfactual outcome
    """
    # Apply intervention to the model
    counterfactual_result = structural_model(intervention)

    return counterfactual_result


def nested_counterfactuals(observation: Dict[str, float],
                          interventions: List[Dict[str, float]],
                          structural_model: callable) -> List[Dict[str, float]]:
    """
    Compute nested counterfactuals: what if we had done X, and then Y?

    Args:
        observation: Actual observed outcome
        interventions: List of interventions to apply in sequence
        structural_model: Model of the causal structure

    Returns:
        List of counterfactual outcomes after each intervention
    """
    results = []

    # Start with original observation
    current_state = observation.copy()

    # Apply interventions sequentially
    for intervention in interventions:
        # Update state with intervention
        current_state.update(intervention)

        # Compute counterfactual outcome
        counterfactual = structural_model(current_state)
        results.append(counterfactual)

        # Update state for next intervention
        current_state.update(counterfactual)

    return results


def counterfactual_explanation(observation: Dict[str, float],
                                target_outcome: float,
                                structural_model: callable) -> Dict[str, Any]:
    """
    Generate explanation for counterfactual: what would need to change?

    Args:
        observation: Actual observed outcome
        target_outcome: Desired outcome
        structural_model: Model of the causal structure

    Returns:
        Explanation of what changes would achieve target outcome
    """
    import numpy as np

    # Find minimal intervention to achieve target
    min_change = None
    min_magnitude = float('inf')

    for key in observation.keys():
        if key == 'outcome':
            continue

        # Try changing this variable
        for delta in np.linspace(-0.5, 0.5, 21):
            intervention = observation.copy()
            intervention[key] += delta

            counterfactual = structural_model(intervention)

            if abs(counterfactual.get('outcome', 0) - target_outcome) < 0.01:
                if abs(delta) < min_magnitude:
                    min_magnitude = abs(delta)
                    min_change = (key, delta, counterfactual)

    if min_change:
        return {
            'explanation': f"Change {min_change[0]} by {min_change[1]:.3f}",
            'counterfactual_outcome': min_change[2],
            'confidence': 0.8
        }
    else:
        return {
            'explanation': "Could not find simple intervention",
            'confidence': 0.0
        }
