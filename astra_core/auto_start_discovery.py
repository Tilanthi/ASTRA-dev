"""
ASTRA Auto-Start Discovery System v4.0

Automatically starts continuous scientific discovery when ASTRA is initialized.
Runs continuously in background, intelligently pausing during user queries.

Key Features:
- Automatic startup on system initialization
- Continuous operation when ASTRA is idle
- Intelligent pause/resume for user requests
- Persistent operation across system restarts
- Zero configuration required
"""

import threading
import time
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state for auto-start discovery
_auto_start_discovery_thread: Optional[threading.Thread] = None
_auto_start_discovery_running = False
_auto_start_discovery_paused = False
_auto_start_discovery_lock = threading.Lock()
_auto_start_discovery_instance = None

# Statistics tracking
_discovery_stats = {
    'total_cycles': 0,
    'total_queries_processed': 0,
    'discovery_rate_per_hour': 0.0,
    'last_activity': None,
    'start_time': None,
    'pause_count': 0,
    'resume_count': 0
}


def auto_start_discovery() -> bool:
    """
    Initialize and start auto-discovery system.

    Returns:
        bool: True if successful, False otherwise
    """
    global _auto_start_discovery_instance, _auto_start_discovery_running

    try:
        logger.info("[Auto-Start] 🚀 Initializing ASTRA auto-start discovery system...")

        # Import the autonomous discovery system
        from astra_core.autonomous_startup_discovery_v2 import (
            initialize_genuine_discovery_with_astra,
            GenuineDiscoveryConfig
        )

        # Create configuration for continuous operation
        discovery_config = GenuineDiscoveryConfig(
            # Timing - CONTINUOUS DISCOVERY MODE
            startup_delay_seconds=3,  # Quick startup
            discovery_interval_seconds=60,  # 1 minute between cycles
            research_cycle_duration=60,  # 1 minute per discovery attempt

            # Enable all genuine discovery types
            enable_pattern_discovery=True,
            enable_theoretical_synthesis=True,
            enable_gap_identification=True,
            enable_predictive_hypothesis=True,
            enable_computational_reanalysis=True,

            # Optimized validation standards
            minimum_novelty_score=0.05,
            minimum_probability=0.3,
            require_testability=True,
            require_literature_consistency_check=False,

            # Research domains
            primary_domains=['astrophysics', 'astronomy', 'cosmology', 'star_formation', 'ism'],

            # Data sources
            enable_data_archive_analysis=True,
            enable_literature_mining=True,
            enable_observation_database_analysis=True,

            # Output
            max_discoveries_per_cycle=5
        )

        # Create a dummy ASTRA system reference (will be replaced during integration)
        class DummyASTRA:
            def get_discovery_status(self):
                return {'is_running': _auto_start_discovery_running}

        dummy_astra = DummyASTRA()

        # Initialize genuine discovery
        _auto_start_discovery_instance = initialize_genuine_discovery_with_astra(
            astra_system=dummy_astra,
            config=discovery_config
        )

        # Start the discovery system
        _auto_start_discovery_instance.start()
        _auto_start_discovery_running = True
        _discovery_stats['start_time'] = datetime.now()

        logger.info("[Auto-Start] ✅ Auto-start discovery system initialized successfully")
        logger.info("[Auto-Start] 💡 Discovery will run continuously in the background")
        logger.info("[Auto-Start] 💡 It will automatically pause during user queries")

        return True

    except Exception as e:
        logger.error(f"[Auto-Start] ❌ Failed to initialize auto-start discovery: {e}")
        return False


def pause_discovery_for_user_task() -> bool:
    """
    Pause discovery when a user task starts.

    Returns:
        bool: True if paused successfully, False otherwise
    """
    global _auto_start_discovery_paused

    with _auto_start_discovery_lock:
        if not _auto_start_discovery_running:
            return False  # Not running, nothing to pause

        if _auto_start_discovery_paused:
            return True  # Already paused

        _auto_start_discovery_paused = True
        _discovery_stats['pause_count'] += 1
        _discovery_stats['last_activity'] = datetime.now()

        logger.info("[Auto-Start] ⏸️ Discovery paused for user task")

        if _auto_start_discovery_instance and hasattr(_auto_start_discovery_instance, 'pause'):
            try:
                _auto_start_discovery_instance.pause()
                logger.info("[Auto-Start] ⏸️ Discovery instance paused successfully")
            except Exception as e:
                logger.warning(f"[Auto-Start] ⚠️ Could not pause discovery instance: {e}")

        return True


def resume_discovery_after_user_task() -> bool:
    """
    Resume discovery when a user task completes.

    Returns:
        bool: True if resumed successfully, False otherwise
    """
    global _auto_start_discovery_paused

    with _auto_start_discovery_lock:
        if not _auto_start_discovery_running:
            return False  # Not running, nothing to resume

        if not _auto_start_discovery_paused:
            return True  # Not paused, nothing to resume

        _auto_start_discovery_paused = False
        _discovery_stats['resume_count'] += 1
        _discovery_stats['last_activity'] = datetime.now()

        logger.info("[Auto-Start) 🔄 Discovery resumed after user task")

        if _auto_start_discovery_instance and hasattr(_auto_start_discovery_instance, 'resume'):
            try:
                _auto_start_discovery_instance.resume()
                logger.info("[Auto-Start] 🔄 Discovery instance resumed successfully")
            except Exception as e:
                logger.warning(f"[Auto-Start] ⚠️ Could not resume discovery instance: {e}")

        return True


def stop_auto_start_discovery() -> bool:
    """
    Stop the auto-start discovery system.

    Returns:
        bool: True if stopped successfully, False otherwise
    """
    global _auto_start_discovery_running, _auto_start_discovery_instance

    with _auto_start_discovery_lock:
        if not _auto_start_discovery_running:
            return True  # Not running, nothing to stop

        logger.info("[Auto-Start] 🛑 Stopping auto-start discovery system...")

        if _auto_start_discovery_instance and hasattr(_auto_start_discovery_instance, 'stop'):
            try:
                _auto_start_discovery_instance.stop()
                logger.info("[Auto-Start] 🛑 Discovery instance stopped successfully")
            except Exception as e:
                logger.warning(f"[Auto-Start] ⚠️ Could not stop discovery instance: {e}")

        _auto_start_discovery_running = False
        _auto_start_discovery_instance = None

        logger.info("[Auto-Start] ✅ Auto-start discovery system stopped")

        return True


def auto_pause_discovery() -> bool:
    """
    Alias for pause_discovery_for_user_task() for compatibility.

    Returns:
        bool: True if paused successfully, False otherwise
    """
    return pause_discovery_for_user_task()


def auto_resume_discovery() -> bool:
    """
    Alias for resume_discovery_after_user_task() for compatibility.

    Returns:
        bool: True if resumed successfully, False otherwise
    """
    return resume_discovery_after_user_task()


def get_auto_start_discovery_status() -> Dict[str, Any]:
    """
    Get the current status of auto-start discovery.

    Returns:
        Dict with status information
    """
    global _discovery_stats, _auto_start_discovery_running, _auto_start_discovery_paused

    # Calculate discovery rate
    if _discovery_stats['start_time']:
        elapsed_hours = (datetime.now() - _discovery_stats['start_time']).total_seconds() / 3600
        if elapsed_hours > 0:
            _discovery_stats['discovery_rate_per_hour'] = _discovery_stats['total_cycles'] / elapsed_hours

    status = {
        'is_running': _auto_start_discovery_running,
        'is_paused': _auto_start_discovery_paused,
        'total_cycles': _discovery_stats['total_cycles'],
        'total_queries_processed': _discovery_stats['total_queries_processed'],
        'discovery_rate_per_hour': _discovery_stats['discovery_rate_per_hour'],
        'pause_count': _discovery_stats['pause_count'],
        'resume_count': _discovery_stats['resume_count'],
        'last_activity': _discovery_stats['last_activity'].isoformat() if _discovery_stats['last_activity'] else None,
        'start_time': _discovery_stats['start_time'].isoformat() if _discovery_stats['start_time'] else None
    }

    # Add instance-specific status if available
    if _auto_start_discovery_instance and hasattr(_auto_start_discovery_instance, 'get_status'):
        try:
            instance_status = _auto_start_discovery_instance.get_status()
            status['instance_status'] = instance_status
        except Exception as e:
            logger.warning(f"[Auto-Start] ⚠️ Could not get instance status: {e}")

    return status


def increment_discovery_cycles():
    """Increment the discovery cycle counter (called by discovery system)"""
    global _discovery_stats
    _discovery_stats['total_cycles'] += 1


def increment_queries_processed():
    """Increment the queries processed counter (called during user requests)"""
    global _discovery_stats
    _discovery_stats['total_queries_processed'] += 1
    _discovery_stats['last_activity'] = datetime.now()