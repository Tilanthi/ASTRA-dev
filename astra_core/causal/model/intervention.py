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
Intervention Planning using Do-Calculus

Implements the do-calculus for planning optimal interventions
in causal systems.
"""

from typing import Dict, Set, Optional, List, Tuple
import numpy as np
from dataclasses import dataclass

from .scm import StructuralCausalModel, Intervention


@dataclass
class InterventionPlan:
    """A plan for intervening in a causal system."""
    intervention: Intervention
    predicted_outcome: float
    confidence: float
    alternatives: List[Dict]
    reasoning: str


class InterventionPlanner:
    """
    Plan optimal interventions to achieve desired outcomes.

    Uses do-calculus to predict effects of interventions and
    selects interventions that maximize objective functions.

    Example:
        >>> planner = InterventionPlanner(scm)
        >>> plan = planner.plan_intervention("Y", target_value=1.0)
        >>> print(plan.intervention)
        >>> print(plan.predicted_outcome)
    """

    def __init__(self,
                 scm: StructuralCausalModel,
                 constraints: Optional[Dict] = None):
        """
        Initialize intervention planner.

        Args:
            scm: Causal model of the system
            constraints: Optional constraints on interventions
        """
        self.scm = scm
        self.constraints = constraints or {}

    def plan_intervention(self,
                          target: str,
                          target_value: Optional[float] = None,
                          objective: str = "maximize") -> InterventionPlan:
        """
        Plan optimal intervention to affect target variable.

        Args:
            target: Variable to affect
            target_value: Desired value (if None, maximize/minimize)
            objective: "maximize", "minimize", or "achieve"

        Returns:
            Intervention plan with predictions
        """
        # Find manipulable variables
        manipulable = self._get_manipulable_variables()

        if target in manipulable:
            manipulable.remove(target)

        if not manipulable:
            return InterventionPlan(
                intervention=Intervention({}),
                predicted_outcome=0,
                confidence=0,
                alternatives=[],
                reasoning="No manipulable variables found"
            )

        # Evaluate effects of intervening on each variable
        interventions = []

        for var in manipulable:
            for value in self._get_possible_values(var):
                intervention = Intervention({var: value})

                # Compute causal effect
                effect = self._compute_causal_effect(intervention, target)

                interventions.append({
                    'intervention': intervention,
                    'effect': effect,
                    'variable': var,
                    'value': value
                })

        # Select best intervention based on objective
        if objective == "maximize":
            best = max(interventions, key=lambda x: x['effect'])
        elif objective == "minimize":
            best = min(interventions, key=lambda x: x['effect'])
        else:  # achieve target value
            best = min(interventions,
                      key=lambda x: abs(x['effect'] - target_value))

        return InterventionPlan(
            intervention=best['intervention'],
            predicted_outcome=best['effect'],
            confidence=self._compute_confidence(best),
            alternatives=interventions,
            reasoning=f"Intervening on {best['variable']} = {best['value']} "
                      f"predicted to achieve {target} = {best['effect']:.2f}"
        )

    def _get_manipulable_variables(self) -> Set[str]:
        """Get variables that can be manipulated."""
        return set(self.scm.endogenous.keys()) - self.constraints.get('fixed', set())

    def _get_possible_values(self, var: str) -> List[float]:
        """Get possible values to set variable to."""
        # Simplified - in practice would use domain knowledge
        return [-1.0, 0.0, 1.0]

    def _compute_causal_effect(self,
                               intervention: Intervention,
                               target: str) -> float:
        """Compute causal effect of intervention on target."""
        mutilated = self.scm.do_intervention(intervention)

        # Simplified effect computation
        # In practice, would run the SCM to compute target value
        base_value = 0.0

        # Get effect size from causal graph
        for intervened_var in intervention.assignments:
            if self.scm.graph.has_edge(intervened_var, target):
                # Direct effect
                conf = self.scm.confidences.get((intervened_var, target), 0.5)
