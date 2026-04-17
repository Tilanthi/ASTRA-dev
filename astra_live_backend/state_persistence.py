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
ASTRA Live — State Persistence Module
Saves and restores ASTRA's state across restarts.

This ensures that:
- Active hypotheses are preserved
- Cognitive state is maintained
- Discovery progress continues
- No knowledge is lost on restart
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

STATE_DIR = Path(__file__).parent.parent / "astra_state"
STATE_FILE = STATE_DIR / "engine_state.json"
HYPOTHESES_FILE = STATE_DIR / "hypotheses.json"
COGNITIVE_STATE_FILE = STATE_DIR / "cognitive_state.json"


def ensure_state_dir():
    """Ensure state directory exists."""
    STATE_DIR.mkdir(exist_ok=True)


def save_engine_state(engine):
    """Save engine state to JSON."""
    ensure_state_dir()

    state = {
        "timestamp": time.time(),
        "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cycle_count": engine.cycle_count,
        "total_data_points": engine.total_data_points,
        "total_decisions": engine.total_decisions,
        "system_confidence": engine.system_confidence,
        "current_phase": engine.current_phase,
        "running": engine.running,
        "start_time": engine.start_time,
        "state_vector_history": list(engine.state_vector_history) if engine.state_vector_history else []
    }

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)

    return state


def save_hypotheses(store):
    """Save hypotheses to JSON."""
    ensure_state_dir()

    hypotheses = [h.to_dict() for h in store.hypotheses.values()]

    with open(HYPOTHESES_FILE, 'w') as f:
        json.dump(hypotheses, f, indent=2, default=str)

    return hypotheses


def load_hypotheses(store):
    """
    Load hypotheses from JSON if available.

    CRITICAL FIX: Deduplicates hypotheses by name during loading.
    Keeps the hypothesis with the highest confidence when duplicates are found.
    """
    if not HYPOTHESES_FILE.exists():
        return 0

    with open(HYPOTHESES_FILE, 'r') as f:
        hypotheses_data = json.load(f)

    # Deduplicate by name (case-insensitive)
    # When duplicates exist, keep the one with highest confidence
    seen_names = {}
    for h_dict in hypotheses_data:
        name_key = h_dict.get('name', '').lower().strip()
        if not name_key:
            continue

        # Store by name key, keeping the version with highest confidence
        if name_key not in seen_names:
            seen_names[name_key] = h_dict
        else:
            # Compare confidence - keep the higher one
            existing_conf = seen_names[name_key].get('confidence', 0)
            new_conf = h_dict.get('confidence', 0)
            if new_conf > existing_conf:
                seen_names[name_key] = h_dict

    # Load deduplicated hypotheses
    loaded_count = 0
    skipped_count = 0
    for h_dict in seen_names.values():
        try:
            from .hypotheses import Hypothesis, Phase
            from dataclasses import fields

            # Convert phase string back to enum
            if isinstance(h_dict.get('phase'), str):
                h_dict['phase'] = Phase(h_dict['phase'])

            # Filter out fields that don't exist in Hypothesis class
            # This prevents errors when loading hypotheses with old/extra fields
            valid_fields = {f.name for f in fields(Hypothesis)}
            filtered_h_dict = {k: v for k, v in h_dict.items() if k in valid_fields}

            hypothesis = Hypothesis(**filtered_h_dict)
            store.hypotheses[hypothesis.id] = hypothesis
            loaded_count += 1
        except Exception as e:
            print(f"Error loading hypothesis {h_dict.get('id')}: {e}")

    skipped_count = len(hypotheses_data) - loaded_count
    if skipped_count > 0:
        print(f"State persistence: Skipped {skipped_count} duplicate hypotheses during loading")

    return loaded_count


def save_cognitive_state(cognitive_core):
    """Save cognitive core state."""
    ensure_state_dir()

    if not cognitive_core:
        return

    state = {
        "timestamp": time.time(),
        "cognitive_mode": cognitive_core.current_mode.value if cognitive_core.current_mode else None,
        "perceptions_count": len(cognitive_core.perceptions),
        "insights_count": len(cognitive_core.insights),
        "discoveries_count": len(cognitive_core.discoveries)
    }

    with open(COGNITIVE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def load_engine_state(engine):
    """Load engine state from JSON if available."""
    if not STATE_FILE.exists():
        return False

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    # Restore state
    engine.cycle_count = state.get("cycle_count", 0)
    engine.total_data_points = state.get("total_data_points", 0)
    engine.total_decisions = state.get("total_decisions", 0)
    engine.system_confidence = state.get("system_confidence", 0.0)
    engine.current_phase = state.get("current_phase", "ORIENT")
    engine.start_time = state.get("start_time", time.time())

    return True


def get_state_summary() -> Dict:
    """Get summary of saved state."""
    summary = {
        "state_dir_exists": STATE_DIR.exists(),
        "engine_state_exists": STATE_FILE.exists(),
        "hypotheses_exist": HYPOTHESES_FILE.exists(),
        "cognitive_state_exists": COGNITIVE_STATE_FILE.exists()
    }

    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            engine_state = json.load(f)
            summary["last_saved"] = engine_state.get("iso_timestamp")
            summary["cycle_count"] = engine_state.get("cycle_count")
            summary["hypotheses_count"] = len([h for h in HYPOTHESES_FILE.exists() and json.load(open(HYPOTHESES_FILE)) or []])

    if HYPOTHESES_FILE.exists():
        with open(HYPOTHESES_FILE, 'r') as f:
            hypotheses = json.load(f)
            summary["hypotheses_count"] = len(hypotheses)
            summary["active_hypotheses"] = len([h for h in hypotheses if h.get("phase") not in ["archived", "published"]])

    return summary


def clear_state():
    """Clear all saved state (for reset)."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    if HYPOTHESES_FILE.exists():
        HYPOTHESES_FILE.unlink()
    if COGNITIVE_STATE_FILE.exists():
        COGNITIVE_STATE_FILE.unlink()
