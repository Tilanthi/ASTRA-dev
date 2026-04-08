# W3_HGBS_Filaments: Integrated Filament Discovery Exercise

## Project Overview

This project brings together observational data from Herschel HGBS survey and W3 HII region with MHD numerical simulations and theoretical modeling to understand interstellar filamentary physics across diverse star-forming environments.

## Research Questions

1. **What determines the characteristic width of interstellar filaments?**
   - Test sonic scale theory against MHD simulations
   - Compare predictions across different environments (Taurus, Orion, W3, etc.)

2. **How do filaments form and evolve in different environments?**
   - Environmental dependence of filament properties
   - Role of turbulence vs. magnetic fields

3. **What governs filament stability and longevity?**
   - Critical mass thresholds across environments
   - Timescales for fragmentation and star formation

4. **What determines star formation potential?**
   - M_line as predictor of prestellar core formation
   - Environmental variations in star formation efficiency

## Data Sources

### Observational Data (HGBS_PAPER)
- **13 Herschel HGBS regions**: Taurus, Ophiuchus, Aquila, Perseus, Orion, etc.
- **W3 HII region**: High-mass star-forming complex
- **6,499+ cores** with mass and evolutionary classifications
- **Filament networks**: Column density maps and skeleton extractions

### Theoretical/Simulation Data (ISM_filaments)
- **MHD simulations**: Athena++ code, 256³-1024³ resolution
- **Parameter sweeps**: Temperature (8-20 K), density (10³-10⁵ cm⁻³), B-field (10-100 μG)
- **Four competing theories**: Sonic scale, Ostriker, Jeans lengths, ambipolar diffusion

## Analysis Pipeline

1. **Data Integration Phase**: Merge observational catalogs with simulation results
2. **Comparative Analysis**: Test theoretical predictions against real data
3. **Environmental Study**: Analyze variations across regions
4. **Literature Integration**: Compare with Arzoumanian et al. 2019 and related work
5. **Discovery Science**: New insights into filament physics

## Expected Deliverables

- **MNRAS-format paper** with comprehensive analysis
- **Multi-panel figures** showing observations + theory + simulations
- **New discoveries** about filament formation and evolution
- **Predictive framework** for star formation potential

## Key References

- Arzoumanian et al. 2019, A&A 621, A42 (Herschel filament characterization)
- André et al. 2010-2016 (HGBS survey papers)
- Ostriker 1964 (hydrostatic equilibrium)
- Inutsuka & Miyama 1997 (cylinder instability)
- Hennebelle & André 2013 (filament formation)

## Directory Structure

```
W3_HGBS_filaments/
├── data/              # Observational and simulation data
├── analysis/          # Analysis scripts
├── figures/           # Publication figures
├── paper/             # LaTeX source and PDF
├── literature/        # Literature survey and citations
└── README.md          # This file
```

## Authorship

G. J. White et al.
