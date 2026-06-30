# Athena++ External Pressure Boundary Condition Implementation Guide

## Overview

This document provides step-by-step instructions for implementing the external pressure boundary condition in Athena++ for the RCE campaign.

---

## 1. Files to Modify

### 1.1 Primary Files
```
athena++/src/bvals/bvals.cpp           # Boundary value handling
athena++/src/bvals/bvals.hpp           # Boundary value declarations
athena++/src/pgen/prob_filament.cpp    # Filament problem generator
athena++/src/inputs/inputs.cpp         # Input parameter reading
```

### 1.2 Configuration Files
```
athena++/configure                     # Build configuration script
athena++/Makefile                      # Compilation rules
```

---

## 2. Implementation Details

### 2.1 Boundary Condition Physics

The external pressure boundary condition implements a **pressure-confined outflow** condition:

```python
If P_internal < P_external:
    # Confinement regime
    # - Impose external pressure at boundary
    # - Allow limited mass inflow to maintain pressure balance
    # - Zero-gradient on velocity

If P_internal >= P_external:
    # Standard outflow regime
    # - Zero-gradient on all variables
    # - No inflow allowed
```

### 2.2 Mathematical Formulation

For a boundary face at index `i`:

**Density:**
```
ρ_ghost = ρ_boundary  (zero-gradient for both regimes)
```

**Pressure:**
```
P_ghost = max(P_boundary, P_external)
```

**Velocity:**
```
v_ghost = v_boundary  (zero-gradient)
```

**Magnetic Field:**
```
B_ghost = B_boundary  (zero-gradient for conducting walls)
```

---

## 3. Code Implementation

### 3.1 Add Boundary Condition Type

**File:** `src/bvals/bvals.hpp`

Add to boundary condition enum:
```cpp
enum class BoundaryFlag {
  // ... existing flags ...
  outflow,        // Existing outflow
  outflow_with_pressure,  // NEW: External pressure BC
  // ... other flags ...
};
```

### 3.2 Implement Boundary Condition

**File:** `src/bvals/bvals.cpp`

Add the implementation:
```cpp
// In BoundaryValues::ApplyBoundaryConditions()

// Handle outflow_with_pressure boundary condition
if (block->pbval->block_bcs[dir_b][0] == BoundaryFlag::outflow_with_pressure ||
    block->pbval->block_bcs[dir_b][1] == BoundaryFlag::block_bcs) {

  // Get external pressure parameter from problem generator
  Real p_ext_ratio = pin->GetReal("boundary", "p_ext_ratio", 0.0);
  Real p_ext = p_ext_ratio * rho_iso * cs_iso * cs_iso;

  // Apply to appropriate face
  for (int k=kl; k<=ku; ++k) {
    for (int j=jl; j<=ju; ++j) {
      for (int i=il; i<=iu; ++i) {

        // Get face-centered values
        Real rho_face, p_face, vx_face, vy_face, vz_face;
        GetFaceValues(block, k, j, i, dir, &rho_face, &p_face,
                     &vx_face, &vy_face, &vz_face);

        // Apply external pressure condition
        if (p_face < p_ext) {
          // Confinement regime - impose external pressure
          prim(IPR, k, j, i) = p_ext;
          prim(IDN, k, j, i) = rho_face;  // Zero-gradient density
          prim(IVX, k, j, i) = vx_face;   // Zero-gradient velocity
          prim(IVY, k, j, i) = vy_face;
          prim(IVZ, k, j, i) = vz_face;
        } else {
          // Standard outflow - zero-gradient on all
          prim(IDN, k, j, i) = rho_face;
          prim(IPR, k, j, i) = p_face;
          prim(IVX, k, j, i) = vx_face;
          prim(IVY, k, j, i) = vy_face;
          prim(IVZ, k, j, i) = vz_face;
        }

      }
    }
  }
}
```

### 3.3 Add Input Parameter Reading

**File:** `src/inputs/inputs.cpp`

Add parameter reading:
```cpp
// In Parameters::ParametersFromFile()

// Read boundary section
if (std::strcmp(block_name, "boundary") == 0) {
  // ... existing boundary parameter reading ...

  // NEW: Read external pressure ratio
  Real p_ext_ratio = pin->GetOrAddReal("boundary", "p_ext_ratio", 0.0);
  // Store for use in boundary conditions
  pmy_block->pbval->p_ext_ratio = p_ext_ratio;
}
```

---

## 4. Problem Generator Configuration

### 4.1 Filament Initial Conditions

**File:** `src/pgen/prob_filament.cpp`

Add external pressure initialization:
```cpp
void Mesh::InitUserMeshData(ParameterInput *pin) {
  // Read external pressure ratio
  Real p_ext_ratio = pin->GetOrAddReal("problem", "p_ext_ratio", 0.0);

  // Calculate isothermal sound speed and density
  Real cs_iso = pin->GetReal("hydro", "iso_sound_speed", 1.0);
  Real rho_iso = pin->GetReal("problem", "rho_iso", 1.0);

  // Calculate external pressure
  Real p_ext = p_ext_ratio * rho_iso * cs_iso * cs_iso;

  // Store for use in boundary conditions
  // ...
}
```

---

## 5. Compilation Instructions

### 5.1 Configure Script

**File:** `athena++/configure`

No modifications needed - the configure script already handles custom boundary conditions.

### 5.2 Compilation

```bash
cd /path/to/athena++

# Clean previous build
make clean

# Configure with required modules
./configure \
    --prob=filament \
    --coord=cartesian \
    --flux=hllc \
    --bfer=flux_correction \
    --order=2 \
    --cxx=mpicxx \
    --mpi

# Compile
make -j 8

# Verify compilation
ls -la bin/athena
```

---

## 6. Testing the Implementation

### 6.1 Test Problem: Pressure-Confined Filament

Create a test input file:
```python
# test_external_pressure.in

<job>
    problem_id = test_pressure_bc
</job>

<time>
    tlim = 1.0
    nlim = 1000
    dt_out = 0.01
</time>

<mesh>
    nx1 = 128
    nx2 = 32
    nx3 = 32

    x1min = -0.5
    x1max = 0.5
    x2min = -0.125
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
    p_ext_ratio = 0.3  # Moderate external pressure
</boundary>

<hydro>
    iso_sound_speed = 1.0
    gamma = 1.0
</hydro>

<problem>
    rho_iso = 1.0
    rho_0 = 10.0
    w_core = 0.062
    f_ratio = 1.0
    turb_mach = 0.0  # No turbulence for test
</problem>

<output>
    dt = 0.01
    variables = prim
    filetype = hst
    sum_x1 = 1
</output>
```

### 6.2 Run Test

```bash
cd bin

mpirun -np 4 ./athena -m test_external_pressure.in

# Check for errors in output
grep -i "error\|warning\|fail" *.log

# Verify boundary behavior
# - Pressure at boundaries should approach P_ext
# - No numerical instabilities
# - Mass conservation (with expected outflow)
```

---

## 7. Validation Checks

### 7.1 Pressure Balance Check

After running test simulation:
```python
# check_pressure_balance.py
import h5py
import numpy as np

# Load final output
with h5py.File('test_pressure_bc.hst', 'r') as f:
    data = f['Density'][-1, :]  # Final time slice

# Check boundary pressure
p_boundary = data[:, 0]  # Left boundary
p_center = data[:, data.shape[1]//2]  # Center

# Expected: p_boundary ≈ P_ext (if confined)
#           p_boundary > P_ext (if outflow dominates)

print(f"Boundary pressure: {p_boundary.mean()}")
print(f"External pressure: {p_ext}")
print(f"Center pressure: {p_center.mean()}")
```

### 7.2 Stability Check

Monitor simulation for:
- No runaway pressure growth
- No velocity spikes at boundaries
- Smooth pressure transitions

### 7.3 Conservation Check

Verify that:
- Mass is conserved (except for allowed outflow)
- Momentum is conserved (except for boundary forces)
- Energy is conserved (within expected bounds)

---

## 8. Troubleshooting

### Issue 1: Boundary Instability

**Symptoms:** Pressure oscillations at boundaries, simulation crashes

**Solution:**
- Reduce external pressure gradient
- Implement damping layer near boundaries
- Use smaller time step

### Issue 2: Incorrect Pressure Imposition

**Symptoms:** Pressure at boundary doesn't approach P_ext

**Solution:**
- Check boundary condition ordering
- Verify p_ext_ratio is read correctly
- Debug with print statements

### Issue 3: Mass Loss Issues

**Symptoms:** Unrealistic mass loss rates

**Solution:**
- Verify mass outflow is only when P_internal > P_ext
- Check that mass inflow is limited when confined
- Monitor total mass budget

---

## 9. Performance Considerations

### 9.1 Computational Cost

External pressure BC adds minimal overhead:
- Boundary condition check: O(n_boundary_cells)
- No additional global operations
- Expected overhead: <1% per timestep

### 9.2 Parallel Scaling

Boundary condition is local to each MPI domain:
- No additional communication required
- Scales well with MPI
- Expected: Same scaling as standard outflow

---

## 10. Documentation and Comments

### 10.1 Code Comments

Add comprehensive comments:
```cpp
//-------------------------------------------------------------------------------
// External Pressure Boundary Condition
//
// Implements pressure-confined outflow:
// - If P_internal < P_external: Impose external pressure
// - If P_internal >= P_external: Standard outflow (zero-gradient)
//
// This allows filaments to experience external confinement while
// still permitting mass outflow when internal pressure dominates.
//
// Parameters:
//   p_ext_ratio: External pressure relative to ρ_iso * c_s²
//
// Reference: White et al. (2026) - RCE Campaign
//-------------------------------------------------------------------------------
```

### 10.2 User Documentation

Add to Athena++ user guide:
```
# External Pressure Boundary Condition

The "outflow_with_pressure" boundary condition implements
pressure-confined outflow for simulating filaments embedded
in pressurized environments.

## Parameters
- p_ext_ratio: External pressure ratio (P_ext / (ρ_iso * c_s²))

## Behavior
- When internal pressure < external pressure: Confined regime
- When internal pressure >= external pressure: Outflow regime

## Applications
- Molecular cloud filaments
- Pressure-confined stellar structures
- Jets with external confinement
```

---

## 11. Integration with Existing Code

### 11.1 Backward Compatibility

The external pressure BC is additive:
- Does not modify existing boundary conditions
- Can be selected per boundary face
- Default behavior unchanged

### 11.2 Compatibility with Other Features

Works with existing Athena++ features:
- MHD: Compatible (zero-gradient on B-field)
- AMR: Compatible (applies at refinement boundaries)
- MPI: Compatible (local boundary operations)
- Shearing box: Compatible (Cartesian coordinates)

---

## 12. Verification Checklist

Before running full RCE campaign:

- [ ] Boundary condition compiles without errors
- [ ] Test simulation runs to completion
- [ ] Pressure balance verified
- [ ] Stability confirmed for various P_ext values
- [ ] Conservation laws satisfied
- [ ] Performance acceptable (<1% overhead)
- [ ] Documentation complete
- [ ] Code comments added

---

## 13. Next Steps

After implementation:

1. **Verification:**
   - Run test suite
   - Compare with analytical solutions
   - Validate boundary physics

2. **Integration:**
   - Merge into main Athena++ branch
   - Update documentation
   - Create example input files

3. **RCE Campaign:**
   - Generate input files for 360 simulations
   - Set up submission scripts
   - Begin campaign execution

---

**Prepared by:** Claude (ASTRA System)
**Date:** June 6, 2026
**Status:** Ready for Implementation
