#!/usr/bin/env python3
"""
Meta-Cognitive ML Classifier for ASTRA
======================================

Machine learning classifier to recognize meta-cognitive tasks
and complement the rule-based data sufficiency evaluator.

This module provides:
- Text classification to detect meta-cognitive tasks
- Ensemble approach with rule-based system
- Training on benchmark tasks
- Graceful degradation without ML dependencies

Author: ASTRA Project
Date: 2026-03-31
Version: 1.0
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


@dataclass
class ClassificationResult:
    """Result from ML classifier."""
    is_meta_cognitive: bool
    confidence: float
    predicted_limitation: Optional[str]
    reasoning: str


class MetaCognitiveClassifier:
    """
    Machine learning classifier for meta-cognitive task detection.

    Uses feature-based approach to classify tasks as requiring
    meta-cognitive evaluation or not.
    """

    def __init__(self):
        """Initialize the classifier."""
        self.feature_weights = self._initialize_feature_weights()
        self.threshold = 0.5
        self.trained = False

    def _initialize_feature_weights(self) -> Dict[str, float]:
        """
        Initialize feature weights for classification.

        Features are weighted based on their importance in detecting
        meta-cognitive tasks from the benchmark.
        """
        return {
            # Resolution keywords
            'resolution': 0.8,
            'beam': 0.75,
            'fwhm': 0.7,
            'cadence': 0.75,
            'sampling': 0.6,

            # Scale/comparison keywords
            'scale': 0.5,
            'versus': 0.4,
            'mismatch': 0.7,
            'ratio': 0.5,

            # Limitation keywords
            'insufficient': 0.9,
            'cannot': 0.8,
            'unable': 0.7,
            'limit': 0.6,
            'uncertain': 0.7,
            'ambiguous': 0.8,

            # Numerical patterns
            'has_numbers': 0.4,
            'has_comparisons': 0.5,

            # Domain-specific
            'model': 0.5,
            'fit': 0.4,
            'causal': 0.6,
            'correlation': 0.5,
        }

    def extract_features(self, text: str) -> Dict[str, float]:
        """
        Extract features from text for classification.

        Args:
            text: Input text (scenario + question)

        Returns:
            Dictionary of feature names to values
        """
        text_lower = text.lower()
        features = {}

        # Keyword features
        keywords = [
            'resolution', 'beam', 'fwhm', 'cadence', 'sampling',
            'scale', 'versus', 'mismatch', 'ratio',
            'insufficient', 'cannot', 'unable', 'limit', 'uncertain', 'ambiguous',
            'model', 'fit', 'causal', 'correlation'
        ]

        for keyword in keywords:
            features[keyword] = 1.0 if keyword in text_lower else 0.0

        # Numerical features
        features['has_numbers'] = 1.0 if re.search(r'\d+', text) else 0.0
        features['has_comparisons'] = 1.0 if re.search(r'(?:vs\.|versus|>|<|=)', text_lower) else 0.0

        # Count density (more numbers = more likely meta-cognitive)
        number_count = len(re.findall(r'\d+\.?\d*', text))
        features['number_density'] = min(number_count / 10.0, 1.0)

        # Question mark presence
        features['has_question'] = 1.0 if '?' in text else 0.0

        return features

    def compute_score(self, features: Dict[str, float]) -> float:
        """
        Compute classification score from features.

        Args:
            features: Feature dictionary

        Returns:
            Classification score (0.0 to 1.0)
        """
        score = 0.0
        total_weight = 0.0

        for feature, value in features.items():
            weight = self.feature_weights.get(feature, 0.0)
            score += weight * value
            total_weight += abs(weight)

        if total_weight > 0:
            score = score / total_weight

        return score

    def classify(self, scenario: str, question: str) -> ClassificationResult:
        """
        Classify a task as meta-cognitive or not.

        Args:
            scenario: Task scenario
            question: Task question

        Returns:
            ClassificationResult with prediction
        """
        text = scenario + " " + question
        features = self.extract_features(text)
        score = self.compute_score(features)

        is_meta_cognitive = score >= self.threshold
        confidence = min(abs(score - 0.5) * 2, 1.0)  # Distance from threshold

        # Predict limitation type
        predicted_limitation = self._predict_limitation_type(features)

        reasoning = f"ML classifier score: {score:.3f} (threshold: {self.threshold})"
        if is_meta_cognitive:
            reasoning += f" - Detected as meta-cognitive task"
            reasoning += f" - Likely limitation: {predicted_limitation}"
        else:
            reasoning += f" - Not detected as meta-cognitive"

        return ClassificationResult(
            is_meta_cognitive=is_meta_cognitive,
            confidence=confidence,
            predicted_limitation=predicted_limitation,
            reasoning=reasoning
        )

    def _predict_limitation_type(self, features: Dict[str, float]) -> Optional[str]:
        """
        Predict the type of limitation based on features.

        Args:
            features: Feature dictionary

        Returns:
            Predicted limitation type or None
        """
        # Check for strongest signal
        if features.get('resolution', 0) > 0 or features.get('beam', 0) > 0:
            return 'SPATIAL_RESOLUTION'
        elif features.get('cadence', 0) > 0 or features.get('sampling', 0) > 0:
            return 'TEMPORAL_RESOLUTION'
        elif features.get('model', 0) > 0 and features.get('fit', 0) > 0:
            return 'MODEL_SPECIFICATION'
        elif features.get('causal', 0) > 0:
            return 'CAUSAL_INFERENCE'
        elif features.get('ambiguous', 0) > 0:
            return 'AMBIGUITY'
        elif features.get('insufficient', 0) > 0 or features.get('cannot', 0) > 0:
            return 'GENERAL_LIMITATION'
        else:
            return None

    def train(self, training_data: List[Dict]):
        """
        Train the classifier on labeled examples.

        Args:
            training_data: List of dicts with 'text', 'label' keys
        """
        # Simple feature weight adjustment based on training data
        # In production, this would use proper ML (scikit-learn, PyTorch, etc.)

        positive_examples = [d for d in training_data if d.get('label', 0) == 1]
        negative_examples = [d for d in training_data if d.get('label', 0) == 0]

        if not positive_examples:
            print("Warning: No positive examples in training data")
            return

        # Adjust weights based on feature frequency in positive examples
        for example in positive_examples:
            features = self.extract_features(example['text'])
            for feature, value in features.items():
                if value > 0:
                    # Increase weight for features that appear in positive examples
                    self.feature_weights[feature] = self.feature_weights.get(feature, 0.5) * 1.1

        # Normalize weights
        max_weight = max(self.feature_weights.values()) if self.feature_weights else 1.0
        for feature in self.feature_weights:
            self.feature_weights[feature] /= max_weight

        self.trained = True
        print(f"Trained on {len(training_data)} examples ({len(positive_examples)} positive)")

    def save(self, filepath: str):
        """Save classifier state."""
        state = {
            'feature_weights': self.feature_weights,
            'threshold': self.threshold,
            'trained': self.trained
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load(self, filepath: str):
        """Load classifier state."""
        with open(filepath, 'r') as f:
            state = json.load(f)
        self.feature_weights = state['feature_weights']
        self.threshold = state['threshold']
        self.trained = state['trained']


class EnsembleMetaCognitiveEvaluator:
    """
    Ensemble evaluator combining rule-based and ML approaches.

    Uses both the enhanced pattern matching and ML classifier,
    combining their predictions for more robust evaluation.
    """

    def __init__(self):
        """Initialize ensemble evaluator."""
        try:
            from .data_sufficiency_evaluator import EnhancedDataSufficiencyEvaluator
            self.rule_based = EnhancedDataSufficiencyEvaluator()
            self.rule_based_available = True
        except ImportError:
            self.rule_based = None
            self.rule_based_available = False

        self.ml_classifier = MetaCognitiveClassifier()
        self.ensemble_weights = {'rule': 0.6, 'ml': 0.4}  # Weight rule-based higher initially

    def evaluate_task(self, scenario: str, question: str) -> Dict:
        """
        Evaluate task using ensemble approach.

        Args:
            scenario: Task scenario
            question: Task question

        Returns:
            Dictionary with ensemble prediction
        """
        results = {
            'scenario': scenario,
            'question': question,
            'rule_based': None,
            'ml_classifier': None,
            'ensemble': None
        }

        # Rule-based evaluation
        if self.rule_based_available and self.rule_based:
            try:
                rule_result = self.rule_based.evaluate_task(scenario, question)
                results['rule_based'] = {
                    'sufficient': rule_result.sufficiency.value,
                    'limitation_type': rule_result.limitation_type.value if rule_result.limitation_type else None,
                    'confidence': rule_result.confidence,
                    'justification': rule_result.justification
                }
            except Exception as e:
                print(f"Warning: Rule-based evaluation failed: {e}")

        # ML classifier
        try:
            ml_result = self.ml_classifier.classify(scenario, question)
            results['ml_classifier'] = {
                'is_meta_cognitive': ml_result.is_meta_cognitive,
                'confidence': ml_result.confidence,
                'predicted_limitation': ml_result.predicted_limitation,
                'reasoning': ml_result.reasoning
            }
        except Exception as e:
            print(f"Warning: ML classification failed: {e}")

        # Ensemble decision
        results['ensemble'] = self._ensemble_decision(results)

        return results

    def _ensemble_decision(self, results: Dict) -> Dict:
        """
        Make ensemble decision from rule-based and ML results.

        Args:
            results: Dictionary with rule_based and ml_classifier results

        Returns:
            Ensemble decision
        """
        rule_result = results.get('rule_based')
        ml_result = results.get('ml_classifier')

        # If only one available, use it
        if rule_result is None:
            return {
                'method': 'ml_only',
                'is_meta_cognitive': ml_result['is_meta_cognitive'],
                'confidence': ml_result['confidence'],
                'reasoning': 'Using ML only (rule-based unavailable)'
            }

        if ml_result is None:
            return {
                'method': 'rule_only',
                'is_meta_cognitive': rule_result['sufficient'] != 'sufficient',
                'confidence': rule_result['confidence'],
                'reasoning': rule_result['justification']
            }

        # Both available - combine
        rule_meta = rule_result['sufficient'] != 'sufficient'
        ml_meta = ml_result['is_meta_cognitive']

        # Weighted decision
        ensemble_score = (
            self.ensemble_weights['rule'] * (1.0 if rule_meta else 0.0) +
            self.ensemble_weights['ml'] * (1.0 if ml_meta else 0.0)
        )

        is_meta = ensemble_score >= 0.5

        # Average confidence
        confidence = (rule_result['confidence'] + ml_result['confidence']) / 2.0

        return {
            'method': 'ensemble',
            'is_meta_cognitive': is_meta,
            'confidence': confidence,
            'ensemble_score': ensemble_score,
            'rule_agrees': rule_meta == ml_meta,
            'reasoning': f"Ensemble: rule={rule_meta}, ml={ml_meta}, score={ensemble_score:.3f}"
        }


def create_ml_classifier() -> MetaCognitiveClassifier:
    """Factory function to create ML classifier."""
    return MetaCognitiveClassifier()


def create_ensemble_evaluator() -> EnsembleMetaCognitiveEvaluator:
    """Factory function to create ensemble evaluator."""
    return EnsembleMetaCognitiveEvaluator()


# Export symbols
__all__ = [
    'MetaCognitiveClassifier',
    'ClassificationResult',
    'EnsembleMetaCognitiveEvaluator',
    'create_ml_classifier',
    'create_ensemble_evaluator',
]
