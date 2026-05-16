# Setup Instructions for HPC Cluster

## 1. Extract the Package

```bash
tar -xzf peer_review_validation_tests.tar.gz
cd peer_review_validation_tests/
```

## 2. Install Dependencies

```bash
# Load required modules (adjust for your cluster)
module load python/3.9
module load openmpi/4.1.1
module load hdf5/1.12.1
module load fftw/3.3.8

# Or use conda
conda create -n athena python=3.9 -y
conda activate athena
pip install ray[default]==2.8.0 h5py numpy matplotlib scipy
```

## 3. Configure Athena++ Binary

**Option A: Use existing Athena++ installation**

```bash
# Create symlink to your Athena++ binary
mkdir -p athena/bin
ln -s /path/to/your/athena/bin/athena athena/bin/athena

# Test
mpirun -np 4 athena/bin/athena -i test.in -d test_output/
```

**Option B: Compile Athena++ from source**

```bash
# Clone Athena++
cd ~
git clone https://github.com/PrincetonUniversity/athena-public-version
cd athena-public-version

# Configure with required options
./configure --prob=film_fragmentation \
            --coord=cartesian \
            --flux=hlld \
            --integr=vl2 \
            --ghost=ghost \
            --fft

# Compile
make all

# Create symlink in package
cd ~/peer_review_validation_tests
mkdir -p athena/bin
ln -s ~/athena-public-version/bin/athena athena/bin/athena
```

**Required Athena++ configuration:**
- Problem generator: `film_fragmentation` (or custom filament problem)
- Riemann solver: HLLD
- Self-gravity: FFT-based Poisson solver enabled
- MPI parallelization: Enabled
- HDF5 output: Enabled

## 4. Verify Installation

```bash
# Test Ray
python3 -c "import ray; print(f'Ray {ray.__version__} OK')"

# Test Athena++
cat > test.in << 'EOF'
<job>
problem_id = test

<time>
cfl_number = 0.3
tlim = 0.1
nlim = -1

<mesh>
nx1 = 32
x1min = -1.0
x1max = 1.0
ix1_bc = periodic
ox1_bc = periodic

nx2 = 32
x2min = -1.0
x2max = 1.0
ix2_bc = periodic
ox2_bc = periodic

nx3 = 32
x3min = -0.25
x3max = 0.25
ix3_bc = periodic
ox3_bc = periodic

<hydro>
iso_sound_speed = 1.0

<problem>
four_pi_G = 39.478418
mach_number = 2.0
plasma_beta = 1.0
wavelength = 2.0
perturb_ampl = 1.0e-4

<output1>
file_type = hdf5
variable = prim
id = out1
dt = 10.0
EOF

mkdir -p test_output
mpirun -np 4 athena/bin/athena -i test.in -d test_output/

# Check for output
ls test_output/*.h5  # Should see HDF5 files
rm -rf test_output test.in
```

## 5. Configure for Your Cluster

### Edit resource settings in each `run_*.py` script:

```python
# Adjust these values for your cluster
ATHENA_BIN = os.path.expanduser("~/athena/bin/athena")  # Path to Athena++
N_PROCS_PER_SIM = 16                                    # MPI ranks per simulation
N_CPUS_AVAILABLE = 220                                  # Total cores available
```

### For Ray on HPC:

```bash
# Set Ray temp directory (ensure fast filesystem)
export RAY_PLASMA_STORE_TIMEOUT_S=3600

# Optional: Restrict Ray to specific nodes
# export RAY_DISABLE_IP_MAC_CHECK=1
```

## 6. Dry Run (Single Simulation)

```bash
cd TEST_M3_RESOLUTION/

# Create minimal test
python3 -c "
import json
with open('config/test_points.json', 'r') as f:
    config = json.load(f)
pt = config['test_points'][0]
print(f'Test point: {pt}')
"

# Run one simulation manually
python3 run_resolution_test.py &
# Wait a few minutes, then check:
ls -lh results/
tail -f logs/*/athena.log
```

## 7. Full Execution

```bash
# Option A: Run all campaigns sequentially
chmod +x run_all_tests.sh
./run_all_tests.sh

# Option B: Run campaigns individually
cd TEST_M3_RESOLUTION/
python3 run_resolution_test.py
cd ../TEST_M2_EQUILIBRIUM/
python3 run_equilibrium_test.py
cd ../TEST_M5_NONISOTHERMAL/
python3 run_nonisothermal_test.py
```

## 8. Monitor Progress

```bash
# Check running simulations
ps aux | grep athena

# Monitor disk usage
watch -n 60 'du -sh TEST_*/results/'

# Check completion status
grep -l "success.*true" TEST_*/status_*.json
```

## 9. Troubleshooting

### Ray initialization fails

```bash
# Kill existing Ray
ray stop

# Clear plasma store
rm -rf /tmp/ray/

# Restart
ray start --head --num-cpus=220
```

### Athena++ fails with "segmentation fault"

```bash
# Reduce memory pressure
# In run_*.py, change:
N_PROCS_PER_SIM = 8  # Instead of 16

# Or reduce domain size
L1, L2, L3 = 4.0, 1.0, 1.0  # Instead of 8.0, 2.0, 2.0
```

### Out of disk space

```bash
# Reduce output frequency
# In run_*.py, change:
DT_OUTPUT = 1.0  # Instead of 0.5 (fewer snapshots)

# Or disable HDF5 outputs (keep only HST)
# Comment out <output1> section in make_input_file()
```

### MPI errors

```bash
# Check MPI compatibility
mpirun --version

# Ensure correct OpenMPI build
# Athena++ must be compiled with same major MPI version

# Test MPI
mpirun -np 16 hostname
```

## 10. Expected Output Structure

```
peer_review_validation_tests/
├── TEST_M3_RESOLUTION/
│   ├── results/
│   │   ├── RES_128cubed_R1_*/
│   │   │   ├── outputs/
│   │   │   │   ├── *.h5         # HDF5 snapshots
│   │   │   │   └── *.hst        # History file
│   │   │   └── athena.log       # Run log
│   │   └── status_resolution.json
│   └── logs/
│       └── ray_plasma/          # Ray temp files
├── TEST_M2_EQUILIBRIUM/
│   └── (similar structure)
├── TEST_M5_NONISOTHERMAL/
│   └── (similar structure)
└── analysis/
    ├── output/
    │   ├── resolution_convergence.pdf
    │   ├── equilibrium_comparison.pdf
    │   └── nonisothermal_effects.pdf
    └── VALIDATION_REPORT.pdf
```

## 11. Cleanup (After completion)

```bash
# Remove Ray plasma store
ray stop
rm -rf */logs/ray_plasma/

# Optional: Remove simulation outputs (keep only analysis)
# tar -czf validation_results_backup.tar.gz TEST_*/results/
# rm -rf TEST_*/results/

# Keep status files for analysis
ls TEST_*/status_*.json
```

---

## Support

For issues with:
- **Athena++**: See https://github.com/PrincetonUniversity/athena-public-version
- **Ray**: See https://docs.ray.io/
- **This package**: See README.md and individual campaign README files
