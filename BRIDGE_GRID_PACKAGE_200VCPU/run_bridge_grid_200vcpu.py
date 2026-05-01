#!/usr/bin/env python3
"""
BRIDGE_GRID Campaign - 200 vCPU Execution Script

Addresses Peer Review Issue #3: BRIDGE_GRID contradiction
- Dense sampling of f = 1.1-2.0
- 48 simulations total
- Optimized for 200 vCPU machine

Usage:
    python3 run_bridge_grid_200vcpu.py
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
import multiprocessing as mp

# Configuration
MAX_CONCURRENT = 12          # Max concurrent simulations
CORES_PER_SIM = 16           # MPI ranks per simulation
TOTAL_CPUS = 200             # Total available CPUs
TIMEOUT_MARGIN = 1.2         # 20% margin over config timeout
ATHENA_EXE = "./athena-public-version/bin/athena"

# Paths
CONFIG_DIR = Path("bridge_grid")
OUTPUT_DIR = Path("outputs")
STATUS_FILE = Path("campaign_status.json")
LOG_FILE = Path("campaign.log")


def log(message):
    """Write to log file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")
    sys.stdout.flush()


def load_config(config_path):
    """Load simulation configuration."""
    with open(config_path) as f:
        return json.load(f)


def get_sim_status(sim_id, output_path):
    """Check current status of a simulation."""
    status_file = output_path / "status.json"

    if status_file.exists():
        try:
            with open(status_file) as f:
                data = json.load(f)
                return data.get("status", "UNKNOWN")
        except:
            pass

    # Check for completion indicators
    if (output_path / "final_snapshot.h5").exists():
        return "COMPLETE"
    if (output_path / "FRAG").exists():
        return "FRAG"
    if (output_path / "STABLE").exists():
        return "STABLE"

    # Check for running indicators
    if list(output_path.glob("*.hst")):
        return "RUNNING"

    return "PENDING"


def run_simulation(config_path):
    """Run a single Athena++ simulation."""
    config = load_config(config_path)
    sim_id = config["metadata"]["sim_id"]
    output_path = OUTPUT_DIR / sim_id

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Check if already complete
    status = get_sim_status(sim_id, output_path)
    if status in ["COMPLETE", "FRAG", "STABLE"]:
        log(f"SKIP: {sim_id} already complete ({status})")
        return {"sim_id": sim_id, "status": status, "skipped": True}

    # Check if running
    if status == "RUNNING":
        log(f"SKIP: {sim_id} already running")
        return {"sim_id": sim_id, "status": "RUNNING", "skipped": True}

    log(f"START: {sim_id}")

    # Build Athena++ command
    cmd = [
        "mpirun",
        "-np", str(CORES_PER_SIM),
        ATHENA_EXE,
        "-i", str(config_path),
        ">", str(output_path / "athena.log"),
        "2>&1"
    ]

    # Calculate timeout
    timeout = config.get("numeristics", {}).get("timeout_seconds", 600)
    timeout = int(timeout * TIMEOUT_MARGIN)

    start_time = time.time()

    try:
        # Run simulation
        with open(output_path / "athena.log", "w") as log_f:
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                timeout=timeout,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                cwd=output_path
            )

        elapsed = time.time() - start_time

        # Analyze output
        status = analyze_output(output_path, config)

        log(f"DONE: {sim_id} - {status['status']} ({elapsed:.1f}s)")

        return {
            "sim_id": sim_id,
            "status": status["status"],
            "elapsed_seconds": elapsed,
            "skipped": False,
            "details": status
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        log(f"TIMEOUT: {sim_id} ({elapsed:.1f}s)")
        return {
            "sim_id": sim_id,
            "status": "TIMEOUT",
            "elapsed_seconds": elapsed,
            "skipped": False
        }
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"ERROR: {sim_id} - {e}")
        return {
            "sim_id": sim_id,
            "status": "ERROR",
            "elapsed_seconds": elapsed,
            "error": str(e),
            "skipped": False
        }


def analyze_output(output_path, config):
    """Analyze simulation output to determine status."""
    # Check for HDF5 outputs
    h5_files = list(output_path.glob("*.h5"))

    if not h5_files:
        return {"status": "NO_OUTPUT", "n_hdf5": 0}

    # Read final HST file for basic metrics
    hst_files = sorted(output_path.glob("*.hst"))
    if hst_files:
        try:
            import numpy as np
            hst_data = np.loadtxt(hst_files[-1])

            # Extract basic metrics
            # Assuming format: time, rho_max, dt, ...
            rho_max = hst_data[:, 1].max() if hst_data.shape[1] > 1 else 0
            dt_min = hst_data[:, 2].min() if hst_data.shape[2] > 2 else 0

            # Simple classification
            if rho_max > 100:  # High density = fragmentation
                return {"status": "FRAG", "rho_max": rho_max, "dt_min": dt_min}
            elif dt_min < 1e-10:
                return {"status": "FRAG", "rho_max": rho_max, "dt_min": dt_min}
            else:
                return {"status": "STABLE", "rho_max": rho_max, "dt_min": dt_min}

        except Exception as e:
            return {"status": "ANALYSIS_ERROR", "error": str(e)}

    return {"status": "UNKNOWN", "n_hdf5": len(h5_files)}


def save_campaign_status(statuses):
    """Save overall campaign status."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_simulations": len(statuses),
        "pending": sum(1 for s in statuses if s["status"] == "PENDING"),
        "running": sum(1 for s in statuses if s["status"] == "RUNNING"),
        "complete": sum(1 for s in statuses if s["status"] in ["FRAG", "STABLE", "COMPLETE"]),
        "timeout": sum(1 for s in statuses if s["status"] == "TIMEOUT"),
        "error": sum(1 for s in statuses if s["status"] == "ERROR"),
        "simulations": statuses
    }

    with open(STATUS_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def print_progress(summary):
    """Print progress summary."""
    total = summary["total_simulations"]
    complete = summary["complete"]
    pending = summary["pending"]
    running = summary["running"]

    progress = complete / total * 100

    print("\n" + "="*60)
    print(f"BRIDGE_GRID Campaign Progress: {progress:.1f}%")
    print("="*60)
    print(f"  Complete: {complete}/{total}")
    print(f"  Running:  {running}")
    print(f"  Pending:  {pending}")
    print(f"  Timeout:  {summary['timeout']}")
    print(f"  Error:    {summary['error']}")
    print("="*60 + "\n")


def main():
    """Main execution loop."""
    log("="*60)
    log("BRIDGE_GRID Campaign - 200 vCPU Execution")
    log("="*60)

    # Verify Athena++ executable
    if not os.path.exists(ATHENA_EXE):
        log(f"ERROR: Athena++ not found at {ATHENA_EXE}")
        log("Please run: bash compile_athena.sh")
        sys.exit(1)

    # Load all configs
    config_files = sorted(CONFIG_DIR.glob("*.json"))
    log(f"Found {len(config_files)} simulation configurations")

    if len(config_files) != 48:
        log(f"WARNING: Expected 48 configs, found {len(config_files)}")

    # Initialize output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load existing status if available
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            saved_status = json.load(f)
            log(f"Resuming from previous run")
            log(f"  Previous complete: {saved_status.get('complete', 0)}")
    else:
        saved_status = None

    # Main execution loop
    all_statuses = []

    for config_file in config_files:
        config = load_config(config_file)
        sim_id = config["metadata"]["sim_id"]

        # Check if already done
        output_path = OUTPUT_DIR / sim_id
        existing_status = get_sim_status(sim_id, output_path)

        if existing_status in ["FRAG", "STABLE", "COMPLETE"]:
            all_statuses.append({
                "sim_id": sim_id,
                "status": existing_status,
                "skipped": True
            })
            continue

        # Run simulation
        result = run_simulation(config_file)
        all_statuses.append(result)

        # Save status
        summary = save_campaign_status(all_statuses)
        print_progress(summary)

    # Final summary
    log("="*60)
    log("BRIDGE_GRID Campaign Complete")
    log("="*60)

    final_summary = save_campaign_status(all_statuses)
    print_progress(final_summary)

    # Generate CSV summary
    csv_file = OUTPUT_DIR / "results_summary.csv"
    with open(csv_file, "w") as f:
        f.write("sim_id,status,elapsed_seconds,skipped\n")
        for s in all_statuses:
            f.write(f"{s['sim_id']},{s['status']},{s.get('elapsed_seconds', 0)},{s['skipped']}\n")

    log(f"Results summary saved to: {csv_file}")
    log(f"\nNext step: python3 analyze_results.py")

    return final_summary


if __name__ == "__main__":
    main()
