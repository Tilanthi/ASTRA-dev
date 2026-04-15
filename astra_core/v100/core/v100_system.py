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
V100 Autonomous Scientific Discovery Engine
============================================

The unified V100 system - a closed-loop autonomous scientific discovery engine.

Integrates all V100 components:
- UTSE: Universal Theory Synthesis Engine (theory generation)
- FPUS: First-Principles Universe Simulator (prediction simulation)
- AAEA: Automated Archive Exploration Agent (data retrieval)
- BEDE: Bayesian Experimental Design Engine (observation planning)
- SVC: Scientific Value Calculator (value assessment)
- MTCS: Multi-Theory Competition System (theory selection)
- HITLI: Human-in-the-Loop Interface (collaborative refinement)
- Validation: Autonomous paper generation (publication)

This is the complete V100 system for autonomous scientific discovery.

Author: STAN-XI ASTRO V100 Development Team
Version: 100.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum, auto
import numpy as np
import time
from pathlib import Path


# =============================================================================
# Import all V100 components
# =============================================================================
try:
    from ..theory.theory_synthesis import TheorySynthesisEngine, TheoryFramework
    from ..simulation.universe_simulator import UniverseSimulator, PredictionResult
    from ..archive.archive_explorer import ArchiveExplorer, DatasetCollection
    from ..design.bayesian_design import BayesianExperimentalDesigner, ObservationSequence
    from ..value.scientific_value import ScientificValueCalculator, ScientificValue, DiscoveryType, DomainImpact, ResourceBudget
    from .validation import ValidationEngine, ValidationResult, ScientificPaper, ValidationStatus
    from .competition import TheoryCompetitionEngine, CompetitionResult, CompetitionStrategy
    from .human_interface import HumanInterfaceManager, InteractionMode, CollaborationSession, FeedbackType
except ImportError as e:
    print(f"Warning: Could not import V100 components: {e}")
    TheorySynthesisEngine = None
    UniverseSimulator = None
    ArchiveExplorer = None
    BayesianExperimentalDesigner = None
    ScientificValueCalculator = None
    ValidationEngine = None
    TheoryCompetitionEngine = None
    HumanInterfaceManager = None


# =============================================================================
# Enumerations
# =============================================================================

class DiscoveryPhase(Enum):
    """Phases of the discovery cycle"""
    INITIALIZATION = "initialization"
    DATA_COLLECTION = "data_collection"
    THEORY_GENERATION = "theory_generation"
    THEORY_COMPETITION = "theory_competition"
    PREDICTION = "prediction"
    EXPERIMENT_DESIGN = "experiment_design"
    VALIDATION = "validation"
    PUBLICATION = "publication"
    REFINEMENT = "refinement"
    COMPLETE = "complete"


class SystemMode(Enum):
    """Operating modes for V100"""
    FULLY_AUTONOMOUS = "autonomous"  # No human intervention
    HUMAN_GUIDED = "guided"  # Human provides high-level direction
    COLLABORATIVE = "collaborative"  # Human-AI partnership
    COMPETITIVE = "competitive"  # Multiple theories compete
    VALIDATION_FOCUSED = "validation"  # Focus on validation


class StoppingCriterion(Enum):
    """Criteria for stopping the discovery cycle"""
    TARGET_CONFIDENCE = "confidence"  # Stop when confidence threshold reached
    TARGET_VALUE = "value"  # Stop when scientific value threshold reached
    TIME_BUDGET = "time"  # Stop after time limit
    ITERATION_LIMIT = "iterations"  # Stop after N iterations
    SATURATION = "saturation"  # Stop when improvements plateau
    MANUAL = "manual"  # Wait for human decision


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class DiscoveryCycle:
    """One complete iteration of the discovery cycle"""
    cycle_number: int
    phase: DiscoveryPhase

    # Artifacts
    theory: Optional[TheoryFramework] = None
    predictions: Optional[Dict[str, Any]] = None
    data: Optional[DatasetCollection] = None
    validation: Optional[ValidationResult] = None
    value: Optional[ScientificValue] = None
    paper: Optional[ScientificPaper] = None

    # Metrics
    confidence: float = 0.5
    novelty: float = 0.5
    scientific_value: float = 50.0

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    def duration_hours(self) -> float:
        """Get cycle duration in hours"""
        end = self.end_time or time.time()
        return (end - self.start_time) / 3600


@dataclass
class V100SystemState:
    """Complete state of the V100 system"""
    current_phase: DiscoveryPhase
    mode: SystemMode
    cycle_number: int
    total_cycles: int

    # Best theory so far
    best_theory: Optional[TheoryFramework] = None
    best_confidence: float = 0.0

    # All cycles
    cycles: List[DiscoveryCycle] = field(default_factory=list)

    # Current iteration
    current_cycle: Optional[DiscoveryCycle] = None

    # System status
    running: bool = False
    paused: bool = False
    stopped: bool = False

    # Performance metrics
    total_time_hours: float = 0.0
    total_value_generated: float = 0.0
    theories_generated: int = 0
    predictions_made: int = 0
    papers_generated: int = 0


@dataclass
class V100Config:
    """Configuration for V100 system"""
    # Operating mode
    mode: SystemMode = SystemMode.FULLY_AUTONOMOUS

    # Stopping criteria
    stopping_criterion: StoppingCriterion = StoppingCriterion.TARGET_CONFIDENCE
    target_confidence: float = 0.95
    target_value: float = 75.0
    max_iterations: int = 10
    max_time_hours: float = 24.0
    saturation_threshold: float = 0.01  # Improvement threshold

    # Theory generation
    n_theories_per_cycle: int = 3
    use_competition: bool = True

    # Data collection
    max_data_volume_tb: float = 10.0
    auto_download: bool = True

    # Validation
    generate_papers: bool = True
    auto_publish: bool = False  # Requires human approval

    # Human interaction
    enable_human_feedback: bool = False
    feedback_frequency: int = 2  # Ask every N cycles

    # Budget
    max_computing_hours: float = 100.0
    max_cost_dollars: float = 10000.0

    # Output
    output_dir: str = "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/data/v100_output"
    save_intermediate: bool = True


# =============================================================================
# V100 Discovery Engine
# =============================================================================

class V100DiscoveryEngine:
    """
    The complete V100 Autonomous Scientific Discovery Engine.

    Closed-loop discovery cycle:
    1. Data Collection (AAEA): Retrieve relevant data
    2. Theory Generation (UTSE): Synthesize explanatory theories
    3. Theory Competition (MTCS): Select best theory
    4. Prediction (FPUS): Generate testable predictions
    5. Experiment Design (BEDE): Plan validation experiments
    6. Validation (Validation): Test against existing/new data
    7. Value Assessment (SVC): Calculate scientific value
    8. Publication: Generate paper or continue
    9. Human Feedback (HITLI): Incorporate expert input
    10. Decision: Continue or stop?

    This cycle continues until stopping criteria are met.
    """

    def __init__(self, config: Optional[V100Config] = None):
        self.config = config or V100Config()

        # Initialize all V100 components
        print("V100: Initializing Autonomous Scientific Discovery Engine")

        self.theory_engine = TheorySynthesisEngine() if TheorySynthesisEngine else None
        self.simulator = UniverseSimulator() if UniverseSimulator else None
        self.archive_explorer = ArchiveExplorer() if ArchiveExplorer else None
        self.designer = BayesianExperimentalDesigner() if BayesianExperimentalDesigner else None
        self.value_calculator = ScientificValueCalculator() if ScientificValueCalculator else None
        self.validation_engine = ValidationEngine() if ValidationEngine else None
        self.competition_engine = TheoryCompetitionEngine() if TheoryCompetitionEngine else None
        self.human_interface = HumanInterfaceManager(mode=InteractionMode.COLLABORATIVE) if HumanInterfaceManager else None

        # System state
        self.state = V100SystemState(
            current_phase=DiscoveryPhase.INITIALIZATION,
            mode=self.config.mode,
            cycle_number=0,
            total_cycles=0
        )

        print(f"V100: Mode = {self.config.mode.value}")
        print(f"V100: Max iterations = {self.config.max_iterations}")
        print(f"V100: Target confidence = {self.config.target_confidence:.0%}")

    def discover(
        self,
        problem_statement: str,
        domain: str = "astrophysics",
        initial_data_path: Optional[str] = None
    ) -> CollaborationSession:
        """
        Run autonomous scientific discovery on a problem.

        Parameters
        ----------
        problem_statement : str
            Clear description of scientific problem
        domain : str
            Scientific domain
        initial_data_path : str, optional
            Path to initial data

        Returns
        -------
        CollaborationSession with complete discovery history
        """
        print(f"\n{'='*70}")
        print(f"V100 AUTONOMOUS SCIENTIFIC DISCOVERY")
        print(f"{'='*70}")
        print(f"Problem: {problem_statement}")
        print(f"Domain: {domain}")
        print(f"Mode: {self.config.mode.value}")
        print(f"{'='*70}\n")

        # Create session
        session = self.human_interface.create_session(
            problem_name=problem_statement,
            experts=["V100_System"],
            mode=InteractionMode.FULLY_AUTONOMOUS
        ) if self.human_interface else None

        # Initialize
        self.state.running = True
        self.state.current_phase = DiscoveryPhase.DATA_COLLECTION

        # Main discovery loop
        for iteration in range(self.config.max_iterations):
            if not self.state.running:
                break

            self.state.cycle_number = iteration + 1

            print(f"\n{'='*70}")
            print(f"CYCLE {self.state.cycle_number}")
            print(f"{'='*70}\n")

            # Run one discovery cycle
            cycle = self._run_discovery_cycle(
                problem_statement, domain, initial_data_path
            )

            self.state.cycles.append(cycle)
            self.state.current_cycle = cycle

            # Update best theory
            if cycle.theory and cycle.confidence > self.state.best_confidence:
                self.state.best_theory = cycle.theory
                self.state.best_confidence = cycle.confidence
                print(f"  New best theory! Confidence: {cycle.confidence:.2%}")

            # Check stopping criteria
            if self._should_stop(cycle):
                print(f"\n  Stopping criterion met: {self._get_stop_reason(cycle)}")
                break

            # Check for human feedback
            if (self.config.enable_human_feedback and
                iteration % self.config.feedback_frequency == 0):
                self._request_human_feedback(cycle, session)

        # Finalize
        self.state.current_phase = DiscoveryPhase.COMPLETE
        self.state.stopped = True
        self.state.total_cycles = self.state.cycle_number

        print(f"\n{'='*70}")
        print(f"V100 DISCOVERY COMPLETE")
        print(f"{'='*70}")
        print(f"Total cycles: {self.state.total_cycles}")
        print(f"Best confidence: {self.state.best_confidence:.2%}")
        print(f"Theories generated: {self.state.theories_generated}")
        print(f"Papers generated: {self.state.papers_generated}")
        print(f"Total time: {self.state.total_time_hours:.1f} hours")
        print(f"{'='*70}\n")

        return session

    def _run_discovery_cycle(
        self,
        problem_statement: str,
        domain: str,
        initial_data_path: Optional[str]
    ) -> DiscoveryCycle:
        """Run one complete discovery cycle"""

        cycle = DiscoveryCycle(
            cycle_number=self.state.cycle_number,
            phase=DiscoveryPhase.INITIALIZATION
        )

        # Phase 1: Data Collection
        cycle.phase = DiscoveryPhase.DATA_COLLECTION
        print("Phase 1: Data Collection")
        data = self._collect_data(problem_statement, initial_data_path)
        cycle.data = data

        # Phase 2: Theory Generation
        cycle.phase = DiscoveryPhase.THEORY_GENERATION
        print("\nPhase 2: Theory Generation")

        if self.config.use_competition and self.competition_engine:
            theory = self._generate_theory_with_competition(
                problem_statement, data
            )
        else:
            theory = self._generate_single_theory(
                problem_statement, data
            )

        cycle.theory = theory
        self.state.theories_generated += 1

        # Phase 3: Prediction
        cycle.phase = DiscoveryPhase.PREDICTION
        print("\nPhase 3: Prediction")
        predictions = self._generate_predictions(theory, problem_statement)
        cycle.predictions = predictions
        self.state.predictions_made += 1

        # Phase 4: Experiment Design
        cycle.phase = DiscoveryPhase.EXPERIMENT_DESIGN
        print("\nPhase 4: Experiment Design")
        experiment_plan = self._design_experiments(theory, predictions)
        cycle.experiments = experiment_plan

        # Phase 5: Validation
        cycle.phase = DiscoveryPhase.VALIDATION
        print("\nPhase 5: Validation")
        validation = self._validate_theory(theory, predictions, data)
        cycle.validation = validation
        cycle.confidence = validation.confidence

        # Phase 6: Value Assessment
        cycle.phase = DiscoveryPhase.VALIDATION  # Reuse phase
        print("\nPhase 6: Value Assessment")
        value = self._assess_value(theory, problem_statement)
        cycle.value = value
        cycle.scientific_value = value.total_score

        # Phase 7: Publication
        cycle.phase = DiscoveryPhase.PUBLICATION
        print("\nPhase 7: Publication")
        paper = self._generate_paper(theory, validation, problem_statement)
        cycle.paper = paper
        self.state.papers_generated += 1

        # Update metrics
        cycle.end_time = time.time()
        self.state.total_time_hours += cycle.duration_hours()
        self.state.total_value_generated += value.total_score

        print(f"\n  Cycle {self.state.cycle_number} Summary:")
        print(f"    Theory: {theory.name if theory else 'None'}")
        print(f"    Confidence: {cycle.confidence:.2%}")
        print(f"    Scientific Value: {cycle.scientific_value:.1f}/100")
        print(f"    Duration: {cycle.duration_hours():.2f} hours")

        return cycle

    def _collect_data(
        self,
        problem_statement: str,
        initial_data_path: Optional[str]
    ) -> DatasetCollection:
        """Collect relevant data"""
        if not self.archive_explorer:
            return DatasetCollection(
                id="dummy_collection",
                name="Dummy Data",
                description="No data available"
            )

        return self.archive_explorer.explore(
            science_question=problem_statement,
            max_data_volume_tb=self.config.max_data_volume_tb
        )

    def _generate_single_theory(
        self,
        problem_statement: str,
        data: DatasetCollection
    ) -> Optional[TheoryFramework]:
        """Generate a single theory"""
        if not self.theory_engine:
            return None

        # Convert data to evidence format
        evidence = {'data_collection': data.get_summary()}

        # Generate contradictions (placeholder)
        contradictions = []

        theories = self.theory_engine.synthesize_theory(
            evidence=evidence,
            contradictions=contradictions,
            domain_boundaries=[],
            max_theories=1
        )

        return theories[0] if theories else None

    def _generate_theory_with_competition(
        self,
        problem_statement: str,
        data: DatasetCollection
    ) -> Optional[TheoryFramework]:
        """Generate theory through competition"""
        if not self.competition_engine:
            return self._generate_single_theory(problem_statement, data)

        # Convert data to evidence format
        evidence = {'data_collection': data.get_summary()}
        contradictions = []

        # Run competition
        result = self.competition_engine.run_competition(
            problem_name=problem_statement,
            evidence=evidence,
            contradictions=contradictions,
            n_theories=self.config.n_theories_per_cycle,
            strategy=CompetitionStrategy.SURVIVAL_OF_FITTEST
        )

        # Return winning theory
        if result.winning_theory and result.winning_theory in self.competition_engine.theory_registry:
            winner = self.competition_engine.theory_registry[result.winning_theory]
            print(f"    Winner: {winner.name} (confidence: {result.confidence_in_winner:.2%})")
            return winner

        return None

    def _generate_predictions(
        self,
        theory: Optional[TheoryFramework],
        problem_statement: str
    ) -> Dict[str, Any]:
        """Generate predictions from theory"""
        if not theory or not self.simulator:
            return {}

        # Use simulator to generate predictions
        result = self.simulator.simulate_filament_evolution(
            initial_density=100.0,
            temperature=15.0,
            magnetic_field=10e-6,
            turbulence=2.0,
            external_pressure=5e4,
            duration_myr=2.0
        )

        return result.predictions

    def _design_experiments(
        self,
        theory: Optional[TheoryFramework],
        predictions: Dict[str, Any]
    ) -> Optional[ObservationSequence]:
        """Design validation experiments"""
        if not self.designer:
            return None

        # Create placeholder belief state
        from ..design.bayesian_design import PosteriorDistribution
        belief = PosteriorDistribution(
            mean=np.array([0.5]),
            covariance=np.array([[0.1]]),
            parameter_names=['filament_width']
        )

        # Placeholder theories
        from ..design.bayesian_design import Theory
        theories = [Theory(
            name=theory.name if theory else "placeholder",
            parameters={},
            predictions={},
            uncertainties={}
        )]

        # Available observations
        available_obs = [
            {
                'observable': 'filament_width',
                'facility': 'ALMA',
                'instrument': 'ALMA',
                'time_hours': 5.0,
                'cost': 5000
            }
        ]

        return self.designer.design_observation_sequence(
            current_belief=belief,
            theories=theories,
            available_observations=available_obs,
            budget_time_hours=50.0,
            budget_cost_dollars=self.config.max_cost_dollars
        )

    def _validate_theory(
        self,
        theory: Optional[TheoryFramework],
        predictions: Dict[str, Any],
        data: DatasetCollection
    ) -> ValidationResult:
        """Validate theory against data"""
        if not self.validation_engine:
            return ValidationResult(
                theory_id="none",
                validation_problem="none",
                predictions_tested=0,
                predictions_confirmed=0,
                predictions_refuted=0,
                inconclusive=0,
                overall_status=ValidationStatus.PENDING,
                confidence=0.5
            )

        return self.validation_engine._validate(
            theory=theory,
            predictions=predictions,
            evidence={'data': data.get_summary()}
        )

    def _assess_value(
        self,
        theory: Optional[TheoryFramework],
        problem_statement: str
    ) -> ScientificValue:
        """Assess scientific value"""
        if not self.value_calculator:
            return ScientificValue(
                total_score=50.0,
                dimensions=None,
                discovery_type=DiscoveryType.NEW_MECHANISM,
                affected_domains=[DomainImpact.ASTROPHYSICS],
                confidence=0.5
            )

        return self.value_calculator.calculate_value(
            discovery_description=problem_statement,
            discovery_type=DiscoveryType.NEW_MECHANISM,
            affected_domains=[DomainImpact.ASTROPHYSICS],
            resources=ResourceBudget(
                time_months=1.0,
                people_fte=0.0,  # Autonomous
                cost_dollars=10000.0
            )
        )

    def _generate_paper(
        self,
        theory: Optional[TheoryFramework],
        validation: ValidationResult,
        problem_statement: str
    ) -> Optional[ScientificPaper]:
        """Generate publication"""
        if not theory or not self.validation_engine:
            return None

        return self.validation_engine._generate_paper(
            theory=theory,
            validation=validation,
            problem_name=problem_statement
        )

    def _should_stop(self, cycle: DiscoveryCycle) -> bool:
        """Check if stopping criteria are met"""

        if self.config.stopping_criterion == StoppingCriterion.TARGET_CONFIDENCE:
            return cycle.confidence >= self.config.target_confidence

        elif self.config.stopping_criterion == StoppingCriterion.TARGET_VALUE:
            return cycle.scientific_value >= self.config.target_value

        elif self.config.stopping_criterion == StoppingCriterion.ITERATION_LIMIT:
            return self.state.cycle_number >= self.config.max_iterations

        elif self.config.stopping_criterion == StoppingCriterion.TIME_BUDGET:
            return self.state.total_time_hours >= self.config.max_time_hours

        elif self.config.stopping_criterion == StoppingCriterion.SATURATION:
            # Check if improvement is below threshold
            if len(self.state.cycles) >= 2:
                prev_value = self.state.cycles[-2].scientific_value
                improvement = abs(cycle.scientific_value - prev_value)
                return improvement < self.config.saturation_threshold
            return False

        return False

    def _get_stop_reason(self, cycle: DiscoveryCycle) -> str:
        """Get reason for stopping"""

        if self.config.stopping_criterion == StoppingCriterion.TARGET_CONFIDENCE:
            return f"Target confidence {self.config.target_confidence:.0%} reached (actual: {cycle.confidence:.2%})"

        elif self.config.stopping_criterion == StoppingCriterion.TARGET_VALUE:
            return f"Target value {self.config.target_value} reached (actual: {cycle.scientific_value:.1f})"

        elif self.config.stopping_criterion == StoppingCriterion.ITERATION_LIMIT:
            return f"Maximum iterations ({self.config.max_iterations}) reached"

        elif self.config.stopping_criterion == StoppingCriterion.TIME_BUDGET:
            return f"Time budget ({self.config.max_time_hours} hours) exceeded"

        elif self.config.stopping_criterion == StoppingCriterion.SATURATION:
            return "Improvements saturated"

        return "Stopping criterion met"

    def _request_human_feedback(
        self,
        cycle: DiscoveryCycle,
        session: Optional[CollaborationSession]
    ):
        """Request feedback from human expert"""
        if not self.human_interface:
            return

        print("\n  [Human Feedback Requested]")

        explanation = self.human_interface.generate_human_readable_explanation(
            cycle.theory,
            detail_level="medium"
        ) if cycle.theory else "No theory generated."

        response = self.human_interface.request_human_input(
            f"Cycle {self.state.cycle_number} complete.\n\n{explanation}\n\n"
            f"Confidence: {cycle.confidence:.2%}\n"
            f"Scientific Value: {cycle.scientific_value:.1f}/100\n\n"
            f"Provide feedback or type 'continue':",
            input_type="text"
        )

        if response and response.lower() != 'continue':
            # Incorporate feedback
            feedback = self.human_interface.receive_feedback(
                feedback=response,
                feedback_type=FeedbackType.SUGGESTION,
                target_type='theory',
                target_id=cycle.theory.id if cycle.theory else None,
                session_id=session.session_id if session else None
            )

            if cycle.theory:
                cycle.theory = self.human_interface.incorporate_feedback(
                    cycle.theory,
                    [feedback]
                )

    def get_report(self) -> Dict[str, Any]:
        """Generate comprehensive report of discovery session"""
        return {
            'system_mode': self.config.mode.value,
            'total_cycles': self.state.total_cycles,
            'best_theory': self.state.best_theory.name if self.state.best_theory else None,
            'best_confidence': self.state.best_confidence,
            'theories_generated': self.state.theories_generated,
            'predictions_made': self.state.predictions_made,
            'papers_generated': self.state.papers_generated,
            'total_time_hours': self.state.total_time_hours,
            'total_value_generated': self.state.total_value_generated,
            'cycles': [
                {
                    'number': c.cycle_number,
                    'theory': c.theory.name if c.theory else None,
                    'confidence': c.confidence,
                    'value': c.scientific_value,
                    'duration_hours': c.duration_hours(),
                }
                for c in self.state.cycles
            ]
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_v100_system(
    mode: SystemMode = SystemMode.FULLY_AUTONOMOUS,
    max_iterations: int = 10,
    target_confidence: float = 0.95
) -> V100DiscoveryEngine:
    """Create a V100 discovery engine"""

    config = V100Config(
        mode=mode,
        max_iterations=max_iterations,
        target_confidence=target_confidence
    )

    return V100DiscoveryEngine(config)


def discover_autonomously(
    problem_statement: str,
    domain: str = "astrophysics",
    max_iterations: int = 10,
    target_confidence: float = 0.95
) -> Tuple[Optional[TheoryFramework], CollaborationSession, Dict[str, Any]]:
    """
    Convenience function for autonomous discovery.

    Parameters
    ----------
    problem_statement : str
        Scientific problem to solve
    domain : str
        Scientific domain
    max_iterations : int
        Maximum discovery cycles
    target_confidence : float
        Target confidence threshold

    Returns
    -------
    Tuple of (best_theory, session, report)
    """
    system = create_v100_system(
        mode=SystemMode.FULLY_AUTONOMOUS,
        max_iterations=max_iterations,
        target_confidence=target_confidence
    )

    session = system.discover(problem_statement, domain)
    report = system.get_report()

    return system.state.best_theory, session, report


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'DiscoveryPhase',
    'SystemMode',
    'StoppingCriterion',
    'DiscoveryCycle',
    'V100SystemState',
    'V100Config',
    'V100DiscoveryEngine',
    'create_v100_system',
    'discover_autonomously',
]
