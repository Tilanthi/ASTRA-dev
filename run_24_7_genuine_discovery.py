#!/usr/bin/env python3
"""
24/7 Genuine Autonomous Discovery Runner for ASTRA v2.0
======================================================

This script runs ASTRA with GENUINE autonomous discovery continuously in the background.
Focus on novel scientific discoveries rather than knowledge synthesis.

Usage:
    python run_24_7_genuine_discovery.py

The genuine discovery system will:
- Focus on novel patterns, theoretical synthesis, and testable hypotheses
- Apply rigorous validation (novelty assessment, probability estimation)
- Store only discoveries that meet genuine research standards
- Maintain persistent memory of validated insights

Version: 2.0.0
"""

import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path.home() / ".astra_persistent"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "24_7_genuine_discovery.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main 24/7 genuine discovery runner"""
    logger.info("=" * 80)
    logger.info("STARTING 24/7 GENUINE AUTONOMOUS DISCOVERY SYSTEM v2.0")
    logger.info("=" * 80)
    logger.info("Focus: Novel scientific discoveries, not knowledge synthesis")
    logger.info("Validation: Rigorous novelty assessment, probability estimation")
    logger.info("Storage: Only discoveries meeting genuine research standards")

    try:
        # Import ASTRA
        from astra_core import create_stan_system
        from astra_core.autonomous_startup_discovery_v2 import get_genuine_discovery_system

        logger.info("Creating ASTRA system with genuine discovery...")

        # Create ASTRA system - this automatically starts genuine discovery
        system = create_stan_system()

        logger.info("✅ ASTRA system initialized")

        # Get genuine discovery instance
        genuine_discovery = get_genuine_discovery_system()

        if not genuine_discovery:
            logger.error("❌ Failed to initialize genuine discovery system")
            sys.exit(1)

        logger.info("✅ Genuine discovery system v2.0 initialized")
        logger.info(f"Discovery standards:")
        logger.info(f"  - Minimum novelty score: {genuine_discovery.config.minimum_novelty_score}")
        logger.info(f"  - Minimum probability: {genuine_discovery.config.minimum_probability}")
        logger.info(f"  - Testability required: {genuine_discovery.config.require_testability}")

        # Log initial status
        logger.info(f"Previous discoveries loaded: {len(genuine_discovery.genuine_discoveries)}")
        logger.info(f"Discovery cycle: {genuine_discovery.discovery_cycle}")

        if genuine_discovery.genuine_discoveries:
            latest = genuine_discovery.genuine_discoveries[-1]
            logger.info(f"Latest discovery: {latest.title}")
            logger.info(f"  Novelty: {latest.novelty_level.value}")
            logger.info(f"  Probability correct: {latest.validation.probability_correct}")

        logger.info("")
        logger.info("=" * 80)
        logger.info("🚀 24/7 GENUINE DISCOVERY SYSTEM NOW RUNNING")
        logger.info("=" * 80)
        logger.info("Discovery types enabled:")
        logger.info(f"  - Pattern discovery: {genuine_discovery.config.enable_pattern_discovery}")
        logger.info(f"  - Theoretical synthesis: {genuine_discovery.config.enable_theoretical_synthesis}")
        logger.info(f"  - Gap identification: {genuine_discovery.config.enable_gap_identification}")
        logger.info(f"  - Predictive hypothesis: {genuine_discovery.config.enable_predictive_hypothesis}")
        logger.info(f"  - Computational reanalysis: {genuine_discovery.config.enable_computational_reanalysis}")
        logger.info("")
        logger.info("Check status and discoveries in:")
        logger.info(f"  - Log file: {log_file}")
        logger.info(f"  - Discovery store: {genuine_discovery.discoverystore_path}")
        logger.info("=" * 80)

        # Keep the main process alive
        try:
            while True:
                time.sleep(3600)  # Check every hour

                # Log status periodically
                genuine_discovery = get_genuine_discovery_system()
                status = genuine_discovery.get_status()

                logger.info(f"Status Check - Cycle: {status['discovery_cycle']}, "
                          f"Genuine discoveries: {status['genuine_discoveries']}, "
                          f"Discovery rate: {status['discovery_rate']:.3f}")

                if status['latest_discovery']:
                    logger.info(f"Latest: {status['latest_discovery']}")

        except KeyboardInterrupt:
            logger.info("Shutting down 24/7 genuine discovery system...")
            genuine_discovery.stop()
            logger.info("✅ Genuine discovery system stopped gracefully")

    except Exception as e:
        logger.error(f"❌ Error starting 24/7 genuine discovery system: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()