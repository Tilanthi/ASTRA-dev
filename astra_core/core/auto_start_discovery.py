"""
ASTRA Auto-Start Discovery System

This module provides automatic discovery startup when ASTRA is active.
The discovery pipeline runs continuously in the background and pauses during
user queries, providing a truly autonomous research experience.

Key Features:
- Auto-starts discovery when ASTRA is initialized
- Pauses discovery during user queries
- Resumes automatically after queries complete
- Runs in background with minimal overhead
- Provides status and control methods

Version: 1.0.0
Date: 2026-07-03
"""

import asyncio
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import sys

logger = logging.getLogger(__name__)


class AutoStartDiscoveryManager:
    """
    Manages auto-starting discovery system that runs continuously
    except when processing user queries.
    """

    def __init__(self):
        self.discovery_process: Optional[Any] = None
        self.discovery_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.pause_lock = threading.Lock()
        self.start_time: Optional[datetime] = None
        self.total_queries_processed = 0
        self.total_discovery_cycles = 0

        # Import discovery system lazily
        self._discovery_system = None
        self._startup_module = None

    def _import_discovery_components(self):
        """Lazily import discovery components to avoid circular dependencies"""
        if self._startup_module is None:
            try:
                # Import the startup module which contains the discovery runner
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from start_autonomous_discovery import AutonomousDiscoveryRunner
                self._startup_module = AutonomousDiscoveryRunner
                logger.info("✅ Discovery components loaded successfully")
                return True
            except ImportError as e:
                logger.error(f"❌ Failed to import discovery components: {e}")
                return False
        return True

    def start_discovery_background(self):
        """Start discovery in background thread"""
        if not self._import_discovery_components():
            logger.error("Cannot start discovery - components unavailable")
            return False

        if self.discovery_thread is not None and self.discovery_thread.is_alive():
            logger.info("Discovery already running")
            return True

        logger.info("🚀 Starting background discovery process...")
        self.is_running = True
        self.should_stop = False
        self.is_paused = False
        self.start_time = datetime.now()

        # Create and start discovery thread
        self.discovery_process = self._startup_module()
        self.discovery_thread = threading.Thread(
            target=self._run_discovery_loop,
            daemon=True,
            name="ASTRA-Discovery"
        )
        self.discovery_thread.start()

        logger.info("✅ Background discovery started successfully")
        return True

    def _run_discovery_loop(self):
        """Main discovery loop running in background thread"""
        try:
            # Initialize discovery system
            if not self.discovery_process.check_dependencies():
                logger.error("❌ Discovery dependencies check failed")
                return

            if not self.discovery_process.initialize_system():
                logger.error("❌ Discovery system initialization failed")
                return

            logger.info("🔄 Discovery loop started")

            # Run discovery cycles until stopped
            while not self.should_stop:
                # Check if paused for user query
                with self.pause_lock:
                    if self.is_paused:
                        logger.debug("Discovery paused for user query")
                        time.sleep(0.5)  # Wait 500ms before checking again
                        continue

                # Run a single discovery cycle
                try:
                    if self.discovery_process.discovery_system:
                        # Run one discovery cycle
                        self._run_single_discovery_cycle()
                        self.total_discovery_cycles += 1

                        # Short pause between cycles
                        time.sleep(1)  # 1 second between cycles

                except Exception as e:
                    logger.error(f"Error in discovery cycle: {e}")
                    time.sleep(5)  # Wait 5 seconds before retry

            logger.info("🛑 Discovery loop stopped")

        except Exception as e:
            logger.error(f"❌ Fatal error in discovery loop: {e}")
            import traceback
            traceback.print_exc()

    def _run_single_discovery_cycle(self):
        """Run a single discovery cycle"""
        try:
            # Call the discovery system's cycle method
            discovery_sys = self.discovery_process.discovery_system
            if hasattr(discovery_sys, 'run_discovery_cycle'):
                discovery_sys.run_discovery_cycle()
            else:
                logger.warning("Discovery system doesn't have run_discovery_cycle method")
        except Exception as e:
            logger.error(f"Error running discovery cycle: {e}")

    def pause_for_query(self):
        """Pause discovery for user query processing"""
        with self.pause_lock:
            self.is_paused = True
            self.total_queries_processed += 1
        logger.debug(f"🔔 Discovery paused for query #{self.total_queries_processed}")

    def resume_after_query(self):
        """Resume discovery after query processing"""
        with self.pause_lock:
            self.is_paused = False
        logger.debug("▶️ Discovery resumed after query")

    def stop_discovery(self):
        """Stop discovery gracefully"""
        logger.info("🛑 Stopping background discovery...")

        self.should_stop = True
        self.is_running = False

        # Wait for thread to finish (max 10 seconds)
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=10.0)

        if self.discovery_process:
            self.discovery_process.stop_discovery()

        logger.info("✅ Background discovery stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current discovery status"""
        uptime = None
        if self.start_time:
            uptime = datetime.now() - self.start_time

        discovery_rate = 0.0
        if self.total_discovery_cycles > 0 and uptime:
            hours = uptime.total_seconds() / 3600
            if hours > 0:
                discovery_rate = self.total_discovery_cycles / hours

        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'uptime_seconds': uptime.total_seconds() if uptime else 0,
            'total_cycles': self.total_discovery_cycles,
            'total_queries_processed': self.total_queries_processed,
            'discovery_rate_per_hour': discovery_rate,
            'thread_alive': self.discovery_thread.is_alive() if self.discovery_thread else False
        }


# Global singleton instance
_auto_start_manager: Optional[AutoStartDiscoveryManager] = None


def get_auto_start_manager() -> AutoStartDiscoveryManager:
    """Get the global auto-start manager instance"""
    global _auto_start_manager
    if _auto_start_manager is None:
        _auto_start_manager = AutoStartDiscoveryManager()
    return _auto_start_manager


def auto_start_discovery():
    """Auto-start discovery system (call during ASTRA initialization)"""
    manager = get_auto_start_manager()
    return manager.start_discovery_background()


def auto_pause_discovery():
    """Auto-pause discovery for user query"""
    manager = get_auto_start_manager()
    manager.pause_for_query()


def auto_resume_discovery():
    """Auto-resume discovery after query"""
    manager = get_auto_start_manager()
    manager.resume_after_query()


def auto_stop_discovery():
    """Auto-stop discovery system"""
    manager = get_auto_start_manager()
    manager.stop_discovery()


def get_auto_start_status() -> Dict[str, Any]:
    """Get auto-start discovery status"""
    manager = get_auto_start_manager()
    return manager.get_status()