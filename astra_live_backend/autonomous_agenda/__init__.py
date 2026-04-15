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
ASTRA V9.0 — Autonomous Scientific Agenda
Enables ASTRA to set its own research goals through curiosity metrics.

Components:
- CuriosityEngine: Computes information-theoretic curiosity metrics
- GoalGenerator: Generates research goals from knowledge gaps
- ApprovalWorkflow: Manages human approval for semi-autonomous mode
- AutonomousAgenda: Main system integrating all components

Example usage:
    from astra_live_backend.autonomous_agenda import create_autonomous_agenda

    agenda = create_autonomous_agenda(
        knowledge_graph=kg,
        discovery_memory=dm,
        mode="semi_autonomous"
    )

    goals = agenda.generate_research_agenda(num_goals=5)
    for goal in goals:
        print(f"{goal.title}: {goal.curiosity_score:.2f}")
"""

from .curiosity_engine import (
    CuriosityMetric,
    GoalStatus,
    GoalPriority,
    ResearchGoal,
    CuriosityAssessment,
    CuriosityEngine,
    GoalGenerator,
    ApprovalWorkflow,
    AutonomousAgenda,
    create_autonomous_agenda,
    create_curiosity_engine
)

__all__ = [
    "CuriosityMetric",
    "GoalStatus",
    "GoalPriority",
    "ResearchGoal",
    "CuriosityEngine",
    "GoalGenerator",
    "ApprovalWorkflow",
    "AutonomousAgenda",
    "create_autonomous_agenda"
]
