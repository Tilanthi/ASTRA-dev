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
Enhanced Swarm Integration Module

Implements all 5 enhanced swarm integration suggestions:
1. Multi-agent reasoning with specialized reasoners
2. Stigmergic signals encoding "this reasoning worked here"
3. MORK coordination for multi-perspective analysis
4. LEAP integration for exploratory search with self-reflection guidance
5. Hypothesis engine integration with analogical reasoning
"""

import re
import math
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class AgentRole(Enum):
    """Specialized agent roles"""
    DECOMPOSER = "decomposer"           # Breaks problems into subproblems
    ANALOGY_FINDER = "analogy_finder"   # Finds analogous problems
    HYPOTHESIS_GENERATOR = "hypothesis_generator"  # Generates hypotheses
    VERIFIER = "verifier"               # Verifies solutions
    SYNTHESIZER = "synthesizer"         # Synthesizes partial results
    EXPLORER = "explorer"               # Explores solution space
    CRITIC = "critic"                   # Critiques and finds flaws
    FORMALIZER = "formalizer"           # Formalizes reasoning


class SignalType(Enum):
    """Types of stigmergic signals"""
    SUCCESS = "success"           # This approach worked
    FAILURE = "failure"           # This approach failed
    PROMISING = "promising"       # This direction looks promising
    DEAD_END = "dead_end"         # This is a dead end
    ANALOGY = "analogy"           # Found useful analogy here
    INSIGHT = "insight"           # Key insight discovered
    CONFLICT = "conflict"         # Detected conflict/contradiction
    VERIFICATION = "verification"  # Verified result


class ConsensusMethod(Enum):
    """Methods for reaching consensus"""
    VOTING = "voting"
    WEIGHTED_VOTING = "weighted_voting"
    DEBATE = "debate"
    BAYESIAN = "bayesian"
    HIERARCHICAL = "hierarchical"


@dataclass
class ReasoningAgent:
    """A specialized reasoning agent"""
    agent_id: str
    role: AgentRole
    specialization: str  # Domain/category specialization

    # Agent state
    active: bool = True
    current_task: Optional[str] = None
    confidence: float = 0.5

    # Performance tracking
    tasks_completed: int = 0
    success_rate: float = 0.5

    # Resources
    reasoning_budget: int = 10  # Max reasoning steps
    tools_available: List[str] = field(default_factory=list)


@dataclass
class StigmergicSignal:
    """A stigmergic signal left by an agent"""
    signal_id: str
    signal_type: SignalType
    source_agent: str
    timestamp: float

    # Location in problem space
    problem_hash: str
    location: str  # Path/state in reasoning

    # Signal content
    content: Dict[str, Any]
    strength: float  # 0-1, decays over time
    relevance_scope: str  # "local", "category", "global"

    def decay(self, time_constant: float = 3600) -> float:
        """Calculate decayed strength"""
        age = time.time() - self.timestamp
        decay_factor = math.exp(-age / time_constant)
        return self.strength * decay_factor


@dataclass
class Perspective:
    """A perspective on a problem from MORK coordination"""
    perspective_id: str
    source: str  # Agent or knowledge source
    viewpoint: str  # Description of viewpoint
    analysis: str
    key_points: List[str]
    confidence: float
    supporting_evidence: List[str]
    potential_biases: List[str]


@dataclass
class HypothesisResult:
    """Result from hypothesis generation/testing"""
    hypothesis_id: str
    hypothesis: str
    source: str  # "direct", "analogical", "deductive"
    prior_probability: float
    posterior_probability: float
    evidence_for: List[str]
    evidence_against: List[str]
    status: str  # "pending", "supported", "refuted", "inconclusive"


class StigmergicEnvironment:
    """
    Environment for stigmergic coordination between agents.
    """

    def __init__(self, decay_constant: float = 3600):
        self.signals: Dict[str, StigmergicSignal] = {}
        self.decay_constant = decay_constant

        # Spatial indices
        self.by_problem: Dict[str, List[str]] = defaultdict(list)  # problem_hash -> signal_ids
        self.by_type: Dict[SignalType, List[str]] = defaultdict(list)
        self.by_location: Dict[str, List[str]] = defaultdict(list)

    def deposit_signal(self, agent_id: str, signal_type: SignalType,
                      problem_hash: str, location: str,
                      content: Dict[str, Any],
                      strength: float = 1.0,
                      scope: str = "local") -> str:
        """
        Deposit a stigmergic signal in the environment.

        Args:
            agent_id: ID of depositing agent
            signal_type: Type of signal
            problem_hash: Hash of current problem
            location: Location in reasoning space
            content: Signal content
            strength: Initial strength
            scope: Relevance scope

        Returns:
            Signal ID
        """
        signal_id = hashlib.md5(
            f"{agent_id}_{problem_hash}_{location}_{time.time()}".encode()
        ).hexdigest()[:12]

        signal = StigmergicSignal(
            signal_id=signal_id,
            signal_type=signal_type,
            source_agent=agent_id,
            timestamp=time.time(),
            problem_hash=problem_hash,
            location=location,
            content=content,
            strength=strength,
            relevance_scope=scope
        )

        self.signals[signal_id] = signal

        # Update indices
        self.by_problem[problem_hash].append(signal_id)
        self.by_type[signal_type].append(signal_id)
        self.by_location[location].append(signal_id)

        return signal_id

    def sense_signals(self, problem_hash: str, location: str = "",
                     signal_types: List[SignalType] = None,
                     radius: float = 1.0) -> List[StigmergicSignal]:
        """
        Sense signals in the environment.

        Args:
            problem_hash: Current problem hash
            location: Current location in reasoning
            signal_types: Types of signals to sense
            radius: Sensing radius (how far to look)

        Returns:
            List of relevant signals with current strength
        """
        relevant = []

        # Get signals for this problem
        signal_ids = set(self.by_problem.get(problem_hash, []))

        # Filter by type if specified
        if signal_types:
            type_ids = set()
            for st in signal_types:
                type_ids.update(self.by_type.get(st, []))
            signal_ids &= type_ids

        # Get signals and calculate current strength
        for sid in signal_ids:
            if sid in self.signals:
                signal = self.signals[sid]
                current_strength = signal.decay(self.decay_constant)

                # Filter by strength threshold
                if current_strength > 0.1:
                    # Create copy with decayed strength
                    relevant.append(StigmergicSignal(
                        signal_id=signal.signal_id,
                        signal_type=signal.signal_type,
                        source_agent=signal.source_agent,
                        timestamp=signal.timestamp,
                        problem_hash=signal.problem_hash,
                        location=signal.location,
                        content=signal.content,
                        strength=current_strength,
                        relevance_scope=signal.relevance_scope
                    ))

        # Sort by strength
        relevant.sort(key=lambda s: -s.strength)

        return relevant

    def get_success_signals(self, problem_hash: str) -> List[StigmergicSignal]:
        """Get success signals for a problem"""
        return self.sense_signals(
            problem_hash,
            signal_types=[SignalType.SUCCESS, SignalType.PROMISING, SignalType.INSIGHT]
        )

    def get_warning_signals(self, problem_hash: str) -> List[StigmergicSignal]:
        """Get warning signals for a problem"""
        return self.sense_signals(
            problem_hash,
            signal_types=[SignalType.FAILURE, SignalType.DEAD_END, SignalType.CONFLICT]
        )

    def cleanup_old_signals(self, max_age: float = 86400):
        """Remove signals older than max_age seconds"""
        current_time = time.time()
        to_remove = []

        for sid, signal in self.signals.items():
            if current_time - signal.timestamp > max_age:
                to_remove.append(sid)

        for sid in to_remove:
            signal = self.signals[sid]
            del self.signals[sid]
            # Clean indices
            self.by_problem[signal.problem_hash] = [
                s for s in self.by_problem[signal.problem_hash] if s != sid
            ]
            self.by_type[signal.signal_type] = [
                s for s in self.by_type[signal.signal_type] if s != sid
            ]


class MultiPerspectiveIntegrator:
    """
    Integrates multiple perspectives on a problem (MORK coordination).
    """

    def __init__(self):
        self.perspectives: Dict[str, List[Perspective]] = {}  # problem_hash -> perspectives

    def add_perspective(self, problem_hash: str, perspective: Perspective):
        """Add a perspective on a problem"""
        if problem_hash not in self.perspectives:
            self.perspectives[problem_hash] = []
        self.perspectives[problem_hash].append(perspective)

    def generate_perspectives(self, problem: str, category: str = "") -> List[Perspective]:
        """
        Generate multiple perspectives on a problem.

        Args:
            problem: The problem text
            category: Optional category

        Returns:
            List of different perspectives
        """
        perspectives = []

        # Domain expert perspective
        perspectives.append(self._domain_perspective(problem, category))

        # Methodological perspective
        perspectives.append(self._methodological_perspective(problem))

        # Critical perspective
        perspectives.append(self._critical_perspective(problem))

        # Historical/analogical perspective
        perspectives.append(self._analogical_perspective(problem))

        return perspectives

    def _domain_perspective(self, problem: str, category: str) -> Perspective:
        """Generate domain expert perspective"""
        # Analyze from domain-specific viewpoint
        domain_keywords = self._extract_domain_keywords(problem, category)

        return Perspective(
            perspective_id=f"domain_{hashlib.md5(problem[:50].encode()).hexdigest()[:8]}",
            source="domain_expert",
            viewpoint=f"Domain expertise in {category or 'general'}",
            analysis=f"From a {category or 'domain'} perspective, this problem involves: {', '.join(domain_keywords[:5])}",
            key_points=[f"Key domain concept: {kw}" for kw in domain_keywords[:3]],
            confidence=0.7,
            supporting_evidence=[f"Domain knowledge of {kw}" for kw in domain_keywords[:2]],
            potential_biases=["May overlook cross-domain connections"]
        )

    def _methodological_perspective(self, problem: str) -> Perspective:
        """Generate methodological perspective"""
        # Analyze methodology/approach
        methods = self._identify_applicable_methods(problem)

        return Perspective(
            perspective_id=f"method_{hashlib.md5(problem[:50].encode()).hexdigest()[:8]}",
            source="methodology_expert",
            viewpoint="Methodological analysis",
            analysis=f"Applicable methods: {', '.join(methods[:3])}",
            key_points=[f"Consider using {m}" for m in methods[:3]],
            confidence=0.6,
            supporting_evidence=["Method applicability analysis"],
            potential_biases=["May favor familiar methods"]
        )

    def _critical_perspective(self, problem: str) -> Perspective:
        """Generate critical perspective"""
        # Look for potential issues
        issues = self._identify_potential_issues(problem)

        return Perspective(
            perspective_id=f"critic_{hashlib.md5(problem[:50].encode()).hexdigest()[:8]}",
            source="critic",
            viewpoint="Critical analysis",
            analysis=f"Potential issues: {', '.join(issues[:3])}",
            key_points=issues[:3],
            confidence=0.5,
            supporting_evidence=["Critical analysis"],
            potential_biases=["May be overly pessimistic"]
        )

    def _analogical_perspective(self, problem: str) -> Perspective:
        """Generate analogical perspective"""
        # Look for analogies
        analogies = self._identify_analogies(problem)

        return Perspective(
            perspective_id=f"analogy_{hashlib.md5(problem[:50].encode()).hexdigest()[:8]}",
            source="analogist",
            viewpoint="Analogical reasoning",
            analysis=f"Potential analogies: {', '.join(analogies[:3])}",
            key_points=[f"Similar to {a}" for a in analogies[:3]],
            confidence=0.5,
            supporting_evidence=["Pattern matching"],
            potential_biases=["Analogies may not fully transfer"]
        )

    def _extract_domain_keywords(self, problem: str, category: str) -> List[str]:
        """Extract domain-specific keywords"""
        domain_terms = {
            'math': ['equation', 'prove', 'calculate', 'theorem', 'formula', 'integral'],
            'physics': ['force', 'energy', 'velocity', 'momentum', 'wave', 'field'],
            'chemistry': ['molecule', 'reaction', 'element', 'bond', 'compound'],
            'biology': ['cell', 'gene', 'protein', 'species', 'organism'],
            'cs': ['algorithm', 'function', 'data', 'program', 'complexity'],
        }

        words = set(problem.lower().split())
        keywords = []

        for domain, terms in domain_terms.items():
            for term in terms:
                if term in words:
                    keywords.append(term)

        return keywords if keywords else ['general']

    def _identify_applicable_methods(self, problem: str) -> List[str]:
        """Identify applicable methods"""
        methods = []
        problem_lower = problem.lower()

        if 'prove' in problem_lower or 'show that' in problem_lower:
            methods.append('formal_proof')
        if 'calculate' in problem_lower or any(c.isdigit() for c in problem):
            methods.append('calculation')
        if 'why' in problem_lower or 'cause' in problem_lower:
            methods.append('causal_reasoning')
        if 'compare' in problem_lower or 'difference' in problem_lower:
            methods.append('comparison')
        if 'how' in problem_lower:
            methods.append('procedural_analysis')

        return methods if methods else ['general_reasoning']

    def _identify_potential_issues(self, problem: str) -> List[str]:
        """Identify potential issues"""
        issues = []
        problem_lower = problem.lower()

        if len(problem.split()) > 100:
            issues.append("Problem is complex, may need decomposition")
        if '?' not in problem:
            issues.append("Goal not explicitly stated as question")
        if any(word in problem_lower for word in ['always', 'never', 'all', 'none']):
            issues.append("Contains absolute quantifiers - check edge cases")

        return issues if issues else ["No obvious issues detected"]

    def _identify_analogies(self, problem: str) -> List[str]:
        """Identify potential analogies"""
        analogies = []
        problem_lower = problem.lower()

        if 'rate' in problem_lower or 'speed' in problem_lower:
            analogies.append("rate problems (distance/time, growth)")
        if 'balance' in problem_lower or 'equilibrium' in problem_lower:
            analogies.append("equilibrium problems")
        if 'optimize' in problem_lower or 'maximum' in problem_lower or 'minimum' in problem_lower:
            analogies.append("optimization problems")

        return analogies if analogies else ["general problem patterns"]

    def integrate_perspectives(self, perspectives: List[Perspective]) -> Dict[str, Any]:
        """
        Integrate multiple perspectives into unified analysis.

        Args:
            perspectives: List of perspectives to integrate

        Returns:
            Integrated analysis
        """
        # Collect all key points
        all_points = []
        for p in perspectives:
            all_points.extend([(point, p.confidence) for point in p.key_points])

        # Weight by confidence
        weighted_points = defaultdict(float)
        for point, conf in all_points:
            weighted_points[point] += conf

        # Sort by weight
        sorted_points = sorted(weighted_points.items(), key=lambda x: -x[1])

        # Find consensus and conflicts
        consensus_points = [p for p, w in sorted_points if w > 1.0]
        unique_points = [p for p, w in sorted_points if w <= 0.6]

        # Calculate overall confidence
        avg_confidence = sum(p.confidence for p in perspectives) / len(perspectives)

        # Identify potential biases
        all_biases = []
        for p in perspectives:
            all_biases.extend(p.potential_biases)

        return {
            'key_points': [p for p, _ in sorted_points[:5]],
            'consensus': consensus_points,
            'unique_insights': unique_points[:3],
            'confidence': avg_confidence,
            'perspectives_count': len(perspectives),
            'potential_biases': list(set(all_biases)),
            'recommendation': self._generate_recommendation(perspectives)
        }

    def _generate_recommendation(self, perspectives: List[Perspective]) -> str:
        """Generate recommendation from perspectives"""
        # Find highest confidence perspective
        best = max(perspectives, key=lambda p: p.confidence)
        return f"Primary approach: {best.viewpoint} (confidence: {best.confidence:.2f})"


class ConsensusBuilder:
    """
    Builds consensus among multiple agents/perspectives.
    """

    def __init__(self, method: ConsensusMethod = ConsensusMethod.WEIGHTED_VOTING):
        self.method = method

    def build_consensus(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build consensus from multiple proposals.

        Args:
            proposals: List of {answer, confidence, reasoning, source}

        Returns:
            Consensus result
        """
        if not proposals:
            return {'answer': None, 'confidence': 0.0, 'method': 'none'}

        if self.method == ConsensusMethod.VOTING:
            return self._simple_voting(proposals)
        elif self.method == ConsensusMethod.WEIGHTED_VOTING:
            return self._weighted_voting(proposals)
        elif self.method == ConsensusMethod.BAYESIAN:
            return self._bayesian_consensus(proposals)
        else:
            return self._weighted_voting(proposals)

    def _simple_voting(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Simple majority voting"""
        votes = defaultdict(int)
        for p in proposals:
            answer = str(p.get('answer', '')).lower().strip()
            votes[answer] += 1

        if not votes:
            return {'answer': None, 'confidence': 0.0, 'method': 'voting'}

        winner = max(votes.items(), key=lambda x: x[1])
        confidence = winner[1] / len(proposals)

        return {
            'answer': winner[0],
            'confidence': confidence,
            'vote_count': winner[1],
            'total_votes': len(proposals),
            'method': 'voting'
        }

    def _weighted_voting(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Voting weighted by confidence"""
        weighted_votes = defaultdict(float)
        total_weight = 0

        for p in proposals:
            answer = str(p.get('answer', '')).lower().strip()
            weight = p.get('confidence', 0.5)
            weighted_votes[answer] += weight
            total_weight += weight

        if not weighted_votes or total_weight == 0:
            return {'answer': None, 'confidence': 0.0, 'method': 'weighted_voting'}

        winner = max(weighted_votes.items(), key=lambda x: x[1])
        confidence = winner[1] / total_weight

        return {
            'answer': winner[0],
            'confidence': confidence,
            'weighted_score': winner[1],
            'total_weight': total_weight,
            'method': 'weighted_voting'
        }

    def _bayesian_consensus(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Bayesian combination of evidence"""
        # Collect all unique answers
        answers = set(str(p.get('answer', '')).lower().strip() for p in proposals)

        # Calculate posterior for each answer
        posteriors = {}
        for answer in answers:
            # Prior: uniform
            log_posterior = math.log(1.0 / len(answers)) if answers else 0

            # Update with each proposal
            for p in proposals:
                p_answer = str(p.get('answer', '')).lower().strip()
                confidence = p.get('confidence', 0.5)

                if p_answer == answer:
                    # Evidence for this answer
                    log_posterior += math.log(confidence + 0.01)
                else:
                    # Evidence against
                    log_posterior += math.log((1 - confidence) / max(len(answers) - 1, 1) + 0.01)

            posteriors[answer] = log_posterior

        # Convert to probabilities
        max_log = max(posteriors.values()) if posteriors else 0
        exp_posteriors = {a: math.exp(lp - max_log) for a, lp in posteriors.items()}
        total = sum(exp_posteriors.values())
        probabilities = {a: ep / total for a, ep in exp_posteriors.items()} if total > 0 else {}

        if not probabilities:
            return {'answer': None, 'confidence': 0.0, 'method': 'bayesian'}

        winner = max(probabilities.items(), key=lambda x: x[1])

        return {
            'answer': winner[0],
            'confidence': winner[1],
            'all_probabilities': probabilities,
            'method': 'bayesian'
        }


class HypothesisSwarm:
    """
    Integrates hypothesis generation with analogical reasoning.
    """

    def __init__(self):
        self.hypotheses: Dict[str, HypothesisResult] = {}

    def generate_hypotheses(self, problem: str, analogies: List[Dict] = None,
                           domain_knowledge: Dict = None) -> List[HypothesisResult]:
        """
        Generate hypotheses from multiple sources.

        Args:
            problem: Problem text
            analogies: Analogies from analogical reasoner
            domain_knowledge: Domain-specific knowledge

        Returns:
            List of hypotheses
        """
        hypotheses = []

        # Direct hypotheses from problem analysis
        direct = self._generate_direct_hypotheses(problem)
        hypotheses.extend(direct)

        # Analogical hypotheses
        if analogies:
            analogical = self._generate_analogical_hypotheses(problem, analogies)
            hypotheses.extend(analogical)

        # Deductive hypotheses from domain knowledge
        if domain_knowledge:
            deductive = self._generate_deductive_hypotheses(problem, domain_knowledge)
            hypotheses.extend(deductive)

        # Store hypotheses
        for h in hypotheses:
            self.hypotheses[h.hypothesis_id] = h

        return hypotheses

    def _generate_direct_hypotheses(self, problem: str) -> List[HypothesisResult]:
        """Generate hypotheses directly from problem"""
        hypotheses = []
        problem_lower = problem.lower()

        # Look for question patterns
        if 'what is' in problem_lower:
            # Value/definition question
            target = re.search(r'what is (?:the )?(.+?)(?:\?|$)', problem_lower)
            if target:
                hypotheses.append(HypothesisResult(
                    hypothesis_id=f"direct_{hashlib.md5(problem[:30].encode()).hexdigest()[:8]}",
                    hypothesis=f"The answer involves determining: {target.group(1)}",
                    source="direct",
                    prior_probability=0.6,
                    posterior_probability=0.6,
                    evidence_for=["Direct question analysis"],
                    evidence_against=[],
                    status="pending"
                ))

        if 'how' in problem_lower:
            # Process/method question
            hypotheses.append(HypothesisResult(
                hypothesis_id=f"direct_how_{hashlib.md5(problem[:30].encode()).hexdigest()[:8]}",
                hypothesis="The answer requires procedural/methodological explanation",
                source="direct",
                prior_probability=0.5,
                posterior_probability=0.5,
                evidence_for=["How-question detected"],
                evidence_against=[],
                status="pending"
            ))

        return hypotheses

    def _generate_analogical_hypotheses(self, problem: str,
                                       analogies: List[Dict]) -> List[HypothesisResult]:
        """Generate hypotheses from analogies"""
        hypotheses = []

        for analogy in analogies[:3]:  # Top 3 analogies
            similarity = analogy.get('similarity', 0.5)
            source = analogy.get('source', '')[:100]

            hypotheses.append(HypothesisResult(
                hypothesis_id=f"analogy_{hashlib.md5(source.encode()).hexdigest()[:8]}",
                hypothesis=f"Solution pattern similar to: {source}",
                source="analogical",
                prior_probability=similarity * 0.8,
                posterior_probability=similarity * 0.8,
                evidence_for=[f"Structural similarity: {similarity:.2f}"],
                evidence_against=["Analogy may not fully transfer"],
                status="pending"
            ))

        return hypotheses

    def _generate_deductive_hypotheses(self, problem: str,
                                      domain_knowledge: Dict) -> List[HypothesisResult]:
        """Generate hypotheses from domain knowledge"""
        hypotheses = []

        # Look for applicable rules/facts
        rules = domain_knowledge.get('rules', [])
        facts = domain_knowledge.get('facts', [])

        for rule in rules[:2]:
            hypotheses.append(HypothesisResult(
                hypothesis_id=f"deductive_{hashlib.md5(str(rule)[:30].encode()).hexdigest()[:8]}",
                hypothesis=f"Apply rule: {str(rule)[:100]}",
                source="deductive",
                prior_probability=0.7,
                posterior_probability=0.7,
                evidence_for=["Domain rule applicable"],
                evidence_against=[],
                status="pending"
            ))

        return hypotheses

    def evaluate_hypothesis(self, hypothesis_id: str, evidence: Dict[str, Any]) -> HypothesisResult:
        """
        Evaluate a hypothesis against new evidence.

        Args:
            hypothesis_id: Hypothesis to evaluate
            evidence: New evidence {support: float, against: float, description: str}

        Returns:
            Updated hypothesis
        """
        if hypothesis_id not in self.hypotheses:
            return None

        h = self.hypotheses[hypothesis_id]

        # Bayesian update
        support = evidence.get('support', 0.5)
        against = evidence.get('against', 0.5)

        # Update posterior
        likelihood_ratio = support / (against + 0.01)
        prior_odds = h.posterior_probability / (1 - h.posterior_probability + 0.01)
        posterior_odds = prior_odds * likelihood_ratio
        h.posterior_probability = posterior_odds / (1 + posterior_odds)

        # Update evidence lists
        if 'description' in evidence:
            if support > 0.5:
                h.evidence_for.append(evidence['description'])
            else:
                h.evidence_against.append(evidence['description'])

        # Update status
        if h.posterior_probability > 0.8:
            h.status = "supported"
        elif h.posterior_probability < 0.2:
            h.status = "refuted"
        else:
            h.status = "inconclusive"

        return h

    def get_best_hypothesis(self) -> Optional[HypothesisResult]:
        """Get hypothesis with highest posterior probability"""
        if not self.hypotheses:
            return None
        return max(self.hypotheses.values(), key=lambda h: h.posterior_probability)


class SwarmReasoningOrchestrator:
    """
    Main swarm reasoning orchestrator.

    Coordinates all swarm components:
    - Multi-agent reasoning
    - Stigmergic coordination
    - Multi-perspective analysis
    - Hypothesis generation
    - Consensus building
    """

    def __init__(self, num_agents: int = 5):
        # Stigmergic environment
        self.environment = StigmergicEnvironment()

        # Multi-perspective integrator
        self.perspective_integrator = MultiPerspectiveIntegrator()

        # Consensus builder
        self.consensus_builder = ConsensusBuilder(ConsensusMethod.BAYESIAN)

        # Hypothesis swarm
        self.hypothesis_swarm = HypothesisSwarm()

        # Agents
        self.agents = self._create_agents(num_agents)

        # Statistics
        self.stats = {
            'problems_processed': 0,
            'signals_deposited': 0,
            'perspectives_generated': 0,
            'hypotheses_generated': 0,
            'consensus_built': 0
        }

    def _create_agents(self, num_agents: int) -> List[ReasoningAgent]:
        """Create specialized agents"""
        roles = list(AgentRole)
        agents = []

        for i in range(num_agents):
            role = roles[i % len(roles)]
            agent = ReasoningAgent(
                agent_id=f"agent_{i}_{role.value}",
                role=role,
                specialization="general"
            )
            agents.append(agent)

        return agents

    def process_problem(self, problem: str, category: str = "",
                       analogies: List[Dict] = None,
                       domain_knowledge: Dict = None) -> Dict[str, Any]:
        """
        Process a problem using swarm intelligence.

        Args:
            problem: Problem text
            category: Optional category
            analogies: Analogies from analogical reasoner
            domain_knowledge: Domain knowledge

        Returns:
            Comprehensive swarm result
        """
        self.stats['problems_processed'] += 1
        problem_hash = hashlib.md5(problem.encode()).hexdigest()[:16]

        # 1. Generate multiple perspectives (MORK coordination)
        perspectives = self.perspective_integrator.generate_perspectives(problem, category)
        self.stats['perspectives_generated'] += len(perspectives)

        # 2. Generate hypotheses (with analogical integration)
        hypotheses = self.hypothesis_swarm.generate_hypotheses(
            problem, analogies, domain_knowledge
        )
        self.stats['hypotheses_generated'] += len(hypotheses)

        # 3. Check stigmergic signals from previous problems
        success_signals = self.environment.get_success_signals(problem_hash)
        warning_signals = self.environment.get_warning_signals(problem_hash)

        # 4. Run agents in parallel
        agent_results = self._run_agents(problem, category, perspectives, hypotheses)

        # 5. Build consensus
        consensus = self.consensus_builder.build_consensus(agent_results)
        self.stats['consensus_built'] += 1

        # 6. Deposit signals based on results
        self._deposit_signals(problem_hash, consensus, agent_results)

        # 7. Integrate perspectives
        integrated_perspectives = self.perspective_integrator.integrate_perspectives(perspectives)

        # 8. Get best hypothesis
        best_hypothesis = self.hypothesis_swarm.get_best_hypothesis()

        return {
            'consensus': consensus,
            'agent_results': agent_results,
            'perspectives': integrated_perspectives,
            'best_hypothesis': best_hypothesis.hypothesis if best_hypothesis else None,
            'hypothesis_confidence': best_hypothesis.posterior_probability if best_hypothesis else 0.5,
            'success_signals': len(success_signals),
            'warning_signals': len(warning_signals),
            'signals_guidance': self._interpret_signals(success_signals, warning_signals),
            'final_answer': consensus['answer'],
            'final_confidence': consensus['confidence']
        }

    def _run_agents(self, problem: str, category: str,
                   perspectives: List[Perspective],
                   hypotheses: List[HypothesisResult]) -> List[Dict]:
        """Run agents to generate proposals"""
        results = []

        for agent in self.agents:
            result = self._run_single_agent(agent, problem, category, perspectives, hypotheses)
            if result:
                results.append(result)

        return results
