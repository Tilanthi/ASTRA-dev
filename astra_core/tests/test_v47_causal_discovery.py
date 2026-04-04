#!/usr/bin/env python3
"""
Test suite for V47+ Enhanced Causal Discovery modules

Tests:
1. Bayesian Structure Learning
2. Expected Information Gain Calculator
3. Online Causal Learning
4. Simulation-Based Inference
5. Module integration and interconnections
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_bayesian_structure_learning():
    """Test Bayesian structure learning module"""
    print("=" * 70)
    print("Test 1: Bayesian Structure Learning")
    print("=" * 70)

    try:
        from astra_core.causal.discovery.bayesian_structure_learning import (
            InferenceMethod,
            BayesianStructureLearner,
            create_bayesian_structure_learner,
        )
        print("✓ BayesianStructureLearner imported successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Create synthetic data
    np.random.seed(42)
    n_samples = 100
    n_nodes = 4

    # Create simple causal structure: X1 -> X2 -> X3 -> X4
    X1 = np.random.randn(n_samples)
    X2 = 0.5 * X1 + np.random.randn(n_samples) * 0.5
    X3 = 0.5 * X2 + np.random.randn(n_samples) * 0.5
    X4 = 0.5 * X3 + np.random.randn(n_samples) * 0.5

    data = pd.DataFrame({'X1': X1, 'X2': X2, 'X3': X3, 'X4': X4})

    # Test Order MCMC
    try:
        learner = create_bayesian_structure_learner(
            method=InferenceMethod.ORDER_MCMC,
            n_samples=100,
            burn_in=20,
            random_state=42
        )
        print("✓ BayesianStructureLearner created (Order MCMC)")

        result = learner.learn_structure(data, verbose=False)
        print(f"✓ Structure learning completed")
        print(f"  - Edge posterior shape: {result.edge_posterior.shape}")
        print(f"  - Number of samples: {len(result.dag_samples)}")
        print(f"  - Log evidence: {result.log_evidence:.2f}")
        print(f"  - MAP DAG edges: {np.sum(result.map_dag)}")

        # Test edge uncertainty
        uncertain_edges = learner.get_most_uncertain_edges(result, top_k=3)
        print(f"  - Most uncertain edges: {len(uncertain_edges)}")

    except Exception as e:
        print(f"✗ Structure learning failed: {e}")
        return False

    print("\n✅ Bayesian Structure Learning tests PASSED\n")
    return True


def test_eig_calculator():
    """Test Expected Information Gain calculator"""
    print("=" * 70)
    print("Test 2: Expected Information Gain Calculator")
    print("=" * 70)

    try:
        from astra_core.causal.discovery.eig_calculator import (
            NoiseModel,
            ObservationPlan,
            EIGResult,
            ExpectedInformationGainCalculator,
            create_eig_calculator,
        )
        print("✓ EIG Calculator modules imported successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Create current posterior
    n_nodes = 4
    current_posterior = np.random.uniform(0.2, 0.8, (n_nodes, n_nodes))
    np.fill_diagonal(current_posterior, 0)  # No self-loops

    # Create EIG calculator
    try:
        eig_calc = create_eig_calculator(
            current_posterior=current_posterior,
            n_monte_carlo_samples=50,
            noise_model=NoiseModel.GAUSSIAN,
            random_state=42
        )
        print("✓ ExpectedInformationGainCalculator created")

        # Create observation plan
        plan = ObservationPlan(
            target_variables=['X1', 'X2', 'X3'],
            sample_size=50,
            noise_model=NoiseModel.GAUSSIAN,
            noise_parameters={'std': 0.1},
            cost=1.0
        )
        print("✓ ObservationPlan created")

        # Compute EIG
        result = eig_calc.compute_eig(plan, verbose=False)
        print(f"✓ EIG computed: {result.eig:.4f} nats")
        print(f"  - Uncertainty reduction: {result.uncertainty_reduction:.2%}")
        print(f"  - Observation value: {result.observation_value:.4f}")
        print(f"  - Convergence probability: {result.convergence_probability:.2%}")

    except Exception as e:
        print(f"✗ EIG calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ Expected Information Gain tests PASSED\n")
    return True


def test_online_causal_learning():
    """Test Online Causal Learning module"""
    print("=" * 70)
    print("Test 3: Online Causal Learning")
    print("=" * 70)

    try:
        from astra_core.causal.discovery.online_causal_learning import (
            UpdateMethod,
            ConceptDriftDetector,
            OnlineCausalLearner,
            create_online_causal_learner,
        )
        print("✓ OnlineCausalLearner modules imported successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Create synthetic streaming data
    np.random.seed(42)
    n_nodes = 3
    initial_n = 200

    # Initial data
    X1 = np.random.randn(initial_n)
    X2 = 0.5 * X1 + np.random.randn(initial_n) * 0.5
    X3 = 0.3 * X1 + 0.3 * X2 + np.random.randn(initial_n) * 0.5
    initial_data = np.column_stack([X1, X2, X3])

    # Create online learner
    try:
        learner = create_online_causal_learner(
            update_method=UpdateMethod.INCREMENTAL_PC,
            window_size=500,
            alpha=0.05,
            detect_concept_drift=True,
            verbose=False
        )
        print("✓ OnlineCausalLearner created")

        # Initialize
        learner.initialize(initial_data, node_names=['X1', 'X2', 'X3'])
        print(f"✓ Initialized with {initial_n} samples")
        print(f"  - Initial edges: {np.sum(learner.current_adjacency)}")

        # Simulate streaming updates
        for i in range(3):
            # New data batch
            new_n = 50
            X1_new = np.random.randn(new_n)
            X2_new = 0.5 * X1_new + np.random.randn(new_n) * 0.5
            X3_new = 0.3 * X1_new + 0.3 * X2_new + np.random.randn(new_n) * 0.5
            new_data = np.column_stack([X1_new, X2_new, X3_new])

            # Update
            result = learner.update(new_data)
            print(f"✓ Update {i+1}: {result.n_new_samples} new samples")
            print(f"  - Total samples seen: {learner.n_seen}")
            print(f"  - Current edges: {np.sum(result.updated_adjacency)}")
            print(f"  - Concept drift: {result.concept_drift}")

        # Get statistics
        stats = learner.get_update_statistics()
        print(f"✓ Update statistics: {stats}")

    except Exception as e:
        print(f"✗ Online learning failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ Online Causal Learning tests PASSED\n")
    return True


def test_simulation_based_inference():
    """Test Simulation-Based Inference module"""
    print("=" * 70)
    print("Test 4: Simulation-Based Inference")
    print("=" * 70)

    try:
        from astra_core.causal.inference import (
            SBIMethod,
            SBIResult,
            SimulatorInterface,
            SimulationBasedInferenceEngine,
            create_sbi_engine,
            default_summary_statistics,
        )
        print("✓ SBI modules imported successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Create SBI engine
    try:
        sbi_engine = create_sbi_engine(
            method=SBIMethod.ABC,
            random_state=42
        )
        print("✓ SimulationBasedInferenceEngine created")

        # Get available simulators
        simulators = sbi_engine.get_available_simulators()
        print(f"✓ Available simulators: {simulators}")

        # Test star formation simulator
        if 'star_formation' in simulators:
            print("\nTesting Star Formation Simulator...")

            # Create synthetic observed data
            observed_data = np.array([
                [1e-7, 2.3, 100, 0.02],  # SFR, IMF slope, cluster mass, efficiency
                [2e-7, 2.4, 150, 0.01],
                [5e-8, 2.2, 80, 0.03],
            ])

            # Run SBI
            result = sbi_engine.infer(
                simulator_name='star_formation',
                observed_data=observed_data,
                n_simulations=100,
                verbose=False
            )

            print(f"✓ SBI inference completed")
            print(f"  - Posterior samples: {len(result.posterior_samples)}")
            print(f"  - Posterior mean: {result.posterior_mean}")
            print(f"  - Log evidence: {result.log_evidence:.2f}")
            print(f"  - Simulations run: {result.n_simulations}")

    except Exception as e:
        print(f"✗ SBI inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ Simulation-Based Inference tests PASSED\n")
    return True


def test_module_interconnections():
    """Test interconnections between modules"""
    print("=" * 70)
    print("Test 5: Module Interconnections")
    print("=" * 70)

    success_count = 0
    total_tests = 0

    # Test 1: Bayesian structure learning → EIG calculator
    total_tests += 1
    try:
        from astra_core.causal.discovery.bayesian_structure_learning import BayesianStructureLearner, InferenceMethod
        from astra_core.causal.discovery.eig_calculator import create_eig_calculator

        # Learn structure
        np.random.seed(42)
        data = pd.DataFrame(np.random.randn(100, 3), columns=['X', 'Y', 'Z'])

        learner = BayesianStructureLearner(method=InferenceMethod.ORDER_MCMC, n_samples=50, random_state=42)
        result = learner.learn_structure(data, verbose=False)

        # Use posterior for EIG calculation
        eig_calc = create_eig_calculator(result.edge_posterior, n_monte_carlo_samples=20)
        print("✓ Bayesian learning → EIG calculator connection works")
        success_count += 1
    except Exception as e:
        print(f"✗ Bayesian learning → EIG connection failed: {e}")

    # Test 2: Online learner → Concept drift detector
    total_tests += 1
    try:
        from astra_core.causal.discovery.online_causal_learning import OnlineCausalLearner

        learner = OnlineCausalLearner(detect_concept_drift=True)
        data = np.random.randn(50, 3)
        learner.initialize(data)
        result = learner.update(np.random.randn(10, 3))

        print("✓ Online learner → Concept drift detector connection works")
        success_count += 1
    except Exception as e:
        print(f"✗ Online learner → Drift detector connection failed: {e}")

    # Test 3: SBI → EIG calculator integration
    total_tests += 1
    try:
        from astra_core.causal.inference import create_sbi_engine
        from astra_core.causal.discovery.eig_calculator import ObservationPlan, NoiseModel

        sbi = create_sbi_engine()
        simulators = sbi.get_available_simulators()

        if simulators:
            # Create observation plan for SBI
            plan = ObservationPlan(
                target_variables=['test'],
                sample_size=10,
                noise_model=NoiseModel.GAUSSIAN
            )
            print("✓ SBI → Observation plan integration works")
            success_count += 1
        else:
            print("⚠ No simulators available, skipping SBI test")
            total_tests -= 1
    except Exception as e:
        print(f"✗ SBI integration failed: {e}")

    # Test 4: All modules importable from top level
    total_tests += 1
    try:
        from astra_core.causal import (
            BayesianStructureLearner,
            ExpectedInformationGainCalculator,
            OnlineCausalLearner,
            SimulationBasedInferenceEngine,
        )
        print("✓ All V47+ modules importable from astra_core.causal")
        success_count += 1
    except Exception as e:
        print(f"✗ Top-level imports failed: {e}")

    print(f"\nInterconnection tests: {success_count}/{total_tests} passed")

    if success_count == total_tests:
        print("\n✅ Module Interconnection tests PASSED\n")
        return True
    else:
        print("\n❌ Some Module Interconnection tests FAILED\n")
        return False


def run_all_tests():
    """Run all V47+ causal discovery tests"""
    print("\n" + "=" * 70)
    print("STAN-XI-ASTRO V47+ Enhanced Causal Discovery Test Suite")
    print("=" * 70)
    print()

    results = {
        "Bayesian Structure Learning": test_bayesian_structure_learning(),
        "Expected Information Gain": test_eig_calculator(),
        "Online Causal Learning": test_online_causal_learning(),
        "Simulation-Based Inference": test_simulation_based_inference(),
        "Module Interconnections": test_module_interconnections(),
    }

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:40s}: {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} test suites passed")

    if passed == total:
        print("\n🎉 All V47+ Enhanced Causal Discovery tests PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
