# Transition Mapping Campaign
# Athena++ Simulations: Filament Fragmentation at f = 1.5-2.5

## Overview

This campaign maps the sharp fragmentation transition between moderate and high supercriticality in magnetized filaments. The grid spans:

- **Supercriticality (f)**: 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5 (11 values)
- **Plasma beta (β)**: 0.5, 0.7, 0.9, 1.1, 1.3, 1.5 (6 values)
- **Mach number (M)**: 1.0, 2.0, 3.0 (3 values)
- **Random seeds**: 42, 137 (2 values)

**Total: 240 simulations**

## Key Features

- **Resolution**: 256³ cells (64³ meshblocks, 4×4×4 decomposition)
- **Domain**: 16λ_J × 4λ_J × 4λ_J (periodic)
- **Runtime**: 4.0 t_J with 41 snapshots (every 0.1 t_J)
- **Physics**: HLLD solver, FFT self-gravity, isothermal EOS
- **Outputs**: VTK snapshots + tab files for analysis

## Expected Results

Based on previous moderate supercriticality campaign:
- **f = 1.5, β = 0.9**: Vigorous fragmentation (C ≈ 2.5-2.9), λ/W ≈ 2.0
- **f = 2.0, β = 0.5**: Suppressed (C < 1.1)
- **Goal**: Map the exact transition boundary in (f, β) space

## Computational Cost

- **Per simulation**: ~2-4 hours on 64 cores
- **Total wall time**: ~24-48 hours on 200 cores
- **Core-hours**: ~46,000 (23k core-hours)

## Quick Start

### 1. Update Paths

Edit `quickstart.sh` and set:
```bash
ATHENA_BINARY="/path/to/your/athena/bin/athena"
SIMULATION_BASE="/path/to/simulations/transition_mapping_campaign_apr2026"
```

### 2. Generate Configurations

```bash
python3 generate_simulations.py
```

This creates:
- `simulation_manifest.json` - Complete parameter list
- 240 directories with `athena_input.dat` files

### 3. Run Campaign (with Ray)

```bash
python3 run_campaign.py --num-workers 200
```

Or use the quickstart script:
```bash
bash quickstart.sh
```

### 4. Analyze Results

```bash
python3 analyze_campaign.py
```

This outputs:
- `transition_mapping_analysis.json` - All fragmentation metrics
- Summary statistics and transition boundary

## Directory Structure

```
transition_mapping_campaign_apr2026/
├── README.md
├── quickstart.sh
├── generate_simulations.py
├── run_campaign.py
├── analyze_campaign.py
├── simulation_manifest.json
├── athena_input_template.dat
└── MSC_f1.5_b0.5_M1.0_s42/
    ├── athena_input.dat
    ├── block*.0.00.00.tab
    ├── ...
    └── block*.0.04.00.tab
```

## Physics Parameters (Code Units)

- Sound speed: c_s = 1
- Gravitational constant: 4πG = 2.636 (for ρ_c = 10)
- Critical line mass: μ_crit = 2/G = 9.534
- Filament width: W = 1
- Jeans length: λ_J = 2π (for ρ_c = 1)

Parameter relationships:
```
f = μ_line / μ_crit
β = 2c_s²/B²
μ_line = √(2π) ρ_c W²
```

For a Gaussian filament with W = 1:
```
ρ_c = 2f / (√(2π) G_code)
B0 = c_s √(2ρ_c/β)
```

## Troubleshooting

### Athena++ not found
- Update `ATHENA_BINARY` in scripts
- Ensure binary is compiled with FFT gravity and MHD

### Ray cluster issues
- Check `ray status` for cluster health
- Reduce `--num-workers` if memory issues

### Analysis fails
- Check that tab files exist in simulation directories
- Verify HDF5 library compatibility

## Contact

For questions about this campaign, see the main ASTRA project documentation.

---
*Generated for ASTRA filament spacing paper - April 2026*
