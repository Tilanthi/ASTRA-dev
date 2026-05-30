# Realistic Turbulence Campaign (RTC) - June 2026
# Addresses Referee Concerns #1 (Transient Beading) and #2 (Turbulence Amplitude Gap)

## CRITICAL ISSUES TO ADDRESS

### Issue 1: Transient Beading Problem (Referee Concern #1)
THEO-1 finds λ/W = 2.66 ± 0.18 (within 5% of HGBS), but beading window Δt ≈ 0.04 tJ is insufficient for core growth (≳ 0.1 tJ required). This agreement may be coincidental. NEED TO TEST: Do transient density peaks survive in realistic turbulent environment? Can they grow to bound cores?

### Issue 2: Turbulence Amplitude Gap (Referee Concern #2)
- TAG campaign: δv/cs ~ 10⁻⁴ (linear regime only, NOT physical)
- Transonic campaign: Mturb = 0.5-1.9 (short of physical Mturb ~ 2-4)
- Campaign 5: validated only to δv/cs ≤ 1.0
NEED TO TEST: Does turbulence-independence extend to physical regime (Mturb ~ 2-4)?

## SIMULATION CAMPAIGN SPECIFICATION

### Campaign Name: Realistic Turbulence Campaign (RTC)
### Target: 1200 simulations (physical Mturb regime with fine temporal resolution)

### PRIMARY GOALS
1. Test whether transient beading survives in realistic turbulent environment (Mturb ~ 2-4)
2. Measure if turbulent peaks can grow to bound cores (t_growth ≳ 0.1 tJ)
3. Test field geometry dependence at physical turbulence amplitudes
4. Determine if turbulent compression enables longitudinal fragmentation in supercritical filaments

### PARAMETER GRID

#### Core Grid (960 simulations)
- Mach numbers: Mturb = 2.0, 2.5, 3.0, 3.5, 4.0 (5 values - PHYSICAL REGIME)
- Line-mass fractions: f = 1.0, 1.2, 1.5, 2.0 (4 values)
- Plasma β: β = 0.3, 0.5, 1.0, 2.0 (4 values)
- Field geometry: θ = 0° (longitudinal), 90° (perpendicular) (2 values)
- Random seeds: 3 per parameter point
- Subtotal: 5 × 4 × 4 × 2 × 3 = 480 simulations

#### Near-Critical Extension (240 simulations)
- Focused on f = 1.0, 1.2 (near-critical where longitudinal beading is expected)
- Full Mach range: Mturb = 2.0, 2.5, 3.0, 3.5, 4.0 (5 values)
- Full β range: β = 0.3, 0.5, 1.0, 2.0 (4 values)
- Longitudinal only (θ = 0°)
- Seeds: 6 per parameter point (higher statistics for key regime)
- Subtotal: 5 × 2 × 4 × 1 × 6 = 240 simulations

#### Supercritical Extension (240 simulations)
- Focused on f = 1.5, 2.0 (supercritical where radial collapse dominates)
- Full Mach range: Mturb = 2.0, 2.5, 3.0, 3.5, 4.0 (5 values)
- Full β range: β = 0.3, 0.5, 1.0, 2.0 (4 values)
- Both geometries (θ = 0°, 90°)
- Seeds: 3 per parameter point
- Subtotal: 5 × 2 × 4 × 2 × 3 = 240 simulations

#### Perpendicular-Field Focus (240 simulations)
- Focused on testing whether turbulence overcomes perpendicular suppression
- Full Mach range with extended sampling: Mturb = 2.0, 2.5, 3.0, 3.5, 4.0 (5 values)
- Full f range: f = 1.0, 1.2, 1.5, 2.0 (4 values)
- Perpendicular only (θ = 90°)
- Full β range: β = 0.3, 0.5, 1.0, 2.0 (4 values)
- Seeds: 3 per parameter point
- Subtotal: 5 × 4 × 4 × 1 × 3 = 240 simulations

TOTAL: 480 + 240 + 240 + 240 = 1200 simulations

### ATHENA++ CONFIGURATION

#### Problem Generator
filament_spacing_pr (same as TAG campaign)

#### Grid and Domain
- Resolution: 512 × 64 × 64 cells (matches TAG for consistency)
- Domain: 16λJ × 2λJ × 2λJ (longer domain for realistic turbulence)
- dx = 0.03125 λJ

#### MPI Configuration
- MPI ranks: 32 (8×2×2 meshblocks of 64×32×32)
- MeshBlock size: 64×32×32 cells

#### Output Configuration
- HDF5 snapshots: dt = 0.01 tJ (CRITICAL for transient beading detection)
- History files: dt = 0.001 tJ
- Fragmentation trigger: dt_Athena++ < 10⁻⁶ (DT_KILL)

#### Boundary Conditions
- Periodic on all faces (standard for filament fragmentation)

### TURBULENCE DRIVING SPECIFICATION

#### CRITICAL DIFFERENCE FROM PREVIOUS CAMPAIGNS
This campaign uses REALISTIC turbulence driving, not linear-regime seeding.

#### Driving Method
- Ornstein-Uhlenbeck (OU) stochastic driving
- Implementation: Based on Transonic Campaign but extended to Mturb = 2-4

#### Driving Parameters
- Driving wavelength: λ_drive = Lx/2 = 8λJ (half longitudinal domain)
- Driving timescale: τ_drive = t_cross = Lx / (2πv_turb)
- Correlation time: t_corr = 0.1 tJ
- Forcing: SOLID BODY rotation (no angular momentum injection)

#### Target Mach Numbers
- Physical regime: Mturb = 2.0, 2.5, 3.0, 3.5, 4.0
- These are REAL Mach numbers, not scaled by 10⁻⁴
- Velocity perturbations: δv/cs = Mturb (physical ISM values)

#### Initial Condition Generation
1. Start with laminar filament (King profile)
2. Add OU-driven velocity field with target Mturb
3. Evolve for 2 tJ to establish turbulent cascade BEFORE fragmentation analysis
4. Begin fine temporal sampling (0.01 tJ) after turbulent saturation

### FRAGMENTATION DETECTION CRITERIA

#### Longitudinal Beading Detection
- Density contrast threshold: C = ρ_max/ρ_background > 2.0
- Axial wavelength measurement: Fourier analysis of axial density profile
- Peak tracking: Track individual density peaks across time steps

#### Radial Collapse Detection
- CFL watchdog: dt_Athena++ < 10⁻⁶ (DT_KILL)
- Central density threshold: ρ_center > 10 × ρ_initial

#### Transient Peak Survival Analysis (CRITICAL for Referee Concern #1)
For each detected density peak:
- Record formation time: t_form (when C > 2.0 first crossed)
- Record destruction time: t_dest (when C < 2.0 or radial collapse completes)
- Calculate peak lifetime: τ_peak = t_dest - t_form
- Measure peak growth: track ρ_peak(t) over time
- Determine if peak reaches bound status: ρ_peak > ρ_Jeans at t_dest
- Output: τ_peak distribution for each (f, β, Mturb, θ) combination

### RAY CLUSTER EXECUTION SPECIFICATION

#### Cluster Configuration
- Cluster: fetch-agi@34.143.130.135 (200 vCPU available)
- Execution framework: Ray (NOT SLURM)
- Working directory: /dev/sdb 492 GB disk space

#### Ray Configuration
```python
# ray_config.py
import ray

ray.init(
    address='auto',
    num_cpus=200,
    object_store_memory=100_000_000_000,  # 100 GB
    runtime_env={"env_vars": {"OMP_NUM_THREADS": "1"}}
)
```

#### Parallel Execution Strategy
- Concurrency: 8 simulations simultaneously (uses 256 vCPU, within 200 vCPU budget with 32 MPI ranks per sim)
- Expected runtime per sim: 30-60 minutes (Mturb = 2-4 with fine sampling)
- Total wall time: ~150 hours (6-7 days)
- Disk space: ~120 GB raw HDF5, purged after each sim

#### Job Submission Template
```python
# submit_realistic_campaign.py
import ray
from ray.util.queue import Queue
import subprocess
import os

@ray.remote(num_cpus=32, memory=10_000_000_000)
def run_simulation(param_set):
    """Run single Athena++ simulation with Ray"""
    f, beta, mturb, theta, seed = param_set
    
    # Generate athena_input.txt
    generate_athena_config(f, beta, mturb, theta, seed)
    
    # Run Athena++
    result = subprocess.run(
        ['mpirun', '-n', '32', './athena', '-i', 'athena_input.txt'],
        capture_output=True, text=True
    )
    
    # Extract results
    results = extract_fragmentation_data(f, beta, mturb, theta, seed)
    
    # Purge HDF5
    subprocess.run(['rm', '-rf', 'hdf5/*.hdf5'])
    
    return results

def main():
    ray.init(address='auto', num_cpus=200)
    
    # Generate parameter grid
    param_sets = generate_parameter_grid()  # 1200 simulations
    
    # Submit jobs
    futures = []
    for params in param_sets:
        future = run_simulation.remote(params)
        futures.append(future)
        
        # Limit concurrency to 8
        if len(futures) >= 8:
            completed, futures = ray.wait(futures, num_returns=1)
            result = ray.get(completed[0])
            save_result(result)
    
    # Complete remaining
    for future in futures:
        result = ray.get(future)
        save_result(result)

if __name__ == '__main__':
    main()
```

### OUTPUT DATA PRODUCTS

#### Per-Simulation Outputs
- Fragmentation wavelength: λ/W (measured from density peaks)
- Fragmentation time: t_frag (longitudinal beading or radial collapse)
- Peak survival analysis: τ_peak distribution (CRITICAL for transient beading)
- Peak growth analysis: ρ_peak(t) evolution
- Final morphology: FULL, PARTIAL, RADIAL_ONLY, or STABLE

#### Campaign-Level Outputs
- CSV file: RTC_results_all1200.csv
- Figure: RTC-1_transient_survival_vs_Mturb.pdf (addresses Referee Concern #1)
- Figure: RTC-2_lW_vs_Mturb_physical.pdf (addresses Referee Concern #2)
- Figure: RTC-3_field_geometry_turbulent.pdf (field geometry × Mturb)
- Figure: RTC-4_supercritical_turbulent_fragmentation.pdf (supercritical × Mturb)
- Figure: RTC-5_perpendicular_suppression_vs_Mturb.pdf (does turbulence overcome suppression?)

### ANALYSIS INSTRUCTIONS

#### Analysis 1: Transient Peak Survival (Addresses Referee Concern #1)
```python
# analysis_transient_survival.py
import pandas as pd
import numpy as np

df = pd.read_csv('RTC_results_all1200.csv')

# Filter supercritical filaments (where transient beading is relevant)
supercritical = df[df['f'] >= 1.5]

# Calculate survival fraction
survival_fraction = supercritical.groupby(['Mturb', 'beta']).apply(
    lambda x: np.sum(x['tau_peak'] >= 0.1) / len(x)
)

# Plot: Survival fraction vs Mturb for each β
# Expected outcome: Does turbulence increase peak survival?
# If survival_fraction increases with Mturb → transient peaks survive longer
```

#### Analysis 2: Turbulence Amplitude Dependence (Addresses Referee Concern #2)
```python
# analysis_turbulence_dependence.py
import pandas as pd
import scipy.stats as stats

df = pd.read_csv('RTC_results_all1200.csv')

# Filter longitudinal field only
longitudinal = df[df['theta'] == 0]

# ANOVA: Does λ/W depend on Mturb?
groups = [group['lW'].values for name, group in longitudinal.groupby('Mturb')]
f_stat, p_value = stats.f_oneway(*groups)

# Regression: λ/W vs Mturb for each β
for beta in [0.3, 0.5, 1.0, 2.0]:
    subset = longitudinal[longitudinal['beta'] == beta]
    slope, intercept, r, p, se = stats.linregress(subset['Mturb'], subset['lW'])
    print(f"β={beta}: slope={slope:.3f}, r={r:.3f}, p={p:.3f}")
    
# Expected outcome: Does turbulence-independence hold at Mturb = 2-4?
```

#### Analysis 3: Perpendicular Suppression vs Turbulence
```python
# analysis_perpendicular_turbulence.py
import pandas as pd

df = pd.read_csv('RTC_results_all1200.csv')

# Fragmentation fraction for perpendicular fields
perpendicular = df[df['theta'] == 90]
frag_fraction = perpendicular.groupby(['Mturb', 'beta']).apply(
    lambda x: np.sum(x['morphology'] != 'RADIAL_ONLY') / len(x)
)

# Plot: Fragmentation fraction vs Mturb
# Expected outcome: Does turbulence overcome perpendicular suppression?
# If frag_fraction increases with Mturb → turbulence enables longitudinal fragmentation
```

### EXPECTED OUTCOMES AND INTERPRETATION

#### Outcome A: Transient Peaks Survive in Turbulence
- Observation: τ_peak increases with Mturb, approaches 0.1 tJ at Mturb ≥ 3
- Interpretation: Realistic turbulence enables density peaks to survive long enough to form bound cores
- Implication: THEO-1 agreement with HGBS is physically meaningful, not coincidental
- Paper impact: Resolves Referee Concern #1

#### Outcome B: Turbulence-Independence Breaks Down
- Observation: λ/W depends on Mturb in physical regime (significant correlation)
- Interpretation: Turbulence amplitude IS a controlling parameter at physical amplitudes
- Implication: Referee Concern #2 is valid - turbulence-independence claim only applies to linear regime
- Paper impact: Requires reframing turbulence-independence as linear-regime result only

#### Outcome C: Turbulence Overcomes Perpendicular Suppression
- Observation: Perpendicular fragmentation fraction increases with Mturb
- Interpretation: Turbulent compression enables longitudinal modes despite perpendicular field geometry
- Implication: Resolves Planck geometry tension - internal geometry can differ from external
- Paper impact: Provides pathway to reconcile field geometry with HGBS observations

### SUCCESS CRITERIA

#### Minimum Success (addresses Referee Concern #1)
- At least 20% of supercritical simulations show τ_peak ≥ 0.1 tJ at Mturb ≥ 3
- Demonstrates transient peaks can survive long enough to form bound cores

#### Moderate Success (addresses Referee Concern #2)
- Clear trend: λ/W depends on Mturb (p < 0.05) OR λ/W independent of Mturb (p > 0.05)
- Either outcome provides definitive answer to turbulence-amplitude question

#### Full Success
- Both concerns addressed simultaneously
- Transient peaks survive in turbulence
- Clear statement about turbulence dependence/independence in physical regime

### CONTINGENCY PLANS

#### If Transient Peaks Don't Survive
- Honest conclusion: THEO-1/HGBS agreement is coincidental
- Paper reframing: THEO-1 measures spacing of transient peaks, not core precursors
- Recommendation: Future work needs longer domain or different driving mechanism

#### If Turbulence-Independence Fails
- Honest conclusion: Laminar simulations do not predict HGBS behavior
- Paper reframing: Simulations establish laminar-limit regime structure only
- Recommendation: Future work needs full turbulent cascade simulations

### ESTIMATED RESOURCE REQUIREMENTS

#### Compute
- 1200 simulations × 32 MPI ranks × 30-60 min = 19200-38400 CPU-hours
- On 200 vCPU cluster: 150-300 hours (6-12 days)

#### Storage
- Raw HDF5: ~120 GB (temporary, purged after each sim)
- Final CSV: ~500 KB
- Figures: ~50 MB

#### Network
- Minimal: All computation local, only final results uploaded

### DELIVERABLES

1. Simulation configuration generator script
2. Ray job submission script
3. Analysis pipeline scripts (3 analyses above)
4. Results CSV file (RTC_results_all1200.csv)
5. Figures (5 figures as specified)
6. Campaign report (RTC_campaign_report.md)
7. Integration instructions for paper update

---

**Campaign Date**: June 2026
**Author**: ASTRA-PA (automated simulation specification system)
**PI**: Glenn J. White (Open University)
**Cluster**: fetch-agi@34.143.130.135 (200 vCPU)
**Total simulations**: 1200
**Expected wall time**: 6-7 days
