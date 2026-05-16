#!/usr/bin/env python3
"""
CTZM Campaign Launcher - Ray Distributed Task Scheduler
========================================================

Launches 96 Athena++ simulations for Critical Transition Zone Mapping campaign.
Configured for astra-climate Google Cloud E2 instances (220 vCPUs).

Usage:
    python ctzm_launcher.py --config ctzm_config.json

Author: ASTRA Autonomous System
Date: 2026-05-13
"""

import ray
import subprocess
import json
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ctzm_launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================================================================
# CTZM Configuration
# ======================================================================

CTZM_CONFIG = {
    "infrastructure": {
        "platform": "astra-climate",
        "num_cpus": 220,
        "concurrent_sims": 6,
        "mpi_ranks_per_sim": 32,
        "memory_per_sim_gb": 8,
        "timeout_sec": 14400,  # 4 hours
    },
    "simulation": {
        "binary_path": "./athena_ic",
        "domain": "256x64x64",
        "geometry": "slab",
        "boundary": "periodic",
        "eos": "isothermal",
        "cs": 1.0,
        "gamma": 1.0,
    },
    "output": {
        "hdf5_interval": "0.02",  # Output every 0.02 tJ
        "max_snapshots": 200,
        "restart_file": False,
    }
}

# ======================================================================
# Parameter Grid Generation
# ======================================================================

def generate_parameter_grid() -> List[Dict[str, Any]]:
    """
    Generate full parameter space for CTZM campaign.

    Returns:
        List of parameter dictionaries, one per simulation
    """
    grid = []

    # Parameter space
    f_values = [1.2, 1.3, 1.4, 1.5]
    beta_values = [0.3, 0.5, 1.0, 2.0]
    mach_values = [1.0, 2.0]
    seeds = [0, 1, 2]

    sim_id = 0
    for f in f_values:
        for beta in beta_values:
            for mach in mach_values:
                for seed in seeds:
                    grid.append({
                        "sim_id": f"f{f:.1f}_b{beta:.1f}_M{mach:.1f}_s{seed}",
                        "f": f,
                        "beta": beta,
                        "mach": mach,
                        "seed": seed,
                        "output_dir": f"output_ctzm/{sim_id:04d}_{f:.1f}_{beta:.1f}_{mach:.1f}_{seed}",
                    })
                    sim_id += 1

    logger.info(f"Generated parameter grid: {len(grid)} simulations")
    return grid


# ======================================================================
# Athena++ Input File Generation
# ======================================================================

def create_athena_input(sim_params: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Generate Athena++ input file for a single simulation.

    Args:
        sim_params: Simulation parameters (f, beta, mach, seed, output_dir)
        config: CTZM configuration dictionary

    Returns:
        Path to generated input file
    """
    output_dir = Path(sim_params["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = output_dir / "athena_input.txt"

    input_content = f"""<job>
job_id      = {sim_params["sim_id"]}

<problem>
problem_id   = ctzm_filament

# CTZM campaign parameters
f_ratio      = {sim_params["f"]}
beta         = {sim_params["beta"]}
mach         = {sim_params["mach"]}
seed         = {sim_params["seed"]}
</problem>

<mesh>
nx1          = {config["simulation"]["domain"].split('x')[0]}
nx2          = {config["simulation"]["domain"].split('x')[1]}
nx3          = {config["simulation"]["domain"].split('x')[2]}
x1min        = 0.0
x1max        = 8.0
x2min        = -1.0
x2max        = 1.0
x3min        = -1.0
x3max        = 1.0
ix1_bc       = periodic
ox1_bc       = periodic
ix2_bc       = periodic
ox2_bc       = periodic
ix3_bc       = periodic
ox3_bc       = periodic
</mesh>

<hydro>
hydro        = eos
iso_sound_speed = {config["simulation"]["cs"]}
gamma        = {config["simulation"]["gamma"]}
R_gas        = 1.0
dfloor       = 1.0e-12
</hydro>

<field>
mag_field    = yes
b_flag       = 1
b_flag_ib    = 0
x1order      = 4
x2order      = 4
x3order      = 4
</field>

<gravity>
gravity      = fft
transpose_fft = false
gravity_mean_rho = 1.0
four_pi_G    = 39.4784176
</gravity>

<time>
nlim         = 1.0e8
tlim         = 4.0
dt_watchdog  = 1.0e-8
</time>

<output1>
out_fmt      = 24
dt           = {config["output"]["hdf5_interval"]}
data_format  = %12.5e
variable     = cons
file_num     = 0
file_sfre    = full
</output1>

<output2>
out_fmt      = 1
dt           = 0.1
variable     = prim
file_num     = 0
</output2>

<output3>
out_fmt      = 2
dt           = 0.1
variable     = cons
file_num     = 0
</output3>

<meshblock>
lx1          = 2
lx2          = 2
lx3          = 2
</meshblock>

<par>
nproc        = 32
nproc_x      = 8
nproc_y      = 2
nproc_z      = 2
</par>
"""

    with open(input_path, 'w') as f:
        f.write(input_content)

    return str(input_path)


# ======================================================================
# Ray Remote Execution Function
# ======================================================================

@ray.remote(num_cpus=32, max_calls=1)
def run_single_simulation(sim_params: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single Athena++ simulation via MPI.

    Args:
        sim_params: Simulation parameters
        config: CTZM configuration

    Returns:
        Result dictionary with exit status, timing, and metadata
    """
    import subprocess
    import time
    from pathlib import Path

    start_time = time.time()

    # Create output directory and input file
    input_path = create_athena_input(sim_params, config)
    output_dir = Path(sim_params["output_dir"])

    # Log file path
    log_path = output_dir / "simulation.log"

    # MPI command
    mpi_cmd = [
        "mpirun",
        "-np", str(config["infrastructure"]["mpi_ranks_per_sim"]),
        config["simulation"]["binary_path"],
        "-i", input_path,
        "-d", str(output_dir)
    ]

    # Run simulation
    try:
        with open(log_path, 'w') as log_file:
            result = subprocess.run(
                mpi_cmd,
                capture_output=True,
                text=True,
                timeout=config["infrastructure"]["timeout_sec"],
                cwd=str(output_dir)
            )

            # Write output to log file
            log_file.write("=== STDOUT ===\n")
            log_file.write(result.stdout)
            log_file.write("\n=== STDERR ===\n")
            log_file.write(result.stderr)

        # Check for fragmentation in output
        # (Athens++ writes "FRAGMENTATION DETECTED" to stdout)
        fragmented = "FRAGMENTATION DETECTED" in result.stdout or "dt_watchdog" in result.stderr

        return {
            "sim_id": sim_params["sim_id"],
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode,
            "fragmented": fragmented,
            "wall_time_sec": time.time() - start_time,
            "output_dir": str(output_dir),
            "log_file": str(log_path),
        }

    except subprocess.TimeoutExpired:
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n=== TIMEOUT AFTER {config['infrastructure']['timeout_sec']} seconds ===\n")

        return {
            "sim_id": sim_params["sim_id"],
            "status": "TIMEOUT",
            "exit_code": -1,
            "fragmented": False,
            "wall_time_sec": config["infrastructure"]["timeout_sec"],
            "output_dir": str(output_dir),
            "log_file": str(log_path),
        }

    except Exception as e:
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n=== EXCEPTION: {str(e)} ===\n")

        return {
            "sim_id": sim_params["sim_id"],
            "status": "EXCEPTION",
            "exit_code": -999,
            "fragmented": False,
            "wall_time_sec": time.time() - start_time,
            "output_dir": str(output_dir),
            "log_file": str(log_path),
            "error": str(e),
        }


# ======================================================================
# Main Execution Function
# ======================================================================

def run_ctzm_campaign(config: Dict[str, Any]) -> None:
    """
    Execute full CTZM campaign using Ray distributed scheduling.

    Args:
        config: CTZM configuration dictionary
    """
    # Initialize Ray
    logger.info("Initializing Ray cluster...")
    ray.init(
        num_cpus=config["infrastructure"]["num_cpus"],
        logging_level=logging.INFO,
    )

    # Generate parameter grid
    logger.info("Generating parameter grid...")
    parameter_grid = generate_parameter_grid()

    # Save parameter grid for reference
    grid_path = Path("ctzm_parameter_grid.json")
    with open(grid_path, 'w') as f:
        json.dump(parameter_grid, f, indent=2)
    logger.info(f"Parameter grid saved to {grid_path}")

    # Check binary exists
    if not Path(config["simulation"]["binary_path"]).exists():
        logger.error(f"Binary not found: {config['simulation']['binary_path']}")
        logger.error("Please compile Athena++ first using: ./compile_athena_ic.sh")
        ray.shutdown()
        sys.exit(1)

    # Launch all simulations via Ray
    logger.info(f"Launching {len(parameter_grid)} simulations...")
    logger.info(f"Concurrent simulations: {config['infrastructure']['concurrent_sims']}")

    pending_refs = []
    results = []

    for sim_params in parameter_grid:
        # Submit simulation to Ray
        ref = run_single_simulation.remote(sim_params, config)
        pending_refs.append(ref)

        # Limit concurrency by waiting when we hit the limit
        while len(pending_refs) >= config["infrastructure"]["concurrent_sims"]:
            # Wait for at least one to complete
            ready_refs, pending_refs = ray.wait(pending_refs, num_returns=1)
            for ref in ready_refs:
                result = ray.get(ref)
                results.append(result)
                logger.info(
                    f"Completed: {result['sim_id']} | "
                    f"Status: {result['status']} | "
                    f"Time: {result['wall_time_sec']:.1f}s | "
                    f"Fragmented: {result['fragmented']}"
                )

    # Wait for remaining simulations to complete
    logger.info("Waiting for remaining simulations...")
    while pending_refs:
        ready_refs, pending_refs = ray.wait(pending_refs, num_returns=len(pending_refs))
        for ref in ready_refs:
            result = ray.get(ref)
            results.append(result)
            logger.info(
                f"Completed: {result['sim_id']} | "
                f"Status: {result['status']} | "
                f"Time: {result['wall_time_sec']:.1f}s | "
                f"Fragmented: {result['fragmented']}"
            )

    # Shutdown Ray
    ray.shutdown()

    # Compile results summary
    logger.info("Compiling results summary...")
    summary = {
        "campaign": "CTZM - Critical Transition Zone Mapping",
        "date": datetime.now().isoformat(),
        "total_sims": len(parameter_grid),
        "completed": len([r for r in results if r["status"] == "SUCCESS"]),
        "failed": len([r for r in results if r["status"] == "FAILED"]),
        "timeout": len([r for r in results if r["status"] == "TIMEOUT"]),
        "fragmented": len([r for r in results if r["fragmented"]]),
        "results": results,
    }

    # Save results
    results_path = Path("ctzm_results.json")
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Results saved to {results_path}")

    # Print summary
    logger.info("=" * 60)
    logger.info("CTZM CAMPAIGN COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Total simulations: {summary['total_sims']}")
    logger.info(f"Successful: {summary['completed']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Timeout: {summary['timeout']}")
    logger.info(f"Fragmented: {summary['fragmented']}")
    logger.info("=" * 60)


# ======================================================================
# Main Entry Point
# ======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CTZM Campaign Launcher")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON configuration file (overrides defaults)"
    )
    parser.add_argument(
        "--binary",
        type=str,
        default="./athena_ic",
        help="Path to Athena++ binary"
    )

    args = parser.parse_args()

    # Load custom config if provided
    if args.config:
        with open(args.config, 'r') as f:
            custom_config = json.load(f)
        CTZM_CONFIG.update(custom_config)

    # Override binary path if specified
    if args.binary:
        CTZM_CONFIG["simulation"]["binary_path"] = args.binary

    # Run campaign
    try:
        run_ctzm_campaign(CTZM_CONFIG)
    except KeyboardInterrupt:
        logger.warning("Campaign interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Campaign failed: {e}")
        sys.exit(1)
