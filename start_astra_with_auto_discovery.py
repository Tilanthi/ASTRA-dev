#!/usr/bin/env python3
"""
ASTRA Auto-Start Discovery System

This script demonstrates the new auto-start discovery functionality where:
1. ASTRA automatically starts discovery when initialized
2. Discovery runs continuously in the background
3. Discovery automatically pauses during user queries
4. Discovery automatically resumes after queries complete

This provides a truly autonomous research experience.

Usage:
    python start_astra_with_auto_discovery.py

The system will:
- Initialize ASTRA with auto-start discovery
- Start continuous discovery in the background
- Provide an interactive query interface
- Automatically pause/resume discovery during queries
- Show discovery status

Version: 1.0.0
Date: 2026-07-03
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from astra_core import create_stan_system

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("🚀 ASTRA v4.0 - Auto-Start Discovery System")
    print("="*70)
    print("✅ Discovery automatically starts when ASTRA is initialized")
    print("✅ Discovery runs continuously in the background")
    print("✅ Discovery pauses automatically during user queries")
    print("✅ Discovery resumes automatically after queries complete")
    print("="*70)
    print()


def print_status(system):
    """Print current system status"""
    print("\n📊 Current Status:")
    print("-" * 50)

    # Get auto-start discovery status
    try:
        status = system.get_auto_start_discovery_status()
        print(f"Auto-Start Discovery: {'✅ ENABLED' if status.get('enabled') else '❌ DISABLED'}")
        print(f"Discovery Running: {'✅ YES' if status.get('is_running') else '❌ NO'}")
        print(f"Currently Paused: {'⏸️ YES' if status.get('is_paused') else '▶️ NO'}")
        print(f"Discovery Cycles: {status.get('total_cycles', 0)}")
        print(f"Queries Processed: {status.get('total_queries_processed', 0)}")
        print(f"Discovery Rate: {status.get('discovery_rate_per_hour', 0):.1f} cycles/hour")
    except Exception as e:
        print(f"Error getting status: {e}")

    print("-" * 50)


def interactive_mode(system):
    """Run interactive query mode"""
    print("\n🎯 Interactive Query Mode")
    print("=" * 70)
    print("Enter your astronomical queries below.")
    print("Discovery will automatically pause during query processing.")
    print("Type 'status' to check discovery status, 'quit' to exit.")
    print("=" * 70)

    while True:
        try:
            query = input("\n❓ Your query: ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for using ASTRA! Goodbye!")
                break

            if query.lower() == 'status':
                print_status(system)
                continue

            print(f"\n🔄 Processing query: {query}")
            print("   (Discovery automatically paused during processing...)")

            # Process the query (discovery auto-pauses)
            result = system.answer(query)

            print(f"\n✅ Query processed!")
            print(f"   (Discovery automatically resumed)")

            # Display result
            print("\n📝 Answer:")
            print("-" * 50)
            print(result.get('answer', 'No answer generated'))
            print("-" * 50)

            # Show metadata
            print(f"\n📊 Metadata:")
            print(f"   Mode: {result.get('mode', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Capabilities: {', '.join(result.get('capabilities_used', []))}")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            logger.error(f"Query error: {e}", exc_info=True)


def demo_mode(system):
    """Run demo with sample queries"""
    print("\n🎯 Demo Mode - Sample Queries")
    print("=" * 70)

    sample_queries = [
        "What causes filament width variations in molecular clouds?",
        "How do magnetic fields influence star formation?",
        "status"
    ]

    for i, query in enumerate(sample_queries, 1):
        print(f"\n📝 Demo Query {i}/{len(sample_queries)}: {query}")

        if query.lower() == 'status':
            print_status(system)
            continue

        print("   (Discovery auto-paused during processing...)")

        result = system.answer(query)

        print("   (Discovery auto-resumed)")
        print(f"   Answer: {result.get('answer', 'No answer')[:100]}...")

    print("\n✅ Demo complete!")


def main():
    """Main entry point"""
    print_banner()

    logger.info("🚀 Initializing ASTRA with auto-start discovery...")

    try:
        # Create ASTRA system (auto-starts discovery automatically)
        print("Initializing ASTRA system...")
        system = create_stan_system()

        print("✅ ASTRA system initialized successfully!")
        print("✅ Auto-start discovery is running in the background!")

        # Check initial status
        print_status(system)

        # Ask user for mode
        print("\n🎯 Choose Mode:")
        print("1. Interactive Mode (enter your own queries)")
        print("2. Demo Mode (run sample queries)")
        print("3. Status Only (check and exit)")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == '1':
            interactive_mode(system)
        elif choice == '2':
            demo_mode(system)
        else:
            print_status(system)
            print("\n✅ ASTRA is now running discovery in the background!")
            print("💡 The system will continue discovering until you stop it.")

        # Stop discovery before exit
        print("\n🛑 Stopping auto-start discovery...")
        system.stop_auto_start_discovery()
        print("✅ Discovery stopped gracefully")

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())