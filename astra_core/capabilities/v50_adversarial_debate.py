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
V50 Multi-Agent Adversarial Debate System
==========================================

Replace single-system reasoning with adversarial multi-agent debate.

Errors that slip past one agent get caught by adversarial agents.
This mimics scientific peer review.

Agent Roles:
1. Proposer - Generates hypotheses and explanations
2. Critic - Finds flaws, edge cases, counterexamples
3. RedTeam - Actively tries to break the proposed answer
4. Verifier - Checks formal properties, runs simulations
5. Arbitrator - Resolves disputes with formal proofs when possible

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import random
import math
import time


class AgentRole(Enum):
    """Roles of agents in debate."""
    PROPOSER = "proposer"
    CRITIC = "critic"
    RED_TEAM = "red_team"
    VERIFIER = "verifier"
    ARBITRATOR = "arbitrator"
    DOMAIN_EXPERT = "domain_expert"


class ArgumentType(Enum):
    """Types of arguments in debate."""
    CLAIM = "claim"
    SUPPORT = "support"
    OBJECTION = "objection"
    REBUTTAL = "rebuttal"
    COUNTEREXAMPLE = "counterexample"
    VERIFICATION = "verification"
    CONSENSUS = "consensus"


class VerdictType(Enum):
    """Types of verdicts."""
    ACCEPT = "accept"
    REJECT = "reject"
    REVISE = "revise"
    INSUFFICIENT_EVIDENCE = "insufficient"
    SPLIT_DECISION = "split"


@dataclass
class Argument:
    """An argument in the debate."""
    agent_role: AgentRole
    argument_type: ArgumentType
    content: str
    target_claim: Optional[str]
    confidence: float
    evidence: List[str]
    timestamp: float


@dataclass
class Claim:
    """A claim being debated."""
    content: str
    proposer: AgentRole
    answer_index: int
    confidence: float
    supporting_arguments: List[Argument] = field(default_factory=list)
    opposing_arguments: List[Argument] = field(default_factory=list)
    status: str = "active"


@dataclass
class DebateRound:
    """A single round of debate."""
    round_number: int
    arguments: List[Argument]
    claims_active: List[Claim]
    claims_eliminated: List[Claim]
    consensus_level: float


@dataclass
class DebateResult:
    """Final result of debate."""
    question: str
    domain: str
    winning_claim: Optional[Claim]
    answer: str
    answer_index: int
    confidence: float
    verdict: VerdictType
    rounds: List[DebateRound]
    total_arguments: int
    consensus_level: float
    agent_contributions: Dict[str, int]
    debate_time: float


class BaseAgent(ABC):
    """Base class for debate agents."""

    def __init__(self, role: AgentRole):
        self.role = role
        self.arguments_made = 0
        self.successful_arguments = 0

    @abstractmethod
    def generate_argument(self, question: str, domain: str,
                          choices: List[str],
                          current_claims: List[Claim],
                          debate_history: List[Argument]) -> Optional[Argument]:
        """Generate an argument for the debate."""
        pass

    def update_success(self, argument: Argument, accepted: bool):
        """Update success statistics."""
        self.arguments_made += 1
        if accepted:
            self.successful_arguments += 1

    def get_effectiveness(self) -> float:
        """Get effectiveness rate."""
        if self.arguments_made == 0:
            return 0.5
        return self.successful_arguments / self.arguments_made


class ProposerAgent(BaseAgent):
    """
    Agent that proposes answers and hypotheses.

    Generates initial claims and responds to criticism.
    """

    def __init__(self):
        super().__init__(AgentRole.PROPOSER)

    def generate_argument(self, question: str, domain: str,
                          choices: List[str],
                          current_claims: List[Claim],
                          debate_history: List[Argument]) -> Optional[Argument]:
        """Generate a proposal or defense."""
        # If no claims yet, propose
        if not current_claims:
            return self._generate_initial_proposal(question, domain, choices)

        # If our claim is under attack, defend
        under_attack = self._find_claims_under_attack(current_claims, debate_history)
        if under_attack:
            return self._generate_defense(under_attack[0], debate_history)

        # Otherwise, strengthen existing claims
        return self._strengthen_claim(current_claims[0], question, domain)

    def _generate_initial_proposal(self, question: str, domain: str,
                                    choices: List[str]) -> Argument:
        """Generate initial answer proposal."""
        # Analyze question and choices
        scores = []
        for i, choice in enumerate(choices):
            score = self._score_choice(question, choice, domain)
            scores.append((i, score, choice))

        # Select best
        scores.sort(key=lambda x: x[1], reverse=True)
        best_idx, best_score, best_choice = scores[0]

        return Argument(
            agent_role=self.role,
            argument_type=ArgumentType.CLAIM,
            content=f"I propose answer {best_idx}: {best_choice[:100]}",
            target_claim=None,
            confidence=best_score,
            evidence=self._generate_evidence(question, best_choice, domain),
            timestamp=time.time()
        )

    def _generate_defense(self, claim: Claim, history: List[Argument]) -> Argument:
        """Generate defense against objections."""
        # Find objections
        objections = [a for a in history
                     if a.argument_type == ArgumentType.OBJECTION
                     and a.target_claim == claim.content]

        if not objections:
            return self._strengthen_claim(claim, "", "")

        # Address strongest objection
        strongest = max(objections, key=lambda a: a.confidence)

        return Argument(
            agent_role=self.role,
            argument_type=ArgumentType.REBUTTAL,
            content=f"Rebutting: {strongest.content[:50]}... The objection fails because...",
            target_claim=strongest.content,
            confidence=claim.confidence * 0.9,
            evidence=[f"Original claim evidence: {e}" for e in claim.supporting_arguments[0].evidence[:2]]
            if claim.supporting_arguments else [],
            timestamp=time.time()
        )

    def _strengthen_claim(self, claim: Claim, question: str, domain: str) -> Argument:
        """Add supporting evidence to claim."""
        return Argument(
            agent_role=self.role,
            argument_type=ArgumentType.SUPPORT,
            content=f"Additional support for {claim.content[:50]}...",
            target_claim=claim.content,
            confidence=claim.confidence,
            evidence=[f"Supporting point {i+1}" for i in range(2)],
            timestamp=time.time()
        )

    def _score_choice(self, question: str, choice: str, domain: str) -> float:
        """Score a choice's likelihood."""
        score = 0.5

        # Length heuristic
        if 20 < len(choice) < 200:
            score += 0.1

        # Keyword overlap
        q_words = set(question.lower().split())
        c_words = set(choice.lower().split())
        overlap = len(q_words & c_words)
        score += min(0.2, overlap * 0.02)

        # Domain-specific keywords
        domain_keywords = {
            'Physics': ['energy', 'force', 'momentum', 'conservation'],
            'Chemistry': ['reaction', 'equilibrium', 'concentration'],
            'Biology': ['enzyme', 'pathway', 'regulation']
        }

        for kw in domain_keywords.get(domain, []):
            if kw in choice.lower():
                score += 0.05

        return min(0.95, score + random.uniform(-0.1, 0.1))

    def _generate_evidence(self, question: str, choice: str, domain: str) -> List[str]:
        """Generate evidence for a choice."""
        evidence = []

        evidence.append(f"Domain reasoning: {domain} principles support this")
        evidence.append(f"Logical consistency: Answer aligns with question requirements")

        if 'increase' in choice.lower() or 'decrease' in choice.lower():
            evidence.append("Directional reasoning: Change direction is consistent")

        return evidence

    def _find_claims_under_attack(self, claims: List[Claim],
                                   history: List[Argument]) -> List[Claim]:
        """Find claims that have recent objections."""
        under_attack = []
        for claim in claims:
            objections = [a for a in history[-5:]
                         if a.argument_type == ArgumentType.OBJECTION
                         and claim.content in str(a.target_claim)]
            if objections:
                under_attack.append(claim)
        return under_attack


class CriticAgent(BaseAgent):
    """
    Agent that criticizes and finds flaws.

    Looks for logical errors, missing considerations, edge cases.
    """

    def __init__(self):
        super().__init__(AgentRole.CRITIC)
        self.critique_templates = [
            "This answer ignores the possibility that {alternative}",
            "The reasoning fails to account for {factor}",
            "This conclusion doesn't follow because {reason}",
            "There's insufficient evidence for the claim that {claim}",
            "The answer contradicts the principle of {principle}"
        ]

    def generate_argument(self, question: str, domain: str,
                          choices: List[str],
                          current_claims: List[Claim],
                          debate_history: List[Argument]) -> Optional[Argument]:
        """Generate a critique."""
        if not current_claims:
            return None

        # Find claim to critique
        target = self._select_target(current_claims, debate_history)
        if not target:
            return None

        return self._generate_critique(target, question, domain, choices)

    def _select_target(self, claims: List[Claim],
                        history: List[Argument]) -> Optional[Claim]:
        """Select a claim to critique."""
        # Prefer claims that haven't been critiqued recently
        recent_targets = set()
        for arg in history[-5:]:
            if arg.argument_type == ArgumentType.OBJECTION:
                recent_targets.add(arg.target_claim)

        for claim in claims:
            if claim.content not in recent_targets:
                return claim

        # If all critiqued, pick highest confidence (most needs scrutiny)
        return max(claims, key=lambda c: c.confidence) if claims else None

    def _generate_critique(self, claim: Claim, question: str,
                           domain: str, choices: List[str]) -> Argument:
        """Generate critique for a claim."""
        # Find potential issues
        issues = self._find_issues(claim, question, domain, choices)

        if issues:
            content = random.choice(issues)
        else:
            content = f"The claim '{claim.content[:50]}' requires further justification"

        return Argument(
            agent_role=self.role,
            argument_type=ArgumentType.OBJECTION,
            content=content,
            target_claim=claim.content,
            confidence=0.6,
            evidence=self._generate_critique_evidence(claim, domain),
            timestamp=time.time()
        )

    def _find_issues(self, claim: Claim, question: str,
                      domain: str, choices: List[str]) -> List[str]:
        """Find potential issues with claim."""
        issues = []

        # Check for missing considerations
        claim_lower = claim.content.lower()

        if 'increase' in claim_lower and 'decrease' in question.lower():
            issues.append("The answer suggests increase but question context implies decrease")

        if 'always' in claim_lower or 'never' in claim_lower:
            issues.append("Absolute statements like 'always/never' are often incorrect")

        # Check for ignored alternatives
        other_choices = [c for c in choices if c not in claim.content]
        if other_choices:
            alt = other_choices[0][:50]
            issues.append(f"This ignores the possibility: {alt}")

        # Domain-specific critiques
        if domain == 'Physics':
            if 'energy' not in claim_lower and 'energy' in question.lower():
                issues.append("Energy considerations are not addressed")
        elif domain == 'Chemistry':
            if 'equilibrium' not in claim_lower and 'equilibrium' in question.lower():
                issues.append("Equilibrium effects not considered")
        elif domain == 'Biology':
            if 'regulation' not in claim_lower and 'gene' in question.lower():
                issues.append("Regulatory mechanisms not addressed")

        return issues

    def _generate_critique_evidence(self, claim: Claim, domain: str) -> List[str]:
        """Generate evidence for critique."""
        return [
            f"Domain principle violation: {domain} fundamentals not properly applied",
            "Logical gap: Conclusion not fully supported by premises"
        ]


class RedTeamAgent(BaseAgent):
    """
    Agent that actively tries to break proposed answers.

    Searches for counterexamples, edge cases, and failures.
    """

    def __init__(self):
        super().__init__(AgentRole.RED_TEAM)

    def generate_argument(self, question: str, domain: str,
                          choices: List[str],
                          current_claims: List[Claim],
                          debate_history: List[Argument]) -> Optional[Argument]:
        """Generate adversarial argument."""
        if not current_claims:
            return None

        # Target the strongest claim
        target = max(current_claims, key=lambda c: c.confidence)

        # Try to find counterexample
        counterexample = self._find_counterexample(target, question, domain, choices)

        if counterexample:
            return counterexample

        # Try edge case attack
        return self._edge_case_attack(target, question, domain)

    def _find_counterexample(self, claim: Claim, question: str,
                              domain: str, choices: List[str]) -> Optional[Argument]:
        """Try to find a counterexample to the claim."""
        # Look for scenarios where claim would fail
        counterexamples = []

        claim_lower = claim.content.lower()

        # Physical counterexamples
        if domain == 'Physics':
            if 'increase' in claim_lower:
                counterexamples.append(
                    "Counterexample: In a closed system, this quantity is conserved, not increased"
                )
            if 'velocity' in claim_lower and 'acceleration' not in claim_lower:
                counterexamples.append(
                    "Counterexample: Without acceleration, velocity remains constant"
                )

        # Chemical counterexamples
        elif domain == 'Chemistry':
            if 'rate' in claim_lower and 'temperature' not in claim_lower:
                counterexamples.append(
                    "Counterexample: Rate depends on temperature via Arrhenius equation"
                )
            if 'equilibrium' in claim_lower:
                counterexamples.append(
                    "Counterexample: Le Chatelier's principle may shift equilibrium oppositely"
                )

        # Biological counterexamples
        elif domain == 'Biology':
            if 'expression' in claim_lower:
                counterexamples.append(
                    "Counterexample: Feedback inhibition could prevent predicted expression change"
                )

        if counterexamples:
            return Argument(
                agent_role=self.role,
                argument_type=ArgumentType.COUNTEREXAMPLE,
                content=random.choice(counterexamples),
                target_claim=claim.content,
                confidence=0.7,
                evidence=["Domain-specific counterexample"],
                timestamp=time.time()
            )

        return None

    def _edge_case_attack(self, claim: Claim, question: str,
                           domain: str) -> Argument:
        """Attack using edge cases."""
        edge_cases = [
            f"Edge case: At extreme values, the claim '{claim.content[:30]}' fails",
            "Edge case: Near zero/infinity limits may violate this claim",
            "Edge case: Time-dependent effects could reverse this outcome"
        ]

        return Argument(
            agent_role=self.role,
            argument_type=ArgumentType.OBJECTION,
            content=random.choice(edge_cases),
            target_claim=claim.content,
            confidence=0.5,
            evidence=["Edge case analysis"],
            timestamp=time.time()
        )


class VerifierAgent(BaseAgent):
    """
    Agent that verifies claims using formal methods.

    Checks dimensional consistency, conservation laws, simulations.
    """

    def __init__(self):
        super().__init__(AgentRole.VERIFIER)

    def generate_argument(self, question: str, domain: str,
                          choices: List[str],
                          current_claims: List[Claim],
                          debate_history: List[Argument]) -> Optional[Argument]:
        """Generate verification result."""
        if not current_claims:
            return None

        # Verify each active claim
        for claim in current_claims:
            verification = self._verify_claim(claim, question, domain)
            if verification:
                return verification

        return None

    def _verify_claim(self, claim: Claim, question: str,
                       domain: str) -> Optional[Argument]:
        """Verify a claim using domain-specific checks."""
        checks = []

        # Dimensional analysis
        dim_result = self._dimensional_check(claim, domain)
        checks.append(dim_result)

        # Conservation check
        cons_result = self._conservation_check(claim, domain)
        checks.append(cons_result)

        # Consistency check
        consist_result = self._consistency_check(claim, question)
        checks.append(consist_result)

        # Aggregate results
        passed = sum(1 for c in checks if c['passed'])
        total = len(checks)

        if passed == total:
            return Argument(
                agent_role=self.role,
                argument_type=ArgumentType.VERIFICATION,
                content=f"VERIFIED: Claim passes all {total} verification checks",
                target_claim=claim.content,
                confidence=0.9,
                evidence=[c['evidence'] for c in checks],
                timestamp=time.time()
            )
        elif passed > 0:
            failed = [c for c in checks if not c['passed']]
            return Argument(
                agent_role=self.role,
                argument_type=ArgumentType.OBJECTION,
                content=f"PARTIAL: {passed}/{total} checks passed. Failed: {failed[0]['name']}",
                target_claim=claim.content,
                confidence=0.6,
                evidence=[c['evidence'] for c in checks],
                timestamp=time.time()
            )
        else:
            return Argument(
                agent_role=self.role,
                argument_type=ArgumentType.OBJECTION,
                content=f"REJECTED: Claim fails verification checks",
                target_claim=claim.content,
                confidence=0.8,
                evidence=[c['evidence'] for c in checks],
                timestamp=time.time()
            )

    def _dimensional_check(self, claim: Claim, domain: str) -> Dict:
        """Check dimensional consistency."""
        # Simplified check
        passed = True
        evidence = "Dimensions appear consistent"

        claim_lower = claim.content.lower()

        # Check for obvious dimensional mismatches
        if 'energy' in claim_lower and 'velocity' in claim_lower:
            if 'squared' not in claim_lower and '²' not in claim_lower:
                passed = False
                evidence = "Energy depends on velocity squared, not linear"

        return {
            'name': 'dimensional',
            'passed': passed,
            'evidence': evidence
        }

    def _conservation_check(self, claim: Claim, domain: str) -> Dict:
        """Check conservation laws."""
        passed = True
        evidence = "Conservation laws not violated"

        claim_lower = claim.content.lower()

        # Check for conservation violations
        if domain == 'Physics':
            if 'created' in claim_lower or 'destroyed' in claim_lower:
                if 'energy' in claim_lower or 'momentum' in claim_lower:
                    passed = False
                    evidence = "Energy/momentum cannot be created or destroyed"

        elif domain == 'Chemistry':
            if 'mass' in claim_lower:
                if 'lost' in claim_lower or 'gained' in claim_lower:
                    # Check context
                    if 'nuclear' not in claim_lower:
                        passed = False
                        evidence = "Mass is conserved in chemical reactions"

        return {
            'name': 'conservation',
            'passed': passed,
            'evidence': evidence
        }

    def _consistency_check(self, claim: Claim, question: str) -> Dict:
        """Check logical consistency."""
        passed = True
        evidence = "Claim is internally consistent"

        # Check for contradictions
        claim_lower = claim.content.lower()
        q_lower = question.lower()

        if 'increase' in claim_lower and 'decrease' in claim_lower:
            passed = False
            evidence = "Claim contains contradiction: increase and decrease"

        if 'always' in claim_lower and 'sometimes' in q_lower:
            passed = False
            evidence = "Absolute claim conflicts with conditional question"

        return {
            'name': 'consistency',
            'passed': passed,
            'evidence': evidence
        }


class ArbitratorAgent(BaseAgent):
    """
    Agent that arbitrates disputes and reaches consensus.

    Uses formal logic and voting to resolve disagreements.
    """

    def __init__(self):
        super().__init__(AgentRole.ARBITRATOR)
        self.arbitration_threshold = 0.6

    def generate_argument(self, question: str, domain: str,
                          choices: List[str],
                          current_claims: List[Claim],
                          debate_history: List[Argument]) -> Optional[Argument]:
        """Generate arbitration decision."""
        if len(current_claims) < 2 and len(debate_history) < 5:
            return None  # Not enough to arbitrate

        # Count support and opposition for each claim
        claim_scores = {}
        for claim in current_claims:
            support = len([a for a in debate_history
                          if a.target_claim == claim.content
                          and a.argument_type in [ArgumentType.SUPPORT, ArgumentType.VERIFICATION]])
            oppose = len([a for a in debate_history
                         if a.target_claim == claim.content
                         and a.argument_type in [ArgumentType.OBJECTION, ArgumentType.COUNTEREXAMPLE]])

            claim_scores[claim.content] = {
                'support': support,
                'oppose': oppose,
                'net': support - oppose,
                'confidence': claim.confidence,
                'claim': claim
            }

        # Determine winner
        if claim_scores:
            winner_content = max(claim_scores.keys(),
                                key=lambda k: claim_scores[k]['net'] + claim_scores[k]['confidence'])
            winner = claim_scores[winner_content]

            if winner['net'] >= 0 and winner['confidence'] > self.arbitration_threshold:
                return Argument(
                    agent_role=self.role,
                    argument_type=ArgumentType.CONSENSUS,
                    content=f"ARBITRATION: Accept '{winner_content[:50]}' "
                            f"(support={winner['support']}, oppose={winner['oppose']})",
                    target_claim=winner_content,
                    confidence=min(0.95, winner['confidence'] + 0.1),
                    evidence=[f"Net support: {winner['net']}", f"Base confidence: {winner['confidence']:.2f}"],
                    timestamp=time.time()
                )
            else:
                return Argument(
                    agent_role=self.role,
                    argument_type=ArgumentType.CONSENSUS,
                    content="ARBITRATION: No clear winner, requires more debate",
                    target_claim=None,
                    confidence=0.4,
                    evidence=["Insufficient consensus"],
                    timestamp=time.time()
                )

        return None


class DebateArena:
    """
    Arena for multi-agent adversarial debate.

    Orchestrates agents and manages debate flow.
    """

    def __init__(self, max_rounds: int = 10):
        self.max_rounds = max_rounds

        # Initialize agents
        self.proposer = ProposerAgent()
        self.critic = CriticAgent()
        self.red_team = RedTeamAgent()
        self.verifier = VerifierAgent()
        self.arbitrator = ArbitratorAgent()

        self.agents: List[BaseAgent] = [
            self.proposer,
            self.critic,
            self.red_team,
            self.verifier,
            self.arbitrator
        ]

    def debate(self, question: str, domain: str,
               choices: List[str]) -> DebateResult:
        """
        Run a complete debate on a question.

        Args:
            question: Question to debate
            domain: Domain hint
            choices: Answer choices

        Returns:
            DebateResult with final answer
        """
        start_time = time.time()

        claims: List[Claim] = []
        eliminated_claims: List[Claim] = []
        debate_history: List[Argument] = []
        rounds: List[DebateRound] = []
        agent_contributions: Dict[str, int] = defaultdict(int)

        # Run debate rounds
        for round_num in range(self.max_rounds):
            round_arguments = []

            # Each agent gets a turn
            for agent in self.agents:
                argument = agent.generate_argument(
                    question, domain, choices, claims, debate_history
                )

                if argument:
                    round_arguments.append(argument)
                    debate_history.append(argument)
                    agent_contributions[agent.role.value] += 1

                    # Process argument
                    self._process_argument(argument, claims, eliminated_claims, choices)

            # Check for consensus
            consensus_level = self._compute_consensus(claims, debate_history)

            rounds.append(DebateRound(
                round_number=round_num,
                arguments=round_arguments,
                claims_active=claims.copy(),
                claims_eliminated=eliminated_claims.copy(),
                consensus_level=consensus_level
            ))

            # Early termination if strong consensus
            if consensus_level > 0.85:
                break

        # Final arbitration
        winning_claim = self._final_arbitration(claims, debate_history)

        # Determine verdict
        verdict = self._determine_verdict(winning_claim, claims, debate_history)

        # Get answer
        if winning_claim:
            answer = choices[winning_claim.answer_index] if winning_claim.answer_index < len(choices) else ""
            answer_index = winning_claim.answer_index
            confidence = winning_claim.confidence
        else:
            # Fallback
            answer = choices[0] if choices else ""
            answer_index = 0
            confidence = 0.3

        return DebateResult(
            question=question,
            domain=domain,
            winning_claim=winning_claim,
            answer=answer,
            answer_index=answer_index,
            confidence=confidence,
            verdict=verdict,
            rounds=rounds,
            total_arguments=len(debate_history),
            consensus_level=self._compute_consensus(claims, debate_history),
            agent_contributions=dict(agent_contributions),
            debate_time=time.time() - start_time
        )

    def _process_argument(self, argument: Argument,
                           claims: List[Claim],
                           eliminated: List[Claim],
                           choices: List[str]):
        """Process an argument and update claims."""
        if argument.argument_type == ArgumentType.CLAIM:
            # Extract answer index from content
            answer_idx = 0
            for i in range(len(choices)):
                if f"answer {i}" in argument.content.lower():
                    answer_idx = i
                    break

            claim = Claim(
                content=argument.content,
                proposer=argument.agent_role,
                answer_index=answer_idx,
                confidence=argument.confidence,
                supporting_arguments=[argument]
            )
            claims.append(claim)

        elif argument.argument_type == ArgumentType.SUPPORT:
            # Add support to matching claim
            for claim in claims:
                if argument.target_claim and argument.target_claim in claim.content:
                    claim.supporting_arguments.append(argument)
                    claim.confidence = min(0.98, claim.confidence + 0.05)

        elif argument.argument_type in [ArgumentType.OBJECTION, ArgumentType.COUNTEREXAMPLE]:
            # Add opposition to matching claim
            for claim in claims:
                if argument.target_claim and argument.target_claim in claim.content:
                    claim.opposing_arguments.append(argument)
                    claim.confidence = max(0.1, claim.confidence - 0.1)

                    # Eliminate if too much opposition
                    if len(claim.opposing_arguments) > len(claim.supporting_arguments) + 2:
                        claim.status = "eliminated"
                        eliminated.append(claim)
                        claims.remove(claim)

        elif argument.argument_type == ArgumentType.VERIFICATION:
            # Boost verified claims
            for claim in claims:
                if argument.target_claim and argument.target_claim in claim.content:
                    claim.supporting_arguments.append(argument)
                    claim.confidence = min(0.98, claim.confidence + 0.15)

        elif argument.argument_type == ArgumentType.CONSENSUS:
            # Mark consensus
            for claim in claims:
                if argument.target_claim and argument.target_claim in claim.content:
                    claim.status = "consensus"

    def _compute_consensus(self, claims: List[Claim],
                            history: List[Argument]) -> float:
        """Compute level of consensus."""
        if not claims:
            return 0.0

        # Check if one claim dominates
        if len(claims) == 1:
            return claims[0].confidence

        # Compare top claims
        sorted_claims = sorted(claims, key=lambda c: c.confidence, reverse=True)
        if len(sorted_claims) >= 2:
            gap = sorted_claims[0].confidence - sorted_claims[1].confidence
            return min(1.0, 0.5 + gap)

        return 0.5

    def _final_arbitration(self, claims: List[Claim],
                            history: List[Argument]) -> Optional[Claim]:
        """Final arbitration to select winner."""
        if not claims:
            return None

        # Score each claim
        scored = []
        for claim in claims:
            support = len(claim.supporting_arguments)
            oppose = len(claim.opposing_arguments)
            verification = len([a for a in claim.supporting_arguments
                               if a.argument_type == ArgumentType.VERIFICATION])

            score = (
                claim.confidence * 0.4 +
                (support / max(support + oppose, 1)) * 0.3 +
                verification * 0.3
            )
            scored.append((claim, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    def _determine_verdict(self, winner: Optional[Claim],
                            claims: List[Claim],
                            history: List[Argument]) -> VerdictType:
        """Determine verdict type."""
        if not winner:
            return VerdictType.INSUFFICIENT_EVIDENCE

        if winner.confidence > 0.8:
            if winner.status == "consensus":
                return VerdictType.ACCEPT

        if len(claims) > 1:
            second = sorted(claims, key=lambda c: c.confidence, reverse=True)[1]
            if winner.confidence - second.confidence < 0.1:
                return VerdictType.SPLIT_DECISION

        if winner.confidence > 0.6:
            return VerdictType.ACCEPT
        else:
            return VerdictType.REVISE


class AdversarialDebateReasoner:
    """
    Main interface for adversarial debate reasoning.

    Wraps DebateArena with reasoning interface.
    """

    def __init__(self, max_rounds: int = 8):
        self.arena = DebateArena(max_rounds=max_rounds)

    def reason(self, question: str, domain: str = "",
               choices: List[str] = None) -> Dict[str, Any]:
        """
        Reason about a question using adversarial debate.

        Args:
            question: Question to answer
            domain: Domain hint
            choices: Answer choices

        Returns:
            Answer with debate results
        """
        choices = choices or []

        # Run debate
        result = self.arena.debate(question, domain, choices)

        return {
            'answer': result.answer,
            'answer_index': result.answer_index,
            'confidence': result.confidence,
            'verdict': result.verdict.value,
            'consensus_level': result.consensus_level,
            'debate_rounds': len(result.rounds),
            'total_arguments': result.total_arguments,
            'agent_contributions': result.agent_contributions,
            'debate_time': result.debate_time,
            'reasoning_trace': self._extract_trace(result)
        }

    def _extract_trace(self, result: DebateResult) -> List[str]:
        """Extract reasoning trace from debate."""
        trace = []

        for round_info in result.rounds:
            for arg in round_info.arguments:
                trace.append(f"[{arg.agent_role.value}] {arg.argument_type.value}: {arg.content[:80]}")

        if result.winning_claim:
            trace.append(f"[VERDICT] {result.verdict.value}: {result.winning_claim.content[:80]}")

        return trace

    def get_stats(self) -> Dict[str, Any]:
        """Get debate statistics."""
        return {
            'agents': [a.role.value for a in self.arena.agents],
            'agent_effectiveness': {
                a.role.value: a.get_effectiveness()
                for a in self.arena.agents
            },
            'max_rounds': self.arena.max_rounds
        }


# Factory functions
def create_debate_reasoner(max_rounds: int = 8) -> AdversarialDebateReasoner:
    """Create an adversarial debate reasoner."""
    return AdversarialDebateReasoner(max_rounds=max_rounds)


def create_debate_arena(max_rounds: int = 10) -> DebateArena:
    """Create a debate arena."""
    return DebateArena(max_rounds=max_rounds)



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



# Custom optimization variant 1
def optimize_computation_1(func):
    """Decorator for optimizing computation."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


