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
Auto-Tunnel Visualization for GraphPalace

Creates interactive visualizations of GraphPalace's auto-tunnels that connect
similar topics across different domain wings. These tunnels represent
cross-domain discovery opportunities.

Usage:
    python3 visualize_autotunnels.py [--db-path PATH] [--output DIR]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def visualize_auto_tunnels(
    db_path: str = "astra_discoveries.db",
    output_dir: str = "autotunnel_viz"
):
    """
    Create visualizations of GraphPalace auto-tunnels.

    Args:
        db_path: Path to GraphPalace database
        output_dir: Directory to save visualizations
    """
    print("="*70)
    print("GraphPalace Auto-Tunnel Visualization")
    print("="*70)

    # Import GraphPalace
    try:
        from astra_live_backend.graphpalace_memory import (
            GraphPalaceMemory,
            GRAPHPALACE_AVAILABLE
        )
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return

    if not GRAPHPALACE_AVAILABLE:
        print("✗ GraphPalace not installed")
        return

    # Initialize GraphPalace
    print(f"\n[Init] Loading GraphPalace memory...")
    try:
        memory = GraphPalaceMemory(db_path)
        print(f"  ✓ GraphPalace loaded")
    except Exception as e:
        print(f"  ✗ Failed to load GraphPalace: {e}")
        return

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    print(f"\n[Output] Saving visualizations to: {output_path}")

    # Get palace status
    status = memory.get_palace_status()
    print(f"\n[Status] GraphPalace state:")
    print(f"  Wings: {status.get('total_wings', 0)}")
    print(f"  Rooms: {status.get('total_rooms', 0)}")
    print(f"  Drawers: {status.get('total_drawers', 0)}")
    print(f"  Entities: {status.get('entity_count', 0)}")
    print(f"  Relationships: {status.get('relationship_count', 0)}")

    # Get all wings
    if memory.palace:
        try:
            wings = memory.palace.list_wings()
            print(f"\n[Wings] Found {len(wings)} domain wings:")
            for wing in wings:
                print(f"  • {wing}")
        except Exception as e:
            print(f"  ⚠ Could not list wings: {e}")
            wings = []
    else:
        wings = []

    # Discover cross-domain connections
    print(f"\n[Tunnels] Discovering auto-tunnels...")

    all_connections = []
    tunnel_strengths = {}

    for i, wing1 in enumerate(wings):
        for wing2 in wings[i+1:]:
            try:
                connections = memory.find_cross_domain_connections(wing1, wing2, k=5)

                if connections:
                    print(f"  • {wing1} ↔ {wing2}: {len(connections)} tunnels")

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

            except Exception as e:
                pass

    if not all_connections:
        print("  ⚠ No auto-tunnels discovered yet")
        print("  (Tunnels emerge as more discoveries are added)")
        return

    print(f"  ✓ Found {len(all_connections)} total auto-tunnels")

    # Create network visualization
    print(f"\n[Viz] Creating network visualization...")
    create_network_visualization(all_connections, wings, output_path)

    # Create tunnel matrix
    print(f"[Viz] Creating tunnel matrix...")
    create_tunnel_matrix(tunnel_strengths, wings, output_path)

    # Create domain stats
    print(f"[Viz] Creating domain statistics...")
    create_domain_stats(memory, wings, output_path)

    # Export connection data
    print(f"[Export] Saving connection data...")
    export_connections(all_connections, output_path)

    # Close memory
    memory.close()

    print(f"\n" + "="*70)
    print("✓ Visualization complete!")
    print("="*70)
    print(f"\nGenerated files:")
    print(f"  • {output_path}/network_graph.png")
    print(f"  • {output_path}/tunnel_matrix.png")
    print(f"  • {output_path}/domain_stats.png")
    print(f"  • {output_path}/connections.json")


def create_network_visualization(
    connections: List[Dict[str, Any]],
    wings: List[str],
    output_path: Path
):
    """Create network graph visualization."""
    # Create network graph
    G = nx.Graph()

    # Add nodes (wings)
    domain_colors = {
        "astrophysics": "#00e5ff",
        "astronomy": "#00e5ff",
        "cosmology": "#7c4dff",
        "physics": "#ff5252",
        "economics": "#ffab00",
        "epidemiology": "#00e676",
        "climate": "#ff5252",
        "data_science": "#7c4dff",
    }

    for wing in wings:
        color = domain_colors.get(wing.lower(), "#ffffff")
        G.add_node(wing, color=color, size=1000)

    # Add edges (tunnels)
    edge_weights = {}
    for conn in connections:
        key = (conn["from"], conn["to"])
        if key not in edge_weights:
            edge_weights[key] = []
        edge_weights[key].append(conn["confidence"])

    # Aggregate edge weights
    for key, confidences in edge_weights.items():
        avg_confidence = sum(confidences) / len(confidences)
        weight = len(confidences) * avg_confidence
        G.add_edge(key[0], key[1], weight=weight, confidence=avg_confidence)

    # Create plot
    plt.figure(figsize=(14, 10))
    ax = plt.gca()

    # Use spring layout for better visualization
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Draw edges with varying widths
    edges = G.edges()
    weights = [G[u][v]["weight"] for u, v in edges]

    if weights:
        max_weight = max(weights)
        normalized_weights = [w / max_weight * 5 for w in weights]
    else:
        normalized_weights = [1] * len(edges)

    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        width=normalized_weights,
        alpha=0.4,
        edge_color="rgba(0, 229, 255, 0.5)",
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

    # Add edge labels (confidence)
    edge_labels = {}
    for u, v in edges:
        conf = G[u][v]["confidence"]
        if conf > 0.3:
            edge_labels[(u, v)] = f"{conf:.2f}"

    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels,
        font_size=8,
        font_color="rgba(255, 255, 255, 0.7)",
        ax=ax
    )

    # Styling
    ax.set_facecolor("#06080d")
    fig = plt.gcf()
    fig.patch.set_facecolor("#06080d")

    plt.title("GraphPalace Auto-Tunnel Network", color="white", fontsize=16, pad=20)
    plt.axis("off")

    # Add legend
    legend_elements = [
        mpatches.Patch(color="#00e5ff", label="Astronomy"),
        mpatches.Patch(color="#7c4dff", label="Physics/Cosmology"),
        mpatches.Patch(color="#ffab00", label="Economics"),
        mpatches.Patch(color="#00e676", label="Epidemiology"),
        mpatches.Patch(color="#ff5252", label="Climate/Other"),
    ]
    plt.legend(
        handles=legend_elements,
        loc="upper right",
        facecolor="#0a0e18",
        edgecolor="rgba(255,255,255,0.2)",
        labelcolor="white"
    )

    plt.tight_layout()
    plt.savefig(output_path / "network_graph.png", dpi=150, facecolor="#06080d")
    plt.close()


def create_tunnel_matrix(
    tunnel_strengths: Dict[str, int],
    wings: List[str],
    output_path: Path
):
    """Create tunnel strength matrix visualization."""
    if not wings or len(wings) < 2:
        return

    # Create matrix
    n = len(wings)
    matrix = np.zeros((n, n))

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
    ax.set_xticklabels(wings, rotation=45, ha="right", color="white")
    ax.set_yticklabels(wings, color="white")

    # Add text annotations
    for i in range(n):
        for j in range(n):
            if i != j and matrix[i][j] > 0:
                text = ax.text(
                    j, i, int(matrix[i][j]),
                    ha="center", va="center",
                    color="white", fontsize=10, fontweight="bold"
                )

    # Styling
    ax.set_facecolor("#06080d")
    fig.patch.set_facecolor("#06080d")

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.ax.yaxis.set_tick_params(color="white")
    cbar.ax.yaxis.set_tick_params(labelcolor="white")
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color="white")

    plt.title("Auto-Tunnel Strength Matrix", color="white", fontsize=14, pad=15)
    plt.xlabel("Domain Wing", color="white", fontsize=12)
    plt.ylabel("Domain Wing", color="white", fontsize=12)
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    # Grid
    ax.set_xticks(np.arange(n) - 0.5, minor=True)
    ax.set_yticks(np.arange(n) - 0.5, minor=True)
    ax.grid(which="minor", color="rgba(255,255,255,0.1)", linestyle="-", linewidth=1)

    plt.tight_layout()
    plt.savefig(output_path / "tunnel_matrix.png", dpi=150, facecolor="#06080d")
    plt.close()


def create_domain_stats(
    memory,
    wings: List[str],
    output_path: Path
):
    """Create domain statistics visualization."""
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
    ax.set_xticklabels(domains, rotation=45, ha="right", color="white")
    ax.set_ylabel("Momentum Score", color="white", fontsize=12)
    ax.set_title("Domain Discovery Momentum", color="white", fontsize=14, pad=15)

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    # Grid
    ax.grid(axis="y", color="rgba(255,255,255,0.1)", linestyle="-", linewidth=0.5)

    # Add value labels on bars
    for i, (bar, score) in enumerate(zip(bars, scores)):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height,
            f"{score:.2f}",
            ha="center", va="bottom",
            color="white", fontsize=9
        )

    plt.tight_layout()
    plt.savefig(output_path / "domain_stats.png", dpi=150, facecolor="#06080d")
    plt.close()


def export_connections(
    connections: List[Dict[str, Any]],
    output_path: Path
):
    """Export connection data to JSON."""
    output_file = output_path / "connections.json"

    with open(output_file, "w") as f:
        json.dump(connections, f, indent=2)

    print(f"  ✓ Exported {len(connections)} connections to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Visualize GraphPalace auto-tunnels"
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

    args = parser.parse_args()

    try:
        import networkx as nx
        import matplotlib.pyplot as plt
    except ImportError as e:
        print(f"✗ Missing dependencies: {e}")
        print("Install with: pip install networkx matplotlib")
        sys.exit(1)

    visualize_auto_tunnels(
        db_path=args.db_path,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
