#!/usr/bin/env python3
"""
ASTRA Autonomous Agent - Persistent Self-Evolving Research System

This agent:
1. Always runs continuous discovery cycles in the background
2. Processes specific user requests as they arrive
3. Evolves its codebase based on discoveries
4. Maintains GraphPalace knowledge graph for long-term memory
"""
import sys
import os
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Add ASTRA to path
ASTRA_ROOT = Path(__file__).parent
sys.path.insert(0, str(ASTRA_ROOT / 'astra_live_backend'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [ASTRA_AGENT] %(message)s',
    handlers=[
        logging.FileHandler(ASTRA_ROOT / 'logs' / 'autonomous_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ASTRAAutonomousAgent:
    """
    Autonomous research agent that continuously evolves while handling
    specific user requests.
    """

    def __init__(self):
        self.discovery_daemon_process = None
        self.running = False
        self.tasks_queue = []

        # Ensure directories exist
        (ASTRA_ROOT / 'logs').mkdir(exist_ok=True)
        (ASTRA_ROOT / 'data').mkdir(exist_ok=True)

        logger.info("=" * 60)
        logger.info("ASTRA Autonomous Agent Initializing")
        logger.info("=" * 60)

    def start_discovery_daemon(self):
        """Start the continuous discovery daemon in background."""
        if self.discovery_daemon_process:
            logger.warning("Discovery daemon already running")
            return

        logger.info("Starting continuous discovery daemon...")

        # Start daemon as subprocess
        self.discovery_daemon_process = subprocess.Popen(
            [sys.executable, str(ASTRA_ROOT / 'continuous_discovery_daemon.py'), '--daemon'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(ASTRA_ROOT)
        )

        # Wait a moment to ensure it started
        time.sleep(2)

        if self.discovery_daemon_process.poll() is None:
            logger.info(f"Discovery daemon started (PID: {self.discovery_daemon_process.pid})")
        else:
            logger.error("Failed to start discovery daemon")
            self.discovery_daemon_process = None

    def stop_discovery_daemon(self):
        """Stop the discovery daemon."""
        if self.discovery_daemon_process:
            logger.info("Stopping discovery daemon...")
            self.discovery_daemon_process.terminate()
            try:
                self.discovery_daemon_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.discovery_daemon_process.kill()
            self.discovery_daemon_process = None
            logger.info("Discovery daemon stopped")

    def check_discovery_status(self):
        """Check status of discovery daemon and report."""
        try:
            import requests
            response = requests.get(f"http://localhost:8787/api/engine/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                logger.info(f"Discovery engine status: {status.get('state', 'unknown')}")
                return True
        except Exception as e:
            logger.warning(f"Could not check discovery status: {e}")
            return False

    def sync_discoveries_to_memory(self):
        """Sync recent discoveries to GraphPalace for long-term memory."""
        try:
            import sync_discoveries_to_graphpalace
            logger.info("Syncing discoveries to GraphPalace...")
            nodes, edges, pheromones = sync_discoveries_to_graphpalace.sync_discoveries()
            logger.info(f"Memory sync complete: {nodes} nodes, {edges} edges, {pheromones} pheromones")
        except Exception as e:
            logger.error(f"Memory sync failed: {e}")

    def analyze_evolution_opportunities(self):
        """Analyze discoveries for opportunities to evolve the codebase."""
        try:
            from graph_palace import get_graph_palace
            graph_palace = get_graph_palace(use_rust=False)
            status = graph_palace.get_status()

            logger.info(f"GraphPalace status: {status['total_nodes']} nodes, "
                       f"{status['total_deposits']} pheromone deposits")

            # Check for high-impact discoveries
            novelty_count = status.get('deposits_by_type', {}).get('novelty', 0)
            success_count = status.get('deposits_by_type', {}).get('success', 0)

            if novelty_count > 20 or success_count > 30:
                logger.info("High discovery activity detected - checking for evolution opportunities")

                # Get recent discoveries
                recent_discoveries = graph_palace.semantic_search(
                    {'domain': 'Astrophysics'},
                    top_k=10,
                    min_score=0.2
                )

                for node, score in recent_discoveries:
                    if node.node_type == 'discovery':
                        p_value = node.metadata.get('p_value', 1.0)
                        if p_value < 0.01:
                            logger.info(f"High-impact discovery: {node.id} (p={p_value})")

                            # Log for potential code evolution
                            discovery_type = node.metadata.get('finding_type', 'unknown')
                            domain = node.metadata.get('domain', 'unknown')
                            logger.info(f"  Type: {discovery_type}, Domain: {domain}")

        except Exception as e:
            logger.error(f"Evolution analysis failed: {e}")

    def start(self):
        """Start the autonomous agent."""
        if self.running:
            logger.warning("Agent already running")
            return

        self.running = True
        logger.info("ASTRA Autonomous Agent starting...")

        # Start discovery daemon
        self.start_discovery_daemon()

        # Initial memory sync
        self.sync_discoveries_to_memory()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("=" * 60)
        logger.info("ASTRA Autonomous Agent RUNNING")
        logger.info("Background: Continuous discovery cycles active")
        logger.info("Memory: GraphPalace knowledge graph active")
        logger.info("Evolution: Codebase analysis enabled")
        logger.info("=" * 60)

    def stop(self):
        """Stop the autonomous agent."""
        if not self.running:
            return

        logger.info("ASTRA Autonomous Agent stopping...")
        self.running = False

        # Stop discovery daemon
        self.stop_discovery_daemon()

        # Final memory sync
        self.sync_discoveries_to_memory()

        logger.info("ASTRA Autonomous Agent stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

    def run_forever(self):
        """Run the agent main loop."""
        self.start()

        last_status_check = time.time()
        last_memory_sync = time.time()
        last_evolution_check = time.time()

        try:
            while self.running:
                current_time = time.time()

                # Periodic status checks
                if current_time - last_status_check > 60:
                    self.check_discovery_status()
                    last_status_check = current_time

                # Periodic memory syncs
                if current_time - last_memory_sync > 300:  # 5 minutes
                    self.sync_discoveries_to_memory()
                    last_memory_sync = current_time

                # Periodic evolution checks
                if current_time - last_evolution_check > 600:  # 10 minutes
                    self.analyze_evolution_opportunities()
                    last_evolution_check = current_time

                # Sleep briefly
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()


def main():
    """Main entry point."""
    agent = ASTRAAutonomousAgent()

    import argparse
    parser = argparse.ArgumentParser(description='ASTRA Autonomous Agent')
    parser.add_argument('--start', action='store_true', help='Start the agent')
    parser.add_argument('--status', action='store_true', help='Check status')
    parser.add_argument('--sync', action='store_true', help='Sync discoveries to memory')
    parser.add_argument('--analyze', action='store_true', help='Analyze evolution opportunities')

    args = parser.parse_args()

    if args.status:
        agent.check_discovery_status()
        return

    if args.sync:
        agent.sync_discoveries_to_memory()
        return

    if args.analyze:
        agent.analyze_evolution_opportunities()
        return

    if args.start:
        agent.run_forever()
    else:
        # Default: run forever
        agent.run_forever()


if __name__ == '__main__':
    main()
