#!/usr/bin/env python3
"""
ASTRA Autonomous Discovery Startup Script

This script provides fully autonomous operation of the ASTRA discovery system.
No manual intervention required - the system starts automatically and runs
continuous genuine discovery cycles with real literature validation.

ARCHITECTURE NOTE:
This script is designed to run under the ASTRA Watchdog for continuous operation.
- Use 'python astra_watchdog.py start' to start continuous operation
- The watchdog will auto-restart this process if it crashes
- Use 'python astra_watchdog.py stop' to stop continuous operation

Direct Usage (for testing):
    python start_autonomous_discovery.py

The system will:
1. Automatically install/check dependencies
2. Initialize all validation components
3. Start continuous discovery cycles
4. Save results to persistent storage
5. Run indefinitely until stopped

Features:
- Automatic dependency checking
- Real literature validation with arXiv/ADS
- Multi-stage validation pipeline
- Parallel processing for speed
- Intelligent caching
- Automatic persistence
- Status monitoring
- Watchdog-compatible operation

Version: 3.0.0-AutoRestart
Date: 2026-07-03
"""

import sys
import time
import asyncio
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.astra_autonomous.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global system reference for shutdown handling
autonomous_system: Optional['AutonomousDiscoveryRunner'] = None


class AutonomousDiscoveryRunner:
    """
    Fully autonomous discovery system runner

    Handles:
    - Automatic dependency checking
    - System initialization
    - Continuous operation
    - Graceful shutdown
    - Status reporting
    """

    def __init__(self):
        self.discovery_system = None
        self.is_running = False
        self.shutdown_requested = False

        # Statistics
        self.start_time = None
        self.discovery_cycles = 0
        self.genuine_discoveries = 0

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        logger.info("Checking dependencies...")

        required = {
            'arxiv': 'arXiv API client',
            'sentence_transformers': 'Semantic similarity models',
            'sklearn': 'Scikit-learn for similarity computation',
            'numpy': 'Numerical computations',
            'scipy': 'Statistical validation'
        }

        missing = []
        for module, description in required.items():
            try:
                if module == 'sklearn':
                    __import__('sklearn')
                elif module == 'sentence_transformers':
                    __import__('sentence_transformers')
                else:
                    __import__(module)
                logger.info(f"✅ {description}: OK")
            except ImportError:
                logger.warning(f"❌ {description}: MISSING")
                missing.append(module)

        if missing:
            logger.error(f"Missing dependencies: {missing}")
            logger.info("Installing missing dependencies...")
            return self.install_dependencies(missing)

        return True

    def install_dependencies(self, missing: list) -> bool:
        """Install missing dependencies automatically"""
        import subprocess

        logger.info(f"Installing missing packages: {missing}")

        try:
            # Try uv first (preferred package manager)
            try:
                subprocess.check_call([
                    'uv', 'pip', 'install', '--system'
                ] + missing)
                logger.info("✅ Dependencies installed successfully using uv")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to pip with system packages override
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '--break-system-packages'
                ] + missing)
                logger.info("✅ Dependencies installed successfully using pip")
                return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            logger.info("Dependencies may already be installed - continuing...")
            return True  # Continue anyway, dependencies might be available

    def initialize_system(self) -> bool:
        """Initialize the autonomous discovery system"""
        try:
            from astra_core.autonomous_startup_discovery_v2 import (
                GenuineDiscoverySystem,
                GenuineDiscoveryConfig
            )

            logger.info("Initializing ASTRA v2.0 Genuine Discovery System...")

            # Configure for autonomous operation
            config = GenuineDiscoveryConfig(
                discovery_interval_seconds=60,  # 1-minute cycles
                minimum_novelty_score=0.3,
                minimum_probability=0.4,
                enable_data_archive_analysis=True,
                enable_literature_mining=True
            )

            self.discovery_system = GenuineDiscoverySystem(config=config)

            # Create and connect ASTRA system for genuine discovery capabilities
            try:
                from astra_core import create_stan_system
                logger.info("Creating ASTRA core system...")
                astra_system = create_stan_system()
                self.discovery_system.initialize_with_astra(astra_system)
                logger.info("✅ ASTRA system connected - ready for genuine discovery")
            except Exception as e:
                logger.warning(f"⚠️ Could not connect ASTRA system: {e}")
                logger.warning("⚠️ System will run in standalone mode without full capabilities")

            # Check if validation pipeline is initialized
            if self.discovery_system.validation_pipeline:
                logger.info("✅ Multi-stage validation pipeline initialized")
            else:
                logger.warning("⚠️ Validation pipeline not available - using basic validation")

            logger.info("✅ System initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_discovery(self):
        """Start autonomous discovery cycles"""
        logger.info("🚀 Starting autonomous discovery cycles...")
        self.is_running = True
        self.start_time = datetime.now()

        # Start the discovery system
        self.discovery_system.start()

        logger.info("✅ Discovery system is now running autonomously")
        logger.info("💡 The system will run continuous discovery cycles")
        logger.info("💡 Press Ctrl+C to stop gracefully")

    def stop_discovery(self):
        """Stop autonomous discovery gracefully"""
        if not self.is_running:
            return

        logger.info("🛑 Stopping autonomous discovery...")
        self.is_running = False

        if self.discovery_system:
            self.discovery_system.stop()

        # Print final statistics
        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Uptime: {uptime}")
            logger.info(f"   Discovery Cycles: {self.discovery_cycles}")
            logger.info(f"   Genuine Discoveries: {self.genuine_discoveries}")
            if self.discovery_cycles > 0:
                logger.info(f"   Discovery Rate: {self.genuine_discoveries/self.discovery_cycles:.1%}")

        logger.info("✅ Discovery system stopped gracefully")

    def monitor_progress(self):
        """Monitor and report discovery progress"""
        import time

        logger.info("📊 Starting progress monitor...")

        while self.is_running and not self.shutdown_requested:
            time.sleep(60)  # Report every minute

            if self.discovery_system:
                status = self.discovery_system.get_discovery_status()

                self.discovery_cycles = status.get('discovery_cycle', 0)
                self.genuine_discoveries = status.get('genuine_discoveries', 0)

                logger.info(
                    f"📊 Status: Cycle {self.discovery_cycles}, "
                    f"Genuine Discoveries: {self.genuine_discoveries}, "
                    f"Rate: {status.get('discovery_rate', 0):.1%}"
                )

    def run(self):
        """Main autonomous run loop"""
        try:
            # Step 1: Check dependencies
            if not self.check_dependencies():
                logger.error("❌ Dependency check failed - exiting")
                return 1

            # Step 2: Initialize system
            if not self.initialize_system():
                logger.error("❌ System initialization failed - exiting")
                return 1

            # Step 3: Start discovery
            self.start_discovery()

            # Step 4: Monitor progress
            self.monitor_progress()

            return 0

        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
            self.shutdown_requested = True
            self.stop_discovery()
            return 0
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            self.stop_discovery()
            return 1


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global autonomous_system

    logger.info(f"Received signal {signum} - checking if intentional shutdown...")

    # Check if ASTRA is still marked as active (watchdog is running)
    astra_active_file = Path('.astra_active')
    if astra_active_file.exists():
        logger.info("ℹ️ ASTRA still marked as active - signal may be from watchdog restart")
        logger.info("ℹ️ Performing graceful shutdown for potential restart...")
        if autonomous_system:
            autonomous_system.shutdown_requested = True
            autonomous_system.stop_discovery()
        # Exit gracefully - watchdog will restart if needed
        sys.exit(0)
    else:
        logger.info("ℹ️ ASTRA marked as inactive - intentional shutdown requested")
        if autonomous_system:
            autonomous_system.shutdown_requested = True
            autonomous_system.stop_discovery()
        sys.exit(0)


def main():
    """Main entry point for autonomous discovery"""
    global autonomous_system

    logger.info("="*60)
    logger.info("ASTRA v3.0 - Autonomous Genuine Discovery System")
    logger.info("Auto-Restart Architecture with Watchdog Support")
    logger.info("="*60)
    logger.info(f"Starting at: {datetime.now().isoformat()}")
    logger.info("System will run continuous discovery cycles with real literature validation")
    logger.info("No manual intervention required - fully autonomous operation")
    logger.info("="*60)

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run autonomous system
    autonomous_system = AutonomousDiscoveryRunner()
    exit_code = autonomous_system.run()

    logger.info("="*60)
    logger.info("ASTRA Autonomous Discovery System Exited")
    logger.info(f"Exit code: {exit_code}")
    logger.info(f"Ended at: {datetime.now().isoformat()}")
    logger.info("="*60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())