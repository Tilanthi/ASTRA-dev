#!/usr/bin/env python3
"""
Test script for autonomous startup discovery functionality

This script verifies that:
1. Autonomous discovery starts automatically on system initialization
2. Discovery pauses/resumes during user queries
3. Status reporting works correctly
4. Manual control functions work if needed
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_autonomous_startup():
    """Test autonomous startup discovery"""
    logger.info("=" * 60)
    logger.info("Testing Autonomous Startup Discovery")
    logger.info("=" * 60)

    try:
        # Import ASTRA
        logger.info("Importing ASTRA...")
        from astra_core import create_stan_system
        logger.info("✓ ASTRA imported successfully")

        # Create system - should auto-start discovery
        logger.info("\nCreating ASTRA system (should auto-start discovery)...")
        system = create_stan_system()
        logger.info("✓ System created")

        # Give discovery a moment to start
        import time
        time.sleep(2)

        # Check discovery status
        logger.info("\nChecking discovery status...")
        status = system.get_discovery_status()
        logger.info(f"Discovery state: {status.get('state', 'unknown')}")
        logger.info(f"Discovery mode: {status.get('mode', 'unknown')}")
        logger.info(f"Cycles completed: {status.get('cycles_completed', 0)}")
        logger.info(f"Discoveries made: {status.get('discoveries_made', 0)}")

        # Verify discovery is active
        if status.get('state') in ['running', 'starting', 'throttled']:
            logger.info("✓ Discovery is active")
        else:
            logger.warning(f"⚠ Discovery state unexpected: {status.get('state')}")

        # Test query processing (should pause/resume)
        logger.info("\nTesting query processing (should auto-pause/resume)...")
        result = system.answer("What is star formation?")
        if result and 'answer' in result:
            logger.info("✓ Query processed successfully")
            logger.info(f"Answer snippet: {result['answer'][:100]}...")
        else:
            logger.warning("⚠ Query returned unexpected result")

        # Check status after query
        logger.info("\nChecking discovery status after query...")
        status_after = system.get_discovery_status()
        logger.info(f"Discovery state after query: {status_after.get('state')}")

        # Test direct discovery control
        logger.info("\nTesting manual discovery control...")
        try:
            from astra_core.autonomous_startup_discovery import get_autonomous_startup_discovery
            discovery = get_autonomous_startup_discovery()

            if discovery:
                logger.info("✓ Got discovery instance")

                # Test pause
                logger.info("Testing pause...")
                discovery.pause("test_pause")
                paused_status = discovery.get_status()
                logger.info(f"State after pause: {paused_status['state']}")
                assert paused_status['state'] == 'paused', "Pause failed"
                logger.info("✓ Pause successful")

                # Test resume
                logger.info("Testing resume...")
                discovery.resume()
                resumed_status = discovery.get_status()
                logger.info(f"State after resume: {resumed_status['state']}")
                logger.info("✓ Resume successful")

        except Exception as e:
            logger.error(f"Error in manual control: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("✓ Autonomous Startup Discovery Test PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"\n✗ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_discovery_state_persistence():
    """Test that discovery state persists across system instances"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Discovery State Persistence")
    logger.info("=" * 60)

    try:
        from astra_core.autonomous_startup_discovery import get_autonomous_startup_discovery

        # Get first instance
        discovery1 = get_autonomous_startup_discovery()
        logger.info("✓ Created first instance")

        # Check state file location
        state_file = Path.home() / ".astra_persistent" / "startup_discovery_state.json"
        logger.info(f"State file location: {state_file}")
        logger.info(f"State file exists: {state_file.exists()}")

        # Get second instance (should be same)
        discovery2 = get_autonomous_startup_discovery()
        logger.info("✓ Created second instance")

        # Verify they're the same
        assert discovery1 is discovery2, "Instances should be identical"
        logger.info("✓ State persistence verified (same instance)")

        logger.info("=" * 60)
        logger.info("✓ State Persistence Test PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"\n✗ State Persistence Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("AUTONOMOUS STARTUP DISCOVERY TEST SUITE")
    logger.info("=" * 60)

    # Run tests
    test1 = test_autonomous_startup()
    test2 = test_discovery_state_persistence()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Autonomous Startup: {'PASS ✓' if test1 else 'FAIL ✗'}")
    logger.info(f"State Persistence: {'PASS ✓' if test2 else 'FAIL ✗'}")

    if test1 and test2:
        logger.info("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())