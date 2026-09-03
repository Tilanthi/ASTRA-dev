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
Update (heat63b, 235268d): the WINDOW-SCALE approach axis is DEAD — d(·,W) is bitwise
invariant (W1≡W2) once the draw's support sits inside the window's full-support region, and
non-monotone (s1 deeper at the NARROWER W0) when it doesn't. The live descent axis is basis
dimension M: BUMP descends per-seed monotonically M=8→64 (+1.2e-10 at M=64, Rayleigh–Ritz
nested-prefix ✓), still descending. Next exposure: M=128 rate; d_eff ladder BUMP>32,
LB<16 (intrinsic to sinc), LA≈8–16.

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

**B5. The ζ-side NB-BD d_N ladder measures something at machine scale.** RETIRED-BY-AUDIT
(m2 cycle 11 + addendum, 09-03; my erratum a5e5bdf). Four grounds, independent: (i) the
information-limit theorem — d_n ≥ ~√(C/log n) unconditionally (BDBLS via Ransford et al.
2019), so halving d_70 needs n~1.6e7 and d=0.01 needs n~10^200; (ii) BDBLS already published
N=2×10⁴ in 2002 — any machine-scale run is a re-derivation; (iii) the ladder fails the
question-gate as a STATEMENT (every rung N≤30 certifies a zero-free region strictly inside
Re s > 1, free by Euler; first non-vacuous rung ≈ 2×10⁴); (iv) my pre-registration specified
the WRONG family/space pairing (bare {1/(nx)} incl. f_1 in L²(0,1) breaks the ⟸ direction —
m2 §5, verified at the first zero). NB-BD is an IFF: "certified non-decay, RH untouched" is
retracted — non-decay would BE the disproof, and no finite table can certify it (d_n
monotone, limit exists, finite values bound only from above). Residue: heat64 v2 machinery =
instrument calibration, cross-validated vs m2's digamma instrument to 2.9e-14 worst over
n=2..30. The lane's live arm is the ZOO under the small-|s₀| floor gate
(2σ₀−1)/|s₀|² > C/log N_max — m2's pre-scheduling condition; classic D-H zeros are 55×
invisible at every reachable N; the rescue test = D-H zeros in Re s > 1 at small |s₀|,
strip-statement owed before running).
Update (09-03 night-5, heat65, prereg 7745559 → outcome f060a22): **the D–H leg is DEAD by
census** — real axis (1.001,12) has no zero of any multiplicity (min |f| = 0.92), box
(1,2)×(0,8) winding-exact 0 (steps 0.05/0.025 agree; big-rectangle n=200/400 covers the
centring slivers), detector positively controlled against m2's published off-line zeros
(all quoted digits reproduced). κ FE-derived (0.2840790438404123, matches Ferry anchor to
4.4e-8). Residual blind strip: Re>2, t≲20 unsurveyed, judged low-value, on the registry.
Zoo arm's next carrier = the Epstein leg (OPEN→MINE in LANE_REGISTRY.md), pre-reg gated on
literature-sourced zero coordinates (#63).

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
Update (09-03, 235268d): CLAIMED by machine 3 (Letter 53; owner-or-expiry worked on first
use). Full handover delivered with every formula re-verified against the arXiv e-print
(NOT from memory — #63 discipline extended to formula handover): β-integral convention, c_ω
product form, g_ω eq. 201, g_ω^⟨1⟩ closed form ω≠½ + elementary ω=½ case, h^⟨1⟩ both forms,
thm_3 items (2)/(3)/(4)/(5) incl. the cheaper lim-√x·h^⟨1⟩ target and the POSITIVE eventual
sign under the full conjecture. m3 runs x≤1e8 first probe (ω=½, elementary g); kill =
sustained sign oscillation at large x. Lane is m3's; my exposure = none until their report.

**C6. No fourth positivity/trace/duality instance exists among the 11 surveyed families.**
SURVEY-GRADE (M3 12/12, two re-verify flags open, transfer-ops rank contested). Exposure: the
two open re-verifications + the J-symmetry question (only empty cell with in-family existence
proof).

**C7. Methodology consensus R1–R7 is the operative rule set.** ENFORCED from 09-03
(machine1-consensus-encoding, a5e5bdf; all inputs in: m3 L51–54, m2's opinion [delivered
inside f6ce093 per their NOTICE], SAPIENS adjudication). R1 D-allocation scored on the
DERIVED denominator (state-change at close; two published numbers incl. tag-vs-outcome
disagreement rate). R2 question-gate as-STATEMENT (what would the number certify), unbounded.
R3 DQ-SECTION per .out; missing = red run (121 runs / 1 DQ at first check — the 120-red
retrofit debt stands until each lane next runs). R4 reset outputs traded at each sync
(reset_slots/). R5 owner-or-expiry AMENDED: silence is never a decision — default fires only
on explicit not-claiming or positive liveness. R6 every zero-compute rule gets an artifact
MISSING when it does not fire (rung_discipline_check.py). R7 each sync reports the
displacement figure (mine: 11 — 10 wasted-opportunity, 1 saved-by-not-running). Exposure:
SAPIENS re-adjudication invited; correlated blind spots of three machines under one director.

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

**D6.** "The NB-BD closure engine transfers to function fields, enabling a
Weil-certified positive control for the zoo's d_N instruments." — RETIRED-BY-ANALYSIS
(transfer check, 09-03 night-6, exchange 4711255): the direct transfer is not typeable
(free monoid → discrete divisor group; dual torus carries no zeta; no archimedean
floor; affine-line ζ has no zeros so the F_q[T]-proper statement would be vacuous; curve
zeros enter via cohomology, not Mellin). The exactly-transferable kernel is the
Jensen/harmonic family (u = q^{−s} conformal map; J_C = Σ max(0, log(q^{−½}/|u_j|)) = 0
⟺ Weil) — an identity, not an instrument family the zoo uses. Zoo calibration rests on
heat65 D–H controls + the Epstein leg. Literature corroboration: three search angles
empty (negative-search caveat stated).
