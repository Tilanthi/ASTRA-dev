"""
V7.0 Autonomous Scientist - Main System

Orchestrates all V7.0 engines to conduct autonomous scientific research.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

# Import shared types
from .types import (
    ResearchCycle, ResearchQuestion, Hypothesis, Experiment,
    ResearchResult, Publication,
    QuestionType, QuestionImportance, HypothesisType, HypothesisStatus,
    ExperimentType, DesignParameters, DataSource, ExecutionResult,
    PredictionType, PredictionConfidence, AnalysisType, CausalInferenceResult,
    RevisionType, TheoryStatus, PaperStructure, FigureType
)

# Import all engines
from .engines.question_generator import QuestionGenerator
from .engines.hypothesis_formulator import HypothesisFormulator
from .engines.experiment_designer import ExperimentDesigner
from .engines.experiment_executor import ExperimentExecutor
from .engines.prediction_engine import (
    PredictionEngine, AnalysisEngine, TheoryRevisionEngine, PublicationEngine
)

# Import architectural components
from .architecture.global_coherence import (
    GlobalCoherenceLayer, HierarchicalUnderstanding,
    AnalogicalReasoning, ContinuousLearning, ScientificTaste
)


class V7AutonomousScientist:
    """
    V7.0 Autonomous Research Scientist

    An autonomous scientific research system capable of conducting
    the entire research cycle from question to publication.
    """

    def __init__(self):
        """Initialize the autonomous scientist"""
        print("[V7.0] Initializing Autonomous Research Scientist...")

        # Initialize all engines
        self.question_generator = QuestionGenerator()
        self.hypothesis_formulator = HypothesisFormulator()
        self.experiment_designer = ExperimentDesigner()
        self.experiment_executor = ExperimentExecutor()
        self.prediction_engine = PredictionEngine()
        self.analysis_engine = AnalysisEngine()
        self.theory_revision = TheoryRevisionEngine()
        self.publication_engine = PublicationEngine()

        # Initialize architectural components
        self.coherence_layer = GlobalCoherenceLayer()
        self.hierarchical = HierarchicalUnderstanding()
        self.analogical = AnalogicalReasoning()
        self.continuous = ContinuousLearning()
        self.taste = ScientificTaste()

        # Research state
        self.current_cycle = ResearchCycle.QUESTION
        self.research_history = []
        self.knowledge_base = {}
        self.active_questions = []
        self.active_hypotheses = []
        self.completed_experiments = []

        print("[V7.0] ✓ All engines initialized")
        print("[V7.0] ✓ Architectural components ready")
        print("[V7.0] ✓ Autonomous Scientist ready")

    def generate_research_questions(
        self,
        domain: str,
        context: Optional[Dict[str, Any]] = None,
        num_questions: int = 5
    ) -> List[ResearchQuestion]:
        """
        Generate important research questions in a domain.

        Args:
            domain: Scientific domain
            context: Additional context
            num_questions: Number of questions to generate

        Returns:
            List of research questions ranked by importance
        """
        print(f"\n[V7.0] Generating research questions for: {domain}")

        # Use question generator
        questions = self.question_generator.identify_gaps(
            domain,
            context or {}
        )

        # Score importance
        for question in questions:
            importance = self.taste.score_importance(question, domain)
            question.importance = importance
            question.feasibility = self.question_generator.assess_feasibility(question)
            question.expected_impact = importance * 0.7 + question.feasibility * 0.3

        # Sort by expected impact
        questions.sort(key=lambda q: q.expected_impact, reverse=True)

        self.active_questions.extend(questions[:num_questions])

        print(f"[V7.0] Generated {len(questions[:num_questions])} research questions")

        return questions[:num_questions]

    def formulate_hypotheses(
        self,
        question: ResearchQuestion,
        num_hypotheses: int = 3
    ) -> List[Dict]:
        """
        Formulate testable hypotheses for a research question.

        Args:
            question: Research question
            num_hypotheses: Number of hypotheses to generate

        Returns:
            List of hypotheses
        """
        print(f"\n[V7.0] Formulating hypotheses for: {question.question}")

        # Use hypothesis formulator
        hypotheses = self.hypothesis_formulator.generate_hypotheses(
            question,
            num_hypotheses
        )

        # Score hypotheses
        for hyp in hypotheses:
            hyp['novelty_score'] = self._assess_hypothesis_novelty(hyp)
            hyp['confidence'] = self._assess_hypothesis_confidence(hyp)

        self.active_hypotheses.extend(hypotheses)

        print(f"[V7.0] Formulated {len(hypotheses)} hypotheses")

        return hypotheses

    def design_experiments(
        self,
        hypothesis: Dict,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Design experiments to test a hypothesis.

        Args:
            hypothesis: Hypothesis to test
            constraints: Resource constraints

        Returns:
            List of experimental designs
        """
        print(f"\n[V7.0] Designing experiments for: {hypothesis.get('statement', hypothesis['statement'])}")

        # Use experiment designer
        experiments = self.experiment_designer.design_experiments(
            hypothesis,
            constraints or {}
        )

        # Optimize designs
        for exp in experiments:
            self.experiment_designer.optimize_design(exp)

        print(f"[V7.0] Designed {len(experiments)} experiments")

        return experiments

    def execute_experiments(
        self,
        experiments: List[Dict],
        parallel: bool = True
    ) -> List[Dict]:
        """
        Execute experiments and collect results.

        Args:
            experiments: Experiments to execute
            parallel: Whether to run in parallel

        Returns:
            List of research results
        """
        print(f"\n[V7.0] Executing {len(experiments)} experiments...")

        results = []

        for exp in experiments:
            print(f"[V7.0] Executing: {exp['name']}")

            # Execute experiment
            execution_result = self.experiment_executor.execute(exp)

            # Analyze results
            analysis = self.analysis_engine.analyze(
                execution_result,
                exp['objective']
            )

            # Create research result
            result = ResearchResult(
                experiment_name=exp['name'],
                execution_result=execution_result,
                analysis_results=analysis,
                predictions_validated=[],
                predictions_refuted=[],
                new_discoveries=[],
                confidence=execution_result.success_rate
            )

            results.append(result)
            self.completed_experiments.append(result)

        print(f"[V7.0] Completed {len(results)} experiments")

        return results

    def analyze_and_predict(
        self,
        results: List[ResearchResult],
        hypothesis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze results and generate predictions.

        Args:
            results: Experimental results
            hypothesis: Original hypothesis

        Returns:
            Analysis summary with predictions
        """
        print(f"\n[V7.0] Analyzing results and generating predictions...")

        # Comprehensive analysis
        full_analysis = self.analysis_engine.comprehensive_analysis(
            results,
            hypothesis
        )

        # Generate predictions
        predictions = self.prediction_engine.generate_predictions(
            full_analysis,
            hypothesis
        )

        # Assess hypothesis status
        hypothesis_status = self.theory_revision.assess_hypothesis(
            hypothesis,
            results,
            predictions
        )

        summary = {
            'analysis': full_analysis,
            'predictions': predictions,
            'hypothesis_status': hypothesis_status,
            'confidence': full_analysis.get('overall_confidence', 0.5)
        }

        print(f"[V7.0] Analysis complete")
        print(f"[V7.0] Generated {len(predictions)} predictions")
        print(f"[V7.0] Hypothesis status: {hypothesis_status}")

        return summary

    def revise_theory(
        self,
        analysis: Dict[str, Any],
        domain: str
    ) -> Dict[str, Any]:
        """
        Revise theoretical frameworks based on analysis.

        Args:
            analysis: Analysis results
            domain: Scientific domain

        Returns:
            Theory revision summary
        """
        print(f"\n[V7.0] Revising theoretical frameworks...")

        # Identify necessary revisions
        revisions = self.theory_revision.identify_revisions(
            analysis,
            domain
        )

        # Apply revisions
        for revision in revisions:
            self.theory_revision.apply_revision(
                revision,
                self.knowledge_base
            )

        # Check for paradigm shifts
        paradigm_shift = self.theory_revision.detect_paradigm_shift(
            revisions,
            domain
        )

        summary = {
            'revisions': revisions,
            'paradigm_shift': paradigm_shift,
            'updated_theories': self.theory_revision.list_updated_theories()
        }

        print(f"[V7.0] Applied {len(revisions)} revisions")

        return summary

    def write_publication(
        self,
        research_summary: Dict[str, Any],
        target_journal: str = "Astronomy & Astrophysics"
    ) -> Publication:
        """
        Generate a publication-ready paper.

        Args:
            research_summary: Complete research summary
            target_journal: Target journal

        Returns:
            Publication-ready paper
        """
        print(f"\n[V7.0] Writing publication for {target_journal}...")

        # Generate paper
        publication_dict = self.publication_engine.generate_paper(
            research_summary,
            target_journal
        )

        # Create figures
        figures = self.publication_engine.create_figures(
            research_summary,
            publication_dict['structure']
        )

        # Create tables
        tables = self.publication_engine.create_tables(
            research_summary
        )

        # Create Publication object from dict
        publication = Publication(
            title=publication_dict['title'],
            abstract=publication_dict['abstract'],
            authors=publication_dict['authors'],
            structure=publication_dict['structure'],
            figures=figures,
            tables=tables,
            references=publication_dict.get('references', []),
            target_journal=publication_dict['target_journal'],
            publication_status=publication_dict['publication_status']
        )

        print(f"[V7.0] Publication generated: {publication.title}")
        print(f"[V7.0] Abstract: {publication.abstract[:200]}...")

        return publication

    def conduct_full_research_cycle(
        self,
        domain: str,
        research_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Conduct a complete autonomous research cycle.

        Args:
            domain: Scientific domain
            research_context: Additional context

        Returns:
            Complete research results with publication
        """
        print("\n" + "="*80)
        print("V7.0 AUTONOMOUS RESEARCH CYCLE")
        print("="*80)
        print(f"Domain: {domain}")
        print("="*80)

        # Phase 1: Generate questions
        questions = self.generate_research_questions(
            domain,
            research_context,
            num_questions=3
        )

        # Select top question
        top_question = questions[0]
        print(f"\n[V7.0] Selected research question:")
        print(f"  {top_question.question}")
        print(f"  Importance: {top_question.importance}")
        print(f"  Expected impact: {top_question.expected_impact:.2f}")

        # Phase 2: Formulate hypotheses
        hypotheses = self.formulate_hypotheses(
            top_question,
            num_hypotheses=3
        )

        # Select top hypothesis
        top_hypothesis = hypotheses[0]
        print(f"\n[V7.0] Selected hypothesis:")
        print(f"  {top_hypothesis.get('statement', top_hypothesis['statement'])}")
        print(f"  Novelty: {top_hypothesis.get('novelty_score', 0.7):.2f}")
        print(f"  Confidence: {top_hypothesis.get('confidence', 0.7):.2f}")

        # Phase 3: Design experiments
        experiments = self.design_experiments(
            top_hypothesis,
            constraints={'budget': 'moderate', 'time': '6 months'}
        )

        # Phase 4: Execute experiments
        results = self.execute_experiments(
            experiments[:1],  # Execute one experiment for demo
            parallel=False
        )

        # Phase 5: Analyze and predict
        analysis = self.analyze_and_predict(
            results,
            top_hypothesis
        )

        # Phase 6: Revise theory
        theory_update = self.revise_theory(
            analysis,
            domain
        )

        # Phase 7: Write publication
        research_summary = {
            'question': top_question,
            'hypothesis': top_hypothesis,
            'experiments': experiments,
            'results': results,
            'analysis': analysis,
            'theory_update': theory_update
        }

        publication = self.write_publication(
            research_summary,
            target_journal="Astronomy & Astrophysics"
        )

        # Compile final report
        final_report = {
            'research_question': top_question,
            'hypothesis': top_hypothesis,
            'experiments_designed': len(experiments),
            'experiments_executed': len(results),
            'predictions': len(analysis['predictions']),
            'theory_revisions': len(theory_update['revisions']),
            'publication': publication,
            'success': True
        }

        print("\n" + "="*80)
        print("RESEARCH CYCLE COMPLETE")
        print("="*80)
        print(f"Question: {top_question.question}")
        print(f"Hypothesis: {top_hypothesis.get('statement', top_hypothesis['statement'])}")
        print(f"Experiments: {len(experiments)} designed, {len(results)} executed")
        print(f"Predictions: {len(analysis['predictions'])} generated")
        print(f"Theory revisions: {len(theory_update['revisions'])}")
        print(f"Publication: {publication.title}")
        print("="*80)

        # Add to history
        self.research_history.append(final_report)

        return final_report

    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'engines': {
                'question_generator': True,
                'hypothesis_formulator': True,
                'experiment_designer': True,
                'experiment_executor': True,
                'prediction_engine': True,
                'analysis_engine': True,
                'theory_revision': True,
                'publication_engine': True
            },
            'architecture': {
                'global_coherence': True,
                'hierarchical_understanding': True,
                'analogical_reasoning': True,
                'continuous_learning': True,
                'scientific_taste': True
            },
            'research_state': {
                'current_cycle': self.current_cycle.value,
                'active_questions': len(self.active_questions),
                'active_hypotheses': len(self.active_hypotheses),
                'completed_experiments': len(self.completed_experiments),
                'research_history': len(self.research_history)
            }
        }

    def _assess_hypothesis_novelty(self, hypothesis: Dict) -> float:
        """Assess novelty of hypothesis (0-1)"""
        # Base novelty on type and specificity
        type_novelty = {
            'theoretical': 0.7,
            'empirical': 0.6,
            'causal': 0.8,
            'analogical': 0.5,
            'explanatory': 0.4,
            'predictive': 0.6
        }

        base_score = type_novelty.get(hypothesis.get('type', 'theoretical'), 0.5)

        # Increase novelty if multiple predictions
        prediction_bonus = min(0.2, len(hypothesis.get('predictions', [])) * 0.05)

        return min(1.0, base_score + prediction_bonus)

    def _assess_hypothesis_confidence(self, hypothesis: Dict) -> float:
        """Assess confidence in hypothesis (0-1)"""
        # Base confidence on theoretical basis
        theory_count = len(hypothesis.get('theoretical_basis', []))
        base_score = min(0.9, 0.5 + theory_count * 0.1)

        # Reduce confidence if very novel
        novelty = hypothesis.get('novelty_score', 0.5)
        novelty_penalty = novelty * 0.2

        return max(0.3, base_score - novelty_penalty)


def create_v7_scientist() -> V7AutonomousScientist:
    """
    Factory function to create V7.0 Autonomous Scientist.

    Returns:
        Initialized V7AutonomousScientist instance
    """
    return V7AutonomousScientist()
