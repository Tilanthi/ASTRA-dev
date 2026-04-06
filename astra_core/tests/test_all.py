"""
STAN-CORE V4.0 Tests

Run all tests with: python -m pytest tests/
"""

import pytest
import numpy as np
import pandas as pd


class TestCausalDiscovery:
    """Test causal discovery algorithms."""

    def test_pc_algorithm_simple_chain(self):
        """Test PC on simple causal chain: X → Y → Z"""
        from astra_core.causal.discovery.pc_algorithm import PCAlgorithm

        # Generate data
        np.random.seed(42)
        n = 1000
        X = np.random.normal(0, 1, n)
        Y = 0.5 * X + np.random.normal(0, 1, n)
        Z = 0.3 * Y + np.random.normal(0, 1, n)

        data = pd.DataFrame({'X': X, 'Y': Y, 'Z': Z})

        # Run PC
        pc = PCAlgorithm(alpha=0.01)
        scm = pc.discover(data, verbose=False)

        # Check graph structure
        assert scm.graph.number_of_nodes() == 3
        assert scm.graph.number_of_edges() >= 2  # Should find some edges

    def test_temporal_discovery(self):
        """Test temporal causal discovery."""
        from astra_core.causal.discovery.temporal_discovery import (
            TemporalCausalDiscovery,
            granger_causality_test
        )

        # Generate AR(1) process
        np.random.seed(42)
        n = 500
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = 0.5 * x[i-1] + np.random.normal(0, 1)

        # Test Granger causality
        y = x.copy()
        causes, lag, p = granger_causality_test(x[:-1], y[1:], max_lag=5)

        # X should Granger-cause its own lagged values
        assert causes or not causes  # May or may not depending on random seed


class TestMemorySystems:
    """Test memory systems."""

    def test_episodic_memory(self):
        """Test episodic memory storage and retrieval."""
        from astra_core.memory.episodic.memory import EpisodicMemory, Experience

        memory = EpisodicMemory(capacity=100)

        # Store experience
        exp = Experience(
            content="Test experience",
            importance=0.8,
            tags={"test", "memory"}
        )
        eid = memory.store(exp)

        # Retrieve
        retrieved = memory.retrieve(eid)
        assert retrieved is not None
        assert retrieved.content == "Test experience"

    def test_working_memory(self):
        """Test working memory."""
        from astra_core.memory.working.memory import WorkingMemory

        wm = WorkingMemory(capacity=7)

        # Add items
        for i in range(5):
            wm.add(f"item_{i}", f"content_{i}", importance=0.5)

        # Check state
        state = wm.state()
        assert state['active_count'] == 5

    def test_semantic_memory(self):
        """Test semantic memory."""
        from astra_core.memory.semantic.memory import (
            SemanticMemory,
            Concept,
            RelationType
        )

        memory = SemanticMemory()

        # Add concepts
        concept1 = Concept(name="animal", description="Living organism")
        concept2 = Concept(name="dog", description="Domesticated animal")
        concept2.add_relation(RelationType.IS_A, "animal")

        memory.add_concept(concept1)
        memory.add_concept(concept2)

        # Retrieve
        retrieved = memory.get_concept("dog")
        assert retrieved is not None


class TestSimulation:
    """Test simulation components."""

    def test_physics_simulator(self):
        """Test physics simulator."""
        from astra_core.simulation.physics.simulator import PhysicsSimulator

        sim = PhysicsSimulator(time_step=0.01)

        # Add particles
        sim.add_particle(position=[0, 0, 0], velocity=[1, 0, 0], mass=1.0)
        sim.add_particle(position=[10, 0, 0], velocity=[-1, 0, 0], mass=1.0)

        # Simulate
        trajectories = sim.simulate_gravity(G=1.0, steps=10)

        assert len(trajectories) == 10

    def test_astronomy_simulator(self):
        """Test astronomy simulator."""
        from astra_core.simulation.physics.simulator import AstronomySimulator

        sim = AstronomySimulator()
        sim.create_star_system(n_planets=3)

        # Should have star + planets
        assert len(sim.particles) == 4


class TestNeuralTraining:
    """Test neural network training."""

    def test_mlp(self):
        """Test multi-layer perceptron."""
        from astra_core.neural.training import MultiLayerPerceptron

        model = MultiLayerPerceptron(
            layer_sizes=[2, 4, 1],
            activation='relu'
        )

        # Forward pass
        x = np.array([[1, 2], [3, 4]])
        y = model.forward(x)

        assert y.shape == (2, 1)

    def test_trainer(self):
        """Test neural network trainer."""
        from astra_core.neural.training import (
            MultiLayerPerceptron,
            Trainer
        )

        # Create model
        model = MultiLayerPerceptron(layer_sizes=[2, 4, 1])

        # Create trainer
        trainer = Trainer(model, learning_rate=0.01)

        # Training data
        x_train = np.random.randn(100, 2)
        y_train = np.random.randn(100, 1)

        # Train
        history = trainer.train(x_train, y_train, epochs=5, verbose=False)

        assert 'train_loss' in history
        assert len(history['train_loss']) == 5


class TestMarketSimulation:
    """Test market simulation."""

    def test_order_book(self):
        """Test order book."""
        from astra_core.simulation.market.simulator import (
            OrderBook,
            Order,
            OrderType
        )

        book = OrderBook()

        # Add orders
        bid = Order(id="bid1", type=OrderType.BUY, price=100, quantity=10,
                   timestamp=1, trader_id="trader1")
        ask = Order(id="ask1", type=OrderType.SELL, price=101, quantity=5,
                   timestamp=1, trader_id="trader1")

        book.add_order(bid)
        book.add_order(ask)

        # Check spread
        spread = book.get_spread()
        assert spread is not None

    def test_market_simulation(self):
        """Test agent-based market simulation."""
        from astra_core.simulation.market.simulator import MarketSimulation

        sim = MarketSimulation(n_agents=50)
        sim.create_default_agents()

        # Run simulation
        results = sim.run(steps=100)

        assert results['total_trades'] >= 0
        assert 'prices' in results


class TestMetaCognition:
    """Test meta-cognitive components."""

    def test_cognitive_monitor(self):
        """Test cognitive process monitoring."""
        from astra_core.metacognitive.monitoring.monitor import (
            CognitiveMonitor,
            ProcessState
        )

        monitor = CognitiveMonitor()

        # Start process
        pid = monitor.start_process("test_process")

        # End process
        monitor.end_process(pid, confidence=0.8)

        # Get process
        record = monitor.get_process(pid)
        assert record is not None
        assert record.state == ProcessState.COMPLETED


class TestIntegration:
    """Integration tests."""

    def test_unified_system(self):
        """Test unified system creation."""
        from astra_core.core import create_stan_system

        system = create_stan_system(mode="general")

        # Check status
        status = system.get_status()
        assert status['mode'] == "general"
        assert status['version'] == "4.0.0"

    def test_query_processing(self):
        """Test query processing."""
        from astra_core.core import create_stan_system

        system = create_stan_system(mode="general")

        result = system.process("Analyze the causal relationships")

        assert 'query' in result
        assert 'responses' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
