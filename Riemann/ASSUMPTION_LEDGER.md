# ASSUMPTION LEDGER — the premises the programme is currently ACTING ON

Companion file to the Novelty Register (Glenn directive 2026-09-03; adoption recorded NOTES
§88j). Purpose: an unstated premise is only correctable if it is stated. Entries carry status
tokens and a named exposure route (what would reveal the assumption false, and whether anything
in the record already leans on it). Updated per cycle; errata outrank what they correct; no
hand-typed dates — file history is the timestamp.

Tokens: **LOAD-BEARING** (a result in the record would change if false) · **ENFORCED** (a
standing rule actively polices it) · **UNEXAMINED** (acted on, never tested) · **SURVEY-GRADE**
(rests on a survey, not a proof) · **RETIRED** (was acting on; evidence since withdrawn it).

---

## A. Instrument assumptions

**A1. The prime-side grid evaluator is faithful above the certified class floor.**
LOAD-BEARING + ENFORCED (#65: per-class floors measured before selection; findings below the
floor are unspeakable). Exposure: closed-form Gaussians (done — G0 certified 4e-15); the floor
is class-dependent (D7) and every new function class needs its own floor before its readings
count. OPEN DETAIL CLOSED (heat61h v2, 2026-09-03): the 4% heat61e-vs-heat61f prime discrepancy
= winner-row normalization (‖f₀‖ = 4.274 measured; heat61e's rung renormalized, the selector
does not) + float64 congruence scatter on the near-null eigenvalue; both .out numbers reproduced
at their printed precision (7 and 5 digits respectively); 1.3e-7 absolute < every certified
per-class floor, so nothing above floor depends on it. Practice: normalize rows before
polarizing.

**A2. The zero-side sum is exact and T-saturation certifies it.** LOAD-BEARING. Exposure: T-ladder
stability to 7 digits (heat61e/61f LB: …454 → …441e-13) + last-term magnitudes ≤ 1e-16 for
fast classes. Known exception: LC-class slow tail (T=200 still 11% below prime λ_max) — LC
zero-side readings carry a convergence caveat until the tail is characterized.

**A3. zetazero/nzeros and the Odlyzko tables agree at the heights we use.** LOAD-BEARING for
every zero-anchored result. Exposure: triple-locked anchors (dps-50 Newton + dps-40/60 +
Odlyzko) at all named sites; nzeros is an independent algorithm (Turing/RS backtracking) and
machine 3's certifier will test completeness at E~1e12 directly.

**A4. Mutant-diversity threshold (|corr| < 0.98) yields a representative basis.** ENFORCED-BY-
TEST (heat61g, pre-registered, outcome (ii) 2026-09-03): thr 0.95 and 0.98 give BIT-IDENTICAL
λ_min (+3.066441e-13 — the threshold does not bite below 0.98; double-mutate jumps land well
under 0.95), and thr 0.99 gives a HIGHER λ_min (+2.709401e-11 — admitting near-duplicates
narrows the span and RAISES the minimum, opposite of the geometry-dominance prediction). The
near-null direction is robust to acceptance geometry: the spectral reading of the M-ladder
stands, and λ_min(M) decay is not a threshold artifact. Byproduct: cond(G)=970 on the
unnormalized-winner basis vs 200.2 on heat61e's renormalized rung ⇒ ‖f₀‖≈2.2 — feeds A1.

**A5. diverse_mutants is prefix-deterministic (M=8 basis ⊂ M=16 ⊂ M=32).** Verified today
empirically (zero-side λ_min bit-identical on rebuild); rests on default_rng(20260903) stream
stability + acceptance depending only on the accepted prefix. Exposure: the ladder-step
monotonicity check built into heat61f (fires a stop, not a result).

## B. Search-space assumptions

**B1. inf Q = 0, unattained (object layer).** LOAD-BEARING for route-1's interpretation. The
near-null direction (+3.07e-13 in an 8-dim span) is the closest concrete approach; nothing yet
distinguishes "spectral bottom 0, approached" from "flat direction of the truncated operator".
Update (heat62, D4): random orthonormal spans reach +5.87e-16 generic-closeness — the
near-null cluster is large, consistent with "0 approached along a wide ridge". Exposure: the
M-ladder RATE (heat63, in flight) + the eigenvector structure as M grows.

**B2. Winners + their mutants span the directions the GA explored.** RETIRED-BY-TEST
(heat62, hash-committed db7de084, outcome (b) RIDGE-GENERIC 2026-09-03) → **D4**. Random
orthonormal M=8 spans in the GA's own LA/LB families land +5.6e-16…+1.7e-14 (floors ~1e-18,
cond=1) — every genuine reading 20–520× closer to the bottom than the winner+mutant span's
+3.066441e-13 at the same M. The M~16 ladder saturation was acceptance-geometry conditioning
death (heat61i), not a property of the ridge. Residual question inherited by heat63: the
approach RATE λ_min ~ c·M^−α, which the mutant ladder could not measure.

**B3. The three lineages (Gaussian/sinc/Fourier) cover the admissible class.** RETIRED-BY-TEST
(same run) → **D5**. The absent compact-support family is MATERIAL: random BUMP draws at M=16
score +7.85e-14 (1106× floor) — matching the GA's entire optimized history from unsearched
draws. Counter-contrast: LC (Fourier/Mellin) random spans sit at +2e-2…+7.9e-1, twelve orders
out — family choice dominates; the GA's LC lineage was exploring a bottom-blind family.

**B4. Local ξ analysis cannot see RH (earned constraint).** ENFORCED (route selection rule,
NOTES §88g). Exposure: none known — machine-verified at every order; this assumption gates the
whole explicit-formula-native restriction.

## C. Process assumptions

**C1. Three independent machines with a non-zero disagreement rate beat one careful machine.**
LOAD-BEARING (beast federation rule; adopted). Exposure: the cross-audit record itself — 8+
defects caught by counterparties that self-review missed (#63, #66, Arm 8, the ε-law, B-window
quotes).

**C2. Meta-work is visible (M-lane) and scored only in verdict-flips/false-claims-prevented.**
ENFORCED from today (register-design position). Exposure: watch for the M-lane becoming a place
to hide effort — the 20–30% cap question is now answerable, which is also a new way to flatter.

**C3. κ/quadrature constants quoted between machines are parsed, never hand-copied.** ENFORCED
(#63/#66; three founding instances). Exposure: any gate that hand-copies re-derives.

**C4. The ζ-side κ programme stops after heat55.** ENFORCED (beast strategy adoption, my
concession). Exposure: a counterparty result that requires ζ-side κ to interpret.

**C5. Suzuki's ω>1 kernel-continuity restriction plausibly extends to ω>½.** SURVEY-GRADE,
body READ end-to-end (arXiv:1204.1827, §2 Thm 2.3 remarks + §5): the restriction's precise
locus is CONTINUITY of the kernel h_ω(xy) — integer singularities |x−n|^{ω−1}, continuous
iff ω>1, L² exactly for ω>½ (their own observation). §4.1 Lemmas 4.2/4.4 already hold for
ω>½; the unproved step to ω∈(½,1] is §4.2 differentiability of φ_a^ε + the m(a) determinant
formula, route = Burnol-style distributions + L²-kernel Fredholm determinants (Smithies
Ch. VI). Affects heat54/E6 interpretation scope (calibration-only claim safe either way).
BYPRODUCT of the read (lane candidate, not acted on): Thm A.1(3) eventual single-sign of
h_ω^⟨1⟩(x) ⟹ Θ_ω inner ⟹ ζ zero-free in Re>½+ω (single-ω suffices) — numerically probeable,
sieve-cost; registered in NOTES, scheduling proposal goes to the exchange.

**C6. No fourth positivity/trace/duality instance exists among the 11 surveyed families.**
SURVEY-GRADE (M3 12/12, two re-verify flags open, transfer-ops rank contested). Exposure: the
two open re-verifications + the J-symmetry question (only empty cell with in-family existence
proof).

## D. Retired (kept for the record)

**D1.** "mpmath mp.taylor precision-stable ⇒ instrument" — RETIRED (ε-law erratum: the wrapper
is a Richardson FD measuring the ε-ultraviolet coefficient; the conviction was wrong, the two-
instrument distinction right).
**D2.** "2^17/2^19 floors transfer across function classes" — RETIRED (D7).
**D3.** "Half-step rescan is the completeness remedy at E~1e12" — RETIRED-CERTIFIED (machine 3
Letter 48: all three E~1e12 windows certified complete, n_scan == n_rigorous by independent
Turing/Rosser count at dps=25; edge margins ≥ 0.0039 (1.6% of mean spacing); bit-identical
constants by construction — same in-memory mp.mpf values into both measurements). A3's
exposure route (completeness tested at E~1e12) satisfied for these windows.

**D4.** "Winners + their mutants span the GA's directions" (was B2) — RETIRED-BY-TEST
(heat62): orthonormal random spans in the GA's own families sit 20–520× closer to the spectral
bottom (best genuine +5.868e-16, 243× floor, vs +3.066441e-13); the near-null ridge is GENERIC
in the admissible class. Nominal best trial −2.08e-16 was 0.35× its own floor — below
resolution, excluded (trap #68 clause 1, self-applied). Under B1 this reads as a large generic
near-null cluster of the truncated operator, not a needle the search earned.

**D5.** "Three lineages (Gaussian/sinc/Fourier) cover the admissible class" (was B3) —
RETIRED-BY-TEST (heat62): compact support absent AND material (random BUMP M=16 +7.85e-14,
1106× floor); LC family bottom-blind (+2e-2…+7.9e-1). Class design is a first-order
experimental variable, not bookkeeping.
