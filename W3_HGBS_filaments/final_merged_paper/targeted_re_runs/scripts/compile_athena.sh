#!/bin/bash
# Athena++ Compilation Script for Filament Spacing Re-run Campaign
# Compiles Athena++ v21.0 with self-gravity, MPI, and FFT support

set -e  # Exit on error

ATHENA_VERSION="v21.0"
ATHENA_DIR="athena-${ATHENA_VERSION}"
BINARY_NAME="../athena_reun"

echo "================================================"
echo "Athena++ Compilation Script"
echo "================================================"
echo "Version: ${ATHENA_VERSION}"
echo "Target binary: ${BINARY_NAME}"
echo ""

# Check if already compiled
if [ -f "${BINARY_NAME}" ]; then
    echo "Binary already exists: ${BINARY_NAME}"
    read -p "Recompile? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing binary."
        exit 0
    fi
    rm -f "${BINARY_NAME}"
fi

# Download Athena++ if not present
if [ ! -d "${ATHENA_DIR}" ]; then
    echo "Downloading Athena++ ${ATHENA_VERSION}..."
    wget https://github.com/PrincetonUniversity/athena/archive/refs/tags/${ATHENA_VERSION}.tar.gz

    echo "Extracting..."
    tar -xzf ${ATHENA_VERSION}.tar.gz
    rm ${ATHENA_VERSION}.tar.gz

    echo "Downloaded and extracted: ${ATHENA_DIR}/"
else
    echo "Using existing directory: ${ATHENA_DIR}/"
fi

# Navigate to Athena++ directory
cd "${ATHENA_DIR}"

echo ""
echo "Configuring Athena++..."
echo "  Problem generator: filament_spacing_re-run.cpp"
echo "  Physics: Self-gravity, MHD, Isothermal EOS"
echo "  Parallel: MPI"
echo "  Poisson solver: FFT"
echo ""

# Configure with required options
./configure \
    --prob=file_spacing \
    --eos=isothermal \
    --flux=hllc \
    --integrator=vl2 \
    --gravity=fft \
    --mpi \
    --fftw

echo ""
echo "Compiling... (this may take 5-10 minutes)"
echo ""

# Compile with 4 parallel jobs
make -j4

# Check if compilation succeeded
if [ ! -f "bin/athena" ]; then
    echo "ERROR: Compilation failed. Binary not found."
    echo "Check the error messages above."
    exit 1
fi

echo ""
echo "Compilation successful!"
echo ""

# Copy binary to parent directory
cp bin/athena "${BINARY_NAME}"

# Verify binary
echo "Binary created:"
ls -lh "${BINARY_NAME}"

echo ""
echo "Testing binary..."
${BINARY_NAME} --help || echo "Binary executable."

echo ""
echo "================================================"
echo "Compilation complete!"
echo "Binary location: ${BINARY_NAME}"
echo "================================================"
