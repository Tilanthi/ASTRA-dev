# Compilation Instructions for IC Sensitivity Test Campaign

## Athena++ Setup

This campaign requires **two separate Athena++ binaries** with different problem generators:
- `athena_king`: Uses King profile initial conditions
- `athena_uniform`: Uses uniform density initial conditions

---

## Step 1: Obtain Athena++ Source Code

If you don't already have Athena++:

```bash
# Clone Athena++ repository (use v21.0 or later)
git clone https://github.com/PrincetonUniversity/athena-public-version.git athena_ic_sensitivity
cd athena_ic_sensitivity
git checkout v21.0
```

---

## Step 2: Install Problem Generator Files

Copy the problem generator files from this package to the Athena++ source:

```bash
# Copy King profile problem generator
cp src/filament_king_ic.cpp /path/to/athena/src/pgen/

# Copy uniform density problem generator
cp src/filament_uniform_ic.cpp /path/to/athena/src/pgen/
```

---

## Step 3: Configure and Compile King IC Binary

```bash
cd /path/to/athena

# Configure for King profile problem generator
./configure --prob=file_king_ic \
            --with-gas=hydro+mhd \
            --with-gravity=fft \
            --coord=cartesian

# Compile
make -j 8

# The binary will be at: bin/athena
# Rename it to athena_king
mv bin/athena bin/athena_king
```

---

## Step 4: Configure and Compile Uniform IC Binary

```bash
cd /path/to/athena

# Clean previous build
make clean

# Configure for uniform density problem generator
./configure --prob=file_uniform_ic \
            --with-gas=hydro+mhd \
            --with-gravity=fft \
            --coord=cartesian

# Compile
make -j 8

# The binary will be at: bin/athena
# Rename it to athena_uniform
mv bin/athena bin/athena_uniform
```

---

## Step 5: Copy Binaries to Campaign Directory

```bash
# Create directory for binaries
mkdir -p ../ic_sensitivity_test_may2026/bin

# Copy both binaries
cp bin/athena_king ../ic_sensitivity_test_may2026/bin/
cp bin/athena_uniform ../ic_sensitivity_test_may2026/bin/
```

---

## Step 6: Verify Binaries

```bash
cd ../ic_sensitivity_test_may2026

# Check that both binaries exist and are executable
ls -lh bin/athena_king bin/athena_uniform

# Test King IC binary
bin/athena_king -i /dev/null --help

# Test Uniform IC binary
bin/athena_uniform -i /dev/null --help
```

Both should print Athena++ version information.

---

## Alternative: Single Binary with Multiple PGEN

If your Athena++ build system supports compiling multiple problem generators into a single binary:

```bash
cd /path/to/athena

# Configure with both problem generators
./configure --prob=file_king_ic,file_uniform_ic \
            --with-gas=hydro+mhd \
            --with-gravity=fft \
            --coord=cartesian

# Compile
make -j 8

# Copy binary
cp bin/athena ../ic_sensitivity_test_may2026/bin/athena
```

**Note**: You'll need to modify `launch_ic_sensitivity.py` to use a single binary instead of selecting by IC type.

---

## Troubleshooting

### "problem generator not found" error

- Verify the problem generator file names match exactly: `filament_king_ic.cpp` and `filament_uniform_ic.cpp`
- Check that the files are in `src/pgen/` directory

### "undefined reference to fft" errors

- Ensure FFTW library is installed: `sudo apt-get install libfftw3-dev`
- Reconfigure with `--with-gravity=fft`

### Compilation fails with syntax errors

- Verify you're using Athena++ v21.0 or later
- Check that the problem generator files are complete (no truncation during copy)

---

## Dependencies

Required system packages:
- C++ compiler (g++ or clang++)
- MPI library (openmpi or mpich)
- FFTW3 library (`libfftw3-dev` on Ubuntu)
- HDF5 library (`libhdf5-dev` on Ubuntu)
- Python 3.7+ with h5py for analysis

---

## Quick Start Script

Save this as `compile_both.sh`:

```bash
#!/bin/bash
set -e

ATHENA_DIR="/path/to/athena"
CAMPAIGN_DIR="$(pwd)"

echo "Compiling King IC binary..."
cd "$ATHENA_DIR"
./configure --prob=file_king_ic --with-gas=hydro+mhd --with-gravity=fft --coord=cartesian
make clean
make -j 8
mv bin/athena "$CAMPAIGN_DIR/bin/athena_king"

echo "Compiling Uniform IC binary..."
cd "$ATHENA_DIR"
./configure --prob=file_uniform_ic --with-gas=hydro+mhd --with-gravity=fft --coord=cartesian
make clean
make -j 8
mv bin/athena "$CAMPAIGN_DIR/bin/athena_uniform"

echo "Done! Binaries are in $CAMPAIGN_DIR/bin/"
```

Run with: `bash compile_both.sh`
