"""
Integrated Counterfactual Reasoning System for ASTRA

This module integrates counterfactual reasoning capabilities into ASTRA's
core system, making it accessible through standard interfaces.

Key features:
- Automatic query classification to detect counterfactual questions
- Integration with domain registry for routing
- Automatic world model initialization
- Access through standard ASTRA interfaces

Date: 2025-12-11
Version: 1.0
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Import fixed components
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unified_world_model import (
    get_world_model, UnifiedWorldModel, CausalEdge, Hypothesis
)
from integration_bus_stub import IntegrationBus, EventType, get_integration_bus


@dataclass
class QueryClassification:
    """Result of query classification"""
    is_counterfactual: bool
    confidence: float
    triggers: List[str]
    query_type: str  # "standard", "counterfactual", "mixed"


class CounterfactualQueryClassifier:
    """
    Classifies queries to determine if counterfactual reasoning is needed.

    Identifies questions asking:
    - "What would happen if..."
    - "What would make X not true..."
    - "What conditions would eliminate..."
    - "What observations would distinguish..."
    """

    # Counterfactual trigger patterns
    COUNTERFACTUAL_PATTERNS = [
        r"what would (happen|make|cause|require)",
        r"what (if|conditions?|would)",
        r"not (have|be|true|exist)",
        r"(eliminate|prevent|suppress|avoid)",
        r"alternative (scenarios?|explanations?|interpretations?)",
        r"distinguish (between|from)",
        r"counterfactual",
        r"(hypothetical|theoretical) scenario",
    ]

    # Standard query patterns (for exclusion)
    STANDARD_PATTERNS = [
        r"calculate|compute|derive",
        r"what is|what are|what's",
        r"explain|describe",
        r"analyze (this|the)",
        r"(list|show|find)",
    ]

    def __init__(self):
        """Initialize the classifier"""
        self.cf_patterns = [re.compile(p, re.IGNORECASE)
                           for p in self.COUNTERFACTUAL_PATTERNS]
        self.std_patterns = [re.compile(p, re.IGNORECASE)
                             for p in self.STANDARD_PATTERNS]

    def classify(self, query: str) -> QueryClassification:
        """
        Classify a query as counterfactual or standard.

        Args:
            query: The query text to classify

        Returns:
            QueryClassification with assessment
        """
        query_lower = query.lower()
        triggers = []
        cf_score = 0
        std_score = 0

        # Check for counterfactual triggers
        for pattern in self.cf_patterns:
            if pattern.search(query):
                cf_score += 1
                # Extract trigger phrase
                match = pattern.search(query)
                if match:
                    triggers.append(match.group(0))

        # Check for standard query indicators
        for pattern in self.std_patterns:
            if pattern.search(query):
                std_score += 1

        # Determine query type
        is_counterfactual = cf_score > std_score
        confidence = min(0.9, cf_score / len(self.cf_patterns) + 0.3)

        if is_counterfactual and std_score > 0:
            query_type = "mixed"
        elif is_counterfactual:
            query_type = "counterfactual"
        else:
            query_type = "standard"

        return QueryClassification(
            is_counterfactual=is_counterfactual,
            confidence=confidence,
            triggers=triggers,
            query_type=query_type
        )


class IntegratedCounterfactualSystem:
    """
    Integrated counterfactual reasoning system for ASTRA.

    This system:
    1. Classifies incoming queries
    2. Routes counterfactual queries to the reasoning engine
    3. Manages world model state
    4. Returns formatted results
    """

    def __init__(self):
        """Initialize the integrated system"""
        self.classifier = CounterfactualQueryClassifier()
        self.world_model = get_world_model()
        self.bus = get_integration_bus()

        # Load counterfactual reasoning module
        try:
            # Try absolute import first
            try:
                from astra_core.reasoning.counterfactual_reasoning import CounterfactualEngine
            except ImportError:
                # Fall back to relative import
                from .counterfactual_reasoning import CounterfactualEngine
            self.cf_engine = CounterfactualEngine(self.world_model, self.bus)
            self.cf_available = True
        except ImportError as e:
            print(f"Warning: Counterfactual engine not available: {e}")
            self.cf_available = False

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query, routing to counterfactual reasoning if appropriate.

        Args:
            query: The query text
            context: Optional context information

        Returns:
            Result dictionary with answer and metadata
        """
        # Classify the query
        classification = self.classifier.classify(query)

        # Log the classification
        self.bus.publish(
            EventType.REASONING_STEP_COMPLETED,
            "query_classifier",
            {
                'query_type': classification.query_type,
                'is_counterfactual': classification.is_counterfactual,
                'confidence': classification.confidence
            }
        )

        # Route based on classification
        if classification.is_counterfactual and self.cf_available:
            return self._process_counterfactual(query, classification)
        else:
            # Return indication that this should be processed by standard domains
            return {
                'answer': None,
                'requires_standard_processing': True,
                'classification': classification,
                'message': 'Query classified as standard analysis - route to domain modules'
            }

    def _process_counterfactual(self, query: str,
                                classification: QueryClassification) -> Dict[str, Any]:
        """
        Process a counterfactual query using the reasoning engine.

        Args:
            query: The counterfactual query
            classification: Query classification result

        Returns:
            Result with counterfactual analysis
        """
        # Import the filament counterfactual analyzer
        # In production, this would be more general
        try:
            # Try absolute import first
            try:
                from astra_core.reasoning.filament_counterfactual_simple import FilamentCounterfactualAnalyzer
            except ImportError:
                # Fall back to relative import
                from .filament_counterfactual_simple import FilamentCounterfactualAnalyzer
            analyzer = FilamentCounterfactualAnalyzer()
            answer = analyzer.analyze_counterfactual(query)

            return {
                'answer': answer,
                'query_type': 'counterfactual',
                'classification': classification,
                'confidence': classification.confidence,
                'requires_standard_processing': False,
                'capabilities_used': ['counterfactual_reasoning', 'causal_analysis',
                                      'hypothesis_generation', 'observational_design']
            }
        except ImportError:
            # Fallback: Generate basic counterfactual analysis
            return self._generate_basic_counterfactual(query, classification)

    def _generate_basic_counterfactual(self, query: str,
                                       classification: QueryClassification) -> Dict[str, Any]:
        """
        Generate basic counterfactual analysis when specialized analyzer unavailable.

        Args:
            query: The query
            classification: Query classification

        Returns:
            Basic counterfactual analysis
        """
        # Extract key concepts from query
        # This is a simplified version - production would use NLP
        answer = f"""
# Counterfactual Analysis

**Query Classification:** Counterfactual (confidence: {classification.confidence:.0%})

**Identified Triggers:** {', '.join(classification.triggers)}

**Analysis:**
This query has been classified as requiring counterfactual reasoning—exploring
hypothetical alternatives to established astrophysical results.

The query asks about conditions that would modify or eliminate an established
phenomenon. To properly address this question, ASTRA would need to:

1. **Understand the causal mechanism** producing the established result
2. **Identify which physical parameters** could be modified
3. **Generate alternative scenarios** with different parameter values
4. **Make quantitative predictions** for each scenario
5. **Design observational tests** to distinguish scenarios

**Current Status:**
ASTRA's counterfactual reasoning engine has been invoked and recognizes this
as a counterfactual query. However, specialized analysis for this specific
topic may require additional domain knowledge.

**Recommendation:**
For detailed counterfactual analysis, please ensure:
- Sufficient domain knowledge is loaded in the world model
- Specialized counterfactual analyzer is available
- Query topic is within ASTRA's domain coverage

This represents a promising direction for autonomous discovery capabilities,
though full integration with domain modules is ongoing work.
"""

        return {
            'answer': answer,
            'query_type': 'counterfactual',
            'classification': classification,
            'confidence': classification.confidence,
            'requires_standard_processing': False,
            'capabilities_used': ['query_classification', 'counterfactual_recognition'],
            'fallback_mode': True
        }


# Singleton instance
_counterfactual_system: Optional[IntegratedCounterfactualSystem] = None


def get_counterfactual_system() -> IntegratedCounterfactualSystem:
    """
    Get or create the singleton counterfactual system instance.

    Returns:
        The integrated counterfactual system
    """
    global _counterfactual_system
    if _counterfactual_system is None:
        _counterfactual_system = IntegratedCounterfactualSystem()
    return _counterfactual_system


def process_query_with_counterfactual(query: str,
                                       context: Optional[Dict[str, Any]] = None,
                                       fallback_handler = None) -> Dict[str, Any]:
    """
    Process a query with automatic counterfactual reasoning.

    This is the main entry point for integrated counterfactual reasoning.
    It can be called from ASTRA's standard interfaces.

    Args:
        query: The query to process
        context: Optional context information
        fallback_handler: Optional function to handle non-counterfactual queries

    Returns:
        Result dictionary
    """
    system = get_counterfactual_system()
    result = system.process_query(query, context)

    # If query requires standard processing, use fallback
    if result.get('requires_standard_processing') and fallback_handler:
        return fallback_handler(query, context)
    else:
        return result


# Auto-initialize on import
def initialize_counterfactual_system():
    """Initialize the counterfactual system (called automatically)"""
    get_counterfactual_system()


if __name__ == "__main__":
    # Test the integrated system
    print("="*80)
    print("ASTRA INTEGRATED COUNTERFACTUAL SYSTEM TEST")
    print("="*80)
    print()

    system = get_counterfactual_system()

    # Test queries
    test_queries = [
        "What is the temperature of the ISM?",
        "What would make filaments not have a characteristic width?",
        "Calculate the Jeans mass for a cloud with n=1e4 cm^-3",
        "What conditions would eliminate the 0.1 pc scale?"
    ]

    for query in test_queries:
        print(f"Query: {query}")
        print("-"*80)
        result = system.process_query(query)
        print(f"Classification: {result['classification'].query_type}")
        print(f"Confidence: {result['classification'].confidence:.0%}")
        if result.get('answer'):
            print(f"Answer preview: {result['answer'][:200]}...")
        print()


__all__ = [
    'IntegratedCounterfactualSystem',
    'CounterfactualQueryClassifier',
    'get_counterfactual_system',
    'process_query_with_counterfactual',
    'initialize_counterfactual_system'
]
