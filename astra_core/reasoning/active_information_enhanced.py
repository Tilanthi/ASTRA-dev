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
Phase 3: Active Information Seeking Module

Enables intelligent, targeted information gathering:
- Gap identification in current knowledge
- Query formulation for targeted information retrieval
- Information integration into reasoning
- Sufficiency assessment to know when to stop seeking
"""

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
from collections import defaultdict


class GapType(Enum):
    """Types of knowledge gaps"""
    FACTUAL = "factual"           # Missing factual information
    DEFINITIONAL = "definitional"  # Need definition/clarification
    PROCEDURAL = "procedural"     # Don't know how to do something
    CAUSAL = "causal"             # Don't understand why
    CONTEXTUAL = "contextual"     # Missing context
    NUMERICAL = "numerical"       # Need specific numbers/data
    TEMPORAL = "temporal"         # Missing time/sequence info
    RELATIONAL = "relational"     # Missing relationship info


class QueryType(Enum):
    """Types of information queries"""
    DEFINITION = "definition"     # What is X?
    FACTUAL = "factual"          # Is X true?
    NUMERICAL = "numerical"      # What is the value of X?
    PROCEDURAL = "procedural"    # How to do X?
    CAUSAL = "causal"            # Why does X happen?
    COMPARATIVE = "comparative"  # How does X compare to Y?
    EXAMPLE = "example"          # Give example of X
    VERIFICATION = "verification"  # Verify X


class InformationSource(Enum):
    """Potential sources of information"""
    INTERNAL_KNOWLEDGE = "internal"
    EXTERNAL_API = "external_api"
    CALCULATION = "calculation"
    INFERENCE = "inference"
    CONTEXT = "context"
    USER = "user"


@dataclass
class KnowledgeGap:
    """Represents a gap in knowledge"""
    gap_type: GapType
    description: str
    context: str
    importance: float  # 0-1, how critical for solving
    topic: str
    specific_question: str
    potential_sources: List[InformationSource] = field(default_factory=list)


@dataclass
class InformationQuery:
    """A query to fill a knowledge gap"""
    query_type: QueryType
    query_text: str
    target_gap: Optional[KnowledgeGap] = None
    source_preference: List[InformationSource] = field(default_factory=list)
    expected_format: str = ""
    priority: float = 0.5
    constraints: List[str] = field(default_factory=list)


@dataclass
class RetrievedInformation:
    """Information retrieved from a source"""
    query: InformationQuery
    source: InformationSource
    content: str
    confidence: float
    relevance: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeState:
    """Current state of knowledge about a problem"""
    known_facts: List[str]
    known_constraints: List[str]
    known_relations: List[Tuple[str, str, str]]  # (entity1, relation, entity2)
    gaps: List[KnowledgeGap]
    retrieved: List[RetrievedInformation]
    completeness: float  # 0-1 estimate
    last_updated: float = 0.0


class GapAnalyzer:
    """
    Analyzes problems to identify knowledge gaps.
    """

    def __init__(self):
        # Patterns indicating knowledge gaps
        self.gap_indicators = {
            GapType.FACTUAL: [
                r"what (?:is|are|was|were) (?:the )?([\w\s]+)",
                r"which ([\w\s]+)",
                r"who (?:is|was|are|were) ([\w\s]+)",
            ],
            GapType.DEFINITIONAL: [
                r"define ([\w\s]+)",
                r"meaning of ([\w\s]+)",
                r"what does ([\w\s]+) mean",
            ],
            GapType.NUMERICAL: [
                r"how (?:many|much) ([\w\s]+)",
                r"what (?:is|are) the (?:number|value|amount) of ([\w\s]+)",
                r"calculate ([\w\s]+)",
            ],
            GapType.CAUSAL: [
                r"why (?:does|do|is|are|did|was|were) ([\w\s]+)",
                r"what causes? ([\w\s]+)",
                r"reason for ([\w\s]+)",
            ],
            GapType.PROCEDURAL: [
                r"how to ([\w\s]+)",
                r"how (?:can|do|should) (?:I|we|you) ([\w\s]+)",
                r"steps? to ([\w\s]+)",
            ],
            GapType.TEMPORAL: [
                r"when (?:did|does|is|was|were) ([\w\s]+)",
                r"what (?:time|date|year|period) ([\w\s]+)",
            ],
            GapType.RELATIONAL: [
                r"how (?:is|are|does|do) ([\w\s]+) related to ([\w\s]+)",
                r"relationship between ([\w\s]+) and ([\w\s]+)",
                r"connection between ([\w\s]+) and ([\w\s]+)",
            ],
        }

        # Keywords suggesting uncertainty
        self.uncertainty_keywords = [
            'unknown', 'unclear', 'uncertain', 'not sure', 'need to know',
            'missing', 'lacking', 'insufficient', 'incomplete'
        ]

    def identify_gaps(self, problem: str, reasoning_trace: List[str] = None,
                     current_knowledge: Dict[str, Any] = None) -> List[KnowledgeGap]:
        """
        Identify knowledge gaps in problem and reasoning.

        Args:
            problem: The problem text
            reasoning_trace: Optional reasoning steps so far
            current_knowledge: Optional dict of known facts

        Returns:
            List of identified knowledge gaps
        """
        gaps = []

        # Analyze problem for explicit information needs
        gaps.extend(self._analyze_problem(problem))

        # Analyze reasoning for implicit gaps
        if reasoning_trace:
            gaps.extend(self._analyze_reasoning(reasoning_trace))

        # Find gaps relative to current knowledge
        if current_knowledge:
            gaps.extend(self._find_knowledge_gaps(problem, current_knowledge))

        # Deduplicate and prioritize
        gaps = self._deduplicate_gaps(gaps)
        gaps = self._prioritize_gaps(gaps, problem)

        return gaps

    def _analyze_problem(self, problem: str) -> List[KnowledgeGap]:
        """Analyze problem for explicit information needs"""
        gaps = []
        problem_lower = problem.lower()

        for gap_type, patterns in self.gap_indicators.items():
            for pattern in patterns:
                matches = re.findall(pattern, problem_lower, re.IGNORECASE)
                for match in matches:
                    topic = match if isinstance(match, str) else match[0]
                    topic = topic.strip()

                    # Determine importance based on position and question type
                    importance = 0.7 if '?' in problem else 0.5

                    # Generate specific question
                    specific_question = self._generate_specific_question(
                        gap_type, topic, problem
                    )

                    gaps.append(KnowledgeGap(
                        gap_type=gap_type,
                        description=f"Need {gap_type.value} information about {topic}",
                        context=problem[:100],
                        importance=importance,
                        topic=topic,
                        specific_question=specific_question,
                        potential_sources=self._suggest_sources(gap_type)
                    ))

        return gaps

    def _analyze_reasoning(self, reasoning_trace: List[str]) -> List[KnowledgeGap]:
        """Analyze reasoning trace for implicit gaps"""
        gaps = []

        combined = ' '.join(reasoning_trace).lower()

        # Check for uncertainty indicators
        for keyword in self.uncertainty_keywords:
            if keyword in combined:
                # Find context around uncertainty
                for step in reasoning_trace:
                    if keyword in step.lower():
                        # Extract the uncertain topic
                        context = self._extract_uncertainty_context(step, keyword)
                        if context:
                            gaps.append(KnowledgeGap(
                                gap_type=GapType.FACTUAL,
                                description=f"Uncertainty about: {context}",
                                context=step[:100],
                                importance=0.6,
                                topic=context,
                                specific_question=f"What is {context}?",
                                potential_sources=[InformationSource.EXTERNAL_API,
                                                 InformationSource.INTERNAL_KNOWLEDGE]
                            ))
                        break

        # Check for incomplete reasoning chains
        transition_words = ['therefore', 'thus', 'hence', 'so', 'because']
        for i, step in enumerate(reasoning_trace):
            if any(tw in step.lower() for tw in transition_words):
                # Check if next step exists and follows logically
                if i == len(reasoning_trace) - 1:
                    gaps.append(KnowledgeGap(
                        gap_type=GapType.PROCEDURAL,
                        description="Reasoning chain incomplete",
                        context=step[:100],
                        importance=0.7,
                        topic="next reasoning step",
                        specific_question="What follows from this reasoning?",
                        potential_sources=[InformationSource.INFERENCE]
                    ))

        return gaps

    def _find_knowledge_gaps(self, problem: str,
                            current_knowledge: Dict[str, Any]) -> List[KnowledgeGap]:
        """Find gaps relative to current knowledge"""
        gaps = []

        # Extract entities from problem
        entities = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', problem)
        entities.extend(re.findall(r'\b([a-z]+(?:\s+[a-z]+){0,2})\b', problem.lower()))

        # Filter to meaningful entities
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'and', 'or'}
        entities = [e for e in entities if e.lower() not in stopwords and len(e) > 2]

        # Check which entities are not in current knowledge
        known_topics = set(str(k).lower() for k in current_knowledge.keys())

        for entity in entities[:10]:  # Limit
            if entity.lower() not in known_topics:
                # Check if any known topic contains this entity
                if not any(entity.lower() in kt for kt in known_topics):
                    gaps.append(KnowledgeGap(
                        gap_type=GapType.FACTUAL,
                        description=f"No knowledge about: {entity}",
                        context=problem[:100],
                        importance=0.5,
                        topic=entity,
                        specific_question=f"What is {entity}?",
                        potential_sources=[InformationSource.EXTERNAL_API,
                                         InformationSource.INTERNAL_KNOWLEDGE]
                    ))

        return gaps

    def _generate_specific_question(self, gap_type: GapType, topic: str, problem: str) -> str:
        """Generate a specific question to fill the gap"""
        templates = {
            GapType.FACTUAL: f"What is {topic}?",
            GapType.DEFINITIONAL: f"Define {topic}.",
            GapType.NUMERICAL: f"What is the numerical value of {topic}?",
            GapType.CAUSAL: f"Why does {topic} occur?",
            GapType.PROCEDURAL: f"How do you {topic}?",
            GapType.TEMPORAL: f"When does/did {topic}?",
            GapType.RELATIONAL: f"How is {topic} related?",
            GapType.CONTEXTUAL: f"What is the context for {topic}?",
        }
        return templates.get(gap_type, f"Tell me about {topic}")

    def _suggest_sources(self, gap_type: GapType) -> List[InformationSource]:
        """Suggest information sources for a gap type"""
        source_map = {
            GapType.FACTUAL: [InformationSource.EXTERNAL_API, InformationSource.INTERNAL_KNOWLEDGE],
            GapType.DEFINITIONAL: [InformationSource.INTERNAL_KNOWLEDGE, InformationSource.EXTERNAL_API],
            GapType.NUMERICAL: [InformationSource.CALCULATION, InformationSource.EXTERNAL_API],
            GapType.CAUSAL: [InformationSource.INFERENCE, InformationSource.EXTERNAL_API],
            GapType.PROCEDURAL: [InformationSource.INTERNAL_KNOWLEDGE, InformationSource.EXTERNAL_API],
            GapType.TEMPORAL: [InformationSource.EXTERNAL_API, InformationSource.CONTEXT],
            GapType.RELATIONAL: [InformationSource.INFERENCE, InformationSource.EXTERNAL_API],
            GapType.CONTEXTUAL: [InformationSource.CONTEXT, InformationSource.USER],
        }
        return source_map.get(gap_type, [InformationSource.EXTERNAL_API])

    def _extract_uncertainty_context(self, text: str, keyword: str) -> Optional[str]:
        """Extract context around uncertainty keyword"""
        idx = text.lower().find(keyword)
        if idx == -1:
            return None

        # Get surrounding text
        start = max(0, idx - 30)
        end = min(len(text), idx + len(keyword) + 30)
        context = text[start:end].strip()

        # Extract key noun phrase
        words = context.split()
        # Find nouns after the keyword
        key_idx = next((i for i, w in enumerate(words) if keyword in w.lower()), 0)
        if key_idx < len(words) - 1:
            return ' '.join(words[key_idx+1:key_idx+4])

        return context[:30]

    def _deduplicate_gaps(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """Remove duplicate gaps"""
        seen = set()
        unique = []

        for gap in gaps:
            key = (gap.topic.lower(), gap.gap_type)
            if key not in seen:
                seen.add(key)
                unique.append(gap)

        return unique

    def _prioritize_gaps(self, gaps: List[KnowledgeGap], problem: str) -> List[KnowledgeGap]:
        """Prioritize gaps by importance"""
        problem_lower = problem.lower()

        for gap in gaps:
            # Boost importance if topic appears multiple times in problem
            mentions = problem_lower.count(gap.topic.lower())
            gap.importance = min(1.0, gap.importance + 0.1 * mentions)

            # Boost importance for certain gap types in questions
            if '?' in problem and gap.gap_type in [GapType.FACTUAL, GapType.NUMERICAL]:
                gap.importance = min(1.0, gap.importance + 0.15)

        # Sort by importance
        gaps.sort(key=lambda g: g.importance, reverse=True)

        return gaps


class QueryFormulator:
    """
    Formulates queries to fill knowledge gaps.
    """

    def __init__(self):
        self.query_templates = {
            QueryType.DEFINITION: [
                "Define {topic}",
                "What is the definition of {topic}",
                "What does {topic} mean",
            ],
            QueryType.FACTUAL: [
                "What is {topic}",
                "Tell me about {topic}",
                "{topic} facts",
            ],
            QueryType.NUMERICAL: [
                "Value of {topic}",
                "Calculate {topic}",
                "{topic} numerical value",
            ],
            QueryType.PROCEDURAL: [
                "How to {topic}",
                "Steps for {topic}",
                "Method for {topic}",
            ],
            QueryType.CAUSAL: [
                "Why {topic}",
                "Cause of {topic}",
                "Reason for {topic}",
            ],
            QueryType.COMPARATIVE: [
                "Compare {topic}",
                "{topic} comparison",
                "Difference between {topic}",
            ],
            QueryType.EXAMPLE: [
                "Example of {topic}",
                "{topic} examples",
                "Instance of {topic}",
            ],
            QueryType.VERIFICATION: [
                "Is {topic} true",
                "Verify {topic}",
                "Check {topic}",
            ],
        }

    def formulate_queries(self, gaps: List[KnowledgeGap],
                         max_queries: int = 5) -> List[InformationQuery]:
        """
        Formulate queries for knowledge gaps.

        Args:
            gaps: List of knowledge gaps
            max_queries: Maximum number of queries to generate

        Returns:
            List of information queries
        """
        queries = []

        for gap in gaps[:max_queries]:
            query = self._formulate_query(gap)
            if query:
                queries.append(query)

        return queries

    def _formulate_query(self, gap: KnowledgeGap) -> InformationQuery:
        """Formulate a query for a single gap"""
        # Map gap type to query type
        query_type = self._map_gap_to_query_type(gap.gap_type)

        # Generate query text
        templates = self.query_templates.get(query_type, self.query_templates[QueryType.FACTUAL])
        query_text = templates[0].format(topic=gap.topic)

        # Determine expected format
        expected_format = self._determine_expected_format(gap.gap_type)

        return InformationQuery(
            query_type=query_type,
            query_text=query_text,
            target_gap=gap,
            source_preference=gap.potential_sources,
            expected_format=expected_format,
            priority=gap.importance,
            constraints=[]
        )

    def _map_gap_to_query_type(self, gap_type: GapType) -> QueryType:
        """Map gap type to appropriate query type"""
        mapping = {
            GapType.FACTUAL: QueryType.FACTUAL,
            GapType.DEFINITIONAL: QueryType.DEFINITION,
            GapType.NUMERICAL: QueryType.NUMERICAL,
            GapType.CAUSAL: QueryType.CAUSAL,
            GapType.PROCEDURAL: QueryType.PROCEDURAL,
            GapType.TEMPORAL: QueryType.FACTUAL,
            GapType.RELATIONAL: QueryType.FACTUAL,
            GapType.CONTEXTUAL: QueryType.FACTUAL,
        }
        return mapping.get(gap_type, QueryType.FACTUAL)

    def _determine_expected_format(self, gap_type: GapType) -> str:
        """Determine expected format for response"""
        format_map = {
            GapType.FACTUAL: "brief factual statement",
            GapType.DEFINITIONAL: "definition with key properties",
            GapType.NUMERICAL: "numerical value with units",
            GapType.CAUSAL: "causal explanation",
            GapType.PROCEDURAL: "step-by-step procedure",
            GapType.TEMPORAL: "time/date specification",
            GapType.RELATIONAL: "relationship description",
            GapType.CONTEXTUAL: "contextual background",
        }
        return format_map.get(gap_type, "informative text")


class InformationIntegrator:
    """
    Integrates retrieved information into knowledge state.
    """

    def __init__(self):
        pass

    def integrate(self, retrieved: RetrievedInformation,
                 knowledge_state: KnowledgeState) -> KnowledgeState:
        """
        Integrate retrieved information into knowledge state.

        Args:
            retrieved: The retrieved information
            knowledge_state: Current knowledge state

        Returns:
            Updated knowledge state
        """
        # Add to retrieved list
        knowledge_state.retrieved.append(retrieved)

        # Extract facts from content
        new_facts = self._extract_facts(retrieved.content)
        knowledge_state.known_facts.extend(new_facts)

        # Extract relations
        new_relations = self._extract_relations(retrieved.content)
        knowledge_state.known_relations.extend(new_relations)

        # Remove filled gap if confidence is high enough
        if retrieved.confidence > 0.7 and retrieved.target_gap:
            knowledge_state.gaps = [
                g for g in knowledge_state.gaps
                if g.topic != retrieved.query.target_gap.topic
            ]

        # Update completeness estimate
        knowledge_state.completeness = self._estimate_completeness(knowledge_state)

        return knowledge_state

    def _extract_facts(self, content: str) -> List[str]:
        """Extract factual statements from content"""
        facts = []

        # Split into sentences
        sentences = re.split(r'[.!?]', content)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 200:
                # Check if it's a factual statement
                if self._is_factual_statement(sentence):
                    facts.append(sentence)

        return facts[:5]  # Limit

    def _is_factual_statement(self, sentence: str) -> bool:
        """Check if sentence is likely a factual statement"""
        factual_patterns = [
            r'\b(?:is|are|was|were)\b',
            r'\b(?:has|have|had)\b',
            r'\b(?:equals?|contains?|includes?)\b',
        ]

        opinion_markers = ['I think', 'I believe', 'maybe', 'perhaps', 'probably', 'might']

        # Exclude opinions
        for marker in opinion_markers:
            if marker.lower() in sentence.lower():
                return False

        # Check for factual patterns
        for pattern in factual_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                return True

        return False

    def _extract_relations(self, content: str) -> List[Tuple[str, str, str]]:
        """Extract relations from content"""
        relations = []

        relation_patterns = [
            (r'(\w+)\s+is\s+(?:a|an)\s+(\w+)', 'is_a'),
            (r'(\w+)\s+(?:contains?|has)\s+(\w+)', 'has'),
            (r'(\w+)\s+causes?\s+(\w+)', 'causes'),
            (r'(\w+)\s+(?:is|are)\s+(?:part|member)\s+of\s+(\w+)', 'part_of'),
        ]

        for pattern, rel_type in relation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    relations.append((match[0], rel_type, match[1]))

        return relations[:5]  # Limit

    def _estimate_completeness(self, state: KnowledgeState) -> float:
        """Estimate how complete the knowledge state is"""
        if not state.gaps:
            return 1.0

        # Calculate based on remaining gaps and retrieved info
        filled = len(state.retrieved)
        remaining = len(state.gaps)
        total = filled + remaining

        if total == 0:
            return 1.0

        # Weighted by gap importance
        gap_weight = sum(g.importance for g in state.gaps)
        max_weight = remaining if remaining > 0 else 1

        # Base completeness
        base = filled / total

        # Adjust by gap importance
        importance_factor = 1 - (gap_weight / max_weight / 2)

        return min(1.0, base * importance_factor + 0.2)


class SufficiencyAssessor:
    """
    Assesses whether current knowledge is sufficient to answer.
    """

    def __init__(self):
        self.sufficiency_threshold = 0.7

    def assess(self, knowledge_state: KnowledgeState,
              problem: str) -> Dict[str, Any]:
        """
        Assess if knowledge is sufficient.

        Args:
            knowledge_state: Current knowledge state
            problem: The original problem

        Returns:
            Assessment with sufficiency score and recommendations
        """
        # Calculate sufficiency score
        score = self._calculate_sufficiency_score(knowledge_state, problem)

        # Determine if sufficient
        is_sufficient = score >= self.sufficiency_threshold

        # Generate recommendations if not sufficient
        recommendations = []
        if not is_sufficient:
            recommendations = self._generate_recommendations(
                knowledge_state, score
            )

        # Identify most critical gaps
        critical_gaps = self._identify_critical_gaps(knowledge_state)

        return {
            'score': score,
            'is_sufficient': is_sufficient,
            'completeness': knowledge_state.completeness,
            'num_facts': len(knowledge_state.known_facts),
            'num_gaps': len(knowledge_state.gaps),
            'critical_gaps': critical_gaps,
            'recommendations': recommendations,
            'confidence': self._estimate_answer_confidence(score, knowledge_state)
        }

    def _calculate_sufficiency_score(self, state: KnowledgeState,
                                    problem: str) -> float:
        """Calculate overall sufficiency score"""
        # Factor 1: Completeness
        completeness_score = state.completeness

        # Factor 2: Coverage of problem topics
        coverage_score = self._calculate_coverage(state, problem)

        # Factor 3: Quality of retrieved information
        quality_score = self._calculate_quality(state)

        # Factor 4: Remaining gaps importance
        gap_penalty = self._calculate_gap_penalty(state)

        # Weighted combination
        score = (
            0.3 * completeness_score +
            0.3 * coverage_score +
            0.2 * quality_score -
            0.2 * gap_penalty
        )

        return max(0.0, min(1.0, score))

    def _calculate_coverage(self, state: KnowledgeState, problem: str) -> float:
        """Calculate how well knowledge covers problem topics"""
        # Extract key words from problem
        words = set(problem.lower().split())
        stopwords = {'the', 'a', 'an', 'is', 'are', 'what', 'how', 'why', 'when', 'where'}
        words -= stopwords

        if not words:
            return 1.0

        # Check coverage in facts and relations
        knowledge_text = ' '.join(state.known_facts).lower()
        for rel in state.known_relations:
            knowledge_text += ' ' + ' '.join(str(x) for x in rel)

        covered = sum(1 for w in words if w in knowledge_text)

        return covered / len(words) if words else 1.0

    def _calculate_quality(self, state: KnowledgeState) -> float:
        """Calculate quality of retrieved information"""
        if not state.retrieved:
            return 0.5  # Neutral if nothing retrieved

        # Average confidence and relevance
        avg_confidence = sum(r.confidence for r in state.retrieved) / len(state.retrieved)
        avg_relevance = sum(r.relevance for r in state.retrieved) / len(state.retrieved)

        return (avg_confidence + avg_relevance) / 2

    def _calculate_gap_penalty(self, state: KnowledgeState) -> float:
        """Calculate penalty for remaining gaps"""
        if not state.gaps:
            return 0.0

        # Sum of important gaps
        total_importance = sum(g.importance for g in state.gaps)
        max_importance = len(state.gaps)  # All gaps at importance 1.0

        return total_importance / max_importance if max_importance > 0 else 0.0

    def _generate_recommendations(self, state: KnowledgeState,
                                 score: float) -> List[str]:
        """Generate recommendations for improving sufficiency"""
        recommendations = []

        # If completeness is low
        if state.completeness < 0.5:
            recommendations.append("Gather more information on key topics")

        # If there are high-importance gaps
        important_gaps = [g for g in state.gaps if g.importance > 0.7]
        if important_gaps:
            recommendations.append(
                f"Fill critical gaps: {', '.join(g.topic for g in important_gaps[:3])}"
            )

        # If quality is low
        if state.retrieved:
            avg_quality = sum(r.confidence for r in state.retrieved) / len(state.retrieved)
            if avg_quality < 0.5:
                recommendations.append("Seek higher-quality information sources")

        # General recommendations based on score
        if score < 0.4:
            recommendations.append("Consider decomposing problem into simpler sub-questions")
        elif score < 0.6:
            recommendations.append("Verify key facts before proceeding")

        return recommendations

    def _identify_critical_gaps(self, state: KnowledgeState) -> List[str]:
        """Identify most critical knowledge gaps"""
        critical = [g for g in state.gaps if g.importance > 0.6]
        return [g.topic for g in critical[:3]]

    def _estimate_answer_confidence(self, sufficiency: float,
                                   state: KnowledgeState) -> float:
        """Estimate confidence in potential answer"""
        # Base confidence from sufficiency
        confidence = sufficiency

        # Adjust by number of supporting facts
        fact_boost = min(0.1, len(state.known_facts) * 0.02)
        confidence += fact_boost

        # Penalize for remaining important gaps
        gap_penalty = sum(g.importance * 0.05 for g in state.gaps)
        confidence -= gap_penalty

        return max(0.1, min(0.95, confidence))


class ActiveInformationSeeker:
    """
    Main module for active information seeking.

    Orchestrates gap identification, query formulation,
    information retrieval, and sufficiency assessment.
    """

    def __init__(self, retrieval_function: Callable = None):
        """
        Initialize the active information seeker.

        Args:
            retrieval_function: Optional function to retrieve information
                               Signature: (query: str, source: str) -> Dict[str, Any]
        """
        self.gap_analyzer = GapAnalyzer()
        self.query_formulator = QueryFormulator()
        self.integrator = InformationIntegrator()
        self.assessor = SufficiencyAssessor()

        # Optional retrieval function
        self.retrieval_function = retrieval_function

        # Statistics
        self.stats = {
            'gaps_identified': 0,
            'queries_formulated': 0,
            'information_retrieved': 0,
            'sufficiency_assessments': 0
        }

    def seek_information(self, problem: str, category: str = "",
                        max_queries: int = 5,
                        min_sufficiency: float = 0.7) -> Dict[str, Any]:
        """
        Main information seeking loop.

        Args:
            problem: The problem to solve
            category: Optional problem category
            max_queries: Maximum queries to make
            min_sufficiency: Minimum sufficiency score to stop

        Returns:
            Final knowledge state and assessment
        """
        # Initialize knowledge state
        knowledge_state = KnowledgeState(
            known_facts=[],
            known_constraints=[],
            known_relations=[],
            gaps=[],
            retrieved=[],
            completeness=0.0
        )

        # Identify initial gaps
        gaps = self.gap_analyzer.identify_gaps(problem)
        knowledge_state.gaps = gaps
        self.stats['gaps_identified'] += len(gaps)

        # Information seeking loop
        queries_made = 0
        while queries_made < max_queries:
            # Check sufficiency
            assessment = self.assessor.assess(knowledge_state, problem)
            self.stats['sufficiency_assessments'] += 1

            if assessment['is_sufficient']:
                break

            # Formulate queries for remaining gaps
            queries = self.query_formulator.formulate_queries(
                knowledge_state.gaps, max_queries=1
            )
            self.stats['queries_formulated'] += len(queries)

            if not queries:
                break

            # Execute queries
            for query in queries:
                retrieved = self._execute_query(query)
                if retrieved:
                    knowledge_state = self.integrator.integrate(
                        retrieved, knowledge_state
                    )
                    self.stats['information_retrieved'] += 1

            queries_made += len(queries)

            # Re-analyze for new gaps based on retrieved information
            new_gaps = self.gap_analyzer.identify_gaps(
                problem,
                current_knowledge={'facts': knowledge_state.known_facts}
            )

            # Update gaps list (remove filled, add new)
            filled_topics = {r.query.target_gap.topic for r in knowledge_state.retrieved
                           if r.query.target_gap}
            knowledge_state.gaps = [
                g for g in new_gaps if g.topic not in filled_topics
            ]

        # Final assessment
        final_assessment = self.assessor.assess(knowledge_state, problem)

        return {
            'knowledge_state': {
                'known_facts': knowledge_state.known_facts,
                'known_constraints': knowledge_state.known_constraints,
                'known_relations': knowledge_state.known_relations,
                'completeness': knowledge_state.completeness
            },
            'remaining_gaps': [
                {'topic': g.topic, 'type': g.gap_type.value, 'importance': g.importance}
                for g in knowledge_state.gaps
            ],
            'retrieved_count': len(knowledge_state.retrieved),
            'queries_made': queries_made,
            'assessment': final_assessment,
            'ready_to_answer': final_assessment['is_sufficient']
        }
