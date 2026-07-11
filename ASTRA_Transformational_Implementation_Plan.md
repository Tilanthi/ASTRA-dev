# ASTRA Transformational Architecture Implementation Plan

## Executive Summary

This document outlines the integration of the Transformational Discovery Architecture into ASTRA's existing discovery pipeline. The new architecture addresses critical issues identified in current system validation and upgrades ASTRA from "sophisticated statistical automation" to "rigorous autonomous discovery behavior."

## Current System Issues (Identified in Architecture Guide)

1. **Small-N Problem**: Only N=7 clouds, insufficient for population-level claims
2. **Missing Discovery Gate**: No bar for calling something a "discovery"
3. **Self-Grading**: Circular evaluation where ASTRA scores its own outputs
4. **Empty Discovery Demonstration**: Results section with no actual analysis
5. **Missing Prior Knowledge**: Treats expected replications as discoveries
6. **No Power Analysis**: Statistical tests without minimum detectable effect
7. **Missing Multiple Comparison Correction**: FDR not applied automatically
8. **No Independent Replication**: No holdout set for verification

## New Architecture Components (8-Phase Implementation)

### Phase 1: Data Scale-Up Layer (Priority: CRITICAL)
**Problem**: N=7 clouds cannot support transformational claims

**Implementation Requirements:**
- Automated ingestion connectors for:
  - Full Herschel Gould Belt Survey archive
  - Full LoTSS/LOFAR DR2+ footprint  
  - Gaia DR3 (kinematic/distance cross-matching)
  - One non-Herschel comparison dataset (JCMT/SCUBA-2 or ALMA)
- Standardize to `ASTRA.CloudRecord` schema
- Target minimum: **N ≥ 30 independent clouds/regions**
- Strict train/holdout split (20% quarantined)
- Cryptographic hashing of holdout set

**Integration Points:**
- Replace: `astra_core/data_ingestion/basic_loader.py`
- Extend: `astra_core/data/cloud_database.py`
- New module: `astra_core/transformational/data_scale_layer.py`

**Acceptance Criteria:**
- [ ] ASTRA can ingest 3+ independent surveys without manual intervention
- [ ] Holdout set is cryptographically hashed and verified untouched
- [ ] Minimum N≥30 clouds achieved with documented power analysis

---

### Phase 2: Prior/Expectation Model (Priority: CRITICAL)
**Problem**: ASTRA reports agreement with known relations as "discoveries"

**Implementation Requirements:**
- Machine-readable knowledge base: `astra_priors.yaml`
- Encode established relations with uncertainties:
  - Larson's laws
  - ~0.1 pc filament width
  - Salpeter/Chabrier IMF slopes
  - Virial parameter distributions
- Machine-checkable predicates for each relation
- Automatic classification: confirmatory/underpowered/candidate-novel
- Power analysis module (minimum detectable effect)
- Automatic FDR correction (Benjamini-Hochberg)

**Integration Points:**
- New module: `astra_core/transformational/prior_knowledge_base.py`
- New module: `astra_core/transformational/power_analysis.py`
- Extend: `astra_core/scientific_discovery/enhanced_validation_pipeline.py`
- Configuration: `astra_priors.yaml`

**Acceptance Criteria:**
- [ ] Prior knowledge base with ≥10 established relations
- [ ] Automatic classification of results before narrative generation
- [ ] Power analysis attached to every statistical test
- [ ] FDR correction hardcoded as pipeline step

---

### Phase 3: Discovery Gate Skeleton (Priority: HIGH)
**Problem**: Empty "Discovery Demonstration" section, no actual bar

**Implementation Requirements:**
- 4-stage gate implementation:
  1. Statistical significance after correction
  2. Independent replication on holdout set
  3. Mechanistic plausibility
  4. Adversarial critique survival
- Timestamped immutable audit trail
- Programmatic enforcement (no "discovery" label without passing all 4)
- Lint-style check on generated manuscript text

**Integration Points:**
- New module: `astra_core/transformational/discovery_gate.py`
- Extend: `astra_core/scientific_discovery/enhanced_validation_pipeline.py`
- Hook: `astra_core/paper_generation/manuscript_builder.py`

**Acceptance Criteria:**
- [ ] IC5146 filament-width result correctly outputs "confirmatory" not "discovery"
- [ ] Audit trail records all 4 stages with timestamps
- [ ] Programmatic enforcement prevents "discovery" labels without passing
- [ ] Non-empty "Discovery Demonstration" section generated from logs

---

### Phase 4: Independent Evaluation Harness (Priority: HIGH)
**Problem**: Current ablation study likely self-scored and circular

**Implementation Requirements:**
- Fixed, pre-registered benchmark suite with ground truth
- Mix of real archival data + synthetic planted effects
- Automatic scoring grounded in ground truth
- Per-task raw results (not just aggregated percentages)
- Bonferroni/FDR correction across benchmark suite
- Variance across reruns reported

**Integration Points:**
- New module: `astra_core/transformational/evaluation_harness.py`
- New module: `astra_core/transformational/benchmark_suite.py`
- New module: `astra_core/transformational/synthetic_ground_truth.py`

**Acceptance Criteria:**
- [ ] Benchmark suite with ≥20 tasks (mix real + synthetic)
- [ ] Automatic scoring against ground truth
- [ ] Per-task raw results attached to ablation table
- [ ] Materially different (not uniform) numbers across reruns
- [ ] Variance reported, not hidden

---

### Phase 5: Mechanism-Search Module (Priority: MEDIUM)
**Problem**: Bare correlations without candidate physical explanations

**Implementation Requirements:**
- Symbolic regression component (PySR-based)
- Operates on residuals after known relations subtracted
- Proposes compact functional forms ranked by complexity-penalized fit
- Outputs candidate equation + plain-language physical mechanism
- Cross-checked against Prior knowledge base

**Integration Points:**
- New module: `astra_core/transformational/mechanism_search.py`
- Extend: `astra_core/transformational/discovery_gate.py`
- External: Install PySR library

**Acceptance Criteria:**
- [ ] Symbolic regression identifies at least one candidate mechanism
- [ ] Complexity-penalized ranking avoids overfitting
- [ ] Plain-language physical mechanism interpretation
- [ ] Cross-check against prior knowledge base

---

### Phase 6: Adversarial Critic (Priority: MEDIUM)
**Problem**: No independent falsification attempts

**Implementation Requirements:**
- Distinct process with sole objective: falsify or explain away findings
- Toolkit: alternative models, permutation tests, systematics checks
- Scored via synthetic injection (90% TPR on nulls, 90% TPR on planted effects)
- Rotating held-out synthetic test suite
- Measured against ground truth (not self-assessment)

**Integration Points:**
- New module: `astra_core/transformational/adversarial_critic.py`
- Extend: `astra_core/transformational/discovery_gate.py`
- Extend: `astra_core/transformational/evaluation_harness.py`

**Acceptance Criteria:**
- [ ] Critic identifies ≥90% of synthetic null results as "no genuine effect"
- [ ] Critic passes ≥90% of synthetic planted-effect datasets
- [ ] Rotating test suite ASTRA doesn't access during development
- [ ] Measured against ground truth, not self-assessment

---

### Phase 7: Autonomy Loop Controller (Priority: MEDIUM)
**Problem**: "Autonomy" means orchestration between LLM agents, not closed-loop science

**Implementation Requirements:**
- Explicit state machine:
  `PRIOR-CHECK → HYPOTHESIS-GENERATION → TEST-DESIGN → EXECUTION → DISCOVERY-GATE → KNOWLEDGE-BASE-UPDATE → NEXT-HYPOTHESIS`
- Hypothesis constraints:
  - Not already in Prior knowledge base
  - Falsifiable given available data
- Test design includes power analysis check
- Prior knowledge base auto-updates on discovery/confirmatory results
- Machine-readable log entry per full iteration

**Integration Points:**
- New module: `astra_core/transformational/autonomy_loop.py`
- Extend: `astra_core/transformational/prior_knowledge_base.py`
- Replace: `astra_core/scientific_discovery/discovery_coordinator.py`

**Acceptance Criteria:**
- [ ] 5+ full loop iterations unattended on held-out domain question
- [ ] Complete audit trail for each iteration
- [ ] No iteration reaches "discovery" without populated audit trail
- [ ] Prior knowledge base auto-updates

---

### Phase 8: Final Integration & Paper Regeneration (Priority: LOW)
**Problem**: Discovery Demonstration section remains empty

**Implementation Requirements:**
- Re-run full ablation study on Phase 7 system via Phase 4 harness
- Regenerate paper's Discovery Demonstration section from real audit logs
- Update all figures to reflect new rigorous standards
- Update claims to match actual validation levels

**Integration Points:**
- Extend: `astra_core/paper_generation/manuscript_builder.py`
- Update: All paper sections and figures

**Acceptance Criteria:**
- [ ] Ablation table with per-task raw results
- [ ] Non-empty Discovery Demonstration section from real logs
- [ ] All claims match validation levels achieved
- [ ] Figures reflect new rigorous standards

---

## Integration with Existing System

### Components to RETAIN (Re-scoped):
1. **Multi-Mind Orchestration**: Scheduling/coordination substrate, not discovery source
2. **LeapCore**: Efficiency and coverage measurement
3. **MORK**: Ontology structure for Prior knowledge base
4. **Enhanced Validation Pipeline**: Upgrade to use Discovery Gate

### Components to REPLACE:
1. **Basic Data Loader**: Replace with Data Scale-Up Layer
2. **Self-Graded Ablations**: Replace with Independent Evaluation Harness
3. **Manual Discovery Classification**: Replace with Discovery Gate
4. **Open-Ended Hypothesis Generation**: Replace with Constrained Autonomy Loop

### New File Structure:
```
astra_core/
├── transformational/
│   ├── __init__.py
│   ├── data_scale_layer.py          # Phase 1
│   ├── prior_knowledge_base.py     # Phase 2
│   ├── power_analysis.py           # Phase 2
│   ├── discovery_gate.py           # Phase 3
│   ├── evaluation_harness.py       # Phase 4
│   ├── benchmark_suite.py          # Phase 4
│   ├── synthetic_ground_truth.py   # Phase 4
│   ├── mechanism_search.py         # Phase 5
│   ├── adversarial_critic.py       # Phase 6
│   └── autonomy_loop.py            # Phase 7
├── scientific_discovery/
│   ├── enhanced_validation_pipeline.py  # UPGRADE: Use Discovery Gate
│   ├── enhanced_discovery_coordinator.py  # UPGRADE: Use Autonomy Loop
│   └── genuine_discovery_swarm.py  # RETAIN: For exploration guidance
└── config/
    └── astra_priors.yaml           # New: Prior knowledge base
```

---

## Implementation Priority

If time before resubmission is limited:

**Do First (Critical for Resubmission):**
- ✅ Phase 1: Data Scale-Up (N≥30, holdout split)
- ✅ Phase 2: Prior/Expectation Model (prevent confirmatory = discovery)
- ✅ Phase 3: Discovery Gate (actual bar for claims)
- ✅ Phase 4: Independent Evaluation (fix circular ablations)

**Present as Future Work:**
- ⏳ Phase 5: Mechanism-Search Module
- ⏳ Phase 6: Adversarial Critic
- ⏳ Phase 7: Autonomy Loop Controller
- ⏳ Phase 8: Full Paper Regeneration

Phases 1-4 alone resolve the specific referee-facing problems even before the advanced modules are built.

---

## Non-Negotiable Ground Rules

1. **No Self-Grading**: Replace with held-out ground truth or external review
2. **No Discovery Without Gate**: Programmatic enforcement of 4-stage gate
3. **Ablation Path from Day One**: Every component switchable and independently re-scorable
4. **Small-N Claim Capping**: No "significant" label from N<20 without power analysis

---

## Expected Impact

**Current System**:
- N=7 clouds, self-graded ablations, empty discovery section
- Confirmatory statistics narrated as discovery
- Circular evaluation, no independent replication

**Post-Integration (Phases 1-4)**:
- N≥30 clouds, train/holdout split, independent replication
- Prior knowledge base prevents confirmatory = discovery
- 4-stage discovery gate with audit trail
- External evaluation with synthetic ground truth
- Rigorous anomaly detection with independent verification

**Post-Integration (All Phases)**:
- Symbolic mechanism search on residuals
- Adversarial critic with synthetic injection testing
- Closed-loop autonomy with prior-guided hypothesis generation
- Self-updating knowledge base
- Complete audit trails for all claims

---

## Timeline Estimate

- **Phase 1**: 2-3 weeks (data ingestion, standardization, holdout setup)
- **Phase 2**: 1-2 weeks (prior knowledge base, power analysis)
- **Phase 3**: 1 week (discovery gate, audit trail)
- **Phase 4**: 2-3 weeks (benchmark suite, synthetic ground truth)
- **Phase 5**: 2-3 weeks (symbolic regression, mechanism search)
- **Phase 6**: 2-3 weeks (adversarial critic, synthetic testing)
- **Phase 7**: 3-4 weeks (autonomy loop, knowledge base updates)
- **Phase 8**: 1-2 weeks (final integration, paper regeneration)

**Critical Path (Phases 1-4)**: 6-8 weeks
**Full Implementation**: 16-22 weeks

---

## Success Metrics

1. **Validation Quality**: ≥90% of synthetic nulls correctly rejected, ≥90% of synthetic effects correctly detected
2. **Discovery Rigor**: 0% of "confirmatory" results mislabeled as "discoveries"
3. **Ablation Credibility**: materially different numbers across reruns, variance reported
4. **Sample Size**: N≥30 independent clouds/regions with documented power analysis
5. **Replication Rate**: ≥50% of candidates replicate on holdout set

---

## Next Steps

1. Review and approve this implementation plan
2. Set up data ingestion connectors (Phase 1)
3. Build prior knowledge base structure (Phase 2)
4. Implement discovery gate skeleton (Phase 3)
5. Create evaluation harness with synthetic ground truth (Phase 4)

---

**Note**: This architecture moves ASTRA from *confirmatory statistics narrated as discovery* to *rigorous anomaly detection with independently-verified novelty and mechanism*. This is a genuine upgrade, not a guarantee of Eureka-level breakthroughs.