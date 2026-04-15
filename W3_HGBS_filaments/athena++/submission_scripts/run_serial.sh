#!/bin/bash
# Simple serial execution script (for testing or local execution)

ATHENA_EXE=/path/to/athena++/bin/athena
INPUT_DIR=$(pwd)/athena_inputs
SIM_LIST=$INPUT_DIR/simulation_list.txt

echo "Running 18 simulations sequentially..."
echo

while read sim_name; do
    input_file=$INPUT_DIR/${sim_name}.athinput

    echo "========================================="
    echo "Starting: $sim_name"
    echo "Input: $input_file"
    echo "Time: $(date)"
    echo "========================================="

    mkdir -p outputs/$sim_name

    # Run Athena++ (adjust -np for your core count)
    mpirun -np 12 $ATHENA_EXE -i $input_file

    if [ $? -eq 0 ]; then
        echo "✓ Completed: $sim_name"
    else
        echo "✗ FAILED: $sim_name"
        exit 1
    fi
    echo
done < "$SIM_LIST"

echo "========================================="
echo "All simulations complete!"
echo "Time: $(date)"
echo "========================================="
