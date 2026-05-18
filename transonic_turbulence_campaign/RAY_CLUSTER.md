# Ray Cluster Setup for Transonic Turbulence Campaign

## Ray Cluster Overview

This guide is specifically tailored for the **220 CPU external Ray cluster** available for this campaign.

## Cluster Specifications

- **Total CPUs**: 220 (distributed across nodes)
- **Architecture**: [CPU architecture - e.g., x86_64, Intel Xeon]
- **RAM per core**: [Memory per core - e.g., 4-8 GB]
- **Interconnect**: [Network type - e.g., InfiniBand, Ethernet]
- **Scheduler**: [Job scheduler - e.g., SLURM, PBS]
- **Storage**: [File system - e.g., /scratch, /home]

## Initial Cluster Access

### 1. SSH Connection
```bash
ssh username@ray-cluster.example.com
```

### 2. Environment Modules
```bash
# List available modules
module avail

# Load necessary modules for Athena++
module load gcc/9.0.0
module load openmpi/4.0.3
module load hdf5/1.12.0_mpich
module load cmake/3.20.0
module load python/3.8.5
module list  # Verify loaded modules
```

### 3. Storage Allocation
```bash
# Request scratch space for simulation outputs
# Contact cluster admin for allocation

# Recommended directory structure:
SCRATCH=/scratch/username/turbulence_campaign
mkdir -p $SCRATCH/{inputs,outputs,checkpoints}
```

## Job Scheduling

### SLURM Job Script Template

Create `submit_slurm.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=turb_fil_512
#SBATCH --nodes=2                    # Adjust based on CPU needs
#SBATCH --ntasks=220                 # Total CPUs
#SBATCH --ntasks-per-node=110      # CPUs per node
#SBATCH --cpus-per-task=1
#SBATCH --time=48:00:00             # Walltime (48 hours)
#SBATCH --partition=compute          # Partition name
#SBATCH --output=turb_%j.out
#SBATCH --error=turb_%j.err

# Load modules
module purge
module load gcc/9.0.0
module load openmpi/4.0.3
module load hdf5/1.12.0_mpich
module load python/3.8.5

# Set environment variables
export OMP_NUM_THREADS=1
export I_MPI_FABRICS=shm
export I_MPI_FALLBACK=disable

# Create work directory
WORKDIR=/scratch/username/turbulence_${SLURM_JOB_ID}
mkdir -p $WORKDIR
cd $WORKDIR

# Copy input files
cp /path/to/transonic_turbulence_campaign/inputs/* .

# Run Athena++
echo "Starting Athena++ simulation at $(date)"
mpirun -np 220 /path/to/athena/bin/athena -i athena.input

# Post-processing
echo "Simulation completed at $(date)"
python /path/to/transonic_turbulence_campaign/scripts/extract_lambda_W.py *.h5

# Copy results back
cp *.h5 *.log /path/to/transonic_turbulence_campaign/results/

echo "Job finished"
```

### Submit Job
```bash
sbatch submit_slurm.sh
```

### Monitor Job
```bash
squeue -u username          # Your jobs only
squeue -j <JOBID>           # Specific job details
scancel <JOBID>             # Cancel job if needed
```

## Optimization for Ray Cluster

### 1. CPU Affinity
```python
# In Python monitoring script, use:
import os
os.environ['OMP_PROC_BIND'] = 'close'
os.environ['OMP_PLACES'] = 'threads'
```

### 2. I/O Optimization
```bash
# Use local SSD for temporary files during simulation
export TMPDIR=/tmp/${SLURM_JOB_ID}
mkdir -p $TMPDIR

# Configure Athena++ to use local temp
# In athena.input:
<output>
restartfile = /tmp/${SLURM_JOB_ID}/restart
</output>
```

### 3. Memory Mapping
```bash
# Preload HDF5 files for faster analysis
python -c "import h5py; f = h5py.File('file.h5', 'r')"
```

## Parallel Execution Strategy

### MPI Process Layout
For 512³ simulation on 220 CPUs:

```
Recommended decomposition:
- X-direction: 220 ranks (full length of filament)
- Y-direction: 1 rank
- Z-direction: 1 rank

Alternative (if domain is larger):
- Use Cartesian topology 2D decomposition
mpirun -np 220 --map-by ppr:2 -n 1 \
        --map-by ppr:4 -n 55 \
        /path/to/athena -i athena.input
```

### Load Balancing
```bash
# Monitor CPU usage during simulation
watch -n 10 'ps aux | grep athena | head -20'

# If severe imbalance occurs, restart with different decomposition
# In athena.input:
<par>
# Try different meshblock configurations
meshblock = [32, 4, 4, 1, 1, 1, 0]
# Or
meshblock = [16, 8, 4, 1, 1, 1, 0]
</par>
```

## Monitoring and Debugging

### Real-Time Monitoring Script
```bash
#!/bin/bash
# monitor_job.sh
JOBID=$1

while squeue -j $JOBID > /dev/null 2>&1; do
    # Check latest output
    tail -n 20 turb_${JOBID}.out
    
    # Monitor Mach number from checkpoint
    python monitor_turbulence.py turb_${JOBID}/turb.0.0200.h5
    
    sleep 300  # Check every 5 minutes
done

echo "Job $JOBID completed"
```

### Common Ray Cluster Issues

#### Issue 1: "Out of memory" errors
```bash
# Solution 1: Reduce number of MPI ranks per node
# In submit script:
#SBATCH --ntasks-per-node=55  # Down from 110

# Solution 2: Increase memory in athena.input
# This reduces memory for caching
<mesh>
nx3 = 32  # Smaller meshblock size
</mesh>
```

#### Issue 2: Slow I/O on parallel filesystem
```bash
# Use local scratch for checkpoints
<output>
file_dir = /tmp/${SLURM_JOB_ID}/outputs
</output>

# Copy to final location after completion
# In job script:
cp -r /tmp/${SLURM_JOB_ID}/outputs /scratch/username/
```

#### Issue 3: Jobs killed unexpectedly
```bash
# Check job logs for specific error
grep -i "error\|kill\|fail" turb_*.err

# Common causes:
# 1. Walltime exceeded -> Request more time
# 2. Memory limit -> Reduce ntasks or increase memory
# 3. License issues -> Contact sysadmin
```

## Batch Processing Multiple Simulations

### Submission Script for Campaign
```bash
#!/bin/bash
# submit_campaign.sh

CONFIG_DIR=/path/to/transonic_turbulence_campaign/inputs/turb_full_campaign
RESULTS_DIR=/scratch/username/turbulence_campaign/results

# Loop over parameter files
for config in $CONFIG_DIR/*/athena.input; do
    # Extract parameter name
    RUN_NAME=$(basename $(dirname $config))
    
    # Create job script
    cat > submit_${RUN_NAME}.sh << EOF
#!/bin/bash
#SBATCH --job-name=${RUN_NAME}
#SBATCH --nodes=1
#SBATCH --ntasks=110
#SBATCH --time=24:00:00
#SBATCH --output=${RUN_NAME}_%j.out
#SBATCH --error=${RUN_NAME}_%j.err

module load gcc/9.0.0 openmpi/4.0.3 hdf5/1.12.0_mpich

mpirun -np 110 /path/to/athena/bin/athena -i $config
EOF
    
    # Submit job
    sbatch submit_${RUN_NAME}.sh
    
    # Avoid queue flooding
    sleep 60
done
```

### Dependency Management
```bash
#!/bin/bash
# submit_with_dependencies.sh

# Run 108 simulations with dependency tracking
# This script uses SLURM job arrays with dependencies

# Phase 1: Run low-β cases first (faster)
sbatch --array=0-35 submit_phase1.sh

# Phase 2: Run high-β cases after Phase 1 completes
sbatch --dependency=afterok:$(squeue -h -o %i | tr '\n' ',') \
       submit_phase2.sh
```

## Performance Benchmarks

### Expected Performance (512³ resolution)

| Metric | Expected Value | Notes |
|--------|----------------|-------|
| Setup time | 5 min | Job initialization, I/O |
| Timestep duration | 2-5 sec | Per dt ~ 10⁻⁴ t_J |
| Time to 1 t_J | ~6-8 hrs | Per simulation |
| Time to fragmentation | ~48 hrs | 4-6 t_J |
| Total for campaign | 2-3 weeks | 108 simulations |

### Optimizing Walltime Usage

1. **Parallel I/O**:
```python
# In athena.input, enable parallel HDF5:
<hdf5>
collective = true   # Enable collective I/O
compression = 1      # Reduce file size
</hdf5>
```

2. **Adaptive Timestepping**:
```python
# In athena.input:
<time>
# Allow larger dt for smooth phases
cfl_number = 0.4       # Can increase to 0.5 for better performance
</time>
```

3. **Selective Output**:
```python
# Only output critical time periods
# In athena.input:
<output>
dt_dir_samples = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]  # Sparse output
# But ensure fragmentation onset is captured
variable_dt = true
</output>
```

## Data Management

### Storage Strategy
```bash
# 1. Work directory: /scratch/username/turbulence_campaign
# 2. Archive: /archive/username/turbulence_hdf5/
# 3. Analysis: ~/transonic_turbulence_campaign/results/

# Compression script for completed runs
python compress_outputs.py /scratch/username/turbulence_campaign/run_*/
```

### Data Transfer
```bash
# From Ray cluster to local machine
rsync -avz username@ray-cluster:/scratch/username/turbulence_campaign/ \
            ~/local_turbulence_data/

# Using globus (if available)
# Configure endpoint on cluster and local machine
```

## Troubleshooting Cluster Issues

### Issue: Jobs stuck in queue
```bash
# Check partition status
sinfo -p compute

# Check why jobs aren't starting
squeue -p compute

# Solution: Adjust job requirements
# In submit script:
#SBATCH --partition=debug     # Try different partition
#SBATCH --qos=short          # Use short queue for testing
```

### Issue: Inconsistent performance across nodes
```bash
# Check node-specific performance
for node in $(sinfo -N -h | grep idle | awk '{print $1}'); do
    echo "Testing node: $node"
    srun --nodelist=$node hostname
done

# Solution: Specify node list if needed
#SBATCH --nodelist=node[001-002]  # Specific nodes
```

## Contact and Support

### Cluster Administration
- **Sysadmin email**: [Admin email]
- **Help desk**: [Help desk info]
- **Documentation**: [Internal wiki]

### Working Hours
- **Prime time**: 8 AM - 8 PM (Mon-Fri)
- **Non-prime time**: Weekends and evenings
- **Recommended**: Submit long jobs during non-prime time

## Emergency Procedures

### If Simulation Crashes
```bash
# 1. Check for restart files
ls -lt /tmp/${SLURM_JOB_ID}/restart*

# 2. If restart exists, modify athena.input:
<job>
job_type = restart
</job>

# 3. Resubmit with extended walltime
#SBATCH --time=72:00:00
```

### If Cluster Maintenance Occurs
```bash
# 1. Check cluster status
sinfo -R

# 2. Cancel jobs during maintenance
scancel $(squeue -u username -h -o %i)

# 3. Resubmit after maintenance
# All input files are preserved
```

## Appendices

### A. Complete Job Script Example
See `submit_slurm_full.sh` for a production-ready script.

### B. Performance Monitoring
See `monitor_cluster_performance.sh` for real-time monitoring tools.

### C. Batch Automation
See `automate_campaign.sh` for end-to-end campaign automation.

---
**Last updated**: 2026-05-18
**Tested on**: Ray cluster, 220 CPUs, SLURM scheduler
**Contact**: username@institute.edu
