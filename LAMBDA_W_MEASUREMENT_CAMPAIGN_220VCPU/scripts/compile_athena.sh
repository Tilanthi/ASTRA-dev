#!/bin/bash
# Athena++ compilation script for λ/W Direct Measurement Campaign

set -e

echo "======================================================================"
echo "Athena++ Compilation for λ/W Direct Measurement Campaign"
echo "======================================================================"

ATHENA_VERSION="v21.0"
ATHENA_DIR="athena${ATHENA_VERSION}"
BINARY_NAME="athena_filament"

# Check if already compiled
if [ -f "$BINARY_NAME" ]; then
    echo "Binary $BINARY_NAME already exists."
    echo "Recompile? (y/n)"
    read -r response
    if [[ ! $response =~ ^[Yy]$ ]]; then
        echo "Exiting."
        exit 0
    fi
fi

# Download Athena++ if not present
if [ ! -d "$ATHENA_DIR" ]; then
    echo "Downloading Athena++ ${ATHENA_VERSION}..."
    if command -v wget &> /dev/null; then
        wget https://github.com/PrincetonUniversity/athena-public/archive/refs/tags/${ATHENA_VERSION}.tar.gz
    elif command -v curl &> /dev/null; then
        curl -L -o ${ATHENA_VERSION}.tar.gz https://github.com/PrincetonUniversity/athena-public/archive/refs/tags/${ATHENA_VERSION}.tar.gz
    else
        echo "ERROR: Neither wget nor curl available. Please install one."
        exit 1
    fi
    tar -xzf ${ATHENA_VERSION}.tar.gz
    mv athena-public-${ATHENA_VERSION} $ATHENA_DIR
    rm ${ATHENA_VERSION}.tar.gz
fi

# Copy problem generator
echo "Installing filament fragmentation problem generator..."
PROBLEM_SOURCE="../templates/filament_spacing_pr.cpp"
PROBLEM_DEST="${ATHENA_DIR}/src/prob/filament_spacing_pr.cpp"

if [ -f "$PROBLEM_SOURCE" ]; then
    cp "$PROBLEM_SOURCE" "$PROBLEM_DEST"
else
    echo "ERROR: Problem generator not found at $PROBLEM_SOURCE"
    echo "Please ensure the filament_spacing_pr.cpp template is available."
    exit 1
fi

# Configure
echo "Configuring Athena++..."
cd $ATHENA_DIR

python3 configure.py \
    --prob filament_spacing_pr \
    --flux hlld \
    --integrators vl2 \
    --coord cartesian_3d \
    --ghost ghost-zone \
    --mpi \
    --hdf5 \
    --fftw \
    --omp

# Compile
echo "Compiling Athena++..."
make clean
make -j 16

# Copy binary
if [ -f "bin/athena" ]; then
    cp bin/athena ../$BINARY_NAME
    echo "======================================================================"
    echo "Compilation successful!"
    echo "Binary created: ../$BINARY_NAME"
    echo "======================================================================"
    echo ""
    echo "IMPORTANT: This campaign requires HDF5 snapshots for λ/W extraction."
    echo "The problem generator will output multiple HDF5 files at specified times."
    echo "======================================================================"
else
    echo "ERROR: Compilation failed"
    exit 1
fi
