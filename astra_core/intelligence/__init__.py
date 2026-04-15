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
