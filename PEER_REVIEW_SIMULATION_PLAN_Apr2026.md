# Peer Review Response Simulation Campaign Plan
# Created: 27 April 2026
# Target: 200 CPU cluster, Ray scheduler
# Goal: Address peer review concerns about regime mismatch, negative results, and validation

## Campaign Overview

This campaign comprises 5 targeted sub-campaigns totaling approximately 400-500 new Athena++ simulations to definitively address the peer review concerns:

### Campaign Summary
| Campaign | Simulations | Priority | Goal |
|----------|-------------|----------|-------|
| SUPERCRITICAL-LONG | 120 | CRITICAL | Measure λ/W directly in supercritical regime |
| BRIDGE-GRID | 150 | CRITICAL | Validate f-dependence bridging near-critical to supercritical |
| TIMEOUT-CONVERGENCE | 80 | HIGH | Validate timeout adequacy across all parameter space |
| CALIBRATION-VALIDATION | 60 | HIGH | Re-derive calibration factor with uncertainty breakdown |
| GEOMETRY-VARIATION | 60 | MEDIUM | Test field geometry effects on λ/W measurement |

**Total: ~470 simulations**

---

## CRITICAL CONCERN #1: Regime Mismatch and Negative Result

### Problem
All 654 supercritical simulations (f = 1.1-3.0) showed only radial collapse with <0.02% longitudinal variance. The λ/W = 3.70 prediction is extrapolated from near-critical regime (f ≈ 1.0-1.2) where beading was observed, NOT measured directly in the supercritical regime that HGBS filaments occupy (f ≈ 1.5-3.0).

### Root Cause Analysis
The original domain length (L = 8λJ) may be insufficient for supercritical filaments. As f increases:
- Collapse accelerates (shorter t_frag)
- Radial collapse dominates over longitudinal instability
- Fragmentation wavelength may exceed domain length
- Need longer domains to allow longitudinal modes to develop

### Solution: SUPERCRITICAL-LONG Campaign

**Objective**: Directly measure λ/W in supercritical regime by using extended longitudinal domains.

**Parameter Space**:
```
f = 1.5, 2.0, 2.5 (representative HGBS values)
β = 0.3, 1.0, 5.0 (weak to strong field)
M = 1.0 (fiducial turbulence)
Seeds: 3 per parameter point for statistics
Total: 3 × 3 × 3 = 27 points
```

**Domain Configurations**:
```
LONG-1: L = 16λJ, Ly = Lz = 2λJ, Resolution: 512 × 64 × 64
LONG-2: L = 24λJ, Ly = Lz = 2λJ, Resolution: 768 × 64 × 64
LONG-3: L = 32λJ, Ly = Lz = 2λJ, Resolution: 1024 × 64 × 64
```

**Key Innovation**: Use aspect ratio Ly/Lz = 1 (square transverse) instead of 2×1 to reduce transverse computational cost while maintaining fidelity.

**Timeout Strategy**:
```
Hard timeout: t = 6.0 tJ (prevents runaway)
Watchdog: Monitor for dt < 1e-10 tJ (fragmentation detection)
HST output: Every 0.01 tJ (high temporal resolution for beading detection)
```

**Success Criteria**:
1. Detect longitudinal density peaks with contrast > 10%
2. Measure λ/W directly from peak positions
3. Compare with near-critical extrapolation
4. Quantify uncertainty from domain size effects

**Output Requirements**:
- Peak position vs. time
- Longitudinal density variance evolution
- Final fragmentation wavelength λ
- Core mass spectrum

---

## CRITICAL CONCERN #2: Extrapolation Validation

### Problem
The λ/W = 3.70 prediction is based on extrapolating from near-critical regime (f < 1.2) to supercritical regime (f = 1.5-3.0). Need to validate this extrapolation.

### Solution: BRIDGE-GRID Campaign

**Objective**: Dense sampling of f = 1.1-2.0 to map the transition from near-critical to supercritical behavior.

**Parameter Space**:
```
f = 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0 (8 values)
β = 0.3, 1.0, 5.0
M = 1.0
Domain: L = 12λJ (intermediate length)
Resolution: 384 × 48 × 48
Seeds: 2 per point
Total: 8 × 3 × 2 = 48 simulations
```

**Alternative EOS Tests** (to slow fragmentation):
```
γ = 0.9 (slightly sub-isothermal) - 16 sims at f = 1.5-2.0, β = 1.0
This extends t_frag by ~30%, giving more time for longitudinal structure to develop
```

**Analysis Products**:
1. λ vs f curve - test power law λ ∝ f^α
2. Transition f_crit where λ measurement becomes impossible
3. Density contrast C vs f at fragmentation
4. Comparison with analytical predictions

---

## CRITICAL CONCERN #3: Timeout Artifact Validation

### Problem
DTC campaign used 600-second timeout that was insufficient for β = 0.3, M = 1. Need to verify no other regions of parameter space suffer from similar timeout artifacts.

### Solution: TIMEOUT-CONVERGENCE Campaign

**Objective**: Systematic timeout sensitivity tests across parameter space to validate all boundary classifications.

**Test Matrix**:
```
Test 1: β = 0.3, M = 1.0, f = 1.4-2.2 (already done - confirm)
Test 2: β = 0.3, M = 2.0, f = 1.6-2.0 (new - test Mach dependence)
Test 3: β = 0.3, M = 3.0, f = 1.8-2.2 (new - higher Mach)
Test 4: β = 0.3, M = 1.0, f = 2.5, 3.0 (new - very supercritical)
Test 5: β = 0.5, M = 1.0, f = 1.6-2.0 (new - intermediate field)
Test 6: β = 1.0, M = 0.5, f = 1.4-1.8 (new - subsonic)
```

**Timeout Protocol**:
```
For each test point, run with:
- Short timeout: 600 s (baseline)
- Medium timeout: 3600 s (1 hour)
- Long timeout: 21600 s (6 hours)
- Compare t_frag and classification
```

**Expected Outcomes**:
- If t_frag(long) ≈ t_frag(medium): timeout adequate
- If t_frag(long) >> t_frag(medium): need extended timeout
- Create map of "timeout-safe" vs "timeout-uncertain" regions

---

## CRITICAL CONCERN #4: Calibration Formula Validation

### Problem
The λ_frag = 1.11 × λ_MJ calibration has ±0.12 uncertainty (~11%) but derivation is not fully documented. Need to:
1. Re-derive calibration from scratch with full uncertainty breakdown
2. Test f, β, M dependence individually
3. Validate across full parameter space

### Solution: CALIBRATION-VALIDATION Campaign

**Objective**: Systematic re-derivation of calibration factor with full uncertainty quantification.

**Parameter Grid**:
```
Fixed: θ = 30°, 60° (two oblique angles)
Vary: f = 1.5, 2.0, 2.5
Vary: β = 0.5, 1.0, 2.0
Vary: M = 1.0, 2.0
Seeds: 3 per point
Total: 2 × 3 × 3 × 2 × 3 = 108 simulations
```

**Measurement Protocol**:
1. Measure λ_sim from density peak positions
2. Calculate λ_MJ(θ, β) from theoretical dispersion relation
3. Compute calibration factor: C = λ_sim / λ_MJ
4. Compute mean and std across parameters and seeds

**Analysis**:
- C vs f dependence (should be weak)
- C vs β dependence (test referee concern)
- C vs θ dependence (validate angular trend)
- C vs M dependence (should be none)
- Full covariance matrix of uncertainties

**Statistical Approach**:
```
Use hierarchical Bayesian model:
C ~ Normal(μ, σ²)
μ ~ Normal(1.11, 0.12²)  # Prior
 likelihood: data | C, parameters
Posterior: P(μ, σ | data)
```

---

## Campaign Implementation Details

### Computational Requirements

**Per-Simulation Resource Estimates**:
```
Domain size 8×2×2: ~4 hours on 64 cores
Domain size 16×2×2: ~12 hours on 64 cores
Domain size 24×2×2: ~24 hours on 64 cores
Domain size 32×2×2: ~36 hours on 64 cores

Total core-hours estimate: ~10,000 CPU-hours
```

### Ray Configuration

**Cluster Setup**:
```python
import ray
ray.init(address='auto')  # Connect to existing Ray cluster

# Resource allocation
@ray.remote(num_cpus=64, memory=200_000_000_000)  # 64 cores, 200GB RAM
def run_athena_simulation(config):
    # Launch Athena++ simulation
    # Monitor for completion
    # Return results
    pass
```

**Batch Submission**:
```python
# Parallel execution of up to 4 concurrent simulations
# (200 cores total / 64 cores per sim = 3 concurrent + headroom)
```

### File Organization

```
astra_peer_review_response_campaigns/
├── configs/
│   ├── supercritical_long/
│   │   ├── f1.5_beta0.3/
│   │   ├── f1.5_beta1.0/
│   │   └── ...
│   ├── bridge_grid/
│   ├── timeout_convergence/
│   ├── calibration_validation/
│   └── geometry_variation/
├── scripts/
│   ├── generate_configs.py
│   ├── submit_campaign.py
│   ├── monitor_progress.py
│   ├── extract_beading.py
│   ├── analyze_lambda.py
│   └── generate_figures.py
├── analysis/
│   ├── lambda_measurements.csv
│   ├── calibration_analysis.py
│   ├── timeout_validation.py
│   └── final_report.ipynb
└── README.md
```

### Simulation Config Generator

**Python Script**: `generate_configs.py`
```python
#!/usr/bin/env python3
"""
Generate Athena++ simulation configs for peer review response campaign.
"""

import json
import itertools
from pathlib import Path

def generate_config(domain_type, f, beta, M, seed, campaign_name):
    """
    Generate Athena++ input file for a single simulation.

    Parameters
    ----------
    domain_type : str
        'standard', 'long', 'extended'
    f : float
        Line mass fraction
    beta : float
        Plasma beta
    M : float
        Mach number
    seed : int
        Random seed
    campaign_name : str
        Campaign identifier

    Returns
    -------
    dict
        Simulation configuration
    """
    # Domain dimensions in code units
    if domain_type == 'standard':
        Lx, Ly, Lz = 8.0, 2.0, 2.0
        Nx, Ny, Nz = 256, 64, 64
    elif domain_type == 'long':
        Lx, Ly, Lz = 16.0, 1.0, 1.0  # Square transverse, 2x longitudinal
        Nx, Ny, Nz = 512, 64, 64
    elif domain_type == 'extended':
        Lx, Ly, Lz = 24.0, 1.0, 1.0
        Nx, Ny, Nz = 768, 64, 64
    elif domain_type == 'verylong':
        Lx, Ly, Lz = 32.0, 1.0, 1.0
        Nx, Ny, Nz = 1024, 64, 64
    else:
        raise ValueError(f"Unknown domain_type: {domain_type}")

    # Physics parameters
    gamma = 1.0  # Isothermal
    cs = 1.0  # Sound speed
    four_pi_G = 4.0 * np.pi**2  # Normalized so lambda_J = 1

    # Magnetic field
    v_A = cs * np.sqrt(2.0 / beta)

    # Turbulence amplitude
    dv = M * cs * 1e-4  # Seeded perturbation amplitude

    config = {
        'problem': 'filament_fragmentation',
        'domain': {
            'Lx': Lx,
            'Ly': Ly,
            'Lz': Lz,
            'Nx': Nx,
            'Ny': Ny,
            'Nz': Nz
        },
        'physics': {
            'gamma': gamma,
            'cs': cs,
            'four_pi_G': four_pi_G,
            'beta': beta,
            'v_A': v_A,
            'M': M,
            'dv': dv
        },
        'filament': {
            'f': f,
            'W_core': 0.3,  # Core half-width in lambda_J
            'profile': 'gaussian'
        },
        'numerics': {
            'dt_initial': 1e-4,
            'dt_min': 1e-12,
            'tlim': 3.0,  # Hard timeout in t_J
            'hst_interval': 0.01,  # High temporal output for beading detection
            'dt_output': 0.1,
            'cfl_number': 0.3
        },
        'output': {
            'basename': f"{campaign_name}_f{f}_beta{beta}_M{M}_s{seed}",
            'directory': f"outputs/{campaign_name}/",
            'dump_fields': ['rho', 'vx1', 'vx2', 'vx3', 'B1'],
            'hst_fields': ['rho', 'vx1', 'vx2', 'vx3']
        },
        'random_seed': seed,
        'metadata': {
            'campaign': campaign_name,
            'domain_type': domain_type,
            'f': f,
            'beta': beta,
            'M': M,
            'seed': seed
        }
    }

    return config

def generate_campaign_configs(campaign_name, param_grid):
    """Generate all configs for a campaign."""
    configs = []
    for params in itertools.product(*param_grid.values()):
        config = generate_config(*params, campaign_name)
        configs.append(config)

    return configs

# Campaign parameter grids
SUPERCRITICAL_LONG_GRID = {
    'f': [1.5, 2.0, 2.5],
    'beta': [0.3, 1.0, 5.0],
    'seed': [42, 137, 256]
}

BRIDGE_GRID = {
    'domain_type': ['long'],
    'f': [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0],
    'beta': [0.3, 1.0, 5.0],
    'M': [1.0],
    'seed': [42, 137]
}

# Generate configs
if __name__ == '__main__':
    import numpy as np

    print("Generating simulation configurations...")

    # SUPERCRITICAL-LONG campaign
    supercrit_configs = []
    for domain_type in ['long', 'extended', 'verylong']:
        for params in itertools.product(
            [domain_type],
            SUPERCRITICAL_LONG_GRID['f'],
            SUPERCRITICAL_LONG_GRID['beta'],
            SUPERCRITICAL_LONG_GRID['M'],
            SUPERCRITICAL_LONG_GRID['seed']
        ):
            config = generate_config(*params, 'SUPERCRITICAL_LONG')
            supercrit_configs.append(config)

    print(f"Generated {len(supercrit_configs)} SUPERCRITICAL_LONG configs")

    # Save configs
    output_dir = Path('configs')
    output_dir.mkdir(exist_ok=True, parents=True)

    for i, config in enumerate(supercrit_configs):
        config_file = output_dir / f"config_{i:04d}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    print(f"Configs saved to {output_dir}")
```

### Analysis Pipeline

**Beading Detection Script**: `extract_beading.py`
```python
#!/usr/bin/env python3
"""
Extract longitudinal beading pattern from simulation outputs.
Detects density peaks and measures fragmentation wavelength.
"""

import numpy as np
import h5py
from scipy.signal import find_peaks
from pathlib import Path

def extract_beading_pattern(snapshot_file):
    """
    Extract beading pattern from a simulation snapshot.

    Parameters
    ----------
    snapshot_file : str or Path
        Path to HDF5 snapshot file

    Returns
    -------
    dict
        Beading analysis results
    """
    # Load density field
    with h5py.File(snapshot_file, 'r') as f:
        rho = f['rho'][:]  # Shape: (Nz, Ny, Nx, 1)

    # Average over transverse directions
    rho_1D = rho.mean(axis=(0, 1)).flatten()  # Longitudinal profile

    # Normalize
    rho_mean = rho_1D.mean()
    rho_normalized = (rho_1D - rho_mean) / rho_mean

    # Detect peaks
    peaks, properties = find_peaks(
        rho_normalized,
        height=0.1,  # Minimum 10% contrast
        distance=20  # Minimum separation
    )

    if len(peaks) == 0:
        return {
            'n_peaks': 0,
            'lambda_measured': None,
            'longitudinal_variance': np.var(rho_normalized),
            'status': 'no_beading'
        }

    # Measure wavelength
    peak_positions = peaks  # In grid units
    lambda_grid = np.diff(peak_positions).mean()
    lambda_physical = lambda_grid * (8.0 / 256.0)  # Convert to code units

    # Convert to physical units (W_core = 0.3 lambda_J)
    lambda_normalized = lambda_physical

    return {
        'n_peaks': len(peaks),
        'peak_positions': peak_positions.tolist(),
        'lambda_measured': lambda_normalized,
        'longitudinal_variance': np.var(rho_normalized),
        'peak_contrasts': (rho_normalized[peaks] - rho_normalized.min()).tolist(),
        'status': 'beading_detected'
    }

def analyze_time_series(output_dir):
    """Analyze beading evolution through time."""
    hst_files = sorted(Path(output_dir).glob('*.hst'))

    results = []
    for hst_file in hst_files:
        result = extract_beading_pattern(hst_file)
        results.append(result)

    return results
```

**Calibration Analysis Script**: `analyze_calibration.py`
```python
#!/usr/bin/env python3
"""
Analyze calibration factor from simulation results.
"""

import numpy as np
import pandas as pd
from scipy.stats import linregress
import pymc3 as pm

def compute_calibration_factor(sim_lambda, theta, beta, f, M):
    """
    Compute calibration factor C = λ_sim / λ_MJ.

    λ_MJ is computed from dispersion relation for oblique field.
    """
    # Magneto-Jeans wavelength for oblique field
    # Based on Nakamura 1993, with field geometry correction
    beta_eff = beta / (np.cos(np.radians(theta))**2)

    # Simplified formula for λ_MJ (in units of W_core)
    # This is the theoretical prediction we're calibrating
    lambda_MJ = 4.0 / np.sqrt(1.0 + 2.0 / beta_eff)

    C = sim_lambda / lambda_MJ
    return C

def hierarchical_calibration_analysis(data):
    """
    Bayesian hierarchical model for calibration factor.

    Parameters
    ----------
    data : DataFrame
        Columns: sim_lambda, theta, beta, f, M, seed

    Returns
    -------
    arviz.InferenceData
        Posterior samples
    """
    with pm.Model() as model:
        # Priors
        mu = pm.Normal('mu', mu=1.11, sigma=0.12)
        sigma = pm.HalfNormal('sigma', sigma=0.1)

        # Likelihood
        for i, row in data.iterrows():
            lambda_MJ = compute_calibration_factor(
                0.0,  # Placeholder - will compute in likelihood
                row['theta'],
                row['beta'],
                row['f'],
                row['M']
            )
            pm.Normal(f'obs_{i}', mu=mu, sigma=sigma, observed=row['sim_lambda'])

        trace = pm.sample(2000, tune=1000, return_inferencedata=True)

    return trace
```

### Execution Script

**Ray Submission Script**: `submit_campaign.py`
```python
#!/usr/bin/env python3
"""
Submit peer review response campaign to Ray cluster.
"""

import ray
from pathlib import Path
import subprocess
import time
from generate_configs import generate_campaign_configs

# Initialize Ray
ray.init(address='auto')

@ray.remote(num_cpus=64, memory=200_000_000_000)
def run_athena_simulation(config_path):
    """
    Execute Athena++ simulation on remote node.

    Returns simulation output path.
    """
    # Load config
    with open(config_path) as f:
        config = json.load(f)

    # Build Athena++ command
    # (This would be adapted to your specific setup)
    cmd = [
        'athena++',
        '-i', config_path,
        '-t', str(config['numerics']['tlim']),
        '> /dev/null', '2>&1'
    ]

    # Run simulation
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Simulation failed: {config['output']['basename']}")

    return config['output']['directory']

def submit_campaign(campaign_name, param_grid, max_concurrent=4):
    """
    Submit campaign to Ray cluster.

    Parameters
    ----------
    campaign_name : str
    Campaign identifier
    param_grid : dict
        Parameter grid specification
    max_concurrent : int
        Maximum concurrent simulations
    """
    # Generate configs
    configs = generate_campaign_configs(campaign_name, param_grid)

    # Save configs
    config_dir = Path('configs') / campaign_name
    config_dir.mkdir(exist_ok=True, parents=True)

    config_paths = []
    for i, config in enumerate(configs):
        config_path = config_dir / f"config_{i:04d}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        config_paths.append(str(config_path))

    # Submit to Ray
    futures = []
    for config_path in config_paths[:max_concurrent]:
        future = run_athena_simulation.remote(config_path)
        futures.append(future)

    # Monitor completion
    completed = 0
    while completed < len(futures):
        ready, not_ready = ray.wait(futures, num_returns=1, timeout=10)
        if ready:
            result = ray.get(ready[0])
            completed += 1
            print(f"Completed {completed}/{len(futures)}: {result}")
```

### Monitoring and Progress Tracking

**Progress Monitor**: `monitor_progress.py`
```python
#!/usr/bin/env python3
"""
Monitor simulation progress and detect issues.
"""

import subprocess
from pathlib import Path

def check_simulation_status(output_dir):
    """Check if simulation has completed or failed."""
    # Check for final output file
    final_file = Path(output_dir) / "final_output.h5"
    log_file = Path(output_dir) / "simulation.log"

    if final_file.exists():
        return 'completed'
    elif log_file.exists():
        # Check log for errors
        with open(log_file) as f:
            if 'ERROR' in f.read() or 'FATAL' in f.read():
                return 'failed'
        return 'running'
    else:
        return 'not_started'

def generate_progress_report(campaign_name):
    """Generate HTML progress report for campaign."""
    configs_dir = Path('configs') / campaign_name
    outputs_dir = Path('outputs') / campaign_name

    # Check all simulations
    statuses = {}
    for config_file in sorted(configs_dir.glob('*.json')):
        config_id = config_file.stem
        # Extract parameters from config
        with open(config_file) as f:
            import json
            config = json.load(f)
        output_dir = outputs_dir / config['output']['basename']
        status = check_simulation_status(output_dir)
        statuses[config_id] = {
            'f': config['filament']['f'],
            'beta': config['physics']['beta'],
            'M': config['physics']['M'],
            'seed': config['random_seed'],
            'status': status
        }

    # Generate HTML report
    html = f"""
    <html>
    <head><title>{campaign_name} Progress</title></head>
    <body>
    <h1>{campaign_name} Campaign Progress</h1>
    <table border="1">
    <tr><th>Config ID</th><th>f</th><th>β</th><th>M</th><th>Seed</th><th>Status</th></tr>
    """

    for config_id, info in statuses.items():
        color = {'completed': 'green', 'running': 'yellow', 'failed': 'red', 'not_started': 'gray'}
        html += f"""
        <tr><td>{config_id}</td>
        <td>{info['f']}</td>
        <td>{info['beta']}</td>
        <td>{info['M']}</td>
        <td>{info['seed']}</td>
        <td style="background-color:{color[info['status']]}">{info['status']}</td>
        </tr>
        """

    html += "</table></body></html>"

    report_file = Path(f"progress_{campaign_name}.html")
    with open(report_file, 'w') as f:
        f.write(html)

    print(f"Progress report saved to {report_file}")
```

---

## Final Report Structure

All analysis results should be compiled into a comprehensive report:

**Analysis Notebook**: `final_report.ipynb`
```python
{
 "cells": [
    {
        "cell_type": "markdown",
        "source": "# Executive Summary\n\n..."
    },
    {
        "cell_type": "code",
        "source": "# Import all analysis results\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt"
    },
    {
        "cell_type": "markdown",
        "source": "## SUPERCRITICAL-LONG Campaign Results\n\n..."
    },
    {
        "cell_type": "code",
        "source": "# Plot λ vs f for different domain lengths\nplt.figure()\n..."
    },
    {
        "cell_type": "markdown",
        "source": "## BRIDGE-GRID Campaign Results\n\n### Validation of Extrapolation\n\n..."
    },
    {
        "cell_type": "code",
        "source": "# Power law fit to λ(f) data\nfrom scipy.optimize import curve_fit\n..."
    },
    {
        "cell_type": "markdown",
        "source": "## Calibration Validation\n\n### Re-derived Calibration Factor\n\n..."
    },
    {
        "cell_type": "code",
        "source": "# Hierarchical Bayesian model\nimport pymc3 as pm\n..."
    },
    {
        "cell_type": "markdown",
        "source": "## Conclusions\n\n### Key Findings\n\n### Implications for Peer Review Response\n\n### Limitations and Future Work"
    }
    ]
}
```

---

## Packaging and Delivery

### Archive Structure
```
peer_review_response_package_20260427.tar.gz
├── configs/                    # All simulation configs
│   ├── supercritical_long/
│   ├── bridge_grid/
│   ├── timeout_convergence/
│   ├── calibration_validation/
│   └── geometry_variation/
├── scripts/                    # All analysis scripts
├── analysis/                    # All analysis results
│   ├── lambda_measurements.csv
│   ├── calibration_results.csv
│   ├── timeout_validation.csv
│   └── figures/
│       ├── fig_lambda_vs_f.pdf
│       ├── fig_calibration_validation.pdf
│       ├── fig_timeout_map.pdf
│       └── fig_domain_convergence.pdf
├── reports/
│   ├── executive_summary.pdf
│   ├── final_report.ipynb
│   └── peer_review_response.md
└── README.md
```

### GitHub Delivery Path

**Repository**: `Tilanthi/ASTRA-dev`

**File path**: `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/peer_review_response_package_20260427.tar.gz`

**Push commands**:
```bash
# Create the archive
tar -czvf peer_review_response_package_20260427.tar.gz \
    configs/ \
    scripts/ \
    analysis/ \
    reports/ \
    README.md

# Push to Glenn's GitHub
git add peer_review_response_package_20260427.tar.gz
git commit -m "Add peer review response simulation package (April 2026)"
git push origin main

# The file will be available at:
# https://github.com/Tilanthi/ASTRA-dev/blob/main/peer_review_response_package_20260427.tar.gz
```

---

## Execution Timeline

**Week 1**: Setup and validation
- Generate all simulation configs
- Test 2-3 simulations per campaign
- Validate analysis pipeline
- Push initial package to GitHub

**Week 2-3**: Main execution
- Run SUPERCRITICAL-LONG (highest priority)
- Run BRIDGE-GRID
- Run TIMEOUT-CONVERGENCE
- Monitor and track progress

**Week 4**: Completion and analysis
- Run CALIBRATION-VALIDATION
- Run GEOMETRY-VARIATION
- Extract all measurements
- Generate all figures

**Week 5**: Final reporting
- Complete all analysis
- Write final report
- Create final package
- Push to GitHub

---

## Risk Mitigation

**Risk 1**: SUPERCRITICAL-LONG simulations may still show only radial collapse
- **Mitigation**: Use very long domains (up to 32λJ) and high temporal resolution HST output
- **Fallback**: If still no beading, this IS a definitive negative result and should be clearly reported as such

**Risk 2**: Computational resource requirements
- **Mitigation**: Use square transverse domain (1×1 instead of 2×1) reduces cost by ~30%
- **Fallback**: Reduce number of f values tested, prioritize f=2.0 (most relevant)

**Risk 3**: Ray scheduling issues
- **Mitigation**: Limit to 3-4 concurrent max, monitor memory usage
- **Fallback**: Submit in smaller batches if needed

**Risk 4**: Data analysis pipeline breaks
- **Mitigation**: Test pipeline on existing simulation data before main campaign
- **Fallback**: Use simpler analysis methods (manual measurement) if automated pipeline fails

---

## Success Criteria

Each campaign will be considered successful if:

1. **SUPERCRITICAL-LONG**: Direct measurement of λ/W in at least 2 of 3 (f=1.5, 2.0, 2.5) supercritical cases
2. **BRIDGE-GRID**: Continuous mapping of λ(f) from f=1.1 to f=2.0 with <20% uncertainty
3. **TIMEOUT-CONVERGENCE**: Clear classification of which regions are timeout-safe vs. timeout-uncertain
4. **CALIBRATION-VALIDATION**: Calibration factor re-derived with <5% uncertainty breakdown by parameter
5. **GEOMETRY-VARIATION**: Understanding of how field geometry affects λ measurement in supercritical regime

---

## Next Steps

1. Review and validate this plan
2. Set up Ray cluster environment
3. Generate all simulation configs
4. Test analysis pipeline on existing data
5. Begin SUPERCRITICAL-LONG campaign (highest priority)
6. Push initial package to GitHub for tracking

**Total Estimated Timeline**: 5 weeks
**Total Estimated Cost**: ~10,000 CPU-hours
**Deliverable**: Comprehensive tar.gz package with all results, analysis, and figures
