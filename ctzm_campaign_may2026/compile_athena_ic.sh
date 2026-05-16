#!/bin/bash
# ========================================================================
# CTZM Campaign: Athena++ Compilation Script
# ========================================================================
#
# Compiles Athena++ with the filament_ctzm.cpp problem generator
# for the Critical Transition Zone Mapping campaign.
#
# Usage:
#   ./compile_athena_ic.sh [athena_root_directory]
#
# Arguments:
#   athena_root_directory: Path to Athena++ root (optional, defaults to ../../athena++)
#
# Output:
#   Binary: athena_ic (in current directory)
#
# Requirements:
#   - HDF5 library with development headers
#   - MPI library (mpicc, mpicxx)
#   - FFTW library (for self-gravity)
#   - Athena++ source tree
#
# ========================================================================

set -e  # Exit on error

# ========================================================================
# Configuration
# ========================================================================

ATHENA_ROOT="${1:-../../athena++}"
PROBLEM_GENERATOR="filament_ctzm.cpp"
BINARY_NAME="athena_ic"
COMPILER="gnu"
DEBUG="OFF"

# Required Athena++ modules
MODULES=(
    "fft"           # FFT-based gravity solver
    "grav"          # Self-gravity
    "hdf5"          # HDF5 output
    "mpi"           # Parallel execution
    "omp"           # OpenMP (optional, can be disabled)
)

# ========================================================================
# Functions
# ========================================================================

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

check_requirements() {
    log_info "Checking requirements..."

    # Check for MPI
    if ! command -v mpicc &> /dev/null; then
        log_error "MPI compiler (mpicc) not found"
        exit 1
    fi

    # Check for HDF5
    if ! pkg-config --exists hdf5; then
        log_error "HDF5 library not found"
        log_error "Install with: apt-get install libhdf5-mpi-dev (Ubuntu/Debian)"
        exit 1
    fi

    # Check for FFTW
    if ! pkg-config --exists fftw3-mpi; then
        log_error "FFTW library not found"
        log_error "Install with: apt-get install libfftw3-mpi-dev (Ubuntu/Debian)"
        exit 1
    fi

    # Check for Athena++ source
    if [ ! -d "$ATHENA_ROOT" ]; then
        log_error "Athena++ source directory not found: $ATHENA_ROOT"
        exit 1
    fi

    # Check for problem generator
    if [ ! -f "$PROBLEM_GENERATOR" ]; then
        log_error "Problem generator not found: $PROBLEM_GENERATOR"
        exit 1
    fi

    log_info "All requirements satisfied"
}

configure_athena() {
    log_info "Configuring Athena++..."

    cd "$ATHENA_ROOT"

    # Clean previous build
    rm -rf build

    # Create build directory
    mkdir -p build
    cd build

    # Configure with required modules
    log_info "Running Python configure script..."

    python ../configure.py \
        --prob "$PROBLEM_GENERATOR" \
        --cc "mpicc" \
        --cxx "mpicxx" \
        --flux "hlld" \
        --coord "cartesian" \
        --bg "periodic" \
        --eos "isothermal" \
        "${MODULES[@]/#/--}" \
        "$DEBUG"

    if [ $? -ne 0 ]; then
        log_error "Athena++ configuration failed"
        exit 1
    fi

    log_info "Configuration successful"
}

compile_athena() {
    log_info "Compiling Athena++..."

    cd "$ATHENA_ROOT/build"

    # Compile with 8 parallel jobs
    make -j8

    if [ $? -ne 0 ]; then
        log_error "Athena++ compilation failed"
        exit 1
    fi

    log_info "Compilation successful"
}

install_binary() {
    log_info "Installing binary..."

    cd -  # Return to campaign directory

    # Copy binary to campaign directory
    cp "$ATHENA_ROOT/build/bin/$BINARY_NAME" .

    if [ $? -ne 0 ]; then
        log_error "Failed to copy binary"
        exit 1
    fi

    chmod +x "$BINARY_NAME"

    log_info "Binary installed: ./$BINARY_NAME"
}

verify_binary() {
    log_info "Verifying binary..."

    # Check if binary runs
    if ./"$BINARY_NAME" --help &> /dev/null; then
        log_info "Binary verification successful"
    else
        log_error "Binary verification failed"
        exit 1
    fi

    # Print binary info
    log_info "Binary information:"
    ./"$BINARY_NAME" --version || true
}

# ========================================================================
# Main Execution
# ========================================================================

main() {
    log_info "=========================================="
    log_info "CTZM Campaign: Athena++ Compilation"
    log_info "=========================================="
    log_info "Athena++ root: $ATHENA_ROOT"
    log_info "Problem generator: $PROBLEM_GENERATOR"
    log_info "Output binary: $BINARY_NAME"
    log_info "=========================================="

    # Check requirements
    check_requirements

    # Configure Athena++
    configure_athena

    # Compile Athena++
    compile_athena

    # Install binary
    install_binary

    # Verify binary
    verify_binary

    log_info "=========================================="
    log_info "Compilation completed successfully!"
    log_info "Binary: ./$BINARY_NAME"
    log_info "=========================================="
}

# Run main function
main "$@"
