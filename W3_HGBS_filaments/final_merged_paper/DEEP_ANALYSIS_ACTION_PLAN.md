# Deep Analysis Action Plan: Resolving the Filament Fragmentation Contradiction

**Date**: 2026-05-02
**Purpose**: Concrete steps to resolve the fundamental contradiction
**Status**: Ready for execution

---

## Phase 1: Literature Deep Dive (Week 1)

### Objective
Understand what is already known about:
1. Fiber-level fragmentation and spacing
2. Temporal evolution of filaments
3. Non-ideal MHD effects
4. Core formation from density peaks

### Key Papers to Review

**Fiber Structure and Fragmentation:**
1. **Yang+2024** - CRITICAL: Fiber-to-core spacing in Orion B
   - Find their λ/W measurement for fibers
   - Understand their methodology
   - Check if they resolve the contradiction

2. Hacar+2013, Hacar+2018 - Fiber discovery
   - Fiber properties (width, spacing, mass-per-unit-length)
   - Relationship between fibers and filaments

3. Tatematsu+2019 - Fiber fragmentation in Taurus
   - Another region to test universality

**Temporal Evolution:**
4. Clarke+2016 - Core formation timescales
   - How long do cores take to form from peaks?
   - Peak-to-core conversion efficiency

5. Kwon+2023 or similar - Filament accretion rates
   - Timescale for near-critical → supercritical transition
   - Is it fast or slow compared to fragmentation?

**Non-Ideal MHD:**
6. Mouschovias+1992 - Ambipolar diffusion in filaments
   - Does it change fragmentation wavelength?

7. Recent reviews on filament evolution
   - Current understanding of filament lifecycle

### Deliverable
`LITERATURE_DEEP_DIVE.md` documenting:
- Summary of key findings from each paper
- What is known vs. unknown
- Which hypotheses have observational support
- Specific claims that can be tested

---

## Phase 2: Hypothesis Development (Week 2)

### Based on Literature, Develop One of Three Hypotheses:

#### Hypothesis A: Fossil Spacing (Temporal Evolution)
**Claim**: HGBS supercritical filaments with cores acquired those cores during a near-critical phase. Cores survive the transition to supercritical state.

**Testable predictions**:
- Cores in supercritical filaments should show age gradients
- Core properties should correlate with local fiber properties
- Filaments with higher f should have similar core spacing (fossil)

**Required work**:
- Literature: Are there core age measurements?
- Simulations: Near-critical → accrete → supercritical with core tracking

#### Hypothesis B: Fiber Bundle with Modified Statistics
**Claim**: Filaments are fiber bundles. True λ/W = 4 at fiber level, but filament-level measurements show compressed spacing due to projection/statistical effects.

**Testable predictions**:
- Fiber-resolved measurements should always give λ/W ≈ 4
- Filament-level measurements should vary with fiber number/geometry
- PM measures L/(3W), NN measures fiber-level spacing (compressed)

**Required work**:
- Literature: Compile all fiber-resolved λ/W measurements
- Analysis: Develop statistical model for bundle → observed spacing

#### Hypothesis C: Measurement Definition Mismatch
**Claim**: Simulation λ/W (peak spacing) ≠ Observation λ/W (core spacing). Peaks have different survival probabilities based on mass, environment.

**Testable predictions**:
- Peak spacing in simulations > core spacing (peaks merge/disappear)
- Core spacing depends on mass threshold
- λ/W should depend on core selection criteria

**Required work**:
- Simulations: Track peak → core conversion
- Analysis: Compute both peak spacing and core spacing in same simulation

### Deliverable
`WORKING_HYPOTHESIS.md` with:
- Clear hypothesis statement
- Testable predictions
- Required work to test
- How it resolves the contradiction

---

## Phase 3: Targeted Analysis/Simulation (Weeks 3-4)

### Depending on Hypothesis, Execute:

#### If Hypothesis A (Fossil Spacing):
**Simulation work**:
1. Set up near-critical filament (f = 1.0-1.2)
2. Let it fragment and form cores
3. Gradually add mass (accrete) to reach f = 2.0-3.0
4. Track core positions through transition
5. Measure: Do cores survive? Does spacing change?

**Observational work**:
1. Compile core ages (if available in literature)
2. Check if cores in supercritical filaments show different properties

#### If Hypothesis B (Fiber Bundle):
**Statistical analysis**:
1. Gather all fiber-resolved λ/W measurements from literature
2. Compare with filament-level measurements
3. Develop model: N_fibers × λ_fiber → observed λ_filament

**Synthetic tests**:
1. Generate multi-fiber models with realistic properties
2. Test NN/PM statistics on them
3. Can we reproduce HGBS values?

#### If Hypothesis C (Measurement Mismatch):
**Simulation analysis**:
1. Take existing near-critical simulations
2. Extract both: (a) all density peaks, (b) only bound cores
3. Compare spacings: Are they different?
4. Vary core mass threshold: Does λ/W change?

### Deliverable
Targeted analysis results addressing the hypothesis

---

## Phase 4: Paper Revision Strategy (Week 5)

### Based on Results, Choose Revision Approach:

#### Option 1: Minimal Revision (Conservative)
**If hypothesis not strongly supported**:
- Acknowledge all limitations upfront
- Present PM = L/3W as geometric measurement
- Present NN λ/W < 1.25 as unsolved problem
- State that simulation-observation comparison not yet possible
- Recommend fiber-resolved future work

**Pros**: Honest, defensible
**Cons**: Limited conclusions

#### Option 2: Evolutionary Framework (Bold)
**If fossil spacing hypothesis supported**:
- Present temporal evolution as main insight
- Cores form during near-critical, survive to supercritical
- Explain all observations in this framework
- Make testable predictions for future work

**Pros**: Novel contribution, resolves contradiction
**Cons**: Speculative, requires strong evidence

#### Option 3: Hierarchical Synthesis (Balanced)
**If fiber bundle hypothesis supported**:
- Present hierarchical picture: fibers → filaments
- Explain PM vs NN in this context
- Synthesize all explanations into coherent framework
- Recommend fiber-resolved observations as critical test

**Pros**: Comprehensive, synthesizes existing work
**Cons**: Complex, may dilute main message

### Deliverable
`PAPER_REVISION_PLAN.md` with:
- Chosen approach with rationale
- Specific sections to revise/rewrite
- New narrative structure
- Figures/tables needed

---

## Phase 5: Execution and Revision (Weeks 6-8)

### Concrete Steps:
1. Complete any remaining analysis
2. Generate required figures
3. Rewrite affected sections
4. Update abstract to reflect new framing
5. Revise conclusions accordingly
6. Peer review internal draft
7. Final polish

### Deliverable
Revised paper ready for resubmission

---

## Immediate Next Steps (This Week)

### Step 1: Literature Review (Start Today)
Use web search and local files to find:
- Yang+2024 paper (fiber-to-core spacing in Orion B)
- Recent filament evolution reviews
- Core formation timescale papers
- Non-ideal MHD in filaments

### Step 2: Check Existing ASTRA Capabilities
Can ASTRA help with:
- Literature search and synthesis
- Hypothesis generation
- Analysis design
- Simulation planning

### Step 3: Regular Check-ins
Report progress every 2-3 days with:
- What was found
- What it means for the contradiction
- What to do next

---

## Success Criteria

The contradiction is resolved when we can explain:
1. **Why HGBS supercritical filaments have cores** (simulation-observation disconnect)
2. **What PM λ/W = 2.79 actually means** (geometric vs. physical)
3. **Why NN λ/W < 1.25** (below theoretical minimum)
4. **How all observations fit into coherent framework**

The paper is ready when:
- No logical contradictions
- All claims supported by evidence
- Clear distinction between what we know vs. what we need to test
- Honest assessment of limitations
- Clear path forward for future work

---

**Status**: Phase 1 (Literature Deep Dive) - READY TO START
**Next Action**: Begin with Yang+2024 and recent filament evolution literature
**Timeline**: 8 weeks total for complete analysis and revision

---

## Questions to Resolve Through This Process

1. What does Yang+2024 actually find about fiber-to-core spacing?
2. Do fibers consistently show λ/W ≈ 4?
3. What are the timescales for core formation vs. filament evolution?
4. Can cores survive the near-critical → supercritical transition?
5. What is the relationship between peak spacing and core spacing?
6. How does hierarchical structure affect measurements?
7. Which hypothesis has the most observational support?
8. What specific test would distinguish between hypotheses?

**Answering these questions will resolve the contradiction.**

---

**End of Action Plan**
