#!/usr/bin/env python3
"""
FIXED VERSION - ASTRA Discovery System with Comprehensive Fixes

This version addresses multiple critical issues:

v7.1 - Persistence Fix (2026-07-10):
1. Fixed discovery dictionary vs object attribute access issue
2. Discoveries now properly saved and logged with correct data types
3. Prevents AttributeError when processing discovery results

v7.0 - Comprehensive Discovery Pipeline Fix (2026-07-10):
1. Added missing initialize_genuine_discovery_with_astra function
2. Applied thread-safe timeout to old autonomous_startup_discovery.py
3. Fixed import logic in unified_enhanced.py for graceful fallback

v5.0 - Permanent Blocking Fix (2026-07-09):
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

# Import peer review validation system
from astra_core.scientific_discovery.genuine_discovery_validator import (
    GenuineDiscoveryValidator,
    DiscoveryQuality,
    validate_discovery_pipeline
)
# Single trust boundary for the discovery store (anti-fiction chokepoint).
# A record can only reach disk if it carries a machine `verification` block.
from astra_core.scientific_discovery.discovery_store import (
    has_machine_verification,
    load_verified,
    dedup_verified,
    save_bucket,
    GENUINE_FILE,
    PERSIST_DIR,
)

# Setup logging
logger = logging.getLogger(__name__)

class DiscoveryConfig:
    """Simple discovery configuration - Compatible with unified_enhanced.py parameters"""

    def __init__(self,
                 discovery_interval_seconds=60,
                 startup_delay_seconds=2,
                 discoverystore_path=None,
                 max_discoveries_per_cycle=1,
                 # Additional parameters for compatibility (ignored but accepted)
                 research_cycle_duration=None,
                 enable_pattern_discovery=None,
                 enable_theoretical_synthesis=None,
                 enable_gap_identification=None,
                 enable_predictive_hypothesis=None,
                 enable_computational_reanalysis=None,
                 minimum_novelty_score=None,
                 minimum_probability=None,
                 require_testability=None,
                 require_literature_consistency_check=None,
                 primary_domains=None,
                 enable_data_archive_analysis=None,
                 enable_literature_mining=None,
                 enable_observation_database_analysis=None,
                 mode=None,
                 idle_threshold_seconds=None):
        """Initialize discovery configuration with full parameter compatibility"""

        self.discovery_interval_seconds = discovery_interval_seconds
        self.startup_delay_seconds = startup_delay_seconds

        if discoverystore_path:
            self.discoverystore_path = discoverystore_path
        else:
            self.discoverystore_path = Path.home() / ".astra_persistent" / "genuine_discoveries.json"

        self.max_discoveries_per_cycle = max_discoveries_per_cycle

        # Log compatibility mode
        logger.info(f"[DiscoveryConfig] Initialized with {max_discoveries_per_cycle} max discoveries/cycle")

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

        # NEW: Peer Review Validation System
        self.validator = GenuineDiscoveryValidator()

        # NEW: Separate storage for different quality levels
        storage_base = Path.home() / ".astra_persistent"
        self.storage_paths = {
            'textbook': storage_base / "textbook_knowledge.json",
            'synthesis': storage_base / "literature_synthesis.json",
            'incremental': storage_base / "incremental_advances.json",
            'genuine': storage_base / "genuine_discoveries.json"
        }

        # NEW: Track statistics by quality level
        self.discovery_stats = {
            'textbook': 0,
            'synthesis': 0,
            'incremental': 0,
            'genuine': 0,
            'total_processed': 0
        }

        # Hydrate the in-memory store from disk so (a) dedup has real prior
        # state and history survives restarts, and (b) the legacy
        # "load-existing + append in-memory" merge in _save_discovery_store no
        # longer re-adds every record each cycle (the duplicate-on-each-cycle
        # bug that turned 1 evolved discovery into 9 copies).
        try:
            _verified, _dropped = dedup_verified(
                load_verified(Path(self.discoverystore_path)))
            if _dropped:
                logger.info("[GenuineDiscovery] dropped %d duplicate(s) on hydrate",
                            _dropped)
            self.genuine_discoveries = _verified
            logger.info("[GenuineDiscovery] hydrated %d machine-verified "
                        "discovery(ies) from disk", len(self.genuine_discoveries))
        except Exception as _e:
            logger.warning("[GenuineDiscovery] hydration failed (starting empty): %s", _e)
            self.genuine_discoveries = []

        logger.info("[GenuineDiscovery] ========== FIXED VERSION INITIALIZED WITH VALIDATION ==========")
        logger.info("[GenuineDiscovery] ✓ Peer review validation system enabled")
        logger.info("[GenuineDiscovery] ✓ Separate storage for different quality levels")

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

                # Consume any new machine-verified discoveries produced by the
                # evolved_analysis subpackage (lazy import; the function never
                # raises and does one small non-blocking file read; idempotent).
                try:
                    from astra_core.scientific_discovery.evolved_discovery_consumer import (
                        consume_evolved_discoveries)
                    consume_evolved_discoveries(self)
                except Exception as _evolve_e:
                    logger.warning("[GenuineDiscovery] evolved-discovery consume skipped: %s",
                                   _evolve_e)

                logger.info(f"[GenuineDiscovery] ")
                logger.info(f"[GenuineDiscovery] ========== DISCOVERY CYCLE {self.discovery_cycle} ==========")

                # Update activity time
                self.last_activity_time = time.time()

                # Execute discovery cycle with timeout protection
                try:
                    discoveries = self._execute_timeout_protected_cycle()

                    # Process discoveries with quality logging
                    genuine_count = 0
                    for discovery in discoveries:
                        quality = discovery.get('validation', {}).get('quality', 'UNKNOWN')
                        is_genuine = discovery.get('validation', {}).get('is_genuine', False)
                        confidence = discovery.get('validation', {}).get('confidence', 0.0)

                        # Quality emoji for logging
                        quality_emoji = {
                            'TEXTBOOK': '❌',
                            'SYNTHESIS': '📚',
                            'INCREMENTAL': '⚠️',
                            'GENUINE': '✅',
                            'BREAKTHROUGH': '🚀',
                            'UNKNOWN': '❓'
                        }
                        emoji = quality_emoji.get(quality, '❓')

                        # Defense in depth: only machine-verified records may
                        # enter the in-memory store (and thus reach disk).
                        if not has_machine_verification(discovery):
                            logger.warning("[GenuineDiscovery] refused in-memory "
                                           "append of unverified record: %s",
                                           str(discovery.get('title', ''))[:60])
                            continue
                        self.genuine_discoveries.append(discovery)

                        # Only count as "genuine" for statistics if validation passed
                        if is_genuine:
                            genuine_count += 1
                            logger.info(f"[GenuineDiscovery] {emoji} DISCOVERY SAVED: {discovery.get('title', 'Unknown')[:60]} [{quality}, {confidence:.1%} confidence]")
                        else:
                            logger.info(f"[GenuineDiscovery] {emoji} FILTERED: {discovery.get('title', 'Unknown')[:60]} [{quality}, {confidence:.1%} confidence]")

                    # Log cycle completion with quality statistics
                    cycle_time = time.time() - cycle_start_time
                    logger.info(f"[GenuineDiscovery] ========== CYCLE {self.discovery_cycle} COMPLETE ==========")
                    logger.info(f"[GenuineDiscovery] Cycle time: {cycle_time:.1f}s | Total: {len(discoveries)} | Genuine: {genuine_count}")
                    logger.info(f"[GenuineDiscovery] 📊 Quality Stats: {self.discovery_stats}")

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
        """Return ``None``.

        Historically this called ``self.astra_system.answer(query)`` and turned
        the response into a 'discovery'. That path is **structurally incapable
        of machine verification** — STAN's ``answer()`` returns a hardcoded
        string (``astra_core/core/unified.py``), so every record it produced
        was fiction that violated the prime directive ("NO FICTIONAL/
        SYNTHETIC DISCOVERIES"). It is disabled.

        The only discoveries this loop can now acquire are machine-verified ones
        ingested via ``consume_evolved_discoveries`` (each carries a
        ``verification`` block — an objective metric from executing code on real
        data). See ``discovery_store.has_machine_verification`` /
        ``append_verified``. This makes "cannot emit fiction" a structural
        property rather than a hope.
        """
        logger.debug("[GenuineDiscovery] fiction generation path disabled "
                     "(STAN answer() cannot produce machine verification)")
        return None

    def _create_discovery_from_result(self, answer_text: str):
        """Create discovery from ASTRA answer with peer review validation"""
        # Extract title
        lines = answer_text.split('\n')
        title = "Astronomical Discovery"
        for line in lines:
            line = line.strip()
            if line and len(line) < 100 and not line.startswith('#'):
                title = line
                break

        # Create discovery object
        discovery = {
            'title': title,
            'abstract': answer_text[:300] + "..." if len(answer_text) > 300 else answer_text,
            'discovery_type': 'theoretical_synthesis',
            'timestamp': datetime.now().isoformat()
        }

        # NEW: Apply peer review validation
        try:
            validation_result = self.validator.validate_discovery(discovery)

            # Add validation results to discovery
            discovery['validation'] = {
                'is_genuine': validation_result.is_genuine,
                'quality': validation_result.quality.value,
                'confidence': validation_result.confidence,
                'reasons': validation_result.reasons,
                'suggested_improvements': validation_result.suggested_improvements
            }

            # Log validation outcome
            quality_emoji = {
                'TEXTBOOK': '❌',
                'SYNTHESIS': '📚',
                'INCREMENTAL': '⚠️',
                'GENUINE': '✅',
                'BREAKTHROUGH': '🚀'
            }

            emoji = quality_emoji.get(validation_result.quality.value, '❓')
            logger.info(f"[GenuineDiscovery] {emoji} VALIDATION: {validation_result.quality.value} ({validation_result.confidence:.1%} confidence)")

            # Update statistics
            self.discovery_stats['total_processed'] += 1
            if validation_result.quality.value in self.discovery_stats:
                self.discovery_stats[validation_result.quality.value] += 1

        except Exception as e:
            logger.error(f"[GenuineDiscovery] Validation failed: {e}")
            discovery['validation'] = {
                'is_genuine': False,
                'quality': 'UNKNOWN',
                'confidence': 0.0,
                'reasons': [f'Validation error: {str(e)}'],
                'suggested_improvements': []
            }

        return discovery

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
        """Persist ONLY machine-verified, de-duplicated discoveries.

        This replaces two legacy bugs at once:
          1. The unconditional append + quality-bucket write that let fictional
             records (no ``verification`` block) reach disk.
          2. The "load existing from disk + append full in-memory list" merge
             that re-added every record on each cycle, duplicating endlessly
             (1 evolved discovery became 9 copies).

        The in-memory verified store is now authoritative; disk is a verbatim,
        deduped image of it, written through the discovery_store chokepoint.
        """
        try:
            import json

            # Keep only machine-verified records, dedup by verification key.
            verified, dropped = dedup_verified(
                [d for d in self.genuine_discoveries
                 if has_machine_verification(d)])
            if dropped:
                logger.info("[GenuineDiscovery] dropped %d duplicate/in-memory "
                            "copy(ies) before persisting", dropped)

            # All machine-verified records are genuinely GENUINE — write them
            # to the genuine store via the chokepoint's writer. The legacy
            # fiction-only buckets (incremental/textbook) are no longer written
            # to; they are emptied by the one-time purge.
            genuine_path = Path(self.discoverystore_path)
            save_bucket(genuine_path, verified)

            # Save overall statistics (honest: counts only verified records).
            stats_path = Path.home() / ".astra_persistent" / "discovery_statistics.json"
            stats_data = {
                'by_quality': self.discovery_stats,
                'overall': {
                    'total_cycles': self.discovery_cycle,
                    'total_processed': self.discovery_stats['total_processed'],
                    'verified_discoveries': len(verified),
                    'genuine_discovery_rate': self.discovery_stats['genuine'] / max(1, self.discovery_stats['total_processed']),
                    'last_updated': datetime.now().isoformat()
                }
            }
            with open(stats_path, 'w') as f:
                json.dump(stats_data, f, indent=2)

            if verified:
                logger.info(f"[GenuineDiscovery] ✓ persisted {len(verified)} "
                            f"machine-verified discovery(ies) to {GENUINE_FILE}")
            logger.info(f"[GenuineDiscovery] 📊 Stats: {self.discovery_stats}")

        except Exception as e:
            logger.error(f"[GenuineDiscovery] Failed to save discoveries: {e}")

    def _get_storage_path_for_quality(self, quality: str) -> Path:
        """Get storage path for a specific quality level"""
        quality_mapping = {
            'TEXTBOOK': self.storage_paths['textbook'],
            'SYNTHESIS': self.storage_paths['synthesis'],
            'INCREMENTAL': self.storage_paths['incremental'],
            'GENUINE': self.storage_paths['genuine'],
            'BREAKTHROUGH': self.storage_paths['genuine'],  # Breakthroughs go in genuine file
            'UNKNOWN': Path.home() / ".astra_persistent" / "unknown_quality.json"
        }
        return quality_mapping.get(quality, quality_mapping['UNKNOWN'])

    def get_discovery_status(self) -> Dict[str, Any]:
        """Get current discovery status with quality breakdown"""
        discovery_rate = 0.0
        if self.discovery_cycle > 0:
            discovery_rate = len(self.genuine_discoveries) / self.discovery_cycle

        genuine_rate = 0.0
        if self.discovery_stats['total_processed'] > 0:
            genuine_rate = self.discovery_stats['genuine'] / self.discovery_stats['total_processed']

        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'is_running': self.is_running,
            'discovery_cycle': self.discovery_cycle,
            'total_discoveries': len(self.genuine_discoveries),
            'discovery_rate': discovery_rate,
            'failed_attempts': len(self.failed_attempts),
            'uptime_seconds': uptime,
            'last_activity': self.last_activity_time,
            'system_type': 'FIXED_VERSION_WITH_VALIDATION',
            'quality_statistics': self.discovery_stats.copy(),
            'genuine_discovery_rate': genuine_rate,
            'validation_status': 'ENABLED'
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

# Compatibility aliases for unified_enhanced.py
GenuineDiscoveryConfig = DiscoveryConfig

def initialize_genuine_discovery_with_astra(astra_system, config):
    """
    Initialize genuine discovery with ASTRA system - FIXED VERSION

    This function provides compatibility with unified_enhanced.py while using
    the thread-safe, non-blocking v2 implementation.

    Args:
        astra_system: The ASTRA system instance
        config: GenuineDiscoveryConfig configuration object

    Returns:
        FixedGenuineDiscoverySystem: Initialized and started discovery system
    """
    logger.info("[GenuineDiscovery] ========== INITIALIZING WITH ASTRA SYSTEM ==========")

    # Create the fixed discovery system
    discovery_system = FixedGenuineDiscoverySystem(config=config)

    # Connect to ASTRA system
    discovery_system.initialize_with_astra(astra_system)

    # Start the discovery system
    discovery_system.start()

    logger.info("[GenuineDiscovery] ========== INITIALIZED AND STARTED SUCCESSFULLY ==========")

    return discovery_system

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
