#!/bin/bash
# Configuration for Expanded Referee Response Campaign
# Update these paths for your Ray cluster environment

# ── Athena++ Configuration ─────────────────────────────────────────────────────
# Path to Athena++ binary with filament_spacing_pr problem generator
# REQUIRED: Update this to point to your Athena++ installation
export ATHENA_BIN="/path/to/athena/bin/athena"

# ── Output Directory ───────────────────────────────────────────────────────────
# Base directory for all campaign outputs
# REQUIRED: Update this to your desired output location
export BASE_DIR="/data/referee_response_may2026"

# ── Ray Cluster Configuration ──────────────────────────────────────────────────
# Number of CPUs available on your Ray cluster
# Adjust based on your cluster configuration
export RAY_NUM_CPUS=220

# Number of concurrent simulations to run
# Each simulation uses 32 MPI ranks (NP=32)
# Concurrent simulations = RAY_NUM_CPUS / NP
export RAY_NUM_WORKERS=6

# ── Simulation Parameters ──────────────────────────────────────────────────────
# Wall-clock time limit per simulation (seconds)
# Default: 14400 = 4 hours
# Increase if many simulations timeout
export WALL_TIME=14400

# Simulation time limit (Jeans times)
# Default: 4.0 tJ (should be sufficient for f > 1.0)
export TLIM=4.0

# HDF5 output interval (Jeans times)
# Default: 0.02 tJ (fine sampling for λ/W measurement)
export HDF5_DT=0.02

# Maximum HDF5 storage before pruning (GB)
# Default: 8 GB per simulation
export MAX_HDF5_GB=8.0

# MPI ranks per simulation
# DO NOT CHANGE unless you modify the domain size
export NP=32

# ── Advanced Options ───────────────────────────────────────────────────────────
# Polling interval for simulation status (seconds)
export POLL_INTERVAL=8.0

# Fragmentation detection threshold (dimensionless)
# Default: 1e-6 tJ (dt below this triggers FRAG classification)
export DT_KILL=1.0e-6

# ── Display Configuration ─────────────────────────────────────────────────────
echo "Configuration loaded:"
echo "  ATHENA_BIN = $ATHENA_BIN"
echo "  BASE_DIR = $BASE_DIR"
echo "  RAY_NUM_CPUS = $RAY_NUM_CPUS"
echo "  RAY_NUM_WORKERS = $RAY_NUM_WORKERS"
echo "  WALL_TIME = $WALL_TIME seconds ($(($WALL_TIME/3600)) hours)"
echo ""
echo "To verify Athena++ binary:"
echo "  ls -lh $ATHENA_BIN"
echo ""
echo "To verify output directory exists:"
echo "  mkdir -p $BASE_DIR"
