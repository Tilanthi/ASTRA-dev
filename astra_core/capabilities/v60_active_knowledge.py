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
Active Knowledge Acquisition Module for STAN (Capabilities Package)
=================================================================

This module re-exports the Active Knowledge Acquisition classes from the
reasoning package for backward compatibility and API consistency.

Provides active knowledge acquisition including gap detection,
hypothesis generation, experiment design, knowledge integration,
and curiosity-driven learning.

Date: 2025-12-17
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional

# Re-export from reasoning package
from astra_core.reasoning.v60_active_knowledge import (
    KnowledgeGapType,
    HypothesisStatus,
    ExperimentType,
    CuriositySource,
    KnowledgeGap,
    Hypothesis,
    Experiment,
    KnowledgeIntegration,
    GapDetector,
    HypothesisGenerator,
)

# Additional classes not in reasoning module - implementing them here

class ExperimentDesigner:
    """
    Designs experiments to test hypotheses.

    Date: 2025-12-17
    """

    def __init__(self):
        self.experiment_templates = {
            'causal': [
                {
                    'type': 'controlled_experiment',
                    'template': 'Manipulate {manipulation} to observe {effect}',
                    'variables': {'manipulation': 'X', 'effect': 'Y'}
                },
            ],
            'observational': [
                {
                    'type': 'observation',
                    'template': 'Observe {target} under conditions {conditions}',
                    'variables': {'target': 'X', 'conditions': 'various'}
                },
            ]
        }

    def design_experiment(self, hypothesis: Hypothesis, constraints: Dict = None) -> Experiment:
        """Design an experiment to test a hypothesis."""
        template_type = 'causal' if 'causes' in hypothesis.description.lower() else 'observational'
        templates = self.experiment_templates.get(template_type, self.experiment_templates['observational'])
        template = templates[0] if templates else self.experiment_templates['observational'][0]

        return Experiment(
            description=template['template'].format(**template['variables']),
            experiment_type=ExperimentType.CONTROLLED if template_type == 'causal' else ExperimentType.OBSERVATIONAL,
            hypothesis_id=hypothesis.gap_id,
            status='designed'
        )


class KnowledgeIntegrator:
    """
    Integrates new knowledge into the knowledge base.

    Date: 2025-12-17
    """

    def __init__(self):
        self.integrations: List[KnowledgeIntegration] = []
        self.knowledge_base: Dict[str, Any] = {
            'concepts': {},
            'relations': {},
            'facts': {}
        }

    def integrate(self, integration: KnowledgeIntegration) -> bool:
        """Integrate new knowledge."""
        self.integrations.append(integration)

        # Add to knowledge base
        if integration.concept and integration.concept not in self.knowledge_base['concepts']:
            self.knowledge_base['concepts'][integration.concept] = {
                'properties': [],
                'relations': []
            }

        return True

    def get_knowledge_base(self) -> Dict[str, Any]:
        """Get the current knowledge base."""
        return self.knowledge_base


class CuriosityEngine:
    """
    Drives curiosity-based knowledge acquisition.

    Date: 2025-12-17
    """

    def __init__(self):
        self.curiosity_sources = [
            CuriositySource.INFO_GAP,
            CuriositySource.CONTRADICTION,
            CuriositySource.NOVELTY
        ]

    def evaluate_curiosity(self, gap: KnowledgeGap) -> float:
        """Evaluate curiosity score for a knowledge gap."""
        # Base curiosity from gap urgency
        score = gap.urgency * 0.5

        # Boost for novel concepts
        if gap.concept not in ['X', 'unknown', 'general']:
            score += 0.3

        return min(1.0, score)

    def select_gap(self, gaps: List[KnowledgeGap]) -> Optional[KnowledgeGap]:
        """Select the most curiosity-inducing gap."""
        if not gaps:
            return None

        scored = [(g, self.evaluate_curiosity(g)) for g in gaps]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]


class ActiveKnowledgeSystem:
    """
    Unified active knowledge acquisition system.

    Integrates gap detection, hypothesis generation, experiment design,
    knowledge integration, and curiosity-driven learning.

    Date: 2025-12-17
    """

    def __init__(self):
        self.gap_detector = GapDetector()
        self.hypothesis_generator = HypothesisGenerator()
        self.experiment_designer = ExperimentDesigner()
        self.knowledge_integrator = KnowledgeIntegrator()
        self.curiosity_engine = CuriosityEngine()

    def detect_gaps(self, domain: str, knowledge_base: Dict = None) -> List[KnowledgeGap]:
        """Detect knowledge gaps."""
        return self.gap_detector.detect_gaps(domain, knowledge_base)

    def generate_hypotheses(self, gap: KnowledgeGap) -> List[Hypothesis]:
        """Generate hypotheses for a gap."""
        return self.hypothesis_generator.generate_hypotheses(gap)

    def design_experiments(self, hypothesis: Hypothesis) -> Experiment:
        """Design experiments for a hypothesis."""
        return self.experiment_designer.design_experiment(hypothesis)

    def integrate_knowledge(self, integration: KnowledgeIntegration) -> bool:
        """Integrate new knowledge."""
        return self.knowledge_integrator.integrate(integration)


# Factory functions
def create_active_knowledge_system() -> ActiveKnowledgeSystem:
    """Create an active knowledge system."""
    return ActiveKnowledgeSystem()

def create_gap_detector() -> GapDetector:
    """Create a gap detector."""
    return GapDetector()

def create_hypothesis_generator() -> HypothesisGenerator:
    """Create a hypothesis generator."""
    return HypothesisGenerator()

def create_curiosity_engine() -> CuriosityEngine:
    """Create a curiosity engine."""
    return CuriosityEngine()

# Aliases for V60 naming
V60KnowledgeGap = KnowledgeGap
V60Hypothesis = Hypothesis
V60Experiment = Experiment
V60KnowledgeGapType = KnowledgeGapType
V60HypothesisGenerator = HypothesisGenerator
V60ExperimentDesigner = ExperimentDesigner

__all__ = [
    'ActiveKnowledgeSystem',
    'GapDetector',
    'HypothesisGenerator',
    'V60HypothesisGenerator',
    'ExperimentDesigner',
    'V60ExperimentDesigner',
    'KnowledgeIntegrator',
    'CuriosityEngine',
    'KnowledgeGap',
    'V60KnowledgeGap',
    'Hypothesis',
    'V60Hypothesis',
    'Experiment',
    'V60Experiment',
    'KnowledgeIntegration',
    'KnowledgeGapType',
    'V60KnowledgeGapType',
    'HypothesisStatus',
    'ExperimentType',
    'V60ExperimentType',
    'CuriositySource',
    'create_active_knowledge_system',
    'create_gap_detector',
    'create_hypothesis_generator',
    'create_curiosity_engine',
]
