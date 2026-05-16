#!/bin/bash
#
# run_all_tests.sh — Master script to execute all three validation campaigns
#
# This script runs the peer review validation tests in sequence:
#   1. TEST_M3_RESOLUTION: Resolution convergence test (48 sims)
#   2. TEST_M2_EQUILIBRIUM: Equilibrium IC test (20 sims)
#   3. TEST_M5_NONISOTHERMAL: Non-isothermal EOS test (15 sims)
#
# Total: 83 simulations
# Estimated runtime: ~190 hours on 220 cores
#

set -e  # Exit on error

echo "=============================================="
echo "Peer Review Validation Tests — Master Script"
echo "=============================================="
echo ""
echo "This will run three test campaigns:"
echo "  1. TEST_M3_RESOLUTION (48 simulations, ~110h)"
echo "  2. TEST_M2_EQUILIBRIUM (20 simulations, ~45h)"
echo "  3. TEST_M5_NONISOTHERMAL (15 simulations, ~35h)"
echo ""
echo "Total estimated runtime: ~190 hours on 220 cores"
echo ""

# Prompt user
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Starting at $(date)"
echo ""

# ── Check prerequisites ───────────────────────────────────────────────────────

echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Check Ray
if ! python3 -c "import ray" 2>/dev/null; then
    echo "ERROR: Ray not installed. Install with: pip install ray[default]"
    exit 1
fi

echo "✓ Python3 and Ray available"

# Check Athena++ binary
if [ ! -f "athena/bin/athena" ]; then
    echo "WARNING: athena/bin/athena not found"
    echo "Please create symlink or copy Athena++ binary to:"
    echo "  athena/bin/athena"
    echo ""
    read -p "Continue anyway? (yes/no): " continue_anyway
    if [ "$continue_anyway" != "yes" ]; then
        exit 1
    fi
else
    echo "✓ Athena++ binary found"
fi

# Create results directories
mkdir -p TEST_M3_RESOLUTION/logs
mkdir -p TEST_M2_EQUILIBRIUM/logs
mkdir -p TEST_M5_NONISOTHERMAL/logs
mkdir -p analysis/output

echo "✓ Results directories created"
echo ""

# ── Function to run a test campaign ─────────────────────────────────────────────

run_campaign() {
    local campaign_dir=$1
    local campaign_name=$2
    local script_name=$3

    echo "=============================================="
    echo "Running: $campaign_name"
    echo "=============================================="
    echo ""

    cd "$campaign_dir"

    if [ ! -f "$script_name" ]; then
        echo "ERROR: $script_name not found in $campaign_dir"
        cd ..
        return 1
    fi

    # Make script executable
    chmod +x "$script_name"

    # Run the campaign
    python3 "$script_name"
    exit_code=$?

    cd ..

    if [ $exit_code -ne 0 ]; then
        echo ""
        echo "ERROR: $campaign_name failed with exit code $exit_code"
        return 1
    fi

    echo ""
    echo "✓ $campaign_name completed successfully"
    echo ""

    return 0
}

# ── Run campaigns sequentially ─────────────────────────────────────────────────

# Campaign 1: Resolution test
run_campaign "TEST_M3_RESOLUTION" "TEST_M3_RESOLUTION: Resolution Convergence Test" "run_resolution_test.py" || exit 1

# Campaign 2: Equilibrium test
run_campaign "TEST_M2_EQUILIBRIUM" "TEST_M2_EQUILIBRIUM: Equilibrium IC Test" "run_equilibrium_test.py" || exit 1

# Campaign 3: Non-isothermal test
run_campaign "TEST_M5_NONISOTHERMAL" "TEST_M5_NONISOTHERMAL: Non-Isothermal EOS Test" "run_nonisothermal_test.py" || exit 1

# ── Run analysis ─────────────────────────────────────────────────────────────────

echo "=============================================="
echo "All campaigns completed!"
echo "=============================================="
echo ""
echo "Running analysis scripts..."
echo ""

cd analysis

echo "Analyzing TEST_M3_RESOLUTION..."
python3 analyze_resolution.py

echo ""
echo "Analyzing TEST_M2_EQUILIBRIUM..."
python3 analyze_equilibrium.py

echo ""
echo "Analyzing TEST_M5_NONISOTHERMAL..."
python3 analyze_nonisothermal.py

echo ""
echo "Generating combined report..."
python3 generate_report.py

cd ..

echo ""
echo "=============================================="
echo "All validation tests complete!"
echo "=============================================="
echo ""
echo "Finished at $(date)"
echo ""
echo "Results:"
echo "  TEST_M3_RESOLUTION/results/  — Simulation outputs"
echo "  TEST_M2_EQUILIBRIUM/results/  — Simulation outputs"
echo "  TEST_M5_NONISOTHERMAL/results/  — Simulation outputs"
echo "  analysis/output/  — Analysis results and figures"
echo "  analysis/VALIDATION_REPORT.pdf  — Combined report"
echo ""
echo "Thank you for supporting peer review validation!"
echo ""
