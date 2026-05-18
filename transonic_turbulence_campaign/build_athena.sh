#!/bin/bash
# build_athena.sh
# Automated Athena++ build script for transonic turbulence campaign

set -e  # Exit on error

echo "=== Athena++ Build Script for Transonic Turbulence Campaign ==="
echo ""

# Configuration
ATHENA_VERSION="v21.0"
ATHENA_REPO="https://github.com/PrincetonUniversity/athena-public-version"
BUILD_DIR="athena_build"
INSTALL_DIR="${TURBULENCE_CAMPAIGN_ROOT:-$(pwd)}/athena_install"

# Detect number of CPU cores for parallel build
if command -v nproc &> /dev/null; then
    NPROC=$(nproc)
elif command -v sysctl &> /dev/null; then
    NPROC=$(sysctl -n hw.ncpu)
else
    NPROC=4
fi

echo "Build configuration:"
echo "  Athena++ version: $ATHENA_VERSION"
echo "  Build directory: $BUILD_DIR"
echo "  Install directory: $INSTALL_DIR"
echo "  Parallel jobs: $NPROC"
echo ""

# Check for required modules
echo "Checking for required software..."

# Check for C compiler
if command -v gcc &> /dev/null; then
    echo "  ✓ gcc found: $(gcc --version | head -n1)"
else
    echo "  ✗ gcc not found"
    echo "    Load with: module load gcc/9.0.0"
    exit 1
fi

# Check for MPI
if command -v mpicc &> /dev/null; then
    echo "  ✓ MPI found: $(mpicc --version | head -n1)"
    MPI_CC="mpicc"
    MPI_CXX="mpicxx"
else
    echo "  ✗ MPI not found"
    echo "    Load with: module load openmpi/4.0.3"
    exit 1
fi

# Check for HDF5
if [ -n "$HDF5_DIR" ] && [ -d "$HDF5_DIR" ]; then
    echo "  ✓ HDF5 found at: $HDF5_DIR"
else
    echo "  ✗ HDF5_DIR not set"
    echo "    Set with: export HDF5_DIR=/path/to/hdf5"
    echo "    Or load with: module load hdf5/1.12.0"
    exit 1
fi

# Check for CMake
if command -v cmake &> /dev/null; then
    echo "  ✓ CMake found: $(cmake --version | head -n1)"
else
    echo "  ⚠ CMake not found (optional, for alternative build method)"
fi

# Check for Python
if command -v python3 &> /dev/null; then
    echo "  ✓ Python found: $(python3 --version)"
else
    echo "  ✗ Python not found (required for analysis)"
    exit 1
fi

echo ""

# Clone Athena++ if not present
if [ ! -d "$BUILD_DIR" ]; then
    echo "Cloning Athena++ repository..."
    git clone "$ATHENA_REPO" "$BUILD_DIR"
    cd "$BUILD_DIR"
    git checkout "$ATHENA_VERSION"
    echo "✓ Athena++ $ATHENA_VERSION cloned"
else
    echo "Athena++ directory already exists: $BUILD_DIR"
    cd "$BUILD_DIR"
fi

echo ""

# Configure build
echo "=== Configuring Athena++ ==="
echo "Turbulence-friendly configuration:"
echo "  - Problem: file_list (custom filament ICs)"
echo "  - HDF5: enabled"
echo "  - MPI: enabled"
echo "  - Gas: isothermal"
echo "  - MHD: stable (constrained transport)"
echo "  - FFT: fftw (for turbulence driving)"
echo ""

CONFIGURE_CMD="../configure \
    --prob=file_list \
    --hdf5=yes \
    --mpi=yes \
    --cxx=$MPI_CXX \
    --cc=$MPI_CC \
    --hdf5-path=$HDF5_DIR \
    --enable-cgl-solver \
    --fft=fftw \
    --with-gas=adiabatic_isothermal \
    --with-mhd=stable"

echo "Running: $CONFIGURE_CMD"
echo ""

# Check if configure script exists
if [ ! -f "configure" ]; then
    echo "ERROR: configure script not found"
    echo "  Running: ./configure"
    exit 1
fi

# Run configure
eval $CONFIGURE_CMD

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Configuration failed"
    echo "Common issues:"
    echo "  1. HDF5 not compiled with MPI support"
    echo "     Solution: Rebuild HDF5 with --enable-parallel"
    echo "  2. MPI compiler mismatch"
    echo "     Solution: Ensure mpicc and h5cc use same MPI library"
    echo "  3. Missing FFTW library"
    echo "     Solution: Install fftw3-dev or module load fftw"
    exit 1
fi

echo "✓ Configuration successful"
echo ""

# Build Athena++
echo "=== Building Athena++ ==="
echo "Running: make -j $NPROC"
echo ""

make -j "$NPROC"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Build failed"
    echo "Try:"
    echo "  1. Reduce parallel jobs: make -j 1"
    echo "  2. Clean and rebuild: make clean && make"
    echo "  3. Check compiler compatibility: mpicc --version"
    exit 1
fi

echo "✓ Build successful"
echo ""

# Verify executable
if [ -f "bin/athena" ]; then
    echo "✓ Executable found: bin/athena"
    echo ""
    echo "Executable information:"
    file bin/athena
    echo ""
    bin/athena -v 2>/dev/null || echo "Version info not available"
else
    echo "ERROR: Executable not found"
    exit 1
fi

# Create symlink in install directory
echo ""
echo "Creating symlink in install directory..."
mkdir -p "$INSTALL_DIR/bin"
ln -sf "$(pwd)/bin/athena" "$INSTALL_DIR/bin/athena"
echo "✓ Symlink created: $INSTALL_DIR/bin/athena"

# Update environment
echo ""
echo "=== Build Complete ==="
echo ""
echo "Add to your PATH:"
echo "  export PATH=\"$INSTALL_DIR/bin:\$PATH\""
echo ""
echo "Or use full path:"
echo "  $INSTALL_DIR/bin/athena -i <input_file>"
echo ""

# Run test simulation
echo "=== Running Verification Test ==="
echo "Creating minimal test problem..."

cat > /tmp/turb_test.in << 'EOF'
<job>
job_id = 0000
</job>

<time>
tlim = 0.01
</time>

<mesh>
nx1 = 32
nx2 = 16
nx3 = 16
</mesh>

<hydro>
iso_sound_speed = 1.0
</hydro>

<output>
dt_dir_samples = 0.01
</output>
EOF

echo "Running test simulation (should complete in <1 minute)..."
"$INSTALL_DIR/bin/athena" -i /tmp/turb_test.in > /tmp/turb_test.log 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Test simulation successful"
    rm -f /tmp/turb_test.in /tmp/turb_test.log
else
    echo "⚠ Test simulation failed. Check log:"
    cat /tmp/turb_test.log
fi

echo ""
echo "=== Athena++ Ready ==="
echo "Proceed to: ./run_resolution_test.sh"
