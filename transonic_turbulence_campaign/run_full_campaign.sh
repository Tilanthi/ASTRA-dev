#!/bin/bash
# run_full_campaign.sh
# Phase 2: Full parameter space exploration (108 simulations)

set -e

echo "=== Transonic Turbulence Campaign: Phase 2 Full Campaign ==="
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

# Check resolution test results
RES_TEST_RESULTS="${TURBULENCE_CAMPAIGN_ROOT}/results/resolution_test/phase1_summary.txt"
if [ ! -f "$RES_TEST_RESULTS" ]; then
    echo "WARNING: Resolution test results not found at $RES_TEST_RESULTS"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Run ./run_resolution_test.sh first."
        exit 1
    fi
fi

# Determine optimal resolution from Phase 1
OPTIMAL_RESOLUTION=512  # Default
if [ -f "$RES_TEST_RESULTS" ]; then
    echo "Analyzing Phase 1 results..."
    # Parse Phase 1 results for M_turb >= 1
    if grep -q "512.*M_turb.*>= 1.0" "$RES_TEST_RESULTS"; then
        OPTIMAL_RESOLUTION=512
        echo "✓ Phase 1 indicates 512³ achieves M_turb >= 1"
    else
        echo "⚠ Phase 1 results inconclusive. Defaulting to 512³."
    fi
fi

echo "Optimal resolution: ${OPTIMAL_RESOLUTION}³"
echo ""

# Parameter space
LINE_MASS_VALUES=(1.2 1.5 2.0)
PLASMA_BETA_VALUES=(0.5 1.0 2.0)
FIELD_ANGLES=(0 90)
DRIVE_MACH_VALUES=(1.0 2.0 3.0)
RANDOM_SEEDS=(0 1)

# Calculate total
TOTAL_SIMS=$((${#LINE_MASS_VALUES[@]} * ${#PLASMA_BETA_VALUES[@]} * \
              ${#FIELD_ANGLES[@]} * ${#DRIVE_MACH_VALUES[@]} * ${#RANDOM_SEEDS[@]}))

echo "Full Parameter Space:"
echo "  Line-mass (f): ${LINE_MASS_VALUES[@]}"
echo "  Plasma beta (β): ${PLASMA_BETA_VALUES[@]}"
echo "  Field angles (θ): ${FIELD_ANGLES[@]}°"
echo "  Driving Mach (M): ${DRIVE_MACH_VALUES[@]}"
echo "  Random seeds: ${RANDOM_SEEDS[@]}"
echo ""
echo "Total simulations: $TOTAL_SIMS"
echo ""

# Output directory
OUTPUT_BASE="${TURBULENCE_CAMPAIGN_ROOT}/results/full_campaign"
mkdir -p "$OUTPUT_BASE"

# Domain for Phase 2
DOMAIN="8x2x2"
if [[ "$OPTIMAL_RESOLUTION" == "512" ]]; then
    NX1=2048
    NX2=512
    NX3=512
elif [[ "$OPTIMAL_RESOLUTION" == "384" ]]; then
    NX1=1536
    NX2=384
    NX3=384
else
    NX1=1024
    NX2=256
    NX3=256
fi

echo "Grid dimensions: ${NX1}×${NX2}×${NX3} (${OPTIMAL_RESOLUTION}³ effective)"
echo ""

# Simulation counter
SIM_COUNT=0

# Loop over parameter space
for F in "${LINE_MASS_VALUES[@]}"; do
    for BETA in "${PLASMA_BETA_VALUES[@]}"; do
        for THETA in "${FIELD_ANGLES[@]}"; do
            for MACH in "${DRIVE_MACH_VALUES[@]}"; do
                for SEED in "${RANDOM_SEEDS[@]}"; do

                    SIM_COUNT=$((SIM_COUNT + 1))
                    RUN_ID=$(printf "f%04.1f_beta%04.1f_theta%03d_M%04.1f_seed%d" \
                              $F $BETA $THETA $MACH $SEED)

                    RUN_DIR="$OUTPUT_BASE/$RUN_ID"
                    mkdir -p "$RUN_DIR"

                    echo "========================================"
                    echo "Simulation $SIM_COUNT/$TOTAL_SIMS"
                    echo "Run ID: $RUN_ID"
                    echo "Parameters: f=$F, β=$BETA, θ=$THETA°, M=$MACH, seed=$SEED"
                    echo "========================================"

                    # Calculate B0 from plasma beta
                    B0=$(python3 -c "import math; print(f'{math.sqrt(2.0/$BETA):.8f}')")

                    # Generate input file
                    INPUT_FILE="$RUN_DIR/athena.input"
                    cat > "$INPUT_FILE" << EOF
# Transonic Turbulence Campaign: Phase 2 Full Campaign
# Run ID: $RUN_ID
# Generated: $(date)

<job>
job_id      = $SIM_COUNT
problem_id  = 1
</job>

<time>
tlim        = 6.0
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
# Field strength from plasma beta
B0 = $B0
beta = $BETA
theta = $THETA

# Divergence cleaning
divb_clean = powell
divb_tol = 1e-10
divb_dtol = 1e-10
</magnetic>

<problem>
# Filament parameters
f = $F

# Turbulent driving
driving_scale = $MACH
driving_corrlength = 2.0
driving_auto = true
driving_decayscale = 0.1

# Random seed
seed = $SEED
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
dt_dir_samples = 0.05
variable_dt = true
summation = -1
</output>

<par>
nproc = $MPI_NUM_PROCS
</par>
EOF

                    # Create SLURM submission script
                    SLURM_FILE="$RUN_DIR/submit.sh"
                    cat > "$SLURM_FILE" << EOF
#!/bin/bash
#SBATCH --job-name=$RUN_ID
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

echo "Starting $RUN_ID at \$(date)"
echo ""

mpirun -np $MPI_NUM_PROCS $ATHENA_BIN/athena -i $INPUT_FILE

echo ""
echo "Simulation completed at \$(date)"

# Post-processing
python $TURBULENCE_SCRIPTS/monitor_turbulence.py $RUN_DIR
EOF

                    chmod +x "$SLURM_FILE"

                    echo "✓ Input and SLURM scripts created"

                    # Batch submission mode
                    if [ "$SIM_COUNT" -eq 1 ]; then
                        echo ""
                        read -p "Submit all $TOTAL_SIMS jobs to SLURM queue? [y/N] " -n 1 -r
                        echo
                        SUBMIT_ALL=$REPLY
                    fi

                    if [[ $SUBMIT_ALL =~ ^[Yy]$ ]]; then
                        sbatch "$SLURM_FILE"
                        echo "✓ Job submitted ($SIM_COUNT/$TOTAL_SIMS)"

                        # Brief pause to avoid queue flooding
                        sleep 1
                    else
                        echo "  (Skipped submission. Submit manually: sbatch $SLURM_FILE)"
                    fi

                    echo ""

                done
            done
        done
    done
done

echo "========================================"
echo "Phase 2 Campaign Setup Complete"
echo "========================================"
echo ""
echo "Total configurations: $TOTAL_SIMS"
echo "Output directory: $OUTPUT_BASE"
echo ""
echo "Monitor queue: squeue -u \$USER"
echo ""
echo "After completion, run analysis:"
echo "  python $TURBULENCE_SCRIPTS/analyze_campaign.py $OUTPUT_BASE"
echo ""
