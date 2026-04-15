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
Spec-Driven Development Module
===============================

Implements GSD's requirements extraction through iterative questioning.

This module extracts complete project specifications by asking targeted
questions until all requirements are captured, similar to `/gsd:new-project`.

Based on: https://github.com/glittercowboy/get-shit-done
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import re


class RequirementCategory(Enum):
    """Categories of requirements to extract."""
    # Core requirements
    GOALS = "goals"                      # What are we trying to achieve?
    CONSTRAINTS = "constraints"          # What are the limitations?
    TECH_PREFERENCES = "tech_preferences" # What technologies to use?
    EDGE_CASES = "edge_cases"            # What edge cases to consider?

    # Project specifics
    FEATURES = "features"                # What features are needed?
    UI_UX = "ui_ux"                      # UI/UX requirements
    PERFORMANCE = "performance"          # Performance requirements
    SECURITY = "security"                # Security requirements
    TESTING = "testing"                  # Testing requirements

    # Domain specifics
    DOMAIN_KNOWLEDGE = "domain_knowledge" # Domain-specific information
    INTEGRATIONS = "integrations"        # External integrations needed
    DATA_SOURCES = "data_sources"        # Data sources and formats
    DEPLOYMENT = "deployment"            # Deployment requirements

    # Astronomy-specific (for STAN_IX_ASTRO)
    ASTRONOMY_DATA = "astronomy_data"    # Astronomical data sources
    INSTRUMENTS = "instruments"          # Instruments/telescopes
    ANALYSIS_METHODS = "analysis_methods" # Analysis methods

    # Trading-specific (for STAN_IX_TRADING)
    MARKETS = "markets"                  # Markets to trade
    RISK_LIMITS = "risk_limits"          # Risk constraints
    EXECUTION = "execution"              # Execution requirements


@dataclass
class Requirement:
    """A single requirement with metadata."""
    category: RequirementCategory
    question: str
    answer: str = ""
    required: bool = True
    verified: bool = False
    follow_up_questions: List[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Check if requirement has been answered."""
        return bool(self.answer.strip()) if self.required else True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "question": self.question,
            "answer": self.answer,
            "required": self.required,
            "verified": self.verified,
            "follow_up_questions": self.follow_up_questions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Requirement':
        """Create from dictionary."""
        return cls(
            category=RequirementCategory(data["category"]),
            question=data["question"],
            answer=data.get("answer", ""),
            required=data.get("required", True),
            verified=data.get("verified", False),
            follow_up_questions=data.get("follow_up_questions", [])
        )


@dataclass
class ProjectSpec:
    """
    Complete project specification.

    Contains all requirements extracted through questioning.
    """

    name: str = ""
    description: str = ""
    requirements: List[Requirement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())

    def add_requirement(self, requirement: Requirement) -> None:
        """Add a requirement to the spec."""
        # Check for duplicates
        for req in self.requirements:
            if req.category == requirement.category and req.question == requirement.question:
                # Update existing
                req.answer = requirement.answer
                req.verified = requirement.verified
                return

        self.requirements.append(requirement)
        self.updated_at = __import__('datetime').datetime.utcnow().isoformat()

    def get_requirements_by_category(
        self,
        category: RequirementCategory
    ) -> List[Requirement]:
        """Get all requirements in a category."""
        return [r for r in self.requirements if r.category == category]

    def get_unanswered_requirements(self) -> List[Requirement]:
        """Get all required but unanswered requirements."""
        return [r for r in self.requirements if r.required and not r.is_complete()]

    def is_complete(self) -> bool:
        """Check if all required requirements are answered."""
        return len(self.get_unanswered_requirements()) == 0

    def get_completion_percentage(self) -> float:
        """Get percentage of completion (0-100)."""
        if not self.requirements:
            return 0.0

        total_required = sum(1 for r in self.requirements if r.required)
        answered_required = sum(1 for r in self.requirements if r.required and r.is_complete())

        if total_required == 0:
            return 100.0

        return (answered_required / total_required) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "requirements": [r.to_dict() for r in self.requirements],
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def to_project_md(self) -> str:
        """Generate PROJECT.md content."""
        lines = [
            f"# {self.name or 'Project'}",
            "",
            f"{self.description}",
            "",
            "## Requirements",
            ""
        ]

        # Group by category
        categories = {}
        for req in self.requirements:
            if req.category not in categories:
                categories[req.category] = []
            categories[req.category].append(req)

        for category, reqs in categories.items():
            lines.append(f"### {category.value.replace('_', ' ').title()}")
            lines.append("")
            for req in reqs:
                lines.append(f"**{req.question}**")
                lines.append(f"{req.answer}")
                lines.append("")

        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSpec':
        """Create from dictionary."""
        spec = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

        for req_data in data.get("requirements", []):
            spec.requirements.append(Requirement.from_dict(req_data))

        return spec

    def save(self, filepath: str) -> None:
        """Save spec to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'ProjectSpec':
        """Load spec from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class QuestionGenerator:
    """
    Generate questions for requirements extraction.

    Provides domain-specific question templates for different
    requirement categories and project types.
    """

    # Base question templates
    BASE_QUESTIONS = {
        RequirementCategory.GOALS: [
            "What is the primary goal of this project?",
            "What problem does this project solve?",
            "What defines success for this project?"
        ],
        RequirementCategory.CONSTRAINTS: [
            "Are there any time constraints or deadlines?",
            "What are the budget constraints?",
            "Are there any technical limitations or constraints?"
        ],
        RequirementCategory.TECH_PREFERENCES: [
            "What programming languages should be used?",
            "Are there any specific frameworks or libraries to use?",
            "Are there any technologies to explicitly avoid?"
        ],
        RequirementCategory.EDGE_CASES: [
            "What edge cases should be considered?",
            "What error conditions need to be handled?",
            "Are there any special conditions or scenarios?"
        ],
        RequirementCategory.FEATURES: [
            "What are the must-have features?",
            "What are the nice-to-have features?",
            "What features should be planned for future versions?"
        ],
        RequirementCategory.TESTING: [
            "What testing approach should be used?",
            "Are there specific testing requirements?",
            "What should be the test coverage target?"
        ],
    }

    # Astronomy-specific questions
    ASTRONOMY_QUESTIONS = {
        RequirementCategory.ASTRONOMY_DATA: [
            "What astronomical data sources will be used? (e.g., surveys, catalogs)",
            "What wavelength ranges are of interest? (radio, optical, X-ray, etc.)",
            "Are there specific telescopes or instruments to target?"
        ],
        RequirementCategory.INSTRUMENTS: [
            "Which ground-based or space-based instruments are relevant?",
            "What are the resolution/sensitivity requirements?",
            "Are there observation planning constraints?"
        ],
        RequirementCategory.ANALYSIS_METHODS: [
            "What analysis methods are needed? (photometry, spectroscopy, etc.)",
            "Are there specific scientific questions to address?",
            "What statistical methods should be applied?"
        ],
    }

    # Trading-specific questions
    TRADING_QUESTIONS = {
        RequirementCategory.MARKETS: [
            "Which markets will be traded? (crypto, forex, equities)",
            "Which exchanges or venues?",
            "What instruments/symbols? (futures, spot, options)"
        ],
        RequirementCategory.RISK_LIMITS: [
            "What are the position size limits?",
            "What is the maximum drawdown tolerance?",
            "Are there leverage constraints?"
        ],
        RequirementCategory.EXECUTION: [
            "What execution style? (market, limit, IOC)",
            "What are the latency requirements?",
            "How should slippage be handled?"
        ],
    }

    @classmethod
    def get_questions(
        cls,
        category: RequirementCategory,
        project_type: str = "general"
    ) -> List[str]:
        """
        Get questions for a category.

        Args:
            category: Requirement category
            project_type: Project type (general, astronomy, trading)

        Returns:
            List of questions
        """
        if project_type == "astronomy" and category in cls.ASTRONOMY_QUESTIONS:
            return cls.ASTRONOMY_QUESTIONS[category]
        elif project_type == "trading" and category in cls.TRADING_QUESTIONS:
            return cls.TRADING_QUESTIONS[category]
        elif category in cls.BASE_QUESTIONS:
            return cls.BASE_QUESTIONS[category]
        else:
            return [f"What are the requirements for {category.value}?"]

    @classmethod
    def get_all_questions(cls, project_type: str = "general") -> Dict[RequirementCategory, List[str]]:
        """Get all questions for a project type."""
        questions = {}

        for category in RequirementCategory:
            qs = cls.get_questions(category, project_type)
            if qs:
                questions[category] = qs

        return questions


class RequirementsExtractor:
    """
    Extract requirements through iterative questioning.

    This class implements GSD's `/gsd:new-project` functionality,
    asking questions until all requirements are captured.
    """

    def __init__(
        self,
        project_type: str = "general",
        ask_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize requirements extractor.

        Args:
            project_type: Type of project (general, astronomy, trading)
            ask_callback: Function to ask user questions (returns answer)
        """
        self.project_type = project_type
        self.ask_callback = ask_callback
        self.question_generator = QuestionGenerator()

    def extract_requirements(
        self,
        user_idea: str,
        max_questions: int = 20
    ) -> ProjectSpec:
        """
        Extract requirements from user idea through questioning.

        Args:
            user_idea: Initial user idea/description
            max_questions: Maximum number of questions to ask

        Returns:
            Complete ProjectSpec
        """
        spec = ProjectSpec(description=user_idea)

        # Generate all questions
        all_questions = self.question_generator.get_all_questions(self.project_type)

        # Ask questions until complete or max reached
        questions_asked = 0

        for category, questions in all_questions.items():
            for question in questions:
                if questions_asked >= max_questions:
                    break

                # Ask the question
                if self.ask_callback:
                    answer = self.ask_callback(question)
                else:
                    # In a real implementation, this would use AskUserQuestion tool
                    answer = input(f"\n{question}\n> ")

                # Create requirement
                requirement = Requirement(
                    category=category,
                    question=question,
                    answer=answer,
                    required=True
                )

                spec.add_requirement(requirement)
                questions_asked += 1

                # Generate follow-up if needed
                follow_ups = self._generate_follow_ups(question, answer)
                for fu in follow_ups[:2]:  # Max 2 follow-ups
                    if questions_asked >= max_questions:
                        break

                    if self.ask_callback:
                        fu_answer = self.ask_callback(fu)
                    else:
                        fu_answer = input(f"\n{fu}\n> ")

                    requirement.follow_up_questions.append(fu)
                    questions_asked += 1

        # Extract project name from description
        spec.name = self._extract_name(user_idea)

        return spec

    def _generate_follow_ups(self, question: str, answer: str) -> List[str]:
        """Generate follow-up questions based on answer."""
        follow_ups = []

        # Look for keywords that suggest follow-ups
        answer_lower = answer.lower()

        if "api" in answer_lower:
            follow_ups.append("Which API endpoints or services will be integrated?")

        if "database" in answer_lower or "data" in answer_lower:
            follow_ups.append("What is the data schema or format?")

        if "security" in answer_lower or "authentication" in answer_lower:
            follow_ups.append("What authentication method should be used?")

        if "performance" in answer_lower or "fast" in answer_lower:
            follow_ups.append("What are the specific performance targets?")

        return follow_ups

    def _extract_name(self, description: str) -> str:
        """Extract potential project name from description."""
        # Look for patterns like "Create X", "Build Y", "Implement Z"
        patterns = [
            r"(?:create|build|implement|develop|make)\s+(?:a\s+)?([a-z][a-z0-9\s]+?)(?:\s+(?:system|application|tool|platform))?",
            r"^(.{3,40?})",
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Capitalize and clean
                name = ' '.join(word.capitalize() for word in name.split())
                return name[:50]  # Max 50 chars

        return "Untitled Project"


class RequirementsValidator:
    """Validate extracted requirements."""

    @staticmethod
    def validate(spec: ProjectSpec) -> tuple[bool, List[str]]:
        """
        Validate a project specification.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for empty spec
        if not spec.requirements:
            issues.append("No requirements defined")
            return False, issues

        # Check for missing required answers
        unanswered = spec.get_unanswered_requirements()
        if unanswered:
            issues.append(f"Missing answers for {len(unanswered)} required questions")

        # Check for contradictions
        answers = {r.category: r.answer for r in spec.requirements if r.answer}
        for cat1, ans1 in answers.items():
            for cat2, ans2 in answers.items():
                if cat1 != cat2 and RequirementsValidator._contradictory(ans1, ans2):
                    issues.append(f"Potential contradiction between {cat1.value} and {cat2.value}")

        return len(issues) == 0, issues

    @staticmethod
    def _contradictory(ans1: str, ans2: str) -> bool:
        """Check if two answers contradict each other."""
        # Simple heuristic: check for opposite keywords
        contradictions = [
            ("fast", "slow"),
            ("real-time", "batch"),
            ("simple", "complex"),
            ("small", "large"),
            ("immediate", "delayed"),
        ]

        ans1_lower = ans1.lower()
        ans2_lower = ans2.lower()

        for pos, neg in contradictions:
            if pos in ans1_lower and neg in ans2_lower:
                return True
            if neg in ans1_lower and pos in ans2_lower:
                return True

        return False


# =============================================================================
# Factory Functions
# =============================================================================

def extract_requirements(
    user_idea: str,
    project_type: str = "general",
    ask_callback: Callable[[str], str] = None
) -> ProjectSpec:
    """
    Extract requirements from user idea.

    Args:
        user_idea: Initial user idea/description
        project_type: Type of project (general, astronomy, trading)
        ask_callback: Function to ask user questions

    Returns:
        Complete ProjectSpec
    """
    extractor = RequirementsExtractor(project_type, ask_callback)
    return extractor.extract_requirements(user_idea)


def validate_spec(spec: ProjectSpec) -> tuple[bool, List[str]]:
    """Validate a project specification."""
    return RequirementsValidator.validate(spec)


__all__ = [
    'RequirementCategory',
    'Requirement',
    'ProjectSpec',
    'QuestionGenerator',
    'RequirementsExtractor',
    'RequirementsValidator',
    'extract_requirements',
    'validate_spec',
]
