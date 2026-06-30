# RCE Campaign: Radial Confinement Escalation
## Complete Implementation Plan for Definitive Filament Spacing Resolution

**Date**: June 6, 2026
**Campaign Type**: Targeted physics exploration
**Objective**: Resolve RTC vs rigid cylinder contradiction by testing intermediate radial confinement
**Total Simulations**: 360
**Estimated Compute**: ~720 hours at 128³ resolution

---

## 1. Scientific Rationale

### The Central Problem
- **RTC (free boundaries)**: 0/1,200 simulations match HGBS (λ/W ≥ 3.75)
- **Rigid cylinder**: 9/45 simulations match HGBS (λ/W = 2.65 ± 0.57 at f ≥ 2.6)
- **Observations**: λ/W = 2.01 ± 0.16 (NN analysis)
- **Conclusion**: Real filaments likely occupy an intermediate confinement regime

### Physical Hypothesis
HGBS filaments are not free boundaries (they exist in pressurized molecular clouds) but they're also not rigid walls (they can accrete and evolve). They occupy an intermediate regime where external pressure provides partial radial confinement, allowing longitudinal fragmentation to complete before radial collapse dominates.

### Expected Behavior
```
Free boundaries (RTC)          → λ/W ≥ 3.75 (radial collapse dominates)
Weak confinement              → λ/W ≈ 3.0-3.5 (transition regime)
Moderate confinement          → λ/W ≈ 2.5-3.0 (approaching HGBS)
Strong confinement            → λ/W ≈ 2.0-2.5 (HGBS regime)
Rigid walls                   → λ/W ≈ 2.65 (artificial suppression)
```

---

## 2. Parameter Space Design

### 2.1 Core Parameter Grid

```
Line-mass ratio (f):
  Values: [1.2, 1.3, 1.4, 1.5]
  Rationale: Bridges the extrapolation gap where physics transitions
  Notes: f = 1.2 is upper limit of Campaign 7, f = 1.5 is lower limit of rigid cylinder

Plasma beta (β):
  Values: [0.5, 1.0, 2.0]
  Rationale: Covers weak to moderate magnetic fields
  Notes: β = 0.5 = strong field, β = 2.0 = moderate field

Mach number (M):
  Values: [2.0, 3.0]
  Rationale: Physical ISM turbulence range
  Notes: M = 2.0 (moderate turbulence), M = 3.0 (strong turbulence)

External pressure level (P_ext):
  Level 0: P_ext = 0.0 ρc_s²    (Free boundary - RTC baseline)
  Level 1: P_ext = 0.1 ρc_s²    (Weak confinement)
  Level 2: P_ext = 0.3 ρc_s²    (Moderate confinement)
  Level 3: P_ext = 0.5 ρc_s²    (Strong confinement)
  Level 4: Reflecting wall       (Rigid baseline)
  Rationale: Smooth progression from free to rigid

Random seeds:
  Count: 3 per parameter point
  Rationale: Assess statistical robustness
```

### 2.2 Total Simulation Count
```
Total = 4 (f) × 3 (β) × 2 (M) × 5 (P_ext) × 3 (seeds) = 360 simulations
```

### 2.3 Parameter Priority Tiers

**Tier 1 (High Priority - Run First):**
```
f = [1.3, 1.4] × β = [1.0] × M = [2.0] × P_ext = [0.1, 0.3, 0.5] × 3 seeds
= 2 × 1 × 1 × 3 × 3 = 18 simulations
```

**Tier 2 (Medium Priority):**
```
Full β variation at f = 1.4, P_ext = 0.3
= 1 × 3 × 1 × 1 × 3 = 9 simulations
```

**Tier 3 (Complete Grid):**
```
Remaining parameter combinations
= 360 - 18 - 9 = 333 simulations
```

---

## 3. Athena++ Code Modifications

### 3.1 External Pressure Boundary Condition

#### Physics Implementation

The external pressure boundary condition modifies the outflow boundary conditions to impose a specified external pressure while allowing mass outflow when internal pressure exceeds external pressure.

**Modified Boundary Condition:**

```cpp
// In boundary conditions file (e.g., bc.cpp)
// Modified outflow boundary with external pressure

if (boundary_type == "outflow_with_pressure") {
    // Get external pressure from user input
    Real p_ext = p_ext_ratio * rho_iso * cs_iso * cs_iso;

    // Get face-centered primitive variables
    Real rho_face, p_face, vx_face, vy_face, vz_face;
    GetFaceValues(i, j, k, boundary_dir, &rho_face, &p_face,
                 &vx_face, &vy_face, &vz_face);

    // Modified boundary condition:
    // If internal pressure < external pressure:
    //   Impose external pressure, allow inflow to maintain pressure balance
    // If internal pressure > external pressure:
    //   Standard outflow (zero gradient)

    if (p_face < p_ext) {
        // Pressure-confined regime
        // Impose external pressure at boundary
        prim(IDN, k, j, i) = rho_face;  // Zero-gradient density
        prim(IPR, k, j, i) = p_ext;     // Impose external pressure
        prim(IVX, k, j, i) = vx_face;   // Zero-gradient velocity
        prim(IVY, k, j, i) = vy_face;
        prim(IVZ, k, j, i) = vz_face;

        // Allow mass inflow if needed to maintain pressure
        // (this represents external material compressing the filament)
    } else {
        // Standard outflow (internal pressure exceeds external)
        // Zero-gradient on all variables
        prim(IDN, k, j, i) = rho_face;
        prim(IPR, k, j, i) = p_face;
        prim(IVX, k, j, i) = vx_face;
        prim(IVY, k, j, i) = vy_face;
        prim(IVZ, k, j, i) = vz_face;
    }
}
```

#### Configuration Parameters

Add to input file:
```python
# Boundary condition configuration
<boundary>
    # Outer x boundaries
    x1_bc = outflow_with_pressure  # -x boundary
    x2_bc = outflow_with_pressure  # +x boundary (transverse)

    # Outer y boundaries (transverse direction)
    y1_bc = outflow_with_pressure  # -y boundary (transverse)
    y2_bc = outflow_with_pressure  # +y boundary (transverse)

    # z boundaries (periodic for infinite filament)
    z1_bc = periodic
    z2_bc = periodic

    # External pressure ratio (P_ext / (ρ_iso * c_s²))
    p_ext_ratio = 0.1  # For Level 1 confinement
    # Options: 0.0 (free), 0.1 (weak), 0.3 (moderate), 0.5 (strong)
</boundary>
```

### 3.2 Problem Generator Modifications

#### Filament Initial Conditions with External Pressure

```cpp
// In problem generator (e.g., fil_3d.cpp)
void Mesh::InitUserMeshData(ParameterInput *pin) {
    // Read external pressure ratio
    p_ext_ratio = pin->GetOrAddReal("problem", "p_ext_ratio", 0.0);
    rho_iso = pin->GetReal("problem", "rho_iso");
    cs_iso = pin->GetReal("problem", "cs_iso");

    // Calculate external pressure
    p_ext = p_ext_ratio * rho_iso * SQR(cs_iso);

    // Initialize filament with pressure balance at boundaries
    // ...
}
```

### 3.3 Compilation Instructions

```bash
cd /path/to/athena++

# Configure with required modules
./configure \
    --prob=fil_3d \
    --coord=cartesian \
    --flux=hllc \
    --bfer=flux_correction \
    --order=2 \
    --cxx=mpicxx

# Add boundary condition flag to Makefile
# Modify the configure script or add to CXXFLAGS after configuration

make clean
make -j 8
```

---

## 4. Simulation Configuration

### 4.1 Input File Template

```python
# RCE Campaign Configuration File
# Parameter: f=1.4, β=1.0, M=2.0, P_ext=0.3

<job>
    problem_id = RCE_f1.4_b1.0_m2.0_p0.3_s1
    # f = line-mass ratio
    # b = plasma beta
    # m = mach number
    # p = external pressure ratio
    # s = random seed
</job>

<time>
    tlim = 3.0      # Simulation time in code units
    nlim = 10000    # Maximum steps (safety limit)
    dt_out = 0.05   # Output interval
</time>

<mesh>
    nx1 = 256
    nx2 = 64        # Transverse extent (y-direction)
    nx3 = 64        # Longitudinal extent (z-direction)

    x1min = -0.5    # Transverse coordinate (pc units)
    x1max = 0.5
    x2min = -0.125  # Longitudinal coordinate
    x2max = 0.125
    x3min = -0.125
    x3max = 0.125

    ix1_bc = outflow_with_pressure
    ix2_bc = outflow_with_pressure
    iy1_bc = outflow_with_pressure
    iy2_bc = outflow_with_pressure
    iz1_bc = periodic
    iz2_bc = periodic
</mesh>

<boundary>
    p_ext_ratio = 0.3  # External pressure level
</boundary>

<hydro>
    iso_sound_speed = 1.0  # c_s in code units
    gamma = 1.0             # Isothermal
</hydro>

<mhd>
    # Magnetic field configuration
    # For longitudinal fields: B = (0, 0, B0)
    # For perpendicular fields: B = (0, B0, 0)

    # Calculate B0 from plasma beta: β = 8πP/B²
    # For β = 1.0, P = ρc_s² = 1.0, B0 = sqrt(8π*1.0) ≈ 5.01
    b_initial = 5.01  # For β = 1.0
</mhd>

<problem>
    # Filament parameters
    rho_iso = 1.0           # Background density
    rho_0 = 10.0            # Central density enhancement
    w_core = 0.062          # Core width (pc)
    f_ratio = 1.4           # Line-mass ratio M_line/M_crit

    # Turbulence parameters
    turb_mach = 2.0         # Mach number
    turb_seed = 1           # Random seed for turbulence
    turb_cutoff = 2.0       # Driving wavenumber
</problem>

<output>
    dt = 0.05               # Output frequency
    variables = prim        # Output primitive variables
    filetype = hst          # History file type
    sum_x1 = 1             # Sum over x1 for history files
</output>
```

### 4.2 Parameter Mapping Table

| f (line-mass) | β (plasma) | M (Mach) | P_ext (pressure) | Seed | Problem ID |
|--------------|------------|-----------|------------------|------|------------|
| 1.2 | 0.5 | 2.0 | 0.1 | 1 | RCE_f1.2_b0.5_m2.0_p0.1_s1 |
| 1.2 | 0.5 | 2.0 | 0.1 | 2 | RCE_f1.2_b0.5_m2.0_p0.1_s2 |
| 1.2 | 0.5 | 2.0 | 0.1 | 3 | RCE_f1.2_b0.5_m2.0_p0.1_s3 |
| ... | ... | ... | ... | ... | ... |

---

## 5. Analysis Pipeline

### 5.1 Fragmentation Detection

```python
# detect_fragmentation.py
import numpy as np
import h5py
from scipy import signal

def detect_fragmentation_spatial(data, threshold=0.5):
    """
    Detect core locations from column density map.

    Parameters:
    - data: 2D column density array
    - threshold: Detection threshold (relative to peak)

    Returns:
    - core_positions: List of (y, z) coordinates
    - n_cores: Number of cores
    """
    # Smooth data
    from scipy.ndimage import gaussian_filter
    smoothed = gaussian_filter(data, sigma=2.0)

    # Find peaks
    peaks, properties = signal.find_peaks(smoothed.flatten(),
                                          height=threshold*smoothed.max())

    # Convert to 2D coordinates
    core_positions = np.unravel_index(peaks, smoothed.shape)

    return core_positions, len(peaks)

def compute_spacing(core_positions, box_size):
    """
    Compute nearest-neighbor spacings.

    Parameters:
    - core_positions: Array of (y, z) coordinates
    - box_size: Physical size of domain

    Returns:
    - spacings: Array of NN distances
    - lambda_mean: Mean spacing
    - lambda_std: Std of spacing
    """
    # Sort cores by position along filament (z-direction)
    sorted_cores = core_positions[np.argsort(core_positions[:, 1])]

    # Compute NN spacings
    spacings = np.diff(sorted_cores[:, 0])

    # Convert to physical units
    spacings_phys = spacings * box_size / len(spacings)

    return spacings_phys, np.mean(spacings_phys), np.std(spacings_phys)
```

### 5.2 Width Measurement

```python
# measure_width.py
def fit_gaussian_profile(column_density, center):
    """
    Fit Gaussian profile to filament cross-section.

    Returns:
    - width: Fitted Gaussian width (W)
    - width_err: Fitting uncertainty
    """
    from scipy.optimize import curve_fit

    # Extract profile across filament
    profile = column_density[:, center]

    # Gaussian model
    def gaussian(x, amp, center, width, offset):
        return amp * np.exp(-(x-center)**2 / (2*width**2)) + offset

    # Fit
    popt, pcov = curve_fit(gaussian, np.arange(len(profile)), profile,
                          p0=[profile.max(), len(profile)/2, 5.0, profile.min()])

    width = popt[2]
    width_err = np.sqrt(pcov[2, 2])

    return width, width_err
```

### 5.3 Automated Analysis Script

```python
# analyze_rce_campaign.py
#!/usr/bin/env python3

import os
import json
import numpy as np
from pathlib import Path

class RCEAnalyzer:
    """Analyze RCE campaign results."""

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.results = []

    def parse_problem_id(self, problem_id):
        """Extract parameters from problem ID."""
        # Format: RCE_f1.4_b1.0_m2.0_p0.3_s1
        parts = problem_id.split('_')
        params = {}

        for part in parts[1:]:  # Skip 'RCE' prefix
            key = part[0]
            value = float(part[2:])

            if key == 'f':
                params['line_mass'] = value
            elif key == 'b':
                params['beta'] = value
            elif key == 'm':
                params['mach'] = value
            elif key == 'p':
                params['p_ext'] = value
            elif key == 's':
                params['seed'] = int(value)

        return params

    def analyze_simulation(self, sim_dir):
        """Analyze a single simulation."""
        problem_id = sim_dir.name

        # Extract parameters
        params = self.parse_problem_id(problem_id)

        # Load final output
        final_file = sim_dir / "final_output.hst"
        if not final_file.exists():
            return None

        # Compute λ/W measurement
        lambda_W, status = self.compute_lambda_over_W(sim_dir)

        result = {
            'problem_id': problem_id,
            'params': params,
            'lambda_W': lambda_W,
            'status': status,
            't_frag': self.get_fragmentation_time(sim_dir)
        }

        return result

    def compute_lambda_over_W(self, sim_dir):
        """Compute λ/W ratio."""
        # Implementation loads data, applies detection algorithms
        # Returns (lambda_W, status) tuple

        # Placeholder - actual implementation loads HDF5 data
        return 2.5, 'FRAG'

    def get_fragmentation_time(self, sim_dir):
        """Extract fragmentation time."""
        # Load from history file
        return 1.25

    def analyze_all(self):
        """Analyze all simulations in campaign."""
        sim_dirs = sorted(self.base_dir.glob('RCE_*'))

        for sim_dir in sim_dirs:
            result = self.analyze_simulation(sim_dir)
            if result:
                self.results.append(result)

        return self.results

    def save_results(self, output_file):
        """Save analysis results."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

    def generate_summary_report(self):
        """Generate summary statistics."""
        df = pd.DataFrame(self.results)

        summary = {
            'total_simulations': len(self.results),
            'fragmented': len(df[df['status'] == 'FRAG']),
            'radial_collapse': len(df[df['status'] == 'RADIAL']),
            'by_p_ext': {
                p_ext: {
                    'mean_lambda_W': df[df['params::p_ext'] == p_ext]['lambda_W'].mean(),
                    'std_lambda_W': df[df['params::p_ext'] == p_ext]['lambda_W'].std(),
                    'fragmented': len(df[(df['params::p_ext'] == p_ext) & (df['status'] == 'FRAG')])
                }
                for p_ext in [0.0, 0.1, 0.3, 0.5]
            }
        }

        return summary

# Usage
if __name__ == '__main__':
    analyzer = RCEAnalyzer('/path/to/RCE_campaign')
    results = analyzer.analyze_all()
    analyzer.save_results('rce_results.json')
    summary = analyzer.generate_summary_report()

    print(f"Analyzed {summary['total_simulations']} simulations")
    print(f"Fragmented: {summary['fragmented']}")
    print(f"Radial collapse: {summary['radial_collapse']}")
```

---

## 6. Expected Outcomes and Interpretation

### 6.1 Outcome 1: Smooth Transition with Confinement

**Result:** λ/W decreases smoothly with increasing P_ext
```
P_ext = 0.0 → λ/W = 4.5 ± 1.2 (RTC baseline)
P_ext = 0.1 → λ/W = 3.8 ± 0.9
P_ext = 0.3 → λ/W = 2.9 ± 0.6
P_ext = 0.5 → λ/W = 2.3 ± 0.4
P_ext = rigid → λ/W = 2.65 ± 0.57 (rigid baseline)
```

**Interpretation:**
- Radial confinement is the PRIMARY parameter controlling λ/W
- Real filaments with P_ext ≈ 0.3-0.5 ρc_s² would match HGBS
- **Discriminating:** Predicts specific column density profile shapes
- **Observational test:** HGBS filaments should show evidence of external pressure

### 6.2 Outcome 2: Threshold Behavior

**Result:** Sharp transition at specific confinement level
```
P_ext ≤ 0.1 → λ/W ≥ 4.0 (radial collapse dominates)
P_ext ≥ 0.3 → λ/W ≤ 2.5 (longitudinal fragmentation)
```

**Interpretation:**
- Critical confinement threshold exists
- Filaments are either confined or not, no middle ground
- **Discriminating:** Suggests bistable filament states
- **Observational test:** Bimodal distribution of filament properties

### 6.3 Outcome 3: No Confinement Effect

**Result:** λ/W remains high even at P_ext = 0.5
```
All P_ext levels → λ/W ≥ 3.5
```

**Interpretation:**
- Radial confinement alone cannot explain discrepancy
- Missing physics is required (non-ideal MHD, thermodynamics)
- **Discriminating:** Rules out confinement as primary explanation
- **Next step:** Implement ambipolar diffusion or time-dependent EOS

### 6.4 Outcome 4: Unexpected Regime

**Result:** New physical behavior emerges
```
Intermediate P_ext → Different fragmentation pattern
(e.g., multiple wavelengths, asymmetric fragmentation)
```

**Interpretation:**
- Physical transition not captured by current framework
- May indicate competition between longitudinal and radial modes
- **Discriminating:** Reveals new physics
- **Next step:** Detailed analysis of mode competition

---

## 7. Timeline and Milestones

### Phase 1: Code Development (Week 1-2)
- [ ] Implement external pressure BC in Athena++
- [ ] Test boundary condition with simple problems
- [ ] Create input file templates
- [ ] Develop analysis pipeline

**Milestone:** Working code with validated boundary conditions

### Phase 2: Tier 1 Simulations (Week 3-4)
- [ ] Run 18 high-priority simulations
- [ ] Preliminary analysis
- [ ] Determine if continuation is warranted

**Milestone:** Preliminary results indicating whether path is promising

### Phase 3: Full Campaign (Week 5-8)
- [ ] Run remaining 342 simulations
- [ ] Complete analysis
- [ ] Generate figures and statistics

**Milestone:** Complete dataset with conclusions

### Phase 4: Paper Preparation (Week 9-10)
- [ ] Integrate results into paper
- [ ] Draft referee response
- [ ] Prepare supplementary material

**Milestone:** Submission-ready manuscript

---

## 8. Risk Assessment and Mitigation

### Risk 1: Boundary Condition Instability
**Description:** External pressure BC may cause numerical instability

**Mitigation:**
- Start with low P_ext values and test thoroughly
- Implement damping near boundaries
- Use Riemann solver with pressure correction

### Risk 2: Unexpected Physical Behavior
**Description:** Intermediate confinement may produce unexpected dynamics

**Mitigation:**
- Monitor simulations for pathologies
- Adjust parameter ranges if needed
- Document unexpected behavior for future investigation

### Risk 3: Inconclusive Results
**Description:** Results may not clearly discriminate between mechanisms

**Mitigation:**
- Design Tier 1 to provide early indication
- Have backup plan (non-ideal MHD campaign)
- Ensure results are publishable even if inconclusive

---

## 9. Success Criteria

The RCE campaign will be considered successful if it:

1. **Bridges the extrapolation gap** by sampling f = 1.2-1.5 with realistic BC
2. **Provides clear discrimination** between confinement and other mechanisms
3. **Makes testable predictions** about filament properties
4. **Resolves or clarifies** the RTC vs rigid cylinder contradiction

Even if the campaign shows that radial confinement cannot explain the discrepancy, it definitively rules out this mechanism and points to missing physics.

---

## 10. Next Steps

1. **Immediate (this week):**
   - Review and validate implementation plan
   - Set up development environment
   - Begin Athena++ modifications

2. **Short-term (next 2 weeks):**
   - Implement and test external pressure BC
   - Run test simulations
   - Validate analysis pipeline

3. **Medium-term (next 4-6 weeks):**
   - Execute Tier 1 simulations
   - Analyze preliminary results
   - Decide on full campaign execution

4. **Long-term (2-3 months):**
   - Complete full campaign
   - Integrate results into paper
   - Prepare for submission

---

**Prepared by:** Claude (ASTRA System)
**Date:** June 6, 2026
**Status:** Ready for Implementation
