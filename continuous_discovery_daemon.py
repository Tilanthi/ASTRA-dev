#!/usr/bin/env python3
"""
Continuous Discovery Daemon for ASTRA

This daemon runs continuous autonomous discovery cycles in the background,
syncs discoveries to GraphPalace, and evolves the codebase based on findings.
"""
import sys
import os
import time
import json
import logging
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add ASTRA to path
ASTRA_ROOT = Path(__file__).parent
sys.path.insert(0, str(ASTRA_ROOT / 'astra_live_backend'))

import requests
from graph_palace import get_graph_palace, PHEROMONE_NOVELTY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ASTRA_SERVER_URL = "http://localhost:8787"
DISCOVERY_INTERVAL = 300  # seconds (5 minutes)
SYNC_INTERVAL = 60  # seconds (1 minute)
EVOLUTION_INTERVAL = 3600  # seconds (1 hour)

# State file for tracking discoveries
STATE_FILE = ASTRA_ROOT / 'data' / 'daemon_state.json'


class ContinuousDiscoveryDaemon:
    """
    Daemon that continuously runs ASTRA discovery cycles and evolves the codebase.
    """

    def __init__(self):
        self.running = False
        self.discovery_thread: Optional[threading.Thread] = None
        self.sync_thread: Optional[threading.Thread] = None
        self.evolution_thread: Optional[threading.Thread] = None
        self.graph_palace = get_graph_palace(use_rust=False)
        self.state = self._load_state()

        logger.info("ContinuousDiscoveryDaemon initialized")

    def _load_state(self) -> Dict:
        """Load daemon state from disk."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

        return {
            'cycles_completed': 0,
            'discoveries_made': 0,
            'last_sync': None,
            'last_evolution': None,
            'code_updates': []
        }

    def _save_state(self):
        """Save daemon state to disk."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _trigger_discovery_cycle(self) -> Dict:
        """Trigger a discovery cycle on the ASTRA server."""
        try:
            response = requests.post(
                f"{ASTRA_SERVER_URL}/api/engine/cycle",
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Discovery cycle completed: {result.get('cycle_id', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Discovery cycle failed: {e}")
            return {}

    def _sync_to_graphpalace(self):
        """Sync recent discoveries to GraphPalace."""
        try:
            # Import sync function
            import sync_discoveries_to_graphpalace
            nodes, edges, pheromones = sync_discoveries_to_graphpalace.sync_discoveries()
            logger.info(f"Synced to GraphPalace: {nodes} nodes, {edges} edges, {pheromones} pheromones")
            self.state['last_sync'] = datetime.now().isoformat()
            self._save_state()
        except Exception as e:
            logger.error(f"GraphPalace sync failed: {e}")

    def _evolve_codebase(self) -> List[str]:
        """
        Analyze discoveries and evolve the codebase.

        Returns list of changes made.
        """
        changes = []

        try:
            # Get recent high-impact discoveries
            status = self.graph_palace.get_status()
            novelty_deposits = status.get('deposits_by_type', {}).get('novelty', 0)

            if novelty_deposits > 10:
                logger.info(f"Found {novelty_deposits} novelty deposits - analyzing for evolution opportunities")

                # Get high-novelty discoveries
            high_novelty_nodes = self.graph_palace.semantic_search(
                {'domain': 'Astrophysics'},
                top_k=5,
                min_score=0.3
            )

            for node, score in high_novelty_nodes:
                if node.node_type == 'discovery':
                    discovery_data = node.metadata
                    p_value = discovery_data.get('p_value', 1.0)

                    # High significance discovery - consider for code evolution
                    if p_value < 0.01:
                        logger.info(f"High significance discovery: {node.id} (p={p_value})")

                        # Check if this suggests new statistical methods
                        if discovery_data.get('finding_type') == 'causal':
                            changes.append(f"Consider adding causal inference methods for {discovery_data.get('domain')} domain")

                        # Check if this suggests new data sources
                        data_source = discovery_data.get('data_source')
                        if data_source and data_source not in ['sdss', 'gaia', 'pantheon']:
                            changes.append(f"New data source identified: {data_source}")

            # Sync discoveries
            self._sync_to_graphpalace()

            # Update state
            self.state['last_evolution'] = datetime.now().isoformat()
            if changes:
                self.state['code_updates'].extend(changes)
            self._save_state()

        except Exception as e:
            logger.error(f"Code evolution analysis failed: {e}")

        return changes

    def _discovery_worker(self):
        """Worker thread that runs discovery cycles."""
        while self.running:
            try:
                logger.info("Starting discovery cycle...")
                result = self._trigger_discovery_cycle()

                if result:
                    self.state['cycles_completed'] += 1
                    discoveries_count = result.get('discoveries', 0)
                    self.state['discoveries_made'] += discoveries_count
                    self._save_state()

                    logger.info(f"Cycle complete. Total cycles: {self.state['cycles_completed']}, "
                               f"Total discoveries: {self.state['discoveries_made']}")

            except Exception as e:
                logger.error(f"Discovery worker error: {e}")

            # Wait before next cycle
            for _ in range(DISCOVERY_INTERVAL):
                if not self.running:
                    break
                time.sleep(1)

    def _sync_worker(self):
        """Worker thread that syncs discoveries to GraphPalace."""
        while self.running:
            try:
                self._sync_to_graphpalace()
            except Exception as e:
                logger.error(f"Sync worker error: {e}")

            # Wait before next sync
            for _ in range(SYNC_INTERVAL):
                if not self.running:
                    break
                time.sleep(1)

    def _evolution_worker(self):
        """Worker thread that analyzes discoveries for code evolution opportunities."""
        while self.running:
            try:
                changes = self._evolve_codebase()

                if changes:
                    logger.info(f"Code evolution suggestions: {changes}")

            except Exception as e:
                logger.error(f"Evolution worker error: {e}")

            # Wait before next evolution check
            for _ in range(EVOLUTION_INTERVAL):
                if not self.running:
                    break
                time.sleep(1)

    def start(self):
        """Start the daemon and all worker threads."""
        if self.running:
            logger.warning("Daemon already running")
            return

        self.running = True
        logger.info("Starting ContinuousDiscoveryDaemon...")

        # Start worker threads
        self.discovery_thread = threading.Thread(target=self._discovery_worker, daemon=True)
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.evolution_thread = threading.Thread(target=self._evolution_worker, daemon=True)

        self.discovery_thread.start()
        self.sync_thread.start()
        self.evolution_thread.start()

        logger.info("Daemon started with 3 worker threads:")
        logger.info(f"  - Discovery worker (interval: {DISCOVERY_INTERVAL}s)")
        logger.info(f"  - Sync worker (interval: {SYNC_INTERVAL}s)")
        logger.info(f"  - Evolution worker (interval: {EVOLUTION_INTERVAL}s)")

    def stop(self):
        """Stop the daemon and all worker threads."""
        if not self.running:
            return

        logger.info("Stopping ContinuousDiscoveryDaemon...")
        self.running = False

        # Wait for threads to finish
        if self.discovery_thread:
            self.discovery_thread.join(timeout=5)
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        if self.evolution_thread:
            self.evolution_thread.join(timeout=5)

        logger.info("Daemon stopped")

    def get_status(self) -> Dict:
        """Get current daemon status."""
        return {
            'running': self.running,
            'state': self.state,
            'graph_palace': self.graph_palace.get_status()
        }


def main():
    """Main entry point for the daemon."""
    import argparse

    parser = argparse.ArgumentParser(description='Continuous Discovery Daemon for ASTRA')
    parser.add_argument('--start', action='store_true', help='Start the daemon')
    parser.add_argument('--stop', action='store_true', help='Stop the daemon')
    parser.add_argument('--status', action='store_true', help='Show daemon status')
    parser.add_argument('--once', action='store_true', help='Run one discovery cycle and exit')
    parser.add_argument('--daemon', action='store_true', help='Run as background daemon')

    args = parser.parse_args()

    daemon = ContinuousDiscoveryDaemon()

    if args.status:
        status = daemon.get_status()
        print(json.dumps(status, indent=2))
        return

    if args.once:
        logger.info("Running single discovery cycle...")
        result = daemon._trigger_discovery_cycle()
        daemon._sync_to_graphpalace()
        print(json.dumps(result, indent=2))
        return

    if args.start or args.daemon:
        if args.daemon:
            # Fork to background
            pid = os.fork()
            if pid > 0:
                # Parent process
                print(f"Daemon started with PID: {pid}")
                with open(ASTRA_ROOT / 'data' / 'daemon.pid', 'w') as f:
                    f.write(str(pid))
                return

        daemon.start()

        if args.daemon:
            # Keep running in background
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt, shutting down...")
                daemon.stop()
        else:
            # Keep in foreground
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt, shutting down...")
                daemon.stop()


if __name__ == '__main__':
    main()
