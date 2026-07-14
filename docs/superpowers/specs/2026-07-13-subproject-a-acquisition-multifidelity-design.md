# Sub-project A — Acquisition + Multi-fidelity (Design Spec)

- **Date:** 2026-07-13
- **Status:** Approved (design); pending implementation
- **Scope:** Features 2 (DeepScientist-style Bayesian-optimization / UCB acquisition) + 3 (multi-fidelity promotion cascade + PROCEED/REFINE/PIVOT), applied to the **Phase-2 claim search** only.
- **Out of scope here:** Sub-project B (cross-run learning memory — MetaClaw / IdeaGraph / PromptEvolver) and Sub-project C (astronomy data lake + literature-mined action space) are separate sub-projects with their own spec → plan → implement cycles. Build order agreed: **A first, then C.**

---

## 1. Motivation

ASTRA's two-gate EVALUATE is a **filter**, not a **selector**: it answers "is this claim real?" but never "which of N candidates deserves the next sandbox run?" Today `run_claim_search.main()` generates one candidate and evaluates it immediately, greedily, with no notion of budget or exploration.

Sub-project A turns the loop into a **budget-aware selector** with **staged fidelity**, borrowing two ideas:

- **DeepScientist** — formalize discovery as `argmax f(I)` over a candidate frontier, with an LLM surrogate scoring each candidate on ⟨utility, quality, exploration⟩ and a UCB acquisition choosing the next experiment.
- **AutoResearchClaw** — a PROCEED/REFINE/PIVOT failure taxonomy that treats failed experiments as information rather than dead-ends.

Both slot in *behind* the existing two-gate EVALUATE. They only change **which** candidates get fully evaluated and add a stability sub-gate. They do **not** change how survivors are stored.

## 2. Hard constraint (read first)

The single write-chokepoint `discovery_store.append_verified()` (`discovery_store.py:154`, gated by `has_machine_verification()` at `:52`) is **inviolable**. Sub-project A must:

- never bypass or weaken it,
- never make "fiction" writeable,
- keep `astra_core/tests/test_discovery_chokepoint.py` and `astra_core/tests/test_claim_gates.py` passing **unchanged**.

Survivors continue to flow through the exact existing path: `_emit()` → `evolved_discoveries.json` → supervisor `_ingest()` → `consume_evolved_discoveries()` → `append_verified()`.

## 3. Decisions (locked)

| Decision | Choice | Reason |
|---|---|---|
| Phase scope | Phase-2 claims only | The "which candidate next" gap is sharpest here; Phase-1 photo-z already has a MAP-Elites archive for diversity. |
| Compute budget per step | Batch-score **K=8** candidates, sandbox **top-1** | Per-step sandbox cost ≈ today, +1 cheap batched LLM call, much smarter selection. |
| Exploration (κ) signal | **LLM-judged novelty** | Self-contained — no embeddings, no Sub-project B infrastructure. The surrogate estimates how unexplored each candidate is as one of three scores. |
| Structure | New module `acquisition.py` + `--acquisition ucb` flag | Isolates new logic, unit-testable, preserves the old loop as default fallback. |
| Tier-2 stability | Hard sub-gate, **k=5** bootstrap | Runs only on Gate-1 survivors; guards against a lucky single split. |

## 4. Integration map (reference)

Relevant files (all under `astra_core/scientific_discovery/evolved_analysis/` unless noted):

- `run_claim_search.py` — `main()` loop `:266-280`; `two_gate_eval()` `:102`; `gate1_run()` `:59`; `_emit()` `:171`.
- `claim_eval_worker.py` — sandboxed subprocess; `main()` `:46`; resource limits `:31-43`.
- `claim_task.py` — `TASK_SYSTEM` prompt `:65-86`; `gate1_significant()` `:101`; `EFFECT_MIN=0.30`/`PMAX=1e-3` `:35-36`.
- `claim_gates.py` — `triviality_check` `:126`; `consistency_check` `:176`; `holdout_distinct_check` `:213`; `bonferroni_pmax` `:274`.
- `novelty_gate.py` — `check_novelty()` `:289` (Gate 2).
- `proposer.py` — `LLMProposer.propose()` `:156` (the single central prompt builder).
- `safety.py` — `check_source()` `:90`; `ALLOWED_IMPORT_ROOTS` `:37`.
- `real_data.py` — `fetch()` `:68`; `load_split()` `:90`.
- `llm_gateway.py` — `LLMGateway.complete()` `:54`; decoupled loader `_llm.py` (importlib, avoids `astra_core/__init__` deadlock).
- `astra_core/scientific_discovery/discovery_store.py` — the chokepoint.
- `astra_core/tests/test_discovery_chokepoint.py`, `astra_core/tests/test_claim_gates.py` — regression contract.

Key facts that shape the design:
- **No claim queue exists.** `main()` generates-and-evaluates one candidate immediately.
- **Failures are discarded** (logged only).
- **`two_gate_eval()` already orchestrates sub-gates** (triviality/consistency/holdout) after Gate-1 — Tier-2 stability joins them.
- **`gate1_run()` is a subprocess call** — bootstrap Tier-2 = k subprocess runs, paid only by survivors.

## 5. Architecture

### 5.1 New loop data flow (`--acquisition ucb`)

```
for step in range(steps):
  1. Batch-propose K=8:        proposer.propose() × 8 (LLM stochasticity + distinct inspiration subsets yield diversity); drop None results
  2. Tier-0 (no sandbox):      surrogate.score_batch(8) → 8 × ⟨utility, quality, exploration⟩
  3. UCB select:               argmax(w_u·utility + w_q·quality + κ·exploration) → top-1 index
  4. Tier-0 reject:            if winner.quality < TIER0_QUALITY_FLOOR → PIVOT, continue (no sandbox spent)
  5. Tier-1 (unchanged):       two_gate_eval(winner) → gate1_run + triviality/consistency/holdout
  6. Tier-2 (new):             if Gate-1 + subgates pass → stability_check(bootstrap k=5); fail → both_pass=False
  7. Gate-2 + _emit():         unchanged; survivors still flow through append_verified()
  8. PIVOT/REFINE:             track consecutive Gate-1 fails; ≥ REFINE_LIMIT → re-seed parent
```

### 5.2 New module: `acquisition.py`

```python
@dataclass
class SurrogateScore:
    utility: float      # 0-1: scientific value if the claim holds
    quality: float      # 0-1: likelihood it is well-formed + passes gates
    exploration: float  # 0-1: LLM-judged how unexplored this region is
    reasoning: str

def score_batch(candidates, context) -> list[SurrogateScore]:
    """One batched gateway call: K (claim, source) pairs in → K score-triples out.
    Strict-JSON output; any malformed entry defaults to a low score; never raises."""

def ucb_acquisition(scores, kappa=1.0, w_u=0.4, w_q=0.4) -> int:
    """Return argmax over acquisition = w_u*utility + w_q*quality + kappa*exploration."""

TIER0_QUALITY_FLOOR = 0.2   # winner below this → PIVOT instead of sandboxing

class AcquisitionLoop:
    """Drives steps 1-8 above. Constructed with a proposer, the existing
    two_gate_eval, a surrogate, and tunables (K, kappa, k_bootstrap, floors).
    Emits through the unchanged _emit() path."""
```

**Surrogate inputs:** each candidate's **CLAIM string + `run_claim` source + parent diagnostics**. It predicts *before* the sandbox runs (cheap pre-eval of the expensive `f(I)`). Uses `llm_gateway` via `_llm.py`.

**Surrogate output contract:** strict JSON, one object per candidate with `utility`, `quality`, `exploration` (each 0-1) and `reasoning` (≤1 line). Defensive parse: malformed → all-zeros score (so it loses UCB, never crashes the loop).

### 5.3 Tier-2 stability gate (`claim_gates.py`)

```python
def stability_check(src, seed, k=5, delta=0.10) -> tuple[bool, str]:
    """k bootstrap resamples of train+eval; require effect stable across resamples
    (std < delta AND every resample clears EFFECT_MIN). Guards against a lucky
    single split. Called from two_gate_eval() ONLY after Gate-1 + triviality +
    consistency + holdout all pass, so the k subprocess runs are paid only by survivors."""
```

Result recorded into the existing `gate` evidence dict (extra provenance). `gate` is already an accepted evidence key, so this does **not** change the chokepoint contract.

### 5.4 PIVOT/REFINE lineage (in-memory, no store)

```python
consecutive_fails = 0
REFINE_LIMIT = 5
# Gate-1 fail → consecutive_fails += 1; if >= REFINE_LIMIT → re-seed parent (PIVOT), reset
# Gate-1 pass → consecutive_fails = 0; parent ← winner
# PIVOT re-seeds from the best Gate-1-passing candidate seen this run, or NAIVE_CLAIM_SEED if none yet.
```

AutoResearchClaw's PROCEED/REFINE/PIVOT distilled to loop state. No persistent failure store (that was Sub-project B, dropped), so this is per-run in-memory only.

## 6. Backward compatibility

- `--acquisition none` (default) = today's exact loop. **All existing tests pass unchanged.**
- `--acquisition ucb` enables the new path. Tunables exposed as CLI flags: `--batch-k` (default 8), `--kappa` (1.0), `--bootstrap-k` (5), `--tier0-floor` (0.2), `--refine-limit` (5).
- Verification block gains only an optional `stability` sub-dict inside `gate`. The five accepted evidence keys are unchanged; `has_machine_verification()` behavior is unchanged.

## 7. Chokepoint-safety analysis

| Risk | Mitigation |
|---|---|
| New path writes fiction | It cannot — it emits through the **unchanged** `_emit()`, which writes only `both_pass` survivors, which the supervisor ingests via the **unchanged** `consume_evolved_discoveries()` → `append_verified()`. |
| Surrogate LLM hallucinates a "pass" | The surrogate only **selects** candidates; it never certifies. Certification still requires the real Gate-1 sandbox significance test + sub-gates + Gate-2. A bad surrogate wastes compute or mis-ranks — it can never inject a false discovery. |
| Tier-2 stability rejects a real result | That is a false-negative, not a fiction risk. Conservative by design (bootstrap guards against overclaiming). |
| New `stability` field breaks the chokepoint | `has_machine_verification()` needs ≥1 of `{program_hash, metric_name, held_out_test_value, gate, real_data_result}`; `stability` nests inside `gate`. No change to acceptance. |

**Net: the worst A can do is be inefficient (bad ranking) or over-conservative (spurious Tier-2 rejects). It cannot create fiction.**

## 8. Testing (TDD, written before/with implementation)

New `astra_core/tests/test_acquisition.py`:
1. `score_batch` parses strict JSON into `SurrogateScore`; a malformed entry → low score, no exception.
2. `ucb_acquisition` returns the correct argmax across a range of κ (κ→0 favours pure exploitation; κ large favours exploration).
3. Tier-0 reject fires only when the UCB winner is below `TIER0_QUALITY_FLOOR`.
4. `stability_check` rejects an unstable effect (high cross-resample std), passes a stable one. `gate1_run` mocked.
5. PIVOT fires after `REFINE_LIMIT` consecutive Gate-1 fails (proposer + `two_gate_eval` mocked); parent is re-seeded.
6. End-to-end `AcquisitionLoop` drives steps 1–8 with mocks, emitting only true `both_pass` survivors.
7. **Regression:** `test_discovery_chokepoint.py` and `test_claim_gates.py` green, unmodified.

## 9. Out of scope / future

- **Sub-project C (data lake)** — built next, after A is implemented and green. A's surrogate + UCB give C a natural ranking surface (which dataset/claim to spend compute on).
- **Sub-project B (learning memory)** — dropped from this round. If revisited, its failure log would feed A's PIVOT/REFINE and surrogate context, and IdeaGraph embeddings would replace LLM-judged exploration with a true novelty term.
- **Phase-1 acquisition** — A targets Phase-2 only. Phase-1 photo-z already uses `MAPElitesArchive`; unifying the two under one acquisition abstraction is a later option.
