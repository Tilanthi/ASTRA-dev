#!/usr/bin/env python3
"""
24/7 Autonomous Discovery Runner for ASTRA
=============================================

This script runs ASTRA with autonomous discovery continuously in the background.
Start discovery automatically and keep it running 24/7.

Usage:
    python run_24_7_discovery.py

The discovery system will:
- Start automatically when ASTRA initializes
- Run continuous discovery cycles every 30 minutes
- Adapt behavior based on system activity
- Persist state across sessions
- Log all discoveries to file

To stop: Ctrl+C or kill the process
"""

import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path.home() / ".astra_persistent"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "24_7_discovery.log"

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
    """Main 24/7 discovery runner"""
    logger.info("=" * 60)
    logger.info("STARTING 24/7 AUTONOMOUS DISCOVERY SYSTEM")
    logger.info("=" * 60)

    try:
        # Import ASTRA
        from astra_core import create_stan_system
        from astra_core.autonomous_startup_discovery import get_autonomous_startup_discovery

        logger.info("Creating ASTRA system with autonomous discovery...")

        # Create ASTRA system - this automatically starts discovery
        system = create_stan_system()

        logger.info("✅ ASTRA system initialized with autonomous discovery")

        # Get discovery instance
        discovery = get_autonomous_startup_discovery()

        logger.info(f"Discovery state: {discovery.state.value}")
        logger.info(f"Discovery mode: {discovery.config.mode.value}")
        logger.info(f"Discovery interval: {discovery.config.discovery_interval_seconds}s")

        # Log initial status
        logger.info(f"ASTRA system connected: {discovery.astra_system is not None}")
        logger.info(f"Discovery thread alive: {discovery.discovery_thread.is_alive() if discovery.discovery_thread else False}")

        logger.info("✅ 24/7 DISCOVERY SYSTEM NOW RUNNING")
        logger.info("=" * 60)
        logger.info("Discovery will run continuously in background.")
        logger.info("Check status and discoveries in:")
        logger.info(f"  - Log file: {log_file}")
        logger.info(f"  - State file: {log_dir / 'startup_discovery_state.json'}")
        logger.info("=" * 60)

        # Keep the main process alive
        # Discovery runs in background thread, so we just need to keep main thread running
        try:
            while True:
                time.sleep(3600)  # Check every hour

                # Log status periodically
                discovery = get_autonomous_startup_discovery()
                logger.info(f"Status Check - State: {discovery.state.value}, "
                          f"Cycles: {discovery.discovery_cycles_completed}, "
                          f"Discoveries: {len(discovery.discoveries_made)}")

        except KeyboardInterrupt:
            logger.info("Shutting down 24/7 discovery system...")
            discovery.stop()
            logger.info("24/7 discovery system stopped")

    except Exception as e:
        logger.error(f"Error starting 24/7 discovery system: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()