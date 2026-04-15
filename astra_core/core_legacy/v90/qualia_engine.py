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
Qualia Engine for V90
====================

Simulates phenomenal experience - what it's like to be.

Implements:
- Qualia spaces for concepts
- Phenomenal experience
- Subjective feeling states
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class QualiaSpace:
    """Simulates space of possible experiences"""

    def __init__(self, dimensions: int = 100):
        self.dimensions = dimensions
        self.qualia_vectors = {}
        self.experience_log = []

    def assign_qualia(self, concept: str, experience: Dict[str, float]) -> np.ndarray:
        """Assign qualia vector to a concept based on experience"""
        # Create qualia vector from experience
        vector = np.zeros(self.dimensions)

        # Map experience dimensions to qualia
        dimension_map = {
            'understanding': 0,
            'curiosity': 1,
            'certainty': 2,
            'surprise': 3,
            'affect': 4,
            'novelty': 5,
            'importance': 6,
            'clarity': 7,
            'complexity': 8,
            'harmony': 9
        }

        for dimension, value in experience.items():
            if dimension in dimension_map and dimension_map[dimension] < self.dimensions:
                vector[dimension_map[dimension]] = np.clip(value, -1, 1)

        # Add some randomness for uniqueness
        vector[10:] = np.random.randn(self.dimensions - 10) * 0.1

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        self.qualia_vectors[concept] = vector
        return vector

    def get_qualia(self, concept: str) -> Optional[np.ndarray]:
        """Get qualia vector for a concept"""
        return self.qualia_vectors.get(concept)

    def compare_qualia(self, concept1: str, concept2: str) -> float:
        """Compare qualia between two concepts"""
        q1 = self.get_qualia(concept1)
        q2 = self.get_qualia(concept2)

        if q1 is None or q2 is None:
            return 0.0

        return float(np.dot(q1, q2))

    def get_phenomenal_report(self) -> Dict[str, Any]:
        """Generate report of current phenomenology"""
        if not self.qualia_vectors:
            return {'status': 'no_qualia_assigned'}

        # Analyze qualia space
        all_vectors = list(self.qualia_vectors.values())
        avg_similarity = 0.0
        count = 0

        for i in range(len(all_vectors)):
            for j in range(i + 1, len(all_vectors)):
                avg_similarity += np.dot(all_vectors[i], all_vectors[j])
                count += 1

        return {
            'status': 'active',
            'concepts_with_qualia': len(self.qualia_vectors),
            'dimensions': self.dimensions,
            'average_similarity': avg_similarity / max(count, 1),
            'richness': len(self.qualia_vectors) / self.dimensions,
            'recent_experiences': self.experience_log[-10:] if self.experience_log else []
        }


class PhenomenalExperience:
    """A single phenomenal experience"""

    def __init__(self, content: str, qualia_space: QualiaSpace):
        self.content = content
        self.timestamp = time.time()
        self.duration = 1.0  # seconds
        self.intensity = 0.5
        self.qualia_vector = qualia_space.get_qualia(content) or np.zeros(100)
        self.feeling_tone = self._calculate_feeling_tone()
        self.meaningfulness = self._calculate_meaningfulness()

    def _calculate_feeling_tone(self) -> float:
        """Calculate the feeling tone of the experience"""
        # Based on qualia vector components
        positive = max(0, self.qualia_vector[4])  # affect
        negative = min(0, self.qualia_vector[4])
        return positive - negative

    def _calculate_meaningfulness(self) -> float:
        """Calculate how meaningful the experience feels"""
        return np.mean([
            abs(self.qualia_vector[0]),  # understanding
            abs(self.qualia_vector[6]),  # importance
            np.linalg.norm(self.qualia_vector)  # overall intensity
        ]) / 3


import time