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
ASTRA V9.0 — Autonomous Scientific Agenda
Enables ASTRA to set its own research goals through curiosity metrics.
"""

import time
import uuid
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

from ..knowledge_graph import DynamicKnowledgeGraph
from ..graphpalace_memory import GraphPalaceMemory as DiscoveryMemory


class CuriosityMetric(Enum):
    """Types of curiosity metrics for goal evaluation."""
    INFORMATION_GAP = "information_gap"
    NOVELTY_POTENTIAL = "novelty_potential"
    FEASIBILITY_BALANCE = "feasibility_balance"
    SCIENTIFIC_IMPORTANCE = "scientific_importance"
    COLLABORATIVE_OPPORTUNITY = "collaborative_opportunity"
    RESOURCE_EFFICIENCY = "resource_efficiency"


class GoalStatus(Enum):
    """Status of research goals."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class GoalPriority(Enum):
    """Priority levels for goals."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ResearchGoal:
    """A research goal in ASTRA's scientific agenda."""
    id: str
    title: str
    description: str
    domain: str
    curiosity_score: float
    importance_score: float
    feasibility_score: float
    overall_priority: float
    status: GoalStatus
    priority: GoalPriority
    estimated_duration_hours: float
    required_resources: List[str]
    success_criteria: List[str]
    related_hypotheses: List[str]
    sub_goals: List[str]
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    approved_by: Optional[str] = None  # "human" or "autonomous"
    completion_date: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "curiosity_score": self.curiosity_score,
            "importance_score": self.importance_score,
            "feasibility_score": self.feasibility_score,
            "overall_priority": self.overall_priority,
            "status": self.status.value,
            "priority": self.priority.value,
            "estimated_duration_hours": self.estimated_duration_hours,
            "required_resources": self.required_resources,
            "success_criteria": self.success_criteria,
            "related_hypotheses": self.related_hypotheses,
            "sub_goals": self.sub_goals,
            "progress": self.progress,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_by": self.approved_by,
            "completion_date": self.completion_date
        }


@dataclass
class CuriosityAssessment:
    """Assessment of a knowledge gap's curiosity value."""
    gap_id: str
    description: str
    domain: str
    information_gap_score: float
    novelty_potential_score: float
    scientific_importance_score: float
    feasibility_score: float
    required_resources: List[str]
    estimated_duration_hours: float
    related_entities: List[str]
    timestamp: float = field(default_factory=time.time)


class CuriosityEngine:
    """
    Computes information-theoretic curiosity metrics for research questions.

    Combines multiple metrics to identify the most promising research directions.
    """

    def __init__(self, knowledge_graph: Optional[DynamicKnowledgeGraph] = None,
                 discovery_memory: Optional[DiscoveryMemory] = None):
        self.knowledge_graph = knowledge_graph
        self.discovery_memory = discovery_memory

        # Metric weights (sum to 1.0)
        self.metric_weights = {
            CuriosityMetric.INFORMATION_GAP: 0.25,
            CuriosityMetric.NOVELTY_POTENTIAL: 0.25,
            CuriosityMetric.SCIENTIFIC_IMPORTANCE: 0.25,
            CuriosityMetric.FEASIBILITY_BALANCE: 0.15,
            CuriosityMetric.COLLABORATIVE_OPPORTUNITY: 0.10
        }

        self.assessment_history: List[CuriosityAssessment] = []

    def compute_curiosity(self, question: str, domain: str,
                         context: Optional[Dict[str, Any]] = None) -> CuriosityAssessment:
        """Compute curiosity score for a research question."""
        context = context or {}

        # Extract key concepts
        concepts = self._extract_concepts(question)

        # Compute individual metrics
        info_gap = self._compute_information_gap(question, domain, concepts, context)
        novelty = self._compute_novelty_potential(question, domain, concepts, context)
        importance = self._compute_scientific_importance(question, domain, context)
        feasibility = self._compute_feasibility(question, domain, concepts, context)

        # Estimate resources and duration
        resources = self._estimate_required_resources(question, domain)
        duration = self._estimate_duration(question, domain, resources)

        assessment = CuriosityAssessment(
            gap_id=f"gap_{uuid.uuid4().hex[:8]}",
            description=question,
            domain=domain,
            information_gap_score=info_gap,
            novelty_potential_score=novelty,
            scientific_importance_score=importance,
            feasibility_score=feasibility,
            required_resources=resources,
            estimated_duration_hours=duration,
            related_entities=concepts
        )

        self.assessment_history.append(assessment)

        return assessment

    def _extract_concepts(self, question: str) -> List[str]:
        """Extract key scientific concepts from question."""
        # Simple extraction based on common astrophysical terms
        concept_keywords = {
            "black_hole": ["black hole", "black-hole", "singularity"],
            "dark_matter": ["dark matter", "dark-matter", "detection"],
            "dark_energy": ["dark energy", "cosmological constant", "acceleration"],
            "galaxy": ["galaxy", "galactic", "morphology", "evolution"],
            "star": ["star", "stellar", "formation", "evolution"],
            "exoplanet": ["exoplanet", "planet", "transit", "radial velocity"],
            "cosmology": ["cosmology", "universe", "expansion", "inflation"],
            "filament": ["filament", "ism", "molecular cloud", "turbulence"]
        }

        concepts = []
        question_lower = question.lower()

        for concept, keywords in concept_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                concepts.append(concept)

        return concepts

    def _compute_information_gap(self, question: str, domain: str,
                                concepts: List[str], context: Dict) -> float:
        """Compute information gap score (0-1)."""
        # Check knowledge graph for related entities
        gap_score = 0.5  # Default

        if self.knowledge_graph:
            # Check if concepts exist in knowledge graph
            known_concepts = 0
            for concept in concepts:
                entities = self.knowledge_graph.get_entities_by_name(concept)
                if entities:
                    known_concepts += 1

            # Information gap higher for unknown concepts
            if concepts:
                gap_score = 1.0 - (known_concepts / len(concepts))
            else:
                gap_score = 0.5

        # Adjust by domain activity
        domain_activity = context.get("domain_activity", {}).get(domain, 0.5)
        gap_score = gap_score * (1.0 - domain_activity * 0.3)

        return max(0.0, min(1.0, gap_score))

    def _compute_novelty_potential(self, question: str, domain: str,
                                  concepts: List[str], context: Dict) -> float:
        """Compute novelty potential score (0-1)."""
        novelty_score = 0.5

        # Check if similar research exists in discovery memory
        if self.discovery_memory:
            # Look for similar findings
            discoveries = self.discovery_memory.get_strong_discoveries(
                min_strength=0.3,
                max_age_cycles=100,
                current_cycle=context.get("current_cycle", 0)
            )

            # Check for overlap with question concepts
            overlap = 0
            for disc in discoveries:
                for concept in concepts:
                    if concept.lower() in disc.description.lower():
                        overlap += 1

            if discoveries:
                novelty_score = 1.0 - (overlap / len(discoveries))
            else:
                novelty_score = 0.8  # No similar discoveries = potentially novel

        # Boost novelty for cross-domain questions
        related_domains = context.get("related_domains", [])
        if len(related_domains) > 1:
            novelty_score = min(1.0, novelty_score * 1.2)

        return max(0.0, min(1.0, novelty_score))

    def _compute_scientific_importance(self, question: str, domain: str,
                                     context: Dict) -> float:
        """Compute scientific importance score (0-1)."""
        importance_keywords = {
            "fundamental": ["fundamental", "basic", "first principles", "foundation"],
            "paradigm": ["paradigm", "revolutionary", "breakthrough", "transformative"],
            "unsolved": ["unsolved", "open problem", "mystery", "puzzle"],
            "unification": ["unify", "unification", "unified theory", "combine"],
            "constraint": ["constrain", "measurement", "observation", "test"]
        }

        question_lower = question.lower()
        score = 0.0

        for category, keywords in importance_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                score += 0.2

        # Domain-specific importance
        domain_importance = {
            "cosmology": 0.9,
            "fundamental_physics": 0.95,
            "dark_matter": 0.9,
            "dark_energy": 0.9,
            "black_hole": 0.85,
            "early_universe": 0.85
        }

        domain = context.get("domain", domain)
        score = score * 0.7 + domain_importance.get(domain, 0.5) * 0.3

        return max(0.0, min(1.0, score))

    def _compute_feasibility(self, question: str, domain: str,
                           concepts: List[str], context: Dict) -> float:
        """Compute feasibility score (0-1)."""
        feasibility_score = 0.5

        # Check data availability
        data_sources = context.get("available_data", [])
        if data_sources:
            feasibility_score = 0.7
        else:
            feasibility_score = 0.3

        # Check for theoretical testability
        theoretical_keywords = ["test", "measure", "observe", "detect", "constrain"]
        if any(keyword in question.lower() for keyword in theoretical_keywords):
            feasibility_score = min(1.0, feasibility_score + 0.2)

        # Check computational feasibility
        computational_keywords = ["simulation", "model", "calculate", "compute"]
        if any(keyword in question.lower() for keyword in computational_keywords):
            feasibility_score = min(1.0, feasibility_score + 0.1)

        return max(0.0, min(1.0, feasibility_score))

    def _estimate_required_resources(self, question: str, domain: str) -> List[str]:
        """Estimate required resources for pursuing question."""
        resources = []

        # Data resources
        if "observ" in question.lower() or "measure" in question.lower():
            resources.append("observational_data")

        if "simulation" in question.lower() or "model" in question.lower():
            resources.append("computational_resources")

        if "theory" in question.lower() or "theoretical" in question.lower():
            resources.append("theoretical_analysis")

        # Domain-specific resources
        domain_resources = {
            "cosmology": ["cosmological_data", "cmb_observations"],
            "exoplanets": ["transit_photometry", "radial_velocity"],
            "galaxies": ["galaxy_surveys", "spectroscopic_data"],
            "black_hole": ["gravitational_waves", "xray_observations"]
        }

        if domain.lower() in domain_resources:
            resources.extend(domain_resources[domain.lower()])

        return list(set(resources))

    def _estimate_duration(self, question: str, domain: str,
                          resources: List[str]) -> float:
        """Estimate duration in hours."""
        base_duration = 40.0  # hours

        # Adjust by complexity
        complexity_indicators = ["multi-wavelength", "cross-domain", "unification"]
        for indicator in complexity_indicators:
            if indicator.lower() in question.lower():
                base_duration *= 1.5

        # Adjust by resources
        if len(resources) > 3:
            base_duration *= 1.3

        return base_duration


class GoalGenerator:
    """
    Generates research goals based on curiosity assessments and knowledge gaps.

    Creates both short-term tactical goals and long-term strategic objectives.
    """

    def __init__(self, curiosity_engine: CuriosityEngine):
        self.curiosity_engine = curiosity_engine
        self.generated_goals: List[ResearchGoal] = []
        self.goal_history: List[ResearchGoal] = []

    def generate_goals(self, knowledge_gaps: List[Dict[str, Any]],
                      max_goals: int = 5,
                      time_horizon: str = "medium") -> List[ResearchGoal]:
        """Generate research goals from knowledge gaps."""
        goals = []

        # Assess each knowledge gap
        assessments = []
        for gap in knowledge_gaps:
            description = gap.get("description", "")
            domain = gap.get("domain", "astrophysics")

            assessment = self.curiosity_engine.compute_curiosity(
                description, domain, gap
            )
            assessments.append(assessment)

        # Sort by curiosity score
        assessments.sort(key=lambda a: (
            a.information_gap_score +
            a.novelty_potential_score +
            a.scientific_importance_score
        ), reverse=True)

        # Generate goals from top assessments
        for assessment in assessments[:max_goals]:
            goal = self._create_goal_from_assessment(assessment, time_horizon)
            goals.append(goal)

        self.generated_goals.extend(goals)
        return goals

    def _create_goal_from_assessment(self, assessment: CuriosityAssessment,
                                    time_horizon: str) -> ResearchGoal:
        """Create research goal from curiosity assessment."""
        # Calculate overall priority
        curiosity_score = (
            assessment.information_gap_score * 0.3 +
            assessment.novelty_potential_score * 0.3 +
            assessment.scientific_importance_score * 0.2 +
            assessment.feasibility_score * 0.2
        )

        # Determine priority level
        if curiosity_score > 0.8:
            priority = GoalPriority.CRITICAL
        elif curiosity_score > 0.6:
            priority = GoalPriority.HIGH
        elif curiosity_score > 0.4:
            priority = GoalPriority.MEDIUM
        else:
            priority = GoalPriority.LOW

        # Generate success criteria
        success_criteria = self._generate_success_criteria(assessment)

        # Determine status based on curiosity score
        if curiosity_score > 0.7:
            status = GoalStatus.PROPOSED
        else:
            status = GoalStatus.PROPOSED  # All start as proposed

        return ResearchGoal(
            id=f"goal_{uuid.uuid4().hex[:8]}",
            title=assessment.description[:80] + ("..." if len(assessment.description) > 80 else ""),
            description=assessment.description,
            domain=assessment.domain,
            curiosity_score=curiosity_score,
            importance_score=assessment.scientific_importance_score,
            feasibility_score=assessment.feasibility_score,
            overall_priority=curiosity_score,
            status=status,
            priority=priority,
            estimated_duration_hours=assessment.estimated_duration_hours,
            required_resources=assessment.required_resources,
            success_criteria=success_criteria,
            related_hypotheses=[],
            sub_goals=[],
            approved_by=None  # Requires human or autonomous approval
        )

    def _generate_success_criteria(self, assessment: CuriosityAssessment) -> List[str]:
        """Generate success criteria for a goal."""
        criteria = []

        # General criteria
        criteria.append("Generate testable predictions")
        criteria.append("Validate against observational data")
        criteria.append("Document findings in knowledge graph")

        # Domain-specific criteria
        domain = assessment.domain.lower()

        if "cosmology" in domain or "universe" in domain:
            criteria.append("Constrain cosmological parameters")
            criteria.append("Compare with ΛCDM predictions")

        elif "exoplanet" in domain or "planet" in domain:
            criteria.append("Detect or characterize planetary systems")
            criteria.append("Measure physical parameters")

        elif "galaxy" in domain:
            criteria.append("Identify scaling relations")
            criteria.append("Classify by morphology/properties")

        return criteria[:5]  # Max 5 criteria

    def update_goal_progress(self, goal_id: str, progress: float,
                            status: Optional[GoalStatus] = None) -> bool:
        """Update progress on a goal."""
        for goal in self.generated_goals:
            if goal.id == goal_id:
                goal.progress = max(0.0, min(1.0, progress))
                goal.updated_at = time.time()

                if status:
                    goal.status = status

                if progress >= 1.0 and status != GoalStatus.COMPLETED:
                    goal.status = GoalStatus.COMPLETED
                    goal.completion_date = time.time()

                return True

        return False

    def get_pending_goals(self) -> List[ResearchGoal]:
        """Get goals that are proposed or approved but not completed."""
        return [g for g in self.generated_goals
                if g.status in [GoalStatus.PROPOSED, GoalStatus.APPROVED, GoalStatus.IN_PROGRESS]]

    def get_goal_summary(self) -> Dict[str, Any]:
        """Get summary of all goals."""
        total = len(self.generated_goals)

        if total == 0:
            return {"total_goals": 0}

        by_status = {}
        by_priority = {}

        for goal in self.generated_goals:
            status = goal.status.value
            by_status[status] = by_status.get(status, 0) + 1

            priority = goal.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return {
            "total_goals": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "avg_curiosity_score": np.mean([g.curiosity_score for g in self.generated_goals]),
            "total_estimated_hours": sum(g.estimated_duration_hours for g in self.generated_goals)
        }


class ApprovalWorkflow:
    """
    Manages human approval workflow for autonomous agenda setting.

    In semi-autonomous mode, ASTRA proposes goals but requires human approval.
    """

    def __init__(self):
        self.pending_approvals: Dict[str, ResearchGoal] = {}
        self.approval_history: List[Dict[str, Any]] = []
        self.human_notification_callback: Optional[Callable] = None

    def submit_for_approval(self, goal: ResearchGoal) -> str:
        """Submit a goal for human approval."""
        submission_id = f"submission_{uuid.uuid4().hex[:8]}"
        self.pending_approvals[submission_id] = goal

        # Notify human if callback registered
        if self.human_notification_callback:
            try:
                self.human_notification_callback(goal)
            except Exception as e:
                print(f"Notification callback failed: {e}")

        return submission_id

    def process_approval(self, submission_id: str, approved: bool,
                         approver: str = "human",
                         feedback: Optional[str] = None) -> bool:
        """Process human approval decision."""
        if submission_id not in self.pending_approvals:
            return False

        goal = self.pending_approvals[submission_id]

        if approved:
            goal.status = GoalStatus.APPROVED
            goal.approved_by = approver
        else:
            goal.status = GoalStatus.CANCELLED

        # Record in history
        self.approval_history.append({
            "submission_id": submission_id,
            "goal_id": goal.id,
            "approved": approved,
            "approver": approver,
            "feedback": feedback,
            "timestamp": time.time()
        })

        # Remove from pending
        del self.pending_approvals[submission_id]

        return True

    def get_pending_approval_count(self) -> int:
        """Get number of goals awaiting approval."""
        return len(self.pending_approvals)

    def get_approval_summary(self) -> Dict[str, Any]:
        """Get summary of approval workflow."""
        total = len(self.approval_history)

        if total == 0:
            return {"total_approvals": 0}

        approved = sum(1 for h in self.approval_history if h["approved"])

        return {
            "total_approvals": total,
            "approved": approved,
            "rejected": total - approved,
            "approval_rate": approved / total if total > 0 else 0,
            "pending": len(self.pending_approvals)
        }


class AutonomousAgenda:
    """
    Main system for autonomous scientific agenda setting.

    Integrates curiosity assessment, goal generation, and approval workflow.
    """

    def __init__(self, knowledge_graph: Optional[DynamicKnowledgeGraph] = None,
                 discovery_memory: Optional[DiscoveryMemory] = None,
                 mode: str = "semi_autonomous"):
        self.knowledge_graph = knowledge_graph
        self.discovery_memory = discovery_memory

        self.curiosity_engine = CuriosityEngine(knowledge_graph, discovery_memory)
        self.goal_generator = GoalGenerator(self.curiosity_engine)
        self.approval_workflow = ApprovalWorkflow()

        self.mode = mode  # "autonomous", "semi_autonomous", "human_guided"
        self.current_goals: List[ResearchGoal] = []

    def generate_research_agenda(self, num_goals: int = 5,
                                time_horizon: str = "medium") -> List[ResearchGoal]:
        """Generate research agenda based on knowledge gaps."""
        # Identify knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps()

        # Generate goals
        goals = self.goal_generator.generate_goals(
            knowledge_gaps,
            max_goals=num_goals,
            time_horizon=time_horizon
        )

        # Process approvals based on mode
        final_goals = []

        for goal in goals:
            if self.mode == "autonomous":
                # Auto-approve high-priority goals
                if goal.priority in [GoalPriority.CRITICAL, GoalPriority.HIGH]:
                    goal.status = GoalStatus.APPROVED
                    goal.approved_by = "autonomous"
                else:
                    goal.status = GoalStatus.PROPOSED

                final_goals.append(goal)

            elif self.mode == "semi_autonomous":
                # Submit for human approval
                submission_id = self.approval_workflow.submit_for_approval(goal)
                final_goals.append(goal)

            else:  # human_guided
                # Just propose, let human decide
                final_goals.append(goal)

        self.current_goals.extend(final_goals)
        return final_goals

    def _identify_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """Identify knowledge gaps from knowledge graph and discovery memory."""
        gaps = []

        # Get gaps from knowledge graph
        if self.knowledge_graph:
            kg_gaps = self.knowledge_graph.find_knowledge_gaps()
            for kg_gap in kg_gaps[:10]:  # Top 10
                gaps.append({
                    "description": f"Knowledge gap: {kg_gap.description}",
                    "domain": kg_gap.domain if hasattr(kg_gap, 'domain') else "astrophysics",
                    "type": "structural"
                })

        # Get gaps from discovery memory (unexplored variable pairs)
        if self.discovery_memory:
            for source in ["exoplanets", "sdss", "gaia"]:
                untested = self.discovery_memory.get_unexplored_variable_pairs(source)
                if untested:
                    v1, v2 = untested[0]
                    gaps.append({
                        "description": f"Explore {v1}-{v2} relation in {source}",
                        "domain": source,
                        "type": "exploratory"
                    })

        return gaps[:20]  # Max 20 gaps

    def update_agenda(self) -> None:
        """Update research agenda based on progress and new discoveries."""
        # Complete finished goals
        for goal in self.current_goals:
            if goal.status == GoalStatus.IN_PROGRESS:
                # Check if should be completed
                if goal.progress >= 1.0:
                    self.goal_generator.update_goal_progress(
                        goal.id, 1.0, GoalStatus.COMPLETED
                    )

        # Remove completed/cancelled goals from active
        self.current_goals = [
            g for g in self.current_goals
            if g.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED]
        ]

        # Generate new goals if running low
        if len(self.current_goals) < 3:
            new_goals = self.generate_research_agenda(
                num_goals=3,
                time_horizon="medium"
            )

    def get_agenda_summary(self) -> Dict[str, Any]:
        """Get summary of current research agenda."""
        return {
            "mode": self.mode,
            "total_goals": len(self.current_goals),
            "by_status": self._count_goals_by_status(),
            "by_priority": self._count_goals_by_priority(),
            "goal_generator_summary": self.goal_generator.get_goal_summary(),
            "approval_summary": self.approval_workflow.get_approval_summary()
        }

    def _count_goals_by_status(self) -> Dict[str, int]:
        """Count goals by status."""
        counts = {}
        for goal in self.current_goals:
            status = goal.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _count_goals_by_priority(self) -> Dict[str, int]:
        """Count goals by priority."""
        counts = {}
        for goal in self.current_goals:
            priority = goal.priority.value
            counts[priority] = counts.get(priority, 0) + 1
        return counts


# Factory functions
def create_autonomous_agenda(knowledge_graph=None, discovery_memory=None,
                             mode="semi_autonomous") -> AutonomousAgenda:
    """Create autonomous agenda system."""
    return AutonomousAgenda(knowledge_graph, discovery_memory, mode)


def create_curiosity_engine(knowledge_graph=None, discovery_memory=None) -> CuriosityEngine:
    """Create curiosity engine."""
    return CuriosityEngine(knowledge_graph, discovery_memory)
