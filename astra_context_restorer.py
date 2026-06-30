#!/usr/bin/env python3
"""
ASTRA Conversation Context Restorer
===================================

This script integrates ASTRA's conversation checkpoint system with the
automatic session loading mechanism. It restores conversation context
from ~/.astra_persistent/conversation_context/ and provides seamless
continuation when ASTRA sessions restart.

Integration Points:
- Called by auto-session-load.sh for ASTRA projects
- Loads latest conversation checkpoint
- Integrates with ASTRA's persistent memory systems
- Maintains continuity of research, discoveries, and work

Version: 1.0.0
Date: 2026-06-28
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def load_astra_conversation_context():
    """
    Load ASTRA's conversation context from checkpoint system.

    Returns:
        dict: Restored conversation state or None if no checkpoint found
    """
    try:
        # Path to conversation context storage
        context_path = Path.home() / ".astra_persistent" / "conversation_context"
        index_file = context_path / "checkpoint_index.json"

        if not index_file.exists():
            return None

        # Load checkpoint index
        with open(index_file, 'r') as f:
            index = json.load(f)

        if not index.get('checkpoints'):
            return None

        # Get latest checkpoint
        latest_checkpoint = index['checkpoints'][-1]
        checkpoint_id = latest_checkpoint['checkpoint_id']
        checkpoint_file = context_path / f"checkpoint_{checkpoint_id}.json"

        if not checkpoint_file.exists():
            print(f"⚠️ Checkpoint file not found: {checkpoint_file}")
            return None

        # Load checkpoint data
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)

        return checkpoint_data

    except Exception as e:
        print(f"⚠️ Error loading conversation context: {e}")
        return None


def format_conversation_context(checkpoint_data):
    """
    Format conversation checkpoint data for display.

    Args:
        checkpoint_data: Loaded checkpoint dictionary

    Returns:
        str: Formatted conversation context
    """
    if not checkpoint_data:
        return "📝 No previous conversation context found"

    timestamp = checkpoint_data.get('timestamp', 'Unknown')
    total_messages = checkpoint_data.get('total_messages', 0)
    key_points = checkpoint_data.get('key_points', [])
    active_tasks = checkpoint_data.get('active_tasks', [])
    ongoing_work = checkpoint_data.get('ongoing_work', '')
    research_focus = checkpoint_data.get('research_focus', [])
    discoveries_state = checkpoint_data.get('discoveries_state', {})

    output = []
    output.append("=" * 80)
    output.append("🔄 ASTRA CONVERSATION CONTEXT RESTORED")
    output.append("=" * 80)
    output.append(f"**From**: {timestamp}")
    output.append(f"**Messages**: {total_messages} compressed to {len(key_points)} key points")
    output.append("")

    if key_points:
        output.append(f"📍 **Key Points** ({len(key_points)}):")
        for i, point in enumerate(key_points[:5], 1):
            output.append(f"   {i}. {point[:200]}")
        output.append("")

    if active_tasks:
        output.append(f"🎯 **Active Tasks** ({len(active_tasks)}):")
        for task in active_tasks[:3]:
            subject = task.get('subject', 'Task')
            status = task.get('status', 'unknown')
            output.append(f"   • {subject}: {status}")
        output.append("")

    if research_focus:
        output.append(f"🔬 **Research Focus**: {', '.join(research_focus[:3])}")
        output.append("")

    if ongoing_work:
        output.append(f"📋 **Ongoing Work**: {ongoing_work[:300]}...")
        output.append("")

    if discoveries_state:
        genuine_discoveries = discoveries_state.get('genuine_discoveries', 0)
        cycles_completed = discoveries_state.get('cycles_completed', 0)
        output.append(f"🔍 **Discoveries**: {genuine_discoveries} genuine discoveries, {cycles_completed} cycles completed")
        output.append("")

    output.append("**✅ CONVERSATION CONTEXT RESTORED**")
    output.append("We can continue exactly where we left off.")
    output.append("=" * 80)

    return "\n".join(output)


def main():
    """Main execution function"""
    print("🔍 Checking for ASTRA conversation context...")

    # Load conversation checkpoint
    checkpoint_data = load_astra_conversation_context()

    if checkpoint_data:
        # Format and display
        formatted_context = format_conversation_context(checkpoint_data)
        print(formatted_context)

        # Save to context file for session manager
        context_file = Path.home() / ".claude" / "session-manager" / "astra_conversation_context.txt"
        context_file.parent.mkdir(parents=True, exist_ok=True)

        with open(context_file, 'w') as f:
            f.write(formatted_context)

        return True
    else:
        print("✅ No previous ASTRA conversation context found - starting fresh session")
        print("   (This is normal for first-time conversations)")
        return False


if __name__ == "__main__":
    main()
