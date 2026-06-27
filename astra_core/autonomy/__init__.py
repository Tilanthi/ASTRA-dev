"""
Autonomy Package - Autonomous Capabilities Integration

This package provides autonomous capabilities for ASTRA:
- AutonomyOrchestrator: Central integration layer
- GenuineDiscoveryGenerator: Contemporary research integration
- AdaptiveDecisionEngine: Adaptive decision-making
- ContinuousAutonomousProcess: Background autonomous operation

Version: 1.0.0
Date: 2026-06-27
"""

from .AutonomyOrchestrator import (
    AutonomyOrchestrator,
    AutonomyLevel,
    AutonomyConfig,
    SubAgentTask,
    DiscoveryReport,
    SafetyConstraint,
    create_autonomy_orchestrator,
    create_autonomy_config
)

from .GenuineDiscoveryGenerator import (
    GenuineDiscoveryGenerator,
    GenuineHypothesis,
    DiscoveryType,
    ValidationStatus,
    ContemporaryResearch,
    DiscoveryValidation,
    create_genuine_discovery_generator,
    generate_contemporary_discovery
)

from .AdaptiveDecisionEngine import (
    AdaptiveDecisionEngine,
    DecisionStrategy,
    DecisionOption,
    AdaptiveDecision,
    CuriositySignal,
    NoveltyType,
    RiskLevel,
    create_adaptive_decision_engine,
    make_autonomous_decision
)

from .ContinuousAutonomousProcess import (
    ContinuousAutonomousProcess,
    ProcessState,
    ActivityType,
    AutonomousActivity,
    ActivityResult,
    ContinuousProcessConfig,
    Priority,
    create_continuous_autonomous_process,
    start_continuous_autonomous_mode
)

__all__ = [
    # AutonomyOrchestrator
    'AutonomyOrchestrator',
    'AutonomyLevel',
    'AutonomyConfig',
    'SubAgentTask',
    'DiscoveryReport',
    'SafetyConstraint',
    'create_autonomy_orchestrator',
    'create_autonomy_config',

    # GenuineDiscoveryGenerator
    'GenuineDiscoveryGenerator',
    'GenuineHypothesis',
    'DiscoveryType',
    'ValidationStatus',
    'ContemporaryResearch',
    'DiscoveryValidation',
    'create_genuine_discovery_generator',
    'generate_contemporary_discovery',

    # AdaptiveDecisionEngine
    'AdaptiveDecisionEngine',
    'DecisionStrategy',
    'DecisionOption',
    'AdaptiveDecision',
    'CuriositySignal',
    'NoveltyType',
    'RiskLevel',
    'create_adaptive_decision_engine',
    'make_autonomous_decision',

    # ContinuousAutonomousProcess
    'ContinuousAutonomousProcess',
    'ProcessState',
    'ActivityType',
    'AutonomousActivity',
    'ActivityResult',
    'ContinuousProcessConfig',
    'Priority',
    'create_continuous_autonomous_process',
    'start_continuous_autonomous_mode',
]


# Convenience function for full autonomous initialization

def create_full_autonomous_system(
    autonomy_level: float = 0.7,
    domains: Optional[List[str]] = None,
    enable_continuous: bool = True
) -> Dict:
    """
    Create fully initialized autonomous system

    Args:
        autonomy_level: Level of autonomous operation (0.0-1.0)
        domains: Primary domains for autonomous operation
        enable_continuous: Enable continuous autonomous processes

    Returns:
        Dictionary containing all autonomous components
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[Autonomy] Creating full autonomous system...")

    # Create autonomy configuration
    config = create_autonomy_config(
        autonomy_level=autonomy_level,
        primary_domains=domains or ["astrophysics", "astronomy"]
    )

    # Initialize orchestrator
    orchestrator = create_autonomy_orchestrator(
        autonomy_level=autonomy_level,
        config=config
    )

    # Initialize discovery generator
    discovery_generator = create_genuine_discovery_generator()

    # Initialize decision engine
    decision_engine = create_adaptive_decision_engine(autonomy_level)

    # Initialize continuous process
    continuous_process = None
    if enable_continuous:
        continuous_process = start_continuous_autonomous_mode()

    system = {
        'orchestrator': orchestrator,
        'discovery_generator': discovery_generator,
        'decision_engine': decision_engine,
        'continuous_process': continuous_process,
        'config': config,
        'autonomy_level': autonomy_level
    }

    logger.info("[Autonomy] Full autonomous system created")

    return system