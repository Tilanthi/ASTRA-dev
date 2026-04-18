#!/usr/bin/env python3
"""
Sync discoveries from SQLite database to GraphPalace knowledge graph.

This script reads discoveries from astra_discoveries.db and populates
GraphPalace with nodes, edges, and pheromones for long-term memory.
"""
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Add ASTRA to path
ASTRA_ROOT = Path(__file__).parent
sys.path.insert(0, str(ASTRA_ROOT / 'astra_live_backend'))

from graph_palace import (
    get_graph_palace,
    GraphNode,
    GraphEdge,
    PHEROMONE_SUCCESS,
    PHEROMONE_FAILURE,
    PHEROMONE_NOVELTY
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_discoveries():
    """Sync all discoveries from database to GraphPalace."""
    db_path = ASTRA_ROOT / 'astra_discoveries.db'

    if not db_path.exists():
        logger.error(f"Discovery database not found: {db_path}")
        return

    # Get GraphPalace bridge
    graph_palace = get_graph_palace(use_rust=False)

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all discoveries
    cursor.execute("SELECT * FROM discoveries")
    discoveries = [dict(row) for row in cursor.fetchall()]

    logger.info(f"Found {len(discoveries)} discoveries in database")

    nodes_added = 0
    edges_added = 0
    pheromones_deposited = 0

    for discovery in discoveries:
        # Create discovery node
        discovery_id = discovery.get('id', f'discovery_{discovery["timestamp"]}')

        # Use data_source as domain for better granularity, fallback to domain
        domain = discovery.get('data_source') or discovery.get('domain', 'unknown')

        node = GraphNode(
            id=discovery_id,
            node_type='discovery',
            domain=domain,
            category=discovery.get('finding_type', 'unknown'),
            metadata={
                'hypothesis_id': discovery.get('hypothesis_id'),
                'test_statistic': discovery.get('statistic'),
                'p_value': discovery.get('p_value'),
                'effect_size': discovery.get('effect_size'),
                'variables': discovery.get('variables'),
                'description': discovery.get('description'),
                'timestamp': discovery.get('timestamp'),
                'data_source': discovery.get('data_source'),
                'strength': discovery.get('strength', 1.0),
                'verified': discovery.get('verified', 0)
            }
        )

        if graph_palace.add_node(node):
            nodes_added += 1

        # Deposit novelty pheromone based on significance
        strength = discovery.get('strength', 1.0)
        p_value = discovery.get('p_value', 1.0)

        # High significance = high novelty pheromone
        if p_value < 0.05:
            pheromone_strength = 3.0 * strength * (1 - p_value/0.05)
            graph_palace.deposit_pheromone(
                discovery_id,
                PHEROMONE_NOVELTY,
                min(pheromone_strength, 5.0)
            )
            pheromones_deposited += 1

        # If significant, also deposit success pheromone
        if p_value < 0.01:
            success_strength = 2.0 * (1 - p_value/0.01)
            graph_palace.deposit_pheromone(
                discovery_id,
                PHEROMONE_SUCCESS,
                min(success_strength, 5.0)
            )

    # Also sync generated hypotheses
    cursor.execute("SELECT * FROM generated_hypotheses LIMIT 100")
    hypotheses = [dict(row) for row in cursor.fetchall()]

    logger.info(f"Found {len(hypotheses)} hypotheses in database")

    for hypothesis in hypotheses:
        # Create hypothesis node
        node = GraphNode(
            id=hypothesis.get('rowid', f'hypothesis_{hypothesis["timestamp"]}'),
            node_type='hypothesis',
            domain=hypothesis.get('domain', 'unknown'),
            category='generated',
            metadata={
                'hypothesis_text': hypothesis.get('hypothesis_text'),
                'source_discovery_id': hypothesis.get('source_discovery_id'),
                'timestamp': hypothesis.get('timestamp')
            }
        )

        if graph_palace.add_node(node):
            nodes_added += 1

    # Create edges between related discoveries
    cursor.execute("""
        SELECT d1.id, d2.id, d1.data_source, d1.finding_type
        FROM discoveries d1
        JOIN discoveries d2 ON d1.data_source = d2.data_source
        WHERE d1.id < d2.id
        LIMIT 50
    """)

    related_pairs = cursor.fetchall()

    for d1_id, d2_id, data_source, finding_type in related_pairs:
        edge = GraphEdge(
            source_id=d1_id,
            target_id=d2_id,
            edge_type='semantic',
            weight=0.8,
            metadata={'domain': data_source, 'category': finding_type}
        )

        if graph_palace.add_edge(edge):
            edges_added += 1

    conn.close()

    # Persist state
    graph_palace.persist_state()

    logger.info(f"Sync complete: {nodes_added} nodes, {edges_added} edges, {pheromones_deposited} pheromones")

    # Print status
    status = graph_palace.get_status()
    logger.info(f"GraphPalace status: {status}")

    return nodes_added, edges_added, pheromones_deposited


if __name__ == '__main__':
    sync_discoveries()
