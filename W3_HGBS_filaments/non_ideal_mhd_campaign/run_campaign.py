#!/usr/bin/env python3
"""
Non-Ideal MHD Campaign: Ambipolar Diffusion and Supercritical Filament Fragmentation
Execute on: External 200 CPU Ray cluster
"""

import ray
from pathlib import Path
import json
import subprocess
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('campaign.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Load campaign configuration
CONFIG_PATH = Path(__file__).parent / "config.json"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)

# Ray cluster configuration
RAY_NUM_CPUS = CONFIG["ray_config"]["num_cpus"]
RAY_DASHBOARD_PORT = CONFIG["ray_config"]["dashboard_port"]
MAX_CONCURRENT_SIMS = CONFIG["ray_config"]["max_concurrent_sims"]

# Athena++ binary path
ATHENA_BINARY = "/path/to/athena++/bin/athena_pg"  # USER MUST UPDATE THIS PATH

# Output directory
OUTPUT_BASE = Path(CONFIG["output_directory"])
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Simulation Generator
# ============================================================================

def generate_simulation_configs() -> List[Dict[str, Any]]:
    """Generate all simulation configurations from the parameter grid."""
    configs = []
    sim_id = 0

    grid = CONFIG["parameter_grid"]

    for f in grid["line_mass_fraction"]:
        for beta in grid["plasma_beta"]:
            for mach in grid["mach_number"]:
                for Am in grid["ambipolar_number_Am"]:
                    for seed in grid["random_seeds"]:

                        # Calculate ambipolar diffusion coefficient
                        # eta_A = Am * c_s * lambda_J / (2*pi) in code units
                        eta_A = Am * 1.0 * 1.0 / (2.0 * np.pi)

                        config = {
                            "sim_id": f"nonideal_{sim_id:03d}",
                            "sim_id_num": sim_id,
                            "line_mass_fraction": f,
                            "plasma_beta": beta,
                            "mach_number": mach,
                            "ambipolar_number_Am": Am,
                            "eta_A": eta_A,
                            "random_seed": seed,
                            "campaign": CONFIG["campaign_name"],
                            "athena_config": CONFIG["athena_config"].copy()
                        }

                        configs.append(config)
                        sim_id += 1

    logger.info(f"Generated {len(configs)} simulation configurations")
    return configs

# ============================================================================
# Ray Remote Function for Single Simulation
# ============================================================================

@ray.remote(num_cpus=1, max_calls=1)
def run_single_simulation(config: Dict[str, Any], athena_binary: str,
                         output_dir: Path) -> Dict[str, Any]:
    """
    Run a single Athena++ simulation.

    Parameters
    ----------
    config : dict
        Simulation configuration
    athena_binary : str
        Path to Athena++ binary
    output_dir : Path
        Output directory for this simulation

    Returns
    -------
    result : dict
        Simulation result with status and metadata
    """
    import subprocess
    import time
    from pathlib import Path

    sim_dir = output_dir / config["sim_id"]
    sim_dir.mkdir(parents=True, exist_ok=True)

    # Write Athena++ input file
    input_file = sim_dir / "athena_pp.in"
    write_athena_input(input_file, config)

    # Run simulation
    start_time = time.time()

    try:
        result = subprocess.run(
            [athena_binary, "-i", str(input_file)],
            cwd=str(sim_dir),
            capture_output=True,
            text=True,
            timeout=config["athena_config"]["max_wall_time_seconds"]
        )

        wall_time = time.time() - start_time

        # Check if simulation completed successfully
        success = (result.returncode == 0)

        # Parse output for key metrics
        t_frag = parse_fragmentation_time(sim_dir)

        return {
            "sim_id": config["sim_id"],
            "params": config,
            "status": "COMPLETE" if success else "FAILED",
            "wall_time_seconds": wall_time,
            "t_frag": t_frag,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-1000:] if result.stdout else "",
            "stderr_tail": result.stderr[-1000:] if result.stderr else ""
        }

    except subprocess.TimeoutExpired:
        wall_time = time.time() - start_time
        return {
            "sim_id": config["sim_id"],
            "params": config,
            "status": "TIMEOUT",
            "wall_time_seconds": wall_time,
            "t_frag": None,
            "error": "Simulation exceeded maximum wall time"
        }
    except Exception as e:
        wall_time = time.time() - start_time
        return {
            "sim_id": config["sim_id"],
            "params": config,
            "status": "ERROR",
            "wall_time_seconds": wall_time,
            "t_frag": None,
            "error": str(e)
        }

def write_athena_input(input_file: Path, config: Dict[str, Any]) -> None:
    """Write Athena++ input file from configuration."""

    ac = config["athena_config"]

    input_content = f"""<job>
problem_id = {ac['problem_generator']}

<time>
tlim = {ac['max_wall_time_seconds'] * 0.00001}  # Convert to code time units
nlim = 1000000
dt_parabolic_reduce = 0.5

<mesh>
nx1 = {ac['resolution'][0]}
nx2 = {ac['resolution'][1]}
nx3 = {ac['resolution'][2]}
x1min = -{ac['domain_size_lambda_j'][0] / 2}
x1max = {ac['domain_size_lambda_j'][0] / 2}
x2min = -{ac['domain_size_lambda_j'][1] / 2}
x2max = {ac['domain_size_lambda_j'][1] / 2}
x3min = -{ac['domain_size_lambda_j'][2] / 2}
x3max = {ac['domain_size_lambda_j'][2] / 2}
mb_flag = uniform
num_meshblocks_x1 = 8
num_meshblocks_x2 = 2
num_meshblocks_x3 = 2}

<hydro>
iso_sound_speed = 1.0

<mhd>
ambipolar_diffusion = {str(ac['ambipolar_diffusion']).lower()}
eta_A_0 = {config['eta_A']:.6e}
eta_O_0 = 0.0
eta_H_0 = 0.0

<gravity>
grav_field_type = fft
four_pi_G = {ac['four_pi_g']}

<problem>
filament_line_mass = {config['line_mass_fraction']}
filament_beta = {config['plasma_beta']}
filament_mach = {config['mach_number']}
random_seed = {config['random_seed']}

<output>
file_type = hst
dt = {ac['output_cadence_tj']}
variable = u, b1, b2, b3, rho
file_type = hdf5
variable = prim
dt = {ac['output_cadence_tj']}
include_ghost_zones = false
output_sum = 0  # Disable summary output for large simulations

<time>
cfl_number = {ac.get('cfl_number', 0.35)}
"""

    with open(input_file, 'w') as f:
        f.write(input_content)

def parse_fragmentation_time(sim_dir: Path) -> float:
    """Parse fragmentation time from simulation output."""
    # Look for timestep dropping below threshold
    stat_file = sim_dir / "stat.dat"

    if not stat_file.exists():
        return None

    try:
        data = np.loadtxt(stat_file)
        # Column 0 is time, column containing dt
        # Find where dt < 1e-8
        dt_col = -1  # Usually last column

        for i in range(data.shape[1]):
            if np.any(data[:, i] < 1e-6):
                dt_col = i
                break

        if dt_col >= 0:
            frag_times = data[data[:, dt_col] < 1e-8, 0]
            if len(frag_times) > 0:
                return float(frag_times[0])

        return None
    except:
        return None

# ============================================================================
# Campaign Scheduler
# ============================================================================

def run_campaign(sim_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the full simulation campaign using Ray.

    Parameters
    ----------
    sim_configs : list of dict
        All simulation configurations

    Returns
    -------
    results : dict
        Campaign results with all simulation outputs
    """
    logger.info(f"Starting campaign with {len(sim_configs)} simulations")
    logger.info(f"Max concurrent simulations: {MAX_CONCURRENT_SIMS}")

    # Submit all simulations as Ray tasks
    futures = []
    for config in sim_configs:
        future = run_single_simulation.remote(
            config,
            ATHENA_BINARY,
            OUTPUT_BASE
        )
        futures.append(future)

    # Monitor progress
    completed = 0
    results = {}
    start_time = datetime.now()

    logger.info(f"Campaign started at {start_time}")

    # Wait for simulations to complete (in batches)
    batch_size = MAX_CONCURRENT_SIMS

    for i in range(0, len(futures), batch_size):
        batch = futures[i:i+batch_size]
        logger.info(f"Waiting for batch {i//batch_size + 1}/{(len(futures)-1)//batch_size + 1}")

        # Get results for this batch
        batch_results = ray.get(batch)

        for result in batch_results:
            results[result["sim_id"]] = result
            completed += 1

            status = result["status"]
            logger.info(f"[{completed}/{len(sim_configs)}] {result['sim_id']}: {status}")

        # Save checkpoint
        save_checkpoint(results, completed, len(sim_configs))

    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 3600

    logger.info(f"Campaign completed in {duration:.2f} hours")

    # Generate summary statistics
    summary = generate_summary(results)

    return {
        "results": results,
        "summary": summary,
        "campaign_config": CONFIG,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_hours": duration
    }

def save_checkpoint(results: Dict[str, Any], completed: int, total: int) -> None:
    """Save intermediate checkpoint of results."""
    checkpoint_file = OUTPUT_BASE / f"checkpoint_{completed}.json"

    checkpoint_data = {
        "completed": completed,
        "total": total,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }

    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_data, f, indent=2, default=str)

    logger.info(f"Checkpoint saved: {checkpoint_file}")

def generate_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics from campaign results."""

    status_counts = {}
    t_frag_by_Am = {}
    t_frag_by_f = {}

    for sim_id, result in results.items():
        # Count statuses
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

        # Collect t_frag by Am
        if result["t_frag"] is not None:
            Am = result["params"]["ambipolar_number_Am"]
            f = result["params"]["line_mass_fraction"]

            if Am not in t_frag_by_Am:
                t_frag_by_Am[Am] = []
            t_frag_by_Am[Am].append(result["t_frag"])

            if f not in t_frag_by_f:
                t_frag_by_f[f] = []
            t_frag_by_f[f].append(result["t_frag"])

    summary = {
        "total_simulations": len(results),
        "status_counts": status_counts,
        "success_rate": status_counts.get("COMPLETE", 0) / len(results) * 100,
        "t_frag_by_Am": {
            Am: np.mean(vals) if vals else None
            for Am, vals in t_frag_by_Am.items()
        },
        "t_frag_by_f": {
            f: np.mean(vals) if vals else None
            for f, vals in t_frag_by_f.items()
        }
    }

    return summary

# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main entry point for campaign execution."""

    # Initialize Ray
    logger.info(f"Initializing Ray with {RAY_NUM_CPUS} CPUs")
    ray.init(
        num_cpus=RAY_NUM_CPUS,
        dashboard_port=RAY_DASHBOARD_PORT,
        ignore_reinit_error=True
    )

    # Generate simulation configurations
    sim_configs = generate_simulation_configs()

    # Run campaign
    campaign_results = run_campaign(sim_configs)

    # Save final results
    results_file = OUTPUT_BASE / "results.json"
    with open(results_file, 'w') as f:
        json.dump(campaign_results, f, indent=2, default=str)

    logger.info(f"Results saved to {results_file}")

    # Shutdown Ray
    ray.shutdown()

    logger.info("Campaign execution complete!")

    return campaign_results

if __name__ == "__main__":
    main()
