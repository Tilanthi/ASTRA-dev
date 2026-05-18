# Simulation Parameters for Transonic Turbulence Campaign

## Parameter Space Philosophy

The referee identified a critical gap: our previous turbulence simulations achieved only **M_turb ≈ 0.15–0.35**, while real HGBS filaments exhibit **M ~ 1–4**. This campaign systematically explores transonic/supersonic regime.

## Reference Values for HGBS Filaments

From paper Section 2.1 and literature:
- **Density**: n ≈ 10⁴ cm⁻³ (characteristic of HGBS filaments)
- **Temperature**: T ≈ 10–15 K
- **Sound speed**: c_s ≈ 0.19 km/s (for T = 10 K)
- **Jeans length**: λ_J ≈ 0.35 pc (for HGBS conditions)
- **Filament width**: W_fil ≈ 0.10 pc (Arzoumanian et al. 2011)

## Simulation Domain Specifications

### Standard Domain (Phase 1: Resolution Test)
```
Geometry: 8 × 2 × 2 λ_J
Units: Normalized to λ_J (λ_J = 1 by construction)
Resolution:
  - 256³: 512 × 128 × 128 cells (baseline)
  - 384³: 768 × 192 × 192 cells (intermediate)
  - 512³: 1024 × 256 × 256 cells (target)

Grid spacing (512³):
  - Δx = 8/1024 = 0.0078 λ_J ≈ 2.7 × 10⁻³ pc
  - This resolves Jeans scale with ~100 cells/λ_J
```

### Extended Domain (Phase 2: Full Campaign)
```
Geometry: 16 × 4 × 4 λ_J
Resolution: 512³
Cell count: 4.2 billion cells
```

**Note**: Extended domain reduces periodicity artifacts and allows larger turbulent eddies to develop.

## Critical Parameters

### 1. Filament Initial Conditions

#### Density Profile
```python
# Gaussian filament profile
def filament_density(r, R_core, rho_0):
    """
    r: radial distance from filament axis
    R_core: core radius (0.3 λ_J)
    rho_0: central density (normalized to 1)
    """
    return rho_0 * exp(-r**2 / (2 * R_core**2))
```

**In athena.input:**
```python
<problem>
# Initial condition
problem_id = 1
# Gamma = 1.0 for isothermal
# Other parameters set in problem generator
</problem>
```

#### Line-Mass Fraction
```
f = M_line / M_crit
M_crit = 16.3 M_sun/pc (for T = 10 K)
```

**Campaign values:**
- f = 1.2: Near-critical
- f = 1.5: Marginally supercritical (HGBS lower bound)
- f = 2.0: Moderately supercritical (HGBS upper range)

### 2. Magnetic Field Configuration

#### Plasma Beta
```
β = c_s² / v_A² = 8πρc_s² / B²
```

**Campaign values:**
- β = 0.5: Strong field (equipartition at f ≈ 2)
- β = 1.0: Equipartition field
- β = 2.0: Weak field

#### Field Geometry
```
θ = 0°: Longitudinal (B along filament axis)
θ = 90°: Perpendicular (B transverse to axis)
```

### 3. Turbulent Driving

#### Ornstein-Uhlenbeck (OU) Forcing
```python
# Key parameters in athena.input:
<problem>
# Driving parameters
driving_scale = 1.0 to 3.0         # Amplitude
driving_corrlength = 2.0        # Correlation length (λ_J)
driving_auto = true              # Auto-determined driving
driving_decayscale = 0.1        # Damping time (t_J)
</problem>
```

**Target Mach numbers:**
```
M_driven = 1.0 → aim for M_turb ≈ 0.8–1.2
M_driven = 2.0 → aim for M_turb ≈ 1.5–2.5
M_driven = 3.0 → aim for M_turb ≈ 2.5–3.5
```

### 4. Boundary Conditions
```python
# In athena.input:
<mesh>
ix1_bc = periodic
ix2_bc = outflow
ox1_bc = periodic
ox2_bc = outflow
ix3_bc = outflow
ox3_bc = outflow
</mesh>
```

**Rationale:**
- **X-direction (along filament)**: Periodic allows fragmentation along infinite cylinder
- **Y/Z-directions (transverse)**: Outflow allows waves to leave domain without reflection

### 5. Time Integration

#### Courant Condition
```
CFL = v_max * Δt / Δx
```

**Turbulence-safe setting:**
```python
<time>
cfl_number = 0.3              # Reduced from 0.4 for safety
nsmoothing = 2                # Time integrator smoothing
</time>
```

#### Integration Scheme
```python
<time>
integrator = vl2
# Or: integrator = rk3 (3rd-order Runge-Kutta, more accurate but slower)
</time>
```

### 6. Output Configuration

#### Checkpoint Strategy
```python
# Full snapshots:
dt_dir_samples = 0.05   # Every 0.05 t_J

# Light-weight outputs for monitoring:
dt_block = 0.01          # Time-averaged data every 0.01 t_J
```

#### Critical Outputs
1. **Density field** (ρ): Track fragmentation
2. **Velocity field** (v): Calculate Mach number
3. **Magnetic field** (B): Monitor ∇·B
4. **Diagnostic variables**: Time-averaged quantities

### 7. Divergence Cleaning

**For maintaining ∇·B = 0:**
```python
<magnetic>
divb_clean = powell
divb_tol = 1e-10
divb_dtol = 1e-10
</magnetic>
```

**Powell's method** is most stable for highly turbulent flows.

### 8. Resolution Requirements

#### Minimum Resolution Criteria
```
1. Resolve Jeans scale: Δx < λ_J / 100
2. Resolve driving scale: Δx < driving_corrlength / 10
3. Resolve sonic scale: Δx < c_s / (M * Ω) where Ω is vorticity
```

**For M = 2 turbulence:**
- Δx < 0.01 λ_J (satisfied by 512³ with Δx = 0.0078 λ_J)
- Driving scale = 2.0 λ_J → Δx < 0.2 λ_J (easily satisfied)

#### Mesh Refinement Study
```python
# Phase 1 tests:
Resolution → Expected M_turb → Justification
256³       → M_turb ≈ 0.3  → Baseline (insufficient)
384³       → M_turb ≈ 0.6  → Intermediate (still insufficient)
512³       → M_turb ≈ 1.0  → Target (transonic achieved)
```

## Full Campaign Parameter Matrix

### Phase 2: 108 Simulations

| Run ID | f   | β  | θ    | M_driver | Seed | Priority | Notes |
|--------|-----|----|------|----------|------|----------|-------|
| 1-18   | 1.2 | 0.5 | 0°   | 1.0      | 0,1  | High     | Near-critical, strong B |
| 19-36  | 1.2 | 0.5 | 0°   | 2.0      | 0,1  | High     | Near-critical, strong B |
| 37-54  | 1.2 | 0.5 | 90°  | 1.0      | 0,1  | Medium  | Perpendicular field |
| 55-72  | 1.2 | 1.0 | 0°   | 1.0      | 0,1  | High     | Near-critical, equipartition |
| 73-90  | 1.2 | 2.0 | 0°   | 1.0      | 0,1  | High     | Near-critical, weak B |
| 91-108 | 1.2 | 2.0 | 90°  | 1.0      | 0,1  | Medium  | Near-critical, weak B, perpendicular |
| ...    | ... | ...| ...  | ...      | ...  | ...     | (similarly for f=1.5, 2.0) |

**Priority system:**
- **High**: Core test cases, directly comparable to HGBS
- **Medium**: Important for physics understanding
- **Low**: Nice-to-have, can be deferred

## Input File Generation

### Automated Parameter File Generator
```python
# generate_inputs.py
import numpy as np

def generate_athena_input(run_id, f, beta, theta, M_drive, seed, resolution):
    """Generate athena.input for given parameters."""
    
    # Convert to Athena++ units
    rho_0 = 1.0  # Normalized density
    cs = 1.0     # Normalized sound speed
    B0 = cs * np.sqrt(2.0 / beta)  # Field strength from plasma beta
    
    # Calculate driving amplitude
    # M_target = M_drive * (1 - exp(-t/tau_d)) ≈ M_drive * damping_factor
    driving_scale = M_drive  # Start with this, adjust if needed
    
    input_template = f"""
<job>
job_id      = {run_id:04d}
problem_id  = 1

<time>
tlim        = 6.0     # Run for 6 t_J (enough for fragmentation)
nlim        = 10000000
dt          = 1e-4    # Initial timestep (will be adaptive)
cfl_number  = 0.3
integrator  = vl2
</time>

<hydro>
iso_sound_speed = {cs}
gamma = 1.0
</hydro>

<magnetic>
# Field strength
B0 = {B0}
beta = {beta}
theta = {theta}

# Divergence cleaning
divb_clean = powell
divb_tol = 1e-10
</magnetic>

<problem>
# Line mass fraction
f = {f}

# Turbulent driving
driving_scale = {driving_scale}
driving_corrlength = 2.0
driving_auto = true
driving_decayscale = 0.1

# Random seed
seed = {seed}
</problem>

<mesh>
nx1 = {resolution[0]}
nx2 = {resolution[1]}
nx3 = {resolution[2]}

# Boundary conditions
ix1_bc = periodic
ix2_bc = outflow
ox1_bc = periodic
ox2_bc = outflow
ix3_bc = outflow
ox3_bc = outflow
</mesh>

<output>
file_type = hdf5
dt_dir_samples = 0.05
variable_dt = true
summation = -1
</output>

<par>
nproc = 220
</par>
"""
    return input_template
```

### Batch Generation Script
```bash
# Generate all 108 input files
python generate_all_inputs.py \
    --resolution 512 \
    --output_dir inputs/turb_full_campaign/
```

## Validation Tests

### Test 1: Turbulence Maintenance
**Goal**: Verify M_turb ≥ 1.0 is sustained

```python
def check_turbulence_maintenance(h5_file):
    """Verify turbulence is maintained throughout simulation."""
    with h5py.File(h5_file, 'r') as f:
        # Calculate Mach number evolution
        for t_idx in range(f['Level0'].shape[0]):
            rho = f['Level0'][t_idx]['prim']['rho'][()]
            vel = f['Level0'][t_idx]['prim']['vel'][()]
            
            # Calculate rms velocity
            v_rms = np.sqrt(np.mean(vel**2))
            M_turb = v_rms / cs
            
            # Check criterion
            if M_turb < 1.0:
                print(f"WARNING: Turbulence decayed at t={t_idx*dt}")
                return False
    
    return True
```

### Test 2: Fragmentation Detection
**Goal**: Detect longitudinal beading or radial collapse

```python
def detect_fragmentation(h5_file):
    """Determine fragmentation outcome."""
    # Check for density peaks along filament axis
    # This is simplified - full version in ANALYSIS.md
    
    with h5py.File(h5_file, 'r') as f:
        rho_midplane = f['Level0'][-1]['prim']['rho'][:, :, nz//2]
        
        # Look for peaks along x-direction
        peaks = find_density_peaks(rho_midplane)
        
        if len(peaks) >= 2:
            return "BEADING"
        else:
            return "RADIAL_COLLAPSE"
```

## Failure Mode Handling

### If Turbulence Cannot Be Sustained
1. **Increase resolution** to 768³ or 1024³
2. **Reduce driving scale** (but this defeats the purpose)
3. **Enable explicit subgrid-scale model** (advanced, requires code modification)

### If Simulations Are Too Slow
1. **Reduce domain size** to 8×2×2 λ_J
2. **Use coarser output** (less frequent checkpoints)
3. **Accept shorter duration** (if fragmentation occurs early)

## Quality Control

### Before Running Campaign
```bash
# Run 5-10 test simulations with varied parameters
# Check:
1. Turbulence is sustained (M_turb ≥ 1.0)
2. No numerical instabilities (|∇·B|/|B| < 10⁻⁸)
3. Reasonable runtime (< 48 hours per simulation)
```

### During Campaign
```bash
# Monitor each simulation after it completes
python quick_check.py results/run_*/
```

## Parameter Dictionary

### Athena++ Input Parameters (alphabetical)

| Parameter | Description | Typical Value | Range |
|-----------|-------------|---------------|-------|
| `cfl_number` | CFL safety factor | 0.3 | 0.2–0.4 |
| `divb_clean` | Divergence cleaning method | powell | powell, linde |
| `divb_tol` | Divergence tolerance | 1e-10 | 1e-12–1e-8 |
| `dt_dir_samples` | Output interval | 0.05 | 0.01–0.1 |
| `f` | Line-mass fraction | 1.2–2.0 | 1.0–3.0 |
| `gamma` | Equation of state index | 1.0 | 1.0 (isothermal) |
| `integrator` | Time integration | vl2 | vl2, rk3 |
| `nlim` | Max timesteps | 10⁷ | 10⁶–10⁸ |
| `tlim` | Simulation duration (t_J) | 6.0 | 4–10 |
| `theta` | Field angle (degrees) | 0, 90 | 0–90 |
| `driving_auto` | Auto-driving | true | true/false |
| `driving_scale` | Driving amplitude | 1.0–3.0 | 0.5–5.0 |
| `driving_corrlength` | Forcing correlation length | 2.0 | 1.0–4.0 |
| `seed` | Random seed | 0–999999 | All integers |

---
**Last updated**: 2026-05-18
**Based on**: Athena++ v21.0, HGBS paper Section 4.7.4
