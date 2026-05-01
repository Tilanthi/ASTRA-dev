#!/usr/bin/env python3
"""
referee_response_campaign_runner.py

Athena++ Campaign Runner for Referee Response Simulations
Supports Campaigns 5, 6, and 7 for addressing specific referee concerns

Usage:
    python referee_response_campaign_runner.py --campaign C5 --config campaign5_turbulence_lambda_W_specification.yaml
    python referee_response_campaign_runner.py --campaign C6 --config campaign6_perpendicular_beta_dependence_specification.yaml
    python referee_response_campaign_runner.py --campaign C7 --config campaign7_critical_transition_specification.yaml
    python referee_response_campaign_runner.py --all  # Run all campaigns sequentially

Author: Peer Review Response Team
Date: 30 April 2026
"""

import os
import sys
import yaml
import argparse
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple
import time


class AthenaCampaignRunner:
    """Runner for Athena++ simulation campaigns on 200 vCPU cluster"""

    def __init__(self, config_file: str):
        """Initialize runner from campaign specification file"""
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.campaign_id = self.config['campaign_id']
        self.campaign_name = self.config['campaign_name']

        # Create output directories
        self.base_dir = Path.cwd()
        self.sim_dir = self.base_dir / self.campaign_id
        self.log_dir = self.sim_dir / 'logs'
        self.output_dir = self.sim_dir / 'output'

        for dir_path in [self.sim_dir, self.log_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Simulation queue
        self.queue = []
        self.results = []
        self.failed = []

    def _load_config(self) -> dict:
        """Load campaign configuration from YAML file"""
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)

    def generate_simulation_queue(self):
        """Generate simulation queue from parameter grid"""
        print(f"Generating simulation queue for {self.campaign_name}")

        f_values = self.config['f_values']
        beta_values = self.config['beta_values']
        seeds = self.config['seeds']

        # Special handling for turbulence campaign
        if self.campaign_id == 'C5_TURBULENCE_LW':
            turb_types = self.config['turbulence_amplitudes']
            for f in f_values:
                for beta in beta_values:
                    for turb in turb_types:
                        for seed in seeds:
                            sim_id = self._generate_sim_id(f, beta, seed, turb_type=turb['type'])
                            self.queue.append({
                                'sim_id': sim_id,
                                'f': f,
                                'beta': beta,
                                'seed': seed,
                                'turb_type': turb['type'],
                                'turb_amp': turb.get('delta_v_over_cs', None)
                            })

        # Special handling for perpendicular campaign (field geometry)
        elif self.campaign_id == 'C6_PERP_BETA':
            field_geometry = self.config['field_geometry']
            for f in f_values:
                for beta in beta_values:
                    for seed in seeds:
                        sim_id = self._generate_sim_id(f, beta, seed, field_geometry=field_geometry)
                        self.queue.append({
                            'sim_id': sim_id,
                            'f': f,
                            'beta': beta,
                            'seed': seed,
                            'field_geometry': field_geometry
                        })

        # Standard handling for other campaigns
        else:
            for f in f_values:
                for beta in beta_values:
                    for seed in seeds:
                        sim_id = self._generate_sim_id(f, beta, seed)
                        self.queue.append({
                            'sim_id': sim_id,
                            'f': f,
                            'beta': beta,
                            'seed': seed
                        })

        print(f"Generated {len(self.queue)} simulations")

    def _generate_sim_id(self, f: float, beta: float, seed: int,
                        turb_type: str = None, field_geometry: int = None) -> str:
        """Generate simulation ID from parameters"""
        if turb_type:
            return f"{self.campaign_id}_f{f}_b{beta}_{turb_type}_s{seed}"
        elif field_geometry == 90:
            return f"{self.campaign_id}_f{f}_b{beta}_s{seed}"
        else:
            return f"{self.campaign_id}_f{f}_b{beta}_s{seed}"

    def write_athena_config(self, sim_params: Dict) -> str:
        """Write Athena++ configuration file for a simulation"""
        sim_dir = self.sim_dir / sim_params['sim_id']
        sim_dir.mkdir(exist_ok=True)

        config_file = sim_dir / 'athena_config.dat'

        # Get base template from campaign config
        athena_config = self.config.get('athena_config', {})

        # Write configuration file
        with open(config_file, 'w') as f:
            # Job section
            job = athena_config.get('job', {})
            f.write(f"<job>\n")
            f.write(f"  problem_id = {sim_params['sim_id']}\n")
            f.write(f"  tlim = {job.get('tlim', 2.5)}\n")
            f.write(f"  dt = {job.get('dt', 1.0e-3)}\n")
            f.write(f"</job>\n\n")

            # Mesh section
            mesh = athena_config.get('mesh', {})
            f.write(f"<mesh>\n")
            f.write(f"  nx1 = {mesh['nx1']}\n")
            f.write(f"  nx2 = {mesh['nx2']}\n")
            f.write(f"  nx3 = {mesh['nx3']}\n")
            f.write(f"  meshblock = {mesh['mesh_block']}\n")
            f.write(f"  ix1_bc = {mesh['bc_ix1']}\n")
            f.write(f"  ox1_bc = {mesh['bc_ox1']}\n")
            f.write(f"  ix2_bc = {mesh['bc_ix2']}\n")
            f.write(f"  ox2_bc = {mesh['bc_ox2']}\n")
            f.write(f"  ix3_bc = {mesh['bc_ix3']}\n")
            f.write(f"  ox3_bc = {mesh['bc_ox3']}\n")
            f.write(f"</mesh>\n\n")

            # Hydro section
            hydro = athena_config.get('hydro', {})
            f.write(f"<hydro>\n")
            f.write(f"  iso_sound_speed = {hydro['iso_sound_speed']}\n")
            f.write(f"  gamma = {hydro['gamma']}\n")
            f.write(f"</hydro>\n\n")

            # Magnetic section
            magnetic = athena_config.get('magnetic', {})
            beta = sim_params['beta']
            b0 = (2.0 / beta)**0.5  # For iso_cs=1

            f.write(f"<magnetic>\n")
            f.write(f"  beta = {beta}\n")
            f.write(f"  bx1 = 0.0\n")
            f.write(f"  bx2 = 0.0\n")
            f.write(f"  bx3 = {b0}\n")
            f.write(f"</magnetic>\n\n")

            # Gravity section
            gravity = athena_config.get('gravity', {})
            f = sim_params['f']
            f.write(f"<gravity>\n")
            f.write(f"  grav_axis_type = {gravity['grav_axis_type']}\n")
            f.write(f"  cyl_axis = {gravity['cyl_axis']}\n")
            f.write(f"  cyl_radius = {gravity['cyl_radius']}\n")
            f.write(f"  cyl_mass_to_flux = {f}\n")
            f.write(f"</gravity>\n\n")

            # Output section
            output = athena_config.get('output', {})
            f.write(f"<output>\n")
            f.write(f"  filetype = {output['filetype']}\n")
            f.write(f"  dt = {output['dt']}\n")
            f.write(f"  variable = dens,mom1,mom2,mom3,B1,B2,B3\n")
            f.write(f"</output>\n")

        return str(config_file)

    def run_simulation(self, sim_params: Dict, np: int = 8, timeout_hours: int = 6) -> bool:
        """Run a single Athena++ simulation"""
        sim_id = sim_params['sim_id']
        sim_dir = self.sim_dir / sim_id

        # Write Athena++ config file
        config_file = self.write_athena_config(sim_params)

        # Set up environment
        athena_bin = os.environ.get('ATHENA_BIN', 'athena')
        env = os.environ.copy()
        env['OMP_NUM_THREADS'] = str(np)

        # Log file
        log_file = self.log_dir / f"{sim_id}.log"

        print(f"Running simulation {sim_id}...")

        try:
            # Run Athena++
            with open(log_file, 'w') as log:
                proc = subprocess.Popen(
                    [athena_bin, '-i', config_file],
                    cwd=sim_dir,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT
                )

                # Wait with timeout
                timeout_seconds = timeout_hours * 3600
                start_time = time.time()

                while proc.poll() is None:
                    if time.time() - start_time > timeout_seconds:
                        proc.kill()
                        print(f"Simulation {sim_id} timed out after {timeout_hours} hours")
                        return False
                    time.sleep(60)  # Check every minute

            # Check for successful completion
            if proc.returncode == 0:
                print(f"Simulation {sim_id} completed successfully")
                return True
            else:
                print(f"Simulation {sim_id} failed with return code {proc.returncode}")
                return False

        except Exception as e:
            print(f"Error running simulation {sim_id}: {e}")
            return False

    def run_campaign(self, max_parallel: int = 25):
        """Run all simulations in the campaign with parallel execution"""
        print(f"Starting campaign {self.campaign_name}")
        print(f"Total simulations: {len(self.queue)}")
        print(f"Max parallel: {max_parallel}")

        # Get per-simulation resources from config
        np_per_sim = self.config.get('np_per_sim', 8)

        # Track running simulations
        running = []
        completed = 0

        while self.queue or running:
            # Start new simulations if capacity available
            while len(running) < max_parallel and self.queue:
                sim_params = self.queue.pop(0)

                # Run simulation in subprocess
                proc = subprocess.Popen(
                    [sys.executable, __file__, '--single', '--config', str(self.config_file),
                     '--sim-id', sim_params['sim_id'], '--np', str(np_per_sim)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                running.append({
                    'params': sim_params,
                    'proc': proc,
                    'start_time': time.time()
                })

            # Check for completed simulations
            still_running = []
            for job in running:
                proc = job['proc']
                if proc.poll() is not None:
                    # Simulation completed
                    sim_params = job['params']
                    if proc.returncode == 0:
                        self.results.append(sim_params)
                        print(f"Completed {sim_params['sim_id']} ({len(self.results)}/{len(self.queue)+len(self.results)+len(self.failed)})")
                    else:
                        self.failed.append(sim_params)
                        print(f"Failed {sim_params['sim_id']}")
                else:
                    still_running.append(job)

            running = still_running
            time.sleep(10)  # Check every 10 seconds

        # Save results summary
        self.save_results_summary()

    def save_results_summary(self):
        """Save campaign results summary to JSON"""
        summary = {
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign_name,
            'config_file': str(self.config_file),
            'total_simulations': len(self.results) + len(self.failed),
            'completed': len(self.results),
            'failed': len(self.failed),
            'success_rate': len(self.results) / (len(self.results) + len(self.failed)) if (len(self.results) + len(self.failed)) > 0 else 0,
            'completed_simulations': self.results,
            'failed_simulations': self.failed
        }

        summary_file = self.sim_dir / 'campaign_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"Campaign summary saved to {summary_file}")

    def analyze_results(self):
        """Run post-campaign analysis"""
        print(f"Analyzing results for {self.campaign_name}")

        # Import analysis script
        analysis_script = self.config.get('analysis_script', 'measure_lambda_W.py')

        # Collect results from all simulations
        lambda_W_results = []

        for sim_params in self.results:
            sim_id = sim_params['sim_id']
            sim_dir = self.sim_dir / sim_id

            # Run analysis script on simulation output
            # (This would call the measure_lambda_W.py script)
            # For now, just record that analysis is needed
            lambda_W_results.append({
                'sim_id': sim_id,
                'status': 'analysis_pending'
            })

        # Save analysis results
        analysis_file = self.output_dir / 'lambda_W_analysis.json'
        with open(analysis_file, 'w') as f:
            json.dump(lambda_W_results, f, indent=2)

        print(f"Analysis results saved to {analysis_file}")


def main():
    parser = argparse.ArgumentParser(description='Run Athena++ referee response campaigns')
    parser.add_argument('--campaign', type=str, choices=['C5', 'C6', 'C7'],
                       help='Campaign ID to run')
    parser.add_argument('--config', type=str,
                       help='Campaign specification YAML file')
    parser.add_argument('--all', action='store_true',
                       help='Run all campaigns sequentially')
    parser.add_argument('--single', action='store_true',
                       help='Run single simulation (internal use)')
    parser.add_argument('--sim-id', type=str,
                       help='Simulation ID for single run')
    parser.add_argument('--np', type=int, default=8,
                       help='Number of processes for single run')
    parser.add_argument('--max-parallel', type=int, default=25,
                       help='Maximum parallel simulations')

    args = parser.parse_args()

    # Single simulation mode (for parallel execution)
    if args.single and args.sim_id:
        # This branch is called by the parent process for each simulation
        # Parse config and run single simulation
        runner = AthenaCampaignRunner(args.config)
        sim_params = next((s for s in runner.queue if s['sim_id'] == args.sim_id), None)

        if sim_params:
            success = runner.run_simulation(sim_params, np=args.np)
            return 0 if success else 1
        else:
            print(f"Simulation {args.sim_id} not found in queue")
            return 1

    # Campaign mode
    if args.all:
        # Run all campaigns
        campaigns = [
            ('C5', 'campaign5_turbulence_lambda_W_specification.yaml'),
            ('C6', 'campaign6_perpendicular_beta_dependence_specification.yaml'),
            ('C7', 'campaign7_critical_transition_specification.yaml')
        ]

        for campaign_id, config_file in campaigns:
            print(f"\n{'='*60}")
            print(f"Running campaign {campaign_id}")
            print(f"{'='*60}\n")

            runner = AthenaCampaignRunner(config_file)
            runner.generate_simulation_queue()
            runner.run_campaign(max_parallel=args.max_parallel)
            runner.analyze_results()

    elif args.campaign and args.config:
        # Run specific campaign
        runner = AthenaCampaignRunner(args.config)
        runner.generate_simulation_queue()
        runner.run_campaign(max_parallel=args.max_parallel)
        runner.analyze_results()

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
