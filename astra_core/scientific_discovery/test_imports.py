#!/usr/bin/env python3
"""
Test script to verify import fixes for astra_core modules.
This verifies that the relative import fixes work correctly.
"""

import sys
import logging
from pathlib import Path

# Set up logging to capture any warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(name)s:%(message)s')

# Add parent directory to path so astra_core can be imported
# We need STAN_IX_ASTRO in the path, not astra_core
project_root = Path(__file__).parent.parent.parent  # Go up from scientific_discovery to STAN_IX_ASTRO
sys.path.insert(0, str(project_root))

def test_adaptive_reasoning_imports():
    """Test adaptive_reasoning.py imports"""
    print("\n" + "="*60)
    print("Testing adaptive_reasoning.py imports")
    print("="*60)

    from astra_core.scientific_discovery.adaptive_reasoning import (
        AdaptiveReasoningController,
        V41_AVAILABLE,
        DiscoveryPhase,
        ReasoningState
    )
    print("✓ AdaptiveReasoningController imported successfully")
    print(f"  V41_AVAILABLE: {V41_AVAILABLE}")

    # Test instantiation
    controller = AdaptiveReasoningController()
    print("✓ AdaptiveReasoningController instantiated successfully")
    assert controller is not None

    # Check what mode it's using
    summary = controller.get_state_summary()
    print(f"  Initial mode: {summary['mode']}")
    print(f"  Initial phase: {summary['phase']}")

    assert 'mode' in summary
    assert 'phase' in summary


def test_discovery_orchestrator_imports():
    """Test discovery_orchestrator.py imports"""
    print("\n" + "="*60)
    print("Testing discovery_orchestrator.py imports")
    print("="*60)

    from astra_core.scientific_discovery.discovery_orchestrator import (
        ScientificDiscoveryOrchestrator,
        HAS_V41_V50_V92,
        HAS_ASTROSWARM,
        HAS_MORK
    )
    print("✓ ScientificDiscoveryOrchestrator imported successfully")
    print(f"  HAS_V41_V50_V92: {HAS_V41_V50_V92}")
    print(f"  HAS_ASTROSWARM: {HAS_ASTROSWARM}")
    print(f"  HAS_MORK: {HAS_MORK}")

    # Test instantiation
    orchestrator = ScientificDiscoveryOrchestrator()
    print("✓ ScientificDiscoveryOrchestrator instantiated successfully")
    assert orchestrator is not None


def test_paper_library_imports():
    """Test paper_library.py imports"""
    print("\n" + "="*60)
    print("Testing paper_library.py imports")
    print("="*60)

    from astra_core.scientific_discovery.paper_library import PaperLibrary
    print("✓ PaperLibrary imported successfully")

    # Test instantiation
    library = PaperLibrary()
    print("✓ PaperLibrary instantiated successfully")
    print(f"  Library path: {library.library_path}")
    assert library is not None

    # Check if it can access existing papers
    stats = library.get_stats()
    print(f"  Papers in library: {stats['total_papers']}")
    print(f"  Total chunks: {stats['total_chunks']}")

    assert 'total_papers' in stats
    assert 'total_chunks' in stats


def test_rag_query_imports():
    """Test paper_rag_query.py imports"""
    print("\n" + "="*60)
    print("Testing paper_rag_query.py imports")
    print("="*60)

    from astra_core.scientific_discovery.paper_rag_query import PaperRAGSystem
    print("✓ PaperRAGSystem imported successfully")

    # Test instantiation
    rag = PaperRAGSystem()
    print("✓ PaperRAGSystem instantiated successfully")
    print(f"  Library path: {rag.library.library_path}")

    assert rag is not None
    assert rag.library is not None


def main():
    """Run all import tests"""
    print("\n" + "="*60)
    print("STAN_IX_ASTRO Import Fix Verification")
    print("="*60)

    results = {}
    for test_name, test_fn in [
        ('adaptive_reasoning', test_adaptive_reasoning_imports),
        ('discovery_orchestrator', test_discovery_orchestrator_imports),
        ('paper_library', test_paper_library_imports),
        ('paper_rag_query', test_rag_query_imports),
    ]:
        try:
            test_fn()
            results[test_name] = True
        except Exception:
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for module, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {module}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All import tests passed!")
        print("  The relative import fixes are working correctly.")
    else:
        print("\n✗ Some import tests failed.")
        print("  Check the error messages above for details.")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}


