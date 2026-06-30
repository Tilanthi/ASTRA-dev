# RCE Campaign: Executive Summary and Quick Start

## Overview

The **Radial Confinement Escalation (RCE)** campaign is designed to definitively resolve the filament spacing discrepancy by testing the hypothesis that real HGBS filaments occupy an intermediate confinement regime between free boundaries and rigid walls.

---

## The Scientific Problem in One Paragraph

**Observation:** HGBS filaments show λ/W ≈ 2.0-2.8
**Theory:** Classical isothermal cylinders predict λ/W ≈ 4×
**Current Results:**
- Free boundaries (RTC): 0/1,200 simulations match (λ/W ≥ 3.75)
- Rigid walls: 9/45 simulations match (λ/W = 2.65 ± 0.57)
- **Conclusion:** Real filaments likely exist somewhere in between

**Critical Gap:** The f = 1.2-1.5 regime where physics transitions from longitudinal beading to radial collapse has never been sampled with realistic boundary conditions.

---

## The RCE Hypothesis

Real filaments are **partially confined by external pressure** from surrounding molecular cloud material, not free boundaries but also not rigid walls. This intermediate confinement:
- Slows radial collapse (allowing longitudinal fragmentation time to complete)
- Reduces λ/W from RTC values toward HGBS observations
- Represents physically realistic filament conditions

---

## Campaign Design at a Glance

### Parameter Space
```
f (line-mass):     [1.2, 1.3, 1.4, 1.5]  ← Bridges extrapolation gap
β (plasma beta):    [0.5, 1.0, 2.0]        ← Weak to moderate fields
M (Mach):           [2.0, 3.0]             ← Physical ISM turbulence
P_ext (pressure):   [0.0, 0.1, 0.3, 0.5]   ← Free → Strong confinement
Seeds:              3 per parameter point
```

### Total Simulations
**360 simulations** (18 high-priority Tier 1 sims)

### Computational Cost
**~720 compute hours** at 128³ resolution

---

## Expected Outcomes and What They Mean

### Outcome 1: Smooth Transition (Most Likely)
**Result:** λ/W decreases smoothly with increasing P_ext
```
P_ext = 0.0 → λ/W ≈ 4.5
P_ext = 0.1 → λ/W ≈ 3.8
P_ext = 0.3 → λ/W ≈ 2.9
P_ext = 0.5 → λ/W ≈ 2.3  ← Matches HGBS!
```

**Interpretation:** **Radial confinement is the key parameter.** Real filaments with P_ext ≈ 0.3-0.5 ρc_s² match observations. This resolves the RTC vs rigid cylinder contradiction.

**Discriminating Power:** HIGH - Makes specific predictions about column density profile shapes

### Outcome 2: Threshold Behavior
**Result:** Sharp transition at specific confinement level

**Interpretation:** Critical confinement threshold exists (bistable filament states)

**Discriminating Power:** HIGH - Predicts bimodal filament population

### Outcome 3: No Confinement Effect
**Result:** λ/W remains high even at P_ext = 0.5

**Interpretation:** **Radial confinement alone cannot explain discrepancy.** Points to missing physics (non-ideal MHD, thermodynamics).

**Discriminating Power:** HIGH - Definitively rules out confinement mechanism

---

## Why This Campaign is Definitive

1. **Bridges the extrapolation gap** - Directly samples f = 1.2-1.5 transition
2. **Physically realistic** - Intermediate confinement represents actual filament conditions
3. **High discriminatory power** - Each outcome makes testable predictions
4. **Computationally feasible** - 360 simulations is manageable (you've run 2,860 already!)
5. **Addresses central tension** - Tests whether RTC vs rigid cylinder contradiction can be resolved

---

## Implementation: Three Simple Steps

### Step 1: Implement External Pressure BC (Week 1)
**File to modify:** `athena++/src/bvals/bvals.cpp`

**Key addition:**
```cpp
// In boundary condition application
if (P_internal < P_external) {
    // Confinement regime - impose external pressure
    prim(IPR, k, j, i) = P_external;
} else {
    // Standard outflow - zero-gradient
    prim(IPR, k, j, i) = P_internal;
}
```

**Estimated time:** 2-3 days for implementation and testing

### Step 2: Generate Campaign Files (1 hour)
```bash
cd /path/to/W3_HGBS_filaments/final_merged_paper
python3 launch_rce_campaign.py --base-dir=./RCE_campaign --athena-path=../../athena++
```

**Generates:**
- 360 input files (`.in`)
- 1080 submission scripts (`.sh` for slurm/pbs/local)
- 1 master launch script

### Step 3: Launch Campaign (Ongoing)
```bash
cd RCE_campaign
./launch_campaign_slurm.sh  # or launch_campaign_pbs.sh
```

---

## Files Created for You

### 1. Complete Implementation Plan
**File:** `RCE_CAMPAIGN_IMPLEMENTATION_PLAN.md`
- Detailed scientific rationale
- Parameter space design
- Analysis pipeline
- Expected outcomes and interpretation

### 2. Athena++ BC Implementation Guide
**File:** `ATHENA_PP_EXTERNAL_PRESSURE_BC.md`
- Step-by-step code modifications
- Boundary condition physics
- Compilation instructions
- Testing and validation procedures

### 3. Campaign Launcher Script
**File:** `launch_rce_campaign.py`
- Generates all input files
- Creates submission scripts for multiple queues
- Tier 1 high-priority subset option

---

## Timeline and Milestones

| Phase | Duration | Milestone |
|-------|----------|-----------|
| **Code Development** | Week 1-2 | Working external pressure BC |
| **Tier 1 Simulations** | Week 3-4 | 18 high-priority results |
| **Full Campaign** | Week 5-8 | Complete dataset |
| **Paper Integration** | Week 9-10 | Submission-ready manuscript |

**Total time to results:** ~4 weeks for Tier 1, ~8 weeks for full campaign

---

## Risk Assessment

### Risk 1: Boundary Condition Instability
**Probability:** LOW
**Mitigation:** Start with low P_ext values, implement damping layers
**Impact:** LOW - Can be debugged and fixed

### Risk 2: Inconclusive Results
**Probability:** MEDIUM
**Mitigation:** Tier 1 provides early indication
**Impact:** LOW - Negative result still rules out mechanism

### Risk 3: Computational Overruns
**Probability:** LOW
**Mitigation:** 720 hours is conservative estimate
**Impact:** MEDIUM - Can extend timeline if needed

---

## Success Criteria

The RCE campaign will be successful if it:

1. ✅ **Samples the extrapolation gap** (f = 1.2-1.5 with realistic BC)
2. ✅ **Provides clear discrimination** between mechanisms
3. ✅ **Makes testable predictions** about filament properties
4. ✅ **Resolves or clarifies** the RTC vs rigid cylinder contradiction

**Even if the campaign shows that radial confinement cannot explain the discrepancy, it definitively rules out this mechanism and points to missing physics.**

---

## Backup Plan: Non-Ideal MHD

If RCE shows no confinement effect, the next priority is **ambipolar diffusion**:

**Hypothesis:** Magnetic flux leaks during filament assembly (multiple free-fall times), reducing effective β and decreasing λ/W.

**Campaign:** "Flux Loss Evolution" (FLE)
- Simulate filament assembly with ambipolar diffusion
- Track flux loss over 0-10 Myr
- 100-150 simulations at moderate resolution

**Athena++ module:** Ambipolar diffusion already exists, just needs activation

---

## Quick Reference Commands

### Generate campaign files
```bash
# Full campaign (360 simulations)
python3 launch_rce_campaign.py

# Tier 1 only (18 simulations)
python3 launch_rce_campaign.py --tier1-only
```

### Test boundary condition
```bash
cd athena++
mpirun -np 4 ./bin/athena -m config/test_pressure_bc.in
```

### Launch campaign
```bash
# SLURM queue
./launch_campaign_slurm.sh

# PBS queue
./launch_campaign_pbs.sh

# Local execution
./launch_campaign_local.sh
```

### Monitor progress
```bash
# SLURM
squeue -u $USER

# PBS
qstat -u $USER

# Check completion
ls outputs/*/RCE_*.hst | wc -l
```

---

## Key Contacts and Resources

### Athena++ Resources
- **Documentation:** https://github.com/PrincetonUniversity/athena/wiki
- **Issue Tracker:** https://github.com/PrincetonUniversity/athena/issues
- **Paper:** Stone et al. (2020), ApJS, 249, 4

### Boundary Condition References
- Pressure-confined boundaries: Stone & Norman (1992)
- Outflow conditions: characteristics method
- External pressure implementation: see ATHENA_PP_EXTERNAL_PRESSURE_BC.md

### Previous Campaign Analysis
- RTC campaign: 2,860 simulations
- Rigid cylinder: 45 simulations
- All results in: `targeted_reruns_results/campaign_summary.json`

---

## Final Recommendation

**Proceed with RCE Campaign.**

This is the most promising path to resolving the filament spacing discrepancy because:

1. It addresses the central tension identified in your paper
2. It uses physically realistic boundary conditions
3. It has high discriminatory power
4. It's computationally feasible
5. It makes testable predictions

The campaign will provide definitive results regardless of outcome:
- **Positive result:** Radial confinement explains discrepancy
- **Negative result:** Rules out confinement, points to missing physics

Either outcome advances the science significantly.

---

## Next Actions

1. **Review** the implementation plan and BC guide
2. **Set up** development environment
3. **Begin** Athena++ modifications
4. **Test** boundary condition with simple problems
5. **Generate** campaign files using launcher script
6. **Launch** Tier 1 simulations
7. **Analyze** preliminary results
8. **Decide** on full campaign execution

---

**Prepared by:** Claude (ASTRA System)
**Date:** June 6, 2026
**Status:** Ready for Implementation
**Confidence:** HIGH that this path will advance understanding significantly

