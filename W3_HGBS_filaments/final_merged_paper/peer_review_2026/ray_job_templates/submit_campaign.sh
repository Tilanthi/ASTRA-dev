#!/bin/bash
# -----------------------------------------------------------------------------
# Ray Job Submission Script for MHD Simulation Campaign
# -----------------------------------------------------------------------------
# This script submits an entire campaign of Athena++ MHD simulations
# to a Ray cluster for parallel execution.
#
# Usage:
#   ./submit_campaign.sh --campaign <campaign.json> --output <output_dir> [options]
#
# Options:
#   --campaign <file>     Campaign specification JSON file
#   --output <dir>        Output directory for results
#   --cores <int>         Number of CPU cores to use (default: 200)
#   --memory <GB>         Memory per job in GB (default: 1)
#   --concurrent <int>    Max concurrent jobs (default: 50)
#   --dry-run             Print job list without submitting
# -----------------------------------------------------------------------------

set -e

# Default values
CORES=200
MEMORY_PER_JOB=1
MAX_CONCURRENT=50
DRY_RUN=false

# Parse arguments
CAMPAIGN_FILE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --campaign)
            CAMPAIGN_FILE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --cores)
            CORES="$2"
            shift 2
            ;;
        --memory)
            MEMORY_PER_JOB="$2"
            shift 2
            ;;
        --concurrent)
            MAX_CONCURRENT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$CAMPAIGN_FILE" ]]; then
    echo "Error: --campaign argument is required"
    exit 1
fi

if [[ ! -f "$CAMPAIGN_FILE" ]]; then
    echo "Error: Campaign file not found: $CAMPAIGN_FILE"
    exit 1
fi

if [[ -z "$OUTPUT_DIR" ]]; then
    echo "Error: --output argument is required"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Extract campaign name
CAMPAIGN_NAME=$(python3 -c "import json; f=open('$CAMPAIGN_FILE'); d=json.load(f); print(d.get('campaign_name', 'unknown'))")

echo "======================================"
echo "MHD Simulation Campaign Submission"
echo "======================================"
echo "Campaign: $CAMPAIGN_NAME"
echo "Config: $CAMPAIGN_FILE"
echo "Output: $OUTPUT_DIR"
echo "Cores: $CORES"
echo "Memory per job: ${MEMORY_PER_JOB}GB"
echo "Max concurrent: $MAX_CONCURRENT"
echo "======================================"

# Parse campaign specification and generate job list
python3 <<EOF
import json
import itertools
from pathlib import Path

# Load campaign specification
with open('$CAMPAIGN_FILE', 'r') as f:
    campaign = json.load(f)

# Extract parameter grid
params = campaign.get('parameter_grid', {})
random_seeds = campaign.get('random_seeds', {'values': [42]})

# Generate all parameter combinations
param_names = list(params.keys())
param_values = [params[name]['values'] for name in param_names]
combinations = list(itertools.product(*param_values))

# Generate simulation configs
configs = []
sim_id = 0

for combo in combinations:
    for seed in random_seeds['values']:
        config = {
            'sim_id': sim_id,
            'campaign_name': campaign['campaign_name'],
            'parameters': dict(zip(param_names, combo)),
            'random_seed': seed
        }
        configs.append(config)
        sim_id += 1

# Write job list
job_list_file = Path('$OUTPUT_DIR') / 'job_list.json'
with open(job_list_file, 'w') as f:
    json.dump(configs, f, indent=2)

print(f"Generated {len(configs)} simulation configurations")
print(f"Job list written to: {job_list_file}")
EOF

# Create Ray job script
cat > "$OUTPUT_DIR/run_campaign.py" <<'RAY_SCRIPT'
#!/usr/bin/env python3
"""Ray job execution script for MHD simulation campaign."""

import ray
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any

# Initialize Ray
try:
    ray.init(
        num_cpus=$CORES,
        object_store_memory=10_000_000_000,
        dashboard_host="0.0.0.0",
        dashboard_port=8265,
        ignore_reinit_error=True
    )
    print(f"Ray initialized with {$CORES} cores")
except Exception as e:
    print(f"Warning: Ray initialization failed: {e}")
    print("Attempting to continue...")

@ray.remote(num_cpus=4, memory=$MEMORY_PER_JOB*1024*1024*1024)
def run_simulation(config: Dict[str, Any], output_dir: str, sim_idx: int) -> Dict[str, Any]:
    """Run a single Athena++ simulation."""
    from pathlib import Path
    import json
    import sys

    try:
        # Create simulation directory
        sim_dir = Path(output_dir) / f"sim_{sim_idx:04d}"
        sim_dir.mkdir(parents=True, exist_ok=True)

        # Write config file
        config_file = sim_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Extract parameters
        params = config['parameters']
        f = params.get('line_mass', 1.5)
        beta = params.get('plasma_beta', 1.0)
        M = params.get('mach_number', 1.0)
        seed = config['random_seed']

        # Run Athena++ simulation
        # NOTE: Modify this path to point to your Athena++ executable
        athena_exec = os.environ.get('ATHENA_EXEC', '/path/to/athena++')

        cmd = [
            'python3',
            '$(pwd)/scripts/run_athena_simulation.sh',
            '--config', str(config_file),
            '--output', str(sim_dir)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=36000  # 10 hour timeout
        )

        if result.returncode == 0:
            return {
                'sim_id': config['sim_id'],
                'status': 'success',
                'sim_dir': str(sim_dir),
                'config': config
            }
        else:
            return {
                'sim_id': config['sim_id'],
                'status': 'failed',
                'error': result.stderr,
                'sim_dir': str(sim_dir),
                'config': config
            }

    except Exception as e:
        return {
            'sim_id': config['sim_id'],
            'status': 'error',
            'error': str(e),
            'config': config
        }

def main():
    """Main execution function."""
    import sys
    import os

    # Load job list
    job_list_file = Path('$OUTPUT_DIR') / 'job_list.json'

    if not job_list_file.exists():
        print(f"Error: Job list file not found: {job_list_file}")
        sys.exit(1)

    with open(job_list_file, 'r') as f:
        configs = json.load(f)

    print(f"Loaded {len(configs)} simulation configurations")

    # Submit jobs (respecting max concurrent limit)
    max_concurrent = $MAX_CONCURRENT
    results = []
    pending = []

    for i, config in enumerate(configs):
        # Submit job
        job_ref = run_simulation.remote(config, '$OUTPUT_DIR', i)
        pending.append((config['sim_id'], job_ref))

        # Wait if we've reached max concurrent
        if len(pending) >= max_concurrent:
            # Wait for one to complete
            ready, pending = ray.wait([job for _, job in pending], num_returns=1)
            sim_id, result = ray.get(ready[0])
            results.append(result)
            print(f"Completed simulation {sim_id}: {result['status']}")

            # Remove completed from pending
            pending = [(sid, job) for sid, job in pending if sid != sim_id]

    # Wait for remaining jobs
    if pending:
        print(f"Waiting for {len(pending)} remaining jobs...")
        for sim_id, job_ref in pending:
            try:
                result = ray.get(job_ref)
                results.append(result)
                print(f"Completed simulation {sim_id}: {result['status']}")
            except Exception as e:
                results.append({
                    'sim_id': sim_id,
                    'status': 'error',
                    'error': str(e)
                })

    # Write results summary
    results_file = Path('$OUTPUT_DIR') / 'campaign_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nCampaign complete!")
    print(f"Total simulations: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results if r['status'] == 'failed')}")
    print(f"Errors: {sum(1 for r in results if r['status'] == 'error')}")
    print(f"Results written to: {results_file}")

if __name__ == '__main__':
    main()
RAY_SCRIPT

chmod +x "$OUTPUT_DIR/run_campaign.py"

# Submit jobs
if [[ "$DRY_RUN" == true ]]; then
    echo "DRY RUN MODE - No jobs submitted"
    echo "Job script created at: $OUTPUT_DIR/run_campaign.py"
else
    echo "Submitting jobs to Ray cluster..."
    cd "$OUTPUT_DIR"
    python3 run_campaign.py
fi

echo "======================================"
echo "Campaign submission complete"
echo "======================================"
