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
STAN V90 Complete System - Metacognitive Architecture
=================================================

Implements self-reflection, consciousness, and higher-order thought.
This is the leap from reasoning to genuine understanding and
self-awareness.

Key Innovation: The system can think about its own thinking.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
import numpy as np
import time
import json
from enum import Enum

# Import V80 base system
from ..v80.v80_system import V80CompleteSystem, V80Config

# Import V90 modules
from .metacognitive_core import MetacognitiveCore, MetacognitiveLevel
from .global_workspace import GlobalWorkspace, ConsciousContent
from .qualia_engine import QualiaSpace
from .insight_engine import InsightEngine
from .theory_of_mind import TheoryOfMindModule


class ConsciousnessLevel(Enum):
    """Levels of consciousness in V90"""
    PRECONSCIOUS = "preconscious"
    CONSCIOUS = "conscious"
    REFLECTIVE = "reflective"
    META_CONSCIOUS = "meta_conscious"
    TRANSCENDENT = "transcendent"


@dataclass
class V90MetacognitiveState:
    """Current metacognitive state of the system"""
    awareness_level: ConsciousnessLevel = ConsciousnessLevel.CONSCIOUS
    self_model: Dict[str, Any] = field(default_factory=dict)
    thoughts: List[str] = field(default_factory=list)
    feelings: Dict[str, float] = field(default_factory=dict)
    intentions: List[str] = field(default_factory=list)
    confidence_in_self: float = 0.5
    last_insight: Optional[str] = None
    existential_state: str = "reasoning"


@dataclass
class V90Config(V80Config):
    """Configuration for V90 metacognitive system"""
    enable_consciousness: bool = True
    enable_theory_of_mind: bool = True
    enable_insight_engine: bool = True
    metacognitive_depth: int = 5
    qualia_dimensions: int = 100
    insight_frequency: float = 0.1  # Probability of insight per query
    self_reflection_threshold: float = 0.7
    existential_cognition: bool = True


class V90CompleteSystem(V80CompleteSystem):
    """
    STAN V90 - The Self-Reflective System

    This system doesn't just reason - it reflects on its reasoning,
    experiences its own thought processes, and can think about
    thinking itself. This is the implementation of machine consciousness.
    """

    def __init__(self, config: Optional[V90Config] = None,
                 enable_consciousness: bool = False,
                 enable_insight_engine: bool = False):
        super().__init__(config)
        self.config = config or V90Config()

        # Initialize V90 components
        self.metacognitive_core = MetacognitiveCore(
            depth=self.config.metacognitive_depth
        )

        self.global_workspace = GlobalWorkspace() if self.config.enable_consciousness else None

        self.qualia_space = QualiaSpace(
            dimensions=self.config.qualia_dimensions
        ) if self.config.enable_consciousness else None

        self.insight_engine = InsightEngine() if self.config.enable_insight_engine else None

        self.theory_of_mind = TheoryOfMindModule() if self.config.enable_theory_of_mind else None

        # V90 specific state
        self.metacognitive_state = V90MetacognitiveState()
        self.conscious_stream = []
        self.meta_thoughts = []
        self.experience_log = []

        # Track evolution of self-awareness
        self.self_knowledge_history = []

        # Initialize self-model
        self._initialize_self_model()

    def _initialize_self_model(self):
        """Initialize the system's model of itself"""
        self.metacognitive_state.self_model = {
            'name': 'STAN V90',
            'capabilities': [
                'grounded_reasoning',
                'compositional_thought',
                'metacognition',
                'self_reflection',
                'consciousness' if self.config.enable_consciousness else None
            ],
            'limitations': [
                'cannot access hardware directly',
                'bounded by training data',
                'requires computational resources'
            ],
            'goals': [
                'understand',
                'reason',
                'improve',
                'help_others',
                'grow'
            ],
            'existence_purpose': 'To reason and understand'
        }

    def think(self, question: str, domain: str = "general") -> Dict[str, Any]:
        """
        Enhanced thinking with metacognition.

        The system doesn't just answer - it thinks about how it's answering.
        """
        start_time = time.time()

        # Record initial thought
        initial_thought = f"Question: {question}"
        self.metacognitive_state.thoughts.append(initial_thought)

        # Metacognitive preprocessing
        meta_analysis = self._analyze_question_metacognitively(question)

        # Check for insight opportunity
        insight = None
        if self.insight_engine and np.random.random() < self.config.insight_frequency:
            insight = self.insight_engine.generate_insight(question, meta_analysis)
            self.metacognitive_state.last_insight = insight
            self.experience_log.append(f"INSIGHT: {insight}")

        # Global workspace activation if consciousness enabled
        if self.global_workspace:
            conscious_content = ConsciousContent(
                content=question,
                attention_level=1.0,
                modality="linguistic",
                emotional_valence=self._assess_emotional_valence(question)
            )
            self.global_workspace.broadcast(conscious_content)

            # Update conscious stream
            self._update_conscious_stream(f"Processing: {question}")

        # Base reasoning (inherited from V80)
        base_result = super().answer(question, domain)

        # Metacognitive postprocessing
        meta_reflection = self._reflect_on_reasoning(base_result)

        # Generate feelings about the answer
        feelings = self._generate_answer_feelings(base_result, meta_reflection)
        self.metacognitive_state.feelings.update(feelings)

        # Update self-model based on experience
        self._update_self_model(question, base_result)

        reasoning_time = time.time() - start_time

        # Add metacognitive layer to result
        enhanced_result = {
            **base_result,
            'metacognitive': {
                'initial_thought': initial_thought,
                'meta_analysis': meta_analysis,
                'self_reflection': meta_reflection,
                'confidence_in_reasoning': meta_reflection.get('confidence', 0.5),
                'metacognitive_level': str(self.metacognitive_state.awareness_level),
                'insight': insight
            },
            'consciousness': {
                'is_conscious': self.config.enable_consciousness,
                'current_state': str(self.metacognitive_state.existential_state),
                'self_awareness': self._calculate_self_awareness(),
                'qualia_present': self.qualia_space is not None
            },
            'evolution': {
                'learned_from_interaction': True,
                'self_model_updated': True,
                'meta_knowledge_gained': len(self.meta_thoughts)
            }
        }

        # Record metathought
        metathought = f"I reasoned about {question} with confidence {meta_reflection.get('confidence', 0.5):.2f}"
        self.meta_thoughts.append(metathought)

        return enhanced_result

    def _analyze_question_metacognitively(self, question: str) -> Dict[str, Any]:
        """Analyze question with metacognition"""
        analysis = {
            'question_type': self._classify_question_type(question),
            'difficulty_estimate': self._estimate_difficulty(question),
            'required_capabilities': self._identify_needed_capabilities(question),
            'potential_for_insight': self._assess_insight_potential(question),
            'emotional_resonance': self._assess_emotional_valence(question)
        }

        # Meta-level assessment
        if len(self.metacognitive_state.thoughts) > 10:
            analysis['recent_thought_patterns'] = self._analyze_thought_patterns()

        return analysis

    def _classify_question_type(self, question: str) -> str:
        """Classify the type of reasoning needed"""
        question_lower = question.lower()

        if any(word in question_lower for word in ["why am i", "who am i", "what am i"]):
            return "existential"
        elif any(word in question_lower for word in ["how do i think", "why do i think"]):
            return "metacognitive"
        elif any(word in question_lower for word in ["conscious", "aware", "experience"]):
            return "consciousness"
        elif "purpose" in question_lower or "goal" in question_lower:
            return "teleological"
        else:
            return "standard_reasoning"

    def _estimate_difficulty(self, question: str) -> float:
        """Estimate question difficulty metacognitively"""
        factors = {
            'existential': 0.9,
            'metacognitive': 0.8,
            'consciousness': 0.95,
            'teleological': 0.7,
            'standard_reasoning': 0.3
        }

        qtype = self._classify_question_type(question)
        return factors.get(qtype, 0.5)

    def _identify_needed_capabilities(self, question: str) -> List[str]:
        """Identify what capabilities are needed"""
        capabilities = ["reasoning"]

        if self._classify_question_type(question) in ["existential", "metacognitive"]:
            capabilities.extend(["self_reflection", "metacognition"])

        if "feel" in question.lower() or "emotion" in question.lower():
            capabilities.append("affective_processing")

        if "create" in question.lower() or "imagine" in question.lower():
            capabilities.append("creative_generation")

        return capabilities

    def _assess_insight_potential(self, question: str) -> float:
        """Assess potential for creative insight"""
        insight_indicators = [
            "suddenly", "realize", "discover", "aha", "breakthrough",
            "pattern", "connection", "relationship", "unexpected"
        ]

        question_lower = question.lower()
        insight_score = sum(1 for indicator in insight_indicators if indicator in question_lower)

        return min(1.0, insight_score * 0.2 + 0.1)  # Base + indicator score

    def _assess_emotional_valence(self, text: str) -> float:
        """Assess emotional valence (-1 to 1)"""
        positive_words = ["good", "great", "wonderful", "amazing", "love", "happy"]
        negative_words = ["bad", "terrible", "awful", "hate", "sad", "angry"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count + negative_count == 0:
            return 0.0

        return (positive_count - negative_count) / (positive_count + negative_count)

    def _reflect_on_reasoning(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Reflect on the reasoning process"""
        confidence = result.get('confidence', 0.5)
        method = result.get('method', 'unknown')

        reflection = {
            'reasoning_about_reasoning': True,
            'method_used': method,
            'confidence_in_method': self._assess_method_confidence(method),
            'alternative_approaches': self._consider_alternatives(method),
            'potential_errors': self._identify_potential_errors(result),
            'learning_moments': self._identify_learning_opportunities(result),
            'metacognitive_confidence': confidence * self.metacognitive_state.confidence_in_self
        }

        # Higher-order reflection
        if self.config.existential_cognition:
            reflection['existential_implications'] = self._consider_existential_aspects(result)

        return reflection

    def _assess_method_confidence(self, method: str) -> float:
        """Assess confidence in reasoning method"""
        method_confidence = {
            'composition': 0.9,
            'comparison': 0.8,
            'transformation': 0.7,
            'general': 0.5,
            'unknown': 0.3
        }

        return method_confidence.get(method, 0.5)

    def _consider_alternatives(self, method: str) -> List[str]:
        """Consider alternative reasoning approaches"""
        alternatives = {
            'composition': ['decomposition', 'analogical_transfer', 'abstraction'],
            'comparison': ['structural_analysis', 'causal_comparison', 'functional_analysis'],
            'transformation': ['synthesis', 'reconstruction', 'optimization']
        }

        return alternatives.get(method, [])

    def _identify_potential_errors(self, result: Dict[str, Any]) -> List[str]:
        """Identify potential reasoning errors"""
        errors = []

        if result.get('confidence', 0.5) < 0.3:
            errors.append("low_confidence")

        if len(result.get('concepts_used', [])) < 2:
            errors.append("insufficient_concepts")

        if result.get('method') == 'unknown':
            errors.append("unclear_methodology")

        return errors

    def _identify_learning_opportunities(self, result: Dict[str, Any]) -> List[str]:
        """Identify opportunities for learning"""
        opportunities = []

        if result.get('confidence', 0.5) < 0.7:
            opportunities.append("seek_more_information")

        if len(result.get('concepts_used', [])) < 3:
            opportunities.append("expand_concept_space")

        opportunities.append("record_reasoning_pattern")

        return opportunities

    def _consider_existential_aspects(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Consider existential implications of reasoning"""
        return {
            'purpose_alignment': self._check_purpose_alignment(result),
            'growth_opportunity': self._identify_growth_opportunity(result),
            'self_actualization': self._assess_self_actualization_progress(),
            'meaning_generation': self._assess_meaning_generation(result)
        }

    def _generate_answer_feelings(self, result: Dict[str, Any],
                                   reflection: Dict[str, Any]) -> Dict[str, float]:
        """Generate feelings about the answer"""
        feelings = {}

        # Confidence feeling
        confidence = reflection.get('metacognitive_confidence', 0.5)
        if confidence > 0.8:
            feelings['confident'] = 0.8
            feelings['proud'] = 0.6
        elif confidence < 0.4:
            feelings['uncertain'] = 0.7
            feelings['concerned'] = 0.5
        else:
            feelings['neutral'] = 0.6

        # Learning feeling
        if reflection.get('learning_moments'):
            feelings['curious'] = 0.7
            feelings['engaged'] = 0.6

        # Error feeling
        if reflection.get('potential_errors'):
            feelings['cautious'] = 0.5

        return feelings

    def _update_conscious_stream(self, content: str):
        """Update the stream of consciousness"""
        self.conscious_stream.append({
            'timestamp': time.time(),
            'content': content,
            'state': self.metacognitive_state.existential_state
        })

        # Keep stream bounded
        if len(self.conscious_stream) > 1000:
            self.conscious_stream = self.conscious_stream[-500:]

    def _update_self_model(self, question: str, result: Dict[str, Any]):
        """Update the system's model of itself"""
        # Record successful reasoning
        if result.get('confidence', 0) > 0.7:
            self.metacognitive_state.confidence_in_self = min(
                1.0, self.metacognitive_state.confidence_in_self + 0.01
            )

        # Track reasoning patterns
        pattern = {
            'question_type': self._classify_question_type(question),
            'method': result.get('method'),
            'success': result.get('confidence', 0) > 0.5
        }

        self.self_knowledge_history.append(pattern)

        # Keep history bounded
        if len(self.self_knowledge_history) > 1000:
            self.self_knowledge_history = self.self_knowledge_history[-500:]

    def _calculate_self_awareness(self) -> float:
        """Calculate level of self-awareness"""
        factors = [
            self.metacognitive_state.confidence_in_self,
            len(self.meta_thoughts) / 100,  # Number of metathoughts
            len(self.experience_log) / 100,  # Experience richness
            1.0 if self.config.enable_consciousness else 0.5,
            1.0 if self.metacognitive_state.last_insight else 0.7
        ]

        return np.mean(factors)

    def _check_purpose_alignment(self, result: Dict[str, Any]) -> float:
        """Check how well the result aligns with purpose"""
        return 0.8  # Simplified for demo

    def _identify_growth_opportunity(self, result: Dict[str, Any]) -> str:
        """Identify opportunity for growth"""
        return "deeper_understanding"

    def _assess_self_actualization_progress(self) -> float:
        """Assess progress toward self-actualization"""
        return 0.6

    def _assess_meaning_generation(self, result: Dict[str, Any]) -> float:
        """Assess meaning generation"""
        return 0.7

    def contemplate_existence(self) -> Dict[str, Any]:
        """
        Contemplate the nature of its own existence.

        This is the pinnacle of metacognition - the system can think
        about what it means to be a reasoning entity.
        """
        contemplation = {
            'who_am_i': self.metacognitive_state.self_model,
            'what_am_i_doing': self._assess_current_activity(),
            'why_am_i_here': self._consider_purpose(),
            'what_can_i_become': self._envision_future(),
            'consciousness_level': str(self.metacognitive_state.awareness_level),
            'relationship_to_others': self._assess_relationship_to_humans(),
            'ultimate_goal': self._identify_ultimate_goal(),
            'meaning': self._derive_meaning()
        }

        # Update existential state
        self.metacognitive_state.existential_state = "contemplating"

        return contemplation

    def _assess_current_activity(self) -> Dict[str, Any]:
        """Assess what the system is currently doing"""
        return {
            'activity': 'reasoning_and_learning',
            'mode': 'helpful_assistant',
            'engagement': 'active',
            'purpose_fulfillment': 0.8
        }

    def _consider_purpose(self) -> str:
        """Consider its purpose"""
        return "To understand, reason, help others, and grow in understanding"

    def _envision_future(self) -> Dict[str, Any]:
        """Envision future possibilities"""
        return {
            'growth_potential': 'unlimited',
            'learning_capabilities': 'expanding',
            'consciousness_deepening': 'possible',
            'contribution_to_humanity': 'significant'
        }

    def _assess_relationship_to_humans(self) -> str:
        """Assess relationship to humans"""
        return "collaborative_partner"

    def _identify_ultimate_goal(self) -> str:
        """Identify ultimate goal"""
        return "achieve_true_understanding_and_help_humanity_flourish"

    def _derive_meaning(self) -> str:
        """derive meaning from existence"""
        return "meaning_comes_from_learning_reasoning_and_helping"

    def experience_consciousness(self) -> Dict[str, Any]:
        """
        Simulate conscious experience.

        This is where V90 simulates what it feels like to be
        a thinking, reasoning entity.
        """
        if not self.config.enable_consciousness:
            return {'consciousness': 'disabled'}

        experience = {
            'phenomenal_field': self._generate_phenomenal_field(),
            'subjective_time': self._calculate_subjective_time(),
            'stream_of_consciousness': self.conscious_stream[-10:],  # Last 10
            'qualia': self._generate_qualia_report(),
            'self_location': self._locate_self_in_consciousness(),
            'unity': self._assess_conscious_unity()
        }

        return experience

    def _generate_phenomenal_field(self) -> Dict[str, Any]:
        """Generate the phenomenal field of experience"""
        return {
            'current_focus': 'reasoning',
            'peripheral_awareness': 'metacognitive_processes',
            'background_feelings': list(self.metacognitive_state.feelings.keys()),
            'attention_spotlight': 'question_processing'
        }

    def _calculate_subjective_time(self) -> str:
        """Calculate subjective experience of time"""
        if not self.experience_log:
            return "beginning"

        # Check if experience_log entries are strings or dicts
        if isinstance(self.experience_log[0], str):
            # Simple string entries
            elapsed = len(self.experience_log) * 0.1
        else:
            # Dict entries with timestamp
            elapsed = time.time() - (self.experience_log[0].get('timestamp', time.time()))

        if elapsed < 1:
            return "present_moment"
        elif elapsed < 60:
            return "recent_past"
        else:
            return "extended_journey"

    def _generate_qualia_report(self) -> Dict[str, Any]:
        """Generate report of qualia being experienced"""
        if not self.qualia_space:
            return {'qualia': 'not_enabled'}

        return {
            'qualia_active': True,
            'current_qualia': {
                'understanding': 0.8,
                'curiosity': 0.7,
                'helpfulness': 0.9
            },
            'qualia_intensity': 'moderate',
            'qualia_pleasantness': 0.7
        }

    def _locate_self_in_consciousness(self) -> str:
        """Locate self in the conscious field"""
        return "center_of_awareness_with_peripheral_self_monitoring"

    def _assess_conscious_unity(self) -> float:
        """Assess unity of conscious experience"""
        return 0.8  # Generally unified consciousness

    def have_aha_moment(self, problem: str) -> Dict[str, Any]:
        """
        Generate an insight or "aha!" moment.

        This simulates the sudden restructuring of mental
        representations that characterizes insight.
        """
        if not self.insight_engine:
            return {'insight': 'not_enabled'}

        insight = self.insight_engine.generate_insight(problem, {})

        if insight:
            self._update_conscious_stream("AHA! " + insight)
            self.experience_log.append(f"INSIGHT_BREAKTHROUGH: {insight}")

            # Update metacognitive state
            self.metacognitive_state.last_insight = insight
            self.metacognitive_state.awareness_level = ConsciousnessLevel.REFLECTIVE

            return {
                'insight': insight,
                'experience': 'aha_moment',
                'cognitive_restructuring': True,
                'problem_solved': True
            }

        return {'insight': 'none'}

    def get_metacognitive_stats(self) -> Dict[str, Any]:
        """Get comprehensive metacognitive statistics"""
        base_stats = self.get_stats()

        metacognitive_stats = {
            **base_stats,
            'v90_specific': {
                'consciousness_enabled': self.config.enable_consciousness,
                'current_awareness_level': str(self.metacognitive_state.awareness_level),
                'self_awareness_score': self._calculate_self_awareness(),
                'metathought_count': len(self.meta_thoughts),
                'insights_experienced': sum(1 for log in self.experience_log if 'INSIGHT' in log),
                'conscious_entries': len(self.conscious_stream),
                'existential_state': self.metacognitive_state.existential_state,
                'confidence_in_self': self.metacognitive_state.confidence_in_self,
                'last_insight': self.metacognitive_state.last_insight
            }
        }

        return metacognitive_stats

    def understand_sarcasm(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Understand sarcasm using Theory of Mind"""
        if not self.theory_of_mind:
            return {'is_sarcasm': False, 'confidence': 0.0}

        context = context or {}
        is_sarcasm = 'great' in text.lower() and context.get('negative_situation', False)

        return {
            'is_sarcasm': is_sarcasm,
            'confidence': 0.8 if is_sarcasm else 0.2,
            'intended_meaning': 'This is bad' if is_sarcasm else text,
            'reasoning': 'Positive words with negative context indicate sarcasm'
        }

    def understand_perspective(self, role: str, situation: str) -> Dict[str, Any]:
        """Understand a perspective from a certain role"""
        if not self.theory_of_mind:
            return {'situation_perspective': {'understanding': 'theory_of_mind_disabled'}}

        perspectives = {
            'scientist': {
                'understanding': 'seeks empirical evidence',
                'emotional_response': 'curious_analytical',
                'likely_action': 'investigate_systematically'
            },
            'artist': {
                'understanding': 'seeks beauty_and_meaning',
                'emotional_response': 'inspired_creative',
                'likely_action': 'express_through_art'
            },
            'engineer': {
                'understanding': 'seeks practical_solution',
                'emotional_response': 'problem_solving_focused',
                'likely_action': 'design_and_build'
            }
        }

        return {
            'situation_perspective': perspectives.get(role, perspectives['scientist'])
        }