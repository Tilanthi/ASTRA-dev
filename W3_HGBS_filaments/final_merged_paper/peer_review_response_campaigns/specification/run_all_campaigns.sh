#!/bin/bash
#
# Master Runner Script: All Peer Review Response Campaigns
# =========================================================
#
# Executes campaigns C8-C13 on 200 CPU ray cluster
#
# Usage:
#   bash run_all_campaigns.sh
#
# Or run individual campaigns:
#   bash run_all_campaigns.sh C8  # Run only Campaign 8
#   bash run_all_campaigns.sh C8 C9  # Run Campaigns 8 and 9
#

# Configuration
RAY_CPUS=200
CONDA_ENV="astra"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Campaigns (in priority order)
CAMPAIGNS=(
    "C8:Mixed_Geometry:175"
    "C9:Staged_Fragmentation:240"
    "C10:L3_Convergence:48"
    "C11:Temporal_Evolution:60"
    "C12:Refined_DTC:300"
    "C13:Beta_Validation:0"
)

# Parse command line arguments
if [ $# -gt 0 ]; then
    # Run only specified campaigns
    REQUESTED=("$@")
else
    # Run all campaigns
    REQUESTED=()
    for entry in "${CAMPAIGNS[@]}"; do
        IFS=':' read -r campaign_id _ _ <<< "$entry"
        REQUESTED+=("$campaign_id")
    done
fi

# Load modules
echo "Loading modules..."
module load astra/athena++
module load ray

# Activate conda environment
echo "Activating conda environment: $CONDA_ENV"
conda activate $CONDA_ENV

# Start execution
echo "="
echo "MASTER RUNNER: Peer Review Response Campaigns"
echo "="
echo
echo "Requested campaigns: ${REQUESTED[@]}"
echo "CPUs per campaign: $RAY_CPUS"
echo

# Track total runtime
START_TIME=$(date +%s)

# Run each requested campaign
for campaign_id in "${REQUESTED[@]}"; do
    # Find campaign in list
    campaign_info=""
    for entry in "${CAMPAIGNS[@]}"; do
        IFS=':' read -r id name sims <<< "$entry"
        if [ "$id" == "$campaign_id" ]; then
            campaign_info="$entry"
            break
        fi
    done

    if [ -z "$campaign_info" ]; then
        echo "ERROR: Unknown campaign $campaign_id"
        continue
    fi

    IFS=':' read -r campaign_name campaign_n_sims <<< "$campaign_info"
    campaign_name=$(echo "$campaign_name" | cut -d':' -f2)
    campaign_n_sims=$(echo "$campaign_info" | cut -d':' -f3)

    echo "="
    echo "RUNNING CAMPAIGN $campaign_id: $campaign_name"
    echo "="
    echo "Simulations: $campaign_n_sims"
    echo

    # Check if campaign directory exists
    campaign_dir="$SCRIPT_DIR/C${campaign_id:1}_${campaign_name}"
    if [ ! -d "$campaign_dir" ]; then
        echo "ERROR: Campaign directory not found: $campaign_dir"
        continue
    fi

    cd "$campaign_dir" || continue

    # Check if submission script exists
    if [ -f "submit_to_ray.sh" ]; then
        echo "Submitting to ray cluster..."
        bash submit_to_ray.sh

        # Wait for completion (optional)
        # sleep 60  # Wait 60 seconds before next campaign

    elif [ -f "run_campaign_${campaign_id}.py" ]; then
        echo "Running Python script directly..."
        python -m ray.execute --num-cpus $RAY_CPUS "run_campaign_${campaign_id}.py"

    else
        echo "ERROR: No submission script found for $campaign_id"
    fi

    echo
    echo "Campaign $campaign_id completed"
    echo

    cd "$SCRIPT_DIR"
done

# Calculate total runtime
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))

echo "="
echo "ALL CAMPAIGNS COMPLETED"
echo "="
echo "Total runtime: ${HOURS}h ${MINUTES}m"
echo

# Generate summary
echo "GENERATING SUMMARY..."
echo
echo "Campaign Summary:"
echo "-----------------"
for entry in "${CAMPAIGNS[@]}"; do
    IFS=':' read -r campaign_id campaign_name campaign_n_sims <<< "$entry"
    status="PENDING"
    campaign_dir="$SCRIPT_DIR/C${campaign_id:1}_${campaign_name}"

    if [ -d "$campaign_dir" ]; then
        if [ -f "$campaign_dir/results.json" ]; then
            status="COMPLETE"
        elif [ -f "$campaign_dir/campaign_specification.json" ]; then
            status="SPECIFIED"
        fi
    fi

    echo "$campaign_id: $status ($campaign_n_sims simulations)"
done

echo
echo "Full report available in specification README.md"
