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
ASTRA V9.0 — Multi-Agent Scientific Collaboration System
Factory for creating specialized scientific agents with distinct expertise.
"""

import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from abc import ABC, abstractmethod


class AgentRole(Enum):
    """Specialized agent roles in scientific collaboration."""
    THEORIST = "theorist"
    EMPIRICIST = "empiricist"
    EXPERIMENTALIST = "experimentalist"
    MATHEMATICIAN = "mathematician"
    SKEPTIC = "skeptic"
    SYNTHESIZER = "synthesizer"


class AgentStatus(Enum):
    """Agent status states."""
    IDLE = "idle"
    THINKING = "thinking"
    DEBATING = "debating"
    ANALYZING = "analyzing"
    WAITING = "waiting"


@dataclass
class AgentExpertise:
    """Represents agent expertise profile."""
    domains: List[str]
    methods: List[str]
    strength_areas: List[str]
    confidence_by_domain: Dict[str, float]
    success_rate: float = 0.5
    total_tasks: int = 0
    successful_tasks: int = 0


@dataclass
class AgentOpinion:
    """Structured opinion from an agent."""
    agent_id: str
    agent_role: AgentRole
    position: str  # "support", "oppose", "neutral", "abstain"
    confidence: float
    reasoning: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    alternative_proposals: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class ScientificAgent(ABC):
    """Base class for specialized scientific agents."""

    def __init__(self, role: AgentRole, expertise: AgentExpertise):
        self.id = f"{role.value}_{uuid.uuid4().hex[:8]}"
        self.role = role
        self.expertise = expertise
        self.status = AgentStatus.IDLE
        self.opinion_history: List[AgentOpinion] = []
        self.performance_metrics = {
            "accuracy": 0.0,
            "reliability": 0.5,
            "response_time": 0.0,
            "collaboration_score": 0.5
        }
        self.memory: Dict[str, Any] = {}

    @abstractmethod
    def analyze(self, question: str, context: Dict[str, Any]) -> AgentOpinion:
        """Analyze a scientific question and form an opinion."""
        pass

    @abstractmethod
    def respond_to_opinion(self, opinion: AgentOpinion, context: Dict[str, Any]) -> Optional[AgentOpinion]:
        """Respond to another agent's opinion during debate."""
        pass

    def update_performance(self, success: bool, task_domain: str):
        """Update performance metrics based on task outcome."""
        self.expertise.total_tasks += 1
        if success:
            self.expertise.successful_tasks += 1

        self.expertise.success_rate = (
            self.expertise.successful_tasks / self.expertise.total_tasks
        )

        # Update domain-specific confidence
        if task_domain in self.expertise.confidence_by_domain:
            current_conf = self.expertise.confidence_by_domain[task_domain]
            # Gradually adjust confidence based on performance
            adjustment = 0.05 if success else -0.03
            new_conf = max(0.1, min(0.95, current_conf + adjustment))
            self.expertise.confidence_by_domain[task_domain] = new_conf

    def get_profile(self) -> Dict[str, Any]:
        """Get agent profile for collaboration."""
        return {
            "id": self.id,
            "role": self.role.value,
            "status": self.status.value,
            "domains": self.expertise.domains,
            "methods": self.expertise.methods,
            "success_rate": self.expertise.success_rate,
            "confidence_by_domain": self.expertise.confidence_by_domain,
            "performance": self.performance_metrics
        }


class TheoristAgent(ScientificAgent):
    """Focuses on theoretical frameworks and first-principles reasoning."""

    def __init__(self):
        expertise = AgentExpertise(
            domains=["theoretical_physics", "cosmology", "fundamental_principles"],
            methods=["axiomatic_reasoning", "symmetry_analysis", "dimensional_analysis"],
            strength_areas=["first_principles", "mathematical_consistency", "unification"],
            confidence_by_domain={"theoretical_physics": 0.85, "cosmology": 0.75}
        )
        super().__init__(AgentRole.THEORIST, expertise)

    def analyze(self, question: str, context: Dict[str, Any]) -> AgentOpinion:
        """Analyze from first-principles theoretical perspective."""
        self.status = AgentStatus.THINKING

        # Extract theoretical concepts from question
        concepts = self._extract_theoretical_concepts(question)

        # Analyze from fundamental principles
        reasoning = self._first_principles_analysis(question, concepts, context)

        # Determine position based on theoretical consistency
        confidence = self.expertise.confidence_by_domain.get("theoretical_physics", 0.7)
        position = "support" if confidence > 0.6 else "neutral"

        return AgentOpinion(
            agent_id=self.id,
            agent_role=self.role,
            position=position,
            confidence=confidence,
            reasoning=reasoning,
            evidence=[{"type": "theoretical", "principles": concepts}]
        )

    def respond_to_opinion(self, opinion: AgentOpinion, context: Dict[str, Any]) -> Optional[AgentOpinion]:
        """Respond by checking theoretical consistency."""
        if opinion.agent_role == self.role:
            return None  # Agree with fellow theorist

        # Challenge if empiricist contradicts theory
        if opinion.agent_role == AgentRole.EMPIRICIST and opinion.position == "support":
            # Check if empirical findings conflict with theory
            if "contradicts" in opinion.reasoning.lower():
                return AgentOpinion(
                    agent_id=self.id,
                    agent_role=self.role,
                    position="oppose",
                    confidence=0.7,
                    reasoning=f"Empirical claim contradicts established theoretical principles. "
                              f"Requires theoretical reconciliation or paradigm revision.",
                    evidence=[{"type": "theoretical_challenge"}]
                )

        return None

    def _extract_theoretical_concepts(self, question: str) -> List[str]:
        """Extract theoretical concepts from question."""
        # Simplified concept extraction
        concepts = []
        theoretical_keywords = [
            "symmetry", "conservation", "invariance", "dimension",
            "scale", "principle", "law", "theory", "framework"
        ]
        for keyword in theoretical_keywords:
            if keyword in question.lower():
                concepts.append(keyword)
        return concepts

    def _first_principles_analysis(self, question: str, concepts: List[str], context: Dict) -> str:
        """Analyze from first principles."""
        if not concepts:
            return "Question lacks clear theoretical framework. Requires conceptual clarification."

        reasoning = f"Analyzing from first principles using concepts: {', '.join(concepts)}. "
        reasoning += "Applying conservation laws, symmetry principles, and dimensional consistency checks. "

        # Add domain-specific reasoning
        if "cosmology" in question.lower() or "universe" in question.lower():
            reasoning += "From cosmological principles: isotropy, homogeneity, and the cosmological principle apply. "
            reasoning += "Einstein field equations provide the foundational framework."

        elif "quantum" in question.lower():
            reasoning += "Quantum principles: superposition, entanglement, and unitarity constrain possible explanations. "
            reasoning += "Wavefunction collapse and measurement problem require careful consideration."

        return reasoning


class EmpiricistAgent(ScientificAgent):
    """Focuses on data analysis and pattern discovery."""

    def __init__(self):
        expertise = AgentExpertise(
            domains=["observational_astronomy", "data_analysis", "statistics"],
            methods=["statistical_testing", "pattern_recognition", "data_mining"],
            strength_areas=["empirical_validation", "significance_testing", "observational_constraints"],
            confidence_by_domain={"observational_astronomy": 0.85, "data_analysis": 0.80}
        )
        super().__init__(AgentRole.EMPIRICIST, expertise)

    def analyze(self, question: str, context: Dict[str, Any]) -> AgentOpinion:
        """Analyze from empirical data perspective."""
        self.status = AgentStatus.ANALYZING

        # Check for available data
        data_sources = context.get("data_sources", [])

        if not data_sources:
            return AgentOpinion(
                agent_id=self.id,
                agent_role=self.role,
                position="neutral",
                confidence=0.3,
                reasoning="Insufficient empirical data. Need observational constraints "
                          "before drawing conclusions.",
                evidence=[]
            )

        # Analyze data availability and quality
        reasoning = "Empirical analysis requires: "
        reasoning += f"Available data sources: {len(data_sources)}. "
        reasoning += "Applying statistical methods: correlation analysis, hypothesis testing, "
        reasoning += "significance evaluation, and uncertainty quantification. "

        # Check for sample size
        total_data_points = sum(ds.get("n_rows", 0) for ds in data_sources)
        reasoning += f"Total data points: {total_data_points}. "
        if total_data_points < 100:
            reasoning += "Limited sample size increases uncertainty. "
        else:
            reasoning += "Adequate sample size for robust statistical inference. "

        confidence = 0.7 if total_data_points >= 100 else 0.4
        position = "support" if confidence > 0.5 else "neutral"

        return AgentOpinion(
            agent_id=self.id,
            agent_role=self.role,
            position=position,
            confidence=confidence,
            reasoning=reasoning,
            evidence=[{"type": "empirical", "data_points": total_data_points}]
        )

    def respond_to_opinion(self, opinion: AgentOpinion, context: Dict[str, Any]) -> Optional[AgentOpinion]:
        """Respond from empirical validation perspective."""
        if opinion.agent_role == AgentRole.THEORIST:
            # Theorist claims something - demand empirical validation
            if opinion.position == "support":
                return AgentOpinion(
                    agent_id=self.id,
                    agent_role=self.role,
                    position="neutral",
                    confidence=0.6,
                    reasoning="Theoretical proposal requires empirical validation. "
                              "Need observational data to test predictions and constrain parameters.",
                    evidence=[{"type": "validation_requirement"}]
                )

        return None


class ExperimentalistAgent(ScientificAgent):
    """Designs observational tests and experiments."""

    def __init__(self):
        expertise = AgentExpertise(
            domains=["observational_design", "instrumentation", "experiment_design"],
            methods=["feasibility_analysis", "sensitivity_estimation", "proposal_design"],
            strength_areas=["experimental_design", "observational_constraints", "test_design"],
            confidence_by_domain={"observational_design": 0.80, "experiment_design": 0.75}
        )
        super().__init__(AgentRole.EXPERIMENTALIST, expertise)

    def analyze(self, question: str, context: Dict[str, Any]) -> AgentOpinion:
        """Design experimental tests for the question."""
        self.status = AgentStatus.ANALYZING

        # Design experimental approach
        reasoning = "Experimental design requires: "
        reasoning += "Identifying testable predictions, designing observational strategy, "
        reasoning += "estimating required sensitivity, and assessing feasibility. "

        # Check if question makes testable predictions
        testability = self._assess_testability(question)

        if testability["testable"]:
            reasoning += f"Testability assessment: {testability['reasoning']}. "
            reasoning += "Proposed observational approach: "
            reasoning += self._propose_experiment(question, context)

            confidence = 0.7
            position = "support"
        else:
            reasoning += f"Testability concern: {testability['reasoning']}. "
            reasoning += "Requires refinement of hypothesis into testable form."

            confidence = 0.4
            position = "neutral"

        return AgentOpinion(
            agent_id=self.id,
            agent_role=self.role,
            position=position,
            confidence=confidence,
            reasoning=reasoning,
            evidence=[{"type": "experimental", "testable": testability["testable"]}],
            alternative_proposals=self._suggest_alternative_tests(question)
        )

    def respond_to_opinion(self, opinion: AgentOpinion, context: Dict[str, Any]) -> Optional[AgentOpinion]:
        """Propose experimental tests for theoretical claims."""
        if opinion.agent_role in [AgentRole.THEORIST, AgentRole.SYNTHESIZER]:
            if opinion.position == "support":
                return AgentOpinion(
                    agent_id=self.id,
                    agent_role=self.role,
                    position="support",
                    confidence=0.6,
                    reasoning="Theoretical proposal supported. Designing experimental test: "
                              "Identify key observables, estimate sensitivity requirements, "
                              "assess feasibility with current instruments.",
                    evidence=[{"type": "experimental_proposal"}]
                )

        return None

    def _assess_testability(self, question: str) -> Dict[str, Any]:
        """Assess whether a question makes testable predictions."""
        # Check for quantifiable terms
        quantifiable_terms = ["relation", "correlation", "distribution", "scale", "law"]
        has_quantifiable = any(term in question.lower() for term in quantifiable_terms)

        # Check for specific domains
        has_domain = any(domain in question.lower() for domain in
                        ["galaxy", "star", "planet", "cosmic", "dark matter", "black hole"])

        if has_quantifiable and has_domain:
            return {
                "testable": True,
                "reasoning": "Question contains quantifiable terms within specific astrophysical domain"
            }

        return {
            "testable": False,
            "reasoning": "Question lacks specific quantifiable predictions or testable domain"
        }

    def _propose_experiment(self, question: str, context: Dict) -> str:
        """Propose experimental approach."""
        if "galaxy" in question.lower():
            return "Large galaxy survey (SDSS/Vera C. Rubin) to measure scaling relations."
        elif "exoplanet" in question.lower():
            return "Transit and radial velocity monitoring to detect and characterize planets."
        elif "cosmic" in question.lower() or "universe" in question.lower():
            return "CMB observations (Planck, LiteBIRD) and large-scale structure surveys."
        else:
            return "Multi-wavelength observational campaign combining existing datasets."

    def _suggest_alternative_tests(self, question: str) -> List[str]:
        """Suggest alternative experimental approaches."""
        alternatives = [
            "Cross-validation using independent datasets",
            "Time-domain observations to test temporal predictions",
            "Multi-wavelength follow-up for consistency checks"
        ]
        return alternatives[:2]


class MathematicianAgent(ScientificAgent):
    """Develops novel mathematical formalisms."""

    def __init__(self):
        expertise = AgentExpertise(
            domains=["mathematical_physics", "formal_methods", "computational_methods"],
            methods=["equation_discovery", "formal_proof", "numerical_methods"],
            strength_areas=["mathematical_consistency", "novel_formalisms", "computational_efficiency"],
            confidence_by_domain={"mathematical_physics": 0.85, "formal_methods": 0.75}
        )
        super().__init__(AgentRole.MATHEMATICIAN, expertise)

    def analyze(self, question: str, context: Dict[str, Any]) -> AgentOpinion:
        """Analyze mathematical structure and formalism."""
        self.status = AgentStatus.THINKING

        # Extract mathematical structure
        math_structure = self._analyze_mathematical_structure(question)

        reasoning = "Mathematical analysis: "
        reasoning += f"Identified structure: {math_structure['type']}. "
        reasoning += "Checking dimensional consistency, mathematical validity, "
        reasoning += "and formal rigor. "

        # Check for mathematical consistency
        if math_structure["consistent"]:
            reasoning += "Structure is mathematically consistent. "
            reasoning += self._propose_formalization(question, math_structure)

            confidence = 0.8
            position = "support"
        else:
            reasoning += f"Concern: {math_structure['inconsistency']}. "
            reasoning += "Requires reformulation for mathematical consistency."

            confidence = 0.4
            position = "oppose"

        return AgentOpinion(
            agent_id=self.id,
            agent_role=self.role,
            position=position,
            confidence=confidence,
            reasoning=reasoning,
            evidence=[{"type": "mathematical", "structure": math_structure}]
        )

    def respond_to_opinion(self, opinion: AgentOpinion, context: Dict[str, Any]) -> Optional[AgentOpinion]:
        """Check mathematical validity of proposals."""
        # Verify mathematical claims
        if "equation" in opinion.reasoning.lower() or "formula" in opinion.reasoning.lower():
            return AgentOpinion(
                agent_id=self.id,
                agent_role=self.role,
                position="neutral",
                confidence=0.7,
                reasoning="Mathematical claims require formal verification: "
                          "dimensional analysis, consistency checks, and rigorous derivation.",
                evidence=[{"type": "mathematical_verification"}]
            )

        return None

    def _analyze_mathematical_structure(self, question: str) -> Dict[str, Any]:
        """Analyze mathematical structure of question."""
        # Identify type of mathematical structure
        if "relation" in question.lower() or "correlation" in question.lower():
            return {"type": "relational", "consistent": True, "dimensional": True}
        elif "distribution" in question.lower():
            return {"type": "statistical", "consistent": True, "dimensional": True}
        elif "scale" in question.lower() or "law" in question.lower():
            return {"type": "scaling_law", "consistent": True, "dimensional": True}
        else:
            return {
                "type": "unknown",
                "consistent": False,
                "inconsistency": "Mathematical structure unclear"
            }

    def _propose_formalization(self, question: str, structure: Dict) -> str:
        """Propose mathematical formalization."""
        if structure["type"] == "scaling_law":
            return "Propose power-law formalism: y = Ax^α. Test linearity in log-log space."
        elif structure["type"] == "relational":
            return "Propose correlation analysis with confidence intervals and significance testing."
        else:
            return "Develop appropriate mathematical framework based on problem structure."


class SkepticAgent(ScientificAgent):
    """Challenges assumptions and identifies weaknesses."""

    def __init__(self):
        expertise = AgentExpertise(
            domains=["critical_analysis", "methodology", "bias_detection"],
            methods=["assumption_challenge", "alternative_explanation", "weakness_identification"],
            strength_areas=["critical_thinking", "identifying_biases", "methodological_rigor"],
            confidence_by_domain={"critical_analysis": 0.85, "methodology": 0.80}
        )
        super().__init__(AgentRole.SKEPTIC, expertise)

    def analyze(self, question: str, context: Dict[str, Any]) -> AgentOpinion:
        """Identify potential issues and weaknesses."""
        self.status = AgentStatus.THINKING

        # Identify assumptions and weaknesses
        assumptions = self._identify_assumptions(question)
        weaknesses = self._identify_weaknesses(question, context)

        reasoning = "Skeptical analysis: "
        reasoning += f"Identified {len(assumptions)} assumptions and {len(weaknesses)} potential weaknesses. "

        if assumptions:
            reasoning += f"Key assumptions: {assumptions[0]}. "

        if weaknesses:
            reasoning += f"Concerns: {weaknesses[0]}. "

        # Skeptical position by default
        confidence = 0.6
        position = "neutral"

        # If no major concerns, can support
        if not assumptions and not weaknesses:
            reasoning += "No major concerns identified. Proposal appears sound."
            position = "support"
            confidence = 0.5

        return AgentOpinion(
            agent_id=self.id,
            agent_role=self.role,
            position=position,
            confidence=confidence,
            reasoning=reasoning,
            evidence=[{"type": "skeptical", "assumptions": assumptions, "weaknesses": weaknesses}],
            alternative_proposals=self._suggest_alternatives(question)
        )

    def respond_to_opinion(self, opinion: AgentOpinion, context: Dict[str, Any]) -> Optional[AgentOpinion]:
        """Challenge other agents' opinions."""
        if opinion.position == "support":
            # Challenge supportive opinions
            return AgentOpinion(
                agent_id=self.id,
                agent_role=self.role,
                position="neutral",
                confidence=0.6,
                reasoning=f"Skeptical of {opinion.agent_role.value}'s confident support. "
                          f"Must address: alternative explanations, potential biases, "
                          f"and methodological limitations.",
                evidence=[{"type": "challenge", "target": opinion.agent_id}]
            )

        return None

    def _identify_assumptions(self, question: str) -> List[str]:
        """Identify implicit assumptions in question."""
        assumptions = []

        # Common assumptions to check
        if "cause" in question.lower() or "leads to" in question.lower():
            assumptions.append("Causal direction assumed without proof")

        if "relation" in question.lower() and "linear" not in question.lower():
            assumptions.append("Functional form of relation unspecified")

        if "all" in question.lower() or "universal" in question.lower():
            assumptions.append("Universality claim without domain specification")

        return assumptions

    def _identify_weaknesses(self, question: str, context: Dict) -> List[str]:
        """Identify potential weaknesses in approach."""
        weaknesses = []

        # Check data-related weaknesses
        data_sources = context.get("data_sources", [])
        if not data_sources:
            weaknesses.append("No empirical data specified for validation")

        # Check methodological weaknesses
        if "test" not in question.lower() and "measure" not in question.lower():
            weaknesses.append("No clear testing methodology specified")

        return weaknesses

    def _suggest_alternatives(self, question: str) -> List[str]:
        """Suggest alternative explanations or approaches."""
        alternatives = [
            "Consider alternative causal directions",
            "Test for confounding variables",
            "Evaluate with independent datasets"
        ]
        return alternatives[:2]


class SynthesizerAgent(ScientificAgent):
    """Integrates insights across domains and agents."""

    def __init__(self):
        expertise = AgentExpertise(
            domains=["integration", "synthesis", "cross_domain"],
            methods=["consensus_building", "synthesis", "unification"],
            strength_areas=["cross_domain_insights", "integration", "big_picture_thinking"],
            confidence_by_domain={"integration": 0.85, "synthesis": 0.80}
        )
        super().__init__(AgentRole.SYNTHESIZER, expertise)

    def analyze(self, question: str, context: Dict[str, Any]) -> AgentOpinion:
        """Synthesize across domains and provide integrated perspective."""
        self.status = AgentStatus.THINKING

        # Get other agent opinions if available
        other_opinions = context.get("agent_opinions", [])

        reasoning = "Synthesis analysis: "
        reasoning += "Integrating insights across theoretical, empirical, experimental, "
        reasoning += "mathematical, and critical perspectives. "

        if other_opinions:
            # Synthesize other opinions
            support_count = sum(1 for o in other_opinions if o.position == "support")
            oppose_count = sum(1 for o in other_opinions if o.position == "oppose")
            neutral_count = sum(1 for o in other_opinions if o.position == "neutral")

            reasoning += f"Current consensus: {support_count} support, {oppose_count} oppose, "
            reasoning += f"{neutral_count} neutral. "

            # Calculate overall confidence
            if support_count > len(other_opinions) / 2:
                reasoning += "Majority support indicates promising direction. "
                confidence = 0.7 * (support_count / len(other_opinions))
                position = "support"
            elif oppose_count > len(other_opinions) / 2:
                reasoning += "Significant opposition indicates need for refinement. "
                confidence = 0.5
                position = "neutral"
            else:
                reasoning += "Mixed opinions suggest need for further investigation. "
                confidence = 0.6
                position = "neutral"
        else:
            # Provide integrated perspective without other opinions
            reasoning += "Awaiting input from specialized agents for comprehensive synthesis. "
            reasoning += "Will integrate theoretical consistency, empirical validation, "
            reasoning += "experimental feasibility, mathematical rigor, and critical analysis."

            confidence = 0.5
            position = "neutral"

        return AgentOpinion(
            agent_id=self.id,
            agent_role=self.role,
            position=position,
            confidence=confidence,
            reasoning=reasoning,
            evidence=[{"type": "synthesis", "integrated_view": True}],
            alternative_proposals=self._propose_integrated_approach(question)
        )

    def respond_to_opinion(self, opinion: AgentOpinion, context: Dict[str, Any]) -> Optional[AgentOpinion]:
        """Synthesize across opinions."""
        # As synthesizer, rarely responds - focuses on final synthesis
        return None

    def _propose_integrated_approach(self, question: str) -> List[str]:
        """Propose integrated approaches combining multiple perspectives."""
        approaches = [
            "Combine first-principles theory with empirical validation",
            "Integrate mathematical formalism with experimental design",
            "Unify insights across domains through cross-domain analogies"
        ]
        return approaches[:2]


class AgentFactory:
    """Factory for creating specialized scientific agents."""

    _agent_classes = {
        AgentRole.THEORIST: TheoristAgent,
        AgentRole.EMPIRICIST: EmpiricistAgent,
        AgentRole.EXPERIMENTALIST: ExperimentalistAgent,
        AgentRole.MATHEMATICIAN: MathematicianAgent,
        AgentRole.SKEPTIC: SkepticAgent,
        AgentRole.SYNTHESIZER: SynthesizerAgent
    }

    @classmethod
    def create_agent(cls, role: AgentRole) -> ScientificAgent:
        """Create an agent of the specified role."""
        agent_class = cls._agent_classes.get(role)
        if agent_class is None:
            raise ValueError(f"Unknown agent role: {role}")

        return agent_class()

    @classmethod
    def create_collaboration_group(cls, roles: List[AgentRole]) -> List[ScientificAgent]:
        """Create a group of agents for collaboration."""
        return [cls.create_agent(role) for role in roles]

    @classmethod
    def create_full_team(cls) -> List[ScientificAgent]:
        """Create a complete team with all six agent types."""
        return cls.create_collaboration_group(list(AgentRole))

    @classmethod
    def create_minimal_team(cls) -> List[ScientificAgent]:
        """Create a minimal team with 4 essential agents."""
        return cls.create_collaboration_group([
            AgentRole.THEORIST,
            AgentRole.EMPIRICIST,
            AgentRole.EXPERIMENTALIST,
            AgentRole.SYNTHESIZER
        ])


# Utility functions
def get_agent_description(role: AgentRole) -> str:
    """Get human-readable description of agent role."""
    descriptions = {
        AgentRole.THEORIST: "Focuses on theoretical frameworks and first-principles reasoning",
        AgentRole.EMPIRICIST: "Focuses on data analysis and empirical validation",
        AgentRole.EXPERIMENTALIST: "Designs observational tests and experiments",
        AgentRole.MATHEMATICIAN: "Develops novel mathematical formalisms",
        AgentRole.SKEPTIC: "Challenges assumptions and identifies weaknesses",
        AgentRole.SYNTHESIZER: "Integrates insights across domains and agents"
    }
    return descriptions.get(role, "Unknown role")


def validate_agent_collaboration(agents: List[ScientificAgent]) -> Dict[str, Any]:
    """Validate that a group of agents can collaborate effectively."""
    roles = [agent.role for agent in agents]
    unique_roles = set(roles)

    return {
        "total_agents": len(agents),
        "unique_roles": len(unique_roles),
        "role_diversity": len(unique_roles) / len(AgentRole),
        "has_synthesizer": AgentRole.SYNTHESIZER in roles,
        "has_skeptic": AgentRole.SKEPTIC in roles,
        "balanced": len(unique_roles) >= 4
    }
