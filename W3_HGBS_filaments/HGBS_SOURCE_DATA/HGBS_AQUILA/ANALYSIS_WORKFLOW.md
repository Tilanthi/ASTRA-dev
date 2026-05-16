# HGBS Discovery Science - Analysis Workflow Guide

This guide explains how to run the complete HGBS discovery analysis on a new region.

## Quick Start (3 Steps)

### Step 1: Copy Scripts to Your New Region Folder

```bash
cd /Users/gjw255/astrodata/SWARM/ASTRA/HGBS
python setup_region.py /path/to/your/new/HGBS_REGION_FOLDER
```

This copies all analysis scripts to your region folder.

### Step 2: Run All 5 Phases

```bash
cd /path/to/your/new/HGBS_REGION_FOLDER
python run_all_phases.py /path/to/your/new/HGBS_REGION_FOLDER REGION_NAME
```

Example for Orion:
```bash
cd /data/HGBS_ORION
python run_all_phases.py /data/HGBS_ORION Orion
```

This will run all 5 phases sequentially (typically takes 10-20 minutes).

### Step 3: Create Visualizations

```bash
python create_visualizations.py
```

This creates 7 comprehensive plots of all discoveries.

---

## What Each Phase Does

| Phase | Name | Description | Output |
|-------|------|-------------|--------|
| 1 | Data Exploration | Loads data, catalogues cores, identifies unusual objects | phase2_results.npz, PHASE1_RESULTS.md |
| 2 | Core-Filament Association | Associates cores with filaments, measures spacing | PHASE2_RESULTS.md |
| 3 | M_line Analysis | Calculates mass-per-unit-length, tests threshold | PHASE3_RESULTS.md |
| 4 | Junction Analysis | Identifies filament junctions, analyzes massive cores | PHASE4_RESULTS.md |
| 5 | Discovery Mode | Multi-parameter analysis, anomaly detection, causal inference | PHASE5_RESULTS.md |

---

## Required Data Files

Your region folder should contain:

1. **Column density map**: `HGBS_<region>_column_density_map.fits` or `<region>_column_density_map.fits`
2. **Temperature map**: `HGBS_<region>_temperature_map.fits` or `<region>_temperature_map.fits`
3. **Skeleton map**: `HGBS_<region>_skeleton_map.fits` or `<region>_skeleton_map.fits`
4. **Core catalog**: `HGBS_<region>_derived_core_catalog.txt` or similar

---

## Running Phases Individually

If you prefer to run phases one at a time:

```bash
cd /path/to/your/new/HGBS_REGION_FOLDER

python hgbs_discovery_phase1_fixed.py
python hgbs_discovery_phase2.py
python hgbs_discovery_phase3.py
python hgbs_discovery_phase4.py
python hgbs_discovery_phase5.py
```

---

## Output Files

After running all phases, you will have:

- `phase2_results.npz` - Core data with all properties (used by subsequent phases)
- `PHASE1_RESULTS.md` - Phase 1 results summary
- `PHASE2_RESULTS.md` - Phase 2 results summary
- `PHASE3_RESULTS.md` - Phase 3 results summary
- `PHASE4_RESULTS.md` - Phase 4 results summary
- `PHASE5_RESULTS.md` - Phase 5 results summary

After running visualizations:
- `hgbs_plot1_distributions.png` - Core property distributions
- `hgbs_plot2_mass_vs_temp.png` - Mass vs. Temperature
- `hgbs_plot3_mass_vs_mline.png` - Mass vs. M_line
- `hgbs_plot4_correlations.png` - Correlation matrix
- `hgbs_plot5_environmental_progression.png` - Environmental scaling
- `hgbs_plot6_massive_cores.png` - Massive core analysis
- `hgbs_plot7_discovery_summary.png` - Discovery summary

---

## Example: Complete Workflow for a New Region

```bash
# 1. Set up the new region
cd /Users/gjw255/astrodata/SWARM/ASTRA/HGBS
python setup_region.py /data/HGBS_ORION

# 2. Go to the region folder and run analysis
cd /data/HGBS_ORION
python run_all_phases.py /data/HGBS_ORION Orion

# 3. Create visualizations
python create_visualizations.py
```

---

## Troubleshooting

**"Script not found" error**: Make sure you ran `setup_region.py` first to copy scripts.

**"FITS file not found" error**: Check your FITS file names match the expected pattern. The scripts look for files like:
- `<region_name>_column_density_map.fits`
- `<region_name>_temperature_map.fits`
- `<region_name>_skeleton_map.fits`

If your files have different names, you can edit the `COL_DEN_FILE`, `TEMP_FILE`, and `SKELETON_FILE` variables at the top of each phase script.

**Phase fails but continues**: The `run_all_phases.py` script will continue running even if one phase fails. Check the individual phase markdown files to see which phases completed successfully.

---

## Contact

For issues or questions about the HGBS Discovery Science framework, please refer to the main documentation or contact the ASTRA development team.
