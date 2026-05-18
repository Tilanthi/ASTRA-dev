# Transonic/Supersonic Turbulence Campaign for HGBS Filaments

## Overview

This campaign addresses a critical limitation identified by the referee: our previous turbulence simulations achieved only **M_turb ≈ 0.15–0.35** (deeply subsonic) due to numerical dissipation at 256³ resolution, while real HGBS filaments exhibit **M ~ 1–4** (transonic to supersonic).

**Goal**: Achieve and sustain transonic/supersonic turbulence (M ≥ 1) in filament fragmentation simulations to determine whether turbulence-independence of λ/W extends to physically realistic regimes.

## Key References

- Athena++ User Guide: https://princetonuniversity.github.io/Athena++/
- Stone et al. (2008): Athena++ Advection-MHD Code
- Paper Section 4.7.4: Current turbulence limitations
- Paper Section 5.3: Turbulent pressure support (Heitsch 2009 formalism)

## Campaign Strategy

### Phase 1: Resolution Test (Target: 512³)
- **Purpose**: Determine resolution required to sustain M ≥ 1 turbulence
- **Parameter space**: Single fiducial point (f = 1.5, β = 1.0, θ = 0°)
- **Resolutions**: 256³ (baseline), 384³, 512³
- **Driving**: Ornstein-Uhlenbeck forcing at M = 2.0
- **Expected outcome**: 512³ should achieve M_turb ≈ 0.8-1.2

### Phase 2: Full Parameter Space (at optimal resolution)
- **Line-mass**: f = 1.2, 1.5, 2.0 (3 values)
- **Plasma β**: 0.5, 1.0, 2.0 (3 values)
- **Field geometry**: θ = 0° (longitudinal), 90° (perpendicular) (2 values)
- **Turbulence**: M_driven = 1.0, 2.0, 3.0 (3 values)
- **Random seeds**: 2 per parameter point
- **Total**: 3 × 3 × 2 × 3 × 2 = **108 simulations**

### Success Criteria
1. Achieve sustained M_turb ≥ 1.0 for ≥ 1 t_J
2. Maintain stable numerics (|∇·B|/|B| < 10⁻¹²)
3. Converged fragmentation measurement (clear beading or radial collapse)

## Quick Start

```bash
# 1. Set up environment
cd /path/to/transonic_turbulence_campaign
source setup_environment.sh

# 2. Build Athena++
cd athena++
./configure --prob=file_list --hdf5=yes
make

# 3. Run resolution test
./run_resolution_test.sh

# 4. Run full campaign (if resolution test successful)
./run_full_campaign.sh
```

## File Structure

```
transonic_turbulence_campaign/
├── README.md                    # This file
├── SETUP.md                     # Athena++ installation
├── RAY_CLUSTER.md               # Ray cluster setup
├── PARAMETERS.md                 # Simulation parameters
├── ANALYSIS.md                  # Analysis procedures
├── setup_environment.sh          # Environment setup script
├── build_athena.sh              # Athena++ build script
├── run_resolution_test.sh       # Phase 1 execution
├── run_full_campaign.sh         # Phase 2 execution
├── config/
│   ├── athena++.512.res        # 512³ configuration
│   └── athena++.384.res        # 384³ configuration
├── inputs/
│   ├── turb_512.fiducial        # Fiducial input files
│   └── turb_full_campaign/      # Full campaign input files
├── scripts/
│   ├── monitor_turbulence.py    # Real-time turbulence monitoring
│   ├── extract_lambda_W.py      # Fragmentation spacing analysis
│   └── analyze_results.py       # Campaign analysis
└── results/
    ├── resolution_test/         # Phase 1 outputs
    └── full_campaign/           # Phase 2 outputs
```

## Critical Technical Considerations

### 1. Numerical Dissipation
- **Problem**: Low-order spatial reconstruction causes numerical dissipation that damps turbulence
- **Solution**: Higher resolution + higher-order reconstruction (PLMC or PPM)
- **Configuration**: Use `--recon=PLMC` or `--recon=PPM` in configure

### 2. Driving Scheme
- **Problem**: Forcing injects energy at specific scales
- **Solution**: Ornstein-Uhlenbeck (OU) driving with broad spectrum
- **Key parameter**: `driving_auto = true` in athena.input

### 3. CFL Condition
- **Problem**: Turbulent flows require small timesteps
- **Solution**: CFL ≤ 0.3 (vs 0.4 for laminar flows)
- **Configuration**: `cour_no = 0.3` in athena.input

### 4. Domain Size
- **Problem**: Small domains introduce artificial periodicity
- **Solution**: Larger domain (16λ_J × 4λ_J × 4λ_J vs 8λ_J × 2λ_J × 2λ_J)
- **Trade-off**: Larger domains require more CPUs

## Expected Compute Requirements

| Resolution | Domain Size | Cells | CPUs | Runtime (hrs) |
|------------|-------------|-------|------|---------------|
| 384³       | 8×2×2       | 589M  | 64   | ~24          |
| 512³       | 8×2×2       | 1.4B  | 220  | ~48          |
| 512³       | 16×4×4      | 4.2B  | 512  | ~120         |

## Monitoring Progress

During simulation runs, monitor:
1. **Turbulent Mach number**: Should remain ≥ 1.0
2. **Divergence error**: |∇·B|/|B| should stay < 10⁻¹²
3. **Fragmentation status**: Beading vs radial collapse
4. **Memory usage**: Should not exceed node RAM

Use the monitoring script:
```bash
python scripts/monitor_turbulence.py <simulation_id>
```

## Timeline Estimate

- **Week 1**: Athena++ setup, resolution test initialization
- **Week 2**: Resolution test execution, analysis
- **Week 3**: Full campaign preparation (parameter files, job scripts)
- **Weeks 4-8**: Full campaign execution (108 simulations)
- **Week 9**: Analysis and paper integration

## Contact

For issues or questions, contact:
- Principal Investigator: G. J. White
- Athena++ support: https://athena.readthedocs.io/
- Ray cluster documentation: https://docs.ray.io/

## References for This Campaign

1. Heitsch (2009): Turbulent pressure support formalism
2. Kritsuk et al. (2018): Supersonic turbulence in molecular clouds
3. Mocz et al. (2017): High-order reconstruction schemes for turbulence
4. Gong et al. (2023): Recent advances in turbulence modeling with Athena++

---
**Last updated**: 2026-05-18
**Campaign version**: 1.0
**Status**: Ready for execution
