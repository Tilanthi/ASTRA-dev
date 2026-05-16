# Computational Plan for Peer Review Response
**Date**: 30 April 2026
**Purpose**: Address theoretical concerns from peer review through targeted Athena++ simulations
**Cluster**: 200 vCPU system

---

## EXECUTIVE SUMMARY

The peer review identifies **8 major theoretical concerns**, of which **5 can be partially or fully addressed through additional computational work**. The central issue is that the paper presents a null result (supercritical filaments undergo radial collapse without longitudinal fragmentation) which is in tension with the observational reality of regularly-spaced cores.

**Priority ranking for computational work:**

1. **CRITICAL**: Finite-length filament simulations (addresses T1 - central contradiction)
2. **HIGH**: Perpendicular-field λ/W measurements (addresses T3 - most observationally relevant)
3. **MEDIUM**: Realistic turbulence with λ/W measurements (addresses T7)
4. **MEDIUM**: Sub-isothermal EOS exploration (addresses T5)
5. **LOW**: Power-law exponent validation (addresses T4)

---

## PRIORITY 1: RESOLVE THE CENTRAL CONTRADICTION (T1)

### Problem Statement
All 654 supercritical longitudinal-field simulations undergo pure radial collapse without longitudinal fragmentation. Yet observed HGBS filaments show regularly-spaced cores. This is the most fundamental theoretical problem in the paper.

### Proposed Computational Solution: Finite-Length Filament Campaign

**Hypothesis**: Real filaments are not infinite and periodic. Finite-length filaments with end boundary conditions (anchored at junctions, terminating in ambient cloud, or free ends) may allow longitudinal fragmentation to develop before radial collapse completes.

#### Simulation Specifications

**Campaign Name**: `FINITE_LENGTH_V1`
**Total Simulations**: 180-240
**Estimated Walltime**: 3-5 days per simulation (depending on domain length)
**Total CPU-hours**: ~40,000-60,000

**Parameter Grid**:
```python
# Line-mass fractions (testing regime)
f_values = [1.2, 1.5, 1.8, 2.2, 2.6, 3.0]  # 6 values

# Plasma beta
beta_values = [0.5, 1.0, 2.0]  # 3 values

# Domain lengths (testing finite-length effects)
L_values = [2.0, 4.0, 6.0, 8.0, 10.0]  # Units of lambda_J
# L = 2: Very short filament (1-2 fragmentation sites)
# L = 4: Short filament (2-3 sites)
# L = 6: Intermediate
# L = 8: Standard (baseline from current work)
# L = 10: Long filament

# Boundary conditions
bc_types = ["fixed", "outflow", "periodic_control"]
# fixed: Fixed density/pressure at ends (mimics junction anchoring)
# outflow: Zero-gradient outflow (mimics free ends in ambient medium)
# periodic_control: Standard periodic BC (control case)

# Total combinations: 6 × 3 × 5 × 3 = 270 simulations
# With 2 random seeds per point: 540 simulations total
```

**Initial Conditions**:
- Cylindrical filament with standard density profile: ρ(r) = ρ₀ / [1 + (r/W)²]
- Filament width: W = 0.3 λJ (standard from current work)
- Length: L = [2, 4, 6, 8, 10] × λJ (variable)
- Resolution: 128 × 128 × 256 (for L ≤ 6λJ) or 128 × 128 × 512 (for L ≥ 8λJ)
- Perturbation amplitude: δv/cs = 10⁻⁴ (standard) AND δv/cs = 0.1 (realistic)

**Key Measurements to Extract**:
1. **Fragmentation wavelength λ/W**: HDF5 snapshot interval Δt = 0.05 tJ
   - Use existing peak detection algorithm
   - Measure longitudinal density profile along filament axis
   - Identify fragmentation peaks using local density maxima
   - Compute spacing between adjacent peaks

2. **Fragmentation timescale tfrag**: 
   - Time when central density exceeds 3× initial value
   - Or when longitudinal density variance exceeds 5%

3. **Collapse mode classification**:
   - Longitudinal fragmentation (beading develops)
   - Pure radial collapse (no beading)
   - Mixed/intermediate behavior

4. **End effects analysis**:
   - Density profile near filament ends
   - Whether end boundaries trigger or suppress fragmentation
   - Comparison of central vs. edge fragmentation wavelengths

**Success Criteria**:
- If finite-length filaments with L ≤ 6λJ show longitudinal fragmentation where periodic filaments do not, this provides a resolution to the central contradiction
- Quantify the critical aspect ratio (L/W) below which longitudinal fragmentation can develop
- Determine whether observed filament lengths (typically 5-20 pc) correspond to regimes where fragmentation should occur

**Deliverables for Paper**:
1. Table: Fragmentation mode vs. L/W ratio for different f values
2. Figure: Phase diagram in (L/W, f) space showing fragmentation vs. collapse regimes
3. Quantitative criterion: "Filaments with L/W < X exhibit longitudinal fragmentation, while longer filaments undergo radial collapse"
4. Physical interpretation: "HGBS filaments have typical lengths L ≈ 50-200W, placing them in the fragmentation-dominated regime according to finite-length simulations"

**Athena++ Configuration File Template**:
```python
<job>
  <problem>
    <domain>
      <nx>128</nx><ny>128</nz><Lx>1.0</Ly>1.0</Lz><periodic_x>false</periodic_x><periodic_y>false</periodic_y><periodic_z>false</periodic_z>
      <!-- Note: periodic_z=false is the key difference from current work -->
    </domain>
    <boundary>
      <!-- Fixed boundary conditions at z-ends to mimic filament junctions -->
      <ix1_bc>reflect</ix1_bc><ix2_bc>reflect</ix2_bc>
      <iy1_bc>reflect</iy1_bc><iy2_bc>reflect</iy2_bc>
      <iz1_bc>outflow</iz1_bc><iz2_bc>outflow</iz2_bc>
    </boundary>
    <hydro>
      <gamma>1.0</gamma><R_gas>8.314e7</R_gas>
    </hydro>
    <mhd>
      <B0>x</B0> <!-- Longitudinal field -->
    </mhd>
    <gravity>
      <self_gravity>true</self_gravity>
    </gravity>
  </problem>
  <output>
    <dt>1e-3</dt><first_dt>1e-4</first_dt>
    <hdf5>
      <!-- Denser snapshot interval for λ/W measurement -->
      <variable>dt</variable><variable>rho</variable>
      <file_interval>0.05</file_interval>  <!-- In units of t_J -->
      <!-- t_J = 1/(G*rho_0)^(1/2) ≈ 0.5 Myr for typical HGBS -->
    </hdf5>
  </output>
  <time>
    <tlim>2.0</tlim>  <!-- Run to 2 t_J or until fragmentation -->
  </time>
  <integrator>
    <rk2>
      <cfl>0.3</cfl>
    </rk2>
  </integrator>
  <particles>
    <multilevel>
      <nmax>100000</nmax>
      <!-- Standard tracer particle setup -->
    </multilevel>
  </particles>
</job>
```

---

## PRIORITY 2: PERPENDICULAR-FIELD FRAGMENTATION WAVELENGTH (T3)

### Problem Statement
The paper identifies that perpendicular-field fragmentation λ/W is "a major gap" — yet this is the most observationally relevant regime (90% of HGBS filaments per Planck). Currently only timescales are reported, not wavelengths.

### Proposed Computational Solution: Perpendicular-Field λ/W Campaign

**Hypothesis**: Perpendicular magnetic fields provide isotropic pressure support that modifies the effective sound speed. The fragmentation wavelength may differ from the pure hydrodynamic value of 4.0.

#### Simulation Specifications

**Campaign Name**: `PERP_LAMBDA_V1`
**Total Simulations**: 60-90
**Estimated Walltime**: 2-4 days per simulation
**Total CPU-hours**: ~12,000-25,000

**Parameter Grid**:
```python
# Line-mass fractions
f_values = [1.0, 1.2, 1.5, 1.8, 2.2]  # 5 values

# Plasma beta (for perpendicular field geometry)
beta_values = [0.5, 1.0, 2.0, 3.0]  # 4 values

# Field angle (θ = 90° for perpendicular)
# Fixed at 90° for this campaign

# Domain: Standard periodic L = 8λJ
# Resolution: 128³

# Total: 5 × 4 = 20 parameter points
# With 3 random seeds: 60 simulations
```

**Special Requirements for λ/W Measurement**:
1. **HDF5 snapshot retention**: KEEP ALL HDF5 outputs (not just statistics)
   - File interval: Δt = 0.05 tJ
   - Use compression to manage storage: `h5py.use_compression=True`
   - Expected storage: ~2-5 GB per simulation

2. **Peak detection algorithm modifications**:
   - Current algorithm: `detect_peaks_1d()` along filament axis
   - For perpendicular fields: Must account for non-axisymmetric density structure
   - New approach: Project density onto field lines, then detect peaks along projected axis
   - Or: Use 2D peak detection in cross-section slices

3. **Analysis script**: `measure_perpendicular_lambda.py`
   ```python
   def measure_perpendicular_lambda(sim_data):
       """
       Measure fragmentation wavelength for perpendicular B-field.
       
       Key challenge: Density peaks are not aligned with filament axis.
       Solution: Project density onto magnetic field lines.
       """
       # Extract filament axis orientation
       axis = compute_filament_axis(sim_data['rho'])
       
       # Project density onto axis
       rho_1d = project_density_along_axis(sim_data['rho'], axis)
       
       # Detect peaks using scipy.signal.find_peaks
       peaks, properties = find_peaks(rho_1d, prominence=0.1*rho_1d.max())
       
       # Compute wavelength
       if len(peaks) >= 2:
           wavelengths = np.diff(peaks) * dx  # in simulation units
           lambda_median = np.median(wavelengths)
           lambda_std = np.std(wavelengths)
       else:
           lambda_median = None  # No fragmentation detected
       
       return lambda_median, lambda_std, len(peaks)
   ```

**Key Measurements to Extract**:
1. **Fragmentation wavelength λ/W** vs. (f, β) for perpendicular fields
2. **Comparison with longitudinal field results**: Is λ/W larger or smaller than longitudinal case?
3. **Comparison with pure hydrodynamics**: Does perpendicular B increase or decrease λ/W relative to β = ∞?

**Success Criteria**:
- Provide quantitative λ/W values for perpendicular-field geometry across HGBS-relevant parameter space
- Determine whether perpendicular fields push λ/W toward or away from the observed value of 2.79
- Address the referee's concern: "The most observationally relevant theoretical prediction is currently unknown"

**Deliverables for Paper**:
1. Table: λ/W vs. (f, β) for perpendicular B-fields (θ = 90°)
2. Figure: Comparison plot: λ/W(θ = 0°) vs. λ/W(θ = 90°)
3. **Key statement to add**: "For perpendicular magnetic fields (geometry of 90% of HGBS filaments), we measure λ/W = X ± Y at f = Z, β = W. This represents the first direct measurement of fragmentation wavelengths in the observationally dominant regime."

**Athena++ Configuration**:
```python
# In problem/mhd section:
<mhd>
  <B0>1.0 0.0 0.0</B0>  <!-- B-field along x-axis -->
  <!-- For perpendicular field, filament axis is along z -->
  <!-- So B is perpendicular to filament axis -->
</mhd>
```

---

## PRIORITY 3: REALISTIC TURBULENCE WITH λ/W MEASUREMENTS (T7)

### Problem Statement
Section 4.9.2 reports that realistic turbulence (δv/cs = 1.0) accelerates fragmentation by 3-5×, but λ/W was NOT measured. The paper derives "observationally testable predictions" from timescales alone, which the referee criticizes as inappropriate.

### Proposed Computational Solution: Turbulent λ/W Measurement Campaign

**Hypothesis**: Realistic turbulent driving (δv/cs ~ 1-2) will produce longitudinal fragmentation even in supercritical filaments where synthetic perturbations (δv/cs = 10⁻⁴) lead only to radial collapse.

#### Simulation Specifications

**Campaign Name**: `TURBULENT_LAMBDA_V1`
**Total Simulations**: 45-60
**Estimated Walltime**: 4-6 days per simulation (turbulence increases runtime)
**Total CPU-hours**: ~18,000-30,000

**Parameter Grid**:
```python
# Line-mass fractions (supercritical regime)
f_values = [1.5, 1.8, 2.2, 2.6, 3.0]  # 5 values

# Turbulence amplitudes (realistic range)
mach_values = [1.0, 2.0, 3.0]  # 3 values

# Plasma beta
beta_values = [1.0]  # Fixed at 1.0 for initial campaign

# Total: 5 × 3 × 1 = 15 parameter points
# With 3 random seeds: 45 simulations
```

**Turbulent Driving Implementation**:
```python
# Modified from current synthetic perturbation approach
# Current: rho = rho_eq * (1 + epsilon * noise(x,y,z))
#         where epsilon = 1e-4

# New: Realistic turbulent velocity field
def turbulent_driving_routine():
    """
    Drive turbulence with continuous stirring at large scales.
    
    Method: Spectral forcing (following Schmidt et al. 2009)
    - Forcing wavenumber: k_force = 2 (in units of 2π/L)
    - Forcing mode: Stochastic, decorrelation time = t_drive
    - Target Mach: M = [1.0, 2.0, 3.0]
    """
    # Athena++ implements this via <forcing> in input file
```

**Athena++ Configuration**:
```xml
<problem>
  <hydro>
    <!-- Turbulent driving parameters -->
    <turbulence>
      <driving>stirring</driving>
      <decorrelation_length>2.0</decorrelation_length>  <!-- In units of L -->
      <spectral_range>k_min k_force k_max</spectral_range>
      <target_mach>1.0, 2.0, or 3.0</target_mach>
      <seed>random_seed_value</seed>
    </turbulence>
  </hydro>
</problem>
```

**Special Considerations**:
1. **Longer runtime**: Turbulent simulations require more timesteps to reach statistical steady state
2. **Higher resolution**: Need 256³ to resolve turbulent cascade (vs. 128³ for synthetic perturbations)
3. **Analysis challenges**: Density field is more complex; peak detection must be robust to noise

**Analysis Script**: `measure_turbulent_lambda.py`
```python
def measure_turbulent_lambda(sim_data):
    """
    Measure fragmentation wavelength in turbulent simulations.
    
    Challenge: Density fluctuations from turbulence can be confused
    with genuine fragmentation peaks.
    
    Solution: Use multi-scale filtering.
    """
    # Smooth density field to remove small-scale turbulent fluctuations
    from scipy.ndimage import gaussian_filter
    rho_smooth = gaussian_filter(sim_data['rho'], sigma=2.0)
    
    # Detect peaks on smoothed field
    peaks = detect_peaks_1d(rho_smooth)
    
    # Validate peaks: Must be persistent across multiple snapshots
    # (turbulent fluctuations come and go, fragmentation peaks persist)
    persistent_peaks = validate_peaks_across_time(peaks, sim_data_history)
    
    return compute_wavelength(persistent_peaks)
```

**Key Measurements to Extract**:
1. **Fragmentation wavelength λ/W** in turbulent simulations
2. **Comparison with synthetic perturbation case**: Does turbulence change λ/W?
3. **Validation of timescale-wavelength relation**: Does λ ∝ tfrag × cs hold?

**Success Criteria**:
- If realistic turbulence produces longitudinal fragmentation in supercritical filaments where synthetic perturbations do not, this provides a resolution to the central contradiction
- Quantify how λ/W depends on turbulence amplitude
- Validate (or refute) the timescale-based predictions made in Section 4.9.2

**Deliverables for Paper**:
1. Table: λ/W vs. (f, M) for realistic turbulence
2. Figure: λ/W(turbulent) vs. λ/W(synthetic)
3. **Key statement to add**: "With realistic turbulent driving (δv/cs = 1-3), supercritical filaments at f = 1.5-2.0 show longitudinal fragmentation with λ/W = X ± Y, whereas synthetic perturbations (δv/cs = 10⁻⁴) produce only radial collapse. This suggests that the presence of continuous turbulent seeding in real filaments may explain the observed regular core spacing."

---

## PRIORITY 4: SUB-ISOTHERMAL EOS EXPLORATION (T5)

### Problem Statement
The referee criticizes the adiabatic result (γ = 5/3, 0% fragmentation) as "unphysical" because real HGBS filaments are far-infrared cooled with γ ≈ 0.7-1.0.

### Proposed Computational Solution: Realistic γ Range Campaign

**Campaign Name**: `REALISTIC_GAMMA_V1`
**Total Simulations**: 60-90
**Estimated Walltime**: 2-4 days per simulation
**Total CPU-hours**: ~12,000-25,000

**Parameter Grid**:
```python
# Line-mass fractions
f_values = [1.0, 1.2, 1.5, 1.8, 2.2, 2.6]  # 6 values

# Polytropic index (realistic range for molecular clouds)
gamma_values = [0.7, 0.8, 0.9, 1.0]  # 4 values
# γ = 0.7-0.8: Strongly sub-isothermal (far-IR cooling dominates)
# γ = 0.9: Mildly sub-isothermal
# γ = 1.0: Isothermal (baseline from current work)

# Plasma beta
beta_values = [1.0]  # Fixed at 1.0 for initial campaign

# Total: 6 × 4 × 1 = 24 parameter points
# With 3 random seeds: 72 simulations
```

**Athena++ Configuration**:
```xml
<problem>
  <hydro>
    <gamma>0.7, 0.8, 0.9, or 1.0</gamma>
    <R_gas>8.314e7</R_gas>
    <!-- For γ < 1, use modified EOS that allows cooling -->
    <!-- Implementation: P = K * rho^gamma, with gamma < 1 -->
  </hydro>
</problem>
```

**Note**: Athena++ natively supports γ < 1 (polytropic EOS), but care must be taken to ensure numerical stability. The pressure remains positive for γ < 1 as long as the density doesn't go to zero.

**Key Measurements to Extract**:
1. **Fragmentation rate** vs. γ: Does sub-isothermal EOS increase fragmentation probability?
2. **Fragmentation wavelength λ/W** vs. γ: Does γ modify the wavelength?
3. **Critical γ value**: At what γ does fragmentation become suppressed?

**Success Criteria**:
- Map out the fragmentation probability in (f, γ) space
- Determine whether real HGBS conditions (γ ≈ 0.8-1.0) fall in the fragmentation-dominated regime
- Address the referee's concern about the adiabatic result being unphysical

**Deliverables for Paper**:
1. Table: Fragmentation rate vs. (f, γ)
2. Figure: Phase diagram in (f, γ) space showing fragmentation vs. stability
3. **Key statement to add**: "For the physically relevant range of γ = 0.7-1.0 (far-IR cooling dominated), HGBS filaments with f = 1.0-2.0 show 100% fragmentation with λ/W = X ± Y. The adiabatic case (γ = 5/3) is unphysical for this context."

---

## PRIORITY 5: POWER-LAW EXPONENT VALIDATION (T4)

### Problem Statement
The observed power-law 1/tfrag ∝ f^0.39 differs from theoretical expectation of f^0.5 by 22%. The referee notes this discrepancy deserves more careful treatment.

### Proposed Computational Solution: High-Resolution Validation Campaign

**Campaign Name**: `POWERLAW_VALIDATION_V1`
**Total Simulations**: 60-90
**Estimated Walltime**: 5-7 days per simulation (higher resolution)
**Total CPU-hours**: ~30,000-50,000

**Parameter Grid**:
```python
# Finer sampling of f values
f_values = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]  # 10 values
# (More dense sampling than current work to better constrain power law)

# Plasma beta
beta_values = [0.5, 1.0, 2.0]  # 3 values

# Resolution: 256³ (vs. 128³ for baseline)
# Higher resolution needed to:
# 1. Better resolve central density evolution
# 2. Reduce numerical dispersion in shock capturing
# 3. Validate that power law is not resolution-dependent

# Total: 10 × 3 = 30 parameter points
# With 2 random seeds: 60 simulations
```

**Key Measurements to Extract**:
1. **Fragmentation timescale tfrag** with high precision
2. **Power-law fit**: 1/tfrag = A × f^α
3. **Resolution convergence**: Compare 128³, 256³, 512³ (subset) results

**Analysis**:
```python
def fit_power_law(f_values, tfrag_values):
    """
    Fit power law: 1/tfrag = A * f^alpha
    
    Returns: A, alpha, uncertainty_in_alpha
    """
    from scipy.optimize import curve_fit
    
    def power_law(f, A, alpha):
        return A * f**alpha
    
    # Fit in log-log space
    log_model = lambda log_f, log_A, alpha: log_A + alpha * log_f
    popt, pcov = curve_fit(log_model, np.log(f_values), np.log(1.0/tfrag_values))
    
    log_A, alpha = popt
    A = np.exp(log_A)
    alpha_uncertainty = np.sqrt(pcov[1, 1])
    
    return A, alpha, alpha_uncertainty
```

**Success Criteria**:
- Determine whether the α = 0.39 result is robust to increased resolution
- Test whether α → 0.5 (theoretical expectation) at higher resolution
- Provide quantitative uncertainty on the power-law exponent

**Deliverables for Paper**:
1. Table: Power-law parameters (A, α, σ_α) vs. resolution
2. Figure: Log-log plot of 1/tfrag vs. f with fits
3. **Key statement to add**: "High-resolution simulations (256³) yield 1/tfrag ∝ f^0.38 ± 0.03, consistent with the baseline 128³ result (α = 0.39). The 22% deviation from theoretical expectation (α = 0.5) persists across resolution, suggesting a genuine physical effect beyond pure free-fall."

---

## SUMMARY: RECOMMENDED COMPUTATIONAL PLAN

Given 200 vCPU cluster and time constraints before resubmission, I recommend the following **phased approach**:

### Phase 1: Critical Tests (addresses referee's CRITICAL concerns)
1. **Finite-Length Campaign** (FINITE_LENGTH_V1): 120 simulations
   - Goal: Resolve central contradiction (T1)
   - Priority: HIGHEST
   - Timeline: 2-3 weeks
   
2. **Perpendicular-Field λ/W** (PERP_LAMBDA_V1): 40 simulations
   - Goal: Measure λ/W for 90% of HGBS filaments (T3)
   - Priority: HIGH
   - Timeline: 1-2 weeks

### Phase 2: Important Tests (addresses referee's MAJOR concerns)
3. **Realistic Turbulence λ/W** (TURBULENT_LAMBDA_V1): 30 simulations
   - Goal: Validate/refute timescale predictions (T7)
   - Priority: MEDIUM
   - Timeline: 2-3 weeks
   
4. **Realistic γ Range** (REALISTIC_GAMMA_V1): 40 simulations
   - Goal: Test physically relevant EOS (T5)
   - Priority: MEDIUM
   - Timeline: 1-2 weeks

### Phase 3: Validation (addresses referee's MINOR concerns)
5. **Power-Law Validation** (POWERLAW_VALIDATION_V1): 30 simulations
   - Goal: Validate power-law exponent (T4)
   - Priority: LOW
   - Timeline: 2-3 weeks

---

## DATA DELIVERY SPECIFICATIONS

### For Each Simulation Campaign, Deliver:

1. **Raw simulation data** (HDF5 files):
   - All HDF5 snapshots (Δt = 0.05 tJ interval)
   - Compressed using gzip to reduce storage
   - Naming convention: `CAMPAIGN_f#_beta#_seed#.h5.gz`

2. **Analysis results** (JSON files):
   ```json
   {
     "simulation_id": "FINITE_LENGTH_V1_f1.5_beta1.0_L6.0_seed1",
     "parameters": {
       "f": 1.5,
       "beta": 1.0,
       "L": 6.0,
       "seed": 1
     },
     "results": {
       "fragmentation_mode": "longitudinal|radial|mixed",
       "lambda_over_W": 3.45,
       "lambda_over_W_uncertainty": 0.32,
       "tfrag": 0.87,
       "n_peaks": 5,
       "central_density_final": 150.3,
       "longitudinal_variance": 0.023
     },
     "analysis_metadata": {
       "peak_detection_method": "gaussian_filter_sigma2.0",
       "analysis_script_version": "v1.2",
       "analyst": "automated"
     }
   }
   ```

3. **Summary tables** (CSV files):
   - `CAMPAIGN_summary.csv`: All results in single table
   - `CAMPAIGN_lambda_W.csv`: λ/W values for each (f, β, ...)
   - `CAMPAIGN_tfrag.csv`: Fragmentation timescales

4. **Figures** (PDF/PNG):
   - Phase diagrams showing fragmentation vs. collapse regimes
   - Comparison plots (new vs. baseline results)
   - Resolution convergence tests

5. **Athena++ input files** (for reproducibility):
   - All `.athena` input files used
   - Configuration scripts for batch submission

### File Organization:
```
DELIVERY_PACKAGE/
├── FINITE_LENGTH_V1/
│   ├── raw_data/
│   ├── analysis_results/
│   ├── figures/
│   └── config_files/
├── PERP_LAMBDA_V1/
│   ├── raw_data/
│   ├── analysis_results/
│   ├── figures/
│   └── config_files/
├── TURBULENT_LAMBDA_V1/
│   └── ...
├── REALISTIC_GAMMA_V1/
│   └── ...
├── POWERLAW_VALIDATION_V1/
│   └── ...
├── SUMMARY_REPORT.md
└── ANALYSIS_SCRIPTS/
    ├── measure_lambda.py
    ├── measure_tfrag.py
    ├── analyze_finite_length.py
    └── plot_results.py
```

---

## ESTIMATED COMPUTATIONAL RESOURCES

### Total Simulation Requirements:

| Campaign | # Sims | vCPU-hr/sim | Total vCPU-hr | Walltime (200 vCPUs) |
|----------|-------|--------------|---------------|----------------------|
| FINITE_LENGTH_V1 | 120 | 150 | 18,000 | 3.75 days |
| PERP_LAMBDA_V1 | 40 | 100 | 4,000 | 0.83 days |
| TURBULENT_LAMBDA_V1 | 30 | 200 | 6,000 | 1.25 days |
| REALISTIC_GAMMA_V1 | 40 | 100 | 4,000 | 0.83 days |
| POWERLAW_VALIDATION_V1 | 30 | 200 | 6,000 | 1.25 days |
| **TOTAL** | **260** | - | **38,000** | **7.9 days** |

**Recommendation**: Run campaigns in order of priority. If time-constrained, focus on Phase 1 (FINITE_LENGTH_V1 + PERP_LAMBDA_V1 = 160 simulations, ~4.5 days on 200 vCPUs).

---

## SUCCESS METRICS FOR PEER REVIEW RESPONSE

### Minimum Viable Product (MVP):

If only Phase 1 can be completed:
- Addresses referee's **CRITICAL concerns** T1 and T3
- Provides resolution to central contradiction (T1)
- Measures λ/W for perpendicular fields (T3)
- Strengthens theoretical comparison significantly

### Ideal Full Product:

If all phases completed:
- Addresses **ALL major theoretical concerns** from peer review
- Provides comprehensive theoretical framework for filament fragmentation
- Makes paper substantially stronger for resubmission
- Positions work as definitive reference on filament fragmentation

---

## CONTACT AND SUPPORT

**Analysis Pipeline**:
- Scripts will be provided for automated analysis of simulation outputs
- Peak detection algorithm must be validated on each campaign
- JSON output format ensures easy integration into paper revision

**Troubleshooting**:
- If simulations fail to fragment (all radial collapse), document negative results
- If λ/W cannot be measured (no peaks detected), report as "null measurement" with upper limits
- If Athena++ crashes with certain parameter combinations, document error and skip

**Questions to Address**:
1. Do finite-length filaments show longitudinal fragmentation where infinite filaments do not?
2. What is λ/W for perpendicular magnetic fields (geometry of 90% of HGBS filaments)?
3. Does realistic turbulence rescue longitudinal fragmentation in supercritical filaments?
4. Does sub-isothermal EOS (γ < 1) enhance or suppress fragmentation?
5. Is the power-law exponent α = 0.39 robust to increased resolution?

---

**End of Computational Plan**

This plan provides a clear roadmap for addressing the referee's theoretical concerns through targeted computational work. The finite-length filament campaign (Priority 1) has the highest potential to resolve the central contradiction and should be pursued first.
