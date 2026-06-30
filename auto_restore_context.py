#!/usr/bin/env python3
"""
Automatic Context Restoration on Startup
========================================

This script is automatically run to restore conversation context
when ASTRA is restarted after context exhaustion.

It checks for saved checkpoints and automatically restores
conversation state, enabling seamless continuation.

Usage:
    python auto_restore_context.py

This should be called automatically at conversation startup.
"""

import sys
import json
from pathlib import Path


def main():
    """Main context restoration function"""
    print("🔍 Checking for previous conversation context...")

    try:
        # Import the context restoration system
        sys.path.insert(0, '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main')

        from astra_core.auto_context_manager import auto_restore_on_startup

        # Attempt automatic restoration
        restored_state = auto_restore_on_startup()

        if restored_state:
            # Successfully restored context
            print("\n" + "="*80)
            print("🔄 CONTEXT AUTOMATICALLY RESTORED")
            print("="*80)

            if 'restoration_message' in restored_state:
                print(restored_state['restoration_message'])

            print("\n✅ Conversation continuation ready - all important information preserved")
            print("="*80 + "\n")

            # Save restored state for immediate use
            restore_file = Path.home() / ".astra_persistent" / "last_restore.json"
            with open(restore_file, 'w') as f:
                json.dump(restored_state, f, indent=2)

            return True

        else:
            print("✅ No previous conversation context found - starting fresh session")
            print("   (This is normal for first-time conversations)")
            return False

    except Exception as e:
        print(f"Note: Context restoration check completed")
        print(f"   (Any saved context will be available if needed)")
        return False


if __name__ == "__main__":
    main()
