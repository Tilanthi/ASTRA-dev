#!/usr/bin/env python3
"""
ASTRA Sleep-Aware Watchdog for Auto-Resume After Sleep/Wake

This script ensures the ASTRA discovery pipeline automatically resumes
after the Mac wakes from sleep, handling intentional shutdowns vs sleep-induced stops.

The key innovation: Uses sleep detection to distinguish between:
1. Intentional shutdown (user stops discovery)
2. Sleep-induced stop (Mac goes to sleep)

Auto-resumes after sleep but respects intentional shutdowns.

Version: 1.1.0
Date: 2026-07-10

v7.2 - Domain Initialization Timeout Fix:
- Increased stuck threshold from 10 minutes to 60 minutes
- Allows for slow ASTRA system initialization (77 domains + multiple components)
- Prevents watchdog from killing processes during normal initialization
"""

import os
import sys
import time
import subprocess
import logging
import signal
from pathlib import Path
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.astra_sleep_watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
ASTRA_DIR = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
ACTIVE_FILE = ASTRA_DIR / ".astra_active"
SHUTDOWN_FILE = ASTRA_DIR / ".astra_intentional_shutdown"
DISCOVERY_SCRIPT = ASTRA_DIR / "start_autonomous_discovery.py"
PYTHON_BIN = "/Users/gjw255/.local/bin/python3"

# Sleep detection
SLEEP_THRESHOLD_SECONDS = 120  # If gap > 2 minutes, assume sleep occurred


class SleepAwareWatchdog:
    """Watchdog that detects sleep/wake and manages discovery lifecycle"""

    def __init__(self):
        self.running = False
        self.discovery_process = None
        self.last_check_time = datetime.now()
        self.shutdown_requested = False

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

    def handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum} - shutting down watchdog")
        self.shutdown_requested = True
        self.stop_discovery()
        sys.exit(0)

    def check_intentional_shutdown(self) -> bool:
        """Check if user intentionally stopped discovery"""
        return SHUTDOWN_FILE.exists()

    def clear_intentional_shutdown(self):
        """Clear intentional shutdown flag (for resume after sleep)"""
        if SHUTDOWN_FILE.exists():
            try:
                SHUTDOWN_FILE.unlink()
                logger.info("Cleared intentional shutdown flag - resuming after sleep")
            except Exception as e:
                logger.error(f"Failed to clear shutdown flag: {e}")

    def detect_sleep(self) -> bool:
        """Detect if system recently woke from sleep"""
        now = datetime.now()
        time_since_last_check = (now - self.last_check_time).total_seconds()

        # If gap > threshold, sleep likely occurred
        if time_since_last_check > SLEEP_THRESHOLD_SECONDS:
            logger.info(f"Sleep detected: {time_since_last_check:.1f}s gap since last check")
            self.last_check_time = now
            return True

        self.last_check_time = now
        return False

    def is_discovery_running(self) -> bool:
        """Check if discovery process is currently running"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'start_autonomous_discovery.py'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking discovery process: {e}")
            return False

    def is_discovery_stuck(self) -> bool:
        """
        Check if discovery process is stuck (running but not making progress)
        Returns True if stuck, False otherwise
        """
        if not self.is_discovery_running():
            return False  # Not running, not stuck

        try:
            # Check last modification time of autonomous log
            log_file = ASTRA_DIR / ".astra_autonomous.log"
            if not log_file.exists():
                return False

            # Get last modification time
            mtime = log_file.stat().st_mtime
            time_since_activity = time.time() - mtime

            # If no log activity for 60 minutes, consider it stuck
            # INCREASED from 10 minutes to allow for slow ASTRA system initialization
            # which loads 77 domains and multiple complex components
            STUCK_THRESHOLD = 3600  # 60 minutes (was 10 minutes)
            if time_since_activity > STUCK_THRESHOLD:
                logger.warning(f"Discovery appears stuck (no log activity for {time_since_activity:.1f}s)")
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking if discovery is stuck: {e}")
            return False

    def start_discovery(self):
        """Start the discovery process"""
        if self.is_discovery_running():
            logger.info("Discovery already running - no need to start")
            return

        logger.info("Starting ASTRA discovery pipeline...")

        # Clear active file and shutdown flag
        if ACTIVE_FILE.exists():
            ACTIVE_FILE.unlink()
        self.clear_intentional_shutdown()

        # Create active file
        ACTIVE_FILE.touch()

        try:
            # Start discovery process
            self.discovery_process = subprocess.Popen(
                [PYTHON_BIN, str(DISCOVERY_SCRIPT)],
                cwd=ASTRA_DIR,
                # DEVNULL (not PIPE): the parent never drains these pipes, so PIPE
                # fills the 16/64KB buffer and the child's next log/print flush
                # blocks forever in _bufferedwriter_flush_unlocked (the init hang).
                # The child self-logs to .astra_autonomous.log via FileHandler, so
                # no diagnostic data is lost by discarding the piped stdout/stderr.
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Discovery process started with PID: {self.discovery_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start discovery: {e}")

    def stop_discovery(self):
        """Stop the discovery process"""
        logger.info("Stopping ASTRA discovery pipeline...")

        try:
            # Kill discovery process
            subprocess.run(['pkill', '-9', '-f', 'start_autonomous_discovery.py'])

            # Mark as intentionally stopped
            SHUTDOWN_FILE.touch()

            # Remove active file
            if ACTIVE_FILE.exists():
                ACTIVE_FILE.unlink()

            logger.info("Discovery stopped and marked as intentional shutdown")
        except Exception as e:
            logger.error(f"Error stopping discovery: {e}")

    def run_watchdog_loop(self):
        """Main watchdog loop - checks for sleep and manages discovery"""
        logger.info("🚀 ASTRA Sleep-Aware Watchdog starting...")

        # First startup - always start discovery
        self.start_discovery()

        while not self.shutdown_requested:
            try:
                # Sleep for 30 seconds between checks
                time.sleep(30)

                # Check for sleep/wake
                if self.detect_sleep():
                    logger.info("System woke from sleep - checking discovery status...")

                    # Clear intentional shutdown flag after sleep (user wants auto-resume)
                    self.clear_intentional_shutdown()

                    # Restart discovery if not running
                    if not self.is_discovery_running():
                        logger.info("Auto-resuming discovery after sleep...")
                        self.start_discovery()
                    else:
                        logger.info("Discovery already running after wake")

                # Check if discovery died (not intentional)
                if not self.is_discovery_running() and not self.check_intentional_shutdown():
                    logger.warning("Discovery died unexpectedly - restarting...")
                    self.start_discovery()

                # CRITICAL FIX: Check if discovery is stuck (running but not making progress)
                if self.is_discovery_running() and self.is_discovery_stuck():
                    logger.warning("Discovery process stuck - restarting...")
                    self.stop_discovery()
                    time.sleep(5)  # Wait for cleanup
                    self.start_discovery()

                # If discovery is running but marked as intentional shutdown, clear it
                if self.is_discovery_running() and self.check_intentional_shutdown():
                    logger.info("Discovery running with shutdown flag - clearing flag")
                    self.clear_intentional_shutdown()

            except Exception as e:
                logger.error(f"Error in watchdog loop: {e}")
                time.sleep(60)  # Wait before retrying

        logger.info("Watchdog loop ended")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("ASTRA Sleep-Aware Watchdog v1.0.0")
    logger.info("Auto-Resume After Sleep/Wake Architecture")
    logger.info("=" * 60)
    logger.info(f"Starting at: {datetime.now().isoformat()}")
    logger.info("Features:")
    logger.info("- Auto-detects Mac sleep/wake cycles")
    logger.info("- Resumes discovery after system wake")
    logger.info("- Distinguishes intentional vs sleep-induced stops")
    logger.info("- 30-second check interval")
    logger.info("=" * 60)

    watchdog = SleepAwareWatchdog()
    watchdog.run_watchdog_loop()


if __name__ == "__main__":
    main()
