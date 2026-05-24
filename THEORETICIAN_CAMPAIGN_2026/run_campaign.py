#!/usr/bin/env python3
"""
Theoretician Campaign 2026: Ray-based Execution Script

Resolves two theoretical crises:
1. Perpendicular-field crisis (λ/W ≈ 1.25 vs observed 2.17)
2. Supercritical extrapolation problem (no direct measurements for f ≥ 1.5)

Author: ASTRA Analysis System
Date: 2026-05-08
"""

import ray
from pathlib import Path
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np

# =============================================================================
# CONFIGURATION
# =============================================================================

RAY_CONFIG = {
    'num_cpus': 220,
    'dashboard_port': 8265,
    'max_concurrent_sims': 13,  # 13 sims × 16 cores = 208 cores (leaving headroom)
    'cores_per_sim': 16,
}

CAMPAIGN_BASE_DIR = Path('/path/to/athena/simulations')  # UPDATE THIS PATH
ATHENA_EXE = CAMPAIGN_BASE_DIR / 'bin' / 'athena'

# =============================================================================
# CAMPAIGN SPECIFICATIONS
# =============================================================================

CAMPAIGN_A_MIXED_FIELD = {
    'name': 'CAMPAIGN_A_MIXED_FIELD',
    'theta_deg': [0, 15, 30, 45, 60, 75, 90],
    'mass_to_critical': [1.0, 1.5, 2.0, 2.5],
    'beta': [0.3, 1.0],
    'mach': [1.0],
    'seeds': [42, 137, 251, 367, 499],
    'domain': {'L_lambdaJ': 16, 'Nx': 512, 'Ny': 64, 'Nz': 64},
    'timeout': 7200,
}

CAMPAIGN_B_SUPERCRITICAL = {
    'name': 'CAMPAIGN_B_SUPERCRITICAL',
    'mass_to_critical': [1.3, 1.5, 1.8, 2.0, 2.5, 3.0],
    'beta': [0.3, 1.0, 3.0],
    'theta_deg': [0],
    'mach': [1.0],
    'seeds': [42, 137, 251, 367, 499],
    'domain': {'L_lambdaJ': 24, 'Nx': 768, 'Ny': 64, 'Nz': 64},
    'timeout': 10800,
}

CAMPAIGN_C_PERPENDICULAR = {
    'name': 'CAMPAIGN_C_PERPENDICULAR',
    'mass_to_critical': [1.0, 1.5, 2.0],
    'beta': [1.0],
    'theta_deg': [90],
    'mach': [1.0],
    'L_lambdaJ': [12, 16, 20, 24],
    'seeds': [42, 137, 251],
    'domain': {'Nx': 512, 'Ny': 64, 'Nz': 64},
    'timeout': 7200,
}

# =============================================================================
# ATHENA++ CONFIG GENERATION
# =============================================================================

def generate_athena_config(params: Dict) -> str:
    """Generate Athena++ configuration file content."""
    L = params['domain']['L_lambdaJ']
    Nx, Ny, Nz = params['domain']['Nx'], params['domain']['Ny'], params['domain']['Nz']

    config = f"""<job>
problemname:   {params.get('problemname', 'hd_amr')}
dt:           {params.get('dt', '0.001')}
tlim:         {params.get('tlim', '3.0')}

<mesh>
nx1:  {Nx}
nx2:  {Nx}
nx3:  {Nx}
x1min: 0.0
x1max: {L}
x2min: 0.0
x2max: {1.0}
x3min: 0.0
x3max: {1.0}
</mesh>

<hydro>
gamma:        1.666666667
</hydro>

<mhd>
gamma:         1.666667
</mhd>

<field>
b_initial:     {params.get('b_initial', '0.0')}
theta_b:       {params.get('theta_deg', 0.0)}
beta:          {params.get('beta', 1.0)}
</field>

<particles>
particle_rho:  {params.get('particle_rho', '0.0')}
</particles>

<output>
output_dir:    {params.get('output_dir', 'outputs')}
dt:            {params.get('output_dt', '0.1')}
</output>

<problem>
mass_to_crit:  {params.get('mass_to_critical', 1.0)}
mach:          {params.get('mach', 1.0)}
seed:          {params.get('seed', 42)}
</problem>
</job>
"""
    return config


def generate_configs_for_campaign(campaign_spec: Dict) -> List[Dict]:
    """Generate all Athena++ config specifications for a campaign."""
    configs = []

    if campaign_spec['name'] == 'CAMPAIGN_C_PERPENDICULAR':
        # Special handling for Campaign C (domain size study)
        for L in campaign_spec['L_lambdaJ']:
            for f in campaign_spec['mass_to_critical']:
                for seed in campaign_spec['seeds']:
                    params = {
                        'problemname': 'hd_amr',
                        'output_dir': f'outputs/campaign_c/L{L:02d}_f{f:.1f}_s{seed}',
                        'domain': {'L_lambdaJ': L, 'Nx': 512, 'Ny': 64, 'Nz': 64},
                        'mass_to_critical': f,
                        'beta': campaign_spec['beta'][0],
                        'theta_deg': campaign_spec['theta_deg'][0],
                        'mach': campaign_spec['mach'][0],
                        'seed': seed,
                        'dt': '0.001',
                        'tlim': '3.0',
                        'output_dt': '0.1',
                    }
                    configs.append(params)
    else:
        # Standard parameter grid
        for theta in campaign_spec['theta_deg']:
            for f in campaign_spec['mass_to_critical']:
                for beta in campaign_spec['beta']:
                    for seed in campaign_spec['seeds']:
                        domain = campaign_spec['domain']
                        params = {
                            'problemname': 'hd_amr',
                            'output_dir': f"outputs/{campaign_spec['name'].lower()}/theta{theta:02d}_f{f:.1f}_beta{beta}_s{seed}",
                            'domain': domain,
                            'mass_to_critical': f,
                            'beta': beta,
                            'theta_deg': theta,
                            'mach': campaign_spec['mach'][0],
                            'seed': seed,
                            'dt': '0.001',
                            'tlim': '2.0' if campaign_spec['name'] == 'CAMPAIGN_B_SUPERCRITICAL' else '3.0',
                            'output_dt': '0.1',
                        }
                        configs.append(params)

    return configs


# =============================================================================
# RAY ACTORS
# =============================================================================

@ray.remote(num_cpus=16)
class AthenaSimulationActor:
    """Ray actor for running Athena++ simulations."""

    def __init__(self, sim_id: str, config: Dict):
        self.sim_id = sim_id
        self.config = config
        self.status = 'pending'
        self.start_time = None
        self.end_time = None
        self.result = None

    def run(self) -> Dict:
        """Run the Athena++ simulation."""
        import subprocess
        import time
        from pathlib import Path

        self.status = 'running'
        self.start_time = time.time()

        try:
            # Create output directory
            output_dir = Path(self.config['output_dir'])
            output_dir.mkdir(parents=True, exist_ok=True)

            # Write config file
            config_file = output_dir / 'athena_config.ini'
            with open(config_file, 'w') as f:
                f.write(generate_athena_config(self.config))

            # Run Athena++
            cmd = [
                str(ATHENA_EXE),
                '-i', str(config_file),
                '<', '/dev/null'
            ]

            start = time.time()
            result = subprocess.run(
                ' '.join(cmd),
                shell=True,
                cwd=str(output_dir),
                timeout=self.config.get('timeout', 7200),
                capture_output=True,
                text=True
            )
            elapsed = time.time() - start

            # Check for beading pattern
            has_beading = self._check_beading(output_dir)

            self.result = {
                'sim_id': self.sim_id,
                'status': 'completed' if result.returncode == 0 else 'failed',
                'elapsed_seconds': elapsed,
                'has_beading': has_beading,
                'returncode': result.returncode,
            }
            self.status = 'completed'

        except Exception as e:
            self.result = {
                'sim_id': self.sim_id,
                'status': 'error',
                'error': str(e),
                'elapsed_seconds': time.time() - self.start_time,
            }
            self.status = 'error'

        self.end_time = time.time()
        return self.result

    def _check_beading(self, output_dir: Path) -> bool:
        """Check if simulation produced beading pattern."""
        # Look for HDF5 output files
        h5_files = list(output_dir.glob('*.hdf5'))
        if not h5_files:
            return False

        # Simple check: analyze density profile along x-axis
        try:
            import h5py
            with h5py.File(h5_files[-1], 'r') as f:
                rho = f['density'][:]

                # Take longitudinal profile (middle of y-z plane)
                ny, nz = rho.shape[1], rho.shape[2]
                profile = rho[:, ny//2, nz//2]

                # Check for variance
                if np.std(profile) / np.mean(profile) > 0.05:
                    return True
        except:
            pass

        return False

    def get_status(self) -> Dict:
        """Get current status."""
        return {
            'sim_id': self.sim_id,
            'status': self.status,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'result': self.result,
        }


# =============================================================================
# CAMPAIGN EXECUTION
# =============================================================================

def run_campaign(campaign_spec: Dict) -> List[Dict]:
    """Run a full campaign using Ray."""
    configs = generate_configs_for_campaign(campaign_spec)
    print(f"Generated {len(configs)} configs for {campaign_spec['name']}")

    # Create actors
    actors = []
    for i, config in enumerate(configs):
        sim_id = f"{campaign_spec['name']}_sim{i:04d}"
        actor = AthenaSimulationActor.remote(sim_id, config)
        actors.append(actor)

    # Run simulations concurrently
    print(f"Starting {len(actors)} simulations...")

    # Batch execution to limit concurrency
    results = []
    batch_size = RAY_CONFIG['max_concurrent_sims']

    for i in range(0, len(actors), batch_size):
        batch = actors[i:i+batch_size]
        print(f"Running batch {i//batch_size + 1}/{(len(actors)-1)//batch_size + 1} ({len(batch)} sims)...")

        # Start all in batch
        refs = [actor.run.remote() for actor in batch]

        # Wait for completion
        batch_results = ray.get(refs)
        results.extend(batch_results)

        # Progress update
        completed = sum(1 for r in results if r['status'] == 'completed')
        print(f"Batch complete: {completed}/{len(results)} total completed")

    return results


def main():
    """Main execution function."""
    print("="*80)
    print("THEORETICIAN CAMPAIGN 2026")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"CPUs: {RAY_CONFIG['num_cpus']}")
    print(f"Max concurrent: {RAY_CONFIG['max_concurrent_sims']}")
    print("="*80)

    # Initialize Ray
    print("\nInitializing Ray...")
    ray.init(num_cpus=RAY_CONFIG['num_cpus'], dashboard_port=RAY_CONFIG['dashboard_port'])

    total_results = {}

    # Run Campaign A: Mixed Field
    print("\n" + "="*80)
    print("CAMPAIGN A: MIXED FIELD GEOMETRY")
    print("="*80)
    results_a = run_campaign(CAMPAIGN_A_MIXED_FIELD)
    total_results['campaign_a'] = results_a

    # Run Campaign B: Supercritical
    print("\n" + "="*80)
    print("CAMPAIGN B: SUPERCRITICAL EXTENSION")
    print("="*80)
    results_b = run_campaign(CAMPAIGN_B_SUPERCRITICAL)
    total_results['campaign_b'] = results_b

    # Run Campaign C: Perpendicular Extended
    print("\n" + "="*80)
    print("CAMPAIGN C: PERPENDICULAR EXTENDED")
    print("="*80)
    results_c = run_campaign(CAMPAIGN_C_PERPENDICULAR)
    total_results['campaign_c'] = results_c

    # Save results
    results_file = Path('theoretician_campaign_2026_results.json')
    with open(results_file, 'w') as f:
        json.dump(total_results, f, indent=2)

    print(f"\n{'='*80}")
    print("CAMPAIGN COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {results_file}")
    print(f"\nSummary:")
    print(f"  Campaign A: {len(results_a)} simulations")
    print(f"  Campaign B: {len(results_b)} simulations")
    print(f"  Campaign C: {len(results_c)} simulations")
    print(f"  Total: {len(results_a) + len(results_b) + len(results_c)} simulations")

    ray.shutdown()


if __name__ == '__main__':
    main()
