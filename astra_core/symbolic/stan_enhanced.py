"""
STAN Enhanced: Unified V38 Integration System

Combines all V38 enhancement modules with the existing V36/V37 system:
- Self-Consistency Engine for multi-sample voting
- Expanded MORK for domain routing
- Tool Integration for external knowledge
- Local RAG for vector retrieval
- Full integration with V37's swarm intelligence and memory systems

Date: 2025-12-10
Version: 38.0
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# V38 module imports
from .self_consistency import (
    SelfConsistencyEngine,
    EnhancedSelfConsistency,
    ConsistencyResult
)
from .mork_expanded import (
    ExpandedMORK,
    MORKConcept,
    Domain,
    DomainRouter
)
from .tool_integration import (
    ToolIntegration,
    ToolResult,
    WikipediaAPI,
    ArXivAPI,
    MathTool,
    PythonExecutor
)
from .local_rag import (
    LocalRAG,
    RetrievalResult,
    KnowledgeBaseBuilder
)


class ReasoningType(Enum):
    """Types of reasoning approaches"""
    FACTUAL = "factual"           # Direct fact retrieval
    MATHEMATICAL = "mathematical"  # Symbolic computation
    ANALYTICAL = "analytical"      # Multi-step reasoning
    RESEARCH = "research"          # Academic/literature based
    CAUSAL = "causal"             # Causal inference (V36)


@dataclass
class EnhancedAnswer:
    """Complete answer from STAN Enhanced"""
    answer: str
    confidence: float
    domain: Domain
    reasoning_type: ReasoningType
    sources: List[str] = field(default_factory=list)

    # Component results
    consistency_result: Optional[ConsistencyResult] = None
    tool_results: List[ToolResult] = field(default_factory=list)
    rag_context: str = ""
    mork_concepts: List[str] = field(default_factory=list)

    # Metadata
    method: str = "stan_enhanced"
    fallback_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'domain': self.domain.value,
            'reasoning_type': self.reasoning_type.value,
            'sources': self.sources,
            'method': self.method,
            'fallback_used': self.fallback_used,
            'mork_concepts': self.mork_concepts
        }

    def __str__(self):
        return f"EnhancedAnswer(answer='{self.answer[:50]}...', confidence={self.confidence:.2f}, domain={self.domain.value})"


class STANEnhanced:
    """
    STAN Enhanced: Unified V38 Integration System.

    Combines:
    - ExpandedMORK: Domain routing with 800+ concepts
    - SelfConsistency: Multi-sample voting
    - ToolIntegration: External APIs (Wikipedia, arXiv, Math, Python)
    - LocalRAG: Vector retrieval

    Expected total gain: +15-24% accuracy
    """

    def __init__(self, rag_persist_dir: Optional[str] = None,
                 n_consistency_samples: int = 5,
                 build_knowledge_base: bool = True):
        """
        Initialize STAN Enhanced.

        Args:
            rag_persist_dir: Directory for RAG persistence (None for in-memory)
            n_consistency_samples: Number of samples for self-consistency
            build_knowledge_base: Whether to build default knowledge base
        """
        # Initialize all V38 modules
        self.mork = ExpandedMORK()
        self.domain_router = DomainRouter(self.mork)
        self.consistency = EnhancedSelfConsistency(n_samples=n_consistency_samples)
        self.tools = ToolIntegration()
        self.rag = LocalRAG(persist_dir=rag_persist_dir)

        # Build knowledge base
        if build_knowledge_base:
            builder = KnowledgeBaseBuilder(self.rag)
            self._kb_stats = builder.build_default_knowledge_base(
                mork_ontology=self.mork
            )
        else:
            self._kb_stats = {}

        # Default LLM function (placeholder)
        self._llm_fn: Optional[Callable] = None

    def set_llm_function(self, llm_fn: Callable[[str, float], str]):
        """
        Set the LLM function for self-consistency.

        Args:
            llm_fn: Function(prompt, temperature) -> response
        """
        self._llm_fn = llm_fn

    def answer(self, question: str, answer_type: str = 'exactMatch',
               llm_fn: Callable = None) -> EnhancedAnswer:
        """
        Answer a question using all V38 enhancements.

        Args:
            question: The question to answer
            answer_type: 'multipleChoice', 'exactMatch', or 'openEnded'
            llm_fn: Optional LLM function override

        Returns:
            EnhancedAnswer with answer, confidence, and metadata
        """
        llm_fn = llm_fn or self._llm_fn

        # 1. Domain classification via MORK
        domain, domain_conf = self.mork.get_domain_for_question(question)
        relevant_concepts = self.mork.get_relevant_concepts(question, top_k=5)

        # 2. Determine reasoning type
        reasoning_type = self._determine_reasoning_type(question, domain)

        # 3. RAG retrieval
        rag_context = self.rag.retrieve_with_context(question, top_k=3)

        # 4. Tool queries (based on domain/reasoning type)
        tool_results = self._query_tools(question, domain, reasoning_type)

        # 5. Build enhanced prompt with all context
        prompt = self._build_prompt(question, domain, rag_context,
                                    tool_results, relevant_concepts)

        # 6. Generate answer
        if llm_fn:
            # Use self-consistency with LLM
            answer_text, consistency_score, consistency_result = \
                self.consistency.solve_with_fallback(prompt, answer_type, llm_fn)
        else:
            # Synthesize from tools and RAG
            answer_text = self._synthesize_from_tools(question, tool_results, rag_context)
            consistency_score = 0.5
            consistency_result = None

        # 7. Calculate confidence
        confidence = self._calculate_confidence(
            consistency_score, domain_conf, tool_results, rag_context
        )

        # 8. Collect sources
        sources = self._collect_sources(tool_results)

        return EnhancedAnswer(
            answer=answer_text,
            confidence=confidence,
            domain=domain,
            reasoning_type=reasoning_type,
            sources=sources,
            consistency_result=consistency_result,
            tool_results=tool_results,
            rag_context=rag_context,
            mork_concepts=[c.concept_id for c in relevant_concepts],
            fallback_used=consistency_result.fallback_used if consistency_result else False
        )

    def _determine_reasoning_type(self, question: str, domain: Domain) -> ReasoningType:
        """Determine the type of reasoning needed"""
        q_lower = question.lower()

        # Mathematical reasoning
        if any(kw in q_lower for kw in ['calculate', 'compute', 'solve', 'integral', 'derivative']):
            return ReasoningType.MATHEMATICAL

        # Research/academic reasoning
        if any(kw in q_lower for kw in ['research', 'paper', 'study', 'theory', 'prove']):
            return ReasoningType.RESEARCH

        # Causal reasoning
        if any(kw in q_lower for kw in ['why', 'cause', 'effect', 'because', 'leads to']):
            return ReasoningType.CAUSAL

        # Analytical reasoning
        if any(kw in q_lower for kw in ['analyze', 'compare', 'explain how', 'what happens']):
            return ReasoningType.ANALYTICAL

        # Default to factual
        return ReasoningType.FACTUAL

    def _query_tools(self, question: str, domain: Domain,
                     reasoning_type: ReasoningType) -> List[ToolResult]:
        """Query relevant tools based on domain and reasoning type"""
        results = []

        # Mathematical reasoning -> MathTool
        if reasoning_type == ReasoningType.MATHEMATICAL:
            math_result = self.tools.query(question, tool='math')
            if math_result.success:
                results.append(math_result)

        # Research reasoning -> arXiv
        if reasoning_type == ReasoningType.RESEARCH:
            arxiv_result = self.tools.query(question, tool='arxiv')
            if arxiv_result.success:
                results.append(arxiv_result)

        # Always try Wikipedia for context
        wiki_result = self.tools.query(question, tool='wikipedia')
        if wiki_result.success:
            results.append(wiki_result)

        # Domain-specific tool queries
        if domain in [Domain.COMPUTER_SCIENCE_AI, Domain.MATHEMATICS]:
            # Try Python for computational questions
            if 'compute' in question.lower() or 'calculate' in question.lower():
                python_result = self.tools.query(question, tool='python')
                if python_result.success:
                    results.append(python_result)

        if domain in [Domain.PHYSICS, Domain.ASTRONOMY]:
            # Also check arXiv for physics/astronomy
            if reasoning_type != ReasoningType.RESEARCH:
                arxiv_result = self.tools.query(question, tool='arxiv')
                if arxiv_result.success:
                    results.append(arxiv_result)

        return results

    def _build_prompt(self, question: str, domain: Domain, rag_context: str,
                      tool_results: List[ToolResult],
                      concepts: List[MORKConcept]) -> str:
        """Build enhanced prompt with all context"""
        prompt_parts = []

        # Domain context
        prompt_parts.append(f"Domain: {domain.value}")

        # Relevant concepts
        if concepts:
            concept_names = [c.name for c in concepts[:3]]
            prompt_parts.append(f"Relevant concepts: {', '.join(concept_names)}")

        # RAG context
        if rag_context:
            prompt_parts.append(f"\nBackground knowledge:\n{rag_context[:500]}")

        # Tool results
        for result in tool_results:
            if result.success:
                result_preview = str(result.result)[:300]
                prompt_parts.append(f"\n{result.tool.title()} says:\n{result_preview}")

        # Question
        prompt_parts.append(f"\nQuestion: {question}")
        prompt_parts.append("\nPlease provide a clear, accurate answer:")

        return "\n".join(prompt_parts)

    def _synthesize_from_tools(self, question: str, tool_results: List[ToolResult],
                                rag_context: str) -> str:
        """Synthesize answer from tools when no LLM available"""
        # Prioritize by tool type
        for result in tool_results:
            if result.success and result.tool == 'math':
                return str(result.result)

        for result in tool_results:
            if result.success and result.tool == 'wikipedia':
                # Extract first sentence
                wiki_text = str(result.result)
                first_sentence = wiki_text.split('.')[0] + '.'
                return first_sentence

        for result in tool_results:
            if result.success and result.tool == 'arxiv':
                # Return paper title/summary
                papers = result.result
                if papers and isinstance(papers, list):
                    return f"Based on research: {papers[0].get('title', 'Unknown')}"

        # Fall back to RAG
        if rag_context:
            return rag_context.split('\n')[0][:200]

        return "Unable to determine answer from available sources."

    def _calculate_confidence(self, consistency_score: float, domain_conf: float,
                              tool_results: List[ToolResult], rag_context: str) -> float:
        """Calculate overall confidence score"""
        scores = [consistency_score * 0.4]  # Self-consistency weight

        # Domain confidence
        scores.append(domain_conf * 0.2)

        # Tool confidence
        if tool_results:
            tool_conf = max(r.confidence for r in tool_results if r.success) if any(r.success for r in tool_results) else 0.0
            scores.append(tool_conf * 0.2)
        else:
            scores.append(0.0)

        # RAG confidence
        rag_conf = 0.2 if rag_context else 0.0
        scores.append(rag_conf)

        return min(sum(scores), 1.0)

    def _collect_sources(self, tool_results: List[ToolResult]) -> List[str]:
        """Collect source URLs from tool results"""
        sources = []
        for result in tool_results:
            if result.success and result.source_url:
                sources.append(result.source_url)
        return sources

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def answer_multiple_choice(self, question: str, choices: List[str],
                                llm_fn: Callable = None) -> EnhancedAnswer:
        """
        Answer a multiple choice question.

        Args:
            question: The question
            choices: List of choices ['A) ...', 'B) ...', ...]
            llm_fn: Optional LLM function

        Returns:
            EnhancedAnswer with selected choice
        """
        # Format question with choices
        full_question = question + "\n\nChoices:\n" + "\n".join(choices)
        return self.answer(full_question, answer_type='multipleChoice', llm_fn=llm_fn)

    def answer_with_reasoning(self, question: str, llm_fn: Callable = None) -> EnhancedAnswer:
        """
        Answer with explicit reasoning chain.

        Args:
            question: The question
            llm_fn: Optional LLM function

        Returns:
            EnhancedAnswer with reasoning
        """
        return self.answer(question, answer_type='openEnded', llm_fn=llm_fn)

    def get_relevant_facts(self, question: str, top_k: int = 5) -> List[str]:
        """
        Get relevant facts from RAG for a question.

        Args:
            question: The question
            top_k: Number of facts to retrieve

        Returns:
            List of relevant fact strings
        """
        result = self.rag.retrieve(question, top_k=top_k)
        return [doc.content for doc in result.documents]

    def get_domain_analysis(self, question: str) -> Dict[str, Any]:
        """
        Get domain analysis for a question.

        Args:
            question: The question

        Returns:
            Dict with domain info and relevant concepts
        """
        domain, confidence = self.mork.get_domain_for_question(question)
        concepts = self.mork.get_relevant_concepts(question, top_k=10)
        all_scores = self.mork.get_all_domain_scores(question)

        return {
            'primary_domain': domain.value,
            'confidence': confidence,
            'relevant_concepts': [{'id': c.concept_id, 'name': c.name} for c in concepts],
            'all_domain_scores': [{'domain': s.domain.value, 'score': s.score} for s in all_scores]
        }

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'mork': self.mork.stats(),
            'rag': self.rag.stats(),
            'knowledge_base': self._kb_stats,
            'consistency': self.consistency.get_cache_stats() if hasattr(self.consistency, 'get_cache_stats') else {},
            'llm_configured': self._llm_fn is not None
        }


class V38CompleteSystem:
    """
    Complete V38 System integrating with V36/V37.

    Extends V37CompleteSystem with V38 enhancements.
    """

    def __init__(self, rag_persist_dir: Optional[str] = None):
        """
        Initialize V38 Complete System.

        Args:
            rag_persist_dir: Directory for RAG persistence
        """
        # Initialize V38 enhanced system
        self.enhanced = STANEnhanced(rag_persist_dir=rag_persist_dir)
