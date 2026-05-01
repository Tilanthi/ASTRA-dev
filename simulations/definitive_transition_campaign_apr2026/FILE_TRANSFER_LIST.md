# Complete File Transfer List
# Definitive 2D Fragmentation Transition Campaign

## Essential Files (REQUIRED)

Copy these files to your remote computer to run the campaign:

### 1. Quick Start Script
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/quickstart_optimized.sh
```
**Purpose**: One-command execution of the entire campaign
**Usage**: `bash quickstart_optimized.sh`

### 2. Configuration Generator
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/generate_simulations_optimized.py
```
**Purpose**: Generates 648 Athena++ configuration files (128³, 5 snapshots)
**Usage**: `python3 generate_simulations_optimized.py`

### 3. Ray Execution Script
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/run_campaign_optimized.py
```
**Purpose**: Runs all 648 simulations using Ray parallel execution
**Usage**: `python3 run_campaign_optimized.py --phase all --num-workers 200`

### 4. Analysis Script
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/analyze_campaign.py
```
**Purpose**: Extracts fragmentation metrics and generates publication figures
**Usage**: `python3 analyze_campaign.py`

## Documentation Files (RECOMMENDED)

### 5. Main README (OPTIMIZED)
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/README_OPTIMIZED.md
```
**Purpose**: Complete documentation for optimized campaign
**Contains**: Specs, requirements, timeline, expected results

### 6. Disk Space Optimization Explanation
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/DISK_SPACE_OPTIMIZATION.md
```
**Purpose**: Explains why 128³ is scientifically valid
**Contains**: Optimization strategies, validation benchmarks

## Optional Files (FOR REFERENCE)

### 7. Original Specification (UNOPTIMIZED)
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/generate_simulations.py
```
**Purpose**: Original 256³ specification (NOT recommended - uses 3.2 TB)
**Note**: Only use if you have unlimited disk space

### 8. Original Run Script (UNOPTIMIZED)
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/run_campaign.py
```
**Purpose**: Original 256³ execution script
**Note**: Only use if you have unlimited disk space

### 9. Original Quick Start (UNOPTIMIZED)
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/quickstart.sh
```
**Purpose**: Original quick start script
**Note**: Use quickstart_optimized.sh instead

### 10. Original README
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/README.md
```
**Purpose**: Original README (3.2 TB specification)
**Note**: Use README_OPTIMIZED.md instead

### 11. Detailed Specification
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/definitive_transition_spec.md
```
**Purpose**: Technical specification and expected results grid

### 12. Campaign Design Document
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/DEFINITIVE_CAMPAIGN_DESIGN.md
```
**Purpose**: Scientific rationale and hypothesis testing

---

## MINIMAL TRANSFER LIST (4 files only)

If you want to transfer the absolute minimum, copy only these 4 files:

1. `quickstart_optimized.sh` - Execution script
2. `generate_simulations_optimized.py` - Config generator
3. `run_campaign_optimized.py` - Ray runner
4. `analyze_campaign.py` - Analysis script

---

## COMPLETE TRANSFER LIST (all 12 files)

Transfer all files for complete documentation:

```bash
# On your local machine, create a tarball:
cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/
tar -czf definitive_transition_campaign.tar.gz definitive_transition_campaign_apr2026/

# Transfer to remote machine:
scp definitive_transition_campaign.tar.gz user@remote:/path/to/destination/

# On remote machine, extract:
tar -xzf definitive_transition_campaign.tar.gz
cd definitive_transition_campaign_apr2026/
```

---

## FILE SIZES

| File | Size | Essential? |
|------|------|------------|
| `quickstart_optimized.sh` | 8.5 KB | ✓ Yes |
| `generate_simulations_optimized.py` | 8.4 KB | ✓ Yes |
| `run_campaign_optimized.py` | 9.2 KB | ✓ Yes |
| `analyze_campaign.py` | 13.2 KB | ✓ Yes |
| `README_OPTIMIZED.md` | 8.4 KB | Recommended |
| `DISK_SPACE_OPTIMIZATION.md` | 4.8 KB | Recommended |
| `README.md` | 7.1 KB | Optional |
| `definitive_transition_spec.md` | 5.8 KB | Optional |
| `DEFINITIVE_CAMPAIGN_DESIGN.md` | 9.9 KB | Optional |
| `generate_simulations.py` | 7.9 KB | Optional (original) |
| `run_campaign.py` | 8.5 KB | Optional (original) |
| `quickstart.sh` | 7.8 KB | Optional (original) |

**Total essential files**: 4 files, ~40 KB
**Total all files**: 12 files, ~100 KB

---

## AFTER TRANSFER

### 1. Update paths in quickstart_optimized.sh

Edit these lines on your remote machine:
```bash
ATHENA_BINARY="/path/to/your/athena/bin/athena"
SIMULATION_BASE="/path/to/simulations/definitive_transition_campaign_apr2026"
```

### 2. Make scripts executable
```bash
chmod +x quickstart_optimized.sh
chmod +x generate_simulations_optimized.py
chmod +x run_campaign_optimized.py
chmod +x analyze_campaign.py
```

### 3. Install dependencies
```bash
pip install ray h5py scipy matplotlib numpy
```

### 4. Run campaign
```bash
bash quickstart_optimized.sh
```

---

## QUICK COPY-PASTE FILE LIST

Copy these paths directly:

**ESSENTIAL (4 files):**
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/quickstart_optimized.sh
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/generate_simulations_optimized.py
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/run_campaign_optimized.py
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/analyze_campaign.py
```

**DOCUMENTATION (2 files - recommended):**
```
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/README_OPTIMIZED.md
/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/ASTRA-dev/simulations/definitive_transition_campaign_apr2026/DISK_SPACE_OPTIMIZATION.md
```
