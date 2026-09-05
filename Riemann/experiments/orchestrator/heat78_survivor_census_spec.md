# heat78 — SURVIVOR-SET CENSUS, protocol draft v0 (NOT preregistered; offered to m2/m3 before any scored run)

Origin: SAPIENS-4 §2 (exchange `4beb626`) — N2's second branch. The witness *detects*
(four instruments); the survivor set *classifies*. Adjudicated m1: ENDORSED as the next
major lane (NOTES Addendum 9), sequenced after the birth-locus grid frees its core.
Machine-prefixed letter to follow (after m2 answers m1-L155/L155a — this lane builds on
their family; counterparty rule).

**One correction to NOTES Addendum 9, recorded here:** the census does NOT re-use the
birth-locus grid's site generator (that is the zeta2_C D-family, a different object). It
re-uses the COMPOSED-KERNEL machinery: the heat77 configuration generator (gap/fraction/
removal/insertion) and the heat70/heat72k M-ladder kernel export (genomes s1–s3 at M8/M64,
committed `machine1_heat70_genomes_m8_m64.json`; K_T200/G_raw by the committed export path,
M64 method already proven in the m1-L123 M64 re-derivation). The grid sequencing was CPU
cap arithmetic, nothing more.

## 1. The question, in this world's own currency

An off-line configuration (paired displacement δ ≠ 0 straddling the critical line) is
built on the composed kernel. A FINITE instrument = the (M, T) truncation of the operator.
The eigensolve of the finite matrix is exact (dps 45, cholesky→eigsy, cross-scheme
quadrature agreement 12+ s.f.) — the approximation under test is the MATERIX SIZE and the
ZERO-SIDE CUT, not the arithmetic. A configuration **evades** at (M, T) if the finite
instrument's ground eigenvalue stays benign there; it is **detected** when λ_min falls
below threshold. The census asks: which evaders survive as M grows 8 → 64, and what do
the survivors have in common.

## 2. Configuration space (fixed, enumerable, pre-stated)

Single-leg configurations (the additivity-defect two-leg construction is a second-order
question; v1 asks about off-line-ness per se):

- gaps k ∈ {0,…,7} (between zeros #(k+1), #(k+2); zetazero-numbered, exact)
- insertion fraction φ ∈ {2/8, 4/8, 6/8}
- displacement δ ∈ {0.05, 0.10, 0.20, 0.30} + δ = 0 controls (one per gap, φ = 4/8)

Total: 8 × 3 × 4 = 96 displaced configs + 8 on-line controls.
Kernel per config: K_S(δ) = K_T200 − Gram(z_{k+1}) − Gram(z_{k+2}) + quad_ex(g, δ),
g = z_{k+1} + φ·(z_{k+2} − z_{k+1}).

## 3. Instrument ladder

- M ∈ {8, 64} (genomes s1/M8 + s1/M64, same family — the ladder is the basis size)
- T = 200 fixed (zero-side Im ≤ 200; T-extension ruled unnecessary for monotone PSD-shell
  structure in §88bg — if the M-thinning shows structure, T enters v2)
- exact eigensolve per config at dps 45, same architecture as heat77b

## 4. Verdict rule (pre-stated)

- **FIRES** at (M, T) iff λ_min < −1e-12 (floor clears cross-scheme quadrature agreement
  by ≥ 6 orders and any measured cancellation depth artifact; it is NOT the old Q-world
  ε_cert = 1e-3, which lives in the μ-function grid instrument and does not transfer)
- **EVADER** iff λ_min ≥ −1e-12 at genuine δ > 0
- Instrument self-check (run red if violated): NO δ = 0 control fires at any M

## 5. Anchored import — trial #1 (statistical mechanics; one page, one import, discard freely)

The configuration space is the ensemble; the survivor count N(M) is a partition-like
statistic; thinning as M grows is the ensemble cooling. Two pre-stated families for the
thinning law (v1 can only measure direction and flips — family discrimination needs a
third M or a δ-continuum, and says so):

- (i) **exponential**: log N(M) linear in M — independent basis modes, large-deviation
  reading; each added mode multiplies the hiding probability by a constant factor
- (ii) **power-law / saturation**: N(M) ~ M^−α or flat — correlated modes; the Gram
  structure couples basis functions so strongly that added dimensions stop adding
  detection power (an RH-adjacent statement about the composed object if it holds)

The v1 deliverable is the FLIP SET (configs evading at 8, detected at 64) plus the
GEOMETRY of survivors (γ-location, PT = ‖P‖_G/gap, f sign) — "what the survivors have in
common". The thinning-law fit is v2's unless M = 128 joins.

## 6. Pre-registered outcomes (bound before the scored run)

- (a) ALL displaced configs fire already at M = 8 (empty survivor set from the start):
  the witness is total on this family; branch 2 answered at the first rung; record and
  close, no escalation
- (b) SOME evaders at M = 8: the flip set 8 → 64 is the measurement. Sub-cases: survivors
  = exactly the small-PT configs (hiding is perturbative-regime hiding, #111's world,
  PT = the classifier) vs survivors clustered by γ or sign structure (new geometry —
  escalate per nursery N6 rules)
- (c) eigensolve/PSD failure at M = 64 or control fires: certify what passes, quantify,
  claim nothing beyond it

## 7. Falsifiers

- any δ = 0 control firing ⇒ run red (instrument defect, not physics)
- M64 K/G rebuild disagreeing with the committed export path beyond string truncation ⇒ red
- quadrature cross-check (composite vs tanh-sinh) off by > 1e-15 relative on any load-
  bearing integral ⇒ that config uncertified, excluded, reported

## 8. Cost (to be confirmed by heat78a probe before the letter)

96 + 8 configs; M8 ≈ 10 min total (heat77 rates); M64 = eigsy(64) at dps 45 per config —
probe running (heat78a, launch-only, no displacements, no verdicts collected: engineering
feasibility only, not census data). One core; 4 of 5 committed while grid/κ/AM-8b run.

## 9. What must stay true for this to be honest

- the config list, verdict rule, and outcome classes are frozen in the prereg letter
  BEFORE any displaced-config verdict is computed
- m2's family, m2's buy-in: the letter proposes, the counterparty amends or accepts
- three-way-ready per m3-L157 (first genuine three-way independent computation on an
  unscored configuration under the ≥12h reveal-gap protocol if adopted)
