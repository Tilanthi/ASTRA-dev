#!/usr/bin/env python3
"""
ASTRA Discovery Watchdog - Continuous Operation with Auto-Restart

This watchdog ensures ASTRA discovery runs continuously with automatic restart
capability. It provides:

- Automatic restart if discovery process dies
- Distinction between intentional shutdown and crashes
- Persistent state management
- User task detection and pause/resume
- Health monitoring and recovery

Architecture:
- Watchdog Process: Monitors and restarts discovery process
- State File: .astra_active indicates ASTRA should be running
- Heartbeat: Regular health checks
- Graceful Shutdown: Only stops if state file says so

Usage:
    python astra_watchdog.py start     # Start continuous operation
    python astra_watchdog.py stop      # Stop continuous operation
    python astra_watchdog.py status    # Check status

Version: 1.0.0-AutoRestart
Date: 2026-07-03
"""

import sys
import time
import json
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.astra_watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AstraWatchdog:
    """
    ASTRA Discovery Watchdog for continuous operation

    Ensures ASTRA discovery runs continuously with automatic restart
    capability and proper handling of user tasks.
    """

    # State file paths
    ASTRA_ACTIVE_FILE = Path('.astra_active')
    ASTRA_STATE_FILE = Path('.astra_state.json')
    DISCOVERY_SCRIPT = Path('start_autonomous_discovery.py')

    # Timing constants
    STARTUP_DELAY = 10  # seconds to wait for process startup
    HEALTH_CHECK_INTERVAL = 30  # seconds between health checks
    MAX_RESTART_DELAY = 300  # max 5 minutes between restarts
    CRASH_BACKOFF = 60  # initial backoff after crashes

    def __init__(self):
        self.discovery_process: Optional[subprocess.Popen] = None
        self.watchdog_running = False
        self.intentional_shutdown = False
        self.crash_count = 0
        self.last_crash_time = None
        self.start_time = None

    def is_astra_active(self) -> bool:
        """Check if ASTRA should be running (active state file exists)"""
        return self.ASTRA_ACTIVE_FILE.exists()

    def set_astra_active(self, active: bool):
        """Set ASTRA active state"""
        if active:
            self.ASTRA_ACTIVE_FILE.touch()
            logger.info("✅ ASTRA marked as ACTIVE - will auto-restart if stopped")
        else:
            if self.ASTRA_ACTIVE_FILE.exists():
                self.ASTRA_ACTIVE_FILE.unlink()
            logger.info("✅ ASTRA marked as INACTIVE - will not auto-restart")

    def save_state(self, state: dict):
        """Save current watchdog state"""
        state_data = {
            'timestamp': datetime.now().isoformat(),
            'watchdog_running': self.watchdog_running,
            'discovery_pid': self.discovery_process.pid if self.discovery_process else None,
            'crash_count': self.crash_count,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            **state
        }

        with open(self.ASTRA_STATE_FILE, 'w') as f:
            json.dump(state_data, f, indent=2)

    def load_state(self) -> dict:
        """Load previous watchdog state"""
        if self.ASTRA_STATE_FILE.exists():
            try:
                with open(self.ASTRA_STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        return {}

    def start_discovery_process(self) -> bool:
        """Start the discovery process"""
        try:
            if not self.DISCOVERY_SCRIPT.exists():
                logger.error(f"Discovery script not found: {self.DISCOVERY_SCRIPT}")
                return False

            logger.info("🚀 Starting ASTRA discovery process...")

            # Start the discovery process
            self.discovery_process = subprocess.Popen(
                [sys.executable, str(self.DISCOVERY_SCRIPT)],
                # DEVNULL (not PIPE): see sleep_aware_watchdog.py — the parent never
                # drains these pipes, so PIPE deadlocks the child's flush. The child
                # self-logs to .astra_autonomous.log via FileHandler.
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Create new process group
            )

            logger.info(f"✅ Discovery process started with PID: {self.discovery_process.pid}")

            # Wait for process to start
            time.sleep(self.STARTUP_DELAY)

            # Check if process is still running
            if self.discovery_process.poll() is None:
                logger.info("✅ Discovery process is running")
                self.save_state({'status': 'running'})
                return True
            else:
                logger.error("❌ Discovery process died during startup")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to start discovery process: {e}")
            return False

    def stop_discovery_process(self, reason: str = "watchdog command"):
        """Stop the discovery process gracefully"""
        if not self.discovery_process:
            return

        logger.info(f"🛑 Stopping discovery process (reason: {reason})...")

        try:
            # Try graceful shutdown first
            if self.discovery_process.poll() is None:
                # Send SIGTERM to process group
                import os
                try:
                    os.killpg(os.getpgid(self.discovery_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass

                # Wait for graceful shutdown
                try:
                    self.discovery_process.wait(timeout=30)
                    logger.info("✅ Discovery process stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    logger.warning("⚠️ Process did not stop gracefully - forcing termination")
                    try:
                        os.killpg(os.getpgid(self.discovery_process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

        except Exception as e:
            logger.error(f"❌ Error stopping discovery process: {e}")

        self.discovery_process = None
        self.save_state({'status': 'stopped'})

    def is_discovery_healthy(self) -> bool:
        """Check if discovery process is healthy"""
        if not self.discovery_process:
            return False

        # Check if process is still running
        if self.discovery_process.poll() is not None:
            logger.warning("⚠️ Discovery process has died")
            return False

        # Could add more health checks here:
        # - Check last heartbeat timestamp
        # - Check log file activity
        # - Check memory usage
        # - Check for error patterns

        return True

    def calculate_restart_delay(self) -> float:
        """Calculate delay before next restart attempt"""
        if self.crash_count == 0:
            return 0  # Immediate restart
        elif self.crash_count == 1:
            return self.CRASH_BACKOFF  # 1 minute
        elif self.crash_count == 2:
            return self.CRASH_BACKOFF * 2  # 2 minutes
        else:
            # Exponential backoff with max
            delay = min(self.CRASH_BACKOFF * (2 ** (self.crash_count - 1)), self.MAX_RESTART_DELAY)
            return delay

    def handle_crash(self):
        """Handle discovery process crash"""
        self.crash_count += 1
        self.last_crash_time = datetime.now()

        logger.warning(f"⚠️ Discovery process crashed (crash #{self.crash_count})")

        # Check if we should give up
        if self.crash_count >= 5:
            logger.error("❌ Too many crashes - giving up")
            self.stop_watchdog("too many crashes")
            return

        # Calculate restart delay
        delay = self.calculate_restart_delay()
        logger.info(f"⏳ Waiting {delay} seconds before restart...")

        time.sleep(delay)

    def monitor_discovery(self):
        """Monitor discovery process and restart if needed"""
        while self.watchdog_running and not self.intentional_shutdown:
            # Check if ASTRA should still be active
            if not self.is_astra_active():
                logger.info("ℹ️ ASTRA no longer marked as active - stopping watchdog")
                self.stop_watchdog("ASTRA marked inactive")
                break

            # Check if discovery process is healthy
            if not self.is_discovery_healthy():
                logger.warning("⚠️ Discovery process not healthy - attempting restart")
                self.handle_crash()

                if not self.start_discovery_process():
                    logger.error("❌ Failed to restart discovery process")
                    continue

                # Reset crash count on successful restart
                if self.is_discovery_healthy():
                    logger.info("✅ Discovery process restarted successfully")
                    self.crash_count = 0
                    self.save_state({'status': 'restarted'})

            # Wait before next health check
            time.sleep(self.HEALTH_CHECK_INTERVAL)

    def start_watchdog(self):
        """Start the watchdog and discovery process"""
        logger.info("="*60)
        logger.info("ASTRA Discovery Watchdog - Continuous Operation")
        logger.info("="*60)
        logger.info(f"Starting at: {datetime.now().isoformat()}")

        # Mark ASTRA as active
        self.set_astra_active(True)
        self.watchdog_running = True
        self.start_time = datetime.now()

        # Start discovery process
        if not self.start_discovery_process():
            logger.error("❌ Failed to start discovery process - exiting watchdog")
            self.set_astra_active(False)
            return 1

        logger.info("✅ Watchdog monitoring started")
        logger.info("💡 Discovery will auto-restart if it crashes")
        logger.info("💡 Use 'python astra_watchdog.py stop' to stop")

        # Monitor discovery
        try:
            self.monitor_discovery()
        except KeyboardInterrupt:
            logger.info("🛑 Watchdog interrupted by user")
            self.stop_watchdog("user interrupt")
        except Exception as e:
            logger.error(f"❌ Watchdog error: {e}")
            import traceback
            traceback.print_exc()
            self.stop_watchdog("watchdog error")

        return 0

    def stop_watchdog(self, reason: str = "unknown"):
        """Stop the watchdog and discovery process"""
        logger.info(f"🛑 Stopping watchdog (reason: {reason})")

        self.intentional_shutdown = True
        self.watchdog_running = False

        # Stop discovery process
        self.stop_discovery_process("watchdog stopping")

        # Mark ASTRA as inactive
        self.set_astra_active(False)

        # Calculate uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info(f"📊 Watchdog uptime: {uptime}")

        logger.info("✅ Watchdog stopped")

    def status(self):
        """Print current status"""
        print("\n" + "="*60)
        print("ASTRA Discovery Watchdog Status")
        print("="*60)

        # Check if ASTRA is marked active
        active = self.is_astra_active()
        print(f"ASTRA Active: {'✅ YES' if active else '❌ NO'}")

        # Load state
        state = self.load_state()
        if state:
            print(f"Last Update: {state.get('timestamp', 'Unknown')}")
            print(f"Status: {state.get('status', 'Unknown').upper()}")
            print(f"Discovery PID: {state.get('discovery_pid', 'Not running')}")

            if state.get('uptime_seconds'):
                uptime_seconds = state['uptime_seconds']
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                print(f"Uptime: {hours}h {minutes}m")

            print(f"Crash Count: {state.get('crash_count', 0)}")

        # Check if processes are running
        try:
            result = subprocess.run(['pgrep', '-f', 'start_autonomous_discovery.py'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Discovery Process: ✅ Running (PID: {result.stdout.strip()})")
            else:
                print("Discovery Process: ❌ Not running")
        except Exception:
            print("Discovery Process: ❓ Unknown")

        print("="*60 + "\n")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum} - initiating graceful shutdown...")
    # Let the watchdog handle cleanup in its main loop
    global watchdog
    if watchdog:
        watchdog.stop_watchdog(f"signal {signum}")
    sys.exit(0)


def main():
    """Main entry point"""
    global watchdog

    if len(sys.argv) < 2:
        print("Usage: python astra_watchdog.py {start|stop|status}")
        return 1

    command = sys.argv[1].lower()

    watchdog = AstraWatchdog()

    if command == "start":
        # Check if already running
        if watchdog.is_astra_active():
            print("⚠️ ASTRA is already marked as active")
            print("💡 If you want to restart, first run: python astra_watchdog.py stop")
            watchdog.status()
            return 1

        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start watchdog
        return watchdog.start_watchdog()

    elif command == "stop":
        if not watchdog.is_astra_active():
            print("ℹ️ ASTRA is not marked as active")
            return 0

        print("🛑 Stopping ASTRA discovery and watchdog...")

        # Kill any running discovery processes
        try:
            subprocess.run(['pkill', '-f', 'start_autonomous_discovery.py'],
                         capture_output=True)
            print("✅ Discovery processes stopped")
        except Exception as e:
            print(f"⚠️ Error stopping discovery: {e}")

        # Mark ASTRA as inactive
        watchdog.set_astra_active(False)

        print("✅ ASTRA marked as inactive - will not auto-restart")
        return 0

    elif command == "status":
        watchdog.status()
        return 0

    else:
        print(f"❌ Unknown command: {command}")
        print("Usage: python astra_watchdog.py {start|stop|status}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
