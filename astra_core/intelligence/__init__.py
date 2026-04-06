"""
Swarm Intelligence: Swarm Systems for V37 Enhanced System

This package provides:
- Digital Pheromone Dynamics: Stigmergic coordination
- LEAPCore Evolution: Evolutionary meta-theory refinement
- Swarm Orchestrator: Agent coordination

Version: 37.0
"""

from .pheromone_dynamics import (
    DigitalPheromoneField,
    PheromoneType,
    PheromoneDeposit,
    PheromoneFieldConfig
)

from .leapcore_evolution import (
    LEAPCoreEvolution,
    EvolutionConfig,
    Chromosome,
    Gene,
    GeneType,
    FitnessEvaluator,
    V36FitnessEvaluator
)

from .orchestrator import (
    SwarmOrchestrator,
    SwarmAgent,
    ExplorerAgent,
    FalsifierAgent,
    AnalogistAgent,
    EvolverAgent,
    AgentType,
    AgentState,
    AgentConfig,
    AgentMessage
)

__version__ = "37.0"

__all__ = [
    # Pheromone Dynamics
    'DigitalPheromoneField',
    'PheromoneType',
    'PheromoneDeposit',
    'PheromoneFieldConfig',

    # LEAPCore Evolution
    'LEAPCoreEvolution',
    'EvolutionConfig',
    'Chromosome',
    'Gene',
    'GeneType',
    'FitnessEvaluator',
    'V36FitnessEvaluator',

    # Orchestrator
    'SwarmOrchestrator',
    'SwarmAgent',
    'ExplorerAgent',
    'FalsifierAgent',
    'AnalogistAgent',
    'EvolverAgent',
    'AgentType',
    'AgentState',
    'AgentConfig',
    'AgentMessage'
]
