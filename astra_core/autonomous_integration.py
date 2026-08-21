"""
ASTRA Autonomous Integration - Main System Integration

This module integrates all autonomous capabilities into the main ASTRA system,
enabling automatic activation at system initialization with proper safety
constraints and domain boundaries.

Key Features:
- Automatic autonomous capability initialization
- Integration with main ASTRA entry points
- Safety constraint enforcement
- Domain boundary enforcement
- Autonomous discovery activation

Version: 1.0.0
Date: 2026-06-27
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Import autonomous components at module level
try:
    from .autonomy import (
        create_autonomy_orchestrator,
        create_genuine_discovery_generator,
        create_adaptive_decision_engine,
        start_continuous_autonomous_mode
    )
    AUTONOMY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"[AutonomousASTRA] Autonomy components not available: {e}")
    AUTONOMY_AVAILABLE = False
    # Create stub functions for graceful fallback
    def create_autonomy_orchestrator(*args, **kwargs):
        raise ImportError("Autonomy components not available")
    def create_genuine_discovery_generator(*args, **kwargs):
        raise ImportError("Autonomy components not available")
    def create_adaptive_decision_engine(*args, **kwargs):
        raise ImportError("Autonomy components not available")
    def start_continuous_autonomous_mode(*args, **kwargs):
        raise ImportError("Autonomy components not available")


class AutonomousMode(Enum):
    """Modes of autonomous operation"""
    OFF = "off"                           # No autonomous operation
    REACTIVE_ONLY = "reactive_only"       # Only reactive to user prompts
    IDLE_EXPLORATION = "idle_exploration"  # Exploration during idle time
    CONTINUOUS = "continuous"              # Continuous autonomous operation
    FULL_AUTONOMY = "full_autonomy"        # Full autonomous operation


@dataclass
class AutonomousSystemConfig:
    """Configuration for autonomous ASTRA system"""
    mode: AutonomousMode = AutonomousMode.IDLE_EXPLORATION
    autonomy_level: float = 0.7

    # Domain boundaries
    primary_domains: List[str] = field(default_factory=lambda: ["astrophysics", "astronomy"])
    related_domains: List[str] = field(default_factory=lambda: ["physics", "mathematics", "computational"])
    forbidden_domains: List[str] = field(default_factory=list)

    # Safety constraints
    require_validation_for_discoveries: bool = True
    allow_self_modification: bool = True
    modification_scope: List[str] = field(default_factory=lambda: [str(Path(__file__).resolve().parents[1]) + "/"])

    # Activity settings
    idle_threshold_seconds: int = 300  # 5 minutes
    discovery_interval: int = 1800      # 30 minutes
    literature_monitoring: bool = True

    # Reporting
    report_discoveries: bool = True
    report_significance_threshold: float = 0.7


class AutonomousASTRASystem:
    """
    Autonomous ASTRA System with integrated autonomous capabilities.

    This class provides the main entry point for autonomous ASTRA operation,
    automatically initializing and coordinating all autonomous capabilities.
    """

    def __init__(self, config: Optional[AutonomousSystemConfig] = None):
        """
        Initialize Autonomous ASTRA System

        Args:
            config: Autonomous system configuration
        """
        self.config = config or AutonomousSystemConfig()

        logger.info(f"[AutonomousASTRA] Initializing autonomous ASTRA system...")
        logger.info(f"[AutonomousASTRA] Mode: {self.config.mode.value}")
        logger.info(f"[AutonomousASTRA] Autonomy level: {self.config.autonomy_level}")

        # Check if autonomy components are available
        self.autonomy_available = AUTONOMY_AVAILABLE
        if not AUTONOMY_AVAILABLE:
            logger.warning("[AutonomousASTRA] Autonomy components not available - running in degraded mode")
            return

        # Initialize autonomous components
        self.orchestrator = None
        self.discovery_generator = None
        self.decision_engine = None
        self.continuous_process = None

        # Discovery tracking
        self.discoveries: List[Dict] = []
        self.autonomous_activities: List[Dict] = []

        # System status
        self.autonomous_initialized = False
        self.continuous_mode_active = False

        # Initialize based on mode
        self._initialize_for_mode()

        logger.info("[AutonomousASTRA] Autonomous ASTRA system initialized")

    def _initialize_for_mode(self):
        """Initialize autonomous capabilities based on mode"""
        if self.config.mode == AutonomousMode.OFF:
            logger.info("[AutonomousASTRA] Autonomous mode OFF - no initialization")
            return

        # Always initialize core autonomous components
        self._initialize_core_components()

        # Mode-specific initialization
        if self.config.mode == AutonomousMode.IDLE_EXPLORATION:
            self._initialize_idle_exploration()
        elif self.config.mode == AutonomousMode.CONTINUOUS:
            self._initialize_continuous_mode()
        elif self.config.mode == AutonomousMode.FULL_AUTONOMY:
            self._initialize_full_autonomy()

        self.autonomous_initialized = True

    def _initialize_core_components(self):
        """Initialize core autonomous components"""
        logger.info("[AutonomousASTRA] Initializing core autonomous components...")

        # Create autonomy orchestrator
        self.orchestrator = create_autonomy_orchestrator(
            autonomy_level=self.config.autonomy_level
        )

        # Create discovery generator
        self.discovery_generator = create_genuine_discovery_generator()

        # Create decision engine
        self.decision_engine = create_adaptive_decision_engine(
            autonomy_level=self.config.autonomy_level
        )

        logger.info("[AutonomousASTRA] Core components initialized")

    def _initialize_idle_exploration(self):
        """Initialize idle exploration mode"""
        logger.info("[AutonomousASTRA] Initializing idle exploration mode...")

        # Configure orchestrator for idle exploration
        self.orchestrator.config.enable_idle_exploration = True
        self.orchestrator.config.idle_threshold_seconds = self.config.idle_threshold_seconds

        # Start idle exploration
        self.orchestrator.start_continuous_mode()

        logger.info("[AutonomousASTRA] Idle exploration mode initialized")

    def _initialize_continuous_mode(self):
        """Initialize continuous autonomous mode"""
        logger.info("[AutonomousASTRA] Initializing continuous autonomous mode...")

        # Start continuous autonomous process
        self.continuous_process = start_continuous_autonomous_mode(
            idle_threshold=self.config.idle_threshold_seconds,
            discovery_interval=self.config.discovery_interval,
            literature_check=self.config.literature_monitoring
        )

        # Set active domains
        self.continuous_process.set_active_domains(self.config.primary_domains)

        self.continuous_mode_active = True

        logger.info("[AutonomousASTRA] Continuous autonomous mode initialized")

    def _initialize_full_autonomy(self):
        """Initialize full autonomous mode"""
        logger.info("[AutonomousASTRA] Initializing full autonomous mode...")

        # Initialize continuous mode
        self._initialize_continuous_mode()

        # Enable sub-agent spawning
        self.orchestrator.config.enable_sub_agent_spawning = True

        # Enable self-modification within constraints
        if self.config.allow_self_modification:
            logger.info("[AutonomousASTRA] Self-modification enabled within constraints")
            # Configure modification scope
            self.orchestrator.config.safe_file_paths = self.config.modification_scope

        logger.info("[AutonomousASTRA] Full autonomous mode initialized")

    def process_with_autonomy(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query with autonomous capabilities

        Args:
            query: User query or task
            context: Additional context

        Returns:
            Processing result with autonomous enhancements
        """
        if not self.autonomous_initialized:
            logger.warning("[AutonomousASTRA] Autonomous capabilities not initialized")
            return {
                'answer': "Autonomous capabilities not available",
                'autonomy_used': False
            }

        logger.info(f"[AutonomousASTRA] Processing with autonomy: {query[:60]}...")

        # Update activity time (used for idle detection)
        if self.orchestrator:
            self.orchestrator.update_activity()
        if self.continuous_process:
            self.continuous_process.update_user_activity()

        # Process with autonomous decision making
        result = {
            'query': query,
            'autonomy_used': True,
            'autonomy_level': self.config.autonomy_level,
            'mode': self.config.mode.value
        }

        # Use autonomous decision engine for complex tasks
        if self.decision_engine and len(query) > 50:  # Complex query
            # Generate decision options
            options = self._generate_processing_options(query)
            decision = self.decision_engine.make_adaptive_decision(
                context=context or {},
                options=options
            )
            result['autonomous_decision'] = {
                'strategy': decision.strategy_used.value,
                'confidence': decision.confidence,
                'rationale': decision.rationale
            }

        # Check if autonomous exploration should be spawned
        if self.config.mode in [AutonomousMode.IDLE_EXPLORATION, AutonomousMode.CONTINUOUS, AutonomousMode.FULL_AUTONOMY]:
            sub_agent = self._spawn_exploration_subagent(query)
            if sub_agent:
                result['exploration_spawned'] = sub_agent

        return result

    def _generate_processing_options(self, query: str) -> List:
        """Generate processing options for autonomous decision"""
        from .autonomy import DecisionOption, RiskLevel

        options = []

        # Option 1: Standard processing
        options.append(DecisionOption(
            option_id="standard",
            description="Process using standard ASTRA capabilities",
            expected_value=0.7,
            novelty_score=0.3,
            risk_level=RiskLevel.MINIMAL,
            feasibility=0.9,
            confidence=0.8
        ))

        # Option 2: Deep analysis
        options.append(DecisionOption(
            option_id="deep",
            description="Perform deep analysis with multiple reasoning approaches",
            expected_value=0.8,
            novelty_score=0.5,
            risk_level=RiskLevel.LOW,
            feasibility=0.7,
            confidence=0.7
        ))

        # Option 3: Novel approach
        options.append(DecisionOption(
            option_id="novel",
            description="Apply novel reasoning approach",
            expected_value=0.6,
            novelty_score=0.8,
            risk_level=RiskLevel.MODERATE,
            feasibility=0.5,
            confidence=0.5
        ))

        return options

    def _spawn_exploration_subagent(self, query: str) -> Optional[Dict]:
        """Spawn exploration sub-agent if relevant"""
        if not self.orchestrator or not self.config.autonomy_level > 0.5:
            return None

        # Check if query relates to primary domains
        domain_relevant = any(
            domain.lower() in query.lower()
            for domain in self.config.primary_domains
        )

        if domain_relevant and self.orchestrator.config.enable_sub_agent_spawning:
            # Extract potential exploration topic
            topic = self._extract_exploration_topic(query)

            sub_agent_id = self.orchestrator.spawn_discovery_subagent(
                domain=self.config.primary_domains[0],
                objective=f"Explore: {topic}",
                capabilities=["discovery", "analysis"]
            )

            return {
                'sub_agent_id': sub_agent_id,
                'domain': self.config.primary_domains[0],
                'objective': f"Explore: {topic}"
            }

        return None

    def _extract_exploration_topic(self, query: str) -> str:
        """Extract exploration topic from query"""
        # Simple extraction - in production would use NLP
        words = query.split()
        # Take first few meaningful words
        meaningful_words = [w for w in words if len(w) > 3][:5]
        return " ".join(meaningful_words)

    def generate_autonomous_discovery(
        self,
        domain: str,
        topic: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Generate autonomous discovery

        Args:
            domain: Scientific domain
            topic: Specific topic

        Returns:
            Discovery result
        """
        if not self.discovery_generator:
            logger.warning("[AutonomousASTRA] Discovery generator not available")
            return None

        logger.info(f"[AutonomousASTRA] Generating autonomous discovery: {domain}/{topic}")

        # Generate genuine discovery
        hypothesis = self.discovery_generator.generate_genuine_hypothesis(
            domain=domain,
            topic=topic
        )

        # Validate discovery
        validation = self.discovery_generator.validate_discovery(hypothesis)

        # Check if should report
        should_report = (
            self.config.report_discoveries and
            validation.confidence_score > self.config.report_significance_threshold
        )

        discovery = {
            'hypothesis': hypothesis.statement,
            'domain': domain,
            'discovery_type': hypothesis.discovery_type.value,
            'novelty_score': hypothesis.novelty_score,
            'confidence': hypothesis.confidence,
            'validation_status': validation.validation_status.value,
            'validation_confidence': validation.confidence_score,
            'should_report': should_report,
            'contemporary_context': {
                'trend': hypothesis.contemporary_context.trend.value,
                'research_gap': hypothesis.contemporary_context.research_gap
            }
        }

        self.discoveries.append(discovery)

        logger.info(f"[AutonomousASTRA] Discovery generated: {hypothesis.statement[:60]}...")

        return discovery

    def report_significant_discoveries(self) -> List[Dict]:
        """Get discoveries that meet significance threshold"""
        return [
            discovery for discovery in self.discoveries
            if discovery.get('should_report', False)
        ]

    def get_autonomous_status(self) -> Dict:
        """Get comprehensive autonomous system status"""
        status = {
            'mode': self.config.mode.value,
            'autonomy_level': self.config.autonomy_level,
            'initialized': self.autonomous_initialized,
            'continuous_active': self.continuous_mode_active,
            'autonomy_available': self.autonomy_available,
            'discoveries_made': len(self.discoveries),
            'significant_discoveries': len(self.report_significant_discoveries()),
            'active_domains': self.config.primary_domains
        }

        # Add component statuses
        if self.orchestrator:
            status['orchestrator'] = self.orchestrator.get_status()

        if self.discovery_generator:
            status['discovery_generator'] = self.discovery_generator.get_status()

        if self.decision_engine:
            status['decision_engine'] = self.decision_engine.get_status()

        if self.continuous_process:
            status['continuous_process'] = self.continuous_process.get_status()

        return status

    def shutdown(self):
        """Shutdown autonomous system gracefully"""
        logger.info("[AutonomousASTRA] Shutting down autonomous system...")

        # Stop continuous process
        if self.continuous_process:
            self.continuous_process.stop()

        # Stop orchestrator continuous mode
        if self.orchestrator:
            self.orchestrator.stop_continuous_mode()

        logger.info("[AutonomousASTRA] Autonomous system shutdown complete")


# Convenience functions

def create_autonomous_astra(
    mode: AutonomousMode = AutonomousMode.IDLE_EXPLORATION,
    autonomy_level: float = 0.7,
    domains: Optional[List[str]] = None
) -> AutonomousASTRASystem:
    """
    Convenience function to create autonomous ASTRA system

    Args:
        mode: Autonomous operation mode
        autonomy_level: Level of autonomy (0.0-1.0)
        domains: Primary domains for autonomous operation

    Returns:
        Initialized autonomous ASTRA system
    """
    config = AutonomousSystemConfig(
        mode=mode,
        autonomy_level=autonomy_level,
        primary_domains=domains or ["astrophysics", "astronomy"]
    )

    return AutonomousASTRASystem(config)


def initialize_astra_with_autonomy(
    autonomy_level: float = 0.7,
    enable_idle_exploration: bool = True,
    enable_continuous: bool = False
) -> AutonomousASTRASystem:
    """
    Initialize ASTRA with autonomous capabilities

    Args:
        autonomy_level: Level of autonomy (0.0-1.0)
        enable_idle_exploration: Enable idle-time exploration
        enable_continuous: Enable continuous autonomous operation

    Returns:
        Autonomous ASTRA system
    """
    mode = AutonomousMode.OFF

    if enable_continuous:
        mode = AutonomousMode.CONTINUOUS
    elif enable_idle_exploration:
        mode = AutonomousMode.IDLE_EXPLORATION
    elif autonomy_level > 0.5:
        mode = AutonomousMode.REACTIVE_ONLY

    return create_autonomous_astra(
        mode=mode,
        autonomy_level=autonomy_level
    )


# Export for __init__.py

__all__ = [
    'AutonomousASTRASystem',
    'AutonomousMode',
    'AutonomousSystemConfig',
    'create_autonomous_astra',
    'initialize_astra_with_autonomy'
]