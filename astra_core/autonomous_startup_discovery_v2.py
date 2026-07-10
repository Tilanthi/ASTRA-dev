#!/usr/bin/env python3
"""
FIXED VERSION - ASTRA Discovery System with Permanent Blocking Fix

This version addresses the critical blocking issue that prevented discovery cycles from completing.
Key fixes:
1. Removed all pause/resume complexity that could cause deadlocks
2. Eliminated heartbeat checking that could block execution
3. Simplified discovery loop to basic synchronous execution
4. Added timeout protection to all blocking operations
5. Removed async/await complexity that was causing event loop issues
"""

import time
import threading
import random
import logging
from astra_core.core.thread_safe_timeout import call_with_timeout
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Setup logging
logger = logging.getLogger(__name__)

class DiscoveryConfig:
    """Simple discovery configuration"""
    def __init__(self):
        self.discovery_interval_seconds = 60
        self.startup_delay_seconds = 2
        self.discoverystore_path = Path.home() / ".astra_persistent" / "genuine_discoveries.json"
        self.max_discoveries_per_cycle = 1

class FixedGenuineDiscoverySystem:
    """
    FIXED VERSION - ASTRA Discovery System

    This version eliminates all blocking operations and implements
    robust timeout protection to prevent the critical blocking issue.
    """

    def __init__(self, config: Optional[DiscoveryConfig] = None):
        logger.info("[GenuineDiscovery] ========== INITIALIZING FIXED VERSION ==========")

        self.config = config or DiscoveryConfig()
        self.discoverystore_path = self.config.discoverystore_path

        # Basic system state - NO complex pause/resume mechanisms
        self.is_running = False
        self.discovery_thread = None
        self.stop_event = threading.Event()

        # Discovery tracking
        self.discovery_cycle = 0
        self.genuine_discoveries = []
        self.failed_attempts = []

        # ASTRA integration (will be set externally)
        self.astra_system = None

        # Statistics
        self.start_time = None
        self.last_activity_time = None

        logger.info("[GenuineDiscovery] ========== FIXED VERSION INITIALIZED ==========")

    def initialize_with_astra(self, astra_system):
        """Connect to ASTRA system"""
        logger.info("[GenuineDiscovery] Connecting to ASTRA system...")
        self.astra_system = astra_system
        logger.info("[GenuineDiscovery] ✓ ASTRA system connected")

    def start(self):
        """Start discovery system - FIXED VERSION with no blocking"""
        if self.is_running:
            logger.warning("[GenuineDiscovery] Already running")
            return

        logger.info("[GenuineDiscovery] ========== STARTING FIXED DISCOVERY SYSTEM ==========")

        self.is_running = True
        self.stop_event.clear()
        self.start_time = datetime.now()
        self.last_activity_time = time.time()

        # CRITICAL: Initialize with real ASTRA system - NO MOCK DATA ALLOWED
        logger.info("[GenuineDiscovery] ========== INITIALIZING REAL ASTRA SYSTEM ==========")
        try:
            from astra_core import create_stan_system
            self.astra_system = create_stan_system()
            logger.info("[GenuineDiscovery] ✓ REAL ASTRA SYSTEM CONNECTED")
            logger.info("[GenuineDiscovery] ✓ Using EnhancedUnifiedSTANSystem - GENUINE DISCOVERIES ONLY")
        except Exception as e:
            logger.error(f"[GenuineDiscovery] ❌ FAILED TO INITIALIZE REAL ASTRA SYSTEM: {e}")
            logger.error("[GenuineDiscovery] ❌ CANNOT PROCEED WITHOUT REAL ASTRA - STOPPING SYSTEM")
            raise RuntimeError("REAL ASTRA SYSTEM REQUIRED - NO MOCK DATA ALLOWED")

        # Start discovery thread
        self.discovery_thread = threading.Thread(
            target=self._robust_discovery_loop,
            name="FixedGenuineDiscovery",
            daemon=True
        )
        self.discovery_thread.start()

        logger.info("[GenuineDiscovery] ✓ FIXED discovery system started")
        logger.info("[GenuineDiscovery] ========== BEGINNING GENUINE DISCOVERY CYCLES ==========")

    def stop(self):
        """Stop discovery system"""
        if not self.is_running:
            return

        logger.info("[GenuineDiscovery] ========== STOPPING DISCOVERY SYSTEM ==========")

        self.is_running = False
        self.stop_event.set()

        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=5.0)

        self._save_discovery_store()

        logger.info("[GenuineDiscovery] ✓ FIXED discovery system stopped")

    def _robust_discovery_loop(self):
        """
        FIXED VERSION - Robust discovery loop with no blocking operations

        Key improvements:
        1. No pause/resume complexity
        2. No heartbeat checking that could block
        3. Simple timeout-protected execution
        4. Immediate error recovery
        """
        logger.info("[GenuineDiscovery] ========== ROBUST DISCOVERY LOOP STARTED ==========")

        # Small initial delay
        time.sleep(self.config.startup_delay_seconds)

        while not self.stop_event.is_set():
            try:
                cycle_start_time = time.time()
                self.discovery_cycle += 1

                logger.info(f"[GenuineDiscovery] ")
                logger.info(f"[GenuineDiscovery] ========== DISCOVERY CYCLE {self.discovery_cycle} ==========")

                # Update activity time
                self.last_activity_time = time.time()

                # Execute discovery cycle with timeout protection
                try:
                    discoveries = self._execute_timeout_protected_cycle()

                    cycle_time = time.time() - cycle_start_time
                    logger.info(f"[GenuineDiscovery] ========== CYCLE {self.discovery_cycle} COMPLETE ==========")
                    logger.info(f"[GenuineDiscovery] Cycle time: {cycle_time:.1f}s | Discoveries: {len(discoveries)}")

                    # Process discoveries
                    for discovery in discoveries:
                        self.genuine_discoveries.append(discovery)
                        logger.info(f"[GenuineDiscovery] ✓ DISCOVERY SAVED: {discovery.title[:60]}")

                    # Save discoveries
                    self._save_discovery_store()

                except TimeoutError:
                    logger.error(f"[GenuineDiscovery] ⏰ Cycle {self.discovery_cycle} timed out - skipping")
                    self.failed_attempts.append({
                        'cycle': self.discovery_cycle,
                        'error': 'Timeout',
                        'timestamp': datetime.now().isoformat()
                    })

                except Exception as e:
                    logger.error(f"[GenuineDiscovery] ❌ Cycle {self.discovery_cycle} failed: {e}")
                    import traceback
                    traceback.print_exc()
                    self.failed_attempts.append({
                        'cycle': self.discovery_cycle,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })

                # Wait between cycles with interrupt checking
                logger.info(f"[GenuineDiscovery] Waiting 60s before next cycle...")

                # Simple non-blocking wait
                for _ in range(12):  # 12 × 5s = 60s
                    if self.stop_event.is_set():
                        logger.info("[GenuineDiscovery] Stop requested, exiting loop")
                        break
                    time.sleep(5)

                if self.stop_event.is_set():
                    break

            except Exception as e:
                logger.error(f"[GenuineDiscovery] 🔥 CRITICAL LOOP ERROR: {e}")
                import traceback
                traceback.print_exc()
                # Continue despite error
                time.sleep(10)

        logger.info(f"[GenuineDiscovery] ========== ROBUST LOOP ENDED ==========")
        logger.info(f"[GenuineDiscovery] Total cycles: {self.discovery_cycle}")
        logger.info(f"[GenuineDiscovery] Total discoveries: {len(self.genuine_discoveries)}")
        logger.info(f"[GenuineDiscovery] Discovery rate: {len(self.genuine_discoveries)/max(1, self.discovery_cycle):.2%}")

    def _execute_timeout_protected_cycle(self) -> List:
        """
        Execute discovery cycle with comprehensive timeout protection

        This is the core fix that prevents blocking:
        1. Signal-based timeout for ASTRA calls
        2. No async/await complexity
        3. Simple error handling
        4. Immediate fallback on failure
        """
        discoveries = []
        max_attempts = 2  # Conservative limit

        logger.info(f"[GenuineDiscovery] Executing timeout-protected cycle (max {max_attempts} attempts)")

        for attempt in range(max_attempts):
            if self.stop_event.is_set():
                logger.info("[GenuineDiscovery] Stop detected during cycle")
                break

            logger.info(f"[GenuineDiscovery] Attempt {attempt + 1}/{max_attempts}")

            try:
                # Simple discovery type selection
                discovery_type = self._get_random_discovery_type()

                # Simple query generation
                discovery_query = self._generate_simple_query()
                logger.info(f"[GenuineDiscovery] Query: {discovery_query[:80]}...")

                # Process with timeout protection
                # CRITICAL: REAL ASTRA SYSTEM IS REQUIRED - NO MOCK DATA ALLOWED
                if not self.astra_system:
                    logger.error("[GenuineDiscovery] ❌ NO ASTRA SYSTEM AVAILABLE")
                    logger.error("[GenuineDiscovery] ❌ CANNOT CREATE DISCOVERIES WITHOUT REAL ASTRA")
                    raise RuntimeError("REAL ASTRA SYSTEM REQUIRED - NO MOCK DATA ALLOWED")

                discovery = self._call_astra_with_timeout(discovery_query)
                if discovery:
                    discoveries.append(discovery)
                    logger.info(f"[GenuineDiscovery] ✓ GENUINE DISCOVERY CREATED")

                    # Success - exit early
                    if len(discoveries) >= 1:
                        break

            except TimeoutError:
                logger.warning(f"[GenuineDiscovery] Attempt {attempt + 1} timed out")
                continue
            except Exception as e:
                logger.error(f"[GenuineDiscovery] Attempt {attempt + 1} failed: {e}")
                continue

        logger.info(f"[GenuineDiscovery] Cycle execution complete: {len(discoveries)} discoveries")
        return discoveries

    def _call_astra_with_timeout(self, query: str):
        """
        Call ASTRA system with thread-safe timeout protection

        This replaces the signal-based timeout (which only works in main thread)
        with a thread-safe implementation using concurrent.futures.
        """
        try:
            # Use thread-safe timeout (20 seconds)
            result = call_with_timeout(
                self.astra_system.answer,
                20,
                query
            )

            if result and 'answer' in result:
                return self._create_discovery_from_result(result['answer'])
            else:
                logger.warning("[GenuineDiscovery] No valid ASTRA result")
                return None

        except TimeoutError:
            logger.error("[GenuineDiscovery] ⏰ ASTRA call timed out after 20s")
            return None
        except Exception as e:
            logger.error(f"[GenuineDiscovery] ASTRA call failed: {e}")
            return None

    def _create_discovery_from_result(self, answer_text: str):
        """Create discovery from ASTRA answer"""
        # Extract title
        lines = answer_text.split('\n')
        title = "Astronomical Discovery"
        for line in lines:
            line = line.strip()
            if line and len(line) < 100 and not line.startswith('#'):
                title = line
                break

        # Create discovery
        return {
            'title': title,
            'abstract': answer_text[:300] + "..." if len(answer_text) > 300 else answer_text,
            'discovery_type': 'theoretical_synthesis',
            'timestamp': datetime.now().isoformat()
        }

    # REMOVED: _create_mock_discovery() - MOCK DATA IS NEVER ALLOWED
    # REAL ASTRA SYSTEM IS REQUIRED FOR ALL DISCOVERIES

    def _get_random_discovery_type(self) -> str:
        """Get random discovery type"""
        types = ["pattern", "theoretical", "gap_analysis", "predictive", "computational"]
        return random.choice(types)

    def _generate_simple_query(self) -> str:
        """Generate simple discovery query"""
        domains = ["stellar", "galactic", "cosmological", "interstellar", "high_energy"]
        focuses = ["formation", "evolution", "structure", "dynamics", "chemistry"]

        domain = random.choice(domains)
        focus = random.choice(focuses)

        queries = [
            f"Analyze {domain} {focus} in nearby galaxies",
            f"Investigate {focus} mechanisms in {domain} environments",
            f"Characterize {domain} {focus} across cosmic time"
        ]

        return random.choice(queries)

    def _save_discovery_store(self):
        """Save discoveries to persistent storage"""
        try:
            self.discoverystore_path.parent.mkdir(parents=True, exist_ok=True)

            import json
            store_data = {
                'discoveries': self.genuine_discoveries,
                'failed_attempts': self.failed_attempts,
                'statistics': {
                    'total_cycles': self.discovery_cycle,
                    'total_discoveries': len(self.genuine_discoveries),
                    'discovery_rate': len(self.genuine_discoveries) / max(1, self.discovery_cycle),
                    'last_updated': datetime.now().isoformat()
                }
            }

            with open(self.discoverystore_path, 'w') as f:
                json.dump(store_data, f, indent=2)

            logger.info(f"[GenuineDiscovery] ✓ Saved {len(self.genuine_discoveries)} discoveries to storage")

        except Exception as e:
            logger.error(f"[GenuineDiscovery] Failed to save discoveries: {e}")

    def get_discovery_status(self) -> Dict[str, Any]:
        """Get current discovery status"""
        discovery_rate = 0.0
        if self.discovery_cycle > 0:
            discovery_rate = len(self.genuine_discoveries) / self.discovery_cycle

        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'is_running': self.is_running,
            'discovery_cycle': self.discovery_cycle,
            'genuine_discoveries': len(self.genuine_discoveries),
            'discovery_rate': discovery_rate,
            'failed_attempts': len(self.failed_attempts),
            'uptime_seconds': uptime,
            'last_activity': self.last_activity_time,
            'system_type': 'FIXED_VERSION'
        }

    def run_discovery_cycle(self, timeout=300):
        """Compatibility method for auto-start system - FIXED VERSION"""
        logger.info("[GenuineDiscovery] Auto-start compatibility: run_discovery_cycle called")

        try:
            # Run a simple discovery cycle with timeout
            discoveries = self._execute_timeout_protected_cycle()

            result = {
                'timestamp': datetime.now().isoformat(),
                'cycle': self.discovery_cycle,
                'discoveries': len(discoveries),
                'status': 'complete',
                'discoveries_data': discoveries
            }

            logger.info(f"[GenuineDiscovery] Auto-start cycle complete: {len(discoveries)} discoveries")
            return result

        except Exception as e:
            logger.error(f"[GenuineDiscovery] Auto-start cycle failed: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'cycle': self.discovery_cycle,
                'discoveries': 0,
                'status': 'failed',
                'error': str(e)
            }

# Factory function for compatibility
def create_fixed_discovery_system(config=None) -> FixedGenuineDiscoverySystem:
    """Create FIXED VERSION discovery system"""
    return FixedGenuineDiscoverySystem(config)

if __name__ == "__main__":
    print("=" * 60)
    print("ASTRA FIXED DISCOVERY SYSTEM - TEST")
    print("=" * 60)
    print("Testing fixed discovery system...")

    system = create_fixed_discovery_system()
    system.start()

    # Let it run for a test
    time.sleep(120)

    status = system.get_discovery_status()
    print("\nTest Results:")
    print(f"  Status: {status}")
    print(f"  Discoveries: {status['genuine_discoveries']}")

    system.stop()
    print("\n✓ Fixed system test completed")
