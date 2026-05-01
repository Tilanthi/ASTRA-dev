#!/bin/bash
# Athena++ compilation script for filament spacing campaign

set -e

echo "======================================================================"
echo "Athena++ Compilation Script"
echo "======================================================================"

ATHENA_VERSION="v21.0"
ATHENA_DIR="athena${ATHENA_VERSION}"
BINARY_NAME="athena_filament_pr"

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
    wget https://github.com/PrincetonUniversity/athena-public/archive/refs/tags/${ATHENA_VERSION}.tar.gz
    tar -xzf ${ATHENA_VERSION}.tar.gz
    mv athena-public-${ATHENA_VERSION} $ATHENA_DIR
    rm ${ATHENA_VERSION}.tar.gz
fi

# Copy problem generator
echo "Installing filament spacing problem generator..."
cp ../templates/filament_spacing_pr.cpp $ATHENA_DIR/src/prob/filament_spacing_pr.cpp

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
else
    echo "ERROR: Compilation failed"
    exit 1
fi
