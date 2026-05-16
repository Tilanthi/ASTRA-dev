#!/usr/bin/env python3
"""
Example: Orchestrated ASTRA System Usage

Demonstrates the new Kubernetes-style orchestration capabilities.
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def basic_example():
    """Basic usage example"""
    print("\n" + "="*60)
    print("BASIC USAGE EXAMPLE")
    print("="*60 + "\n")

    from astra_core.orchestration import create_orchestrated_astra_system

    # Create system
    print("Creating orchestrated ASTRA system...")
    system = create_orchestrated_astra_system()
    await system.start()

    # Process a query
    print("Processing query...")
    result = await system.process_query(
        "What is the relationship between filament line-mass and core spacing?"
    )

    print(f"Result: {result}")

    # Get system status
    status = system.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Running: {status['running']}")
    print(f"  Uptime: {status['uptime_seconds']:.1f}s")
    print(f"  Health: {status['observability']['health']['overall_status']}")

    # Stop system
    await system.stop()
    print("\nSystem stopped.")


async def task_example():
    """Declarative task example"""
    print("\n" + "="*60)
    print("DECLARATIVE TASK EXAMPLE")
    print("="*60 + "\n")

    from astra_core.orchestration import (
        create_orchestrated_astra_system,
        TaskSpec,
        ResourceState
    )

    # Create system
    system = create_orchestrated_astra_system()
    await system.start()

    # Create a task
    task_spec = TaskSpec(
        kind="Task",
        name="filament-spacing-analysis",
        query="Analyze core spacing in Orion B filaments",
        priority="high",
        timeout=60.0,
        max_retries=2
    )

    print(f"Creating task: {task_spec.name}")
    task = await system.create_task(task_spec)
    print(f"Task UID: {task.get_uid()}")

    # Monitor task progress
    print("\nMonitoring task progress...")
    for i in range(10):
        await asyncio.sleep(1)
        status = await system.get_task_status(task.get_uid())

        if status == ResourceState.PENDING:
            print(f"  [{i+1}] Task pending...")
        elif status == ResourceState.RUNNING:
            print(f"  [{i+1}] Task running...")
        elif status == ResourceState.COMPLETED:
            print(f"  [{i+1}] Task completed!")
            print(f"  Result: {task.status.output}")
            break
        elif status == ResourceState.FAILED:
            print(f"  [{i+1}] Task failed: {task.status.error_message}")
            break

    await system.stop()
    print("\nSystem stopped.")


async def multi_mind_example():
    """Multi-mind orchestration example"""
    print("\n" + "="*60)
    print("MULTI-MIND ORCHESTRATION EXAMPLE")
    print("="*60 + "\n")

    from astra_core.orchestration import create_orchestrated_astra_system

    # Create system with mind mesh enabled
    config = {
        "enable_mind_mesh": True,
        "mind_selection_strategy": "confidence"
    }

    system = create_orchestrated_astra_system()
    await system.start()

    # Query with mind orchestration
    print("Processing query with multi-mind orchestration...")
    result = await system.process_query_with_minds(
        "Calculate the critical line mass for an isothermal filament",
        candidate_minds=["PhysicsMind", "MathMind"]
    )

    print(f"\nResult: {result}")

    # Get service mesh status
    mesh_status = system.service_mesh.get_mesh_status()
    print(f"\nService Mesh:")
    print(f"  Registered minds: {mesh_status['registered_minds']}")
    print(f"  Total requests: {mesh_status['mesh_metrics']['total_requests']}")

    await system.stop()
    print("\nSystem stopped.")


async def discovery_campaign_example():
    """Discovery campaign example"""
    print("\n" + "="*60)
    print("DISCOVERY CAMPAIGN EXAMPLE")
    print("="*60 + "\n")

    from astra_core.orchestration import create_orchestrated_astra_system

    system = create_orchestrated_astra_system()
    await system.start()

    # Create discovery campaign
    print("Creating discovery campaign...")
    campaign_name = await system.create_discovery_campaign(
        campaign_name="filament-physics-2026",
        domain="filaments",
        research_questions=[
            "What is the role of magnetic field geometry in fragmentation?",
            "How does subsonic turbulence affect core spacing?",
            "Can magnetic tension explain the observed sub-Jeans spacing?"
        ]
    )

    print(f"Campaign created: {campaign_name}")

    # Note: In production, you would run the campaign
    # results = await system.run_discovery_campaign(campaign_name)

    await system.stop()
    print("\nSystem stopped.")


async def custom_capability_example():
    """Custom capability registration example"""
    print("\n" + "="*60)
    print("CUSTOM CAPABILITY EXAMPLE")
    print("="*60 + "\n")

    from astra_core.orchestration import create_orchestrated_astra_system

    system = create_orchestrated_astra_system()
    await system.start()

    # Define custom capability
    async def stellar_evolution_analysis(query: str, context: dict) -> dict:
        """Custom capability for stellar evolution analysis"""
        return {
            "analysis_type": "stellar_evolution",
            "result": f"Analysis of query: {query[:50]}...",
            "confidence": 0.85,
            "methods_used": ["MESA", "SYNTHETIC"],
            "timestamp": datetime.now().isoformat()
        }

    # Register custom capability
    print("Registering custom capability...")
    system.register_custom_capability(
        name="stellar_evolution",
        handler=stellar_evolution_analysis,
        dependencies=["physics"]
    )

    # Use custom capability
    print("Using custom capability...")
    result = await system.process_query(
        "Analyze the evolution path of a 1.5 solar mass star"
    )

    print(f"Result: {result}")

    # Get CRD status
    crd_status = system.get_system_status()["crds"]
    print(f"\nCRD System:")
    print(f"  Registered CRDs: {crd_status['kinds']}")

    await system.stop()
    print("\nSystem stopped.")


async def system_observability_example():
    """System observability example"""
    print("\n" + "="*60)
    print("SYSTEM OBSERVABILITY EXAMPLE")
    print("="*60 + "\n")

    from astra_core.orchestration import create_orchestrated_astra_system

    system = create_orchestrated_astra_system()
    await system.start()

    # Get comprehensive system status
    print("Getting comprehensive system status...")
    status = system.get_system_status()

    print(f"\n{'='*60}")
    print(f"SYSTEM STATUS SUMMARY")
    print(f"{'='*60}")
    print(f"Running: {status['running']}")
    print(f"Uptime: {status['uptime_seconds']:.1f} seconds")

    print(f"\nControl Plane:")
    cp = status['control_plane']
    print(f"  API Status: {len(cp.get('api_status', {}).get('resource_types', []))} resource types")
    print(f"  Controllers: {len(cp.get('controllers', {}))} controllers")

    print(f"\nData Plane:")
    dp = status['data_plane']
    print(f"  Cache hit rate: {dp.get('cache_hit_rate', 0):.1%}")
    print(f"  Active executions: {dp.get('active_executions', 0)}")
    print(f"  Registered capabilities: {dp.get('registered_capabilities', 0)}")

    print(f"\nService Mesh:")
    sm = status['service_mesh']
    print(f"  Registered services: {sm.get('registered_services', 0)}")
    print(f"  Total requests: {sm.get('mesh_metrics', {}).get('total_requests', 0)}")

    print(f"\nObservability:")
    obs = status['observability']
    health = obs['health']
    print(f"  Overall health: {health.get('overall_status', 'unknown')}")
    print(f"  Component count: {health.get('component_count', 0)}")

    print(f"\nCRD System:")
    crd = status['crds']
    print(f"  Registered CRDs: {crd.get('registered_crds', 0)}")
    print(f"  Available kinds: {', '.join(crd.get('kinds', [])[:5])}...")

    await system.stop()
    print("\nSystem stopped.")


async def main():
    """Run all examples"""
    examples = [
        ("Basic Usage", basic_example),
        ("Declarative Tasks", task_example),
        ("Multi-Mind Orchestration", multi_mind_example),
        ("Discovery Campaign", discovery_campaign_example),
        ("Custom Capabilities", custom_capability_example),
        ("System Observability", system_observability_example),
    ]

    print("\n" + "="*70)
    print("ASTRA ORCHESTRATION LAYER EXAMPLES")
    print("="*70)
    print("\nDemonstrating Kubernetes-style orchestration for autonomous scientific discovery")
    print("\nExamples to run:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    # Run each example
    for name, example_func in examples:
        try:
            await example_func()
            await asyncio.sleep(1)  # Brief pause between examples
        except Exception as e:
            logger.error(f"Error in {name} example: {e}")

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
