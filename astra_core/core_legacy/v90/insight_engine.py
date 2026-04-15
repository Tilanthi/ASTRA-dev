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
Insight Engine for V90
====================

Implements creative insight generation - the "aha!" moment
where understanding suddenly restructures.

Based on:
- Gestalt principles
- Remote association theory
- Incubation effects
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time
import random


@dataclass
class Insight:
    """Represents an insight or creative breakthrough"""
    content: str
    breakthrough_type: str
    confidence: float
    restructuring: List[str]
    domain: str
    timestamp: float
    precursor_patterns: List[str]


class InsightEngine:
    """
    Generates insights through creative restructuring.

    Key mechanisms:
    1. Remote association
    2. Pattern completion
    3. Contradiction resolution
    4. Perspective shifting
    """

    def __init__(self):
        self.insight_history = []
        self.association_patterns = self._initialize_associations()
        self.gestalt_principles = self._initialize_gestalt_principles()
        self.incubation_threshold = 0.7  # Confidence needed for insight

    def generate_insight(self, problem: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate an insight about a problem.

        Uses multiple insight mechanisms:
        - Remote association
        - Pattern recognition
        - Contradiction detection
        - Perspective shift
        """
        # Analyze problem structure
        structure = self._analyze_problem_structure(problem)

        # Try different insight mechanisms
        insights = []

        # 1. Remote association
        remote_insight = self._generate_remote_association(problem, structure)
        if remote_insight:
            insights.append(remote_insight)

        # 2. Gestalt completion
        gestalt_insight = self._complete_gestalt(problem, structure)
        if gestalt_insight:
            insights.append(gestalt_insight)

        # 3. Contradiction resolution
        contradiction_insight = self._resolve_contradiction(problem, context)
        if contradiction_insight:
            insights.append(contradiction_insight)

        # 4. Perspective shift
        perspective_insight = self._shift_perspective(problem, context)
        if perspective_insight:
            insights.append(perspective_insight)

        # Select best insight
        if insights:
            best_insight = max(insights, key=lambda i: i[1])  # Max by confidence
            self._record_insight(best_insight[0], problem, context)
            return best_insight[0]

        return None

    def _analyze_problem_structure(self, problem: str) -> Dict[str, Any]:
        """Analyze the structural properties of a problem"""
        words = problem.lower().split()
        return {
            'complexity': len(words),
            'question_words': [w for w in words if w in ['what', 'how', 'why', 'when', 'where']],
            'comparison_words': [w for w in words if w in ['like', 'versus', 'than', 'compared']],
            'causal_words': [w for w in words if w in ['because', 'cause', 'effect', 'leads']],
            'action_words': [w for w in words if w in ['do', 'make', 'create', 'solve']],
            'object_words': [w for w in words if w in ['ball', 'box', 'number', 'system']]
        }

    def _generate_remote_association(self, problem: str, structure: Dict) -> Optional[Tuple[str, float]]:
        """
        Generate insight through remote association.

        Connect seemingly unrelated concepts to find novel solutions.
        """
        # Extract key concepts
        concepts = structure['object_words']
        if not concepts:
            return None

        # Remote associations database
        remote_associations = {
            'ball': ['sphere', 'orbit', 'planet', 'electron', 'wave', 'probability'],
            'box': ['container', 'set', 'category', 'framework', 'system', 'space'],
            'number': ['quantity', 'amount', 'scale', 'dimension', 'measurement', 'infinity'],
            'system': ['network', 'pattern', 'organization', 'ecosystem', 'collective', 'emergence']
        }

        # Find remote associations
        all_associations = []
        for concept in concepts:
            if concept in remote_associations:
                all_associations.extend(remote_associations[concept])

        # Select unexpected association
        if all_associations:
            selected = random.choice(all_associations)

            # Generate insight
            insight = f"Think about this as a '{selected}' instead"
            confidence = 0.3 + 0.1 * len(all_associations)  # More connections = more confidence

            return (insight, confidence)

        return None

    def _complete_gestalt(self, problem: str, structure: Dict) -> Optional[Tuple[str, float]]:
        """
        Complete incomplete patterns using Gestalt principles.

        Gestalt principles:
        - Closure: Fill in missing pieces
        - Similarity: Group similar elements
        - Continuity: Follow natural flow
        - Figure-ground: Distinguish important from background
        """
        if structure['complexity'] < 3:
            return None

        # Look for incomplete patterns
        if 'how' in problem and not 'why' in problem:
            insight = "Ask why first to understand the underlying mechanism"
            return (insight, 0.6)

        if 'compare' in problem and 'transform' not in problem:
            insight = "Instead of just comparing, ask how one could become the other"
            return (insight, 0.7)

        if structure['action_words'] and not structure['causal_words']:
            insight = "Before asking what to do, understand why something is the way it is"
            return (insight, 0.5)

        return None

    def _resolve_contradiction(self, problem: str, context: Dict) -> Optional[Tuple[str, float]]:
        """
        Detect and resolve contradictions.
        """
        contradictions = []

        # Check for obvious contradictions
        if 'always' in problem.lower() and 'never' in problem.lower():
            contradictions.append("absolute_claims")
        if 'impossible' in problem.lower() and 'possible' in problem.lower():
            contradictions.append("possibility_conflict")

        if not contradictions:
            return None

        # Generate resolution insight
        insights = {
            "absolute_claims": "Nothing is absolute in reality. Look for exceptions and edge cases.",
            "possibility_conflict": "Possibility depends on conditions. What constraints change the outcome?",
            "certainty_doubt": "Certainty is rare. What would make it uncertain?"
        }

        for contradiction in contradictions:
            if contradiction in insights:
                return (insights[contradiction], 0.8)

        return None

    def _shift_perspective(self, problem: str, context: Dict) -> Optional[Tuple[str, float]]:
        """
        Shift perspective to gain new insights.
        """
        perspective_shifts = [
            ("What would this look like from a microscopic view?", 0.6),
            ("What happens over geologic time scales?", 0.5),
            ("How would an alien intelligence see this?", 0.4),
            ("What if the opposite were true?", 0.7),
            ("What are the unstated assumptions?", 0.8)
        ]

        # Select most appropriate shift based on problem
        if 'small' in problem.lower():
            shift = perspective_shifts[1]  # Large scale
        elif 'large' in problem.lower() or 'system' in problem.lower():
            shift = perspective_shifts[0]  # Microscopic
        else:
            shift = random.choice(perspective_shifts)

        return shift

    def _record_insight(self, insight: str, problem: str, context: Dict):
        """Record an insight for future learning"""
        insight_record = Insight(
            content=insight,
            breakthrough_type=self._classify_breakthrough_type(insight),
            confidence=0.7,
            restructuring=[],
            domain='general',
            timestamp=time.time(),
            precursor_patterns=[]
        )

        self.insight_history.append(insight_record)

        # Keep history bounded
        if len(self.insight_history) > 1000:
            self.insight_history = self.insight_history[-500:]

    def _classify_breakthrough_type(self, insight: str) -> str:
        """Classify the type of breakthrough"""
        if 'instead' in insight.lower():
            return 'paradigm_shift'
        elif 'ask why' in insight.lower():
            return 'causal_insight'
        elif 'assumptions' in insight.lower():
            return 'critical_thinking'
        elif 'perspective' in insight.lower():
            return 'viewpoint_change'
        else:
            return 'restructuring'

    def _initialize_associations(self) -> Dict[str, List[str]]:
        """Initialize remote association database"""
        return {
            'abstract': ['concrete', 'embodied', 'physical', 'real_world'],
            'static': ['dynamic', 'process', 'change', 'evolution'],
            'linear': ['nonlinear', 'emergent', 'complex', 'chaotic'],
            'individual': ['collective', 'network', 'system', 'organism'],
            'simple': ['complex', 'emergent', 'unpredictable'],
            'certainty': ['probability', 'uncertainty', 'risk', 'chance']
        }

    def _initialize_gestalt_principles(self) -> List[str]:
        """Initialize Gestalt principles"""
        return [
            'closure',
            'similarity',
            'continuity',
            'figure_ground',
            'proximity',
            'common_fate'
        ]

    def simulate_incubation(self, problem: str, duration: float = 1.0) -> Optional[str]:
        """
        Simulate incubation period for creative insight.

        The mind works on the problem unconsciously.
        """
        # Simulate time passing
        time.sleep(min(duration, 0.1))  # Max 100ms for simulation

        # Insight is more likely after incubation
        incubation_bonus = min(0.3, duration * 0.1)

        # Random chance of insight
        if random.random() < (0.1 + incubation_bonus):
            # Generate incubation insight
            insights = [
                "The solution involves working backwards",
                "Consider the simplest case first",
                "Look for the hidden constraint",
                "What pattern emerges at the limit?",
                "The answer may be in the question itself"
            ]

            return random.choice(insights)

        return None

    def get_insight_statistics(self) -> Dict[str, Any]:
        """Get statistics about insights generated"""
        if not self.insight_history:
            return {'total_insights': 0}

        types = [i.breakthrough_type for i in self.insight_history]
        type_counts = {t: types.count(t) for t in set(types)}

        return {
            'total_insights': len(self.insight_history),
            'breakthrough_types': type_counts,
            'most_recent': self.insight_history[-1].content if self.insight_history else None,
            'average_confidence': np.mean([i.confidence for i in self.insight_history])
        }