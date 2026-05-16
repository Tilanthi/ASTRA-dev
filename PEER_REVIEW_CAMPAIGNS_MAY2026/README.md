# Peer Review Response Campaign Specification (May 2026)

**Date**: 2026-05-04
**Authors**: G. J. White (Open University) & R. Dey (VBRL Holdings Inc)
**Target System**: astra-climate (GCE, 224 vCPU)
**Purpose**: Address peer review concerns about domain-length effects, field geometry physics, and turbulence amplitude

---

## Campaign Overview

This specification addresses three critical concerns raised by peer reviewers:

1. **Domain-Length Independence Test (DLIT)**: Demonstrate that Campaign 8's λ/W = 3.333 measurement at f=1.5 is a physical result, not a domain-mode artifact
2. **Perpendicular-Field Physics Investigation (PFPI)**: Resolve the β-dependence inconsistency between perpendicular and longitudinal field geometries
3. **Realistic Turbulence Validation (RTV)**: Validate that linear perturbation results extend to realistic ISM turbulence levels

---

## Campaign 1: Domain-Length Independence Test (DLIT)

### Scientific Rationale

**Concern from Reviewer B**: "The near-zero seed variance in Campaign 8 (σ = 0.000) is physically suspicious: it suggests the result is domain-length-constrained (the system selects modes that fit the domain) rather than reflecting a physical fragmentation scale. If 24 cores form in a 24λJ domain at λ/W = 3.333, that is exactly 24/(3.333) = 7.2 ≈ 7 wavelengths — meaning the domain accommodates almost exactly an integer number of wavelengths. This may indicate mode-locking to the domain rather than a physical fragmentation scale."

**Test**: Demonstrate that λ/W is independent of domain length across a range of domain sizes (16, 20, 24, 28, 32 λJ) at f=1.5. If λ/W varies systematically with domain length, it indicates domain-mode selection. If λ/W is constant, it confirms a physical fragmentation scale.

### Configuration

```python
Domain_Length_Test_Parameters = {
    # Fixed parameter point (same as Campaign 8)
    'f': 1.5,                    # Line-mass ratio
    'beta': 1.0,                 # Plasma β
    'theta': 0.0,               # Longitudinal B field
    'mach': 1.0,                 # Turbulent Mach number
    
    # Domain length variations (test domain-length independence)
    'Lx_lambdaJ': [16, 20, 24, 28, 32],  # 5 different domain lengths
    
    # Resolution (scale proportionally)
    'Nx_per_lambdaJ': 64,         # Cells per λJ
    'Ny': 64,                    # Transverse cells
    'Nz': 64,                    # Transverse cells
    
    # Seeds for statistical assessment
    'seeds': [42, 137, 251],       # 3 seeds per domain length
    
    # Runtime
    't_max': 1.5,                 # Maximum simulation time (tJ)
    'output_interval': 0.1,        # HDF5 output interval
    'walltime_hours': 4           # Per simulation
}

# Derived parameters for each domain length
for Lx_lambdaJ in Domain_Length_Test_Parameters['Lx_lambdaJ']:
    Nx = Lx_lambdaJ * Domain_Length_Test_Parameters['Nx_per_lambdaJ']
    Ny = Domain_Length_Test_Parameters['Ny']
    Nz = Domain_Length_Parameters['Nz']
    
    # Expected wavelengths that fit in domain
    # If λ/W = 3.333 and W = 0.3 λJ, then λ = 1.0 λJ
    # Domain accommodates Lx_lambdaJ / 1.0 wavelengths
    n_wavelengths = Lx_lambdaJ / 1.0
    
    print(f"Lx = {Lx_lambdaJ} λJ: Nx = {Nx}, n_λ ≈ {n_wavelengths:.1f}")
```

### Expected Outcomes

**If λ/W is constant** (≈3.33) across all domain lengths:
- Confirms physical fragmentation scale
- Campaign 8 result is robust
- Mode-locking concern is resolved

**If λ/W varies systematically** with domain length:
- Indicates domain-mode selection effect
- Campaign 8 result may be biased
- Need to identify preferred wavelength from alternative method

### Analysis Protocol

```python
# DLIT analysis script
def analyze_dlit_results():
    """
    For each domain length (16, 20, 24, 28, 32 λJ):
    
    1. Load HDF5 snapshots at t = 0.60 tJ
    2. Extract longitudinal density profile (y-z averaged)
    3. Detect peaks using scipy.signal.find_peaks
    4. Measure λ/W from peak spacing
    5. Count number of peaks N_peaks
    6. Compute λ/W_mean ± σ across seeds
    
    Output format:
    - Table: Lx, Nx, N_peaks (mean±σ), λ/W (mean±σ)
    - Figure: λ/W vs Lx (with error bars)
    - Figure: N_peaks vs Lx (check for mode-locking)
    """
```

### Success Criteria

1. **Primary**: λ/W independent of Lx (variation < 5% across 16-32 λJ)
2. **Secondary**: N_peaks scales proportionally to Lx (confirms wavelength constant)
3. **Statistical**: Seed variance ≤ 5% for each domain length

### Resource Requirements

- **Total simulations**: 5 domain lengths × 3 seeds = 15 simulations
- **Resolution**: 1024×64×64 (16λJ), 2048×64×64 (32λJ)
- **Cores per sim**: 16 MPI ranks (32 for 32λJ domain)
- **Wall time**: 2-4 hours per simulation
- **Total CPU-hours**: ~60 hours
- **Disk**: ~15 GB (HDF5 outputs)

---

## Campaign 2: Perpendicular-Field Physics Investigation (PFPI)

### Scientific Rationale

**Concern from Reviewer B**: "Campaign 6 reports that for perpendicular fields with β ≤ 0.5, there is 'no axial fragmentation — pure radial collapse,' while for β ≥ 1.0, λ/W = 1.25 ± 0.09. The physical explanation given is that perpendicular fields provide radial support but no axial tension. However, if perpendicular fields provide radial support against collapse for β ≤ 0.5, why does the longitudinal field geometry show the opposite trend — weaker fields (higher β) giving smaller λ/W (shorter spacings)? This apparent inconsistency is not discussed."

**Investigation**: Systematically map the transition from "no axial fragmentation" to "axial fragmentation with λ/W ≈ 1.25" for perpendicular fields. Identify the critical β threshold and physical mechanism.

### Configuration

```python
Perpendicular_Field_Physics_Parameters = {
    # Fixed parameters
    'f': 1.2,                    # Near-critical (where Campaign 6 found transition)
    'theta': 90.0,              # Perpendicular B field
    'mach': 1.0,
    
    # Dense β sampling across transition region
    'beta_values': [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5],
    
    # Domain (longitudinal to capture axial structure)
    'Lx_lambdaJ': 16,
    'Ly_lambdaJ': 1,
    'Lz_lambdaJ': 1,
    
    # Resolution
    'Nx': 1024,
    'Ny': 64,
    'Nz': 64,
    
    # Seeds
    'seeds': [42, 137, 251, 367, 499],  # 5 seeds per β point
    
    # Runtime
    't_max': 2.0,
    'output_interval': 0.1,
    'walltime_hours': 3
}
```

### Physics Investigation

**Key questions to answer**:

1. **Critical β threshold**: At what β does axial fragmentation first appear?
   - Is there a sharp transition or gradual onset?
   - Does the threshold depend on f or M?

2. **Physical mechanism**: Why do perpendicular fields show the OPPOSITE β-trend to longitudinal fields?
   - Longitudinal: weaker field (higher β) → smaller λ/W
   - Perpendicular: weaker field (higher β) → λ/W appears (from 1.25)
   - Is this related to magnetic pressure vs tension balance?

3. **Regime classification**:
   - β ≤ 0.5: FLAT_PROFILE (pure radial collapse)
   - 0.5 < β < 1.0: TRANSITIONAL (weak beading?)
   - β ≥ 1.0: AXIAL_BEADING (λ/W ≈ 1.25)

### Analysis Protocol

```python
# PFPI analysis script
def analyze_pfp_results():
    """
    For each β value (12 points) with 5 seeds:
    
    1. Load HDF5 snapshots at multiple times (t = 0.5, 1.0, 1.5 tJ)
    2. Extract longitudinal density profile
    3. Compute longitudinal variance σ²(ρ)/⟨ρ⟩²
    4. Classify: FLAT if σ²/⟨ρ⟩² < 2×10⁻⁴
             TRANSITIONAL if 2×10⁻⁴ < σ²/⟨⟩² < 0.02
             AXIAL_BEADING if σ²/⟨⟩² ≥ 0.02
    5. For AXIAL_BEADING: detect peaks, measure λ/W
    6. Plot classification phase diagram: β vs t (beading onset)
    7. Compare with longitudinal field results at same β
    
    Output format:
    - Table: β, Classification, t_beading, λ/W, N_peaks
    - Figure: Classification phase diagram in (β, t) space
    - Figure: λ/W vs β comparison (perpendicular vs longitudinal)
    - Figure: Longitudinal variance evolution vs β
    """
```

### Success Criteria

1. **Primary**: Identify critical β threshold with ±0.1 precision
2. **Secondary**: Physical explanation for opposite β-trends vs longitudinal
3. **Tertiary**: Quantitative beading onset time vs β relationship

### Resource Requirements

- **Total simulations**: 12 β values × 5 seeds = 60 simulations
- **Resolution**: 1024×64×64
- **Cores per sim**: 16 MPI ranks
- **Wall time**: 2-3 hours per simulation
- **Total CPU-hours**: ~120 hours
- **Disk**: ~30 GB (HDF5 outputs)

---

## Campaign 3: Realistic Turbulence Validation (RTV)

### Scientific Rationale

**Concern from Reviewer B**: "The turbulence amplitude δv = M × cs × 10⁻⁴ is far below ISM levels. Campaign 5 addresses this by testing physical turbulence (δv/cs = 1.0) and finding that λ/W is unchanged while t_frag decreases by 3.2×. However, the base grid (208 simulations) and DTC (540 simulations) all use δv/cs = 10⁻⁴, which represents purely linear perturbations. These results cannot be straightforwardly extrapolated to the ISM without acknowledging that real filaments with δv/cs ~ 1–3 will behave differently in detail."

**Validation**: Extend Campaign 5 to a broader parameter space, testing realistic turbulence levels across multiple (f, β) combinations to confirm that:
1. λ/W is robust to turbulence amplitude (Campaign 5 result is general)
2. t_frag acceleration factor (≈3.2×) is consistent across parameter space
3. Linear perturbation results can be qualitatively applied to real ISM conditions

### Configuration

```python
Realistic_Turbulence_Parameters = {
    # Representative sample of parameter space
    'f_values': [1.2, 1.5, 2.0, 2.5],     # Near-critical to supercritical
    'beta_values': [0.5, 1.0, 2.0],            # Weak to intermediate field
    'theta': 0.0,                               # Longitudinal B
    
    # Turbulence amplitudes to test
    'turbulence_amplitudes': [
        1e-4,     # Linear (baseline from base grid)
        0.01,     # Low (δv/cs = 0.01)
        0.1,      # Moderate (δv/cs = 0.1)
        0.5,      # High (δv/cs = 0.5, subsonic)
        1.0,      # Physical ISM (δv/cs = 1.0, transonic)
    ],
    
    # Domain and resolution
    'Lx_lambdaJ': 8,
    'Ly_lambdaJ': 1,
    'Lz_lambdaJ': 1,
    'Nx': 256,
    'Ny': 64,
    'Nz': 64,
    
    # Seeds (2 per parameter point to reduce cost)
    'seeds': [42, 137],
    
    # Runtime
    't_max': 2.0,
    'output_interval': 0.1,
    'walltime_hours': 2
}
```

### Analysis Protocol

```python
# RTV analysis script
def analyze_rtv_results():
    """
    For each (f, β, turbulence_amplitude) combination with 2 seeds:
    
    1. Measure t_frag (collapse time)
    2. Extract λ/W (if axial beading present)
    3. Compute acceleration factor: t_frag(δv) / t_frag(linear)
    4. Compute λ/W ratio: λ/W(δv) / λ/W(linear)
    
    Output format:
    - Table: f, β, δv/cs, t_frag, λ/W, acceleration_factor
    - Figure: Acceleration factor vs turbulence amplitude (color by f, β)
    - Figure: λ/W ratio vs turbulence amplitude
    - Figure: t_frag vs turbulence amplitude (log-log plot to test power law)
    
    Key questions:
    - Does acceleration factor (≈3.2× at δv/cs=1) vary with f or β?
    - Is λ/W independent of turbulence amplitude across parameter space?
    - Can linear perturbation results be qualitatively applied to δv/cs ~ 1?
    """
```

### Success Criteria

1. **Primary**: λ/W independent of turbulence amplitude (variation < 5%) for δv/cs ≤ 1
2. **Secondary**: t_frag acceleration factor consistent (±20%) across f=1.2-2.5, β=0.5-2.0
3. **Tertiary**: Validate that Campaign 5 single-point result generalizes

### Resource Requirements

- **Total simulations**: 4 f × 3 β × 5 amplitudes × 2 seeds = 120 simulations
- **Resolution**: 256×64×64
- **Cores per sim**: 8 MPI ranks (reduced due to turbulence computational cost)
- **Wall time**: 1-3 hours per simulation (turbulent cases are more expensive)
- **Total CPU-hours**: ~200 hours
- **Disk**: ~25 GB (HDF5 outputs)

---

## Combined Campaign Execution

### Total Resource Requirements

- **Total simulations**: DLIT (15) + PFPI (60) + RTV (120) = 195 simulations
- **CPU-hours**: ~385 hours
- **Disk**: ~70 GB (HDF5 outputs)
- **Estimated wall time**: ~40-50 hours on 220-vCPU cluster (with 12-20 concurrent jobs)

### Ray Configuration

```python
import ray

# Initialize Ray
ray.init(num_cpus=220, dashboard_port=8265)

# Campaign configurations
campaigns = {
    'DLIT': {
        'sims_per_batch': 3,  # Low memory, can run more concurrent
        'cores_per_sim': 16,
        'max_concurrent': 12,
        'timeout': 14400,  # 4 hours
    },
    'PFPI': {
        'sims_per_batch': 3,
        'cores_per_sim': 16,
        'max_concurrent': 12,
        'timeout': 10800,  # 3 hours
    },
    'RTV': {
        'sims_per_batch': 2,  # Turbulent cases are expensive
        'cores_per_sim': 8,   # Reduced for turbulent cases
        'max_concurrent': 10,
        'timeout': 10800,  # 3 hours
    }
}

# Execution priority: DLIT → PFPI → RTV
# (DLIT has highest scientific priority per reviewer request)
```

### File Structure

```
peer_review_campaigns_may2026/
├── README.md                           # This file
├── run_campaigns.py                    # Main Ray execution script
├── generate_configs.py                  # Config file generator
├── monitor_progress.py                   # Progress monitoring
├── analyze_dlit.py                      # DLIT analysis
├── analyze_pfp.py                       # PFPI analysis
├── analyze_rtv.py                       # RTV analysis
├── analyze_integrated.py                # Cross-campaign synthesis
├── configs/                             # Generated config files
│   ├── dlit/
│   ├── pfp/
│   └── rtv/
├── results/                             # Campaign outputs (created during run)
└── reports/                             # Analysis reports
    ├── DLIT_REPORT.md
    ├── PFPI_REPORT.md
    ├── RTV_REPORT.md
    └── INTEGRATED_ANALYSIS.md
```

---

## Deliverables

### Simulation Outputs
1. All HDF5 snapshots with density, velocity, magnetic field
2. Checkpoint files for restart capability
3. Status JSON files for each simulation

### Analysis Products
1. **DLIT_REPORT.md**:
   - Table: λ/W vs domain length with uncertainties
   - Figure: λ/W vs Lx (with error bars)
   - Figure: N_peaks vs Lx (mode-locking test)
   - Conclusion: Domain-length independence confirmed or rejected

2. **PFPI_REPORT.md**:
   - Table: Classification vs β for all seeds
   - Figure: Phase diagram in (β, t) space
   - Figure: λ/W vs β (perpendicular vs longitudinal comparison)
   - Physical explanation for opposite β-trends

3. **RTV_REPORT.md**:
   - Table: Acceleration factor vs (f, β, δv/cs)
   - Figure: λ/W ratio vs turbulence amplitude
   - Figure: t_frag vs turbulence amplitude (log-log)
   - Validation: Linear perturbation results applicable to ISM?

4. **INTEGRATED_ANALYSIS.md**:
   - Cross-campaign synthesis
   - Revised recommendations for Campaign 8 interpretation
   - Updated paper integration recommendations

### Paper Integration

**If DLIT confirms domain-length independence**:
- Strengthen confidence in Campaign 8 λ/W = 3.333 measurement
- Add to paper: "Domain-length independence test confirms λ/W = 3.33 reflects physical fragmentation scale"

**If PFPI resolves β-dependence inconsistency**:
- Add physical explanation to paper
- Clarify why perpendicular and longitudinal fields show opposite trends

**If RTV validates linear perturbation extrapolation**:
- Add qualification: "Linear perturbation results apply qualitatively to realistic ISM turbulence"
- Note: t_frag 3× faster for δv/cs = 1, but λ/W unchanged

---

## Timeline

1. **Config generation**: 2 hours
2. **Campaign execution**: 40-50 hours wall time
3. **Analysis**: 8 hours
4. **Paper integration**: 4 hours

**Total**: 3-4 days from start to paper-ready results

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| DLIT shows domain-mode selection | Campaign 8 result may be domain-biased; paper needs revision |
| PFPI reveals complex physics | May require additional simulations to resolve |
| RTV shows strong λ/W dependence | Linear perturbation extrapolation invalid; major paper revision |
| Insufficient disk space | Archive completed simulations to compressed storage |
| Cluster instability | Checkpointing enables resume after restart |

---

## Success Metrics

The campaign will be considered successful if it addresses all three reviewer concerns:

1. **DLIT**: Domain-length independence demonstrated with <5% variation in λ/W
2. **PFPI**: Critical β threshold identified to ±0.1, physical explanation provided
3. **RTV**: λ/W independence from turbulence confirmed (<5% variation) for δv/cs ≤ 1

All three campaigns must succeed for the paper to be ready for resubmission.

---

**Contact**: Glenn J. White (g.j.white@open.ac.uk)
**Date**: 2026-05-04
**Version**: 1.0
