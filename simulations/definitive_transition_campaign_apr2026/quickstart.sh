#!/bin/bash
#
# Definitive 2D Fragmentation Transition Campaign - Quick Start Script
# Usage: bash quickstart.sh [--phase PHASE] [--resume]
#
# This is the FINAL MHD campaign for the ASTRA filament spacing paper.
# Total: 648 simulations, ~3 days on 200 vCPUs
#

# ==================== CONFIGURATION ====================
# UPDATE THESE PATHS FOR YOUR SYSTEM

ATHENA_BINARY="/path/to/athena/bin/athena"
SIMULATION_BASE="/path/to/simulations/definitive_transition_campaign_apr2026"
NUM_WORKERS=200

# ======================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_blue() {
    echo -e "${BLUE}[CAMPAIGN]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    if [ ! -f "$ATHENA_BINARY" ]; then
        log_error "Athena++ binary not found: $ATHENA_BINARY"
        log_error "Please update ATHENA_BINARY in quickstart.sh"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found"
        exit 1
    fi

    if ! python3 -c "import ray" 2> /dev/null; then
        log_error "Ray Python package not found"
        log_error "Install with: pip install ray"
        exit 1
    fi

    if ! python3 -c "import h5py, scipy, matplotlib" 2> /dev/null; then
        log_error "Required Python packages missing"
        log_error "Install with: pip install h5py scipy matplotlib"
        exit 1
    fi

    log_info "✓ All dependencies OK"
}

# Print campaign banner
print_banner() {
    echo ""
    echo "=============================================="
    log_blue "Definitive 2D Fragmentation Transition"
    log_blue "Campaign - FINAL MHD Run"
    echo "=============================================="
    echo "Athena++ binary: $ATHENA_BINARY"
    echo "Output directory: $SIMULATION_BASE"
    echo "Workers: $NUM_WORKERS"
    echo ""
    echo "Campaign specs:"
    echo "  • 9 f values: 1.4-2.2"
    echo "  • 6 β values: 0.3-1.3"
    echo "  • 5 M values: 1.0-5.0"
    echo "  • 2 seeds: 42, 137"
    echo "  • Total: 648 simulations"
    echo "  • Resolution: 256³ cells"
    echo "  • Estimated time: ~3 days on 200 cores"
    echo ""
    echo "This is the FINAL MHD campaign."
    echo "No follow-up runs needed."
    echo "=============================================="
    echo ""
}

# Step 1: Generate configurations
step1_generate() {
    log_info "Step 1: Generating 648 simulation configurations..."

    python3 generate_simulations.py

    if [ -f "$SIMULATION_BASE/simulation_manifest.json" ]; then
        log_info "✓ Configurations generated successfully"
        log_info "  Manifest: $SIMULATION_BASE/simulation_manifest.json"

        # Count simulations
        count=$(python3 -c "import json; print(len(json.load(open('$SIMULATION_BASE/simulation_manifest.json'))))")
        log_info "  Total simulations: $count"
    else
        log_error "Failed to generate configurations"
        exit 1
    fi
}

# Step 2: Run simulations
step2_run() {
    local phase="${1:-all}"

    log_info "Step 2: Running simulations with Ray..."
    log_info "  Phase: $phase"

    if [ ! -f "$SIMULATION_BASE/simulation_manifest.json" ]; then
        log_error "Manifest not found. Run step 1 first."
        exit 1
    fi

    # Check if resume requested
    if [ "$RESUME" = "true" ]; then
        log_info "Resume mode: skipping completed simulations"
        RESUME_FLAG="--resume"
    else
        RESUME_FLAG=""
    fi

    python3 run_campaign.py \
        --phase "$phase" \
        --num-workers $NUM_WORKERS \
        --athena-binary "$ATHENA_BINARY" \
        --simulation-base "$SIMULATION_BASE" \
        $RESUME_FLAG

    log_info "✓ Simulations completed"
}

# Step 3: Analyze results
step3_analyze() {
    log_info "Step 3: Analyzing results..."

    if [ ! -f "$SIMULATION_BASE/campaign_summary.json" ]; then
        log_warn "Campaign summary not found. Did simulations complete?"
        log_warn "Attempting analysis anyway..."
    fi

    python3 analyze_campaign.py \
        --simulation-base "$SIMULATION_BASE" \
        --output "definitive_transition_analysis.json"

    if [ -f "$SIMULATION_BASE/definitive_transition_analysis.json" ]; then
        log_info "✓ Analysis complete"
        log_info "  Results: $SIMULATION_BASE/definitive_transition_analysis.json"
        log_info "  Figures: $SIMULATION_BASE/figures/"

        # Print summary
        log_info "  Results preview:"
        python3 -c "
import json
with open('$SIMULATION_BASE/definitive_transition_analysis.json') as f:
    data = json.load(f)
print(f'  Analyzed: {len(data)} simulations')
if data:
    frag_count = sum(1 for d in data if d['C_final'] > 2.0)
    supp_count = sum(1 for d in data if d['C_final'] < 1.5)
    trans_count = len(data) - frag_count - supp_count
    print(f'  Fragmented: {frag_count}')
    print(f'  Transition: {trans_count}')
    print(f'  Suppressed: {supp_count}')
"
    else
        log_error "Analysis failed"
        exit 1
    fi
}

# Main execution
main() {
    local step="${1:-all}"
    RESUME="false"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --step)
                step="$2"
                shift 2
                ;;
            --phase)
                PHASE="$2"
                shift 2
                ;;
            --resume)
                RESUME="true"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: bash quickstart.sh [--step STEP] [--phase PHASE] [--resume]"
                echo "Steps: 1 (generate), 2 (run), 3 (analyze), all (default)"
                echo "Phases: primary, extended, all (default)"
                exit 1
                ;;
        esac
    done

    print_banner
    check_dependencies

    case "$step" in
        1)
            step1_generate
            ;;
        2)
            step2_run "${PHASE:-all}"
            ;;
        3)
            step3_analyze
            ;;
        all)
            step1_generate
            echo ""
            step2_run "${PHASE:-all}"
            echo ""
            step3_analyze
            ;;
        *)
            log_error "Unknown step: $step"
            echo "Usage: bash quickstart.sh [--step STEP]"
            echo "Steps: 1 (generate), 2 (run), 3 (analyze), all (default)"
            exit 1
            ;;
    esac

    echo ""
    log_info "=============================================="
    log_blue "CAMPAIGN STATUS: COMPLETE"
    log_info "=============================================="
    log_info "Definitive 2D Fragmentation Transition"
    log_info "Campaign finished successfully!"
    echo ""
    log_info "Next steps:"
    log_info "1. Review results in:"
    log_info "   $SIMULATION_BASE/definitive_transition_analysis.json"
    log_info "2. View figures in:"
    log_info "   $SIMULATION_BASE/figures/"
    log_info "3. Update paper with definitive results"
    log_info "=============================================="
}

# Parse arguments early
STEP="all"
PHASE="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        --step)
            STEP="$2"
            shift 2
            ;;
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --resume)
            RESUME="true"
            shift
            ;;
        *)
            # Unknown argument, will be handled in main()
            break
            ;;
    esac
done

main "$STEP"
