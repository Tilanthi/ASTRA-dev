#!/bin/bash
# -----------------------------------------------------------------------------
# Athena++ MHD Simulation Runner for Ray Cluster
# -----------------------------------------------------------------------------
# This script submits and manages Athena++ MHD simulations on a Ray cluster.
# It handles job submission, monitoring, and output management.
#
# Usage:
#   ./run_athena_simulation.sh --config <config.json> --output <output_dir>
#
# -----------------------------------------------------------------------------

set -e

# Parse arguments
CONFIG_FILE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$CONFIG_FILE" ]]; then
    echo "Error: --config argument is required"
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    exit 1
fi

if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="./simulation_output"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Extract simulation parameters from config
LINE_MASS=$(python3 -c "import json; f=open('$CONFIG_FILE'); d=json.load(f); print(d.get('line_mass', 1.5))")
PLASMA_BETA=$(python3 -c "import json; f=open('$CONFIG_FILE'); d=json.load(f); print(d.get('plasma_beta', 1.0))")
MACH_NUMBER=$(python3 -c "import json; f=open('$CONFIG_FILE'); d=json.load(f); print(d.get('mach_number', 1.0))")
RANDOM_SEED=$(python3 -c "import json; f=open('$CONFIG_FILE'); d=json.load(f); print(d.get('random_seed', 42))")

# Set up Athena++ executable path
ATHENA_EXEC="${ATHENA_EXEC_PATH:-/path/to/athena++/bin/athena}"

# Check if executable exists
if [[ ! -f "$ATHENA_EXEC" ]]; then
    echo "Error: Athena++ executable not found at $ATHENA_EXEC"
    echo "Set ATHENA_EXEC_PATH environment variable to point to your Athena++ binary"
    exit 1
fi

# Create simulation input file
cat > "$OUTPUT_DIR/athena_input.txt" <<EOF
# -----------------------------------------------------------------------------
# Athena++ Input File for Filament Fragmentation Simulation
# -----------------------------------------------------------------------------

<job>
problem_id   = filament_${LINE_MASS}_${PLASMA_BETA}_${MACH_NUMBER}_${RANDOM_SEED}
$${outdir}   = $OUTPUT_DIR

<time>
tlim         = 10.0
dt           = 1e-4
n Cycle      = 100000

<mesh>
nx1          = 128
nx2          = 128
nx3          = 128
x1min        = 0.0
x1max        = 8.0
x2min        = 0.0
x2max        = 2.0
x3min        = 0.0
x3max        = 2.0
boundary     = periodic

<hydro>
iso_sound_speed = 1.0
gamma           = 1.0

<problem>
line_mass      = $LINE_MASS
plasma_beta    = $PLASMA_BETA
mach_number    = $MACH_NUMBER
random_seed    = $RANDOM_SEED
field_geometry = longitudinal

<output>
file_type      = hdf5
variable       = prim
dt             = 0.05
output_dt      = 0.1
EOF

# Run Athena++ simulation
echo "Starting Athena++ simulation..."
echo "  Line mass: $LINE_MASS"
echo "  Plasma beta: $PLASMA_BETA"
echo "  Mach number: $MACH_NUMBER"
echo "  Random seed: $RANDOM_SEED"
echo "  Output directory: $OUTPUT_DIR"

$ATHENA_EXEC -i "$OUTPUT_DIR/athena_input.txt" > "$OUTPUT_DIR/athena.log" 2>&1

# Check if simulation completed successfully
if [[ $? -eq 0 ]]; then
    echo "Simulation completed successfully"
else
    echo "Error: Simulation failed. Check $OUTPUT_DIR/athena.log for details"
    exit 1
fi

# Create simulation parameters file
cat > "$OUTPUT_DIR/simulation_params.json" <<EOF
{
  "line_mass": $LINE_MASS,
  "plasma_beta": $PLASMA_BETA,
  "mach_number": $MACH_NUMBER,
  "random_seed": $RANDOM_SEED,
  "resolution": [128, 128, 128],
  "domain_dimensions": [8.0, 2.0, 2.0],
  "status": "completed"
}
EOF

echo "Simulation results written to $OUTPUT_DIR"
