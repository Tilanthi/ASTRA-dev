"""
Autonomous ASTRA Capabilities Test Script

This script demonstrates and tests the new autonomous capabilities integrated into ASTRA.

Run this script to verify:
1. AutonomyOrchestrator integration
2. GenuineDiscoveryGenerator with contemporary research
3. AdaptiveDecisionEngine with novel decision-making
4. ContinuousAutonomousProcess for background operation
5. Full autonomous system integration

Usage:
    python test_autonomous_capabilities.py

Date: 2026-06-27
"""

import sys
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_autonomy_orchestrator():
    """Test Phase 1: Autonomy Orchestrator"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Autonomy Orchestrator")
    logger.info("="*70)

    try:
        from astra_core.autonomy import create_autonomy_orchestrator, create_autonomy_config

        # Create orchestrator with moderate autonomy
        config = create_autonomy_config(
            autonomy_level=0.7,
            enable_idle_exploration=True,
            enable_sub_agent_spawning=True,
            primary_domains=["astrophysics", "astronomy"]
        )

        orchestrator = create_autonomy_orchestrator(
            autonomy_level=0.7,
            config=config
        )

        logger.info("✓ Autonomy Orchestrator created successfully")

        # Test sub-agent spawning
        sub_agent_id = orchestrator.spawn_discovery_subagent(
            domain="astrophysics",
            objective="Explore filament structure variations",
            capabilities=["discovery", "analysis"]
        )

        logger.info(f"✓ Sub-agent spawned: {sub_agent_id}")

        # Test idle exploration
        orchestrator.update_activity()  # Simulate activity
        time.sleep(1)  # Small delay to test idle detection

        # Get status
        status = orchestrator.get_status()
        logger.info(f"✓ Orchestrator status: {status['autonomy_level']} autonomy level")
        logger.info(f"  - Sub-agents spawned: {status['sub_agents_spawned']}")
        logger.info(f"  - Capabilities initialized: {sum(status['capabilities_initialized'].values())}/4")

        return True

    except Exception as e:
        logger.error(f"✗ Autonomy Orchestrator test failed: {e}")
        return False


def test_genuine_discovery_generator():
    """Test Phase 2: Genuine Discovery Generator"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Genuine Discovery Generator")
    logger.info("="*70)

    try:
        from astra_core.autonomy import (
            create_genuine_discovery_generator,
            generate_contemporary_discovery,
            DiscoveryType
        )

        # Create discovery generator
        generator = create_genuine_discovery_generator()
        logger.info("✓ Genuine Discovery Generator created")

        # Test contemporary research analysis
        context = generator.analyze_contemporary_research(
            domain="astrophysics",
            topic="filament structure",
            time_window_days=180
        )

        logger.info(f"✓ Analyzed contemporary research: {len(context.recent_papers)} papers")
        logger.info(f"  - Research trend: {context.trend.value}")
        logger.info(f"  - Research gap: {context.research_gap}")

        # Test genuine hypothesis generation
        hypothesis = generator.generate_genuine_hypothesis(
            domain="astrophysics",
            topic="magnetic fields in filaments",
            discovery_type=DiscoveryType.THEORETICAL
        )

        logger.info(f"✓ Genuine hypothesis generated: {hypothesis.statement[:80]}...")
        logger.info(f"  - Novelty score: {hypothesis.novelty_score:.2f}")
        logger.info(f"  - Confidence: {hypothesis.confidence:.2f}")

        # Test discovery validation
        validation = generator.validate_discovery(hypothesis)
        logger.info(f"✓ Discovery validation: {validation.validation_status.value}")
        logger.info(f"  - Novelty confirmed: {validation.novelty_confirmed}")
        logger.info(f"  - Validation confidence: {validation.confidence_score:.2f}")

        # Get status
        status = generator.get_status()
        logger.info(f"✓ Generator status: {status['hypotheses_generated']} hypotheses, {status['novel_discoveries']} novel discoveries")

        return True

    except Exception as e:
        logger.error(f"✗ Genuine Discovery Generator test failed: {e}")
        return False


def test_adaptive_decision_engine():
    """Test Phase 3: Adaptive Decision Engine"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Adaptive Decision Engine")
    logger.info("="*70)

    try:
        from astra_core.autonomy import (
            create_adaptive_decision_engine,
            make_autonomous_decision,
            DecisionOption,
            RiskLevel
        )

        # Create decision engine
        engine = create_adaptive_decision_engine(autonomy_level=0.7)
        logger.info("✓ Adaptive Decision Engine created")

        # Test autonomous decision making
        context = {
            'domain': 'astrophysics',
            'uncertainty': 0.6,
            'exploration_ratio': 0.3
        }

        options = [
            DecisionOption(
                option_id="standard",
                description="Use standard analysis methods",
                expected_value=0.7,
                novelty_score=0.3,
                risk_level=RiskLevel.MINIMAL,
                feasibility=0.9,
                confidence=0.8
            ),
            DecisionOption(
                option_id="novel",
                description="Apply novel machine learning approach",
                expected_value=0.6,
                novelty_score=0.8,
                risk_level=RiskLevel.MODERATE,
                feasibility=0.6,
                confidence=0.5
            )
        ]

        decision = engine.make_adaptive_decision(context, options)

        logger.info(f"✓ Autonomous decision made: {decision.selected_option.description[:60]}...")
        logger.info(f"  - Strategy used: {decision.strategy_used.value}")
        logger.info(f"  - Confidence: {decision.confidence:.2f}")
        logger.info(f"  - Rationale: {decision.rationale[:80]}...")

        # Test curiosity signal generation
        curiosity = engine.generate_curiosity_signal(
            topic="turbulent cascade in ISM",
            domain="astrophysics",
            intensity=0.8
        )

        logger.info(f"✓ Curiosity signal generated: {curiosity.topic} (intensity: {curiosity.intensity:.2f})")

        # Test novel behavior exploration
        exploration = engine.explore_novel_behavior("astrophysics", context)
        logger.info(f"✓ Novel behavior exploration: {exploration['selected_behavior'][:60]}...")

        # Get status
        status = engine.get_status()
        logger.info(f"✓ Decision engine status: {status['decisions_made']} decisions, {status['novel_options_selected']} novel selections")

        return True

    except Exception as e:
        logger.error(f"✗ Adaptive Decision Engine test failed: {e}")
        return False


def test_continuous_autonomous_process():
    """Test Phase 4: Continuous Autonomous Process"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Continuous Autonomous Process")
    logger.info("="*70)

    try:
        from astra_core.autonomy import create_continuous_autonomous_process

        # Create continuous process
        process = create_continuous_autonomous_process()
        logger.info("✓ Continuous Autonomous Process created")

        # Start process
        process.start()
        logger.info("✓ Continuous process started")

        # Wait a bit to see activity
        time.sleep(2)

        # Update user activity
        process.update_user_activity()
        logger.info("✓ User activity updated")

        # Get status
        status = process.get_status()
        logger.info(f"✓ Process status: {status['state']}")
        logger.info(f"  - Active activities: {status['active_activities']}")
        logger.info(f"  - Queued activities: {status['queued_activities']}")
        logger.info(f"  - Success rate: {status['success_rate']:.2f}")

        # Stop process
        process.stop()
        logger.info("✓ Continuous process stopped")

        return True

    except Exception as e:
        logger.error(f"✗ Continuous Autonomous Process test failed: {e}")
        return False


def test_full_autonomous_integration():
    """Test Full Autonomous System Integration"""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: Full Autonomous System Integration")
    logger.info("="*70)

    try:
        from astra_core.autonomous_integration import (
            create_autonomous_astra,
            AutonomousMode,
            initialize_astra_with_autonomy
        )

        # Test full autonomous system creation
        system = create_autonomous_astra(
            mode=AutonomousMode.IDLE_EXPLORATION,
            autonomy_level=0.7,
            domains=["astrophysics", "astronomy"]
        )

        logger.info("✓ Full autonomous ASTRA system created")

        # Test processing with autonomy
        result = system.process_with_autonomy(
            "Analyze magnetic field variations in molecular cloud filaments"
        )

        logger.info(f"✓ Processed with autonomy: {result['autonomy_used']}")
        logger.info(f"  - Mode: {result['mode']}")
        logger.info(f"  - Autonomy level: {result['autonomy_level']:.2f}")

        # Test autonomous discovery generation
        discovery = system.generate_autonomous_discovery(
            domain="astrophysics",
            topic="filament width variations"
        )

        if discovery:
            logger.info(f"✓ Autonomous discovery generated: {discovery['hypothesis'][:60]}...")
            logger.info(f"  - Novelty score: {discovery['novelty_score']:.2f}")
            logger.info(f"  - Validation: {discovery['validation_status']}")

        # Get comprehensive status
        status = system.get_autonomous_status()
        logger.info(f"✓ System status retrieved")
        logger.info(f"  - Discoveries made: {status['discoveries_made']}")
        logger.info(f"  - Significant discoveries: {status['significant_discoveries']}")

        # Shutdown
        system.shutdown()
        logger.info("✓ System shutdown successfully")

        return True

    except Exception as e:
        logger.error(f"✗ Full autonomous integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all autonomous capability tests"""
    logger.info("\n" + "="*70)
    logger.info("ASTRA AUTONOMOUS CAPABILITIES TEST SUITE")
    logger.info("Testing all phases of autonomy implementation")
    logger.info("="*70)

    results = {
        'AutonomyOrchestrator': test_autonomy_orchestrator(),
        'GenuineDiscoveryGenerator': test_genuine_discovery_generator(),
        'AdaptiveDecisionEngine': test_adaptive_decision_engine(),
        'ContinuousAutonomousProcess': test_continuous_autonomous_process(),
        'FullAutonomousIntegration': test_full_autonomous_integration()
    }

    # Print summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✓ PASSED" if passed_test else "✗ FAILED"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 ALL AUTONOMOUS CAPABILITIES VERIFIED!")
        return 0
    else:
        logger.warning("⚠️  Some tests failed - review logs above")
        return 1


if __name__ == "__main__":
    sys.exit(main())