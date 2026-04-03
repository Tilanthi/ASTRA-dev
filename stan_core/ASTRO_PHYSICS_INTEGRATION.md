# Integration: Existing Specialist Modules with New Domain System

## Overview

This document describes how the existing `stan_core.astro_physics` specialist modules integrate with the new modular domain system introduced in Phase 2-4.

## Architecture

```
stan_core/
├── astro_physics/              # Existing specialist modules (V45)
│   ├── molecular_cloud_physics.py
│   ├── radiative_transfer.py
│   ├── shock_physics.py
│   ├── star_formation.py
│   ├── sph_gas_dynamics.py
│   └── ... (30+ specialist modules)
│
├── domains/                    # NEW: Modular domain architecture (Phase 2-4)
│   ├── __init__.py             # BaseDomainModule interface
│   ├── registry.py             # DomainRegistry for hot-swapping
│   ├── exoplanets/             # Example domain modules
│   ├── gravitational_waves/
│   └── ...                     # To be expanded with ISM domains
│
├── physics/                    # NEW: Unified physics (Phase 3)
│   ├── unified_physics.py      # UnifiedPhysicsEngine
│   ├── curriculum_learning.py  # PhysicsCurriculum
│   └── analogical_reasoner.py  # PhysicalAnalogicalReasoner
│
└── reasoning/
    └── cross_domain_meta_learner.py  # NEW: Cross-domain adaptation
```

## Integration Strategy

### Option 1: Direct Import (Current)
Existing specialist modules can be imported directly from `astro_physics`:

```python
from stan_core.astro_physics import (
    MolecularCloudPhysics,
    RadiativeTransfer,
    ShockPhysics,
    StarFormation,
    SPHSimulation
)
```

### Option 2: Domain Wrappers (Recommended)
Create domain modules that wrap existing specialist capabilities:

```python
# stan_core/domains/ism/__init__.py
from .. import BaseDomainModule
from ...astro_physics import (
    MolecularCloudPhysics,
    RadiativeTransfer,
    ShockPhysics
)

class ISMDomain(BaseDomainModule):
    def __init__(self):
        self.mc_physics = MolecularCloudPhysics()
        self.rad_transfer = RadiativeTransfer()
        self.shock_physics = ShockPhysics()
```

### Option 3: Hybrid Approach
Use existing modules directly while leveraging new domain infrastructure for meta-learning and cross-domain reasoning:

```python
# Enhanced system can route to either
if domain == "molecular_clouds":
    result = astro_physics.molecular_cloud_physics.analyze(data)
elif domain == "star_formation":
    result = astro_physics.star_formation.calculate_sfr(data)
```

## Existing Specialist Capabilities

### Core ISM Physics
| Module | Capabilities |
|--------|--------------|
| `molecular_cloud_physics.py` | Jeans analysis, virial equilibrium, fragmentation |
| `radiative_transfer.py` | Line profiles, dust continuum, PDR models |
| `shock_physics.py` | J-shocks, C-shocks, shock chemistry |
| `hii_region_physics.py` | Strömgren spheres, recombination lines |
| `gravitational_collapse.py` | Freefall collapse, accretion rates |
| `supernova_remnant_physics.py` | Sedov-Taylor blastwaves, SNR evolution |

### Star Formation & Stellar Evolution
| Module | Capabilities |
|--------|--------------|
| `star_formation.py` | IMF, SFR laws, stellar populations, feedback |
| `sph_gas_dynamics.py` | SPH simulations, filament finding, cloud formation |

### Observational Techniques
| Module | Capabilities |
|--------|--------------|
| `radio_surveys.py` | Radio source detection, survey catalogs |
| `infrared_submm.py` | Dust SED fitting, IR colors, gas mass |
| `interferometry.py` | UV coverage, CLEAN, self-calibration |
| `spectral_line_analysis.py` | Line fitting, optical depth, column density |

### Data Analysis
| Module | Capabilities |
|--------|--------------|
| `source_extraction.py` | Dendrograms, filament finding, core catalogs |
| `kinematic_analysis.py` | Moment maps, PV diagrams, infall signatures |
| `turbulence_analysis.py` | Structure functions, power spectra, VCS/DCF |

### Deep Learning (V45)
| Module | Capabilities |
|--------|--------------|
| `filament_detector.py` | Neural network filament detection |
| `molecular_cloud_segmenter.py` | Cloud segmentation in velocity cubes |
| `shock_detector.py` | Shock classification from spectral lines |

## Cross-Domain Synergies

The new domain system enables:

1. **Meta-learning across domains**: Transfer knowledge from exoplanets to molecular clouds
2. **Unified physics reasoning**: Apply same physics engine across all domains
3. **Curriculum learning**: Progress from basic mechanics to MHD turbulence
4. **Analogical reasoning**: Apply filament understanding from clouds to galaxies

## Integration Points

```python
# Example: Unified query processing
system = EnhancedUnifiedSTANSystem()

# Query gets routed to appropriate specialist module
result = system.process_query(
    "Calculate the Jeans length in a molecular cloud with density 1e4 cm^-3",
    context={'domain': 'ism', 'subdomain': 'molecular_clouds'}
)

# System routes to:
# 1. ISMDomain (new domain module)
# 2. Which wraps astro_physics.molecular_cloud_physics (existing specialist)
# 3. Using physics_engine.newtonian_gravity (unified physics)
# 4. With cross_domain_meta_learner suggesting analogous problems in other domains
```

## Migration Path

1. **Phase 1** (Current): Keep existing modules, add domain wrappers
2. **Phase 2**: Gradually migrate specialist capabilities to domain modules
3. **Phase 3**: Full integration with cross-domain meta-learning
4. **Phase 4**: Curriculum-based learning across all domains

## Summary

- ✅ All existing specialist capabilities remain intact
- ✅ New domain system is additive, not replacing
- ✅ Can use existing modules directly or via domain wrappers
- ✅ Meta-learning enables knowledge transfer across specialist areas
- ✅ Unified physics engine applies to all domains
- ✅ Curriculum learning progresses from basic to advanced physics

## Next Steps

1. Create domain wrappers for ISM subfields
2. Implement domain modules for star formation stages
3. Add cross-domain connections (e.g., filaments → galaxy formation)
4. Validate end-to-end integration
