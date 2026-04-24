#!/usr/bin/env python3
"""
Extract t_frag from Simulation History Files

Analyzes Athena++ history (.hst) files to extract fragmentation times
and classify simulation outcomes (FRAG, STABLE, TIMEOUT).
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
HST_DIR = "../output/simulations"
STATUS_DIR = "../output/status"
OUTPUT_DIR = "../output/analysis"

def parse_history_file(hst_path: str) -> Dict:
    """
    Parse Athena++ history file and extract fragmentation information.

    Parameters:
    -----------
    hst_path : str
        Path to .hst file

    Returns:
    --------
    result : dict
        Dictionary with keys: status, t_frag, t_final, dt_min, n_steps
    """
    if not os.path.exists(hst_path):
        return {"error": f"History file not found: {hst_path}"}

    try:
        # Read history file
        data = np.loadtxt(hst_path, comments='#')

        # Extract columns (typical Athena++ HST format)
        # Columns: time, dt, mass, momentum, energy, maxbeta, minbeta, etc.
        time = data[:, 1]      # Simulation time in t_J units
        dt = data[:, -1]       # Minimum timestep (usually last column)

        # Find fragmentation (runaway collapse criterion)
        # dt_min < 1e-8 indicates Jeans collapse
        frag_mask = dt < 1e-8

        if np.any(frag_mask):
            # Fragmentation detected
            frag_idx = np.where(frag_mask)[0][0]
            t_frag = time[frag_idx]
            dt_min = dt[frag_idx]
            t_final = time[-1]
            status = "FRAG"
        else:
            # No fragmentation detected
            t_frag = None
            dt_min = dt[-1]
            t_final = time[-1]
            status = "STABLE"

        return {
            "status": status,
            "t_frag": t_frag,
            "t_final": float(t_final),
            "dt_min": float(dt_min),
            "n_steps": len(time)
        }

    except Exception as e:
        return {"error": f"Failed to parse {hst_path}: {str(e)}"}

def extract_all_tfrag() -> List[Dict]:
    """
    Extract t_frag from all simulation history files.

    Returns:
    --------
    results : list of dict
        List of extraction results for each simulation
    """
    results = []

    # Find all .hst files
    sim_dir = Path(HST_DIR)
    if not sim_dir.exists():
        print(f"Warning: Simulation directory not found: {HST_DIR}")
        return results

    hst_files = list(sim_dir.glob("*/ *.hst"))

    print(f"Found {len(hst_files)} history files")

    for hst_file in hst_files:
        run_id = hst_file.parent.name

        # Parse history file
        result = parse_history_file(str(hst_file))

        if "error" in result:
            print(f"Warning: {result['error']}")
            continue

        # Add run_id to result
        result["run_id"] = run_id
        results.append(result)

        print(f"  {run_id}: {result['status']}, t_frag={result['t_frag']:.3f}" if result['t_frag'] else f"  {run_id}: {result['status']}")

    return results

def update_status_files(results: List[Dict]):
    """Update status JSON files with extracted t_frag values."""
    for result in results:
        run_id = result['run_id']
        status_file = os.path.join(STATUS_DIR, f"status_{run_id}.json")

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)

            # Update with extracted values
            status_data['t_frag'] = result['t_frag']
            status_data['t_final'] = result['t_final']
            status_data['dt_min'] = result['dt_min']
            status_data['status'] = result['status']

            # Write back
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)

def main():
    """Main extraction workflow."""
    print("Extracting t_frag from history files")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Extract t_frag from all history files
    results = extract_all_tfrag()

    if not results:
        print("No results extracted. Check that simulations have completed.")
        sys.exit(1)

    # Update status files
    print("\nUpdating status files...")
    update_status_files(results)

    # Save extraction results
    output_path = os.path.join(OUTPUT_DIR, "tfrag_extractions.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path}")

    # Summary statistics
    frag_count = sum(1 for r in results if r['status'] == 'FRAG')
    stable_count = sum(1 for r in results if r['status'] == 'STABLE')

    print(f"\nSummary:")
    print(f"  Total simulations: {len(results)}")
    print(f"  FRAG: {frag_count}")
    print(f"  STABLE: {stable_count}")

    if frag_count > 0:
        t_frag_values = [r['t_frag'] for r in results if r['status'] == 'FRAG']
        print(f"  Mean t_frag: {np.mean(t_frag_values):.3f} +/- {np.std(t_frag_values):.3f} t_J")

    print("\nExtraction complete!")

if __name__ == "__main__":
    main()
