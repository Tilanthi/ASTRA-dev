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
Create Example Cross-Domain Discoveries for GraphPalace

Generates sample discoveries across multiple domains to demonstrate
GraphPalace's auto-tunnel capabilities for cross-domain discovery.

Usage:
    python3 create_cross_domain_discoveries.py
"""

import os
import sys
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_example_discoveries():
    """Create example cross-domain discoveries to demonstrate auto-tunnels."""

    print("="*70)
    print("Creating Example Cross-Domain Discoveries")
    print("="*70)

    # Import GraphPalace
    try:
        from astra_live_backend.graphpalace_memory import GraphPalaceMemory
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return

    # Initialize GraphPalace
    print(f"\n[Init] Creating GraphPalace memory...")
    try:
        memory = GraphPalaceMemory("astra_discoveries.db")
        print(f"  ✓ GraphPalace loaded")
    except Exception as e:
        print(f"  ✗ Failed to load GraphPalace: {e}")
        return

    # Define cross-domain discovery examples
    # Each demonstrates a pattern that appears across multiple domains
    examples = [
        # Power Law Scaling Pattern (appears in astronomy, economics, physics)
        {
            "description": "Filament spacing follows power law distribution N(L) ∝ L^(-2.3) with 150 parsec scale range",
            "domain": "astronomy",
            "finding_type": "scaling",
            "variables": ["log_spacing", "log_length"],
            "statistic": 2.3,
            "p_value": 0.001,
            "data_source": "W3_HGBS",
            "strength": 0.95,
            "effect_size": 0.87
        },
        {
            "description": "City size distribution follows Zipf's law P(S) ∝ S^(-2.1) across 4000 US cities",
            "domain": "economics",
            "finding_type": "scaling",
            "variables": ["log_population", "log_rank"],
            "statistic": 2.1,
            "p_value": 0.0001,
            "data_source": "US_Census",
            "strength": 0.92,
            "effect_size": 0.91
        },
        {
            "description": "Earthquake magnitude distribution follows Gutenberg-Richter law log N = a - bM with b=1.05",
            "domain": "physics",
            "finding_type": "scaling",
            "variables": ["log_count", "magnitude"],
            "statistic": 1.05,
            "p_value": 0.00001,
            "data_source": "USGS",
            "strength": 0.98,
            "effect_size": 0.95
        },

        # Critical Phenomena Pattern (appears in physics, astronomy, climate)
        {
            "description": "Percolation threshold at pc = 0.593 for 2D lattice with cluster size distribution n(s) ∝ s^(-τ)",
            "domain": "physics",
            "finding_type": "anomaly",
            "variables": ["occupation_prob", "cluster_size"],
            "statistic": 0.593,
            "p_value": 0.0001,
            "data_source": "simulation",
            "strength": 0.88,
            "effect_size": 0.82
        },
        {
            "description": "Star formation efficiency shows sharp threshold at gas density 10^4 cm^-3 in molecular clouds",
            "domain": "astronomy",
            "finding_type": "anomaly",
            "variables": ["gas_density", "sfr_efficiency"],
            "statistic": 0.61,
            "p_value": 0.002,
            "data_source": "Gaia_DR3",
            "strength": 0.85,
            "effect_size": 0.79
        },
        {
            "description": "Forest fire spread shows critical transition at relative humidity 35% with jump in burn area",
            "domain": "climate",
            "finding_type": "anomaly",
            "variables": ["humidity", "burn_area"],
            "statistic": 0.35,
            "p_value": 0.01,
            "data_source": "satellite_data",
            "strength": 0.78,
            "effect_size": 0.71
        },

        # Correlation vs Causation Pattern (appears in economics, epidemiology, astronomy)
        {
            "description": "Stock market correlation ρ = 0.76 between tech sector returns without causal link (confounder: Fed policy)",
            "domain": "economics",
            "finding_type": "causal",
            "variables": ["tech_returns", "fed_policy_rate"],
            "statistic": 0.76,
            "p_value": 0.03,
            "data_source": "NYSE",
            "strength": 0.72,
            "effect_size": 0.65
        },
        {
            "description": "Vaccination rates correlated with COVID-19 cases (ρ = -0.68) but confounded by population density",
            "domain": "epidemiology",
            "finding_type": "causal",
            "variables": ["vaccination_rate", "case_rate"],
            "statistic": -0.68,
            "p_value": 0.02,
            "data_source": "CDC",
            "strength": 0.69,
            "effect_size": 0.58
        },
        {
            "description": "Galaxy color correlated with distance (ρ = -0.71) due to redshift evolution, not environmental effects",
            "domain": "astronomy",
            "finding_type": "causal",
            "variables": ["color_index", "redshift"],
            "statistic": -0.71,
            "p_value": 0.001,
            "data_source": "SDSS_DR18",
            "strength": 0.81,
            "effect_size": 0.73
        },

        # Oscillation Pattern (appears in economics, astronomy, biology)
        {
            "description": "Business cycle oscillation with period 5.2 years and amplitude 2.3% GDP variance",
            "domain": "economics",
            "finding_type": "bimodality",
            "variables": ["gdp_growth", "time_lagged"],
            "statistic": 5.2,
            "p_value": 0.01,
            "data_source": "BEA",
            "strength": 0.75,
            "effect_size": 0.68
        },
        {
            "description": "Cepheid variable period-luminosity relation with characteristic oscillation period 2-50 days",
            "domain": "astronomy",
            "finding_type": "bimodality",
            "variables": ["period", "luminosity"],
            "statistic": 2.3,
            "p_value": 0.0001,
            "data_source": "Hubble_Space_Telescope",
            "strength": 0.96,
            "effect_size": 0.92
        },
        {
            "description": "Circadian rhythm oscillation with 24.2 hour period and 0.8 amplitude variation",
            "domain": "biology",
            "finding_type": "bimodality",
            "variables": ["activity_level", "time_of_day"],
            "statistic": 24.2,
            "p_value": 0.00001,
            "data_source": "sleep_studies",
            "strength": 0.93,
            "effect_size": 0.88
        },

        # Network Theory Pattern (appears in sociology, astronomy, biology)
        {
            "description": "Social network degree distribution follows power law P(k) ∝ k^(-2.4) with small-world clustering coefficient 0.23",
            "domain": "sociology",
            "finding_type": "scaling",
            "variables": ["degree", "probability"],
            "statistic": 2.4,
            "p_value": 0.0001,
            "data_source": "social_media",
            "strength": 0.91,
            "effect_size": 0.85
        },
        {
            "description": "Galaxy cluster network shows small-world properties with path length 2.3 and clustering 0.45",
            "domain": "astronomy",
            "finding_type": "scaling",
            "variables": ["path_length", "clustering_coeff"],
            "statistic": 2.3,
            "p_value": 0.005,
            "data_source": "SDSS_Clusters",
            "strength": 0.83,
            "effect_size": 0.77
        },
        {
            "description": "Protein interaction network exhibits scale-free topology with hub nodes and γ = 2.1 exponent",
            "domain": "biology",
            "finding_type": "scaling",
            "variables": ["node_degree", "count"],
            "statistic": 2.1,
            "p_value": 0.00001,
            "data_source": "bioinformatics",
            "strength": 0.94,
            "effect_size": 0.89
        },
    ]

    # Add discoveries to GraphPalace
    print(f"\n[Create] Adding {len(examples)} example discoveries...")

    created = 0
    for i, example in enumerate(examples):
        try:
            rec = memory.record_discovery(
                hypothesis_id=f"example_hyp_{i+1:03d}",
                domain=example["domain"],
                finding_type=example["finding_type"],
                variables=example["variables"],
                statistic=example["statistic"],
                p_value=example["p_value"],
                description=example["description"],
                data_source=example["data_source"],
                sample_size=random.randint(100, 1000),
                effect_size=example["effect_size"]
            )

            if rec:
                created += 1
                print(f"  ✓ [{i+1}/{len(examples)}] {example['domain']}: {example['description'][:60]}...")

        except Exception as e:
            print(f"  ✗ [{i+1}/{len(examples)}] Failed: {e}")

    print(f"\n[Created] Added {created} example discoveries")

    # Add knowledge graph relations for cross-domain patterns
    print(f"\n[KG] Adding cross-domain knowledge relations...")

    relations = [
        ("power law", "manifests_in", "astronomy", 0.95),
        ("power law", "manifests_in", "economics", 0.92),
        ("power law", "manifests_in", "physics", 0.98),
        ("critical phenomena", "exhibits", "astronomy", 0.85),
        ("critical phenomena", "exhibits", "physics", 0.88),
        ("critical phenomena", "exhibits", "climate", 0.78),
        ("correlation", "distinct_from", "causation", 0.90),
        ("oscillation", "characterizes", "periodic_behavior", 0.87),
        ("scale-free network", "observed_in", "astronomy", 0.83),
        ("scale-free network", "observed_in", "biology", 0.94),
        ("scale-free network", "observed_in", "sociology", 0.91),
    ]

    for subject, predicate, obj, confidence in relations:
        try:
            memory.add_knowledge_relation(subject, predicate, obj, confidence)
            print(f"  ✓ {subject} {predicate} {obj} ({confidence})")
        except Exception as e:
            print(f"  ✗ Failed to add relation: {e}")

    # Build auto-tunnels
    print(f"\n[Tunnels] Building auto-tunnels...")
    try:
        if memory.palace:
            memory.palace.build_tunnels()
            print(f"  ✓ Auto-tunnels built")
        else:
            print(f"  ⚠ GraphPalace not available")
    except Exception as e:
        print(f"  ⚠ Auto-tunnel build failed: {e}")

    # Find cross-domain connections
    print(f"\n[Discover] Finding cross-domain connections...")
    domains = ["astronomy", "economics", "physics", "climate", "epidemiology", "sociology", "biology"]

    connections_found = 0
    for i, domain1 in enumerate(domains):
        for domain2 in domains[i+1:]:
            try:
                connections = memory.find_cross_domain_connections(domain1, domain2, k=2)

                if connections:
                    print(f"  • {domain1} ↔ {domain2}: {len(connections)} tunnels")
                    connections_found += len(connections)

                    for conn in connections:
                        print(f"    - {conn.get('topic', '')}: {conn.get('explanation', '')}")

            except Exception as e:
                pass

    print(f"\n✓ Found {connections_found} cross-domain connections")

    # Get final status
    print(f"\n[Status] Final GraphPalace state:")
    status = memory.get_palace_status()
    print(f"  Total wings: {status.get('total_wings', 0)}")
    print(f"  Total rooms: {status.get('total_rooms', 0)}")
    print(f"  Total drawers: {status.get('total_drawers', 0)}")
    print(f"  Total discoveries: {status.get('total_discoveries', 0)}")
    print(f"  Entities: {status.get('entity_count', 0)}")
    print(f"  Relationships: {status.get('relationship_count', 0)}")

    # Save and close
    memory.close()

    print(f"\n" + "="*70)
    print("✓ Example discoveries created successfully!")
    print("="*70)
    print(f"\nNext steps:")
    print(f"  1. View dashboard: http://localhost:8787")
    print(f"  2. Click CONNECTIONS tab to see cross-domain network")
    print(f"  3. Try semantic search: 'power law' or 'critical phenomena'")
    print(f"  4. Run visualizations: python3 visualize_autotunnels.py")


if __name__ == "__main__":
    create_example_discoveries()
