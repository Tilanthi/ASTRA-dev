#!/bin/bash
# Master launch script for peer review response campaign
# This script manages the complete campaign execution

set -e

echo "======================================================================"
echo "Peer Review Response Campaign - Filament Spacing MHD Simulations"
echo "Master Launch Script"
echo "======================================================================"

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Check required Python packages
python3 -c "import ray, numpy, pandas, matplotlib" 2>/dev/null || {
    echo "ERROR: Missing required Python packages"
    echo "Install with: pip install ray numpy pandas matplotlib"
    exit 1
}

# Check MPI
if ! command -v mpirun &> /dev/null; then
    echo "ERROR: mpirun not found (MPI required for Athena++)"
    exit 1
fi

# Check Ray availability
python3 -c "import ray; ray.init(num_cpus=200, ignore_reinit_error=True); ray.shutdown()" || {
    echo "ERROR: Ray cannot initialize with 200 CPUs"
    echo "Check: ray start --head"
    exit 1
}

echo "✓ Prerequisites satisfied"
echo ""

# Check Athena++ binary
if [ ! -f "./athena_filament_pr" ]; then
    echo "WARNING: athena_filament_pr not found"
    echo ""
    echo "Would you like to compile Athena++ now? (y/n)"
    read -r response
    if [[ $response =~ ^[Yy]$ ]]; then
        bash scripts/compile_athena.sh
    else
        echo "Cannot proceed without Athena++ binary"
        exit 1
    fi
fi

echo "✓ Athena++ binary found"
echo ""

# Check configuration
if [ ! -f "config/simulation_manifest.json" ]; then
    echo "ERROR: simulation_manifest.json not found"
    exit 1
fi

echo "✓ Configuration found"
echo ""

# Show campaign summary
echo "Campaign Summary:"
echo "------------------"
python3 << 'EOF'
import json
with open('config/simulation_manifest.json') as f:
    manifest = json.load(f)

by_phase = {}
by_priority = {}
for sim in manifest:
    p = sim['phase']
    by_phase[p] = by_phase.get(p, 0) + 1
    prio = sim.get('priority', 999)
    by_priority[prio] = by_priority.get(prio, 0) + 1

print(f"Total simulations: {len(manifest)}")
print(f"\nBy phase:")
for p in sorted(by_phase.keys()):
    print(f"  Phase {p}: {by_phase[p]} simulations")

print(f"\nBy priority:")
for prio in sorted(by_priority.keys()):
    print(f"  Priority {prio}: {by_priority[prio]} simulations"

# Field geometry breakdown
bfield_count = {}
for sim in manifest:
    b = sim.get('bfield', 'longitudinal')
    bfield_count[b] = bfield_count.get(b, 0) + 1

print(f"\nBy field geometry:")
for b, count in bfield_count.items():
    print(f"  {b}: {count} simulations")
EOF

echo ""
echo "======================================================================"

# Ask what to run
echo ""
echo "Select execution mode:"
echo "  1) Phase 1 only (Near-critical, 80 sims)"
echo "  2) Phase 2 only (Perpendicular field, 96 sims)"
echo "  3) Phase 3 only (Oblique calibration, 90 sims)"
echo "  4) Phase 4 only (Adiabatic, 54 sims)"
echo "  5) Phases 1+2 (Priority 1, 176 sims)"
echo "  6) All phases (Full campaign, 320 sims)"
echo "  7) Single simulation (for testing)"
echo "  8) Analysis only (skip simulation)"
echo "  q) Quit"
echo ""
read -p "Enter choice [1-8 or q]: " choice

case $choice in
    1)
        echo "Launching Phase 1 (Near-critical)..."
        python3 scripts/launch_campaign.py --phase 1
        ;;
    2)
        echo "Launching Phase 2 (Perpendicular field)..."
        python3 scripts/launch_campaign.py --phase 2
        ;;
    3)
        echo "Launching Phase 3 (Oblique calibration)..."
        python3 scripts/launch_campaign.py --phase 3
        ;;
    4)
        echo "Launching Phase 4 (Adiabatic)..."
        python3 scripts/launch_campaign.py --phase 4
        ;;
    5)
        echo "Launching Phases 1+2 (Priority 1)..."
        python3 scripts/launch_campaign.py --phase 1 2
        ;;
    6)
        echo "Launching Full Campaign (All phases)..."
        python3 scripts/launch_campaign.py --all
        ;;
    7)
        echo "Enter simulation ID:"
        read sim_id
        python3 scripts/launch_campaign.py --sim "$sim_id"
        ;;
    8)
        echo "Running analysis only..."
        python3 scripts/analyze_campaign.py
        ;;
    q|Q)
        echo "Exiting"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "======================================================================"
echo "Campaign execution complete!"
echo ""
echo "Next steps:"
echo "  1. Check results: ls status/*.json | wc -l"
echo "  2. Generate analysis: python3 scripts/analyze_campaign.py"
echo "  3. Review outputs: ls analysis_output/"
echo "  4. Return to paper integration (see INDEX.md)"
echo "======================================================================"
