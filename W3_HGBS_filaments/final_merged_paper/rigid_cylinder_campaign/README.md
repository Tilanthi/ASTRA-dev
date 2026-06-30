# Rigid Cylinder Campaign: Supercritical Filament Fragmentation

## Purpose

To address the referee's concern about extrapolation from near-critical (f ≈ 1.0–1.2) to supercritical (f ≥ 1.5) regime by using rigid cylindrical boundary conditions to suppress radial collapse, allowing longitudinal fragmentation modes to develop.

## Campaign Design

**Key Innovation**: Use rigid cylindrical wall boundary condition at r = R_filament to suppress radial collapse while allowing longitudinal fragmentation modes to develop.

### Parameter Space

- **Line-mass fraction (f)**: 1.5, 1.8, 2.2, 2.6, 3.0 (5 values)
- **Plasma β**: 0.5, 1.0, 2.0 (3 values)
- **Mach M**: 1.0 (fixed)
- **Field geometry**: θ = 0° (longitudinal B only)
- **Seeds**: 3 per parameter point
- **Total simulations**: 5 × 3 × 3 = 45 simulations

### Boundary Conditions

- **Rigid cylindrical wall**: r = R_cylinder (reflective)
- **Outflow**: x boundaries (axial)
- **Periodic**: y, z boundaries (if not using cylinder)

### Domain & Resolution

- **Axial length**: L_x = 16 λ_J (to accommodate multiple wavelengths)
- **Cylinder radius**: R_cyl = 1.0 λ_J
- **Resolution**: 256 × 64 × 64 (high axial resolution)
- **Aspect ratio**: 16:1 (enough for ~4 wavelengths)

## Running the Campaign

```bash
# Activate conda environment
conda activate athena

# Initialize Ray cluster (220 CPUs)
ray start --head --num-cpus=220 --port=6379

# In another terminal, launch campaign
cd rigid_cylinder_campaign
python launch_rigid_cylinder_campaign.py
```

## Analysis Instructions

### 1. Extract λ/W Measurements

```python
# analyze_rigid_cylinder_results.py
import h5py
import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

def extract_lambda_W(hdf5_file):
    """Extract fragmentation wavelength from HDF5 snapshots."""

    with h5py.File(hdf5_file, 'r') as f:
        # Get density data along axis
        rho = f['density'][:]  # Shape: (nx, ny, nz)

    # Extract axial density profile (average over cross-section)
    rho_axial = np.mean(rho, axis=(1, 2))

    # Normalize
    rho_norm = rho_axial / np.mean(rho_axial)

    # Find peaks (cores)
    peaks, properties = find_peaks(rho_norm, distance=10, prominence=0.1)

    if len(peaks) < 2:
        return None  # No fragmentation

    # Calculate spacings between peaks
    spacings = np.diff(peaks)

    # Convert to physical units
    dx = L_x / nx
    spacings_physical = spacings * dx

    # Median spacing
    lambda_median = np.median(spacings_physical)

    # Convert to λ/W units
    W_fil = 0.3  # Simulation half-width
    lambda_by_W = lambda_median / W_fil

    return {
        'n_cores': len(peaks),
        'lambda_W': lambda_by_W,
        'spacings': spacings_physical.tolist(),
    }
```

### 2. Classification Criteria

- **FRAGMENTED**: ≥ 2 density peaks with clear axial structure
- **STABLE**: No axial structure or single peak
- **RADIAL_DOMINATED**: Axial density variation < 2%

### 3. Expected Results

If λ/W extrapolation is valid:
- f = 1.5: λ/W ≈ 2.8–3.2
- f = 2.0: λ/W ≈ 2.6–3.0
- f = 2.6: λ/W ≈ 2.4–2.8
- f = 3.0: λ/W ≈ 2.2–2.6

If extrapolation fails:
- Sharp discontinuity in λ/W at f ≈ 1.5–1.8
- Different functional form than near-critical regime
- Or no longitudinal structure at all

## Deliverables

1. **Simulation results**: HDF5 snapshots for all 45 simulations
2. **Analysis**: λ/W measurements for each simulation
3. **Plots**: λ/W vs. f curve for supercritical regime
4. **Comparison**: Direct validation/refutation of extrapolation
