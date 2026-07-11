# ASTRA Architecture Implementation Guide
## Toward Rigorous Autonomous Discovery Behaviour

**Purpose of this document:** a concrete, buildable specification for architectural changes to ASTRA, intended to close the gap between "sophisticated statistical automation with a discovery narrative" and genuine, defensible discovery behaviour within its domain (star formation / molecular cloud structure from Herschel/LOFAR data, extensible to other survey-scale astronomical datasets).

This guide assumes ASTRA's current state as described in the RASTI review cycle (V7.11–V7.23):
- Multi-Mind Orchestration, LeapCore, MORK, and the Autocatalytic Self-Compiler are implemented but **not shown to change output quality** relative to a baseline statistical pipeline.
- The validation study (partial correlation, logistic regression, DBSCAN, temperature-density fitting) is reproducible in a few hundred lines of plain Python.
- N=7 clouds is too small to support strong claims; no multiple-comparison correction was applied.
- The "Discovery Demonstration" section was structurally empty; figures labelled "ASTRA Discovery 1–3" were added without corresponding analysis, and at least one (filament width vs. Arzoumanian 2011) is an *expected* replication, not a discovery.
- Ablation numbers were suspiciously uniform and likely self-scored (circular evaluation).

**Design philosophy for this guide:** every new module must earn its place by changing a *measurable output*, verified by a process that ASTRA itself cannot grade. Narrative sophistication is explicitly excluded as a success criterion. "Autonomy" is treated as a property of a closed *hypothesis → test → validation → knowledge-update* loop, not as a property of how many orchestrating agents are involved.

---

## 0. Non-Negotiable Ground Rules for This Implementation

1. **No self-grading.** Any module that scores ASTRA's own output (ablations, discovery confidence, quality metrics) must be replaced or supplemented with scoring that ASTRA cannot see or influence during the run being scored. Where full external human review isn't feasible per-run, use held-out ground truth (known physical relations, synthetic injected signals) as the grader.
2. **No discovery claim without a gate.** A finding may not be labelled "discovery" internally or externally until it passes the Discovery Gate (Section 4). Below that bar it is labelled "candidate finding" or "confirmatory result."
3. **Every architectural component must have an ablation path from day one.** If a component cannot be cleanly switched off and independently re-scored, it should not be built yet.
4. **Small-N outputs are capped in claim strength regardless of p-value.** No component may output a "significant" or "novel" label from N < ~20 independent units without an explicit power-analysis pass (Section 3).

---

## 1. Target Architecture Overview

```
                         ┌───────────────────────────┐
                         │   Data Ingestion & Scale   │  (Sec. 2)
                         │  Layer (multi-survey)      │
                         └─────────────┬─────────────┘
                                       ▼
                         ┌───────────────────────────┐
                         │  Prior/Expectation Model    │  (Sec. 3)
                         │  (formal knowledge base)    │
                         └─────────────┬─────────────┘
                                       ▼
              ┌────────────────────────────────────────────┐
              │           Inference Core                     │
              │  ┌───────────────┐   ┌────────────────────┐ │
              │  │ Correlational  │   │  Mechanism-Search   │ │  (Sec. 3, 5)
              │  │ Analysis       │   │  (symbolic regress.)│ │
              │  └───────────────┘   └────────────────────┘ │
              └─────────────────────┬────────────────────────┘
                                    ▼
                         ┌───────────────────────────┐
                         │   Discovery Gate            │  (Sec. 4)
                         │  (statistical + replication │
                         │   + adversarial critique)   │
                         └─────────────┬─────────────┘
                                       ▼
                         ┌───────────────────────────┐
                         │  Knowledge-Base Update &    │  (Sec. 6)
                         │  Autonomy Loop Controller   │
                         └─────────────┬─────────────┘
                                       ▼
                         ┌───────────────────────────┐
                         │  Independent Evaluation     │  (Sec. 7)
                         │  Harness (blind ablations)  │
                         └───────────────────────────┘
```

Existing components (Multi-Mind Orchestration, LeapCore, MORK) are **retained but re-scoped**: they become the scheduling/coordination substrate that runs the modules below, not sources of discovery claims in their own right. Their contribution should be measured as *efficiency and coverage* (do more hypotheses get tested per unit compute, do more of the search space get covered) rather than *discovery quality*, which is what the Discovery Gate measures independently.

---

## 2. Data Scale-Up Layer

**Problem addressed:** N=7 clouds cannot support transformational claims regardless of architecture quality.

**Implementation tasks:**
- Build automated ingestion connectors for at least: full Herschel Gould Belt Survey archive, full LoTSS/LOFAR DR2+ footprint, Gaia DR3 (for kinematic/distance cross-matching), and one non-Herschel comparison dataset (e.g. JCMT/SCUBA-2 or ALMA archival continuum) to allow independent replication on a genuinely different instrument.
- Standardise all ingested products to a common `ASTRA.CloudRecord` schema: physical units, calibration provenance, angular resolution, distance estimate with uncertainty, and a machine-readable citation to the originating survey paper.
- Target minimum sample size before any population-level statistical claim is attempted: **N ≥ 30 independent clouds/regions**, with a documented rationale in code (not just prose) for why this N was judged sufficient (see Section 3, power analysis).
- Maintain a strict train/holdout split at ingestion time: a fixed subset of clouds (e.g. 20%) is quarantined and never touched during hypothesis generation, reserved exclusively for the replication step in the Discovery Gate.

**Acceptance criterion:** ASTRA can ingest, standardise, and hold out data from at least 3 independent surveys without manual intervention, and the holdout set is cryptographically hashed/logged so it can be verified untouched at Discovery Gate time.

---

## 3. Prior/Expectation Model (Formal Knowledge Base)

**Problem addressed:** ASTRA currently reports agreement with known relations (e.g. filament width ≈ universal 0.1 pc) as if it were a finding, rather than recognising it as the *expected* outcome.

**Implementation tasks:**
- Build a machine-readable knowledge base, `astra_priors.yaml` (or a graph DB if preferred — this maps naturally onto MORK's existing ontology structure), encoding:
  - Established scaling relations relevant to the domain (e.g. Larson's laws, the ~0.1 pc filament width, Salpeter/Chabrier IMF slopes, virial parameter distributions) with their quoted values **and uncertainties**, and citations.
  - For each relation, a machine-checkable predicate: given new data, compute whether the result is *consistent with*, *in tension with*, or *significantly deviant from* the prior, with the deviation expressed in units of the prior's own uncertainty (not just a point comparison).
- Any inference-core output must be automatically checked against this knowledge base before it can proceed to the Discovery Gate. Outputs consistent with prior (within its quoted uncertainty) are auto-labelled "confirmatory" and routed to a separate, lower-stakes reporting track — they should never again be mislabelled "ASTRA Discovery N."
- Build a formal power-analysis module that runs *before* any statistical test is finalised: given the sample size, effect size of interest, and number of planned comparisons, compute the minimum detectable effect and attach it to every result. Any result whose effect size is near or below the minimum detectable effect is flagged, not reported as significant.
- Multiple-comparison correction (Benjamini-Hochberg FDR at minimum) must be applied automatically across all tests run in a given analysis session — this must be a hard-coded pipeline step, not a discretionary choice left to the reviewer-facing writeup.

**Acceptance criterion:** Given a new dataset, ASTRA automatically classifies every result as confirmatory / underpowered / candidate-novel *before* any narrative text is generated, and this classification is reproducible by re-running the same code independent of any LLM-generated commentary.

---

## 4. The Discovery Gate

**Problem addressed:** the empty "Discovery Demonstration" section and the self-scored ablations reflect the absence of any actual bar for calling something a discovery.

A candidate result may only be labelled a "discovery" if it passes **all four** of the following, logged with a timestamped, immutable audit trail:

1. **Statistical significance after correction** (from Section 3), computed on the training/discovery subset.
2. **Independent replication** on the quarantined holdout subset (Section 2) — the same effect must appear, at reduced but still meaningful significance, on data never seen during hypothesis generation.
3. **Mechanistic plausibility** — the Mechanism-Search module (Section 5) must propose at least one candidate physical explanation that is not immediately contradicted by known physics; a bare correlation with no candidate mechanism is downgraded to "candidate finding, mechanism unknown," not "discovery."
4. **Adversarial critique survival** — an independently-scoped critic process (Section 5) has attempted and failed to explain the result away via confounds, selection effects, calibration artefacts, or alternative models.

**Implementation tasks:**
- Build this as an actual pipeline gate in code (e.g. `discovery_gate.evaluate(candidate) -> {"status": "discovery"|"candidate"|"confirmatory"|"rejected", "audit_trail": [...]}`), not a prose checklist applied manually before submission.
- The audit trail must record: which data were used at each step, what the critic process attempted, and why it failed or succeeded — this becomes the actual content of a non-empty "Discovery Demonstration" section, generated from logs rather than written after the fact.
- No text-generation step (paper drafting, figure captions) may reference the word "discovery" for a result that hasn't passed all four gates. This should be enforced programmatically (a lint-style check on generated manuscript text against the gate's audit log), not left to manual proofreading.

**Acceptance criterion:** for the current IC5146 filament-width result, running it through this gate should correctly output "confirmatory" (since it replicates an expected value), not "discovery" — this is a good regression test for the gate itself.

---

## 5. Mechanism-Search and Adversarial Critic Modules

**Mechanism-Search:**
- Add a symbolic-regression component (e.g. built on PySR or an equivalent open-source symbolic regression library) that operates specifically on the *residuals* after known relations (from the Prior model) are subtracted out.
- Its job is narrow: propose compact functional forms that explain residual structure, ranked by a complexity-penalised fit quality (to avoid overfitting noise with an arbitrarily complex expression).
- Output should be a candidate equation plus a plain-language statement of what physical mechanism (if any) it resembles (e.g. "consistent with magnetic support scaling as B∝ρ^k") — cross-checked against the Prior knowledge base for whether such a mechanism is already known, extends a known mechanism, or is genuinely unaccounted for.

**Adversarial Critic:**
- Implement as a distinct process (can use the existing Multi-Mind framework for this — this is the correct use of a "second mind") whose sole objective function is to falsify or explain away a candidate finding.
- Its toolkit should include: reruns of the analysis with (a) alternative statistical models, (b) randomly permuted/shuffled labels (a permutation-test sanity check that the specific finding isn't an artefact of the pipeline itself), (c) known instrumental/calibration systematics for the relevant survey, and (d) a check for whether the finding could result from a subset of anomalous objects rather than a population-level effect.
- Score the critic not by ASTRA's own assessment but by **injected synthetic tests**: periodically feed the critic known-null datasets (no real signal, by construction) and known-planted-signal datasets, and measure its true positive/false negative rate on catching or missing them. This is the fix for the circularity problem the review identified — the critic's competence is measured against ground truth the researcher controls, not against ASTRA's self-assessment.

**Acceptance criterion:** the critic module correctly identifies at least 90% of synthetic null results as "no genuine effect" and correctly passes at least 90% of synthetic planted-effect datasets, measured on a rotating held-out synthetic test suite that ASTRA does not have access to during development.

---

## 6. Autonomy Loop Controller

**Problem addressed:** "autonomy" currently seems to mean orchestration between LLM agents, not a genuine closed-loop scientific process.

**Implementation tasks:**
- Define the autonomy loop explicitly as a state machine:
  `PRIOR-CHECK → HYPOTHESIS-GENERATION → TEST-DESIGN → EXECUTION → DISCOVERY-GATE → KNOWLEDGE-BASE-UPDATE → NEXT-HYPOTHESIS`
- Hypothesis generation should be constrained to produce hypotheses that are (a) not already resolved in the Prior knowledge base, and (b) falsifiable given the data ASTRA can access — reject or deprioritise hypotheses that fail either check before any compute is spent testing them.
- Test design should include an automatic check of whether the currently ingested data (Section 2) has sufficient power (Section 3) to test the hypothesis at all; if not, the loop should generate a data-acquisition/ingestion request rather than running an underpowered test anyway.
- On a result reaching "discovery" or "confirmatory" status, the Prior knowledge base (Section 3) is automatically updated — this is what makes the loop genuinely autonomous over time: later hypotheses are generated against an evolving, self-updated picture of the field rather than a static prior written once by a human.
- Each full loop iteration should produce a structured, machine-readable log entry (hypothesis, test, data used, gate outcome, knowledge-base delta) — this log *is* the raw material for the "Discovery Demonstration" section, and should make it structurally impossible to ship an empty results section again.

**Acceptance criterion:** ASTRA can run at least 5 full loop iterations unattended on a held-out domain question, producing a complete audit trail for each, with no iteration reaching "discovery" status without a populated audit trail satisfying Section 4.

---

## 7. Independent Evaluation Harness

**Problem addressed:** the current ablation study is likely self-scored and circular; the round-numbered percentages (45.0%, 40.0%, 34.9%...) are not credible as raw empirical measurements.

**Implementation tasks:**
- Build a harness that runs full-architecture ASTRA and each ablated variant (no Multi-Mind, no LeapCore, no MORK prior integration, no Mechanism-Search, no Adversarial Critic) against a **fixed, pre-registered benchmark suite** of tasks with known ground-truth answers (a mix of real archival data with independently-published results, and synthetic data with planted effects of known size).
- Scoring must be automatic and grounded in ground truth (did the variant correctly find the planted effect, correctly reject the null, correctly replicate the published result) — not a composite Likert-style quality score assigned by any part of ASTRA itself.
- Run this harness on a schedule independent of paper-writing deadlines, and store raw per-task results (not just aggregated percentages) so an external reviewer or referee can inspect the actual task-level pass/fail data, not just a summary table.
- Bonferroni or FDR-correct across the benchmark suite's multiple comparisons before reporting any component as making a statistically distinguishable contribution.

**Acceptance criterion:** the resulting ablation table can be handed to a referee with per-task raw results attached, and reproduces materially different (not suspiciously uniform) numbers when rerun — variance across reruns should itself be reported, not hidden.

---

## 8. Suggested Implementation Order

| Phase | Focus | Depends on | Rough effort |
|---|---|---|---|
| 1 | Data Scale-Up Layer (Sec. 2) | — | Medium |
| 2 | Prior/Expectation Model + power analysis + FDR correction (Sec. 3) | Phase 1 | Medium |
| 3 | Discovery Gate skeleton, wired to existing (unchanged) inference core (Sec. 4) | Phase 2 | Small |
| 4 | Independent Evaluation Harness with synthetic ground truth (Sec. 7) | Phase 1 | Medium |
| 5 | Mechanism-Search module (Sec. 5) | Phase 3 | Large |
| 6 | Adversarial Critic, scored via synthetic injection (Sec. 5) | Phase 4, 5 | Large |
| 7 | Autonomy Loop Controller (Sec. 6) | Phases 3–6 | Large |
| 8 | Re-run full ablation study on Phase 7 system via Phase 4 harness; regenerate paper's Discovery Demonstration section from real audit logs | All above | Medium |

Phases 1–4 alone would already resolve the specific referee-facing problems from the current RASTI review cycle (empty discovery section, self-scored ablations, unconnected small-N claims) even before Mechanism-Search, Adversarial Critic, or the full Autonomy Loop are built. If time before resubmission is limited, prioritise Phases 1–4 and present Phases 5–7 explicitly as "future work now supported by the architecture," which is an honest and defensible framing a referee can accept.

---

## 9. What This Guide Deliberately Does Not Promise

This architecture is designed to move ASTRA from *confirmatory statistics narrated as discovery* to *rigorous anomaly detection with independently-verified novelty and mechanism*. That is a genuine and valuable upgrade. It is **not** a guarantee of Eureka-level conceptual breakthroughs of the kind that reframed physics historically (special relativity, quantum mechanics) — no existing architecture, published or otherwise, has a demonstrated method for producing those on demand, and any claim to the contrary should be treated with the same scepticism ASTRA's own Adversarial Critic is being built to apply to its outputs.
