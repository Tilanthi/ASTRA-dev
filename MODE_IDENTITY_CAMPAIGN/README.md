# Mode Identity Validation Campaign

## Overview

This package contains the complete setup for running the Mode Identity Validation Campaign on a 220 vCPU Ray cluster. The campaign addresses a critical uncertainty in filament fragmentation theory: **whether sub-isothermal beading (γ < 1) represents the same physical instability mode as isothermal beading (γ = 1)**.

## Scientific Justification

### The Problem

Our MNRAS paper reports that sub-isothermal filaments with longitudinal magnetic fields produce λ/W ≈ 2.8-3.2, which matches HGBS observations (λ/W ≈ 2.8). However, a fundamental question remains:

**Mode Identity Uncertainty**: Does the beading detected at f ≥ 1.5 with γ < 1 represent the same physical instability (sausage instability mode) as isothermal beading at f ≤ 1.3, or is it a different collapse mode that happens to produce numerically similar λ/W values?

### The Solution

This campaign runs 36 matched Athena++ simulations (18 isothermal + 18 sub-isothermal pairs) to validate mode identity through:

1. **Power Spectrum Shape Comparison**: Same mode → similar spectral shapes (peak width, slope, harmonics)
2. **Growth Rate Analysis**: Same mode → growth rates scale with effective sound speed (c_eff ∝ √γ)  
3. **Phase Coherence Analysis**: Same mode → coherent phase structure in density peaks

## Package Contents

- `mode_identity_campaign.tar.gz`: Complete campaign package with:
  - `README.md`: Comprehensive scientific and technical documentation
  - `requirements.txt`: Python dependencies (ray, numpy, pandas, scipy, h5py, matplotlib)
  - `parameters.csv`: 36 simulation parameters (18 isothermal + 18 sub-isothermal pairs)
  - `run_campaign.sh`: Main execution script for Ray cluster
  - `config/ray_cluster.yaml`: Ray configuration for 220 vCPUs
  - `analysis/mode_identity_analysis.py`: Full mode identity analysis methods

## Quick Start

### 1. Extract Package

```bash
cd /tmp
tar -xzf mode_identity_campaign.tar.gz
cd mode_identity_campaign
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Athena++

Ensure Athena++ binary (`athena_pr`) is available on worker nodes.

### 4. Run Campaign

```bash
bash run_campaign.sh
```

## Expected Outcomes

After running the campaign, the analysis will produce one of three conclusions:

1. **VALIDATED**: Strong evidence that sub-isothermal beading IS the same physical mode → Paper claim strongly supported
2. **MODERATE SUPPORT**: Evidence suggests same mode but uncertainty remains → Paper claim reasonably supported  
3. **NOT VALIDATED**: Evidence does NOT support same physical mode → Paper requires revision

## Resources Required

- **Compute**: 220 vCPUs (54 workers × 4 CPUs)
- **Time**: ~12-24 hours walltime
- **Storage**: ~500-900 GB disk space
- **Memory**: ~16 GB per worker

## Citation

If you use this campaign package or its results, please cite:

```bibtex
@article{filament_spacing_2026,
  author = {Jadhav, et al.},
  title = {Filament Spacing in Molecular Clouds: 
           Isothermal vs Sub-Isothermal Fragmentation},
  journal = {MNRAS},
  year = {2026}
}
```

## Contact

For questions or issues, contact:
- Glenn J. W. (Tilanthi) - https://github.com/Tilanthi

---

**Status**: Package ready for deployment on 220 vCPU Ray cluster
**Created**: 2026-05-16
**Version**: 1.0
