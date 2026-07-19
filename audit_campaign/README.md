# AUDIT CAMPAIGN PACKAGE
## Referee-Requested Simulation Audit for the Filament Spacing Paper

### OVERVIEW

This package contains **66 Athena++ simulation configs + runner + analysis pipeline** for the comprehensive audit requested by the referees. It tests whether the central results of the paper (domain-size dependence of supercritical fragmentation, field-geometry effects, and near-critical validation) hold under independent verification.

**Total simulations**: 66 (est. ~10 hours on 220 CPUs)
**Expected output**: `audit_summary.json` (feed this back to Claude for paper integration)

### WHAT IT TESTS

1. **Extended-domain supercritical audit** (24 sims): Does longitudinal beading develop at f=1.5–3.0 in extended (24λ_J) domains? (The f=1.5 result is already known: λ/W=3.33. This extends to f=2.0–3.0 and β=0.3/2.0.)

2. **Domain-size convergence map** (15 sims): At f=2.0, β=1.0, maps λ/W as a function of domain size Lx=8/16/24/32/48 λ_J. Shows where the transition from radial-collapse to beading occurs.

3. **Field Geometry spot-check** (18 sims): Perpendicular (θ=90°), oblique (θ=45°), and longitudinal (θ=0°) fields at f=1.5 and 2.0 in extended domains. Confirms the perpendicular-field λ/W≈1.25 and the t_frag acceleration.

4. **Near-critical validation** (9 sims): f=1.0–1.2 at 24λ_J. Confirms beading in the near-critical regime at extended domain.

### EXISTING T1 PLUMMER RESULTS (already done!)

The T1 Plummer re-measurement has **already been completed** (June 2026). Results in `t1_plummer_existing_results.json`:
- **ratio_GP (Plummer/Gaussian) = 1.17 ± 0.04** — the Plummer fit gives a 17% wider filament than Gaussian
- This is **within the existing ±11.9% T1 systematic** (0.606 ± 0.072)
- **Conclusion**: the Gaussian approximation is adequate; no new T1 sims needed

### INSTRUCTIONS

#### 1. Transfer to the cluster machine
```bash
# On the local Mac:
cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main
tar czf audit_campaign.tar.gz audit_campaign/
# Transfer audit_campaign.tar.gz to the cluster machine
```

#### 2. On the cluster machine
```bash
# Extract
tar xzf audit_campaign.tar.gz
cd audit_campaign/

# Compile Athena++ with the filament problem generator
# (if not already compiled on this machine)
# The problem generator uses: four_pi_G, f_line_mass, plasma_beta,
# theta_deg, mach_number, perturb_ampl, random_seed, W_core
# Compile with: cd athena++-src && cmake -B build && cmake --build build
# The binary should be named 'athena++' or similar

# Generate configs (if not already present)
python3 generate_audit_configs.py

# Run the campaign via Ray
python3 run_audit_campaign.py --athena_path /path/to/athena++ --max_concurrent 13

# Wait for completion (~10 hours)

# Analyse results
python3 analyze_audit_results.py --results audit_campaign_results.json --output_dir analysis_output
```

#### 3. Feed back to Claude
After the analysis completes, send back:
- `analysis_output/audit_summary.json` — the complete summary of all 66 sims
- (Optional) Any HDF5 snapshots for the extended-domain sims that show beading (for independent λ/W verification)

Claude will integrate these results into the paper, update the audit status from "partially audited" to "fully audited," and resolve the referees' remaining concerns.

### FILE STRUCTURE
```
audit_campaign/
├── README.md                              ← This file
├── generate_audit_configs.py              ← Config generator (66 .athinput files)
├── run_audit_campaign.py                  ← Ray-distributed runner
├── analyze_audit_results.py               ← Analysis + reduction pipeline
├── t1_plummer_existing_results.json       ← T1 Plummer results (already done)
├── configs/
│   ├── manifest.json                      ← Campaign manifest
│   ├── supercritical_extended/            ← 24 .athinput files
│   ├── domain_convergence/                ← 15 .athinput files
│   ├── field_geometry/                    ← 18 .athinput files
│   └── near_critical/                     ← 9 .athinput files
└── analysis_scripts/                      ← (empty, for user's analysis outputs)
```

### KEY PARAMETERS
- **Seeds**: 42, 137, 251 (3 per parameter point)
- **Resolution**: 1536×64×64 for 24λ_J domain (64 cells/λ_J)
- **Wall timeout**: 21600s (6 hours) per sim
- **Cores per sim**: 16 (→ 13 concurrent on 220 CPUs)
- **Domain**: 24λ_J × 1λ_J × 1λ_J (extended)
- **EOS**: Isothermal (γ=1.0)
- **BCs**: Periodic on all faces

### WHAT THE RESULTS WILL TELL US

| If beading develops at f=2.0–3.0 in 24λ_J... | Then... |
|---|---|
| YES (λ/W measured) | The magnetic-tension calibration is a direct measurement at all f; the paper's negative result was purely domain-size limited |
| NO (radial collapse only) | The domain-size transition is f-dependent; at high f, even extended domains show radial collapse (physically interesting) |
| MIXED (transition at f≈2–2.5) | The transition maps the regime where radial vs longitudinal modes compete most closely |

Either outcome is scientifically valuable and publishable.
