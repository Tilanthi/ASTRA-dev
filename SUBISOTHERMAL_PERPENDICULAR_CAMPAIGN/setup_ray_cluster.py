#!/usr/bin/env python3
"""
Ray cluster setup for Sub-Isothermal Perpendicular Field Campaign

This script sets up and manages the Ray cluster for running 72 Athena++ simulations
to resolve the Planck mixture calculation uncertainty.

Usage:
    python setup_ray_cluster.py --cluster_config <config.yaml> --sim_params simulation_parameters.csv
    python setup_ray_cluster.py --run  # Run simulations directly
"""

import os
import sys
import argparse
import subprocess
import pandas as pd
import yaml
import ray
from ray.util.queue import Queue
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RayClusterConfig:
    """Configuration for Ray cluster setup"""

    def __init__(self, config_path=None):
        if config_path:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = self._default_config()

        self.cluster_id = config.get('cluster_id', 'subiso-perp-campaign')
        self.num_workers = config.get('num_workers', 220)
        self.cpus_per_worker = config.get('cpus_per_worker', 1)
        self.memory_per_worker_gb = config.get('memory_per_worker_gb', 8)
        self.object_store_memory_gb = config.get('object_store_memory_gb', 100)
        self.ray_temp_dir = config.get('ray_temp_dir', '/tmp/ray')
        self.dashboard_port = config.get('dashboard_port', 8265)

    def _default_config(self):
        return {
            'cluster_id': 'subiso-perp-campaign',
            'num_workers': 220,
            'cpus_per_worker': 1,
            'memory_per_worker_gb': 8,
            'object_store_memory_gb': 100,
            'ray_temp_dir': '/tmp/ray',
            'dashboard_port': 8265,
            'athena_executable': 'athena',
            'athena_container': None,
            'output_base_dir': './simulation_output',
            'max_concurrent_jobs': 36,  # Run 36 sims at once (2 per worker)
            'checkpoint_interval': 3600,  # Checkpoint every hour
        }


class SimulationJob:
    """Athena++ simulation job"""

    def __init__(self, sim_id, params, config):
        self.sim_id = sim_id
        self.params = params
        self.config = config
        self.status = 'pending'
        self.start_time = None
        self.end_time = None
        self.output_dir = None
        self.error = None

    def get_athena_command(self, athena_bin='athena'):
        """Generate Athena++ command line"""

        # Extract parameters
        f = self.params['f']
        beta = self.params['beta']
        gamma = self.params['gamma']
        seed = self.params['seed']
        theta = self.params['theta']
        mach = self.params['mach']
        res = int(self.params['resolution'])

        # Calculate filament properties
        # Reference: standard filament campaign setup
        rho_0 = 1.0  # Normalized density
        c_s_iso = 1.0  # Isothermal sound speed
        p_eq = rho_0 * c_s_iso**2

        # Adjust for gamma
        if gamma < 1.0:
            # Polytropic EOS: P = K * rho^gamma
            K = p_eq / (rho_0 ** gamma)
        else:
            K = p_eq / rho_0

        # Critical mass-per-unit-length (normalized)
        mline_crit = 1.0
        mline = f * mline_crit

        # Cylinder radius for line mass mline
        # From mline = pi * r^2 * rho_0
        radius = (mline / (np.pi * rho_0))**0.5

        # Domain size
        L_x = 4.0 * radius  # Axial length
        L_y = 8.0 * radius  # Transverse extent
        L_z = 8.0 * radius  # Transverse extent

        # Grid
        nx = res
        ny = int(res * L_y / L_x)
        nz = int(res * L_z / L_x)

        # Ensure even numbers for FFT
        ny = ny + (ny % 2)
        nz = nz + (nz % 2)

        # Convert theta to radians
        theta_rad = np.radians(theta)
        b0_x = 0.0  # Perpendicular: B in y-z plane

        # Calculate B field strength for beta
        # beta = P_thermal / P_magnetic = (rho * c_s^2) / (B^2 / 8pi)
        # For gamma != 1, use effective sound speed
        cs_eff = np.sqrt(gamma * K * rho_0**(gamma-1)) if gamma != 1.0 else c_s_iso
        p_mag = p_eq * (8.0 * np.pi / beta)  # This is actually the magnetic pressure
        b0 = np.sqrt(p_mag * 8.0 * np.pi)  # B field

        # Calculate background field strength for beta
        # We want beta = c_s^2 / v_A^2 = (rho * c_s^2) / (B^2 / 8pi * rho)
        # So B^2 = 8pi * rho * c_s^2 / beta
        b0 = np.sqrt(8.0 * np.pi * rho_0 * cs_iso**2 / beta)

        # Output directory
        output_dir = os.path.join(
            self.config.output_base_dir,
            self.sim_id
        )

        cmd = [
            athena_bin,
            f'-i', f'problem/prob_filament_x-{theta_rad:.3f}.athinput',
            f'-d', f'{res} {ny} {nz}',
            f'-t', f'{t_final} 3.0',  # Run time
            f'output/{output_dir}',
            f'output1',
            f'output2',
            f'--deriv', 'output1',
        ]

        return cmd, output_dir


@ray.remote(num_cpus=1, memory=8000_000_000)  # 8GB RAM
def run_athena_simulation(sim_job):
    """Run a single Athena++ simulation"""
    import subprocess
    import os
    import shutil
    from datetime import datetime
    import logging

    logger = logging.getLogger(f"Simulation:{sim_job.sim_id}")

    try:
        # Create output directory
        os.makedirs(sim_job.output_dir, exist_ok=True)

        # Set environment variables
        env = os.environ.copy()
        env['OMP_NUM_THREADS'] = '1'

        # Run simulation
        cmd = sim_job.get_athena_command()
        logger.info(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=sim_job.output_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=36000  # 10 hour timeout
        )

        if result.returncode == 0:
            sim_job.status = 'completed'
            logger.info(f"Simulation {sim_job.sim_id} completed successfully")
        else:
            sim_job.status = 'failed'
            sim_job.error = result.stderr
            logger.error(f"Simulation {sim_job.sim_id} failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        sim_job.status = 'timeout'
        sim_job.error = "Simulation exceeded 10 hour timeout"
        logger.error(f"Simulation {sim_job.sim_id} timed out")

    except Exception as e:
        sim_job.status = 'failed'
        sim_job.error = str(e)
        logger.error(f"Simulation {sim_job.sim_id} crashed: {e}")

    sim_job.end_time = datetime.now()
    return sim_job


def setup_ray_cluster(config):
    """Initialize Ray cluster"""

    logger.info(f"Initializing Ray cluster: {config.cluster_id}")
    logger.info(f"Workers: {config.num_workers}, CPUs/worker: {config.cpus_per_worker}")
    logger.info(f"Memory/worker: {config.memory_per_worker_gb}GB, Total: {config.object_store_memory_gb}GB")

    # Initialize Ray
    ray.init(
        ignore_reinit_error=True,
        num_cpus=config.num_workers * config.cpus_per_worker,
        object_store_memory=config.object_store_memory_gb * 1024**3,  # Convert GB to bytes
        _memory=config.memory_per_worker_gb * 1024**3,
        _temp_dir=config.ray_temp_dir,
        include_dashboard=True,
        dashboard_port=config.dashboard_port,
        logging_level=logging.INFO,
    )

    logger.info(f"Ray dashboard: http://localhost:{config.dashboard_port}")
    return ray


def load_simulation_parameters(param_file):
    """Load simulation parameters from CSV file"""
    df = pd.read_csv(param_file)
    logger.info(f"Loaded {len(df)} simulation parameters from {param_file}")
    return df


def create_simulation_jobs(df, config):
    """Create simulation job objects"""
    jobs = []
    for _, row in df.iterrows():
        job = SimulationJob(
            sim_id=row['sim_id'],
            params=row.to_dict(),
            config=config
        )
        jobs.append(job)
    return jobs


def run_campaign(jobs, max_concurrent=36):
    """Run simulation campaign with Ray"""

    logger.info(f"Starting campaign with {len(jobs)} simulations")
    logger.info(f"Max concurrent: {max_concurrent}")

    # Create work queue
    queue = Queue()
    for job in jobs:
        queue.put(job)

    # Track progress
    completed = 0
    failed = 0
    timeout = 0
    total = len(jobs)

    # Worker function
    @ray.remote
    def worker(queue):
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("worker")

        while True:
            try:
                job = queue.get(block=False)
                if job is None:
                    break

                logger.info(f"Worker processing: {job.sim_id}")
                result = run_athena_simulation.remote(job)
                job = ray.get(result)

                # Update status
                if job.status == 'completed':
                    logger.info(f"Completed: {job.sim_id}")
                else:
                    logger.error(f"Failed: {job.sim_id} - {job.error}")

            except Exception as e:
                logger.error(f"Worker error: {e}")

    # Launch workers
    workers = [worker.remote(queue) for _ in range(max_concurrent)]

    # Wait for completion
    import time
    while completed + failed < total:
        time.sleep(60)  # Check every minute
        # Could add checkpointing logic here

    # Signal workers to stop
    for _ in range(max_concurrent):
        queue.put(None)

    # Wait for workers
    ray.get(workers)

    logger.info(f"Campaign complete: {completed} completed, {failed} failed, {timeout} timeout")


def main():
    parser = argparse.ArgumentParser(description='Setup Ray cluster for sub-isothermal perpendicular campaign')
    parser.add_argument('--cluster_config', type=str, help='YAML config file for Ray cluster')
    parser.add_argument('--sim_params', type=str, help='CSV file with simulation parameters')
    parser.add_argument('--run', action='store_true', help='Run simulations directly')
    parser.add_argument('--dry_run', action='store_true', help='Set up cluster but don\'t run simulations')

    args = parser.parse_args()

    # Load configuration
    config = RayClusterConfig(args.cluster_config)

    # Setup Ray cluster
    setup_ray_cluster(config)

    # Load simulation parameters
    if args.sim_params:
        df = load_simulation_parameters(args.sim_params)
        jobs = create_simulation_jobs(df, config)

        if args.run:
            # Run campaign
            run_campaign(jobs, max_concurrent=config.max_concurrent_jobs)
        elif args.dry_run:
            logger.info(f"Dry run: Would run {len(jobs)} simulations")

    else:
        logger.info("No simulation parameters provided. Use --sim_params to specify parameter file.")
        logger.info("Use --run to directly launch simulations, or --dry_run to test setup.")


if __name__ == "__main__":
    main()
