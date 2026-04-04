"""
Phase 1: Self-Reflection Module

Enables the system to reason about its own reasoning:
- Contradiction detection in reasoning chains
- Confidence calibration based on reasoning quality
- Uncertainty explanation and articulation
- Failure analysis and improvement suggestions
"""

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict
import hashlib


class ContradictionType(Enum):
    """Types of logical contradictions"""
    DIRECT = "direct"              # A and not-A
    IMPLICIT = "implicit"          # Statements that together imply contradiction
    TEMPORAL = "temporal"          # Changed conclusion without justification
    NUMERICAL = "numerical"        # Inconsistent numbers/calculations
    DEFINITIONAL = "definitional"  # Using term with conflicting meanings


class UncertaintySource(Enum):
    """Sources of uncertainty in reasoning"""
    KNOWLEDGE_GAP = "knowledge_gap"
    AMBIGUOUS_QUESTION = "ambiguous_question"
    MULTIPLE_VALID_ANSWERS = "multiple_valid_answers"
    REASONING_COMPLEXITY = "reasoning_complexity"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


@dataclass
class Contradiction:
    """Represents a detected contradiction in reasoning"""
    type: ContradictionType
    statement1: str
    statement2: str
    explanation: str
    severity: float  # 0-1, how serious the contradiction is
    location: Tuple[int, int]  # Indices in reasoning trace
    suggested_resolution: Optional[str] = None


@dataclass
class UncertaintyExplanation:
    """Explains why a problem is uncertain/difficult"""
    sources: List[UncertaintySource]
    explanations: Dict[UncertaintySource, str]
    knowledge_gaps: List[str]
    ambiguities: List[str]
    confidence_estimate: float
    improvement_suggestions: List[str]


@dataclass
class ReasoningQualitySignals:
    """Signals about reasoning quality"""
    logical_coherence: float  # 0-1
    evidence_support: float   # 0-1
    completeness: float       # 0-1
    clarity: float            # 0-1
    consistency: float        # 0-1
    depth: float              # 0-1


@dataclass
class ImprovementSuggestion:
    """Suggestion for improving reasoning"""
    category: str
    description: str
    priority: float  # 0-1
    expected_impact: float  # 0-1
    implementation_hint: str


class ContradictionDetector:
    """
    Detects logical contradictions in reasoning traces.
    """

    def __init__(self):
        # Patterns for detecting contradictions
        self.negation_patterns = [
            (r'\b(is|are|was|were)\b', r'\b(is not|are not|was not|were not|isn\'t|aren\'t|wasn\'t|weren\'t)\b'),
            (r'\b(can|could|will|would)\b', r'\b(cannot|could not|will not|would not|can\'t|couldn\'t|won\'t|wouldn\'t)\b'),
            (r'\b(true|correct|valid)\b', r'\b(false|incorrect|invalid)\b'),
            (r'\b(increase|more|greater)\b', r'\b(decrease|less|smaller)\b'),
            (r'\b(always|all|every)\b', r'\b(never|none|no)\b'),
        ]

        # Track statement semantics
        self.statement_cache = {}

    def detect(self, reasoning_trace: List[str]) -> List[Contradiction]:
        """
        Detect contradictions in a reasoning trace.

        Args:
            reasoning_trace: List of reasoning steps

        Returns:
            List of detected contradictions
        """
        contradictions = []

        # Extract key claims from each step
        claims = self._extract_claims(reasoning_trace)

        # Check for direct contradictions
        contradictions.extend(self._check_direct_contradictions(claims, reasoning_trace))

        # Check for numerical inconsistencies
        contradictions.extend(self._check_numerical_inconsistencies(reasoning_trace))

        # Check for temporal contradictions (changed conclusions)
        contradictions.extend(self._check_temporal_contradictions(claims, reasoning_trace))

        # Check for implicit contradictions
        contradictions.extend(self._check_implicit_contradictions(claims, reasoning_trace))

        return contradictions

    def _extract_claims(self, reasoning_trace: List[str]) -> List[Dict[str, Any]]:
        """Extract key claims from reasoning steps"""
        claims = []

        for i, step in enumerate(reasoning_trace):
            step_lower = step.lower()

            # Extract conclusion-like statements
            conclusion_patterns = [
                r'therefore[,:]?\s*(.+?)(?:\.|$)',
                r'thus[,:]?\s*(.+?)(?:\.|$)',
                r'hence[,:]?\s*(.+?)(?:\.|$)',
                r'so[,:]?\s*(.+?)(?:\.|$)',
                r'this means[,:]?\s*(.+?)(?:\.|$)',
                r'we conclude[,:]?\s*(.+?)(?:\.|$)',
                r'the answer is[,:]?\s*(.+?)(?:\.|$)',
            ]

            for pattern in conclusion_patterns:
                matches = re.findall(pattern, step_lower, re.IGNORECASE)
                for match in matches:
                    claims.append({
                        'text': match.strip(),
                        'step_index': i,
                        'type': 'conclusion',
                        'full_step': step
                    })

            # Extract assertion-like statements
            assertion_patterns = [
                r'(\w+)\s+(is|are|was|were)\s+(.+?)(?:\.|,|$)',
                r'(\w+)\s+(equals?|=)\s+(.+?)(?:\.|,|$)',
            ]

            for pattern in assertion_patterns:
                matches = re.findall(pattern, step_lower)
                for match in matches:
                    claims.append({
                        'subject': match[0],
                        'predicate': match[1],
                        'object': match[2] if len(match) > 2 else '',
                        'step_index': i,
                        'type': 'assertion',
                        'full_step': step
                    })

        return claims

    def _check_direct_contradictions(self, claims: List[Dict],
                                     reasoning_trace: List[str]) -> List[Contradiction]:
        """Check for direct logical contradictions (A and not-A)"""
        contradictions = []

        for i, claim1 in enumerate(claims):
            for j, claim2 in enumerate(claims[i+1:], i+1):
                # Check if claims are about the same subject
                if claim1.get('subject') and claim1.get('subject') == claim2.get('subject'):
                    # Check for contradictory predicates
                    for pos_pattern, neg_pattern in self.negation_patterns:
                        if (re.search(pos_pattern, claim1.get('full_step', ''), re.IGNORECASE) and
                            re.search(neg_pattern, claim2.get('full_step', ''), re.IGNORECASE)):

                            contradictions.append(Contradiction(
                                type=ContradictionType.DIRECT,
                                statement1=claim1.get('full_step', ''),
                                statement2=claim2.get('full_step', ''),
                                explanation=f"Direct contradiction about '{claim1.get('subject', 'unknown')}'",
                                severity=0.9,
                                location=(claim1['step_index'], claim2['step_index']),
                                suggested_resolution="Review and reconcile conflicting statements"
                            ))
                            break

        return contradictions

    def _check_numerical_inconsistencies(self, reasoning_trace: List[str]) -> List[Contradiction]:
        """Check for numerical inconsistencies"""
        contradictions = []

        # Extract all numbers with context
        number_contexts = []
        for i, step in enumerate(reasoning_trace):
            # Find numbers
            numbers = re.findall(r'(\w+)\s*[=:]\s*([\d.]+)', step)
            for var, val in numbers:
                number_contexts.append({
                    'variable': var.lower(),
                    'value': float(val),
                    'step_index': i,
                    'full_step': step
                })

        # Check for same variable with different values
        var_values = defaultdict(list)
        for nc in number_contexts:
            var_values[nc['variable']].append(nc)

        for var, contexts in var_values.items():
            if len(contexts) > 1:
                values = [c['value'] for c in contexts]
                if len(set(values)) > 1:  # Different values for same variable
                    contradictions.append(Contradiction(
                        type=ContradictionType.NUMERICAL,
                        statement1=contexts[0]['full_step'],
                        statement2=contexts[-1]['full_step'],
                        explanation=f"Variable '{var}' has inconsistent values: {values}",
                        severity=0.8,
                        location=(contexts[0]['step_index'], contexts[-1]['step_index']),
                        suggested_resolution=f"Verify calculations for '{var}'"
                    ))

        return contradictions

    def _check_temporal_contradictions(self, claims: List[Dict],
                                       reasoning_trace: List[str]) -> List[Contradiction]:
        """Check for conclusions that change without justification"""
        contradictions = []

        # Group conclusions
        conclusions = [c for c in claims if c.get('type') == 'conclusion']

        # Check for changed conclusions
        for i, c1 in enumerate(conclusions):
            for c2 in conclusions[i+1:]:
                # If conclusions are about same topic but different
                if self._similar_topic(c1.get('text', ''), c2.get('text', '')):
                    if not self._consistent_conclusions(c1.get('text', ''), c2.get('text', '')):
                        # Check if there's justification for the change
                        steps_between = reasoning_trace[c1['step_index']:c2['step_index']+1]
                        if not self._has_justification(steps_between):
                            contradictions.append(Contradiction(
                                type=ContradictionType.TEMPORAL,
                                statement1=c1.get('full_step', ''),
                                statement2=c2.get('full_step', ''),
                                explanation="Conclusion changed without explicit justification",
                                severity=0.6,
                                location=(c1['step_index'], c2['step_index']),
                                suggested_resolution="Add explicit reasoning for why conclusion changed"
                            ))

        return contradictions

    def _check_implicit_contradictions(self, claims: List[Dict],
                                       reasoning_trace: List[str]) -> List[Contradiction]:
        """Check for statements that together imply a contradiction"""
        contradictions = []

        # Simple implication checking
        # If A implies B, and we have A and not-B, that's a contradiction

        implication_patterns = [
            (r'if\s+(.+?)\s+then\s+(.+)', 'conditional'),
            (r'(.+?)\s+implies\s+(.+)', 'implies'),
            (r'(.+?)\s+means\s+(.+)', 'means'),
        ]

        implications = []
        for i, step in enumerate(reasoning_trace):
            for pattern, impl_type in implication_patterns:
                matches = re.findall(pattern, step.lower())
                for match in matches:
                    implications.append({
                        'antecedent': match[0],
                        'consequent': match[1],
                        'step_index': i,
                        'type': impl_type
                    })

        # Check if antecedent is affirmed but consequent is denied elsewhere
        for impl in implications:
            for claim in claims:
                # Check if antecedent is affirmed
                if self._text_similarity(impl['antecedent'], claim.get('text', '')) > 0.7:
                    # Look for denial of consequent
                    for other_claim in claims:
                        if self._is_negation(impl['consequent'], other_claim.get('text', '')):
                            contradictions.append(Contradiction(
                                type=ContradictionType.IMPLICIT,
                                statement1=f"If {impl['antecedent']} then {impl['consequent']}",
                                statement2=other_claim.get('full_step', ''),
                                explanation="Modus tollens violation: antecedent true but consequent false",
                                severity=0.7,
                                location=(impl['step_index'], other_claim['step_index']),
                                suggested_resolution="Review the implication or the conflicting statement"
                            ))

        return contradictions

    def _similar_topic(self, text1: str, text2: str) -> bool:
        """Check if two texts are about similar topics"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        words1 -= stopwords
        words2 -= stopwords

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return overlap > 0.3

    def _consistent_conclusions(self, text1: str, text2: str) -> bool:
        """Check if two conclusions are consistent"""
        # Check for negation patterns
        for pos_pattern, neg_pattern in self.negation_patterns:
            if ((re.search(pos_pattern, text1) and re.search(neg_pattern, text2)) or
                (re.search(neg_pattern, text1) and re.search(pos_pattern, text2))):
                return False
        return True

    def _has_justification(self, steps: List[str]) -> bool:
        """Check if there's justification for a change in steps"""
        justification_patterns = [
            r'however', r'but', r'although', r'on second thought',
            r'reconsidering', r'actually', r'correction', r'wait',
            r'let me reconsider', r'i was wrong'
        ]

        for step in steps:
            for pattern in justification_patterns:
                if re.search(pattern, step.lower()):
                    return True
        return False

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _is_negation(self, text1: str, text2: str) -> bool:
        """Check if text2 is a negation of text1"""
        text1_lower = text1.lower()
        text2_lower = text2.lower()

        # Check for explicit negation words
        negation_words = ['not', 'no', 'never', 'none', 'neither', 'nobody', 'nothing']

        for word in negation_words:
            if word in text2_lower and word not in text1_lower:
                # Check if rest of text is similar
                text2_without_neg = text2_lower.replace(word, '').strip()
                if self._text_similarity(text1_lower, text2_without_neg) > 0.5:
                    return True

        return False


class ConfidenceCalibrator:
    """
    Calibrates confidence estimates based on reasoning quality signals.
    """

    def __init__(self):
        self.calibration_history = []
        self.feature_weights = {
            'logical_coherence': 0.25,
            'evidence_support': 0.20,
            'completeness': 0.15,
            'clarity': 0.10,
            'consistency': 0.20,
            'depth': 0.10
        }

    def calibrate(self, initial_confidence: float,
                  reasoning_trace: List[str],
                  answer: str,
                  contradictions: List[Contradiction]) -> float:
        """
        Calibrate confidence based on reasoning quality.

        Args:
            initial_confidence: Initial confidence estimate
            reasoning_trace: The reasoning steps
            answer: The proposed answer
            contradictions: Detected contradictions

        Returns:
            Calibrated confidence score
        """
        # Extract quality signals
        signals = self._extract_quality_signals(reasoning_trace, answer)

        # Apply contradiction penalty
        contradiction_penalty = self._calculate_contradiction_penalty(contradictions)

        # Calculate weighted quality score
        quality_score = sum(
            getattr(signals, feature) * weight
            for feature, weight in self.feature_weights.items()
        )

        # Combine with initial confidence
        calibrated = initial_confidence * (0.5 + 0.5 * quality_score) * (1 - contradiction_penalty)

        # Apply Bayesian adjustment based on history
        if self.calibration_history:
            calibrated = self._bayesian_adjustment(calibrated)

        return max(0.0, min(1.0, calibrated))

    def _extract_quality_signals(self, reasoning_trace: List[str],
                                 answer: str) -> ReasoningQualitySignals:
        """Extract quality signals from reasoning"""

        # Logical coherence: presence of logical connectors and structure
        logical_markers = ['therefore', 'thus', 'hence', 'because', 'since', 'if', 'then']
        logical_count = sum(
            1 for step in reasoning_trace
            for marker in logical_markers
            if marker in step.lower()
        )
        logical_coherence = min(1.0, logical_count / max(len(reasoning_trace), 1) * 2)

        # Evidence support: references to facts, data, or established knowledge
        evidence_markers = ['according to', 'studies show', 'data indicates',
                          'known that', 'established', 'proven', 'fact']
        evidence_count = sum(
            1 for step in reasoning_trace
            for marker in evidence_markers
            if marker in step.lower()
        )
        evidence_support = min(1.0, evidence_count / max(len(reasoning_trace), 1) * 3)

        # Completeness: does reasoning address key aspects?
        completeness = self._assess_completeness(reasoning_trace, answer)

        # Clarity: average sentence length and structure
        clarity = self._assess_clarity(reasoning_trace)

        # Consistency: no self-contradictions detected
        consistency = 1.0  # Will be adjusted by contradiction detector

        # Depth: number of reasoning steps relative to problem complexity
        depth = min(1.0, len(reasoning_trace) / 5)  # Assume 5 steps is good depth

        return ReasoningQualitySignals(
            logical_coherence=logical_coherence,
            evidence_support=evidence_support,
            completeness=completeness,
            clarity=clarity,
            consistency=consistency,
            depth=depth
        )

    def _assess_completeness(self, reasoning_trace: List[str], answer: str) -> float:
        """Assess reasoning completeness"""
        # Check if reasoning leads to answer
        if not reasoning_trace:
            return 0.0

        # Check if final step references the answer
        final_step = reasoning_trace[-1].lower()
        answer_lower = answer.lower()

        # Simple check: does the answer appear in reasoning?
        answer_in_reasoning = any(answer_lower in step.lower() for step in reasoning_trace)

        # Check for conclusion markers
        has_conclusion = any(
            marker in final_step
            for marker in ['therefore', 'thus', 'answer is', 'conclude']
        )

        completeness = 0.5
        if answer_in_reasoning:
            completeness += 0.25
        if has_conclusion:
            completeness += 0.25

        return completeness

    def _assess_clarity(self, reasoning_trace: List[str]) -> float:
        """Assess reasoning clarity"""
        if not reasoning_trace:
            return 0.0

        # Average words per step (too few or too many reduces clarity)
        avg_words = sum(len(step.split()) for step in reasoning_trace) / len(reasoning_trace)

        # Optimal range: 10-30 words per step
        if 10 <= avg_words <= 30:
            word_score = 1.0
        elif avg_words < 10:
            word_score = avg_words / 10
        else:
            word_score = max(0.5, 1.0 - (avg_words - 30) / 50)

        return word_score

    def _calculate_contradiction_penalty(self, contradictions: List[Contradiction]) -> float:
        """Calculate penalty based on contradictions"""
        if not contradictions:
            return 0.0

        # Weight by severity
        total_severity = sum(c.severity for c in contradictions)

        # Diminishing returns: first contradiction is worst
        penalty = 1 - math.exp(-total_severity)

        return min(0.9, penalty)  # Cap at 90% penalty

    def _bayesian_adjustment(self, confidence: float) -> float:
        """Apply Bayesian adjustment based on calibration history"""
        if len(self.calibration_history) < 5:
            return confidence

        # Calculate historical accuracy at this confidence level
        similar_predictions = [
            h for h in self.calibration_history
            if abs(h['predicted'] - confidence) < 0.1
        ]

        if not similar_predictions:
            return confidence

        actual_accuracy = sum(h['correct'] for h in similar_predictions) / len(similar_predictions)

        # Adjust toward historical accuracy
        adjustment = (actual_accuracy - confidence) * 0.3

        return confidence + adjustment

    def record_outcome(self, predicted_confidence: float, was_correct: bool):
        """Record outcome for calibration learning"""
        self.calibration_history.append({
            'predicted': predicted_confidence,
            'correct': was_correct
        })

        # Keep last 1000 records
        if len(self.calibration_history) > 1000:
            self.calibration_history = self.calibration_history[-1000:]


class UncertaintyAnalyzer:
    """
    Analyzes and explains sources of uncertainty.
    """

    def __init__(self):
        self.uncertainty_patterns = {
            UncertaintySource.KNOWLEDGE_GAP: [
                r"don't know", r"not sure", r"unclear", r"unknown",
                r"no information", r"cannot determine"
            ],
            UncertaintySource.AMBIGUOUS_QUESTION: [
                r"could mean", r"interpret", r"ambiguous", r"unclear what",
                r"depends on", r"multiple meanings"
            ],
            UncertaintySource.MULTIPLE_VALID_ANSWERS: [
                r"could be", r"alternatively", r"another possibility",
                r"or", r"either", r"multiple solutions"
            ],
            UncertaintySource.REASONING_COMPLEXITY: [
                r"complex", r"complicated", r"many steps", r"difficult",
                r"intricate", r"involved"
            ],
            UncertaintySource.INSUFFICIENT_CONTEXT: [
                r"need more", r"without knowing", r"assuming", r"if we",
                r"given that", r"provided that"
            ],
            UncertaintySource.CONFLICTING_EVIDENCE: [
                r"however", r"but", r"conflicting", r"contradicts",
                r"on the other hand", r"nevertheless"
            ]
        }

    def analyze(self, question: str, reasoning_trace: List[str],
                answer: str) -> UncertaintyExplanation:
        """
        Analyze uncertainty in the reasoning.

        Args:
            question: The original question
            reasoning_trace: The reasoning steps
            answer: The proposed answer

        Returns:
            UncertaintyExplanation with detailed analysis
        """
        # Detect uncertainty sources
        sources = self._detect_sources(reasoning_trace)

        # Generate explanations for each source
        explanations = self._generate_explanations(sources, reasoning_trace)

        # Identify knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(question, reasoning_trace)

        # Identify ambiguities
        ambiguities = self._identify_ambiguities(question, reasoning_trace)

        # Estimate confidence
        confidence = self._estimate_confidence(sources, reasoning_trace)

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(sources, knowledge_gaps, ambiguities)

        return UncertaintyExplanation(
            sources=sources,
            explanations=explanations,
            knowledge_gaps=knowledge_gaps,
            ambiguities=ambiguities,
            confidence_estimate=confidence,
            improvement_suggestions=suggestions
        )

    def _detect_sources(self, reasoning_trace: List[str]) -> List[UncertaintySource]:
        """Detect uncertainty sources from reasoning"""
        detected = set()

        combined_text = ' '.join(reasoning_trace).lower()

        for source, patterns in self.uncertainty_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    detected.add(source)
                    break

        return list(detected)

    def _generate_explanations(self, sources: List[UncertaintySource],
                               reasoning_trace: List[str]) -> Dict[UncertaintySource, str]:
        """Generate explanations for detected uncertainty sources"""
        explanations = {}

        combined_text = ' '.join(reasoning_trace).lower()

        for source in sources:
            if source == UncertaintySource.KNOWLEDGE_GAP:
                explanations[source] = "The reasoning reveals gaps in required knowledge"
            elif source == UncertaintySource.AMBIGUOUS_QUESTION:
                explanations[source] = "The question has multiple valid interpretations"
            elif source == UncertaintySource.MULTIPLE_VALID_ANSWERS:
                explanations[source] = "Multiple answers could be correct depending on interpretation"
            elif source == UncertaintySource.REASONING_COMPLEXITY:
                explanations[source] = "The problem requires complex multi-step reasoning"
            elif source == UncertaintySource.INSUFFICIENT_CONTEXT:
                explanations[source] = "Additional context would help narrow the answer"
            elif source == UncertaintySource.CONFLICTING_EVIDENCE:
                explanations[source] = "Evidence points in different directions"

        return explanations

    def _identify_knowledge_gaps(self, question: str,
                                 reasoning_trace: List[str]) -> List[str]:
        """Identify specific knowledge gaps"""
        gaps = []

        # Patterns indicating knowledge needs
        gap_patterns = [
            (r"need to know (.+?)(?:\.|,|$)", "Need to know: {}"),
            (r"requires knowledge of (.+?)(?:\.|,|$)", "Requires: {}"),
            (r"don't have information about (.+?)(?:\.|,|$)", "Missing info about: {}"),
            (r"assuming (.+?)(?:\.|,|$)", "Assumption (unverified): {}"),
        ]

        combined = ' '.join(reasoning_trace)

        for pattern, template in gap_patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            for match in matches:
                gaps.append(template.format(match.strip()))

        return gaps[:5]  # Limit to top 5 gaps

    def _identify_ambiguities(self, question: str,
                              reasoning_trace: List[str]) -> List[str]:
        """Identify ambiguities in question or reasoning"""
        ambiguities = []

        # Check question for ambiguous terms
        ambiguous_constructs = [
            (r'\b(it|this|that|they|them)\b', "Pronoun reference unclear: '{}'"),
            (r'\b(some|many|few|several)\b', "Quantity unspecified: '{}'"),
            (r'\b(best|better|optimal)\b', "Criterion for '{}' not specified"),
        ]

        for pattern, template in ambiguous_constructs:
            matches = re.findall(pattern, question, re.IGNORECASE)
            for match in matches:
                ambiguities.append(template.format(match))

        return ambiguities[:3]  # Limit to top 3

    def _estimate_confidence(self, sources: List[UncertaintySource],
                            reasoning_trace: List[str]) -> float:
        """Estimate confidence based on uncertainty sources"""
        base_confidence = 0.7

        # Penalties for each uncertainty source
        penalties = {
            UncertaintySource.KNOWLEDGE_GAP: 0.15,
            UncertaintySource.AMBIGUOUS_QUESTION: 0.10,
            UncertaintySource.MULTIPLE_VALID_ANSWERS: 0.08,
            UncertaintySource.REASONING_COMPLEXITY: 0.05,
            UncertaintySource.INSUFFICIENT_CONTEXT: 0.12,
            UncertaintySource.CONFLICTING_EVIDENCE: 0.15
        }

        total_penalty = sum(penalties.get(s, 0) for s in sources)

        return max(0.1, base_confidence - total_penalty)

    def _generate_suggestions(self, sources: List[UncertaintySource],
                             knowledge_gaps: List[str],
                             ambiguities: List[str]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        if UncertaintySource.KNOWLEDGE_GAP in sources:
            suggestions.append("Consult external knowledge sources to fill information gaps")

        if UncertaintySource.AMBIGUOUS_QUESTION in sources:
            suggestions.append("Clarify the question interpretation before proceeding")

        if UncertaintySource.MULTIPLE_VALID_ANSWERS in sources:
            suggestions.append("Consider presenting multiple valid answers with conditions")

        if UncertaintySource.INSUFFICIENT_CONTEXT in sources:
            suggestions.append("Request additional context or make explicit assumptions")

        if UncertaintySource.CONFLICTING_EVIDENCE in sources:
            suggestions.append("Weigh evidence carefully and explain the resolution")

        for gap in knowledge_gaps[:2]:
            suggestions.append(f"Research: {gap}")

        return suggestions


class SelfReflectionModule:
    """
    Main module for self-reflective reasoning.

    Combines contradiction detection, confidence calibration,
    and uncertainty analysis to enable metacognitive awareness.
    """

    def __init__(self):
        self.contradiction_detector = ContradictionDetector()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.uncertainty_analyzer = UncertaintyAnalyzer()

        # Statistics
        self.stats = {
            'reflections': 0,
            'contradictions_found': 0,
            'calibrations': 0,
            'average_confidence_adjustment': 0.0
        }

    def reflect(self, question: str, reasoning_trace: List[str],
                answer: str, initial_confidence: float) -> Dict[str, Any]:
        """
        Perform comprehensive self-reflection on reasoning.

        Args:
            question: The original question
            reasoning_trace: List of reasoning steps
            answer: The proposed answer
            initial_confidence: Initial confidence estimate

        Returns:
            Comprehensive reflection results
        """
        self.stats['reflections'] += 1

        # Detect contradictions
        contradictions = self.contradiction_detector.detect(reasoning_trace)
        self.stats['contradictions_found'] += len(contradictions)

        # Calibrate confidence
        calibrated_confidence = self.confidence_calibrator.calibrate(
            initial_confidence, reasoning_trace, answer, contradictions
        )
        self.stats['calibrations'] += 1

        # Track adjustment
        adjustment = calibrated_confidence - initial_confidence
        n = self.stats['calibrations']
        self.stats['average_confidence_adjustment'] = (
            (self.stats['average_confidence_adjustment'] * (n-1) + adjustment) / n
        )

        # Analyze uncertainty
        uncertainty = self.uncertainty_analyzer.analyze(question, reasoning_trace, answer)

        # Generate overall assessment
        assessment = self._generate_assessment(
            contradictions, calibrated_confidence, uncertainty
        )

        # Generate improvement suggestions
        improvements = self._suggest_improvements(
            contradictions, uncertainty, reasoning_trace
        )

        return {
            'contradictions': contradictions,
            'initial_confidence': initial_confidence,
            'calibrated_confidence': calibrated_confidence,
            'confidence_adjustment': adjustment,
            'uncertainty_analysis': uncertainty,
            'assessment': assessment,
            'improvements': improvements,
            'should_revise': len(contradictions) > 0 or calibrated_confidence < 0.4
        }

    def _generate_assessment(self, contradictions: List[Contradiction],
                            confidence: float,
                            uncertainty: UncertaintyExplanation) -> str:
        """Generate overall assessment of reasoning quality"""

        if not contradictions and confidence > 0.7:
            return "Reasoning appears sound with high confidence"
        elif not contradictions and confidence > 0.4:
            return "Reasoning is coherent but confidence is moderate"
        elif contradictions and confidence > 0.5:
            return "Reasoning contains contradictions that should be addressed"
        else:
            return "Significant issues detected; recommend revision"

    def _suggest_improvements(self, contradictions: List[Contradiction],
                             uncertainty: UncertaintyExplanation,
                             reasoning_trace: List[str]) -> List[ImprovementSuggestion]:
        """Generate specific improvement suggestions"""
        suggestions = []

        # Address contradictions
        for c in contradictions[:2]:  # Top 2 contradictions
            suggestions.append(ImprovementSuggestion(
                category="contradiction_resolution",
                description=f"Resolve: {c.explanation}",
                priority=c.severity,
                expected_impact=0.3,
                implementation_hint=c.suggested_resolution or "Review conflicting statements"
            ))

        # Address uncertainty sources
        for source in uncertainty.sources:
            if source == UncertaintySource.KNOWLEDGE_GAP:
                suggestions.append(ImprovementSuggestion(
                    category="knowledge_acquisition",
                    description="Fill identified knowledge gaps",
                    priority=0.8,
                    expected_impact=0.25,
                    implementation_hint="Query external knowledge sources"
                ))
            elif source == UncertaintySource.AMBIGUOUS_QUESTION:
                suggestions.append(ImprovementSuggestion(
                    category="clarification",
                    description="Clarify question interpretation",
                    priority=0.7,
                    expected_impact=0.2,
                    implementation_hint="State explicit interpretation before reasoning"
                ))

        # Depth improvement if reasoning is shallow
        if len(reasoning_trace) < 3:
            suggestions.append(ImprovementSuggestion(
                category="depth",
                description="Add more reasoning steps",
                priority=0.5,
                expected_impact=0.15,
                implementation_hint="Break down reasoning into smaller steps"
            ))

        # Sort by priority
        suggestions.sort(key=lambda s: s.priority, reverse=True)

        return suggestions[:5]

    def record_outcome(self, predicted_confidence: float, was_correct: bool):
        """Record outcome for learning"""
        self.confidence_calibrator.record_outcome(predicted_confidence, was_correct)

    def get_stats(self) -> Dict[str, Any]:
        """Get reflection statistics"""
        return self.stats.copy()
