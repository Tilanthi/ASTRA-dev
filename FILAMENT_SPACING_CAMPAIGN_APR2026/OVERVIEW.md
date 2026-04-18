# Filament Spacing Campaign — April 2026

**Authors:** Glenn J. White (Open University) · Robin Dey (VBRL Holdings Inc)  
**Date:** 2026-04-18  
**Platform:** astra-climate (224 vCPU, 220 GB RAM)  
**Code:** Athena++ (isothermal MHD + FFT self-gravity)

## Overview

208-simulation parameter survey of MHD filament gravitational fragmentation, spanning a
10×10 grid in Mach number (M = 0.5–10) and plasma-β (β = 0.1–10), with focused
deep-dive near W3-like conditions and regime boundaries.

- **Batch 1**: 100 simulations, 10×10 M-β broad grid
- **Batch 2**: 108 simulations, regime boundaries + W3 conditions + high-Mach exploration
- **Resolution**: 128 × 128 × 32 (128³-class)
- **Domain**: 4 λ_J × 4 λ_J × 1 λ_J (periodic)
- **Self-gravity**: FFT solver, 4πG = 4π² → λ_J = 1.0 code unit
- **tlim**: 2.0 code units ≈ 6.5 free-fall times
- **Wall time**: 39.6 minutes (200 CPUs active, 12–14 concurrent sims)
- **Output**: 2,288 HDF5 snapshots (not in repo — see Data Location below)

## Key Results

| Quantity | Value |
|---|---|
| Simulations completed | 208 / 208 (0 failures) |
| HDF5 snapshots | 2,288 |
| C_final range | 1.005 (β=0.1) – 22.5 (β=10) |
| W3 conditions (M~3, β~0.7–1.5) | C = 6–10, γ ≈ 4–6 code units⁻¹ |
| Peak growth rate (measured) | γ = 6.33 ≈ √(4πGρ₀) = 6.28 ✓ |
| Magnetic criticality threshold | β_crit ≈ 0.15 (domain-scale) |

## Directory Structure

```
filament_spacing_campaign_apr2026/
├── README.md                    ← This file
├── pgen/
│   └── filament_spacing.cpp     ← Athena++ problem generator (v2, with SetFourPiG)
├── scripts/
│   ├── run_campaign.py          ← Ray-based campaign launcher (208 sims)
│   ├── analyse_campaign_v2.py   ← Scientific analysis pipeline
│   └── example_input_M3_b1.in  ← Example Athena++ input (M=3.0, β=1.0)
├── results/
│   ├── analysis_results.json    ← Per-sim C(t), γ, λ_peak for all 208 sims
│   ├── regime_grids.json        ← 10×10 C and γ grids (Batch 1)
│   ├── w3_subset.json           ← 104 W3-regime simulation results
│   └── campaign_status_v2.json  ← Full campaign metadata + per-sim timing
└── report/
    └── filament_spacing_campaign_report_2026-04-18.md  ← Full scientific report
```

## Critical Bug Fix (v1 → v2)

Campaign v1 (run immediately prior) showed C_final ≈ 1.002 across all 208 sims —
no gravitational collapse. Root cause: Athena++ does **not** auto-read `four_pi_G`
from the `<gravity>` input block. The problem generator must call `SetFourPiG()` from
`Mesh::InitUserMeshData()`. The v1 pgen was missing this function; `four_pi_G_`
defaulted to −1.0 (repulsive gravity of negligible magnitude).

Fixed in `pgen/filament_spacing.cpp` by adding:
```cpp
void Mesh::InitUserMeshData(ParameterInput *pin) {
    if (SELF_GRAVITY_ENABLED) {
        Real four_pi_G = pin->GetReal("problem", "four_pi_G");
        SetFourPiG(four_pi_G);
    }
}
```

## Compilation

```bash
# On astra-climate
export CPATH=/usr/include/hdf5/openmpi
cd ~/athena
make clean
python3 configure.py \
    --prob=filament_spacing \
    --coord=cartesian \
    --eos=isothermal \
    --flux=hlld \
    -b -mpi --grav=fft -fft -hdf5
make -j32
```

## Running the Campaign

```bash
# Start Ray cluster
~/.local/bin/ray start --head --num-cpus=200 --num-gpus=0

# Launch campaign (nohup for background execution)
nohup python3 scripts/run_campaign.py > campaign.log 2>&1 &

# Monitor
tail -f campaign.log
cat /home/fetch-agi/campaign_status_v2.json | python3 -m json.tool
```

## Data Location

The full HDF5 dataset (2,288 files, ~1.1 GB) is stored on astra-climate:
```
fetch-agi@34.143.130.135:/home/fetch-agi/campaign_1day_v2/
```
Directory structure: `campaign_1day_v2/{sim_name}/outputs/*.athdf`

Analysis outputs:
```
fetch-agi@34.143.130.135:/home/fetch-agi/analysis_v2/
```

## Full Report

See `report/filament_spacing_campaign_report_2026-04-18.md` for complete scientific
analysis including regime diagrams, growth rate tables, W3 comparison, and physical
interpretation.
