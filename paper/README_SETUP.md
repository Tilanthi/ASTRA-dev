# RASTI Paper Split - Folder Setup Complete

## Overview

Two independent working folders have been created for developing separate papers:

1. **RASTI_AI** - AI/ML venue paper focusing on meta-cognitive capabilities
2. **RASTI_ASTRO** - Astronomy venue paper focusing on astrophysical applications

## Folder Locations

- `/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_AI/`
- `/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_ASTRO/`

## Files in Each Folder

### Core LaTeX Files
- `ASTRA_V8_40_RASTI.tex` - Main paper document (41 pages)
- `RASTI.cls` - RASTI journal class file
- `astra_references.bib` - ASTRA bibliography
- `references.bib` - Additional references

### Included LaTeX Files
- `fig_architecture_revised.tex` - Architecture diagram (TikZ)
- `comparison_table.tex` - Comparison table

### Figures (figures_v41/)
All 9 figures used in the paper:
- `fig_domain_coverage_v69.pdf` - Domain coverage diagram
- `fig_system_integration_v70.pdf` - System integration diagram
- `hgbs_cmf_environment.png` - CMF-environment correlation
- `hgbs_experimental_design.png` - Experimental design proposals
- `hgbs_filament_spacing_resonance.png` - Filament spacing resonance
- `hgbs_harmonic_resonance_v71.png` - Harmonic resonance mechanism
- `hgbs_magnetic_mediation.png` - Magnetic field mediation
- `hgbs_multi_cloud_cmf.png` - Multi-cloud CMF comparison
- `hgbs_multiscale_hierarchy.png` - Multi-scale hierarchy

## Compilation

Both folders compile successfully:

```bash
cd /Users/gjw255/astrodata/SWARM/ASTRA/RASTI_AI
pdflatex ASTRA_V8_40_RASTI.tex
# Output: ASTRA_V8_40_RASTI.pdf (41 pages, 2.1 MB)

cd /Users/gjw255/astrodata/SWARM/ASTRA/RASTI_ASTRO
pdflatex ASTRA_V8_40_RASTI.tex
# Output: ASTRA_V8_40_RASTI.pdf (41 pages, 2.1 MB)
```

## Next Steps

### For RASTI_AI Paper
Focus on:
- Meta-cognitive self-evaluation capability
- Comparisons to science AI systems (AI Feynman, ChemCrow)
- Novel meta-cognitive benchmark
- Ablation studies

Recommended restructuring:
- Delete Sections 2-8 (100+ pages of architecture)
- Keep Sections 1, 5-9, 10.7
- Add benchmark comparison sections
- Emphasize methodological contribution

### For RASTI_ASTRO Paper
Focus on:
- Conservative astrophysical analysis
- CMF-environment correlation (solid result)
- Self-critical evaluation as methodological contribution
- Address all data quality issues

Recommended restructuring:
- Reduce system description to 3-4 pages
- Fix sample definition issues
- Use homogeneous data only
- Add proper statistical methods (mixed-effects models)

## Version Control

Each folder is independent. You can:
- Edit files in one folder without affecting the other
- Compile and test changes independently
- Keep different versions for different venues

## Notes

- Both folders currently contain identical copies of ASTRA_V8_40_RASTI.tex
- Image paths are already correct (referencing `figures_v41/` subdirectory)
- All files are ready for independent development
- No shared dependencies between folders
