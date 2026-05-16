# Quick Start Guide: Critical Regime Filament Spacing Campaign

## Overview

This campaign runs MHD simulations in the **moderate supercriticality regime (f ≈ 2-3)** that is directly relevant to HGBS filaments. The goal is to measure λ/W (fragmentation spacing / filament width) and test whether magnetic tension or hierarchical fragmentation explains the observed λ/W ≈ 2.11.

## What This Campaign Does

- **126 base simulations** covering:
  - f ∈ {1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0}
  - β ∈ {0.3, 0.5, 0.7, 1.0, 1.5, 2.0}
  - M ∈ {1.0, 2.0, 3.0}
  - 2 seeds per point = 504 simulations total
- Measures λ/W for each simulation
- Direct comparison with HGBS observation (λ/W = 2.11)
- Tests magnetic tension and hierarchical fragmentation predictions

## Prerequisites

### Software Requirements

```bash
# Python 3.8+
pip install numpy pandas scipy matplotlib h5py pyvista ray

# Athena++ (must be compiled with FFT gravity)
# See: https://github.com/PrincetonUniversity/athena
```

### Hardware Requirements

- **200 cores** recommended (32 cores per simulation × 6 parallel)
- **8 GB RAM per 32-core slot** (512³ resolution)
- **2 GB disk per simulation** (~1 TB total)
- **~2 weeks** wallclock for full campaign

### System Configuration

For Slurm-based clusters, ensure your job script allows:
- 10+ hour walltime per simulation
- 32 cores per simulation
- FFT Poisson solver support

## Step-by-Step Instructions

### 1. Extract the Package

```bash
tar -xzf filament_spacing_critical_regime.tar.gz
cd filament_spacing_critical_regime
```

### 2. Compile Athena++ (if not already compiled)

```bash
# Get Athena++ (or use your existing installation)
git clone https://github.com/PrincetonUniversity/athena.git
cd athena

# Configure with FFT gravity and self-gravity
./configure --with-gravity --with-fft --with-hdf5

# Compile (use 8-16 cores for speed)
make -j 16

# Verify compilation
./bin/athena --help
```

**Important**: Set ATHENA_PATH to point to your compiled binary:
```bash
export ATHENA_PATH=/path/to/athena/bin/athena
```

### 3. Test Run (10 Simulations)

Before launching the full campaign, run a small test:

```bash
python3 run_campaign.py \
    --athena $ATHENA_PATH \
    --cores 64 \
    --work-dir ./test_simulations \
    --test
```

Expected output:
- 10 simulations completed
- Results in `test_simulations/results_final.csv`
- Takes ~4 hours on 64 cores

### 4. Full Campaign

When test run succeeds, launch the full campaign:

```bash
python3 run_campaign.py \
    --athena $ATHENA_PATH \
    --cores 200 \
    --work-dir ./simulations
```

Expected timeline:
- **~2 weeks** on 200 cores
- Progress printed every 32 simulations
- Intermediate results saved to `results_partial.csv`

### 5. Monitor Progress

Watch the simulation directories:
```bash
watch -n 60 'ls -1 simulations | wc -l'
```

Check completed results:
```bash
tail -f simulations/results_partial.csv
```

### 6. Analyze Results

After campaign completes (or periodically during execution):

```bash
python3 analyze_results.py simulations/ results_final.csv comparison.pdf
```

This generates:
- `results_summary.csv`: Table of all λ/W measurements
- `comparison.pdf`: Three-panel comparison with HGBS data

### 7. Interpret Results

The analysis will show one of three outcomes:

**Scenario 1: Magnetic tension confirmed**
- λ/W ≈ 2.0-2.3 for f ≈ 2-3, β ≈ 0.5-1.5
- Strong support for magnetic tension mechanism
- Explains observed universal λ/W ≈ 2.1

**Scenario 2: Hierarchical fragmentation supported**
- λ/W ≈ 3-4 regardless of β
- Magnetic tension has weak effect in supercritical regime
- Suggests fiber-level physics is dominant

**Scenario 3: New physics required**
- λ/W shows unexpected behavior
- Indicates missing physics (ambipolar diffusion, non-isothermal EOS)
- Requires theoretical re-examination

## Troubleshooting

### Simulations Timeout

If simulations consistently timeout:
1. Reduce resolution: Change `512³` to `256³` in template
2. Reduce domain length: Change `32H` to `24H`
3. Run with more cores: Increase `--cores` argument

### Memory Errors

If you encounter memory errors:
1. Reduce number of parallel simulations
2. Use larger-memory nodes
3. Check FFT Poisson solver memory requirements

### Athena++ Configuration Issues

Common Athena++ problems:

1. **FFT solver not found**: Ensure `--with-fft` in configure
2. **Gravity not working**: Check `--with-gravity` flag
3. **HDF5 output errors**: Install HDF5 libraries: `conda install h5py`

### Ray Initialization Errors

If Ray fails to initialize:
```bash
# Check port availability
ray stop  # Clean up previous Ray instance
# Try again
python3 run_campaign.py ...
```

## Expected Results

### File Structure After Completion

```
simulations/
├── f2.00_beta0.50_M2.0_seed1/
│   ├── athena_input.in
│   ├── athena.log
│   ├── *.vtk (output files)
│   ├── lambda_W_result.txt
│   └── summary.json
├── f2.00_beta0.50_M2.0_seed2/
│   └── ...
├── ...
├── results_final.csv
└── comparison.pdf
```

### Key Output Files

- **`results_final.csv`**: Table of all (f, β, M, seed, λ/W) measurements
- **`comparison.pdf`**: Visual comparison with HGBS observation
- **Individual `lambda_W_result.txt`**: One-line file with λ/W per simulation

## Integration with MNRAS Paper

After campaign completion, update the paper with:

1. **New results section**: Report λ/W vs (f, β, M) trends
2. **Updated Figure 2**: Replace regime diagram with λ/W measurements
3. **Revised abstract**: State that MHD simulations now cover HGBS-relevant regime
4. **New comparison table**: Direct λ/W comparison with predictions

## Contact

For questions or issues, contact:
- Glenn J. White (The Open University / RAL Space)
- ASTRA project: https://github.com/Tilanthi/ASTRA-dev

## References

- Athena++ code: Stone et al. 2020, ApJS, 249, 4
- HGBS observations: Arzoumanian et al. 2011, A&A, 529, L6
- Magnetic tension theory: Nakamura et al. 1993, ApJ, 407, L51
