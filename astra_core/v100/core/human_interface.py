"""
Human-in-the-Loop Interface (HITLI)
===================================

Enables collaborative refinement between V100 and human scientists.

Features:
- Interactive theory refinement
- Expert knowledge injection
- Validation feedback incorporation
- Publication workflow collaboration
- Community feedback integration

This ensures V100 benefits from human expertise while maintaining autonomy.

Author: STAN-XI ASTRO V100 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum, auto
import json
import time
from pathlib import Path


# =============================================================================
# Import V100 components
# =============================================================================
try:
    from ..theory.theory_synthesis import TheoryFramework
    from ..simulation.universe_simulator import PredictionResult
    from .validation import ValidationResult, ScientificPaper
    from .competition import CompetitionResult
except ImportError:
    TheoryFramework = None
    PredictionResult = None
    ValidationResult = None
    ScientificPaper = None
    CompetitionResult = None


# =============================================================================
# Enumerations
# =============================================================================

class InteractionMode(Enum):
    """Types of human-AI interaction"""
    FULLY_AUTONOMOUS = "autonomous"  # V100 operates independently
    HUMAN_GUIDED = "guided"  # Human provides high-level direction
    COLLABORATIVE = "collaborative"  # Equal partnership
    HUMAN_SUPERVISED = "supervised"  # Human approves each step
    ADVISORY = "advisory"  # V100 advises human


class FeedbackType(Enum):
    """Types of feedback from humans"""
    CORRECTION = "correction"  # Fix error
    SUGGESTION = "suggestion"  # Suggest improvement
    APPROVAL = "approval"  # Confirm correctness
    REJECTION = "rejection"  # Reject approach
    REFERENCE = "reference"  # Provide citation/knowledge
    DIRECTION = "direction"  # Redirect focus


class FeedbackChannel(Enum):
    """Channels for receiving feedback"""
    COMMAND_LINE = "cli"  # Interactive terminal
    WEB_INTERFACE = "web"  # Browser-based UI
    API = "api"  # Programmatic interface
    FILE = "file"  # Read from feedback files
    EMAIL = "email"  # Email notifications


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class HumanFeedback:
    """Feedback from a human expert"""
    id: str
    feedback_type: FeedbackType
    channel: FeedbackChannel

    # Content
    content: str
    target_type: str  # 'theory', 'prediction', 'paper', 'method'
    context: Optional[str] = None  # What is this feedback about?
    target_id: Optional[str] = None

    # Metadata
    timestamp: float = field(default_factory=time.time)
    expert_id: Optional[str] = None
    confidence: float = 0.8
    priority: float = 0.5  # [0, 1]

    # Status
    incorporated: bool = False
    incorporation_notes: Optional[str] = None


@dataclass
class CollaborationSession:
    """A session of human-AI collaboration"""
    session_id: str
    problem_name: str
    mode: InteractionMode

    # Participants
    human_experts: List[str] = field(default_factory=list)

    # Timeline
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    # Artifacts
    theories_generated: List[str] = field(default_factory=list)
    feedback_received: List[HumanFeedback] = field(default_factory=list)
    papers_generated: List[str] = field(default_factory=list)

    # Outcomes
    final_theory: Optional[str] = None
    human_contributions: List[str] = field(default_factory=list)

    def add_feedback(self, feedback: HumanFeedback):
        """Add feedback to session"""
        self.feedback_received.append(feedback)

    def duration_hours(self) -> float:
        """Get session duration in hours"""
        end = self.end_time or time.time()
        return (end - self.start_time) / 3600


@dataclass
class ExpertKnowledge:
    """Domain knowledge from human experts"""
    domain: str
    facts: List[str]
    constraints: List[str]  # Things that must be true/false
    references: List[str]  # Papers to cite
    heuristics: List[str]  # Rules of thumb

    # Confidence
    confidence: float = 0.9
    source: str = "human_expert"


# =============================================================================
# Human Interface Manager
# =============================================================================

class HumanInterfaceManager:
    """
    Manages human-AI collaboration.

    Features:
    - Receive and categorize feedback
    - Incorporate expert knowledge
    - Refine theories based on feedback
    - Generate human-readable explanations
    - Track collaboration sessions
    """

    def __init__(self, mode: InteractionMode = InteractionMode.COLLABORATIVE):
        self.mode = mode
        self.sessions: Dict[str, CollaborationSession] = {}
        self.feedback_history: List[HumanFeedback] = []
        self.expert_knowledge: Dict[str, ExpertKnowledge] = {}

        # Feedback queue
        self.pending_feedback: List[HumanFeedback] = []

    def create_session(
        self,
        problem_name: str,
        experts: List[str],
        mode: Optional[InteractionMode] = None
    ) -> CollaborationSession:
        """Create a new collaboration session"""
        session = CollaborationSession(
            session_id=f"session_{int(time.time())}",
            problem_name=problem_name,
            mode=mode or self.mode,
            human_experts=experts
        )

        self.sessions[session.session_id] = session
        return session

    def receive_feedback(
        self,
        feedback: str,
        feedback_type: FeedbackType,
        target_type: str,
        target_id: Optional[str] = None,
        expert_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> HumanFeedback:
        """
        Receive feedback from human expert.

        Parameters
        ----------
        feedback : str
            Feedback content
        feedback_type : FeedbackType
            Type of feedback
        target_type : str
            What the feedback is about
        target_id : str, optional
            ID of target artifact
        expert_id : str, optional
            Expert providing feedback
        session_id : str, optional
            Session to attach to

        Returns
        -------
        HumanFeedback object
        """
        fb = HumanFeedback(
            id=f"feedback_{int(time.time() * 1000000)}",
            feedback_type=feedback_type,
            channel=FeedbackChannel.COMMAND_LINE,
            content=feedback,
            target_type=target_type,
            target_id=target_id,
            expert_id=expert_id
        )

        self.feedback_history.append(fb)
        self.pending_feedback.append(fb)

        # Add to session if provided
        if session_id and session_id in self.sessions:
            self.sessions[session_id].add_feedback(fb)

        print(f"HITLI: Received {feedback_type.value} feedback from {expert_id or 'anonymous'}")

        return fb

    def incorporate_feedback(
        self,
        theory: TheoryFramework,
        feedback: List[HumanFeedback]
    ) -> TheoryFramework:
        """
        Incorporate human feedback into a theory.

        Parameters
        ----------
        theory : TheoryFramework
            Theory to refine
        feedback : list
            Feedback to incorporate

        Returns
        -------
        Refined TheoryFramework
        """
        print(f"HITLI: Incorporating {len(feedback)} feedback items")

        for fb in feedback:
            if fb.target_type == 'theory' and fb.target_id == theory.id:
                theory = self._apply_theory_feedback(theory, fb)
                fb.incorporated = True
                fb.incorporation_notes = "Applied to theory"

        return theory

    def _apply_theory_feedback(
        self,
        theory: TheoryFramework,
        feedback: HumanFeedback
    ) -> TheoryFramework:
        """Apply feedback to a theory"""

        if feedback.feedback_type == FeedbackType.CORRECTION:
            # Fix something in the theory
            return self._apply_correction(theory, feedback)

        elif feedback.feedback_type == FeedbackType.SUGGESTION:
            # Add suggested improvement
            return self._apply_suggestion(theory, feedback)

        elif feedback.feedback_type == FeedbackType.REFERENCE:
            # Add reference/knowledge
            return self._add_reference(theory, feedback)

        elif feedback.feedback_type == FeedbackType.DIRECTION:
            # Redirect theory focus
            return self._redirect_theory(theory, feedback)

        return theory

    def _apply_correction(
        self,
        theory: TheoryFramework,
        feedback: HumanFeedback
    ) -> TheoryFramework:
        """Apply correction to theory"""

        # Parse correction (simplified)
        content = feedback.content.lower()

        # Common corrections
        if 'width' in content and '0.1' in content:
            # Correcting width prediction
            for mechanism in theory.mechanisms:
                if 'width' in mechanism.get('description', '').lower():
                    mechanism['description'] = feedback.content
                    break

        elif 'magnetic' in content:
            # Correcting magnetic field treatment
            for mechanism in theory.mechanisms:
                if 'magnetic' in mechanism.get('name', '').lower():
                    mechanism['description'] = feedback.content
                    mechanism['confidence'] *= 0.8  # Reduce confidence
                    break

        # Adjust confidence based on correction
        theory.confidence *= 0.9

        # Add to reasoning trace
        theory.reasoning_trace.append(
            f"Human correction: {feedback.content}"
        )

        return theory

    def _apply_suggestion(
        self,
        theory: TheoryFramework,
        feedback: HumanFeedback
    ) -> TheoryFramework:
        """Apply suggestion to theory"""

        # Add as additional mechanism or refinement
        suggestion = {
            'name': f"Human_suggestion_{feedback.id[:8]}",
            'description': feedback.content,
            'confidence': feedback.confidence,
            'source': 'human_expert',
            'evidence_support': []
        }

        theory.mechanisms.append(suggestion)

        # Add to reasoning trace
        theory.reasoning_trace.append(
            f"Human suggestion incorporated: {feedback.content}"
        )

        return theory

    def _add_reference(
        self,
        theory: TheoryFramework,
        feedback: HumanFeedback
    ) -> TheoryFramework:
        """Add reference/knowledge to theory"""

        # Add to evidence base
        reference = {
            'type': 'reference',
            'source': 'human_expert',
            'content': feedback.content,
            'confidence': feedback.confidence
        }

        theory.evidence_base.append(reference)

        # Add to reasoning trace
        theory.reasoning_trace.append(
            f"Expert reference: {feedback.content}"
        )

        return theory

    def _redirect_theory(
        self,
        theory: TheoryFramework,
        feedback: HumanFeedback
    ) -> TheoryFramework:
        """Redirect theory focus based on feedback"""

        # Update focus area
        theory.metadata['focus_redirect'] = feedback.content

        # Add to reasoning trace
        theory.reasoning_trace.append(
            f"Redirected focus: {feedback.content}"
        )

        return theory

    def generate_human_readable_explanation(
        self,
        theory: TheoryFramework,
        detail_level: str = "medium"  # 'brief', 'medium', 'detailed'
    ) -> str:
        """
        Generate human-readable explanation of theory.

        Parameters
        ----------
        theory : TheoryFramework
            Theory to explain
        detail_level : str
            Level of detail

        Returns
        -------
        Human-readable explanation
        """

        if detail_level == 'brief':
            return self._brief_explanation(theory)
        elif detail_level == 'detailed':
            return self._detailed_explanation(theory)
        else:  # medium
            return self._medium_explanation(theory)

    def _brief_explanation(self, theory: TheoryFramework) -> str:
        """Generate brief explanation"""
        return f"""
Theory: {theory.name}

Summary: {theory.summary}

Key Mechanism: {theory.mechanisms[0]['description'] if theory.mechanisms else 'None'}

Confidence: {theory.confidence:.0%}
""".strip()

    def _medium_explanation(self, theory: TheoryFramework) -> str:
        """Generate medium-length explanation"""
        mechanisms_text = "\n".join(
            f"  - {m['name']}: {m['description']}"
            for m in theory.mechanisms[:3]
        )

        return f"""
Theory: {theory.name}
{'=' * 60}

Summary
-------
{theory.summary}

Key Mechanisms
--------------
{mechanisms_text}

Predictions
-----------
{len(theory.testable_predictions)} testable predictions generated.

Validation
----------
Confidence: {theory.confidence:.0%}
Evidence sources: {len(theory.evidence_base)}
""".strip()

    def _detailed_explanation(self, theory: TheoryFramework) -> str:
        """Generate detailed explanation"""
        return f"""
Theory: {theory.name}
{'=' * 80}

Executive Summary
-----------------
{theory.summary}

Detailed Mechanisms
-------------------
""".strip()

    def request_human_input(
        self,
        prompt: str,
        input_type: str = "text",  # 'text', 'choice', 'confirmation'
        choices: Optional[List[str]] = None
    ) -> str:
        """
        Request input from human expert.

        Parameters
        ----------
        prompt : str
            Prompt to display
        input_type : str
            Type of input expected
        choices : list, optional
            Choices for multiple choice

        Returns
        -------
        Human response
        """
        print(f"\n{'='*60}")
        print(f"HITLI: Input Required")
        print(f"{'='*60}")
        print(f"\n{prompt}\n")

        if input_type == 'choice' and choices:
            for i, choice in enumerate(choices, 1):
                print(f"  {i}. {choice}")
            print()

        # This would block for actual input
        # For now, return a placeholder
        response = "continue"

        return response

    def save_session(
        self,
        session_id: str,
        output_dir: str = "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/data/v100_sessions"
    ) -> str:
        """Save collaboration session to disk"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        output_path = Path(output_dir) / f"{session_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize session
        session_data = {
            'session_id': session.session_id,
            'problem_name': session.problem_name,
            'mode': session.mode.value,
            'human_experts': session.human_experts,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'theories_generated': session.theories_generated,
            'feedback': [
                {
                    'id': fb.id,
                    'type': fb.feedback_type.value,
                    'content': fb.content,
                    'target': fb.target_type,
                    'incorporated': fb.incorporated,
                }
                for fb in session.feedback_received
            ],
            'human_contributions': session.human_contributions,
        }

        output_path.write_text(json.dumps(session_data, indent=2))

        print(f"  Session saved to: {output_path}")
        return str(output_path)

    def load_expert_knowledge(
        self,
        domain: str,
        knowledge_file: str
    ) -> ExpertKnowledge:
        """Load expert knowledge from file"""
        path = Path(knowledge_file)

        if path.exists():
            data = json.loads(path.read_text())
            knowledge = ExpertKnowledge(**data)
            self.expert_knowledge[domain] = knowledge
            print(f"  Loaded expert knowledge for {domain}")
            return knowledge
        else:
            # Create default knowledge
            knowledge = ExpertKnowledge(
                domain=domain,
                facts=[],
                constraints=[],
                references=[],
                heuristics=[]
            )
            self.expert_knowledge[domain] = knowledge
            return knowledge


# =============================================================================
# Factory Functions
# =============================================================================

def create_human_interface(
    mode: InteractionMode = InteractionMode.COLLABORATIVE
) -> HumanInterfaceManager:
    """Create a human interface manager"""
    return HumanInterfaceManager(mode=mode)


# =============================================================================
# Convenience Functions
# =============================================================================

def collaborate_with_human(
    problem_name: str,
    experts: List[str],
    theory: TheoryFramework
) -> Tuple[TheoryFramework, CollaborationSession]:
    """
    Convenience function for human-AI collaboration.

    Parameters
    ----------
    problem_name : str
        Name of scientific problem
    experts : list
        List of expert IDs
    theory : TheoryFramework
        Initial theory to refine

    Returns
    -------
    Tuple of (refined_theory, session)
    """
    interface = create_human_interface()
    session = interface.create_session(problem_name, experts)

    # Request feedback
    explanation = interface.generate_human_readable_explanation(theory)
    interface.request_human_input(
        f"Review this theory and provide feedback:\n\n{explanation}",
        input_type="text"
    )

    return theory, session


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'InteractionMode',
    'FeedbackType',
    'FeedbackChannel',
    'HumanFeedback',
    'CollaborationSession',
    'ExpertKnowledge',
    'HumanInterfaceManager',
    'create_human_interface',
    'collaborate_with_human',
]
