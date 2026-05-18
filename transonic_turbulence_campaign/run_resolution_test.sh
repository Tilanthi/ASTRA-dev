#!/bin/bash
# run_resolution_test.sh
# Phase 1: Resolution test to determine minimum resolution for M_turb >= 1

set -e

echo "=== Transonic Turbulence Campaign: Phase 1 Resolution Test ==="
echo ""

# Load environment
if [ -f "environment_setup.tmp" ]; then
    source environment_setup.tmp
else
    echo "ERROR: Environment not set up. Run ./setup_environment.sh first."
    exit 1
fi

# Check Athena++ installation
if [ ! -f "$ATHENA_BIN/athena" ]; then
    echo "ERROR: Athena++ not found at $ATHENA_BIN/athena"
    echo "Run ./build_athena.sh first."
    exit 1
fi

# Configuration
FIDUCIAL_PARAMS=(
    "256:8x2x2"
    "384:8x2x2"
    "512:8x2x2"
)

LINE_MASS=1.5
PLASMA_BETA=1.0
FIELD_ANGLE=0
DRIVE_MACH=2.0
RANDOM_SEED=42

TURBULENCE_DURATION=6.0  # t_J
OUTPUT_INTERVAL=0.05

# Output directory
OUTPUT_BASE="${TURBULENCE_CAMPAIGN_ROOT}/results/resolution_test"
mkdir -p "$OUTPUT_BASE"

# Phase 1 summary
PHASE1_SUMMARY="$OUTPUT_BASE/phase1_summary.txt"
echo "Phase 1 Resolution Test Summary" > "$PHASE1_SUMMARY"
echo "Started: $(date)" >> "$PHASE1_SUMMARY"
echo "=======================================" >> "$PHASE1_SUMMARY"
echo "" >> "$PHASE1_SUMMARY"
echo "Parameters:" >> "$PHASE1_SUMMARY"
echo "  Line-mass fraction: f = $LINE_MASS" >> "$PHASE1_SUMMARY"
echo "  Plasma beta: β = $PLASMA_BETA" >> "$PHASE1_SUMMARY"
echo "  Field angle: θ = $FIELD_ANGLE°" >> "$PHASE1_SUMMARY"
echo "  Driving Mach: M = $DRIVE_MACH" >> "$PHASE1_SUMMARY"
echo "  Random seed: $RANDOM_SEED" >> "$PHASE1_SUMMARY"
echo "" >> "$PHASE1_SUMMARY"

echo "Resolution Test Configuration:"
echo "  Parameters: f=$LINE_MASS, β=$PLASMA_BETA, θ=$FIELD_ANGLE°, M=$DRIVE_MACH"
echo "  Resolutions: 256³, 384³, 512³"
echo "  Domain: 8×2×2 λ_J (baseline)"
echo "  Duration: $TURBULENCE_DURATION t_J"
echo "  Output directory: $OUTPUT_BASE"
echo ""

# Loop over resolutions
for PARAM_PAIR in "${FIDUCIAL_PARAMS[@]}"; do
    IFS=':' read -r RESOLUTION DOMAIN <<< "$PARAM_PAIR"

    RUN_DIR="$OUTPUT_BASE/res_${RESOLUTION}"
    mkdir -p "$RUN_DIR"

    echo "========================================"
    echo "Resolution: ${RESOLUTION}³ ($DOMAIN λ_J)"
    echo "Run directory: $RUN_DIR"
    echo "========================================"

    # Calculate grid dimensions
    if [[ "$DOMAIN" == "8x2x2" ]]; then
        NX1=$((RESOLUTION * 4))
        NX2=$((RESOLUTION))
        NX3=$((RESOLUTION))
    else
        echo "ERROR: Unknown domain: $DOMAIN"
        exit 1
    fi

    echo "Grid dimensions: ${NX1}×${NX2}×${NX3}"
    echo ""

    # Generate input file
    INPUT_FILE="$RUN_DIR/athena.input"
    cat > "$INPUT_FILE" << EOF
# Transonic Turbulence Campaign: Phase 1 Resolution Test
# Resolution: ${RESOLUTION}³
# Generated: $(date)

<job>
job_id      = res${RESOLUTION}
problem_id  = 1
</job>

<time>
tlim        = $TURBULENCE_DURATION
nlim        = 10000000
dt          = 1e-4
cfl_number  = 0.3
integrator  = vl2
nsmoothing  = 2
</time>

<hydro>
iso_sound_speed = 1.0
gamma = 1.0
</hydro>

<magnetic>
# Field strength from plasma beta: B0 = cs * sqrt(2/β)
B0 = 1.41421356
beta = $PLASMA_BETA

# Field orientation (0 = longitudinal, 90 = perpendicular)
theta = $FIELD_ANGLE

# Divergence cleaning
divb_clean = powell
divb_tol = 1e-10
divb_dtol = 1e-10
</magnetic>

<problem>
# Filament parameters
f = $LINE_MASS

# Turbulent driving
driving_scale = $DRIVE_MACH
driving_corrlength = 2.0
driving_auto = true
driving_decayscale = 0.1

# Random seed
seed = $RANDOM_SEED
</problem>

<mesh>
nx1 = $NX1
nx2 = $NX2
nx3 = $NX3

# Boundary conditions
ix1_bc = periodic
ox1_bc = periodic
ix2_bc = outflow
ox2_bc = outflow
ix3_bc = outflow
ox3_bc = outflow
</mesh>

<output>
file_type = hdf5
dt_dir_samples = $OUTPUT_INTERVAL
variable_dt = true
summation = -1
</output>

<par>
nproc = $MPI_NUM_PROCS
</par>
EOF

    echo "✓ Input file created: $INPUT_FILE"

    # Create SLURM submission script
    SLURM_FILE="$RUN_DIR/submit.sh"
    cat > "$SLURM_FILE" << EOF
#!/bin/bash
#SBATCH --job-name=turb_res${RESOLUTION}
#SBATCH --nodes=2
#SBATCH --ntasks=$MPI_NUM_PROCS
#SBATCH --ntasks-per-node=$((MPI_NUM_PROCS / 2))
#SBATCH --cpus-per-task=1
#SBATCH --time=48:00:00
#SBATCH --output=$RUN_DIR/turb_%j.out
#SBATCH --error=$RUN_DIR/turb_%j.err

module load gcc/9.0.0 openmpi/4.0.3 hdf5/1.12.0_mpich

export OMP_NUM_THREADS=1
export I_MPI_FABRICS=shm

cd $RUN_DIR

echo "Starting Athena++ at \$(date)"
echo "Working directory: \$(pwd)"
echo "Input file: $INPUT_FILE"
echo ""

mpirun -np $MPI_NUM_PROCS $ATHENA_BIN/athena -i $INPUT_FILE

echo ""
echo "Simulation completed at \$(date)"

# Post-processing
echo "Running post-processing analysis..."
python $TURBULENCE_SCRIPTS/monitor_turbulence.py $RUN_DIR
EOF

    chmod +x "$SLURM_FILE"
    echo "✓ SLURM script created: $SLURM_FILE"

    # Prompt for submission
    echo ""
    read -p "Submit resolution ${RESOLUTION}³ job now? [y/N] " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        JOB_ID=$(sbatch "$SLURM_FILE" | awk '{print $4}')
        if [ -n "$JOB_ID" ]; then
            echo "✓ Job submitted: $JOB_ID"
            echo "  Monitor with: squeue -j $JOB_ID"
            echo "  View output: tail -f $RUN_DIR/turb_${JOB_ID}.out"

            # Log job
            echo "Job ID: $JOB_ID" >> "$PHASE1_SUMMARY"
            echo "  Resolution: ${RESOLUTION}³" >> "$PHASE1_SUMMARY"
            echo "  Status: RUNNING" >> "$PHASE1_SUMMARY"
            echo "" >> "$PHASE1_SUMMARY"

            # Check if user wants to wait
            read -p "Wait for completion before next resolution? [y/N] " -n 1 -r
            echo

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "Waiting for job $JOB_ID..."
                while squeue -j "$JOB_ID" &> /dev/null; do
                    sleep 60
                    echo -n "."
                done
                echo ""
                echo "Job completed."
            fi
        else
            echo "✗ Job submission failed"
        fi
    else
        echo "Skipped. To submit later: sbatch $SLURM_FILE"
    fi

    echo ""
done

echo "========================================"
echo "Phase 1 Resolution Test Initiated"
echo "========================================"
echo ""
echo "Summary file: $PHASE1_SUMMARY"
echo ""
echo "Next steps:"
echo "  1. Monitor job progress: squeue -u \$USER"
echo "  2. After completion, analyze results:"
echo "     python $TURBULENCE_SCRIPTS/analyze_resolution_test.py $OUTPUT_BASE"
echo "  3. If M_turb >= 1 achieved at 512³, proceed to Phase 2:"
echo "     ./run_full_campaign.sh"
echo ""

cat "$PHASE1_SUMMARY"
