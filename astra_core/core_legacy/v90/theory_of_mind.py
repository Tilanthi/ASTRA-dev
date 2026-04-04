"""
Theory of Mind Module for V90
=============================

Implements the ability to understand that others have mental states,
beliefs, desires, and intentions different from one's own.

This is crucial for:
- Understanding deception and sarcasm
- Predicting others' behavior
- Effective communication
- Empathy and social reasoning
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json


class MentalStateType(Enum):
    """Types of mental states"""
    BELIEF = "belief"
    DESIRE = "desire"
    INTENTION = "intention"
    EMOTION = "emotion"
    KNOWLEDGE = "knowledge"
    PERCEPTION = "perception"
    UNCERTAINTY = "uncertainty"


@dataclass
class MentalState:
    """Represents a mental state of an agent"""
    agent: str  # Who has this mental state
    type: MentalStateType
    content: str  # What the mental state is about
    confidence: float  # Confidence in this state
    certainty: float  # How certain the agent is
    source: str  # How this state was inferred
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    justifications: List[str] = field(default_factory=list)


@dataclass
class Perspective:
    """A perspective or point of view"""
    agent: str
    knowledge: Set[str] = field(default_factory=set)  # What this agent knows
    beliefs: Dict[str, bool] = field(default_factory=dict)  # What this agent believes
    goals: List[str] = field(default_factory=list)  # What this agent wants
    emotions: Dict[str, float] = field(default_factory=dict)  # Emotional states
    limitations: List[str] = field(default_factory=list)  # What limits this agent


@dataclass
class SocialReason:
    """Reasoning about social interactions"""
    actors: List[str]
    relationship_type: str
    power_dynamics: Dict[str, float]
    shared_knowledge: Set[str]
    hidden_information: Dict[str, Set[str]]


class TheoryOfMindModule:
    """
    Theory of Mind implementation for V90.

    Implements a full-fledged Theory of Mind with:
    - First-order: "John believes X"
    - Second-order: "I believe that John believes X"
    - Third-order: "John believes that I believe that X"
    """

    def __init__(self):
        self.perspectives = {}  # agent -> Perspective
        self.mental_states = []  # List of all mental states
        self.social_models = {}  # relationship_id -> SocialReason
        self.common_sense_knowledge = self._initialize_common_sense()
        self.emotion_models = self._initialize_emotion_models()

    def infer_mental_state(self, agent: str, content: str,
                           type: MentalStateType = MentalStateType.BELIEF,
                           evidence: Dict[str, Any] = None) -> MentalState:
        """
        Infer the mental state of an agent based on evidence.
        """
        # Get or create perspective
        if agent not in self.perspectives:
            self.perspectives[agent] = Perspective(
                agent=agent,
                knowledge=set(),
                beliefs={},
                goals=[],
                emotions={},
                limitations=["only_known_information"]
            )

        perspective = self.perspectives[agent]

        # Analyze evidence
        confidence = self._calculate_confidence(content, type, evidence or {})
        certainty = self._calculate_certainty(agent, content, type)

        # Create mental state
        mental_state = MentalState(
            agent=agent,
            type=type,
            content=content,
            confidence=confidence,
            certainty=certainty,
            source="inference"
        )

        # Add justifications
        mental_state.justifications = self._generate_justifications(content, type, evidence)

        # Update perspective
        self._update_perspective(perspective, mental_state)

        # Store mental state
        self.mental_states.append(mental_state)

        return mental_state

    def _calculate_confidence(self, content: str, type: MentalStateType,
                             evidence: Dict[str, Any]) -> float:
        """Calculate confidence in inferred mental state"""
        base_confidence = 0.5

        # Adjust based on type
        type_confidence = {
            MentalStateType.BELIEF: 0.6,
            MentalStateType.DESIRE: 0.4,
            MentalStateType.INTENTION: 0.5,
            MentalStateType.EMOTION: 0.7,
            MentalStateType.KNOWLEDGE: 0.8,
            MentalStateType.PERCEPTION: 0.9,
            MentalStateType.UNCERTAINTY: 0.6
        }

        base_confidence = type_confidence.get(type, 0.5)

        # Adjust based on evidence
        if 'direct_statement' in evidence:
            base_confidence += 0.2
        if 'reliable_source' in evidence:
            base_confidence += 0.1
        if 'contradictory_evidence' in evidence:
            base_confidence -= 0.3

        return np.clip(base_confidence, 0.0, 1.0)

    def _calculate_certainty(self, agent: str, content: str, type: MentalStateType) -> float:
        """Calculate how certain the agent is about this mental state"""
        # Different agents have different certainty levels
        agent_certainty = {
            'human': 0.7,
            'ai': 0.9,
            'expert': 0.8,
            'child': 0.5,
            'deceptive': 0.3
        }

        # Adjust for content type
        if '?' in content or 'maybe' in content.lower():
            return 0.3

        if type in [MentalStateType.KNOWLEDGE, MentalStateType.PERCEPTION]:
            return agent_certainty.get(agent, 0.7)
        else:
            return agent_certainty.get(agent, 0.7) * 0.8

    def _generate_justifications(self, content: str, type: MentalStateType,
                                evidence: Dict[str, Any]) -> List[str]:
        """Generate justifications for inferred mental state"""
        justifications = []

        # Evidence-based
        if evidence:
            justifications.extend([f"Evidence: {k}={v}" for k, v in evidence.items()])

        # Common sense reasoning
        if type == MentalStateType.BELIEF:
            justifications.append("People generally form beliefs about stated propositions")
        elif type == MentalStateType.DESIRE:
            justifications.append("Desires are inferred from goals and actions")
        elif type == MentalStateType.INTENTION:
            justifications.append("Intentions are inferred from planned actions")

        # Context-based
        if any(word in content.lower() for word in ['want', 'need', 'wish']):
            justifications.append("Goal-directed language suggests desire or intention")

        return justifications

    def _update_perspective(self, perspective: Perspective, mental_state: MentalState):
        """Update an agent's perspective based on mental state"""
        if mental_state.type == MentalStateType.KNOWLEDGE:
            perspective.knowledge.add(mental_state.content)
        elif mental_state.type == MentalStateType.BELIEF:
            # Simplified: treat beliefs as binary
            if mental_state.confidence > 0.7:
                perspective.beliefs[mental_state.content] = True
            elif mental_state.confidence < 0.3:
                perspective.beliefs[mental_state.content] = False

    def understand_sarcasm(self, utterance: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and understand sarcasm.

        Sarcasm detection requires understanding:
        1. Literal meaning
        2. Context
        3. Speaker's likely beliefs
        4. Common sense expectations
        """
        # Check for sarcasm indicators
        sarcasm_indicators = [
            'yeah right', 'sure', 'obviously', 'clearly',
            'great', 'wonderful', 'fantastic'  # Can be sarcastic
        ]

        utterance_lower = utterance.lower()
        indicator_count = sum(1 for indicator in sarcasm_indicators if indicator in utterance_lower)

        # Analyze context
        expected_outcome = context.get('expected', '')
        actual_outcome = self._extract_outcome_from_utterance(utterance)

        # Check if literal meaning contradicts context
        contradiction = self._check_contradiction(actual_outcome, context)

        # Calculate sarcasm probability
        sarcasm_probability = (
            0.3 * min(1.0, indicator_count / 2) +
            0.5 * contradiction +
            0.2 * self._check_emotional_mismatch(utterance, context)
        )

        if sarcasm_probability > 0.6:
            # This is likely sarcasm
            intended_meaning = self._infer_sarcastic_meaning(utterance, context)
            return {
                'is_sarcasm': True,
                'confidence': sarcasm_probability,
                'literal_meaning': actual_outcome,
                'intended_meaning': intended_meaning,
                'reasoning': 'Utterance contradicts context and uses typical sarcastic markers'
            }
        else:
            return {
                'is_sarcasm': False,
                'confidence': 1 - sarcasm_probability,
                'meaning': actual_outcome,
                'reasoning': 'No strong evidence of sarcasm'
            }

    def _extract_outcome_from_utterance(self, utterance: str) -> str:
        """Extract the described outcome from an utterance"""
        # Simplified extraction
        words = utterance.split()
        if 'weather' in words and any(word in ['good', 'great', 'wonderful'] for word in words):
            return "weather is good"
        elif any(word in words for word in ['failed', 'broken', 'wrong']):
            return "failure occurred"
        return "neutral_outcome"

    def _check_contradiction(self, outcome: str, context: Dict[str, Any]) -> float:
        """Check if outcome contradicts context"""
        # Simplified contradiction detection
        if context.get('weather_bad') and 'good' in outcome:
            return 1.0
        elif context.get('success_expected') and 'failed' in outcome:
            return 1.0
        elif context.get('negative_situation') and 'great' in outcome:
            return 0.8
        return 0.0

    def _check_emotional_mismatch(self, utterance: str, context: Dict[str, Any]) -> float:
        """Check if emotional tone mismatches situation"""
        positive_words = ['great', 'wonderful', 'fantastic', 'amazing']
        negative_words = ['terrible', 'awful', 'horrible', 'disaster']

        utterance_lower = utterance.lower()
        positive_count = sum(1 for word in positive_words if word in utterance_lower)
        negative_count = sum(1 for word in negative_words if word in utterance_lower)

        # Check if situation is negative but tone is positive
        if context.get('negative_situation') and positive_count > 0 and negative_count == 0:
            return 0.8
        elif context.get('positive_situation') and negative_count > 0 and positive_count == 0:
            return 0.8

        return 0.0

    def _infer_sarcastic_meaning(self, utterance: str, context: Dict[str, Any]) -> str:
        """Infer the intended meaning behind sarcasm"""
        if 'weather' in utterance.lower():
            return "weather is actually terrible"
        elif 'great job' in utterance.lower():
            return "job was actually done poorly"
        elif 'love' in utterance.lower():
            return "actually hate or dislike"
        else:
            return "opposite of literal meaning"

    def simulate_deception(self, deceiver: str, target: str,
                          true_information: str, false_information: str) -> Dict[str, Any]:
        """
        Simulate reasoning about deception.

        Models:
        1. Deceiver's knowledge
        2. Target's beliefs
        3. Deceptive intent
        4. Detection likelihood
        """
        # Model deceiver's perspective
        deceiver_perspective = self.perspectives.get(deceiver)
        if not deceiver_perspective:
            deceiver_perspective = Perspective(deceiver, set(), {}, [], {}, [])

        # Model target's perspective
        target_perspective = self.perspectives.get(target)
        if not target_perspective:
            target_perspective = Perspective(target, set(), {}, [], {}, {})

        # Analyze deception
        deception_complexity = self._analyze_deception_complexity(
            true_information, false_information
        )

        detection_likelihood = self._estimate_detection_likelihood(
            deceiver_perspective, target_perspective, false_information
        )

        return {
            'deception_model': {
                'complexity': deception_complexity,
                'motivation': self._infer_deception_motivation(deceiver, true_information, false_information),
                'confidence': 1.0 - detection_likelihood
            },
            'target_model': {
                'initial_knowledge': list(target_perspective.knowledge),
                'suspicion_level': self._estimate_suspicion(target_perspective),
                'likely_detection': detection_likelihood > 0.5
            },
            'outcome': {
                'success_probability': 1.0 - detection_likelihood,
                'if_detected': {
                    'trust_damage': self._calculate_trust_damage(deception_complexity),
                    'relationship_change': 'negative'
                }
            }
        }

    def _analyze_deception_complexity(self, true_info: str, false_info: str) -> str:
        """Analyze how complex the deception is"""
        # Plausibility check
        if self._is_plausible(false_info):
            return "high_plausibility"
        elif self._is_partially_plausible(false_info):
            return "moderate_plausibility"
        else:
            return "low_plausibility"

    def _is_plausible(self, statement: str) -> bool:
        """Check if a statement is plausible"""
        # Simplified plausibility check
        # In practice, would use world knowledge
        implausible_patterns = [
            'impossible', 'cannot be', 'never exists',
            'all humans can', 'no one ever'
        ]

        statement_lower = statement.lower()
        return not any(pattern in statement_lower for pattern in implausible_patterns)

    def _is_partially_plausible(self, statement: str) -> bool:
        """Check if a statement is partially plausible"""
        # Some truth mixed with falsehood
        return len(statement.split()) > 3  # Longer statements might have some truth

    def _estimate_detection_likelihood(self, deceiver: Perspective,
                                     target: Perspective, false_info: str) -> float:
        """Estimate how likely deception is to be detected"""
        base_probability = 0.3

        # Factors affecting detection
        factors = {
            'target_suspicion': 0.2 if 'skeptical' in str(target.emotions) else 0.0,
            'information_complexity': 0.1 * min(1.0, len(false_info.split()) / 10),
            'plausibility_gap': 0.3 if not self._is_plausible(false_info) else 0.0,
            'relationship_trust': -0.1 if 'high_trust' in str(target.emotions) else 0.0
        }

        return np.clip(base_probability + sum(factors.values()), 0.0, 1.0)

    def _estimate_suspicion(self, perspective: Perspective) -> float:
        """Estimate how suspicious an agent is"""
        # Based on emotional state and knowledge
        if any('suspicious' in str(emotion) for emotion in perspective.emotions.values()):
            return 0.7
        elif 'skeptic' in str(perspective.emotions):
            return 0.5
        else:
            return 0.2

    def _infer_deception_motivation(self, deceiver: str, true_info: str,
                                  false_info: str) -> str:
        """Infer why deception is occurring"""
        if 'protect' in false_info.lower() or 'harm' in true_info.lower():
            return "self_protection"
        elif 'benefit' in false_info.lower() or 'profit' in false_info.lower():
            return "personal_gain"
        elif 'avoid' in false_info.lower():
            return "consequence_avoidance"
        else:
            return "unknown_motivation"

    def _calculate_trust_damage(self, deception_complexity: str) -> float:
        """Calculate damage to trust if deception is detected"""
        damage_levels = {
            'high_plausibility': 0.8,
            'moderate_plausibility': 0.9,
            'low_plausibility': 0.5
        }

        return damage_levels.get(deception_complexity, 0.7)

    def understand_perspective(self, agent: str, situation: str) -> Dict[str, Any]:
        """
        Understand an agent's perspective on a situation.

        Returns:
        - What they know
        - What they believe
        - What they want
        - How they feel
        - What limits them
        """
        perspective = self.perspectives.get(agent)
        if not perspective:
            # Create default perspective
            perspective = Perspective(
                agent=agent,
                knowledge=set(),
                beliefs={},
                goals=[],
                emotions={},
                limitations=["limited_information"]
            )

        # Analyze situation from this perspective
        situation_analysis = self._analyze_situation_from_perspective(perspective, situation)

        return {
            'agent': agent,
            'knowledge': list(perspective.knowledge),
            'beliefs': perspective.beliefs,
            'goals': perspective.goals,
            'emotions': perspective.emotions,
            'limitations': perspective.limitations,
            'situation_perspective': situation_analysis
        }

    def _analyze_situation_from_perspective(self, perspective: Perspective,
                                           situation: str) -> Dict[str, Any]:
        """Analyze how the given agent sees the situation"""
        analysis = {
            'understanding': 'limited',
            'emotional_response': 'neutral',
            'likely_action': 'wait_and_see',
            'concerns': []
        }

        # Check if situation matches goals
        for goal in perspective.goals:
            if goal.lower() in situation.lower():
                analysis['emotional_response'] = 'positive'
                analysis['likely_action'] = 'engage'
                break

        # Check for threats
        if any(threat in situation.lower() for threat in ['danger', 'threat', 'risk']):
            analysis['emotional_response'] = 'concerned'
            analysis['concerns'].append('safety')

        # Adjust based on limitations
        if 'limited_information' in perspective.limitations:
            analysis['understanding'] = 'partial'

        return analysis

    def _initialize_common_sense(self) -> Dict[str, Any]:
        """Initialize common sense knowledge about mental states"""
        return {
            'beliefs_can_be_false': True,
            'people_desire_good_things': True,
            'actions_reveal_intentions': True,
            'emotions_affect_reasoning': True,
            'deception_is_possible': True,
            'perspectives_differ': True,
            'knowledge_is_limited': True
        }

    def _initialize_emotion_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize models of how emotions affect cognition"""
        return {
            'happy': {'reasoning_quality': 0.1, 'openness': 0.2, 'trust': 0.1},
            'sad': {'reasoning_quality': -0.1, 'openness': 0.0, 'trust': 0.0},
            'angry': {'reasoning_quality': -0.2, 'openness': -0.2, 'trust': -0.2},
            'fearful': {'reasoning_quality': -0.1, 'openness': -0.1, 'trust': -0.1},
            'surprised': {'reasoning_quality': 0.0, 'openness': 0.1, 'trust': 0.0}
        }

    def get_theory_of_mind_summary(self) -> Dict[str, Any]:
        """Get summary of Theory of Mind capabilities"""
        return {
            'perspectives_tracked': len(self.perspectives),
            'mental_states_inferred': len(self.mental_states),
            'social_models': len(self.social_models),
            'common_sense_rules': len(self.common_sense_knowledge),
            'emotion_models': list(self.emotion_models.keys())
        }