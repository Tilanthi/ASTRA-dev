# Athena++ Setup for Transonic Turbulence Simulations

## Prerequisites

### System Requirements
- Linux-based cluster (Ray cluster: 220 nodes, CPUs per node varies)
- HDF5 library (version ≥ 1.10)
- MPI library (OpenMPI or MPICH ≥ 3.0)
- C++ compiler with C++14 support (gcc ≥ 7.0, clang ≥ 5.0)
- Python ≥ 3.7 (for analysis scripts)
- Git (for cloning Athena++)

### Recommended Software Versions
```bash
GCC: 9.0 or later
OpenMPI: 4.0.3 or later
HDF5: 1.12.0 or later (with MPI support)
CMake: 3.20 or later
Python: 3.8 or later
```

## Step 1: Clone and Build Athena++

### 1.1 Clone Repository
```bash
cd /path/to/your/workspace
git clone https://github.com/PrincetonUniversity/athena-public-version
cd athena-public-version
git checkout v21.0  # Stable version with good turbulence support
```

### 1.2 Load Required Modules (Ray Cluster)
```bash
# Adjust module names based on your cluster configuration
module load gcc/9.0.0
module load openmpi/4.0.3
module load hdf5/1.12.0
module load cmake/3.20.0
module load python/3.8.5
```

### 1.3 Configure Build
```bash
# Create build directory
mkdir build
cd build

# Configure with turbulence-friendly options
../configure \
    --prob=file_list \
    --hdf5=yes \
    --mpi=yes \
    --cxx=/usr/bin/mpicxx \
    --cc=/usr/bin/mpicc \
    --f90=/usr/bin/mpifort \
    --hdf5-path=$HDF5_DIR \
    --enable-cgl-solver \
    --fft=fftw \
    --with-gas=adiabatic_isothermal \
    --with-mhd=stable
```

**Critical Configuration Options for Turbulence:**
- `--prob=file_list`: Use file_list problem type
- `--hdf5=yes`: Required for checkpoint analysis
- `--mpi=yes`: Parallel execution
- `--enable-cgl-solver`: Constrained transport for ∇·B control
- `--with-gas=adiabatic_isothermal`: Isothermal equation of state

### 1.4 Build Athena++
```bash
# Use multiple cores for faster compilation
make -j 16

# Verify build success
bin/athena -v  # Should display version info
```

## Step 2: Test Installation

### 2.1 Basic Test
```bash
cd ../test/turbulence
./test.sh  # Run built-in turbulence tests
```

### 2.2 Resolution Test (Mini Campaign)
```bash
# Create minimal test case
cd ../../transonic_turbulence_campaign/config
# Use provided test input file
cp inputs/turb_512.fiducial/athena.input.test .
../athena-public-version/build/bin/athena -i athena.input.test

# Check output
ls -lh *.hdf5  # Should produce output files
```

## Step 3: Ray-Specific Optimizations

### 3.1 Create Job Submission Script Template
```bash
#!/bin/bash
#SBATCH --job-name=turb_fil_512
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=220
#SBATCH --cpus-per-task=1
#SBATCH --time=48:00:00
#SBATCH --output=turb_%j.out
#SBATCH --error=turb_%j.err

module load gcc/9.0.0 openmpi/4.0.3 hdf5/1.12.0

# Set OpenMP threads
export OMP_NUM_THREADS=1

# Run simulation
mpirun -np 220 /path/to/athena-public-version/build/bin/athena -i athena.input
```

### 3.2 Memory Management
For 512³ resolution with domain 8×2×2λ_J:
- **Memory per core**: ~2 GB
- **Total memory**: ~440 GB for 220 cores
- **Recommendation**: Use nodes with ≥ 8 GB RAM per core

### 3.3 I/O Optimization
```bash
# Use burst size for checkpointing
# Add to athena.input:
<output>
file_type       = hdf5       # HDF5 output format
dt_dir_samples   = 0.05       # Output every 0.05 t_J
variable_dt      = true       # Allow adaptive timesteps
</output>
```

## Step 4: File List Problem Setup

### 4.1 Problem Source Files
Athena++ uses a "file list" system for problems. Create the file list:

```bash
cd athena-public-version/src/prob
vi file_list.cpp
```

### 4.2 Essential Components for Filament Simulations
```cpp
// file_list.cpp must include:
#include "filament.hpp"           // Filament initial conditions
#include "turbulence.hpp"         // Turbulent driving
#include "magnetic_field.hpp"     // Magnetic field initialization
#include "outputs.hpp"            // Output handling
```

### 4.3 Compile File List
```bash
make clean
make -j 16
```

## Step 5: Verification Test

### 5.1 Small-Scale Test (128³)
Before running full 512³, verify setup with 128³:

```bash
# Modify athena.input for quick test:
nx1 = 128
nx2 = 32
nx3 = 32
nghost = 3

# Run for 0.1 t_J
tlim = 0.1

# Verify:
# 1. Simulation starts without errors
# 2. Turbulence driving activates
# 3. Output files are produced
```

### 5.2 Check Turbulence Parameters
```python
# Monitor initial turbulence development
import h5py
import numpy as np

with h5py.File('turb_fil.0.0100.h5') as f:
    rho = f['prim']['rho'][()]  # Density field
    # Calculate rms velocity
    v_rms = np.sqrt(np.mean((f['prim']['vel'][()])**2))
    print(f"Initial Mach: {v_rms:.3f}")
```

## Common Issues and Solutions

### Issue 1: "segmentation fault" at startup
**Cause**: Incompatible MPI/Atlas libraries
**Solution**: Ensure `--mpi=yes` uses same MPI library as HDF5

```bash
# Check MPI consistency
mpicc --showme:libs
h5cc --showme:libs

# Both should show same libmpi.so path
```

### Issue 2: Turbulence decays immediately
**Cause**: Insufficient driving amplitude
**Solution**: Increase `driving_scale` in athena.input:

```python
# In athena.input:
<problem>
driving_scale = 2.0    # Increase from 1.0
driving_auto = true
</problem>
```

### Issue 3: |∇·B| grows rapidly
**Cause**: Unstable divergence cleaning
**Solution**: Enable more frequent divergence cleaning:

```python
# In athena.input:
<magnetic>
divb_clean = "powell"    # Use Powell's method
divb_tol = 1e-10          # Stricter tolerance
</magnetic>
```

## Performance Tuning

### Compiler Optimization
For maximum performance on Ray cluster:

```bash
CXXFLAGS="-O3 -march=native -funroll-loops"
CFLAGS="-O3 -march=native -funroll-loops"

# Reconfigure with optimization flags
../configure --with-cflags="$CFLAGS" --with-cxxflags="$CXXFLAGS" ...
```

### MPI Optimization
For large domains (512³), use MPI collective optimization:

```bash
export MPI_PARAM_MPI_COLL_ML=0  # Disable ML-based collectives
mpirun -np 220 --mca btl_openib_allow_bad_module_placement 1 \
        /path/to/athena -i athena.input
```

## Post-Build Verification

Run this verification script:
```bash
cd transonic_turbulence_campaign/scripts
bash verify_athena_build.sh
```

This will check:
1. Binary executable exists and is executable
2. Required HDF5 libraries are linked
3. MPI functionality works correctly
4. File list problem is properly compiled

## Next Steps

After successful Athena++ setup:
1. Proceed to `RAY_CLUSTER.md` for cluster-specific setup
2. Review `PARAMETERS.md` for simulation configuration
3. Run `./run_resolution_test.sh` to begin Phase 1

## Getting Help

### Athena++ Resources
- Documentation: https://athena.readthedocs.io/
- GitHub Issues: https://github.com/PrincetonUniversity/athena-public-version/issues
- User Forum: https://athenaastro.groups.io/g/athena-users

### Cluster-Specific Help
- Ray cluster sysadmin: [Contact info]
- Local HPC support: [Contact info]

## Appendix: Alternative Build Methods

### Using Spack (Recommended for HPC Clusters)
```bash
spack install athena+hdf5+mpi@21.0
spack load athena
```

### Using Container (Docker/Singularity)
```bash
# Singularity definition file
Bootstrap: docker
From: ubuntu:20.04

%post
    apt-get update && apt-get install -y \
        gcc-9 openmpi-bin hdf5-tools cmake git
    git clone https://github.com/PrincetonUniversity/athena-public-version
    cd athena-public-version
    git checkout v21.0
    ./configure --prob=file_list --hdf5=yes --mpi=yes
    make -j 16
%runscript
    export OMP_NUM_THREADS=1
    exec /athena-public-version/build/bin/athena "$@"
```

Build image:
```bash
sudo singularity build athena-turb.sif Singularity
```

---
**Last updated**: 2026-05-18
**Tested on**: Ray cluster, 220 nodes, GCC 9.0, OpenMPI 4.0.3
