"""
ASTRA Autonomous Startup Discovery - Automatic Discovery Launch
==================================================================

This module provides automatic discovery startup functionality for ASTRA.
Whenever ASTRA is initialized, this system automatically launches autonomous
discovery mode that runs continuously in the background.

KEY FEATURES:
- Automatic startup discovery when ASTRA initializes
- Continuous autonomous discovery operation
- Automatic pause/resume based on user activity
- Integration with all ASTRA capabilities
- Discovery state persistence across sessions

OPERATION MODES:
- CONTINUOUS: Discovery runs continuously, throttled during user activity
- IDLE: Discovery only runs during idle periods
- PAUSED: Discovery paused (user actively working)
- OFF: Discovery disabled

Version: 1.0.0
Date: 2026-06-27
"""

import asyncio
import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class StartupDiscoveryMode(Enum):
    """Modes for startup discovery operation"""
    CONTINUOUS = "continuous"  # Always running, throttled during user activity
    IDLE = "idle"  # Only runs during idle periods
    INTELLIGENT = "intelligent"  # Adapts based on task complexity
    OFF = "off"  # Discovery disabled


class DiscoveryState(Enum):
    """Current state of discovery process"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    THROTTLED = "throttled"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class StartupDiscoveryConfig:
    """Configuration for automatic startup discovery"""
    mode: StartupDiscoveryMode = StartupDiscoveryMode.INTELLIGENT

    # Timing configuration
    startup_delay_seconds: int = 5  # Delay before starting discovery
    idle_threshold_seconds: int = 300  # 5 minutes of no user activity
    discovery_interval_seconds: int = 1800  # 30 minutes between discovery cycles
    throttle_factor: float = 0.5  # Throttle to 50% during user activity

    # Discovery scope
    enable_literature_monitoring: bool = True
    enable_hypothesis_generation: bool = True
    enable_data_analysis: bool = True
    enable_theoretical_discovery: bool = True
    enable_causal_discovery: bool = True

    # Priority domains
    primary_domains: List[str] = field(default_factory=lambda: [
        "astrophysics", "astronomy", "cosmology",
        "star_formation", "ism", "exoplanets"
    ])

    # Output and reporting
    report_discoveries: bool = True
    discovery_log_path: Optional[str] = None
    max_discoveries_per_cycle: int = 10

    # Resource management
    max_cpu_usage: float = 0.7  # Max 70% CPU
    max_memory_gb: float = 8.0  # Max 8GB memory


class AutonomousStartupDiscovery:
    """
    Autonomous Startup Discovery System

    Automatically launches discovery mode when ASTRA starts and manages
    continuous autonomous discovery with intelligent pause/resume behavior.
    """

    def __init__(self, config: Optional[StartupDiscoveryConfig] = None):
        """
        Initialize autonomous startup discovery

        Args:
            config: Configuration for startup discovery
        """
        self.config = config or StartupDiscoveryConfig()

        # Discovery state
        self.state = DiscoveryState.STOPPED
        self.discovery_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        # Activity tracking
        self.last_user_activity = datetime.now()
        self.user_task_active = False
        self.activity_callbacks: List[Callable] = []

        # Discovery tracking
        self.discoveries_made: List[Dict] = []
        self.discovery_cycles_completed = 0
        self.current_discovery_task: Optional[str] = None

        # Integration with ASTRA components
        self.astra_system = None
        self.discovery_orchestrator = None
        self.autonomous_system = None

        # State persistence
        self.state_file = Path.home() / ".astra_persistent" / "startup_discovery_state.json"
        self._load_state()

        logger.info(f"[AutonomousStartupDiscovery] Initialized with mode: {self.config.mode}")

    def initialize_with_astra(self, astra_system, discovery_orchestrator=None, autonomous_system=None):
        """
        Initialize with ASTRA system components

        Args:
            astra_system: Main ASTRA system
            discovery_orchestrator: Discovery orchestrator component
            autonomous_system: Autonomous system component
        """
        self.astra_system = astra_system
        self.discovery_orchestrator = discovery_orchestrator
        self.autonomous_system = autonomous_system

        logger.info("[AutonomousStartupDiscovery] Connected to ASTRA system components")

    def start(self):
        """Start automatic discovery process"""
        if self.state != DiscoveryState.STOPPED:
            logger.warning(f"[AutonomousStartupDiscovery] Already running (state: {self.state})")
            return

        logger.info("[AutonomousStartupDiscovery] Starting automatic discovery...")
        self.state = DiscoveryState.STARTING

        # Create and start discovery thread
        self.stop_event.clear()
        self.pause_event.clear()
        self.discovery_thread = threading.Thread(
            target=self._discovery_loop,
            name="AutonomousStartupDiscovery",
            daemon=True
        )
        self.discovery_thread.start()

        logger.info("[AutonomousStartupDiscovery] Discovery thread started")

    def pause(self, reason: str = "user activity"):
        """
        Pause discovery process

        Args:
            reason: Reason for pausing
        """
        if self.state in [DiscoveryState.PAUSED, DiscoveryState.STOPPED]:
            return

        logger.info(f"[AutonomousStartupDiscovery] Pausing discovery: {reason}")
        self.state = DiscoveryState.PAUSED
        self.pause_event.set()

        # Notify activity callbacks
        for callback in self.activity_callbacks:
            try:
                callback("pause", {"reason": reason})
            except Exception as e:
                logger.error(f"Error in activity callback: {e}")

    def resume(self):
        """Resume discovery process"""
        if self.state != DiscoveryState.PAUSED:
            return

        logger.info("[AutonomousStartupDiscovery] Resuming discovery")
        self.state = DiscoveryState.RUNNING
        self.pause_event.clear()

        # Update activity timestamp
        self.last_user_activity = datetime.now()

        # Notify activity callbacks
        for callback in self.activity_callbacks:
            try:
                callback("resume", {})
            except Exception as e:
                logger.error(f"Error in activity callback: {e}")

    def stop(self):
        """Stop discovery process"""
        if self.state == DiscoveryState.STOPPED:
            return

        logger.info("[AutonomousStartupDiscovery] Stopping discovery...")
        self.state = DiscoveryState.STOPPING
        self.stop_event.set()

        # Wait for thread to finish (with timeout)
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=5.0)

        self.state = DiscoveryState.STOPPED
        self._save_state()
        logger.info("[AutonomousStartupDiscovery] Discovery stopped")

    def register_user_activity(self, activity_type: str = "task"):
        """
        Register user activity (call this when user gives tasks)

        Args:
            activity_type: Type of activity ("task", "query", "command")
        """
        self.last_user_activity = datetime.now()
        self.user_task_active = True

        # Determine if we should pause based on mode
        if self.config.mode == StartupDiscoveryMode.IDLE:
            self.pause(f"user {activity_type}")
        elif self.config.mode == StartupDiscoveryMode.INTELLIGENT:
            # Intelligent mode: throttle rather than pause
            if self.state == DiscoveryState.RUNNING:
                logger.info(f"[AutonomousStartupDiscovery] Throttling for user {activity_type}")
                self.state = DiscoveryState.THROTTLED

    def register_user_idle(self):
        """Register that user is idle (call when user task completes)"""
        self.user_task_active = False
        self.last_user_activity = datetime.now()

        # Resume if paused or throttled
        if self.state in [DiscoveryState.PAUSED, DiscoveryState.THROTTLED]:
            logger.info("[AutonomousStartupDiscovery] User idle - resuming discovery")
            self.resume()

    def add_activity_callback(self, callback: Callable):
        """
        Add callback for discovery state changes

        Args:
            callback: Function to call when discovery state changes
        """
        self.activity_callbacks.append(callback)

    def _discovery_loop(self):
        """Main discovery loop (runs in background thread)"""
        logger.info("[AutonomousStartupDiscovery] Discovery loop starting")

        # Initial startup delay
        time.sleep(self.config.startup_delay_seconds)

        self.state = DiscoveryState.RUNNING
        self.last_user_activity = datetime.now()

        while not self.stop_event.is_set():
            try:
                # Check if we should pause
                if self._should_pause():
                    self.pause("idle timeout")
                    self.stop_event.wait(self.config.idle_threshold_seconds)
                    if self.stop_event.is_set():
                        break
                    self.resume()
                    continue

                # Check if we're paused
                if self.pause_event.is_set():
                    self.stop_event.wait(1)  # Wait while paused
                    continue

                # Run discovery cycle
                self._run_discovery_cycle()

                # Wait for next cycle
                cycle_interval = self._calculate_cycle_interval()
                self.stop_event.wait(cycle_interval)

            except Exception as e:
                logger.error(f"[AutonomousStartupDiscovery] Error in discovery loop: {e}")
                time.sleep(60)  # Wait before retrying

        self.state = DiscoveryState.STOPPED
        logger.info("[AutonomousStartupDiscovery] Discovery loop ended")

    def _should_pause(self) -> bool:
        """Check if discovery should pause based on mode and activity"""
        if self.config.mode == StartupDiscoveryMode.CONTINUOUS:
            return False

        if self.config.mode == StartupDiscoveryMode.IDLE:
            idle_time = (datetime.now() - self.last_user_activity).total_seconds()
            return idle_time < self.config.idle_threshold_seconds

        if self.config.mode == StartupDiscoveryMode.INTELLIGENT:
            # Intelligent mode: only pause if complex user task
            idle_time = (datetime.now() - self.last_user_activity).total_seconds()
            return self.user_task_active and idle_time < 60  # Only pause if actively working

        return False

    def _calculate_cycle_interval(self) -> float:
        """Calculate interval until next discovery cycle"""
        base_interval = self.config.discovery_interval_seconds

        # Throttle during user activity in intelligent mode
        if self.state == DiscoveryState.THROTTLED:
            return base_interval / self.config.throttle_factor

        return base_interval

    def _run_discovery_cycle(self):
        """Run a single discovery cycle"""
        logger.info("[AutonomousStartupDiscovery] Starting discovery cycle...")
        self.discovery_cycles_completed += 1

        try:
            # Use ASTRA system if available
            if self.astra_system:
                self._run_discovery_with_astra()
            elif self.discovery_orchestrator:
                self._run_discovery_with_orchestrator()
            else:
                self._run_standalone_discovery()

            logger.info(f"[AutonomousStartupDiscovery] Discovery cycle {self.discovery_cycles_completed} completed")

        except Exception as e:
            logger.error(f"[AutonomousStartupDiscovery] Discovery cycle error: {e}")

    def _run_discovery_with_astra(self):
        """Run discovery using main ASTRA system"""
        if not self.astra_system:
            return

        # Generate discovery query
        discovery_query = self._generate_discovery_query()

        try:
            # Use ASTRA to process discovery
            result = self.astra_system.answer(discovery_query)

            # Extract and store discoveries
            if result and 'answer' in result:
                self._process_discovery_result(result['answer'])

        except Exception as e:
            logger.error(f"Error running discovery with ASTRA: {e}")

    def _run_discovery_with_orchestrator(self):
        """Run discovery using discovery orchestrator"""
        if not self.discovery_orchestrator:
            return

        try:
            # Run discovery cycle through orchestrator
            result = self.discovery_orchestrator.run_discovery_cycle(
                domains=self.config.primary_domains,
                max_discoveries=self.config.max_discoveries_per_cycle
            )

            # Process results
            if result:
                self._process_discovery_result(result)

        except Exception as e:
            logger.error(f"Error running discovery with orchestrator: {e}")

    def _run_standalone_discovery(self):
        """Run standalone discovery without ASTRA integration"""
        logger.info("[AutonomousStartupDiscovery] Running standalone discovery")

        # Generate simple discovery prompts
        discovery_prompts = [
            "Analyze recent astrophysical literature for novel connections",
            "Generate hypotheses about star formation efficiency",
            "Explore causal relationships in ISM physics",
            "Identify gaps in current exoplanet atmosphere models"
        ]

        for prompt in discovery_prompts[:self.config.max_discoveries_per_cycle]:
            discovery_entry = {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "status": "queued",
                "cycle": self.discovery_cycles_completed
            }
            self.discoveries_made.append(discovery_entry)

    def _generate_discovery_query(self) -> str:
        """Generate discovery query for ASTRA"""
        base_query = "Conduct autonomous scientific discovery in astrophysics focusing on "

        # Add primary domains
        domains_str = ", ".join(self.config.primary_domains[:3])
        query = f"{base_query} {domains_str}. "

        # Add specific instructions based on cycle number
        cycle_focus = [
            "Generate novel hypotheses about unexplained phenomena",
            "Identify causal relationships in observational data",
            "Discover connections between seemingly unrelated astrophysical processes",
            "Propose theoretical frameworks to resolve current contradictions"
        ]

        focus = cycle_focus[self.discovery_cycles_completed % len(cycle_focus)]
        query += focus

        return query

    def _process_discovery_result(self, result: Any):
        """Process and store discovery results"""
        discovery_entry = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.discovery_cycles_completed,
            "result": str(result)[:500],  # Truncate long results
            "status": "processed"
        }

        self.discoveries_made.append(discovery_entry)

        # Log discoveries if enabled
        if self.config.report_discoveries:
            logger.info(f"[AutonomousStartupDiscovery] Discovery made: {discovery_entry}")

        # Persist if we have too many discoveries
        if len(self.discoveries_made) > 100:
            self._save_state()

    def _load_state(self):
        """Load discovery state from disk"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    self.discoveries_made = state_data.get('discoveries', [])
                    self.discovery_cycles_completed = state_data.get('cycles_completed', 0)
                logger.info(f"[AutonomousStartupDiscovery] Loaded state: {len(self.discoveries_made)} discoveries")
        except Exception as e:
            logger.warning(f"Could not load discovery state: {e}")

    def _save_state(self):
        """Save discovery state to disk"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    'discoveries': self.discoveries_made[-100:],  # Keep last 100
                    'cycles_completed': self.discovery_cycles_completed
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save discovery state: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current discovery status"""
        return {
            "state": self.state.value,
            "mode": self.config.mode.value,
            "cycles_completed": self.discovery_cycles_completed,
            "discoveries_made": len(self.discoveries_made),
            "last_user_activity": self.last_user_activity.isoformat(),
            "user_task_active": self.user_task_active,
            "current_discovery_task": self.current_discovery_task
        }


# Global instance
_global_startup_discovery: Optional[AutonomousStartupDiscovery] = None


def get_autonomous_startup_discovery(
    config: Optional[StartupDiscoveryConfig] = None
) -> AutonomousStartupDiscovery:
    """
    Get or create global autonomous startup discovery instance

    Args:
        config: Configuration for startup discovery

    Returns:
        AutonomousStartupDiscovery instance
    """
    global _global_startup_discovery

    if _global_startup_discovery is None:
        _global_startup_discovery = AutonomousStartupDiscovery(config)
        logger.info("[AutonomousStartupDiscovery] Created global instance")

    return _global_startup_discovery


def initialize_autonomous_startup_discovery(
    astra_system=None,
    discovery_orchestrator=None,
    autonomous_system=None,
    config: Optional[StartupDiscoveryConfig] = None
) -> AutonomousStartupDiscovery:
    """
    Initialize and start autonomous startup discovery

    This is the main entry point for automatic discovery startup.
    Call this when ASTRA initializes to automatically start discovery.

    Args:
        astra_system: Main ASTRA system
        discovery_orchestrator: Discovery orchestrator component
        autonomous_system: Autonomous system component
        config: Configuration for startup discovery

    Returns:
        AutonomousStartupDiscovery instance
    """
    discovery = get_autonomous_startup_discovery(config)

    # Initialize with ASTRA components
    if astra_system or discovery_orchestrator or autonomous_system:
        discovery.initialize_with_astra(astra_system, discovery_orchestrator, autonomous_system)

    # Start automatic discovery
    discovery.start()

    logger.info("[AutonomousStartupDiscovery] Automatic discovery startup initialized")
    return discovery


def register_user_task_start():
    """Register that a user task has started (pauses intelligent discovery)"""
    discovery = get_autonomous_startup_discovery()
    if discovery:
        discovery.register_user_activity("task")


def register_user_task_complete():
    """Register that a user task has completed (resumes discovery)"""
    discovery = get_autonomous_startup_discovery()
    if discovery:
        discovery.register_user_idle()


def get_discovery_status() -> Dict[str, Any]:
    """Get current discovery status"""
    discovery = get_autonomous_startup_discovery()
    if discovery:
        return discovery.get_status()
    return {"state": "not_initialized"}