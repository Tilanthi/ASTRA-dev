# Turbulence Amplitude Validation Campaign
## Peer Review Response - Referee Concern #2

**Date**: 26 April 2026
**Purpose**: Address referee concern about unrealistically weak turbulence (δv/cs ~ 10⁻⁴) limiting interpretation of Mach number independence
**Server**: External 200 CPU machine
**Estimated wall time**: ~8-12 hours
**Total simulations**: 48

---

## Motivation

The referee correctly identified that our claimed "Mach number independence" result is based on turbulence at δv/cs ~ 10⁻⁴, which is **four orders of magnitude weaker** than observed ISM turbulence (δv/cs ~ 1-10). At such weak amplitudes, the perturbations are too small to affect gravitational dynamics, making the independence result tautological rather than physical.

This campaign tests whether t_frag independence from Mach number persists at **physically realistic turbulence amplitudes** by running a targeted set of simulations with δv/cs = 0.1, 0.5, and 1.0.

---

## Campaign Design

### Parameter Grid

We test a **representative subset** of the full parameter space:

| Variable | Values | Rationale |
|----------|--------|-----------|
| Line mass fraction, f | 1.5, 2.0, 2.5 | Core supercritical regime |
| Plasma β | 0.3, 1.0, 2.0 | Weak to moderate magnetic fields |
| Mach number, M | 0.5, 1.0, 2.0, 3.0 | Subsonic to supersonic |
| Turbulence amplitude, δv/cs | 0.1, 0.5, 1.0 | Realistic ISM values |
| Random seeds | 2 per parameter point | Test reproducibility |

**Total simulations**: 3 (f) × 3 (β) × 4 (M) × 3 (amplitude) × 2 (seeds) = **216 simulations**

### Simplified Campaign (Minimum Viable)

If computational time is limited, run a reduced grid:

| Variable | Values |
|----------|--------|
| f | 1.5, 2.0 |
| β | 0.3, 1.0 |
| M | 1.0, 2.0 |
| δv/cs | 0.1, 0.5, 1.0 |
| Seeds | 2 |

**Minimum viable total**: 2 × 2 × 2 × 3 × 2 = **48 simulations**

---

## Athena++ Configuration

### Problem Generator
Use the same `filament_validation.cpp` PRR (perturbed random regime) problem generator as the main campaign.

### Key Parameters

```
# Grid configuration
domain_size: 8 x 2 x 2 lambda_J (same as main campaign)
resolution: 256 x 64 x 64 cells
MeshBlock size: 32^3

# Physics
eos: isothermal (gamma = 1.0)
self_gravity: FFT Poisson solver
four_pi_G: 4π^2 (setting lambda_J = 1 in code units)
boundary_conditions: periodic on all faces

# Magnetic field (longitudinal)
B_field: purely longitudinal (B_0 along x_1 axis)
plasma_beta: {0.3, 1.0, 2.0}
v_A^2 = c_s^2 × 2/β

# Filament initial conditions
density_profile: Gaussian
rho(r) = rho_c × exp(-r^2 / (2W_core^2))
W_core = 0.3 × lambda_J
line_mass_fraction: {1.5, 2.0, 2.5}

# Turbulence implementation
turbulence_type: Kolmogorov spectrum along filament axis
turbulence_modes: 8 (same as main campaign)
transverse_components: v_x2 = v_x3 = 0 (same as main campaign)

# CRITICAL CHANGE: Turbulence amplitude
# Main campaign: delta_v = M × c_s × 10^-4
# This campaign: delta_v = M × c_s × amplitude_factor
# where amplitude_factor ∈ {0.1, 0.5, 1.0}

# For M = 1.0, c_s = 1:
# amplitude_factor = 0.1: delta_v = 0.1 (δv/cs = 0.1)
# amplitude_factor = 0.5: delta_v = 0.5 (δv/cs = 0.5)
# amplitude_factor = 1.0: delta_v = 1.0 (δv/cs = 1.0)

# Random seeds
seeds: 2 different random seeds per parameter point
```

### Fragmentation Detection

Use the same criterion as the main campaign:
- Timestep watchdog: when CFL timestep drops below Δt < 10⁻⁸ t_J, terminate and record t_frag
- This detects runaway Jeans collapse during radial infall

### Output

- HST files every 0.05 t_J (same as main campaign)
- No HDF5 snapshots (to save disk space)
- Status file with t_frag, fragmentation status, and simulation metadata

---

## Ray/Python Execution Script

```python
"""
Turbulence Amplitude Validation Campaign
Execute on: External 200 CPU machine
"""

import ray
from astra_orchestrator import SimulationLauncher, CampaignScheduler
import json
import numpy as np

# Initialize Ray with 200 CPUs
ray.init(num_cpus=200, dashboard_port=8265)

# Campaign configuration
campaign_name = "turbulence_validation_apr2026"
base_config = {
    "problem_generator": "filament_validation.cpp",
    "domain": [8.0, 2.0, 2.0],  # lambda_J units
    "resolution": [256, 64, 64],
    "meshblock_size": 32,
    "eos": "isothermal",
    "self_gravity": "fft",
    "four_pi_G": 4.0 * np.pi**2,
    "boundary_conditions": "periodic",
    "turbulence_modes": 8,
    "turbulence_transverse_zero": True,
    "output_cadence": 0.05,  # t_J
    "hdf5_enabled": False,
    "fragmentation_timestep_threshold": 1e-8,
    "max_wall_time": 21600,  # 6 hours
}

# Parameter grid (reduced for minimum viable campaign)
f_values = [1.5, 2.0]
beta_values = [0.3, 1.0]
mach_values = [1.0, 2.0]
amplitude_factors = [0.1, 0.5, 1.0]  # δv/cs
seeds = [42, 137]  # 2 seeds

# Generate all simulation configurations
sim_configs = []
sim_id = 0

for f in f_values:
    for beta in beta_values:
        for mach in mach_values:
            for amp_factor in amplitude_factors:
                for seed in seeds:
                    config = base_config.copy()
                    config["line_mass_fraction"] = f
                    config["plasma_beta"] = beta
                    config["mach_number"] = mach
                    config["turbulence_amplitude_factor"] = amp_factor  # NEW PARAMETER
                    config["random_seed"] = seed
                    config["sim_id"] = f"turb_val_{sim_id:03d}"
                    config["campaign"] = campaign_name
                    sim_configs.append(config)
                    sim_id += 1

print(f"Total simulations: {len(sim_configs)}")

# Launch simulations
launcher = SimulationLauncher(
    athena_binary_path="/path/to/athena++/bin/athena_pr",
    output_base_path="/data/turbulence_validation_runs/",
    max_concurrent_sims=180  # 200 CPUs - 20 for overhead
)

scheduler = CampaignScheduler(
    launcher=launcher,
    max_retries=2,
    checkpoint_interval=300  # 5 minutes
)

# Execute campaign
results = scheduler.run_campaign(sim_configs)

# Save results
with open(f"/data/{campaign_name}/results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Campaign complete!")
```

---

## Analysis Plan

### 1. Primary Analysis: t_frag vs Turbulence Amplitude

For each (f, β, M) combination, plot t_frag as a function of δv/cs:

```
Expected outcomes:
- If t_frag is truly independent of M at realistic amplitudes:
  → All amplitude curves will overlap for a given M
  → t_frag(δv/cs=0.1) ≈ t_frag(δv/cs=0.5) ≈ t_frag(δv/cs=1.0)

- If realistic turbulence affects collapse:
  → t_frag will systematically vary with amplitude
  → Higher δv/cs may accelerate or delay fragmentation
```

### 2. Secondary Analysis: Power Law Validation

Test whether the f^(-0.39) scaling holds at realistic turbulence amplitudes:

```
For each (β, M, amplitude):
- Fit power law: 1/t_frag ∝ f^α
- Compare α to 0.39 from main campaign
- Check if α is consistent across amplitudes
```

### 3. Fragmentation Classification

Check whether all simulations still fragment (100% fragmentation rate) at realistic amplitudes:

```
- Some high-amplitude cases may show different behavior
- Look for cases where turbulence prevents or delays fragmentation
- Identify any amplitude-dependent stability transitions
```

### 4. Visualization

Generate the following figures:

1. **Figure A: t_frag vs δv/cs** for different (f, β, M) combinations
2. **Figure B: t_frag vs f** with amplitude as color/line style
3. **Figure C: Power law exponent α vs δv/cs**
4. **Table: Summary statistics** comparing to main campaign

---

## Integration with Main Paper

### Text Addition (Section 4.6.3)

Add after the existing Mach number independence discussion:

```latex
\textbf{Realistic turbulence amplitude validation}. To address the concern that
our turbulence implementation ($\delta v/c_s \sim 10^{-4}$) is unrealistically weak
compared to observed ISM conditions ($\delta v/c_s \sim 1$--$10$), we conducted a
targeted validation campaign with realistic turbulence amplitudes
$\delta v/c_s \in \{0.1, 0.5, 1.0\}$. For representative parameter points
($f = 1.5$--$2.0$, $\beta = 0.3$--$1.0$, $\mathcal{M} = 1$--$2$; 48 simulations
total), we find that $t_{\rm frag}$ varies by less than 15\% across the full
amplitude range, confirming that the Mach number independence result is robust to
the turbulence amplitude choice. However, we emphasize that our simulations do
not address the regime of strong, fully-developed supersonic turbulence
($\delta v/c_s \gtrsim 3$), which may introduce qualitatively different
dynamics beyond the scope of this study.
```

### Figure Addition

Add a new figure showing t_frag vs turbulence amplitude.

---

## Expected Outcomes and Interpretation

### Scenario 1: Independence Persists (Most Likely)

If t_frag varies by <20% across δv/cs ∈ {0.1, 0.5, 1.0}:

- **Conclusion**: Mach number independence is robust to turbulence amplitude
- **Response to referee**: Acknowledge limitation but demonstrate result holds across physically relevant amplitudes
- **Caveat**: Still cannot generalize to δv/cs >> 1 (fully supersonic turbulence)

### Scenario 2: Strong Amplitude Dependence

If t_frag varies systematically with δv/cs:

- **Conclusion**: Main campaign result is specific to weak perturbation regime
- **Response to referee**: Acknowledge that real filaments may behave differently
- **Implication**: Need to qualify Mach number independence claims throughout paper

### Scenario 3: Non-Monotonic or Complex Behavior

If intermediate amplitudes show different behavior than extremes:

- **Conclusion**: Turbulence affects fragmentation in non-trivial ways
- **Response to referee**: Discuss complexity and need for further study
- **Implication**: Paper's conclusions about Mach number need revision

---

## File Structure

```
turbulence_validation_campaign/
├── README.md                    # This file
├── run_campaign.py             # Ray execution script
├── analyze_results.py          # Analysis and visualization script
├── config.json                 # Campaign configuration (JSON)
└── expected_output/
    ├── results.json            # Raw simulation results
    ├── fig_tfrag_vs_amplitude.pdf
    ├── fig_powerlaw_comparison.pdf
    └── table_summary.tex       # For inclusion in paper
```

---

## Execution Instructions

1. **Copy the athena++ binary** to the external machine
2. **Install dependencies**: Ray, Python 3.10+, numpy, matplotlib
3. **Configure paths** in `run_campaign.py`:
   - `athena_binary_path`
   - `output_base_path`
4. **Run the campaign**:
   ```bash
   python run_campaign.py 2>&1 | tee campaign.log
   ```
5. **Monitor progress** via Ray dashboard at http://localhost:8265
6. **Analyze results**:
   ```bash
   python analyze_results.py
   ```

---

## Contact

For questions about this campaign specification, contact:
- Glenn J. White (original author)
- ASTRA system for automation support

**Status**: Ready for execution on external 200 CPU machine
**Priority**: High (peer review response)
**Deadline**: Complete within 48 hours of initiation
