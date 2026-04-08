# 3D HYDRODYNAMICAL/MHD SIMULATION PLAN
## For Definitive Validation of Filament Fragmentation Theory

---

## Executive Summary

**Objective**: Perform full 3D hydrodynamical and magnetohydrodynamic (MHD) simulations of filament fragmentation to provide definitive validation of the 2× vs 4× core spacing discrepancy.

**Deliverables**:
1. 3D simulation code with realistic filament physics
2. Parameter study across key filament properties
3. Direct comparison with HGBS observations (all 9 regions)
4. Updated paper with 3D simulation results
5. Publication-ready figures and validation

---

## PHASE 1: Theoretical Foundation

### 1.1 Governing Equations

**3D Isothermal MHD Equations**:

\begin{align}
\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{v}) &= 0 \\
\frac{\partial (\rho \mathbf{v})}{\partial t} + \nabla \cdot (\rho \mathbf{v} \mathbf{v}) &= -\nabla P - \rho \nabla \Phi + \frac{1}{4\pi}(\nabla \times \mathbf{B}) \times \mathbf{B} \\
\frac{\partial \mathbf{B}}{\partial t} &= \nabla \times (\mathbf{v} \times \mathbf{B}) \\
\nabla \cdot \mathbf{B} &= 0 \\
P &= c_s^2 \rho \quad \text{(isothermal)} \\
\nabla^2 \Phi &= 4\pi G \rho
\end{align}

### 1.2 Initial Conditions

**Filament Profile**:
\begin{equation}
\rho(x, y, z, t=0) = \rho_0 \exp\left(-\frac{x^2 + y^2}{2H^2}\right) \times \left[1 + \sum_i A_i \cos\left(\frac{2\pi z}{\lambda_i}\right)\right]
\end{equation}

**Perturbations**: Random density fluctuations with amplitude $\epsilon = 0.01$

### 1.3 Boundary Conditions

- **z-direction**: Periodic (simulates infinite filament)
- **r-direction**: Outflow with fixed external pressure
- **Boundaries**: $P_{\rm out} = P_{\rm ext}$

---

## PHASE 2: Software Selection

### 2.1 Options Evaluated

| Software | Advantages | Disadvantages | Suitability |
|----------|------------|---------------|-------------|
| **Athena++** | AMR, well-tested | Steep learning curve | ⭐⭐⭐⭐⭐ |
| **FLASH** | AMR, MHD | Complex setup | ⭐⭐⭐⭐ |
| **AREPO** | Moving mesh | Complex | ⭐⭐⭐ |
| **GADGET** | SPH, fast | AMR limited | ⭐⭐⭐ |
| **Custom Python** | Flexible, transparent | Slow | ⭐⭐ |

### 2.2 Recommended Approach: Hybrid

**Primary**: Custom Python code with:
- NumPy arrays for grid
- FFT-based Poisson solver
- Operator splitting for time integration
- OpenMP/MPI parallelization

**Why Python?**
- Transparent methodology (can see every step)
- Easy to modify for different physics
- Sufficient for 2D validation
- Can be accelerated with Numba/JAX

**Alternative**: Athena++ for production runs

---

## PHASE 3: Simulation Parameters

### 3.1 Grid Requirements

**Base Resolution**:
- Longitudinal: $N_z = 256$ points
- Cross-section: $N_x = N_y = 64$ points
- Total: $256 \times 64 \times 64 = 1,048,576$ cells

**Adaptive Mesh Refinement (AMR)**:
- Base grid: $128 \times 32 \times 32$
- Refinement criterion: $|\nabla \rho| / \rho > 0.5$
- Max refinement: 2 levels (factor of 4)

### 3.2 Physical Parameters

**Base Values** (from 2D analysis):
- Temperature: $T = 10$ K
- Number density: $n_0 = 10^3$ cm⁻³
- Scale height: $H = 0.043$ pc
- Sound speed: $c_s = 0.19$ km/s

**Filament Properties**:
- Length: $L = 4$ pc (L/H = 93 for "infinite")
- For finite: $L = 0.4$ pc (L/H = 10)
- Radius: $R = 0.3$ pc
- Mass/length: $M_{\rm line} = 20$ M☉/pc

### 3.3 Parameter Study Matrix

| Simulation | L (pc) | L/H | P_ext (10⁵ K/cm³) | B (μG) | Purpose |
|------------|---------|-----|-------------------|---------|---------|
| **Series A: Length Study** |
| A1 | 0.4 | 10 | 0 | 0 | Baseline finite |
| A2 | 0.6 | 15 | 0 | 0 | Longer |
| A3 | 0.8 | 20 | 0 | 0 | Longest |
| **Series B: Pressure Study** |
| B1 | 0.4 | 10 | 0 | 0 | No pressure |
| B2 | 0.4 | 10 | 1 | 0 | Low pressure |
| B3 | 0.4 | 10 | 2 | 0 | Medium pressure |
| B4 | 0.4 | 10 | 5 | 0 | High pressure |
| **Series C: Magnetic Study** |
| C1 | 0.4 | 10 | 2 | 0 | No field |
| C2 | 0.4 | 10 | 2 | 10 | Weak field |
| C3 | 0.4 | 10 | 2 | 20 | Medium field |
| C4 | 0.4 | 10 | 2 | 50 | Strong field |
| **Series D: Full Physics** |
| D1 | 0.4 | 10 | 2 | 20 | Best 2D match |
| D2 | 0.32 | 8 | 5 | 20 | W3-like |
| D3 | 0.48 | 12 | 1 | 10 | CRA-like |

**Total**: 15 core simulations + 5 verification runs = 20 simulations

---

## PHASE 4: Computational Requirements

### 4.1 Hardware

**Minimum**:
- 16 CPU cores
- 64 GB RAM
- 500 GB SSD storage

**Recommended**:
- 32 CPU cores
- 128 GB RAM
- 1 TB NVMe storage
- GPU (for Poisson solver acceleration)

### 4.2 Software Stack

```python
# Core scientific computing
numpy >= 1.21
scipy >= 1.7
h5py >= 3.7  # HDF5 I/O

# Parallelization
numba >= 0.56  # JIT compilation
dask >= 2021.0  # Distributed computing

# Visualization
matplotlib >= 3.5
mayavi >= 4.7  # 3D visualization
yt >= 4.0  # Analysis
```

### 4.3 Runtime Estimates

| Resolution | Cells/Domain | Time/Step | Steps | Wall Time |
|------------|--------------|-----------|-------|-----------|
| 128³ | 2M | 0.01 sec | 10,000 | ~2 min |
| 256³ | 16M | 0.08 sec | 10,000 | ~15 min |
| 512³ | 134M | 0.6 sec | 10,000 | ~2 hr |

**With AMR**: 2-3× faster

**Total estimated time**: 20 simulations × 15 min = 5 hours (on 32 cores)

---

## PHASE 5: Validation Strategy

### 5.1 Code Verification

**Test Problems**:
1. **Isothermal sphere collapse** (known solution)
2. **Infinite cylinder linear stability** (compare with IM92)
3. **Pressure-confined cylinder** (compare with Fischera 2012)

### 5.2 Convergence Testing

**Resolution Study**:
- Run at 64³, 128³, 256³
- Verify convergence of core spacing
- Confirm numerical errors < 5%

**Time Step Study**:
- Test CFL numbers: 0.3, 0.5, 0.7
- Verify energy conservation

### 5.3 Comparison with 2D Results

Before running 3D simulations:
- Validate against 2D linear theory
- Ensure same physics produces similar results
- Document any 3D-specific effects

---

## PHASE 6: Analysis Pipeline

### 6.1 Core Identification

**Algorithm**:
```python
1. Smooth density field with Gaussian kernel (σ = 2 cells)
2. Find local maxima with peak_local_max()
3. Filter peaks above threshold: ρ > 2×ρ_mean
4. Compute separations between all peak pairs
5. Take median as core spacing
```

### 6.2 Diagnostics

**Outputs**:
- Core positions and masses
- Density PDF
- Velocity PDF
- Magnetic field structure
- Spacing histogram
- Time evolution of fragmentation

---

## PHASE 7: Timeline

| Week | Milestone |
|------|------------|
| 1 | Code development and testing |
| 2 | Verification simulations (5 runs) |
| 3 | Production simulations (15 runs) |
| 4 | Analysis and comparison |
| 5 | Paper update and figure generation |
| 6 | Final review and submission |

**Total**: 6 weeks from start to publication-ready results

---

## PHASE 8: Success Criteria

### 8.1 Quantitative

**Required**:
- Match observed spacing (0.213 pc) within ±10%
- Reproduce 2D results to within ±15%
- Convergence verified (resolution study)
- Energy conserved to ±5%

### 8.2 Qualitative

**Required**:
- Clear core formation process visible
- Realistic filament morphology
- Reproduces known instabilities
- Computational results reproducible

---

## Appendix: Code Structure

```
3d_mhd_filaments/
├── solver/
│   ├── __init__.py
│   ├── hydro.py           # Hydro equations
│   ├── mhd.py             # MHD equations
│   ├── poisson.py         # Gravity solver
│   └── boundary.py        # Boundary conditions
├── analysis/
│   ├── core_finder.py     # Core identification
│   ├── diagnostics.py     # Analysis tools
│   └── visualization.py   # 3D plotting
├── simulations/
│   ├── run_simulation.py  # Main driver
│   ├── param_files/       # Simulation parameters
│   └── output/            # Results
└── tests/
    ├── test_collapse.py   # Verification tests
    └── test_convergence.py # Convergence tests
```

---

## Budget Summary

| Item | Time | Cost |
|------|------|------|
| Code development | 1 week | N/A (author time) |
| Verification runs | 0.5 weeks | N/A (institutional HPC) |
| Production runs | 0.5 weeks | N/A (institutional HPC) |
| Analysis | 1 week | N/A (author time) |
| Paper update | 1 week | N/A (author time) |
| **Total** | **4 weeks** | **~5000 CPU-hours** |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Code bugs | Medium | High | Extensive testing, verification |
| Long runtime | Low | Medium | Start with coarse grid, optimize |
| Memory issues | Low | High | AMR, checkpointing |
| Poor convergence | Low | High | Resolution study, diagnostics |
| 3D effects differ | Medium | Medium | Compare with 2D early |

---

**PREPARED BY**: G. J. White  
**DATE**: 8 April 2026  
**VERSION**: 1.0  
**STATUS**: Ready for implementation
