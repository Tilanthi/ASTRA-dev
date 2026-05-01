#!/bin/bash
#
# run_referee_campaigns.sh
#
# Convenience script for running Referee Response Campaigns on 200 vCPU cluster
#
# Usage:
#   ./run_referee_campaigns.sh          # Interactive menu
#   ./run_referee_campaigns.sh all     # Run all campaigns
#   ./run_referee_campaigns.sh C5      # Run Campaign 5 only
#   ./run_referee_campaigns.sh setup   # Setup environment only
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
ATHENA_BIN="${ATHENA_BIN:-/path/to/athena/bin/athena}"
MAX_PARALLEL="${MAX_PARALLEL:-25}"
PYTHON="${PYTHON:-python3}"

echo "======================================================================"
echo "  Referee Response Simulation Campaigns"
echo "  MNRAS Major Revision - 30 April 2026"
echo "======================================================================"
echo ""

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check Python
    if ! command -v "$PYTHON" &> /dev/null; then
        echo -e "${RED}Error: Python not found. Install Python 3.8+${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python found: $($PYTHON --version)${NC}"

    # Check Python packages
    required_packages="numpy scipy h5py pandas matplotlib yaml"
    for pkg in $required_packages; do
        if ! $PYTHON -c "import $pkg" 2>/dev/null; then
            echo -e "${RED}Error: Python package '$pkg' not found${NC}"
            echo "Install with: pip install $pkg"
            exit 1
        fi
    done
    echo -e "${GREEN}✓ All required Python packages installed${NC}"

    # Check Athena++ binary
    if [ ! -f "$ATHENA_BIN" ] && [ ! -x "$ATHENA_BIN" ]; then
        echo -e "${YELLOW}Warning: Athena++ binary not found at ATHENA_BIN=$ATHENA_BIN${NC}"
        echo "Set ATHENA_BIN environment variable or edit this script"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Athena++ binary found: $ATHENA_BIN${NC}"
    fi

    echo ""
}

# Setup environment
setup_environment() {
    echo -e "${YELLOW}Setting up environment...${NC}"

    # Create output directories
    for campaign in C5_TURBULENCE_LW C6_PERP_BETA C7_CRITICAL_TRANSITION; do
        mkdir -p "$campaign"/{logs,output}
    done

    # Create symlink to Athena++ if ATHENA_BIN is set
    if [ -f "$ATHENA_BIN" ]; then
        ln -sf "$ATHENA_BIN" ./athena
        echo -e "${GREEN}✓ Created symlink to Athena++ binary${NC}"
    fi

    echo -e "${GREEN}✓ Environment setup complete${NC}"
    echo ""
}

# Run Campaign 5
run_c5() {
    echo "======================================================================"
    echo "  Campaign 5: Turbulence λ/W Measurements"
    echo "  54 simulations | ~9 hours on 200 cores"
    echo "======================================================================"
    echo ""

    read -p "Run Campaign 5? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $PYTHON referee_response_campaign_runner.py \
            --campaign C5 \
            --config campaign5_turbulence_lambda_W_specification.yaml \
            --max-parallel "$MAX_PARALLEL"
    fi
}

# Run Campaign 6
run_c6() {
    echo "======================================================================"
    echo "  Campaign 6: Perpendicular-B β-Dependence"
    echo "  100 simulations | ~2 days on 200 cores"
    echo "======================================================================"
    echo ""

    echo -e "${YELLOW}Note: Campaign 6 requires more memory per simulation (32 GB)${NC}"
    echo -e "${YELLOW}Reducing max_parallel to 12 for Campaign 6${NC}"
    echo ""

    read -p "Run Campaign 6? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $PYTHON referee_response_campaign_runner.py \
            --campaign C6 \
            --config campaign6_perpendicular_beta_dependence_specification.yaml \
            --max-parallel 12
    fi
}

# Run Campaign 7
run_c7() {
    echo "======================================================================"
    echo "  Campaign 7: Critical Transition Mapping"
    echo "  135 simulations | ~22 hours on 200 cores"
    echo "======================================================================"
    echo ""

    read -p "Run Campaign 7? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $PYTHON referee_response_campaign_runner.py \
            --campaign C7 \
            --config campaign7_critical_transition_specification.yaml \
            --max-parallel "$MAX_PARALLEL"
    fi
}

# Run all campaigns
run_all() {
    echo "======================================================================"
    echo "  Running All Campaigns"
    echo "  Total: 289 simulations | ~3-4 days on 200 cores"
    echo "======================================================================"
    echo ""

    echo "Campaign order: C5 → C6 → C7"
    echo ""

    read -p "Run all campaigns? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Run Campaign 5
        run_c5
        echo ""

        # Run Campaign 6
        run_c6
        echo ""

        # Run Campaign 7
        run_c7
        echo ""

        echo "======================================================================"
        echo -e "${GREEN}All campaigns complete!${NC}"
        echo "======================================================================"
        echo ""
        echo "Next steps:"
        echo "1. Check campaign summaries: cat C*/campaign_summary.json"
        echo "2. Analyze results: python analysis/measure_lambda_W.py <sim_dir>"
        echo "3. Update paper with new λ/W measurements"
    fi
}

# Interactive menu
show_menu() {
    echo "Select an option:"
    echo "  1) Run Campaign 5 (Turbulence λ/W)"
    echo "  2) Run Campaign 6 (Perpendicular-B β-Dependence)"
    echo "  3) Run Campaign 7 (Critical Transition)"
    echo "  4) Run All Campaigns"
    echo "  5) Setup Environment Only"
    echo "  6) Check Prerequisites"
    echo "  0) Exit"
    echo ""
    read -p "Enter choice [0-6]: " choice

    case $choice in
        1) run_c5 ;;
        2) run_c6 ;;
        3) run_c7 ;;
        4) run_all ;;
        5) setup_environment ;;
        6) check_prerequisites ;;
        0) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
}

# Main
main() {
    check_prerequisites

    if [ "$1" = "setup" ]; then
        setup_environment
    elif [ "$1" = "all" ]; then
        setup_environment
        run_all
    elif [ "$1" = "C5" ]; then
        setup_environment
        run_c5
    elif [ "$1" = "C6" ]; then
        setup_environment
        run_c6
    elif [ "$1" = "C7" ]; then
        setup_environment
        run_c7
    else
        show_menu
    fi
}

main "$@"
