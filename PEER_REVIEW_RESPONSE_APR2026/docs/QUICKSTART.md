# Quick Start Guide
## Peer Review Response Campaign

This guide will get you running simulations in 5 minutes.

---

## PREREQUISITES CHECK

Before starting, verify you have:

```bash
# Python 3.8+
python3 --version

# MPI
mpirun --version

# Required Python packages
python3 -c "import ray, numpy, pandas, matplotlib"
```

If any are missing:
```bash
pip install ray numpy pandas matplotlib h5py scipy
```

---

## STEP 1: EXTRACT PACKAGE

```bash
tar -xzf peer_review_response_APR2026.tar.gz
cd peer_review_response_APR2026
```

---

## STEP 2: COMPILE ATHENA++

```bash
bash scripts/compile_athena.sh
```

This will:
1. Download Athena++ v21.0
2. Apply the filament spacing problem generator
3. Compile with MPI, HDF5, and FFTW3 support
4. Create the `athena_filament_pr` binary

**Expected time**: 5-10 minutes

---

## STEP 3: LAUNCH CAMPAIGN

### Option A: Interactive (Recommended)

```bash
bash run_campaign.sh
```

Follow the prompts to select which phase(s) to run.

### Option B: Direct Command

```bash
# Phase 1 only (80 sims, ~20 hours)
python3 scripts/launch_campaign.py --phase 1

# Phase 2 only (96 sims, ~24 hours)
python3 scripts/launch_campaign.py --phase 2

# Phases 1+2 (176 sims, ~44 hours)
python3 scripts/launch_campaign.py --phase 1 2

# Full campaign (320 sims, ~85 hours)
python3 scripts/launch_campaign.py --all
```

---

## STEP 4: MONITOR PROGRESS

While simulations are running:

```bash
# Check number of completed simulations
ls status/*.json | wc -l

# Check recent status files
tail -20 status/*.json | grep -E "(sim_id|status)"

# Monitor Ray dashboard (if available)
# Open http://localhost:8265 in your browser
```

---

## STEP 5: ANALYZE RESULTS

After simulations complete:

```bash
python3 scripts/analyze_campaign.py
```

This will generate:
- `analysis_output/simulation_catalog.csv`
- `analysis_output/fig1_beading_threshold.pdf`
- `analysis_output/fig2_lambda_W_comparison.pdf`
- `analysis_output/SUMMARY_REPORT.md`

---

## COMMON ISSUES

### Ray initialization error

**Problem**: `ray.init()` fails

**Solution**:
```bash
ray stop
ray start --head
```

### Out of memory

**Problem**: System runs out of RAM

**Solution**: Edit `scripts/launch_campaign.py`:
```python
MAX_CONCURRENT = 8  # Reduce from 12
```

### Athena++ compilation fails

**Problem**: Missing dependencies

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install libhdf5-dev libfftw3-dev openmpi-bin

# CentOS/RHEL
sudo yum install hdf5-devel fftw-devel openmpi
```

### Simulations timeout

**Problem**: All simulations timing out before completion

**Solution**: Edit `scripts/launch_campaign.py`:
```python
TIMEOUT_SECONDS = 21600  # Increase from 14400 (4h to 6h)
```

---

## ESTIMATED RUN TIMES

| Phase | Simulations | Wall Time (12 concurrent) |
|-------|-------------|---------------------------|
| 1     | 80          | ~20 hours                 |
| 2     | 96          | ~24 hours                 |
| 3     | 90          | ~22.5 hours               |
| 4     | 54          | ~18 hours                 |
| **Total** | **320**  | **~85 hours (3.5 days)**  |

---

## NEXT STEPS

After analysis:

1. **Review results**: Check `analysis_output/SUMMARY_REPORT.md`
2. **Validate figures**: Open PDF figures in `analysis_output/`
3. **Integration**: Copy outputs to paper directory
4. **Response**: Generate reviewer response document

For detailed documentation, see `docs/README.md`.

---

**Need help?** Check `docs/README.md` for comprehensive documentation.
