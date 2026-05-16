#!/usr/bin/env python3
"""
Run λ/W Direct Measurement Campaign using Ray for distributed execution.

This campaign CORRECTLY addresses the theoretician's concerns by measuring
λ/W (fragmentation wavelength), not t_frag (fragmentation timescale).

Key differences from previous campaign:
- HDF5 snapshots at multiple times for direct λ/W extraction
- Extended domains (16-32λJ) to ensure beading develops before collapse
- Time-series analysis for perpendicular-field beading evolution
- Domain size/resolution tests to explain FLAT entries

Usage: python scripts/run_campaign.py [--campaign CAMPAIGN] [--num-workers N]
"""

import ray
import os
import subprocess
import json
from pathlib import Path
import time
from datetime import datetime

# Configuration (to be updated by user)
ATHENA_BINARY = "./athena_filament"  # Path to compiled Athena++ binary
CAMPAIGN_BASE = Path(__file__).parent.parent  # Campaign directory
NUM_WORKERS_DEFAULT = 220  # 220 CPU cluster

# Expected simulation counts
CAMPAIGN_CONFIGS = {
    'LW_DIRECT': 36,      # Supercritical λ/W direct measurements
    'PERP_TIMESERIES': 27, # Perpendicular field time-series
    'DOMAIN_TEST': 18,    # Domain size/resolution investigation
}


@ray.remote
def run_athena_simulation(sim_config, athena_binary, sim_index, total_sims):
    """
    Run a single Athena++ simulation for λ/W measurement.

    Key feature: Outputs multiple HDF5 snapshots for λ/W extraction.
    """
    sim_name = sim_config['output']['basename']
    campaign = sim_config['metadata']['campaign']
    metadata = sim_config['metadata']

    status_label = f"[{sim_index}/{total_sims}] {campaign}:{sim_name}"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_label} Starting...")

    print(f"  Parameters: f={metadata['f']}, β={metadata['beta']}, θ={metadata['theta']}°")
    print(f"  Domain: Lx={metadata['Lx_lambdaJ']}λJ, res={metadata['resolution']}")
    print(f"  Snapshots: n={metadata['n_snapshots']} at t={metadata['snap_times'][:3]}...")

    start_time = time.time()

    try:
        # Create simulation output directory
        output_dir = CAMPAIGN_BASE / 'outputs' / campaign
        output_dir.mkdir(parents=True, exist_ok=True)
        sim_dir = output_dir / sim_name
        sim_dir.mkdir(exist_ok=True)

        # Write athena_input.dat from config
        config_path = sim_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(sim_config, f, indent=2)

        # Change to simulation directory
        os.chdir(sim_dir)

        # Build athena_input.dat from config
        athena_input = build_athena_input(sim_config)
        with open('athena_input.dat', 'w') as f:
            f.write(athena_input)

        # Run Athena++
        timeout_sec = sim_config.get('timeout_seconds', 7200)
        result = subprocess.run(
            [athena_binary, "-i", "athena_input.dat"],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            # Check if outputs exist
            output_files = list(sim_dir.glob('*.h5')) + list(sim_dir.glob '*.hst')
            if output_files:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_label} ✓ Completed ({elapsed/60:.1f}min)")
                print(f"  Generated {len(output_files)} output files")

                # Save status
                status = {
                    'run_id': sim_name,
                    'status': 'FRAG',  # Will be updated by analysis scripts
                    'elapsed_time': elapsed,
                    'returncode': result.returncode,
                    'output_files': [f.name for f in output_files],
                    'timestamp': datetime.now().isoformat()
                }

                with open(sim_dir / 'status.json', 'w') as f:
                    json.dump(status, f, indent=2)

                return status
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_label} ⚠ No outputs generated")
                return {
                    'run_id': sim_name,
                    'status': 'NO_OUTPUT',
                    'elapsed_time': elapsed
                }
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_label} ✗ FAILED (code={result.returncode})")
            print(f"  stderr: {result.stderr[-200:]}")

            status = {
                'run_id': sim_name,
                'status': 'FAILED',
                'elapsed_time': elapsed,
                'returncode': result.returncode,
                'stderr': result.stderr[-500:]
            }

            with open(sim_dir / 'status.json', 'w') as f:
                json.dump(status, f, indent=2)

            return status

    except subprocess.TimeoutExpired:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_label} ⏱ TIMEOUT")
        return {
            'run_id': sim_name,
            'status': 'TIMEOUT',
            'elapsed_time': timeout_sec
        }
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_label} ⚠ ERROR: {str(e)}")
        return {
            'run_id': sim_name,
            'status': 'ERROR',
            'error': str(e)
        }


def build_athena_input(config):
    """Build Athena++ input file from config dictionary."""
    mesh = config['mesh']
    hydro = config['hydro']
    field = config['field']
    gravity = config['gravity']
    filament = config['filament']
    time_config = config['time']
    output = config['output']

    # Determine output format based on snapshot requirements
    has_snapshots = len(output.get('snapshots', [])) > 0

    input_lines = [
        f"<job>",
        f"  problem_id = {config['job']['problem_id']}",
        f"</job>",
        "",
        f"<mesh>",
        f"  nx1 = {mesh['nx1']}",
        f"  nx2 = {mesh['nx2']}",
        f"  nx3 = {mesh['nx3']}",
        f"  x1min = {mesh['x1min']}",
        f"  x1max = {mesh['x1max']}",
        f"  x2min = {mesh['x2min']}",
        f"  x2max = {mesh['x2max']}",
        f"  x3min = {mesh['x3min']}",
        f"  x3max = {mesh['x3max']}",
        f"</mesh>",
        "",
        f"<hydro>",
        f"  gamma = {hydro['gamma']}",
        f"  cs0 = {hydro['cs0']}",
        f"</hydro>",
        "",
        f"<field>",
        f"  b1_initial = {field['b1_initial']}",
        f"  b2_initial = {field['b2_initial']}",
        f"  b3_initial = {field['b3_initial']}",
        f"</field>",
        "",
        f"<gravity>",
        f"  four_pi_G = {gravity['four_pi_G']}",
        f"</gravity>",
        "",
        f"<problem>",
        f"  line_mass_fraction = {filament['line_mass_fraction']}",
        f"  W_core = {filament['W_core']}",
        f"  profile = {filament['profile']}",
        f"  perturbation_amplitude = {filament['perturbation_amplitude']}",
        f"</problem>",
        "",
        f"<time>",
        f"  tlim = {time_config['tlim']}",
        f"  dt_initial = {time_config['dt_initial']}",
        f"  dt_min = {time_config['dt_min']}",
        f"  cfl_number = {time_config['cfl_number']}",
        f"</time>",
        "",
        f"<output>",
        f"  file_type = {output['file_type']}",
        f"  dt = {output['dt']}",
        f"  variable = cons,prim",
    ]

    # Add HDF5 snapshots if configured
    if has_snapshots:
        input_lines.extend([
            f"  filetype = hst, tab",  # History + HDF5 snapshots
        ])

        # Add snapshot outputs
        for i, snap_time in enumerate(output['snapshots']):
            input_lines.extend([
                f"",
                f"<output{i}>",
                f"  file_type = tab",
                f"  variable = {','.join(output['snapshot_variables'])}",
                f"  dt = {snap_time}",
                f"  start_time = {snap_time}",
                f"  num = 1",
            ])

            # Stop output after this snapshot
            if i < len(output['snapshots']) - 1:
                input_lines.append(f"  end_time = {snap_time + 0.01}")

            input_lines.append(f"</output{i}>")
    else:
        input_lines.append(f"  variable = cons,prim")

    input_lines.extend([
        "",
        f"<output1>",
        f"  file_type = hst",
        f"  dt = {output.get('hst_dt', output['dt'])}",
        f"  variable = cons,prim",
        f"</output1>",
        f"</output>",
    ])

    return "\n".join(input_lines)


def load_campaign_configs(campaign=None):
    """Load simulation configurations from configs directory."""
    configs_dir = CAMPAIGN_BASE / 'configs'

    if campaign:
        campaign_dir = configs_dir / campaign
        config_files = list(campaign_dir.glob("config_*.json"))
    else:
        config_files = []
        for camp in CAMPAIGN_CONFIGS.keys():
            campaign_dir = configs_dir / camp
            config_files.extend(list(campaign_dir.glob("config_*.json")))

    configs = []
    for config_file in config_files:
        with open(config_file) as f:
            config = json.load(f)
            configs.append(config)

    print(f"Loaded {len(configs)} configurations")
    return configs


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run λ/W Direct Measurement Campaign"
    )
    parser.add_argument(
        "--campaign",
        type=str,
        choices=list(CAMPAIGN_CONFIGS.keys()) + ['all'],
        default='all',
        help="Campaign to run (default: all)"
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=NUM_WORKERS_DEFAULT,
        help="Number of Ray workers (default: 220)"
    )
    parser.add_argument(
        "--athena-binary",
        type=str,
        default=ATHENA_BINARY,
        help="Path to Athena++ binary"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous run (skip completed)"
    )

    args = parser.parse_args()

    # Check binary path
    if not os.path.exists(args.athena_binary):
        print(f"ERROR: Athena++ binary not found: {args.athena_binary}")
        print("Please compile Athena++ first: ./scripts/compile_athena.sh")
        return 1

    # Load configs
    configs = load_campaign_configs(args.campaign if args.campaign != 'all' else None)

    if not configs:
        print("ERROR: No configuration files found")
        print("Please run generate_configs.py first")
        return 1

    # Print campaign info
    print("\n" + "="*80)
    print("λ/W Direct Measurement Campaign")
    print("="*80)
    print("\nThis campaign measures λ/W (fragmentation wavelength) to address:")
    print("  Concern 5: Test λ_frag = 1.11 λ_MJ calibration extrapolation")
    print("  Concern 6: Time-series λ/W analysis for perpendicular fields")
    print("  Concern 7: Domain size/resolution investigation for FLAT entries")
    print("\nCRITICAL: Uses HDF5 snapshots (not just HST files) for λ/W extraction")
    print("="*80)

    # Print breakdown by campaign
    for camp, expected in CAMPAIGN_CONFIGS.items():
        if args.campaign == 'all' or args.campaign == camp:
            count = sum(1 for c in configs if c['metadata']['campaign'] == camp)
            print(f"  {camp}: {count} simulations")

    print(f"\nTotal: {len(configs)} simulations")
    print(f"Workers: {args.num_workers}")
    print("="*80 + "\n")

    # Filter completed simulations if resuming
    if args.resume:
        original_count = len(configs)
        configs_to_run = []
        for config in configs:
            sim_dir = (CAMPAIGN_BASE / 'outputs' /
                      config['metadata']['campaign'] /
                      config['output']['basename'])
            status_file = sim_dir / 'status.json'
            if status_file.exists():
                with open(status_file) as f:
                    status = json.load(f)
                    if status.get('status') in ['FRAG', 'completed']:
                        continue  # Skip completed
            configs_to_run.append(config)

        print(f"Resuming: skipping {original_count - len(configs_to_run)} completed simulations")
        configs = configs_to_run

    if not configs:
        print("All simulations completed!")
        return 0

    # Estimate resources
    avg_timeout = sum(c.get('timeout_seconds', 7200) for c in configs) / len(configs)
    estimated_hours = len(configs) * avg_timeout / args.num_workers / 3600
    print(f"\nEstimated wall time: {estimated_hours:.1f} hours")
    print(f"Estimated CPU-hours: {len(configs) * avg_timeout / 3600:.0f}\n")

    # Initialize Ray
    print(f"Initializing Ray with {args.num_workers} workers...")
    try:
        ray.init(num_cpus=args.num_workers)
        print(f"Ray initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize Ray: {e}")
        print("Make sure Ray is installed: pip install ray")
        return 1

    # Submit all simulations
    start_time = time.time()
    total_sims = len(configs)

    futures = [
        run_athena_simulation.remote(config, args.athena_binary, i+1, total_sims)
        for i, config in enumerate(configs)
    ]

    print(f"\nSubmitting {total_sims} simulations...\n")

    # Wait for completion and collect results
    completed = 0
    results = []
    start_timestamp = time.time()

    # Progress tracking
    status_counts = {'FRAG': 0, 'FAILED': 0, 'TIMEOUT': 0, 'ERROR': 0, 'NO_OUTPUT': 0}

    while futures:
        ready_futures, futures = ray.wait(futures, num_returns=1, timeout=30.0)

        for future in ready_futures:
            result = ray.get(future)
            results.append(result)
            completed += 1

            # Track status
            status = result.get('status', 'UNKNOWN')
            if status in status_counts:
                status_counts[status] += 1

            # Print progress every 5 completions
            if completed % 5 == 0 or completed == total_sims:
                elapsed = time.time() - start_timestamp
                rate = completed / elapsed * 3600  # sims per hour
                eta = (total_sims - completed) / rate * 3600 if rate > 0 else 0

                print(f"[{completed:3d}/{total_sims}] {completed/total_sims*100:5.1f}% | "
                      f"Rate: {rate:4.1f}/h | ETA: {eta/60:4.0f}min | "
                      f"FRAG: {status_counts['FRAG']} | "
                      f"FAIL: {status_counts['FAILED']} | "
                      f"TIMEOUT: {status_counts['TIMEOUT']}")

    # Print final summary
    total_elapsed = time.time() - start_timestamp
    print("\n" + "="*80)
    print("CAMPAIGN COMPLETE")
    print("="*80)
    print(f"Total time: {total_elapsed/3600:.1f} hours")
    print(f"Completed: {completed}/{total_sims} simulations")
    print(f"\nStatus breakdown:")
    print(f"  FRAG:      {status_counts['FRAG']} (fragmented - λ/W extraction needed)")
    print(f"  FAILED:    {status_counts['FAILED']}")
    print(f"  TIMEOUT:   {status_counts['TIMEOUT']}")
    print(f"  ERROR:     {status_counts['ERROR']}")
    print(f"  NO_OUTPUT: {status_counts['NO_OUTPUT']}")
    print("\nNext steps:")
    print("  1. Extract λ/W from HDF5 snapshots:")
    print("     python scripts/extract_beading.py outputs/LW_DIRECT/")
    print("  2. Analyze each campaign:")
    print("     python scripts/analyze_lw_direct.py")
    print("     python scripts/analyze_perp_timeseries.py")
    print("     python scripts/analyze_domain_test.py")
    print("="*80)

    # Save results
    results_file = CAMPAIGN_BASE / 'simulation_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_elapsed': total_elapsed,
            'status_counts': status_counts,
            'results': results
        }, f, indent=2)

    print(f"\nResults saved to {results_file}")

    return 0


if __name__ == '__main__':
    main()
