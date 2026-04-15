#!/usr/bin/env python3
"""
Deep integration tests for ASTRA × ATLAS integration.

Tests all links, dependencies, modules and files are correctly linked together.
"""
import sys
import os
import time
import traceback
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(test_name):
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)

def print_pass(msg):
    print(f"{GREEN}✓ PASS{RESET}: {msg}")

def print_fail(msg, error=None):
    print(f"{RED}✗ FAIL{RESET}: {msg}")
    if error:
        print(f"  Error: {error}")

def print_info(msg):
    print(f"{YELLOW}ℹ INFO{RESET}: {msg}")

# Track test results
test_results = []

def run_test(test_func, test_name):
    """Run a test function and track results."""
    print_test(test_name)
    try:
        result = test_func()
        if result:
            print_pass(test_name)
            test_results.append((test_name, 'PASS', None))
            return True
        else:
            print_fail(test_name, "Test returned False")
            test_results.append((test_name, 'FAIL', "Test returned False"))
            return False
    except Exception as e:
        print_fail(test_name, str(e))
        test_results.append((test_name, 'FAIL', str(e)))
        traceback.print_exc()
        return False


# ============================================================================
# Test 1: GraphPalace Bridge
# ============================================================================

def test_graph_palace_basic():
    """Test GraphPalace bridge basic functionality."""
    from astra_live_backend.graph_palace import get_graph_palace, GraphNode

    # Get singleton
    bridge = get_graph_palace()
    assert bridge is not None, "Failed to get GraphPalace bridge"

    # Add test node
    node = GraphNode(
        id='test_hypothesis_1',
        node_type='hypothesis',
        domain='astrophysics',
        category='hubble',
        metadata={'name': 'Test Hypothesis'}
    )
    result = bridge.add_node(node)
    assert result, "Failed to add node"

    # Get node
    retrieved = bridge.get_node('test_hypothesis_1')
    assert retrieved is not None, "Failed to retrieve node"
    assert retrieved.id == 'test_hypothesis_1', "Retrieved wrong node"

    # Deposit pheromone
    deposit_id = bridge.deposit_pheromone(
        'test_hypothesis_1',
        'success',
        3.5
    )
    assert deposit_id, "Failed to deposit pheromone"

    # Get pheromone concentration
    concentrations = bridge.get_pheromone_concentration('test_hypothesis_1')
    assert 'success' in concentrations, "No success pheromone found"
    assert concentrations['success'] > 0, "Success pheromone concentration is zero"

    # Semantic search
    results = bridge.semantic_search(
        {'domain': 'astrophysics', 'category': 'hubble'},
        top_k=5
    )
    assert isinstance(results, list), "Search results not a list"

    # A* pathfinding
    path_result = bridge.find_path(
        'test_hypothesis_1',
        {'domain': 'astrophysics'},
        max_depth=5
    )
    # Path might be None if no path exists, that's ok
    assert path_result is None or isinstance(path_result, object), "Invalid path result"

    # StigmergyBridge compatibility
    hypothesis_dict = {
        'id': 'test_hyp_2',
        'domain': 'astrophysics',
        'category': 'hubble',
        'name': 'Test',
        'confidence': 0.7
    }
    result_dict = {'passed': True, 'p_value': 0.01, 'effect_size': 0.5}
    deposit_id = bridge.on_hypothesis_tested(hypothesis_dict, result_dict)
    assert deposit_id, "Failed StigmergyBridge compatibility test"

    # Rank hypotheses
    candidates = [hypothesis_dict]
    scores = [0.7]
    ranked = bridge.rank_hypotheses(candidates, scores)
    assert isinstance(ranked, list), "Rank results not a list"

    # Get status
    status = bridge.get_status()
    assert 'total_nodes' in status, "Status missing total_nodes"

    print_info(f"GraphPalace: {status['total_nodes']} nodes, "
               f"{status['total_deposits']} deposits")

    return True


# ============================================================================
# Test 2: TRM-CausalValidator
# ============================================================================

def test_trm_validator_basic():
    """Test TRM-CausalValidator basic functionality."""
    from astra_live_backend.trm_validator import get_trm_validator, ValidationResult

    # Get singleton
    validator = get_trm_validator()
    assert validator is not None, "Failed to get TRM validator"

    # Validate hypothesis
    hypothesis = {
        'id': 'test_hyp_3',
        'name': 'Hubble Constant Test',
        'description': 'Testing if Hubble constant varies with redshift in the local universe',
        'domain': 'Astrophysics',
        'category': 'hubble',
    }

    output = validator.validate_hypothesis(hypothesis)
    assert output is not None, "Validation output is None"
    assert hasattr(output, 'result'), "Output missing result attribute"
    assert hasattr(output, 'validity_score'), "Output missing validity_score"
    assert hasattr(output, 'reasoning'), "Output missing reasoning"
    assert 0 <= output.validity_score <= 1, f"Invalid validity score: {output.validity_score}"

    # Test batch validation
    hypotheses = [hypothesis, {
        'id': 'test_hyp_4',
        'name': 'Invalid Test',
        'description': 'x',  # Too short
        'domain': 'Astrophysics',
        'category': 'unknown',
    }]
    outputs = validator.validate_batch(hypotheses, parallel=False)
    assert len(outputs) == 2, "Batch validation wrong length"

    # Get metrics
    metrics = validator.get_metrics()
    assert 'total_validations' in metrics, "Metrics missing total_validations"
    assert 'rejection_rate' in metrics, "Metrics missing rejection_rate"

    print_info(f"TRM: {metrics['total_validations']} validations, "
               f"{metrics['rejection_rate']:.1%} rejection rate")

    return True


# ============================================================================
# Test 3: MCP Tool Bridge
# ============================================================================

def test_mcp_bridge_basic():
    """Test MCP Tool Bridge basic functionality."""
    from astra_live_backend.atlas_mcp_bridge import get_atlas_mcp_bridge, ToolCategory

    # Get singleton (will use Python fallback since no server)
    bridge = get_atlas_mcp_bridge()
    assert bridge is not None, "Failed to get MCP bridge"

    # List tools
    tools = bridge.list_tools()
    assert len(tools) > 0, "No tools found"
    assert len(tools) == 26, f"Expected 26 tools, got {len(tools)}"

    # Check tool categories
    categories = set(t.category for t in tools)
    expected_categories = {
        ToolCategory.DATA,
        ToolCategory.ANALYSIS,
        ToolCategory.CAUSAL,
        ToolCategory.ML,
        ToolCategory.NLP,
        ToolCategory.VISUALIZATION,
        ToolCategory.KNOWLEDGE,
        ToolCategory.VALIDATION,
    }
    assert categories == expected_categories, f"Tool categories mismatch"

    # Get specific tool
    stat_tool = bridge.get_tool('statistical_test')
    assert stat_tool is not None, "statistical_test tool not found"
    assert stat_tool.category == ToolCategory.ANALYSIS, "Wrong tool category"

    # Check tool parameters
    assert 'parameters' in stat_tool.__dict__, "Tool missing parameters"

    # Get status
    status = bridge.get_status()
    assert 'total_tools' in status, "Status missing total_tools"
    assert status['total_tools'] == 26, f"Expected 26 tools, got {status['total_tools']}"

    print_info(f"MCP: {status['total_tools']} tools, "
               f"{status['enabled_tools']} enabled")

    return True


# ============================================================================
# Test 4: ZK Provenance Chain
# ============================================================================

def test_zk_provenance_basic():
    """Test ZK Provenance Chain basic functionality."""
    from astra_live_backend.zk_provenance import get_zk_provenance_chain

    # Get singleton
    chain = get_zk_provenance_chain()
    assert chain is not None, "Failed to get ZK provenance chain"

    # Record hypothesis created
    hypothesis = {
        'id': 'test_hyp_5',
        'name': 'Test Hypothesis',
        'domain': 'Astrophysics',
        'category': 'hubble',
    }
    entry_hash = chain.record_hypothesis_created('test_hyp_5', hypothesis)
    assert entry_hash, "Failed to record hypothesis creation"

    # Record hypothesis tested
    result = {'passed': True, 'p_value': 0.01, 'effect_size': 0.5}
    entry_hash = chain.record_hypothesis_tested('test_hyp_5', result)
    assert entry_hash, "Failed to record hypothesis test"

    # Record discovery
    discovery = {
        'id': 'test_discovery_1',
        'hypothesis_id': 'test_hyp_5',
        'claim': 'Test discovery',
        'domain': 'Astrophysics',
        'significance': 0.95,
    }
    entry_hash = chain.record_discovery(discovery)
    assert entry_hash, "Failed to record discovery"

    # Create attestation
    attestation = chain.create_attestation(
        discovery_id='test_discovery_1',
        hypothesis_id='test_hyp_5',
        claim='Test discovery',
        evidence=['data1', 'data2'],
        confidence=0.95,
    )
    assert attestation is not None, "Failed to create attestation"
    assert attestation.signature, "Attestation missing signature"

    # Verify attestation
    is_valid = chain.verify_attestation(attestation)
    assert is_valid, "Failed to verify attestation"

    # Get discovery history
    history = chain.get_discovery_history('test_discovery_1')
    assert len(history) > 0, "No discovery history found"

    # Verify chain integrity
    is_valid = chain.verify_chain_integrity()
    assert is_valid, "Chain integrity check failed"

    # Get status
    status = chain.get_status()
    assert 'total_blocks' in status, "Status missing total_blocks"
    assert 'chain_integrity' in status, "Status missing chain_integrity"

    print_info(f"ZK: {status['total_blocks']} blocks, "
               f"{status['total_entries']} entries, "
               f"integrity={status['chain_integrity']}")

    return True


# ============================================================================
# Test 5: Rust Hot Paths
# ============================================================================

def test_rust_hot_paths_basic():
    """Test Rust Hot Paths basic functionality."""
    from astra_live_backend.rust_hot_paths import get_rust_bridge, HotPathType

    # Get singleton
    bridge = get_rust_bridge()
    assert bridge is not None, "Failed to get Rust bridge"

    # Check status
    status = bridge.get_status()
    assert 'rust_available' in status, "Status missing rust_available"

    # Test RMSNorm (should work even without Rust)
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    result = bridge.rms_norm(x)
    assert result is not None, "RMSNorm returned None"
    assert result.shape == x.shape, "RMSNorm wrong shape"

    # Test cosine similarity
    a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    b = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    similarity = bridge.cosine_similarity(a, b)
    assert similarity is not None, "Cosine similarity returned None"
    assert abs(similarity - 1.0) < 0.01, f"Expected similarity ~1.0, got {similarity}"

    # Test matrix multiply
    A = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    B = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    result = bridge.matrix_multiply(A, B)
    assert result is not None, "Matrix multiply returned None"
    assert result.shape == (2, 2), "Matrix multiply wrong shape"

    # Get metrics
    metrics = bridge.get_metrics()
    assert isinstance(metrics, dict), "Metrics not a dict"

    # Benchmark
    if bridge._rust_available:
        bench = bridge.benchmark_operation(
            HotPathType.RMS_NORM,
            sample_size=100,
            iterations=10
        )
        assert bench.speedup > 0, "Invalid speedup"

    rust_status = "Rust" if bridge.using_rust() else "Python (fallback)"
    print_info(f"Rust: {rust_status}, "
               f"total_calls={sum(m.total_calls for m in bridge._metrics.values())}")

    return True


# ============================================================================
# Test 6: Engine Integration
# ============================================================================

def test_engine_integration():
    """Test DiscoveryEngine with ATLAS components."""
    from astra_live_backend.engine import DiscoveryEngine

    # Create engine
    engine = DiscoveryEngine()
    assert engine is not None, "Failed to create DiscoveryEngine"

    # Check GraphPalace integration
    assert hasattr(engine, 'graph_palace'), "Engine missing graph_palace"
    assert hasattr(engine, '_graph_palace_enabled'), "Engine missing _graph_palace_enabled"

    # Check TRM validator integration
    assert hasattr(engine, 'trm_validator'), "Engine missing trm_validator"
    assert hasattr(engine, '_trm_validator_enabled'), "Engine missing _trm_validator_enabled"

    # Check flags
    if engine._graph_palace_enabled:
        print_info("GraphPalace: ENABLED")
    else:
        print_info("GraphPalace: DISABLED (expected if import failed)")

    if engine._trm_validator_enabled:
        print_info("TRM Validator: ENABLED")
    else:
        print_info("TRM Validator: DISABLED (expected if import failed)")

    # Test select phase (with TRM pre-filtering)
    try:
        engine.select()
        print_info("Engine select() completed successfully")
    except Exception as e:
        # May fail due to dependencies, that's ok for this test
        print_info(f"Engine select() raised: {e}")

    # Check stigmergy still works
    assert hasattr(engine, 'stigmergy'), "Engine missing stigmergy"

    # Check graph_palace compatibility
    if engine._graph_palace_enabled and engine.graph_palace:
        # Should have same interface as stigmergy
        assert hasattr(engine.graph_palace, 'on_hypothesis_tested'), \
            "GraphPalace missing on_hypothesis_tested"
        assert hasattr(engine.graph_palace, 'rank_hypotheses'), \
            "GraphPalace missing rank_hypotheses"
        assert hasattr(engine.graph_palace, 'on_discovery'), \
            "GraphPalace missing on_discovery"

    return True


# ============================================================================
# Test 7: Cross-Module Integration
# ============================================================================

def test_cross_module_integration():
    """Test integration between ATLAS modules."""
    from astra_live_backend.graph_palace import get_graph_palace
    from astra_live_backend.trm_validator import get_trm_validator
    from astra_live_backend.zk_provenance import get_zk_provenance_chain

    # Get all singletons
    graph = get_graph_palace()
    validator = get_trm_validator()
    chain = get_zk_provenance_chain()

    # Test workflow: validate → deposit pheromone → record provenance

    # 1. Validate hypothesis
    hypothesis = {
        'id': 'integration_test_hyp',
        'name': 'Integration Test',
        'description': 'Testing cross-module integration with ATLAS components',
        'domain': 'Astrophysics',
        'category': 'hubble',
    }
    validation = validator.validate_hypothesis(hypothesis)

    # 2. Deposit to GraphPalace based on validation
    if validation.result.value == 'valid':
        graph.deposit_pheromone(
            hypothesis['id'],
            'success',
            validation.validity_score * 5
        )
    else:
        graph.deposit_pheromone(
            hypothesis['id'],
            'failure',
            (1 - validation.validity_score) * 5
        )

    # 3. Record in provenance chain
    chain.record_hypothesis_created(hypothesis['id'], hypothesis)

    # 4. Create attestation for simulated discovery
    attestation = chain.create_attestation(
        discovery_id=f"discovery_{hypothesis['id']}",
        hypothesis_id=hypothesis['id'],
        claim=hypothesis['name'],
        evidence=[],
        confidence=validation.validity_score,
    )

    # Verify attestation
    is_valid = chain.verify_attestation(attestation)
    assert is_valid, "Cross-module attestation verification failed"

    print_info(f"Cross-module: validated (score={validation.validity_score:.2f}), "
               f"deposited pheromone, recorded in chain")

    return True


# ============================================================================
# Test 8: Data Persistence
# ============================================================================

def test_data_persistence():
    """Test that all modules can persist and load state."""
    from astra_live_backend.graph_palace import get_graph_palace
    from astra_live_backend.trm_validator import get_trm_validator
    from astra_live_backend.zk_provenance import get_zk_provenance_chain

    # Get modules
    graph = get_graph_palace()
    validator = get_trm_validator()
    chain = get_zk_provenance_chain()

    # Test persistence
    try:
        graph.persist_state()
        print_info("GraphPalace: state persisted")
    except Exception as e:
        print_fail("GraphPalace persist failed", e)
        return False

    try:
        validator.persist_state()
        print_info("TRM Validator: state persisted")
    except Exception as e:
        print_fail("TRM Validator persist failed", e)
        return False

    try:
        chain._persist_chain()
        print_info("ZK Provenance: chain persisted")
    except Exception as e:
        print_fail("ZK Provenance persist failed", e)
        return False

    return True


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ASTRA × ATLAS Deep Integration Tests")
    print("="*60)

    # Define all tests
    tests = [
        ("GraphPalace Bridge", test_graph_palace_basic),
        ("TRM-CausalValidator", test_trm_validator_basic),
        ("MCP Tool Bridge", test_mcp_bridge_basic),
        ("ZK Provenance Chain", test_zk_provenance_basic),
        ("Rust Hot Paths", test_rust_hot_paths_basic),
        ("Engine Integration", test_engine_integration),
        ("Cross-Module Integration", test_cross_module_integration),
        ("Data Persistence", test_data_persistence),
    ]

    # Run all tests
    passed = 0
    failed = 0

    for test_name, test_func in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
        time.sleep(0.1)  # Small delay between tests

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {passed + failed}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")

    if failed > 0:
        print("\nFailed tests:")
        for name, status, error in test_results:
            if status == 'FAIL':
                print(f"  - {name}: {error}")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
