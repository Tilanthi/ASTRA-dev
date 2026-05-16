#!/usr/bin/env python3
"""
Modify HGBS Discovery Scripts to Use Persistence Threshold >= 50

This script modifies the phase scripts to use a persistence threshold of 50
instead of > 0 when creating filament masks from the skeleton map.
"""

import re
from pathlib import Path

# Configuration
PERSISTENCE_THRESHOLD = 50
HGBS_DIR = "/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB"

# Scripts to modify
scripts_to_modify = [
    "hgbs_discovery_phase2.py",
    "hgbs_discovery_phase3.py",
    "hgbs_discovery_phase4.py"
]

def modify_script(script_path, threshold):
    """Modify a script to use the specified persistence threshold."""
    print(f"\nModifying {script_path.name}...")

    with open(script_path, 'r') as f:
        content = f.read()

    original_content = content

    # 1. Add threshold constant after HGBS_DIR definition
    threshold_const = f"PERSISTENCE_THRESHOLD = {threshold}\n"

    # Find the HGBS_DIR line and add threshold after it
    pattern = r"(HGBS_DIR = '[^']+'\n)"
    replacement = r"\1" + threshold_const

    if "PERSISTENCE_THRESHOLD" not in content:
        content = re.sub(pattern, replacement, content)
        print(f"  Added PERSISTENCE_THRESHOLD = {threshold}")

    # 2. Replace skeleton threshold conditions
    # Pattern: self.skel_data > 0
    old_pattern = r"self\.skel_data > 0"
    new_pattern = f"self.skel_data >= {threshold}"

    matches = re.findall(old_pattern, content)
    if matches:
        content = re.sub(old_pattern, new_pattern, content)
        print(f"  Changed {len(matches)} occurrence(s): skel_data > 0 → skel_data >= {threshold}")

    # 3. Update comments if present
    content = re.sub(
        r"# Create boolean mask of filament pixels",
        f"# Create boolean mask of filament pixels (persistence >= {threshold})",
        content
    )

    # Only write if changes were made
    if content != original_content:
        # Write modified script
        backup_path = script_path.with_suffix('.py.bak_original')
        with open(backup_path, 'w') as f:
            f.write(original_content)
        print(f"  Backed up original to {backup_path.name}")

        with open(script_path, 'w') as f:
            f.write(content)
        print(f"  Modified script saved")
        return True
    else:
        print(f"  No changes needed")
        return False

def main():
    """Main function."""
    print("="*70)
    print("MODIFYING HGBS DISCOVERY SCRIPTS")
    print(f"New Persistence Threshold: >= {PERSISTENCE_THRESHOLD}")
    print("="*70)

    modified_count = 0

    for script_name in scripts_to_modify:
        script_path = Path(HGBS_DIR) / script_name

        if not script_path.exists():
            print(f"\nWARNING: {script_name} not found in {HGBS_DIR}")
            continue

        if modify_script(script_path, PERSISTENCE_THRESHOLD):
            modified_count += 1

    print("\n" + "="*70)
    print(f"MODIFICATION COMPLETE: {modified_count} script(s) modified")
    print("="*70)

    print("\nChanges made:")
    print(f"  - Added PERSISTENCE_THRESHOLD = {PERSISTENCE_THRESHOLD} constant")
    print(f"  - Changed filament_mask conditions to use >= {PERSISTENCE_THRESHOLD}")
    print("\nNext steps:")
    print(f"  1. Review modified scripts")
    print(f"  2. Run phases: python run_all_phases.py {HGBS_DIR} Orion")
    print(f"  3. Compare results with original_results/")

if __name__ == "__main__":
    main()
