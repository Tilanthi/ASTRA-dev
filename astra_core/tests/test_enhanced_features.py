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
Enhanced STAR-Learn V2.0 Feature Demonstration

This script demonstrates the new enhanced features:
1. Embedding-based novelty detection
2. Scientific data integration for law discovery
3. Multi-agent swarm coordination
4. arXiv literature integration

Compares V1.0 (baseline) vs V2.0 (enhanced) performance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import json
from datetime import datetime


def test_enhanced_features():
    """Test all enhanced V2.0 features."""
    print("\n" + "="*70)
    print("STAR-Learn V2.0 Enhanced Features Test")
    print("="*70)

    results = {
        'v1_baseline': {},
        'v2_enhanced': {},
        'timestamp': datetime.now().isoformat()
    }

    # ========================================================================
    # Test 1: Enhanced Novelty Detection
    # ========================================================================
    print("\n[1] Enhanced Novelty Detection (Embedding-based)")
    print("-" * 70)

    from astra_core.self_teaching.embedding_novelty import (
        EnhancedRewardCalculator,
        SimpleEmbeddingModel,
        ScientificKnowledgeGraph
    )

    calc = EnhancedRewardCalculator()

    # Test discoveries
    discovery1 = {
        'content': 'Energy is conserved in isolated systems through time',
        'domain': 'physics',
        'confidence': 0.9
    }

    discovery2 = {
        'content': 'Energy remains constant in closed physical systems',
        'domain': 'physics',
        'confidence': 0.9
    }

    novelty1, details1 = calc.calculate_enhanced_novelty(discovery1, use_embeddings=True)
    novelty2, details2 = calc.calculate_enhanced_novelty(discovery2, use_embeddings=True)

    print(f"  Discovery 1 novelty: {novelty1:.4f}")
    print(f"  Discovery 2 novelty: {novelty2:.4f} (should be lower)")
    print(f"  Similarity detected: {details2.get('max_similarity', 0):.4f}")

    results['v2_enhanced']['embedding_novelty'] = {
        'first_discovery_novelty': novelty1,
        'similar_discovery_novelty': novelty2,
        'similarity_detected': details2.get('max_similarity', 0)
    }

    # Test conservation law detection
    print("\n[2] Conservation Law Detection")
    print("-" * 70)

    conservation_reward, cons_details = calc.check_conservation_discovery(discovery1)
    print(f"  Energy conservation reward: {conservation_reward:.4f}")
    print(f"  Quantity: {cons_details.get('quantity', 'N/A')}")

    results['v2_enhanced']['conservation_detection'] = {
        'reward': conservation_reward,
        'quantity': cons_details.get('quantity', 'N/A')
    }

    # ========================================================================
    # Test 3: Scientific Data Integration
    # ========================================================================
    print("\n[3] Scientific Data Integration")
    print("-" * 70)

    from astra_core.self_teaching.scientific_data import (
        PhysicsDataLibrary,
        PhysicalLawDiscovery,
        get_scientific_discovery_reward
    )

    data_lib = PhysicsDataLibrary()
    law_engine = PhysicalLawDiscovery()

    datasets = data_lib.list_datasets()
    print(f"  Available datasets: {len(datasets)}")
    for ds in datasets[:5]:
        print(f"    - {ds}")

    # Discover laws from Kepler dataset
    kepler_dataset = data_lib.get_dataset('kepler_third_law')
    if kepler_dataset:
        laws = law_engine.discover_all_laws(kepler_dataset)
        print(f"\n  Laws discovered from Kepler data: {len(laws)}")
        for law in laws[:3]:
            print(f"    - {law.name}: {law.equation[:60]}...")

    results['v2_enhanced']['scientific_data'] = {
        'datasets_available': len(datasets),
        'laws_discovered': len(laws) if kepler_dataset else 0
    }

    # ========================================================================
    # Test 4: Multi-Agent Swarm
    # ========================================================================
    print("\n[4] Multi-Agent Swarm Coordination")
    print("-" * 70)

    from astra_core.self_teaching.multi_agent_swarm import (
        create_multi_agent_swarm,
        ExplorerAgent,
        FalsifierAgent
    )

    swarm = create_multi_agent_swarm()
    print(f"  Swarm initialized with {len(swarm.agents)} agents")

    # Agent breakdown
    from astra_core.self_teaching.multi_agent_swarm import AgentRole
    agent_counts = {}
    for agent in swarm.agents:
        role = agent.role.value
        agent_counts[role] = agent_counts.get(role, 0) + 1

    print("  Agents by role:")
    for role, count in agent_counts.items():
        print(f"    - {role}: {count}")

    # Run coordination
    swarm_results = swarm.coordinate(n_steps=5)
    print(f"\n  Coordination results (5 steps):")
    print(f"    - Discoveries: {len(swarm_results['discoveries'])}")
    print(f"    - Validations: {len(swarm_results['validations'])}")
    print(f"    - Theories: {len(swarm_results['theories'])}")

    results['v2_enhanced']['swarm'] = {
        'total_agents': len(swarm.agents),
        'discoveries': len(swarm_results['discoveries']),
        'validations': len(swarm_results['validations']),
        'theories': len(swarm_results['theories']),
        'metrics': swarm_results['metrics']
    }

    # ========================================================================
    # Test 5: arXiv Literature Integration
    # ========================================================================
    print("\n[5] arXiv Literature Integration")
    print("-" * 70)

    from astra_core.self_teaching.arxiv_integration import (
        create_arxiv_integration,
        get_literature_learning_reward
    )

    arxiv_system = create_arxiv_integration()

    # Learn from literature
    learning_results = arxiv_system.learn_from_literature(n_papers=5)
    print(f"  Papers read: {learning_results['papers']}")
    print(f"  Concepts learned: {learning_results['concepts']}")

    # Get trending topics
    trends = arxiv_system.get_trending_topics(top_n=3)
    print(f"\n  Trending topics:")
    for trend in trends:
        print(f"    - {trend.topic}: {trend.growth_rate:.2f} growth, {trend.papers_count} papers")

    results['v2_enhanced']['arxiv'] = {
        'papers_read': len(learning_results.get('papers', [])),
        'concepts_learned': learning_results.get('concepts', 0),
        'trending_topics': len(trends),
        'top_trends': [
            {'topic': t.topic, 'growth': t.growth_rate}
            for t in trends
        ]
    }

    # ========================================================================
    # Test 6: Full Enhanced System
    # ========================================================================
    print("\n[6] Full Enhanced STAR-Learn System")
    print("-" * 70)

    from astra_core.self_teaching import STARLearnSystem

    system = STARLearnSystem()

    # Check capabilities
    capabilities = system.get_enhanced_capabilities()
    print("  Enhanced capabilities status:")
    for cap, status in capabilities.items():
        print(f"    - {cap}: {status}")

    # Run autonomous training with enhanced features
    print("\n  Running autonomous training (5 iterations with enhanced features)...")
    training_results = system.train_autonomously(
        n_iterations=5,
        generate_report=False,
        verbose=False
    )

    rewards = [r.total_reward for r in training_results]
    print(f"  Rewards: {[f'{r:.3f}' for r in rewards]}")
    print(f"  Average reward: {np.mean(rewards):.3f}")
    print(f"  Best reward: {np.max(rewards):.3f}")

    results['v2_enhanced']['full_system'] = {
        'average_reward': float(np.mean(rewards)),
        'best_reward': float(np.max(rewards)),
        'final_reward': float(rewards[-1]),
        'capabilities': capabilities
    }

    # ========================================================================
    # Comparison Summary
    # ========================================================================
    print("\n" + "="*70)
    print("V2.0 ENHANCEMENT SUMMARY")
    print("="*70)

    print("\nKey Improvements:")
    print(f"  1. Embedding-based Novelty Detection: {results['v2_enhanced']['embedding_novelty']['similarity_detected']:.2%} similarity detection")
    print(f"  2. Conservation Law Detection: {results['v2_enhanced']['conservation_detection']['reward']:.2%} reward for energy conservation")
    print(f"  3. Scientific Datasets: {results['v2_enhanced']['scientific_data']['datasets_available']} real-world datasets available")
    print(f"  4. Multi-Agent Swarm: {results['v2_enhanced']['swarm']['total_agents']} specialized agents")
    print(f"  5. Literature Learning: {results['v2_enhanced']['arxiv']['papers_read']} papers analyzed, {results['v2_enhanced']['arxiv']['concepts_learned']} concepts learned")
    print(f"  6. Full System Performance: {results['v2_enhanced']['full_system']['average_reward']:.3f} average reward")

    return results


if __name__ == '__main__':
    results = test_enhanced_features()

    # Save results
    output_file = Path(__file__).parent.parent.parent / 'star_learn_v2_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
