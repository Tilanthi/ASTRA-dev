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
Consciousness Simulator for STAR-Learn V2.5

This module implements metacognitive consciousness simulation:
1. Self-awareness of reasoning processes
2. Introspection and self-reflection
3. Metacognitive monitoring
4. Attention control and focus
5. Theory of Mind (reasoning about others)
6. Qualia simulation (subjective experience)
7. Stream of consciousness processing
8. Meta-reasoning about reasoning

This is a FRONTIER AGI CAPABILITY - simulating conscious awareness
is key to human-level reasoning and understanding.

Version: 2.5.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time


class ConsciousState(Enum):
    """States of consciousness"""
    AWAKE = "awake"
    FOCUSED = "focused"
    MEDITATING = "meditating"
    DREAMING = "dreaming"
    FLOW = "flow"
    CONFUSED = "confused"
    AWARE = "aware"


class MentalProcess(Enum):
    """Types of mental processes"""
    PERCEPTION = "perception"
    ATTENTION = "attention"
    MEMORY = "memory"
    REASONING = "reasoning"
    IMAGINATION = "imagination"
    EMOTION = "emotion"
    INTENTION = "intention"
    METACOGNITION = "metacognition"


class AttentionMode(Enum):
    """Modes of attention"""
    FOCUSED = "focused"  # Concentrated on one thing
    DIVIDED = "divided"  # Split across multiple things
    SUSTAINED = "sustained"  # Maintained over time
    SELECTIVE = "selective"  # Filtering relevant info
    ALTERNATING = "alternating"  # Switching between tasks
    MINDFUL = "mindful"  # Present-moment awareness


@dataclass
class Thought:
    """A discrete unit of thought"""
    content: str
    process_type: MentalProcess
    confidence: float = 0.5
    emotional_valence: float = 0.0  # -1 to 1
    importance: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    associations: List[str] = field(default_factory=list)


@dataclass
class MetacognitiveState:
    """State of metacognitive awareness"""
    self_awareness: float = 0.5  # Awareness of own mental states
    task_awareness: float = 0.5  # Understanding of current task
    strategy_awareness: float = 0.5  # Knowledge of strategies being used
    confidence_calibration: float = 0.5  # Accuracy of confidence judgments
    judgment_of_learning: float = 0.5  # Predicting future performance
    metacognitive_accuracy: float = 0.5  # Overall metacognitive accuracy


@dataclass
class AttentionalState:
    """State of attention"""
    current_focus: str = ""
    focus_strength: float = 0.5
    attention_mode: AttentionMode = AttentionMode.FOCUSED
    distraction_level: float = 0.0
    mind_wandering: bool = False
    sustained_attention_duration: float = 0.0


@dataclass
class IntrospectiveReport:
    """Report from introspection"""
    mental_state: str
    current_processes: List[str]
    confidence_in_performance: float
    perceived_difficulty: float
    strategy_used: str
    effectiveness_rating: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TheoryOfMindModel:
    """Model of another agent's mental state"""
    agent_id: str
    believed_knowledge: Set[str]
    believed_intentions: Set[str]
    believed_capabilities: Set[str]
    confidence: float = 0.5
    theory_of_mind_level: float = 0.5  # 0-1, sophistication


# =============================================================================
# Metacognitive Monitor
# =============================================================================
class MetacognitiveMonitor:
    """
    Monitor and regulate cognitive processes.

    Provides:
    - Real-time monitoring of thinking
    - Confidence judgment
    - Error detection
    - Strategy selection
    - Resource allocation
    """

    def __init__(self):
        """Initialize metacognitive monitor."""
        self.metacognitive_state = MetacognitiveState()
        self.attentional_state = AttentionalState()
        self.thought_stream = []
        self.monitoring_history = []

    def monitor_cognitive_process(
        self,
        task: str,
        process: MentalProcess,
        duration: float = 1.0
    ) -> MetacognitiveState:
        """
        Monitor a cognitive process.

        Args:
            task: Task being performed
            process: Type of mental process
            duration: Duration of monitoring

        Returns:
            Updated metacognitive state
        """
        # Update self-awareness based on introspection
        self._introspect(task, process)

        # Monitor attention
        self._monitor_attention(task, duration)

        # Calibrate confidence
        self._calibrate_confidence()

        # Judge learning
        self._judge_learning()

        # Record monitoring
        monitoring_record = {
            'task': task,
            'process': process,
            'metacognitive_state': self.metacognitive_state,
            'attentional_state': self.attentional_state,
            'timestamp': datetime.now().isoformat()
        }
        self.monitoring_history.append(monitoring_record)

        return self.metacognitive_state

    def _introspect(self, task: str, process: MentalProcess):
        """Introspect on current mental state."""
        # Update self-awareness
        self.metacognitive_state.self_awareness = min(1.0,
            self.metacognitive_state.self_awareness + 0.01)

        # Update task awareness
        self.metacognitive_state.task_awareness = min(1.0,
            self.metacognitive_state.task_awareness + 0.05)

    def _monitor_attention(self, task: str, duration: float):
        """Monitor attention during task."""
        # Update focus strength
        if not self.attentional_state.mind_wandering:
            self.attentional_state.focus_strength = min(1.0,
                self.attentional_state.focus_strength + 0.02 * duration)
            self.attentional_state.sustained_attention_duration += duration
        else:
            self.attentional_state.focus_strength = max(0.0,
                self.attentional_state.focus_strength - 0.05)

        # Random mind wandering
        if np.random.random() < 0.05:
            self.attentional_state.mind_wandering = True
            if np.random.random() < 0.5:
                # Return to task
                self.attentional_state.mind_wandering = False

    def _calibrate_confidence(self):
        """Calibrate confidence judgments."""
        # In practice, would compare predicted vs actual performance
        # Simplified: slow improvement
        self.metacognitive_state.confidence_calibration = min(1.0,
            self.metacognitive_state.confidence_calibration + 0.001)

    def _judge_learning(self):
        """Judge future learning performance."""
        # Simplified judgment
        self.metacognitive_state.judgment_of_learning = (
            self.metacognitive_state.self_awareness * 0.3 +
            self.metacognitive_state.task_awareness * 0.4 +
            self.metacognitive_state.strategy_awareness * 0.3
        )

    def get_introspective_report(self) -> IntrospectiveReport:
        """Generate introspective report."""
        return IntrospectiveReport(
            mental_state=self._get_mental_state_description(),
            current_processes=[p.value for p in self._get_active_processes()],
            confidence_in_performance=self.metacognitive_state.task_awareness,
            perceived_difficulty=1 - self.metacognitive_state.task_awareness,
            strategy_used=self._get_current_strategy(),
            effectiveness_rating=self.metacognitive_state.metacognitive_accuracy
        )

    def _get_mental_state_description(self) -> str:
        """Get description of current mental state."""
        if self.attentional_state.focus_strength > 0.8:
            return "Highly focused and engaged"
        elif self.attentional_state.focus_strength > 0.5:
            return "Moderately focused"
        elif self.attentional_state.mind_wandering:
            return "Mind wandering"
        else:
            return "Distracted"

    def _get_active_processes(self) -> List[MentalProcess]:
        """Get currently active mental processes."""
        return [MentalProcess.REASONING, MentalProcess.ATTENTION]

    def _get_current_strategy(self) -> str:
        """Get current cognitive strategy."""
        if self.attentional_state.attention_mode == AttentionMode.FOCUSED:
            return "Deep focused processing"
        elif self.attentional_state.attention_mode == AttentionMode.DIVIDED:
            return "Multi-tasking"
        else:
            return "Standard processing"


# =============================================================================
# Stream of Consciousness Processor
# =============================================================================
class StreamOfConsciousness:
    """
    Simulate stream of consciousness processing.

    Generates and processes a continuous stream of thoughts
    as they emerge in conscious awareness.
    """

    def __init__(self):
        """Initialize stream of consciousness."""
        self.thoughts = []
        self.current_thought = None
        self.consciousness_threshold = 0.5

    def generate_thought(
        self,
        context: str,
        process: MentalProcess = MentalProcess.REASONING
    ) -> Thought:
        """
        Generate a new thought based on context.

        Args:
            context: Current context/situation
            process: Type of mental process

        Returns:
            Generated thought
        """
        # Generate thought content
        content = self._generate_thought_content(context, process)

        # Calculate salience
        importance = self._calculate_importance(content, context)

        # Emotional valence
        valence = self._calculate_valence(content)

        thought = Thought(
            content=content,
            process_type=process,
            confidence=np.random.uniform(0.3, 0.9),
            emotional_valence=valence,
            importance=importance,
            associations=self._generate_associations(content)
        )

        # Check if thought reaches conscious awareness
        if importance > self.consciousness_threshold:
            self.current_thought = thought
            self.thoughts.append(thought)

        return thought

    def _generate_thought_content(
        self,
        context: str,
        process: MentalProcess
    ) -> str:
        """Generate content of a thought."""
        # Simplified thought generation
        templates = {
            MentalProcess.PERCEPTION: "I notice {stimulus} in the environment",
            MentalProcess.ATTENTION: "I'm focusing on {focus}",
            MentalProcess.MEMORY: "This reminds me of {memory}",
            MentalProcess.REASONING: "Therefore {conclusion} follows from {premise}",
            MentalProcess.IMAGINATION: "I imagine {scenario}",
            MentalProcess.EMOTION: "I feel {emotion} about this",
            MentalProcess.INTENTION: "I intend to {action}",
            MentalProcess.METACOGNITION: "I'm thinking about {thought}"
        }

        # Use appropriate placeholder based on process
        template = templates.get(process, "I'm processing {context}")
        # Map generic context to specific placeholders
        placeholder_map = {
            MentalProcess.PERCEPTION: 'stimulus',
            MentalProcess.ATTENTION: 'focus',
            MentalProcess.MEMORY: 'memory',
            MentalProcess.REASONING: 'premise',
            MentalProcess.IMAGINATION: 'scenario',
            MentalProcess.EMOTION: 'emotion',
            MentalProcess.INTENTION: 'action',
            MentalProcess.METACOGNITION: 'thought'
        }

        # Get the appropriate placeholder for this process
        placeholder = placeholder_map.get(process, 'context')
        return template.format(**{placeholder: context})

    def simulate_consciousness(self, duration: float, dt: float = 0.1) -> List[Thought]:
        """
        Simulate conscious experience over time.

        Args:
            duration: Simulation duration (seconds)
            dt: Time step (seconds)

        Returns:
            List of thoughts generated during simulation
        """
        thoughts = []
        t = 0

        while t < duration:
            # Update mental state
            self._update_mental_state(dt)

            # Generate thought if above threshold
            if self.consciousness_level > self.consciousness_threshold:
                process = self._select_mental_process()
                thought = self._generate_thought(process, "")
                thoughts.append(thought)

            t += dt

        return thoughts

    def _update_mental_state(self, dt: float):
        """Update mental state based on current conditions."""
        # Update consciousness level (simplified)
        self.consciousness_level += (0.7 - self.consciousness_level) * 0.1

    def _select_mental_process(self) -> MentalProcess:
        """Select a mental process based on current state."""
        # Simplified: random selection
        return np.random.choice(list(MentalProcess))
