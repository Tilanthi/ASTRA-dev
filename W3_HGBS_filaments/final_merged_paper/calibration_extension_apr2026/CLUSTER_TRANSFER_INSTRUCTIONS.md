# CLUSTER TRANSFER INSTRUCTIONS

## Package Contents

This archive contains the complete CALIBRATION_EXTENSION campaign specification for execution on an external 200-CPU cluster.

**Files:**
- `README.md` — Campaign overview and scientific motivation
- `calibration_extension_spec.json` — Machine-readable parameter grid
- `run_campaign.py` — Python script to generate Athena++ input files
- `analyze_calibration.py` — Analysis script for measuring calibration factor
- `CLUSTER_TRANSFER_INSTRUCTIONS.md` — This file

## Transfer Procedure

1. **Extract archive on cluster:**
   ```bash
   tar -xzf calibration_extension_apr2026.tar.gz
   cd calibration_extension_apr2026
   ```

2. **Verify Python environment:**
   ```bash
   python3 --version  # Should be 3.7+
   pip3 install numpy scipy matplotlib  # If not already installed
   ```

3. **Generate simulation files:**
   ```bash
   python3 run_campaign.py
   ```

   This creates 36 simulation directories (calib_f*_beta*_s*), each containing:
   - `athinput.*` — Athena++ input file
   - `run.sh` — Execution script for that simulation

4. **Run simulations:**

   **Option A: Run all automatically (recommended)**
   ```bash
   bash run_all.sh
   ```

   **Option B: Run manually**
   ```bash
   cd calib_f1.5_beta0.5_s42
   bash run.sh
   cd ..
   ```

5. **Monitor progress:**
   ```bash
   # Check number of completed simulations
   ls -d */output.txt | wc -l

   # Check individual simulation status
   for dir in calib_*/; do
       if [ -f "$dir/output.txt" ]; then
           echo "$dir: COMPLETED"
       else
           echo "$dir: RUNNING or PENDING"
       fi
   done
   ```

## Expected Runtime

**Per simulation:** ~15-60 minutes (depends on f)
- f = 1.3: ~45-60 minutes (slower fragmentation)
- f = 1.5-1.6: ~30-45 minutes
- f = 1.8-2.0: ~15-30 minutes (faster fragmentation)

**Total campaign:** ~5 hours on 200 CPUs with 8 concurrent jobs

## Resource Requirements

**Per simulation:**
- MPI ranks: 24 (np=24 required for FFT gravity with 24 meshblocks)
- Memory: ~2-4 GB per simulation
- Disk: ~50 MB per simulation (outputs)

**Total campaign:**
- Peak concurrent: 8 simulations × 24 ranks = 192 MPI processes
- Total disk: ~2 GB for all outputs

## Verification Checklist

Before launching full campaign:

- [ ] Python 3.7+ available
- [ ] MPI (mpirun) installed and working
- [ ] Athena++ executable in PATH
- [ ] 200+ CPUs available
- [ ] 4+ GB free disk space
- [ ] run_campaign.py executed successfully (36 dirs created)

## Athena++ Requirements

**Version:** Athena++ 1.1 or later with:
- Self-gravity module (FFT Poisson solver)
- MHD module
- Filament problem generator

**Build flags:**
- `-mpi=yes` (required for parallel execution)
- `-fft=fftw` (required for FFT gravity)

## Data Transfer Back

After campaign completion:

1. **Package results:**
   ```bash
   cd calibration_extension_apr2026
   python3 analyze_calibration.py
   tar -czf calibration_results_$(date +%Y%m%d).tar.gz \
       calibration_results.json \
       C_f_beta_table.* \
       calib_*/output.txt \
       calib_*/stdout.txt \
       calib_*/final.out*.0*
   ```

2. **Transfer back to local machine:**
   ```bash
   # scp or rsync to your local machine
   scp calibration_results_*.tar.gz user@local:/path/to/destination/
   ```

## Troubleshooting

**Simulation fails to start:**
- Check Athena++ is in PATH: `which athena`
- Check MPI is working: `mpirun -np 2 hostname`

**Simulation hangs:**
- Reduce concurrent jobs in run_all.sh (MAX_CONCURRENT)
- Check cluster job scheduler limits

**All simulations show STABLE (no fragmentation):**
- May indicate timeout too short
- Check stdout.txt for "time=" value at end
- Consider re-running with longer timeout (edit input files: tlim = 8.0)

**FFT gravity error:**
- Ensure np=24 matches meshblock count
- Check Athena++ was compiled with FFT support

## Contact

**Campaign origin:** ASTRA-dev project
**Date:** 2026-04-28
**Purpose:** Address peer review issue on field-geometry calibration extrapolation
**Questions:** See main paper (filament_spacing_streamlined_mnras.tex) for context
