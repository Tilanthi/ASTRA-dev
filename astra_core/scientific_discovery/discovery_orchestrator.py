"""
Scientific Discovery Orchestrator - Autonomous Research Conductor
=================================================================

Central coordinator for autonomous scientific discovery in astronomy
and astrophysics. Orchestrates the complete discovery cycle from
literature review through hypothesis generation, experimental design,
analysis, and synthesis.

6-Phase Discovery Loop:
1. LITERATURE REVIEW: Read and synthesize research papers
2. DATA GATHERING: Access databases and archives
3. HYPOTHESIS GENERATION: Generate novel hypotheses
4. EXPERIMENTAL DESIGN: Design experiments and observations
5. ANALYSIS & TESTING: Execute analysis and test hypotheses
6. SYNTHESIS: Integrate findings and discover new knowledge

Integrations:
- V41 Orchestrator: Complex reasoning and metacognition
- V50 Discovery Engine: World simulation and program synthesis
- V92 Scientific Discovery: Hypothesis generation and experimental design
- AstroSwarm: Physics-based Bayesian inference
- Integration Bus: Event-driven communication
- MORK: Knowledge persistence

Version: 1.0.0
Date: 2025-12-27
"""

import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pathlib import Path
import json

# Import discovery components
from .adaptive_reasoning import (
    AdaptiveReasoningController, DiscoveryPhase,
    get_adaptive_reasoning_controller
)
from .feasibility_checker import (
    FeasibilityAssessor, SafetyLimits, FeasibilityResult,
    create_feasibility_assessor
)

# Import V41, V50, V92 components (try both relative and absolute imports)
try:
    from ..reasoning.v41_orchestrator import (
        V41Orchestrator, ReasoningMode, ReasoningTask, ReasoningResult
    )
    from ..reasoning.integration_bus import (
        get_integration_bus, Event, EventType, EventPriority
    )
    from ..core_legacy.v92.v92_system import V92CompleteSystem
    from ..core_legacy.v50.v50_discovery_engine import V50DiscoveryEngine
    HAS_V41_V50_V92 = True
except (ImportError, ValueError):
    try:
        # Fallback to absolute imports
        from astra_core.reasoning.v41_orchestrator import (
            V41Orchestrator, ReasoningMode, ReasoningTask, ReasoningResult
        )
        from astra_core.reasoning.integration_bus import (
            get_integration_bus, Event, EventType, EventPriority
        )
        from astra_core.core_legacy.v92.v92_system import V92CompleteSystem
        from astra_core.core_legacy.v50.v50_discovery_engine import V50DiscoveryEngine
        HAS_V41_V50_V92 = True
    except ImportError as e:
        logging.warning(f"Could not import V41/V50/V92 components: {e}")
        HAS_V41_V50_V92 = False

# Import AstroSwarm
try:
    from ..astro_physics.core import AstroSwarmSystem
    HAS_ASTROSWARM = True
except (ImportError, ValueError):
    try:
        from astra_core.astro_physics.core import AstroSwarmSystem
        HAS_ASTROSWARM = True
    except ImportError as e:
        logging.warning(f"Could not import AstroSwarm: {e}")
        HAS_ASTROSWARM = False

# Import MORK
try:
    from ..swarm.client import MORKClient
    HAS_MORK = True
except (ImportError, ValueError):
    try:
        from astra_core.swarm.client import MORKClient
        HAS_MORK = True
    except ImportError as e:
        logging.warning(f"Could not import MORK: {e}")
        HAS_MORK = False

logger = logging.getLogger(__name__)


# =============================================================================
# Discovery Task and Result Dataclasses
# =============================================================================

@dataclass
class DiscoveryTask:
    """A scientific discovery task"""
    task_id: str
    research_question: str
    domain: str = "astrophysics"

    # Configuration
    enable_literature_review: bool = True
    enable_data_access: bool = True
    enable_hypothesis_generation: bool = True
    enable_experimental_design: bool = True
    enable_analysis: bool = True
    enable_simulations: bool = True

    # Constraints
    max_time_hours: float = 48.0
    max_papers: int = 50
    max_data_gb: float = 100.0
    safety_limits: Optional[SafetyLimits] = None

    # Context
    prior_knowledge: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)

    # Status tracking
    status: str = "pending"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"DISCOVERY-{uuid.uuid4().hex[:8]}"


@dataclass
class Hypothesis:
    """A scientific hypothesis"""
    hypothesis_id: str
    statement: str
    domain: str
    plausibility: float  # 0-1
    testability: float  # 0-1
    novelty: float  # 0-1
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    proposed_tests: List[str] = field(default_factory=list)

    def overall_score(self) -> float:
        """Calculate overall hypothesis score"""
        return (0.4 * self.plausibility +
                0.3 * self.testability +
                0.3 * self.novelty)


@dataclass
class ExperimentProposal:
    """Proposed experiment or observation"""
    experiment_id: str
    description: str
    experiment_type: str  # 'observational', 'computational', 'theoretical'
    target_hypothesis: str

    # Feasibility
    feasibility: Optional[FeasibilityResult] = None

    # Requirements
    required_data: List[str] = field(default_factory=list)
    required_compute: Dict[str, float] = field(default_factory=dict)
    required_time_hours: float = 1.0

    # Expected outcomes
    expected_outcomes: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class LiteratureReview:
    """Results of literature review"""
    num_papers_reviewed: int
    key_findings: List[str]
    identified_gaps: List[str]
    extracted_hypotheses: List[Hypothesis]
    citation_network_stats: Dict[str, Any]
    synthesis_summary: str


@dataclass
class DiscoveryResult:
    """Complete results of discovery process"""
    task_id: str
    research_question: str
    success: bool

    # Phase results
    literature_review: Optional[LiteratureReview] = None
    data_gathered: Dict[str, Any] = field(default_factory=dict)
    hypotheses_generated: List[Hypothesis] = field(default_factory=list)
    experiments_proposed: List[ExperimentProposal] = field(default_factory=list)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    synthesized_knowledge: Dict[str, Any] = field(default_factory=dict)

    # Discoveries
    novel_insights: List[str] = field(default_factory=list)
    new_research_directions: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    # Metadata
    total_time_hours: float = 0.0
    phases_completed: List[str] = field(default_factory=list)
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)

    # Assessment
    discovery_quality: float = 0.0
    novelty_score: float = 0.0
    impact_assessment: str = ""

    def summary(self) -> str:
        """Generate summary string"""
        status = "SUCCESS" if self.success else "INCOMPLETE"
        return f"""
{'='*60}
DISCOVERY RESULT: {status}
{'='*60}
Research Question: {self.research_question}
Total Time: {self.total_time_hours:.2f} hours
Phases Completed: {', '.join(self.phases_completed)}

Literature Review:
  - Papers Reviewed: {self.literature_review.num_papers_reviewed if self.literature_review else 0}
  - Key Findings: {len(self.literature_review.key_findings) if self.literature_review else 0}

Hypotheses Generated: {len(self.hypotheses_generated)}
Experiments Proposed: {len(self.experiments_proposed)}
Novel Insights: {len(self.novel_insights)}

Discovery Quality: {self.discovery_quality:.2f}
Novelty Score: {self.novelty_score:.2f}

Top Hypotheses:
{self._format_top_hypotheses()}

New Research Directions:
{self._format_research_directions()}
{'='*60}
"""

    def _format_top_hypotheses(self) -> str:
        """Format top 3 hypotheses"""
        if not self.hypotheses_generated:
            return "  (none)"

        sorted_hyp = sorted(self.hypotheses_generated,
                           key=lambda h: h.overall_score(),
                           reverse=True)
        lines = []
        for i, hyp in enumerate(sorted_hyp[:3], 1):
            lines.append(f"  {i}. {hyp.statement}")
            lines.append(f"     Score: {hyp.overall_score():.2f} "
                        f"(P={hyp.plausibility:.2f}, "
                        f"T={hyp.testability:.2f}, "
                        f"N={hyp.novelty:.2f})")
        return "\n".join(lines)

    def _format_research_directions(self) -> str:
        """Format research directions"""
        if not self.new_research_directions:
            return "  (none)"
        return "\n".join(f"  - {d}" for d in self.new_research_directions[:5])


# =============================================================================
# Scientific Discovery Orchestrator
# =============================================================================

class ScientificDiscoveryOrchestrator:
    """
    Main orchestrator for autonomous scientific discovery.

    Coordinates the complete 6-phase discovery cycle, integrating
    V41/V50/V92 reasoning systems with AstroSwarm inference and
    domain-specific analysis capabilities.
    """

    def __init__(self,
                 safety_limits: Optional[SafetyLimits] = None,
                 storage_path: Optional[Path] = None,
                 enable_mork: bool = True):
        """
        Initialize discovery orchestrator.

        Args:
            safety_limits: Resource and safety constraints
            storage_path: Path for storing discovery results
            enable_mork: Whether to use MORK persistence
        """
        # Core controllers
        self.reasoning_controller = get_adaptive_reasoning_controller()
        self.feasibility_assessor = create_feasibility_assessor(
            custom_limits=safety_limits
        )

        # Initialize subsystems
        self._init_v41_v50_v92()
        self._init_astroswarm()
        self._init_mork(enable_mork)
        self._init_integration_bus()

        # Storage
        self.storage_path = storage_path or Path.home() / ".stan_discovery"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.current_task: Optional[DiscoveryTask] = None
        self.discovery_history: List[DiscoveryResult] = []
