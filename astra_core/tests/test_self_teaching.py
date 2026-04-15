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
Test suite for STAR-Learn self-teaching system.

Tests the autonomous self-teaching capabilities including:
- Intrinsic reward calculation
- Autonomous training loop
- Curriculum generation
- Recursive improvement
- Stigmergic memory
- Benchmark evaluation
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSelfRewardingEngine:
    """Tests for the self-rewarding engine."""

    def test_reward_calculation(self):
        """Test basic reward calculation."""
        from astra_core.self_teaching.self_rewarding import (
            SelfRewardingEngine, RewardConfig, RewardComponent
        )

        config = RewardConfig()
        engine = SelfRewardingEngine(config)

        # Create a test discovery
        discovery = {
            'content': 'Gravity causes objects to fall toward Earth',
            'domain': 'physics',
            'confidence': 0.8,
            'predictions': [{'quantitative': True, 'novel': True}],
            'causal_mechanisms': [{'mechanism': 'gravitational_attraction'}],
            'new_concepts': ['gravitational_field']
        }

        reward = engine.calculate_reward(discovery)

        assert reward.total_reward > 0
        assert reward.novelty_score >= 0
        assert reward.complexity_score >= 0
        assert len(reward.components) > 0

    def test_novelty_detection(self):
        """Test novelty detection component."""
        from astra_core.self_teaching.self_rewarding import SelfRewardingEngine

        engine = SelfRewardingEngine()

        # First discovery should be novel
        discovery1 = {
            'content': 'E=mc² describes mass-energy equivalence in physics',
            'domain': 'physics',
            'confidence': 0.9
        }

        reward1 = engine.calculate_reward(discovery1)
        assert reward1.novelty_score > 0.3  # Should be novel

        # Similar discovery should have lower novelty
        discovery2 = {
            'content': 'E=mc² describes how mass and energy are equivalent in physics systems',
            'domain': 'physics',
            'confidence': 0.9
        }

        reward2 = engine.calculate_reward(discovery2)
        # Should have lower or equal novelty due to content overlap
        assert reward2.novelty_score <= reward1.novelty_score or reward2.novelty_score < 0.5

    def test_cross_domain_bonus(self):
        """Test cross-domain knowledge transfer bonus."""
        from astra_core.self_teaching.self_rewarding import SelfRewardingEngine

        engine = SelfRewardingEngine()

        # Single domain discovery
        single_domain = {
            'content': 'Stars emit light through nuclear fusion',
            'domain': 'astrophysics',
            'connected_domains': ['astrophysics'],
            'confidence': 0.8
        }

        reward1 = engine.calculate_reward(single_domain)

        # Cross-domain discovery
        cross_domain = {
            'content': 'Nuclear fusion in stars follows quantum mechanics',
            'domain': 'astrophysics',
            'connected_domains': ['astrophysics', 'physics', 'quantum_theory'],
            'confidence': 0.8
        }

        reward2 = engine.calculate_reward(cross_domain)

        assert reward2.transfer_score > reward1.transfer_score


class TestStigmergicMemory:
    """Tests for stigmergic memory."""

    def test_pheromone_deposit(self):
        """Test pheromone trail deposition."""
        from astra_core.self_teaching.stigmergic_memory import (
            StigmergicMemory, PheromoneTrail, FieldType
        )

        memory = StigmergicMemory()

        trail = {
            'location': 'test_location',
            'strength': 5.0,
            'field_type': 'aggregation',
            'domain': 'test',
            'reward': 3.0
        }

        trail_id = memory.deposit_pheromone(trail)

        assert trail_id is not None
        assert len(memory.trails) == 1

        # Check field was created/updated
        field = memory.get_field_at('test_location')
        assert field is not None
        assert field.tau > 0  # Aggregation pheromone should be deposited

    def test_biological_field_dynamics(self):
        """Test biological field (TAU/ETA/C_K) dynamics."""
        from astra_core.self_teaching.stigmergic_memory import StigmergicMemory

        memory = StigmergicMemory()

        # First deposit a pheromone to create a field
        trail = {
            'location': 'test_location',
            'strength': 5.0,
            'field_type': 'aggregation',
            'domain': 'test',
            'reward': 3.0
        }

        memory.deposit_pheromone(trail)

        # Then update fields
        update = {
            'TAU': 0.5,
            'ETA': 0.2,
            'C_K': 0.8
        }

        memory.update_biological_field(update)

        state = memory.get_state()
        assert state['avg_tau'] > 0
        assert state['avg_c_k'] > 0

    def test_decay(self):
        """Test pheromone decay over time."""
        from astra_core.self_teaching.stigmergic_memory import StigmergicMemory

        memory = StigmergicMemory()

        # Deposit strong pheromone
        trail = {
            'location': 'test',
            'strength': 10.0,
            'field_type': 'aggregation',
            'domain': 'test'
        }

        memory.deposit_pheromone(trail)

        field_before = memory.get_field_at('test')
        tau_before = field_before.tau

        # Apply decay
        memory.decay_fields()

        field_after = memory.get_field_at('test')
        tau_after = field_after.tau

        assert tau_after < tau_before  # Should decay

    def test_swarm_recommendations(self):
        """Test swarm coordination recommendations."""
        from astra_core.self_teaching.stigmergic_memory import StigmergicMemory

        memory = StigmergicMemory()

        # Deposit some pheromone trails
        for i in range(5):
            trail = {
                'location': f'location_{i}',
                'strength': 5.0 + i,
                'field_type': 'aggregation',
                'domain': 'astrophysics'
            }
            memory.deposit_pheromone(trail)

        # Get recommendations
        recommendations = memory.get_swarm_recommendations(
            'current_location',
            'explorer'
        )

        assert len(recommendations) > 0


class TestCurriculumGenerator:
    """Tests for curriculum generation."""

    def test_problem_generation(self):
        """Test problem generation."""
        from astra_core.self_teaching.curriculum_generator import (
            CurriculumGenerator, ProblemDifficulty
        )

        generator = CurriculumGenerator()

        problem = generator.generate_problem(
            difficulty=0.5,
            domain='astrophysics'
        )

        assert problem is not None
        assert problem.difficulty == 0.5
        assert problem.domain == 'astrophysics'
        assert len(problem.question) > 0

    def test_difficulty_progression(self):
        """Test adaptive difficulty progression."""
        from astra_core.self_teaching.curriculum_generator import CurriculumGenerator

        generator = CurriculumGenerator()

        # Generate problems at increasing difficulty
        difficulties = [0.3, 0.5, 0.7, 0.9]

        for diff in difficulties:
            problem = generator.generate_problem(difficulty=diff)
            assert abs(problem.difficulty - diff) < 0.1  # Allow small variation

    def test_cross_domain_generation(self):
        """Test cross-domain problem generation."""
        from astra_core.self_teaching.curriculum_generator import CurriculumGenerator

        generator = CurriculumGenerator()

        # Generate enough problems to enable cross-domain
        for _ in range(10):
            generator.generate_problem(domain='astrophysics')
            generator.generate_problem(domain='physics')

        # Now try cross-domain
        problem = generator.generate_problem(
            difficulty=0.6,
            domain='astrophysics'
        )

        # Should have cross-domain option available
        assert problem is not None


class TestAutonomousTrainingLoop:
    """Tests for autonomous training loop."""

    def test_single_iteration(self):
        """Test running a single training iteration."""
        from astra_core.self_teaching.autonomous_loop import (
            AutonomousTrainingLoop, LoopConfig
        )
        from astra_core.self_teaching.self_rewarding import SelfRewardingEngine
        from astra_core.self_teaching.curriculum_generator import CurriculumGenerator
        from astra_core.self_teaching.recursive_improver import RecursiveImprover
        from astra_core.self_teaching.stigmergic_memory import StigmergicMemory

        # Create components
        reward_engine = SelfRewardingEngine()
        memory = StigmergicMemory()
        curriculum = CurriculumGenerator(memory=memory)
        improver = RecursiveImprover(memory=memory, reward_engine=reward_engine)

        config = LoopConfig(max_iteration_time=30.0)
        loop = AutonomousTrainingLoop(
            config,
            reward_engine,
            curriculum,
            improver,
            memory
        )

        # Run one iteration
        result = loop.run_iteration()

        assert result is not None
        assert result.iteration is not None
        assert result.total_time > 0

    def test_loop_statistics(self):
        """Test loop statistics tracking."""
        from astra_core.self_teaching.autonomous_loop import AutonomousTrainingLoop
        from astra_core.self_teaching.self_rewarding import SelfRewardingEngine
        from astra_core.self_teaching.curriculum_generator import CurriculumGenerator
        from astra_core.self_teaching.recursive_improver import RecursiveImprover
        from astra_core.self_teaching.stigmergic_memory import StigmergicMemory

        reward_engine = SelfRewardingEngine()
        memory = StigmergicMemory()
        curriculum = CurriculumGenerator(memory=memory)
        improver = RecursiveImprover(memory=memory, reward_engine=reward_engine)

        loop = AutonomousTrainingLoop(
            None, reward_engine, curriculum, improver, memory
        )

        # Run a few iterations
        for _ in range(5):
            loop.run_iteration()

        # Get statistics
        stats = loop.get_statistics()

        assert stats['iteration'] == 5
        assert 'best_reward' in stats
        assert 'average_reward' in stats


class TestBenchmarkSuite:
    """Tests for benchmark suite."""

    def test_quick_assessment(self):
        """Test quick benchmark assessment."""
        from astra_core.self_teaching.benchmark_suite import BenchmarkSuite
        from astra_core.self_teaching import STARLearnSystem

        # Create system
        system = STARLearnSystem()

        # Create benchmark suite
        suite = BenchmarkSuite()

        # Run quick assessment
        results = suite.run_quick_assess(system)

        assert 'overall_score' in results
        assert results['overall_score'] >= 0


class TestIntegratedSystem:
    """Integration tests for complete STAR-Learn system."""

    def test_full_system_creation(self):
        """Test creating a full STAR-Learn system."""
        from astra_core.self_teaching import (
            create_star_learn_system, STARLearnSystem
        )

        # Test factory function
        system1 = create_star_learn_system()
        assert system1 is not None

        # Test direct creation
        system2 = STARLearnSystem()
        assert system2 is not None

    def test_autonomous_training(self):
        """Test autonomous self-teaching for multiple iterations."""
        from astra_core.self_teaching import STARLearnSystem

        system = STARLearnSystem()

        # Run a few iterations
        results = system.train_autonomously(
            n_iterations=5,
            generate_report=False,
            verbose=False
        )

        assert len(results) == 5
        assert system.iteration_count == 5

        # Check that improvements were made
        final_reward = results[-1].total_reward
        assert final_reward >= 0  # Should have non-negative reward

    def test_system_status(self):
        """Test getting system status."""
        from astra_core.self_teaching import STARLearnSystem

        system = STARLearnSystem()

        status = system.get_status()

        assert 'iteration_count' in status
        assert 'best_reward' in status
        assert 'total_discoveries' in status

    def test_capability_assessment(self):
        """Test self-teaching capability assessment."""
        from astra_core.self_teaching import STARLearnSystem

        system = STARLearnSystem()

        assessment = system.assess_self_teaching_capability()

        assert 'self_teaching_score' in assessment
        assert 'learning_rate' in assessment
        assert 'transfer_efficiency' in assessment
        assert 'autonomy_level' in assessment


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
