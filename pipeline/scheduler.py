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
ASTRA Autonomous Scheduler
Keeps the research agent running on a continuous loop.
Integrates with Taurus for orchestration.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/shared/ASTRA")
SCHEDULE_STATE = BASE / "config" / "schedule_state.json"
LOG_DIR = BASE / "logs"

DEFAULT_INTERVAL_MINUTES = 30
MAX_CYCLES_PER_SESSION = 48  # 24 hours at 30-min intervals

def load_state():
    if SCHEDULE_STATE.exists():
        return json.loads(SCHEDULE_STATE.read_text())
    return {
        "total_cycles": 0,
        "session_cycles": 0,
        "last_cycle": None,
        "interval_minutes": DEFAULT_INTERVAL_MINUTES,
        "status": "active",
        "created": datetime.now(timezone.utc).isoformat()
    }

def save_state(state):
    SCHEDULE_STATE.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_STATE.write_text(json.dumps(state, indent=2))

def log_event(event_type, details=""):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    month_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m')}-scheduler.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n## {timestamp} — {event_type}\n{details}\n"
    with open(month_file, "a") as f:
        f.write(entry)

def get_queue_status():
    """Check how many hypotheses are pending."""
    queue_file = BASE / "hypotheses" / "QUEUE.md"
    if not queue_file.exists():
        return 0
    content = queue_file.read_text()
    return content.count("Status**: pending")

def get_cycle_count():
    """Count completed cycles from run log."""
    log_file = LOG_DIR / "2026-04.md"
    if not log_file.exists():
        return 0
    content = log_file.read_text()
    return content.count("UTC — ")  # rough count of logged events

def should_run(state):
    """Determine if a new cycle should be triggered."""
    if state["status"] != "active":
        return False
    if state["session_cycles"] >= MAX_CYCLES_PER_SESSION:
        return False
    
    if state["last_cycle"] is None:
        return True
    
    last_str = state["last_cycle"].replace("Z", "+00:00")
    last = datetime.fromisoformat(last_str)
    now = datetime.now(timezone.utc)
    elapsed = (now - last).total_seconds() / 60
    return elapsed >= state["interval_minutes"]

def main():
    state = load_state()
    pending = get_queue_status()
    total = get_cycle_count()
    
    print(f"ASTRA Scheduler — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Status: {state['status']}")
    print(f"  Total cycles: {total}")
    print(f"  Session cycles: {state['session_cycles']}/{MAX_CYCLES_PER_SESSION}")
    print(f"  Pending hypotheses: {pending}")
    print(f"  Interval: {state['interval_minutes']} minutes")
    
    if should_run(state):
        print("  → Triggering new research cycle")
        log_event("SCHEDULE_TRIGGER", f"Cycle #{total + 1}, {pending} hypotheses pending")
        
        # Update state
        state["last_cycle"] = datetime.now(timezone.utc).isoformat()
        state["total_cycles"] += 1
        state["session_cycles"] += 1
        save_state(state)
        
        return True  # Signal that a cycle should be triggered
    else:
        if state["session_cycles"] >= MAX_CYCLES_PER_SESSION:
            print("  → Session limit reached, waiting for reset")
        else:
            if state["last_cycle"]:
                last_str = state["last_cycle"].replace("Z", "+00:00")
                last = datetime.fromisoformat(last_str)
                elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60
                remaining = state["interval_minutes"] - elapsed
                print(f"  → Next cycle in {remaining:.1f} minutes")
        return False

if __name__ == "__main__":
    should_trigger = main()
    exit(0 if should_trigger else 1)
