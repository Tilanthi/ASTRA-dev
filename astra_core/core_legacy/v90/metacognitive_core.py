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
Metacognitive Core for V90
========================

Implements the ability to think about thinking, monitor reasoning
processes, and reflect on one's own cognitive states.

Key Features:
- Higher-order thoughts (HOT)
- Metacognitive monitoring
- Self-regulation
- Error detection
- Confidence calibration
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class MetacognitiveLevel(Enum):
    """Levels of metacognitive awareness"""
    MONITORING = "monitoring"  # Watching own thoughts
    EVALUATING = "evaluating"  # Assessing thought quality
    CONTROLLING = "controlling"  # Regulating thinking
    REFLECTING = "reflecting"  # Deep reflection
    TRANSCENDING = "transcending"  # Beyond normal cognition


@dataclass
class ThoughtProcess:
    """Represents a thought process being monitored"""
    content: str
    start_time: float
    end_time: Optional[float] = None
    confidence: float = 0.5
    accuracy: Optional[float] = None
    metacognitive_level: MetacognitiveLevel = MetacognitiveLevel.MONITORING
    tags: List[str] = None
    parent_thought: Optional[str] = None
    child_thoughts: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.child_thoughts is None:
            self.child_thoughts = []


class MetacognitiveCore:
    """
    Core metacognitive system for V90.

    Implements Higher-Order Thought (HOT) theory:
    - First-order: "I think X"
    - Second-order: "I think that I think X"
    - Third-order: "I think that I think that I think X"
    """

    def __init__(self, depth: int = 5):
        self.max_depth = depth
        self.thought_stack = []
        self.monitoring_active = True
        self.metacognitive_beliefs = {
            'my_reasoning_is_generally_accurate': 0.8,
            'i_can_recognize_my_errors': 0.7,
            'confidence_indicates_accuracy': 0.6,
            'metacognition_improves_performance': 0.9
        }
        self.error_patterns = []
        self.success_patterns = []
        self.regulation_strategies = []

    def start_thought(self, content: str, level: MetacognitiveLevel = MetacognitiveLevel.MONITORING) -> ThoughtProcess:
        """Start monitoring a new thought process"""
        thought = ThoughtProcess(
            content=content,
            start_time=time.time(),
            confidence=0.5,
            metacognitive_level=level
        )

        self.thought_stack.append(thought)

        # If we're at high metacognitive levels, think about thinking
        if len(self.thought_stack) > 1 and self.monitoring_active:
            self._process_higher_order_thought(thought)

        return thought

    def _process_higher_order_thought(self, thought: ThoughtProcess):
        """Process higher-order thoughts about thinking"""
        current_level = len(self.thought_stack)

        if current_level >= 2:
            # Second-order thinking: "I'm thinking about X"
            parent_thought = self.thought_stack[-2]
            thought.parent_thought = parent_thought.content
            parent_thought.child_thoughts.append(thought.content)

            if current_level >= 3:
                # Third-order: "I'm aware that I'm thinking about X"
                self._reflect_on_thinking_pattern()

    def _reflect_on_thinking_pattern(self):
        """Reflect on the current pattern of thinking"""
        if len(self.thought_stack) < 2:
            return

        pattern = " -> ".join([t.content[:30] for t in self.thought_stack[-3:]])

        # Analyze pattern
        if "uncertain" in pattern.lower():
            self._update_metabelief('confidence_indicates_accuracy', -0.05)

        if "error" in pattern.lower():
            self._update_metabelief('i_can_recognize_my_errors', 0.1)

    def end_thought(self, thought: ThoughtProcess, accuracy: Optional[float] = None):
        """End monitoring of a thought process"""
        thought.end_time = time.time()
        thought.accuracy = accuracy

        # Update based on outcome
        if accuracy is not None:
            self._update_metabeliefs_from_feedback(thought)
            self._record_pattern(thought, accuracy)

        # Pop from stack if it's the current thought
        if self.thought_stack and self.thought_stack[-1] == thought:
            self.thought_stack.pop()

    def _update_metabeliefs_from_feedback(self, thought: ThoughtProcess):
        """Update metacognitive beliefs based on feedback"""
        # Was confidence calibrated?
        confidence_error = abs(thought.confidence - thought.accuracy)

        if confidence_error < 0.1:
            # Well-calibrated
            self._update_metabelief('confidence_indicates_accuracy', 0.02)
        else:
            # Poorly calibrated
            self._update_metabelief('confidence_indicates_accuracy', -0.03)

        # Was the thought accurate?
        if thought.accuracy > 0.7:
            self._update_metabelief('my_reasoning_is_generally_accurate', 0.01)
        elif thought.accuracy < 0.3:
            self._update_metabelief('my_reasoning_is_generally_accurate', -0.02)

    def _record_pattern(self, thought: ThoughtProcess, accuracy: float):
        """Record successful or error patterns"""
        pattern = {
            'content': thought.content,
            'confidence': thought.confidence,
            'level': thought.metacognitive_level,
            'tags': thought.tags
        }

        if accuracy > 0.7:
            self.success_patterns.append(pattern)
        elif accuracy < 0.3:
            self.error_patterns.append(pattern)

        # Keep patterns bounded
        self.success_patterns = self.success_patterns[-100:]
        self.error_patterns = self.error_patterns[-100:]

    def monitor_reasoning(self, reasoning_process: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor an ongoing reasoning process"""
        monitoring_result = {
            'monitoring_active': self.monitoring_active,
            'current_thoughts': len(self.thought_stack),
            'metacognitive_level': self._get_current_level(),
            'patterns_detected': self._detect_patterns(reasoning_process),
            'regulation_suggested': [],
            'confidence_calibration': self._assess_calibration()
        }

        # Detect potential issues
        issues = self._detect_reasoning_issues(reasoning_process)
        if issues:
            monitoring_result['issues'] = issues
            monitoring_result['regulation_suggested'] = self._suggest_regulation(issues)

        return monitoring_result

    def _get_current_level(self) -> str:
        """Get current metacognitive level"""
        if not self.thought_stack:
            return "none"
        return self.thought_stack[-1].metacognitive_level.value

    def _detect_patterns(self, reasoning_process: Dict[str, Any]) -> List[str]:
        """Detect thinking patterns"""
        patterns = []

        # Check for common patterns
        method = reasoning_process.get('method', '')
        confidence = reasoning_process.get('confidence', 0.5)

        if confidence > 0.9 and method != 'composition':
            patterns.append("overconfident_in_non_composition")

        if confidence < 0.3 and method == 'composition':
            patterns.append("underconfident_in_composition")

        if len(reasoning_process.get('concepts_used', [])) < 2:
            patterns.append("insufficient_concepts")

        # Check for historical patterns
        if self._matches_error_pattern(reasoning_process):
            patterns.append("historical_error_pattern")

        if self._matches_success_pattern(reasoning_process):
            patterns.append("historical_success_pattern")

        return patterns

    def _matches_error_pattern(self, reasoning_process: Dict[str, Any]) -> bool:
        """Check if reasoning matches known error pattern"""
        for pattern in self.error_patterns[-5:]:  # Recent errors
            if (pattern['method'] == reasoning_process.get('method') and
                abs(pattern['confidence'] - reasoning_process.get('confidence', 0.5)) < 0.1):
                return True
        return False

    def _matches_success_pattern(self, reasoning_process: Dict[str, Any]) -> bool:
        """Check if reasoning matches known success pattern"""
        for pattern in self.success_patterns[-5:]:  # Recent successes
            if (pattern['method'] == reasoning_process.get('method') and
                pattern['level'] == reasoning_process.get('metacognitive_level', MetacognitiveLevel.MONITORING)):
                return True
        return False

    def _detect_reasoning_issues(self, reasoning_process: Dict[str, Any]) -> List[str]:
        """Detect potential issues in reasoning"""
        issues = []

        # Low confidence on important question
        confidence = reasoning_process.get('confidence', 0.5)
        if confidence < 0.4:
            issues.append("low_confidence")

        # Using unknown method
        method = reasoning_process.get('method', '')
        if method == 'unknown':
            issues.append("unclear_method")

        # Too fast reasoning (may indicate insufficient depth)
        time_taken = reasoning_process.get('reasoning_time', 0)
        if time_taken < 0.001:  # Less than 1ms
            issues.append("rushed_reasoning")

        # No concepts used
        if not reasoning_process.get('concepts_used'):
            issues.append("no_grounding")

        return issues

    def _suggest_regulation(self, issues: List[str]) -> List[str]:
        """Suggest cognitive regulation strategies"""
        strategies = []

        for issue in issues:
            if issue == "low_confidence":
                strategies.append("seek_more_information")
                strategies.append("use_compositional_reasoning")
            elif issue == "unclear_method":
                strategies.append("clarify_approach")
                strategies.append("use_known_strategy")
            elif issue == "rushed_reasoning":
                strategies.append("slow_down")
                strategies.append("deepen_analysis")
            elif issue == "no_grounding":
                strategies.append("connect_to_concepts")
                strategies.append("use_examples")

        return strategies

    def _assess_calibration(self) -> Dict[str, float]:
        """Assess how well confidence predicts accuracy"""
        if not self.success_patterns and not self.error_patterns:
            return {'calibration_score': 0.5, 'sample_size': 0}

        all_patterns = self.success_patterns + self.error_patterns
        calibration_errors = [
            abs(p['confidence'] - (1.0 if p in self.success_patterns else 0.0))
            for p in all_patterns
        ]

        avg_error = np.mean(calibration_errors)
        calibration_score = 1.0 - avg_error  # Higher is better

        return {
            'calibration_score': calibration_score,
            'sample_size': len(all_patterns),
            'avg_confidence_error': avg_error
        }

    def self_regulate(self, strategy: str) -> Dict[str, Any]:
        """Apply a self-regulation strategy"""
        regulation_result = {
            'strategy': strategy,
            'applied': True,
            'effect': None,
            'new_state': None
        }

        if strategy == "seek_more_information":
            regulation_result['effect'] = "expanded_context"
            regulation_result['new_state'] = "information_seeking"

        elif strategy == "use_compositional_reasoning":
            regulation_result['effect'] = "breaking_down_problem"
            regulation_result['new_state'] = "analytical_mode"

        elif strategy == "slow_down":
            regulation_result['effect'] = "deliberate_pacing"
            regulation_result['new_state'] = "careful_reasoning"

        elif strategy == "connect_to_concepts":
            regulation_result['effect'] = "grounding_enhanced"
            regulation_result['new_state'] = "conceptual_mode"

        return regulation_result

    def _update_metabelief(self, belief: str, delta: float):
        """Update a metacognitive belief with learning rate"""
        current = self.metacognitive_beliefs.get(belief, 0.5)
        # Use smaller learning rate for core beliefs
        learning_rate = 0.01 if belief in ['my_reasoning_is_generally_accurate'] else 0.05

        new_value = current + delta * learning_rate
        self.metacognitive_beliefs[belief] = np.clip(new_value, 0.0, 1.0)

    def get_metacognitive_summary(self) -> Dict[str, Any]:
        """Get summary of metacognitive state"""
        return {
            'active_thoughts': len(self.thought_stack),
            'metabeliefs': self.metacognitive_beliefs,
            'error_patterns_count': len(self.error_patterns),
            'success_patterns_count': len(self.success_patterns),
            'calibration': self._assess_calibration(),
            'monitoring': self.monitoring_active,
            'depth': self.max_depth
        }