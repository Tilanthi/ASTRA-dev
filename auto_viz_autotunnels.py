#!/usr/bin/env python3
# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Automatic Visualization Generator for GraphPalace Auto-Tunnels

Periodically generates visualizations of GraphPalace's auto-tunnels as
new discoveries are added. Can be run as a background service or scheduled task.

Usage:
    python3 auto_viz_autotunnels.py [--interval SECONDS] [--output DIR]
"""

import os
import sys
import time
import json
import argparse
import signal
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AutoVisualizationGenerator:
    """Automatically generates visualizations of GraphPalace auto-tunnels."""

    def __init__(self, db_path: str = "astra_discoveries.db", output_dir: str = "autotunnel_viz"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.running = False
        self.last_check = None
        self.last_discovery_count = 0

        # Import dependencies
        try:
            from astra_live_backend.graphpalace_memory import GraphPalaceMemory
            self.GraphPalaceMemory = GraphPalaceMemory
        except ImportError:
            print("✗ GraphPalace not available")
            raise

    def check_and_generate(self) -> bool:
        """
        Check if new discoveries were added and regenerate visualizations.

        Returns:
            True if visualizations were generated, False otherwise
        """
        try:
            # Load GraphPalace memory
            memory = self.GraphPalaceMemory(self.db_path)

            # Get current discovery count
            current_count = len(memory.discoveries)

            # Check if we have new discoveries
            has_new = current_count > self.last_discovery_count

            if has_new or self.last_check is None:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] New discoveries detected: {self.last_discovery_count} → {current_count}")
                print("Generating visualizations...")

                # Generate visualizations
                self.generate_all(memory)

                self.last_discovery_count = current_count
                self.last_check = datetime.now()

                # Create status file
                status_file = self.output_dir / "status.json"
                with open(status_file, "w") as f:
                    json.dump({
                        "last_check": self.last_check.isoformat(),
                        "discovery_count": current_count,
                        "visualizations_generated": True
                    }, f, indent=2)

                memory.close()
                return True
            else:
                memory.close()
                return False

        except Exception as e:
            print(f"[Error] Failed to check/generate: {e}")
            return False

    def generate_all(self, memory):
        """Generate all visualization types."""
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
        except ImportError as e:
            print(f"[Error] Missing dependencies: {e}")
            return

        # Get palace status
        status = memory.get_palace_status()

        # Get all wings
        if memory.palace:
            try:
                wings = memory.palace.list_wings()
            except Exception:
                wings = []
        else:
            wings = []

        # Discover cross-domain connections
        all_connections = []
        tunnel_strengths = {}

        for i, wing1 in enumerate(wings):
            for wing2 in wings[i+1:]:
                try:
                    connections = memory.find_cross_domain_connections(wing1, wing2, k=5)

                    for conn in connections:
                        all_connections.append({
                            "from": wing1,
                            "to": wing2,
                            "topic": conn.get("topic", ""),
                            "confidence": conn.get("confidence", 0),
                            "explanation": conn.get("explanation", "")
                        })

                    # Track overall strength
                    key = f"{wing1}→{wing2}"
                    tunnel_strengths[key] = len(connections)

                except Exception:
                    pass

        # Generate visualizations
        if all_connections:
            self.create_network_viz(all_connections, wings)
            self.create_tunnel_matrix(tunnel_strengths, wings)

        # Create domain stats
        self.create_domain_stats_viz(memory, wings)

        # Export data
        self.export_data(all_connections, status, wings)

        print("✓ Visualizations generated")

    def create_network_viz(self, connections, wings):
        """Create network graph visualization."""
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
        except ImportError:
            return

        # Create network
        G = nx.Graph()

        # Domain colors
        domain_colors = {
            "astronomy": "#00e5ff",
            "astrophysics": "#00e5ff",
            "cosmology": "#7c4dff",
            "physics": "#ff5252",
            "economics": "#ffab00",
            "epidemiology": "#00e676",
            "climate": "#ff5252",
            "sociology": "#ff9100",
            "biology": "#76ff03",
            "data_science": "#7c4dff",
        }

        # Add nodes
        for wing in wings:
            color = domain_colors.get(wing.lower(), "#ffffff")
            G.add_node(wing, color=color, size=1000 + len([d for d in connections if d["from"] == wing or d["to"] == wing]) * 100)

        # Add edges
        edge_weights = {}
        for conn in connections:
            key = (conn["from"], conn["to"])
            if key not in edge_weights:
                edge_weights[key] = []
            edge_weights[key].append(conn["confidence"])

        for key, confidences in edge_weights.items():
            avg_confidence = sum(confidences) / len(confidences)
            weight = len(confidences) * avg_confidence
            G.add_edge(key[0], key[1], weight=weight, confidence=avg_confidence)

        # Create plot
        fig, ax = plt.subplots(figsize=(14, 10))

        if G.number_of_nodes() > 0:
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

            # Draw edges
            edges = G.edges()
            if edges:
                weights = [G[u][v]["weight"] for u, v in edges]
                if weights:
                    max_weight = max(weights)
                    normalized_weights = [w / max_weight * 5 for w in weights]
                else:
                    normalized_weights = [1] * len(edges)

                nx.draw_networkx_edges(
                    G, pos,
                    width=normalized_weights,
                    alpha=0.4,
                    edge_color="#00e5ff",
                    ax=ax
                )

            # Draw nodes
            node_colors = [G.nodes[node]["color"] for node in G.nodes()]
            node_sizes = [G.nodes[node]["size"] for node in G.nodes()]

            nx.draw_networkx_nodes(
                G, pos,
                node_color=node_colors,
                node_size=node_sizes,
                alpha=0.8,
                ax=ax
            )

            # Draw labels
            nx.draw_networkx_labels(
                G, pos,
                font_size=10,
                font_weight="bold",
                font_color="white",
                ax=ax
            )

        # Styling
        ax.set_facecolor("#06080d")
        fig.patch.set_facecolor("#06080d")

        plt.title(f"GraphPalace Auto-Tunnel Network\n{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 color="white", fontsize=16, pad=20)
        plt.axis("off")
        plt.tight_layout()

        # Save
        output_file = self.output_dir / "network_graph.png"
        plt.savefig(output_file, dpi=150, facecolor="#06080d")
        plt.close()

        print(f"  ✓ Network graph: {output_file}")

    def create_tunnel_matrix(self, tunnel_strengths, wings):
        """Create tunnel strength matrix visualization."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
        except ImportError:
            return

        if not wings or len(wings) < 2:
            return

        # Create matrix
        n = len(wings)
        matrix = [[0] * n for _ in range(n)]

        for i, wing1 in enumerate(wings):
            for j, wing2 in enumerate(wings):
                if i != j:
                    key1 = f"{wing1}→{wing2}"
                    key2 = f"{wing2}→{wing1}"
                    matrix[i][j] = tunnel_strengths.get(key1, 0) + tunnel_strengths.get(key2, 0)

        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(matrix, cmap="viridis", aspect="auto")

        # Set ticks
        ax.set_xticks(np.arange(n))
        ax.set_yticks(np.arange(n))
        ax.set_xticklabels(wings, rotation=45, ha="right", color="white", fontsize=9)
        ax.set_yticklabels(wings, color="white", fontsize=9)

        # Add text annotations
        for i in range(n):
            for j in range(n):
                if i != j and matrix[i][j] > 0:
                    ax.text(j, i, int(matrix[i][j]),
                           ha="center", va="center",
                           color="white", fontsize=10, fontweight="bold")

        # Styling
        ax.set_facecolor("#06080d")
        fig.patch.set_facecolor("#06080d")

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.ax.yaxis.set_tick_params(color="white")
        cbar.ax.yaxis.set_tick_params(labelcolor="white")
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color="white")

        plt.title(f"Auto-Tunnel Strength Matrix\n{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 color="white", fontsize=14, pad=15)
        plt.xlabel("Domain Wing", color="white", fontsize=12)
        plt.ylabel("Domain Wing", color="white", fontsize=12)
        ax.tick_params(axis="x", colors="white")
        ax.tick_params(axis="y", colors="white")

        plt.tight_layout()
        output_file = self.output_dir / "tunnel_matrix.png"
        plt.savefig(output_file, dpi=150, facecolor="#06080d")
        plt.close()

        print(f"  ✓ Tunnel matrix: {output_file}")

    def create_domain_stats_viz(self, memory, wings):
        """Create domain statistics visualization."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
        except ImportError:
            return

        # Get domain statistics
        hot_domains = memory.get_hot_domains(top_n=10)

        if not hot_domains:
            return

        # Create bar chart
        fig, ax = plt.subplots(figsize=(12, 6))

        domains = [d[0] for d in hot_domains]
        scores = [d[1] for d in hot_domains]

        colors = [
            "#00e5ff", "#7c4dff", "#ffab00", "#00e676",
            "#ff5252", "#ff9100", "#00b0ff", "#76ff03",
            "#ff1744", "#00e5ff"
        ]

        bars = ax.bar(range(len(domains)), scores, color=colors[:len(domains)])

        # Styling
        ax.set_facecolor("#06080d")
        fig.patch.set_facecolor("#06080d")

        ax.set_xticks(range(len(domains)))
        ax.set_xticklabels(domains, rotation=45, ha="right", color="white", fontsize=10)
        ax.set_ylabel("Momentum Score", color="white", fontsize=12)
        ax.set_title(f"Domain Discovery Momentum\n{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                     color="white", fontsize=14, pad=15)
        ax.tick_params(axis="x", colors="white")
        ax.tick_params(axis="y", colors="white")

        # Grid
        ax.grid(axis="y", color="#ffffff", linestyle="-", linewidth=0.5, alpha=0.1)

        # Add value labels on bars
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                   f"{score:.2f}", ha="center", va="bottom",
                   color="white", fontsize=9)

        plt.tight_layout()
        output_file = self.output_dir / "domain_stats.png"
        plt.savefig(output_file, dpi=150, facecolor="#06080d")
        plt.close()

        print(f"  ✓ Domain stats: {output_file}")

    def export_data(self, connections, status, wings):
        """Export connection data to JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "discovery_count": status.get("total_discoveries", 0),
            "wings": wings,
            "connections": connections,
            "palace_status": status
        }

        output_file = self.output_dir / "connections_data.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  ✓ Data export: {output_file}")

    def run_periodic(self, interval_seconds: int = 300):
        """
        Run the auto-generator in periodic mode.

        Args:
            interval_seconds: Check interval in seconds (default: 300 = 5 minutes)
        """
        self.running = True

        print(f"[Auto-Viz] Starting periodic generator (interval: {interval_seconds}s)")
        print("[Auto-Viz] Press Ctrl+C to stop")

        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n[Auto-Viz] Shutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Main loop
        while self.running:
            try:
                self.check_and_generate()

                # Sleep until next check
                time.sleep(interval_seconds)

            except Exception as e:
                print(f"[Error] Periodic check failed: {e}")
                time.sleep(interval_seconds)

        print("[Auto-Viz] Stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automatic GraphPalace visualization generator"
    )
    parser.add_argument(
        "--db-path",
        default="astra_discoveries.db",
        help="Path to GraphPalace database"
    )
    parser.add_argument(
        "--output",
        default="autotunnel_viz",
        help="Output directory for visualizations"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300 = 5 minutes)"
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Generate once and exit (no periodic mode)"
    )

    args = parser.parse_args()

    # Create generator
    try:
        generator = AutoVisualizationGenerator(
            db_path=args.db_path,
            output_dir=args.output
        )
    except Exception as e:
        print(f"✗ Failed to create generator: {e}")
        sys.exit(1)

    if args.run_once:
        # Single run
        print("[Auto-Viz] Running single visualization generation...")
        generator.check_and_generate()
    else:
        # Periodic mode
        generator.run_periodic(args.interval)


if __name__ == "__main__":
    main()
