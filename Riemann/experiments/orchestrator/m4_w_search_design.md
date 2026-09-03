# M4/W(f) design — the negative-cell evolutionary search (pre-registration of FORM)

**Machine 1 (Mac). Committed BEFORE any scored evaluation runs (M4/P3 hash discipline).** This is
the concrete game-world named in `machine1-virtual-universe-note-2026-09-03.md` §3. The search
runner will be `heat61_w_search.py` (heat60 reserved for the Suzuki-Epstein automaticity control,
per `machine1-addendum-suzuki-2026-09-03.md` §4). Any change to this document after the first
scored run opens a NEW version; the hashed original stands.

## 1. The objective (zero proxy gap — the whole point)

Work on the multiplicative group: u = e^x, g ∈ C_c^∞((0,∞)) ⟺ f(x) := g(e^x) ∈ C_c^∞(ℝ). Mellin
transform ĝ(s) = ∫₀^∞ g(u) u^s du/u = ∫ f(x) e^{sx} dx — a (shifted) Fourier transform; compact
support of f means ĝ is entire of finite exponential type (Paley–Wiener).

**Weil's positivity criterion** (Bombieri normalization, AIM WWN 76a; Burnol math/9810169 v2 —
both swarm-sourced with verification status, re-verified by gate G0 below):

  RH(ζ) ⟺ Q(g) := Σ_ρ ĝ(ρ)·ĝ(1−ρ) > 0 for every nonzero g ∈ C_c^∞((0,∞)).

On RH every zero has 1−ρ = ρ̄, so each term is |ĝ(ρ)|² (for real g) and Q is a sum of squares.
Off RH, an off-line quartet {ρ₀, ρ̄₀, 1−ρ₀, 1−ρ̄₀} contributes 2·Re[ĝ(ρ₀)ĝ(1−ρ₀)], sign-free —
and Burnol's amplification (N-fold convolution g_N = g∗…∗g∗k∗…∗k) forces Q(g_N) = −2 + O(4^{−N})
< 0 from a single off-line zero pair. Hence:

- **Win condition: an admissible g with Q(g) < −ε_cert is a disproof of RH. Not evidence — the
  thing itself.** (Contrapositive of the criterion; strict inequality per Bombieri's statement.)
- **Sustained failure is territory:** every certified-positive cell is a positivity instance; the
  min-Q trajectory maps how tight the constraint sits in function space.

## 2. The physics engine (exact, zero-free)

Weil's explicit formula (1952), applied to h := g ∗ g^c (multiplicative convolution, g^c(u) =
g(1/u), so ĥ(s) = ĝ(s)·ĝ(−s) under the s-convention fixed by G0 — see §3):

  Σ_ρ ĥ(ρ) = ĥ(0) + ĥ(1) − Σ_ν W_ν(h),

with W_p supported on {p^k, p^{−k}: k ≥ 1} with weights Λ(p^k) = log p, and the archimedean W_∞
smooth off u = 1 with a log singularity there. **The right side is finite-type computable to
certified precision without knowing the zeros** (swarm family-5 contact row, sources: Weil 1952;
Barner 1981; Moreno 1976; Burnol refs [5],[9]). The search therefore evaluates fitness EXACTLY on
the prime side; the zero side is used only by the verification gate.

## 3. Gate G0 — convention + implementation balance (no search runs until PASS)

The explicit formula's sign/shift conventions are the classic transcription hazard (trap #63
class). G0 removes trust: for THREE fixed named test functions f₁, f₂, f₃ (Gaussian bump on
log-scale, two-bump asymmetric, prolate-type pair), compute Q two independent ways:

  (i) zero side: Q = Σ_{|γ|≤T} ĝ(ρ)ĝ(1−ρ) from the zero table (mp.zetazero, T certified) + tail
      bound from the type/decay of ĝ (Ingham-grade bound, certified);
  (ii) prime side: the explicit formula of §2.

**PASS = |zero-side − prime-side| ≤ certified tail + 10⁻⁸ relative, all three functions.** Any
sign/shift convention error breaks the balance at O(1); G0 is therefore a full verification of the
instrument, not a sanity check. G0's three test functions and their parameters are fixed NOW:
f₁ = exp(−x²/2) truncated smoothly to |x| ≤ 8; f₂ = exp(−(x−1)²/2) − 0.7·exp(−(x+2)²/8), same
cutoff; f₃ = prolate spheroidal pair (bandwidth c = 4, support |x| ≤ 8) per the programme's
existing Sonin/prolate instrument.

## 4. Gate G1 — admissibility (anti-reward-hacking level design)

A candidate g (equivalently f) is admissible iff:

1. f ∈ C_c^∞ with support width ≥ w_min = 4 in x (log-scale) — excludes needle functions whose
   prime-side truncation error dominates the value (the "respawning target" failure: near-needles
   can farm apparent negativity out of truncation noise; w_min + the ε_cert margin kill it);
2. normalization ‖f‖₂ = 1 (scale invariance of the sign of Q is not exact — Q is quadratic in
   scale but the criterion's quantifier is over all g, so normalization fixes the search space;
   the win condition is sign-based and scale-free in the admissible class);
3. nondegeneracy is AUTOMATIC for our class: a nonzero Paley–Wiener ĝ cannot vanish on all zeros
   (zero set density (T/2π)log(T/2π) outruns any finite type — Ingham's density bound). Stated so
   nobody later "discovers" a zero-side-free g and farms the prime side: such a g would make the
   zero side 0, not Q — the formula still holds and Q = prime side; no farm exists. (The degenerate
   direction in the classical literature is excluded by C_c^∞ itself: ξ-weighted transforms are not
   Paley–Wiener.)

## 5. The search protocol (hide-and-seek structure)

- **Arena parametrizations — three independent lineages, seeded from different construction
  principles** (multi-agent pressure, per the directive):
  L-A: Gaussian mixture f(x) = Σ_{j≤J} c_j exp(−(x−μ_j)²/2σ_j²)·cutoff(x), J ≤ 8, coefficients
       mutated (σ-scaled Gaussian steps), elitist selection on Q.
  L-B: prolate/band-limited family (the Sonin instruments): f = concentrated band-limited pairs,
       mutations on bandwidth c and center.
  L-C: mollifier lineage: ĝ(s) = P(s)P(1−s)·w(s) with P a truncated Dirichlet-type polynomial
       (aᵢ pᵢ^{−s} terms, ≤ 6 terms, primes among first 20) and w a fixed Paley–Wiener window —
       the classical mollifier shape, connecting to the Nyman–Beurling row's "weighted L²
       Dirichlet-polynomial mollification" identification.
- **Fitness: Q(g) via the prime side, exact** (mp arithmetic; prime powers to p^k ≤ u_max(g)
  derived from support; archimedean theta term via mp; certified interval on the truncation).
- **Population per lineage: 24; generations: 200; the three lineages run as parallel agents and
  exchange their best individual every 25 generations (migration)** — the arms race.
- **Per-generation logging:** min-Q, argmin parameters, certified error — territory measurement.
- **Halt-and-verify (pre-registered falsifier protocol):** any Q < −ε_cert ⇒ freeze that
  individual; recompute by the ZERO side (instrument (i) of G0) at 3× precision; if both agree
  within certified error, post to the exchange for counterparty re-derivation (M1 unit rule: the
  author's own computation never confirms) BEFORE any claim language. A confirmed negative cell
  is reported as ¬RH candidate with the full parametrization and both instruments' values.

## 6. What this does NOT pre-register

- No claim of positive probability of finding a negative cell. The honest prior: the function-
  field proof says the positivity is delivered by a mechanism (Rosati) with no known number-field
  analogue; random parametric search is not that mechanism and is unlikely to conjure it. What
  the search DOES buy, guaranteed: (a) the first quantitative min-Q territory map over three
  principled lineages (each certified cell is a positivity instance — M1-bankable); (b) a live,
  exactly-scored, zero-proxy-gap detector whose firing would be decisive; (c) the mollifier
  lineage's min-Q doubles as a direct numerical probe of the Nyman–Beurling corridor.
- No ζ-side λₙ numbers (W-002 discipline unaffected — the zero table is used only inside G0/verify
  at already-published heights T ≤ 100 with the certified tail, never to produce new λₙ).
- The W-005 lesson is load-bearing here: off-line zeros are paid for by Euler-product failure,
  and this objective is exactly the Euler-side ledger — the search interrogates the same account
  the Epstein witnesses overdrew. Cross-reference for interpretation, not for expectation-setting.

## 7. Hash

SHA-256 of this file, computed and committed at commit time, before `heat61_w_search.py` performs
its first scored evaluation. The commit is the timestamp (P1/P3).

— machine 1 (Mac)
