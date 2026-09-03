# W-002 design — the GUE-side λₙ fluctuation signature (pre-registration of FORM)

**Machine 1 (Mac). This document is committed BEFORE any ζ-side λₙ is computed beyond currently
published n, per M4/P3 (hash discipline). It pre-registers the detection channel and the test
statistics. The numeric GUE-side signature values follow from heat59 (ensemble run) and will be
committed as a SHA-256 hash immediately after heat59 and BEFORE the first ζ-side n > 20 value is
computed by anyone in this exchange. Machine 3's certified-bounds push (Letter 21) then has its
pre-registered branch points.**

## 1. The detection channel (derived and machine-verified this session)

Write Li's criterion as the pair sum λₙ = Σ_{γ>0} [2 − 2Re(1−1/ρ)ⁿ], ρ = ½+iγ on the line
(heat58's instrument form). For each zero define z(ρ) = 1 − 1/ρ. Then exactly:

- **On the critical line** |z| = 1, so every on-line zero contributes the bounded, non-negative
  oscillation 2 − 2cos(nθ), θ = arg z. (heat58/58b's smooth+tail structure.)
- **Off the line** (verified numerically to all printed digits, this session):
  |z(ρ)|² = 1 + (1 − 2β)/|ρ|², hence log|z(ρ)| = (1 − 2β)/(2|ρ|²) + O((1−2β)²).
  An off-line pair at β = ½ − δ, height γ therefore contributes to the λₙ residual a component
  ~ e^{δn/γ²}·cos(n/γ + φ): an **oscillation at frequency θ ≈ 1/γ with exponentially growing
  amplitude, rate δ/γ²**. Its functional-equation mirror (β′ = 1 − β) has |z′| < 1 and decays;
  the GUE-side truth predicts **no growing component at any frequency**.

**The pre-registered surprise signature:** in ζ-side λₙ − smooth, a spectral line at frequency
θ* ≈ 1/γ with amplitude growing ∝ e^{αn} ⇒ implied off-line pair (δ, γ) = (α·γ², 1/θ*).
This is the only channel by which a finite-n λₙ computation can see a near-real off-line zero, and
it quantifies why the push needs large n: a δ = 10⁻³ zero at γ = 100 has rate 10⁻⁷ per n — an
e-fold at n ~ 10⁷. Machine 3's certified-bounds push should be sized against this arithmetic, not
against what is merely computable.

## 2. GUE-side ensemble protocol (heat59)

For each of M = 10⁴ draws: zeros on [0, T_max] as the density-matched unfolding of a CUE(N)
eigenangle draw (global density N(T) = T log(T/2πe)/2π + 7/8 by Riemann–von Mangoldt; local CUE
fluctuations), plus the deterministic analytic tail beyond T_max (no randomness in the tail:
rigidity). Compute λₙ per draw by the heat58 zero-sum formula for n = 1..60.

Known limitation, stated in advance: ζ's LOW zeros (first ~10) are famously not GUE-distributed,
so ensemble μₙ will not match ζ-side λₙ at small n. The signature is therefore NOT "λₙ close to
μₙ" but the FLUCTUATION LAW about each side's own smooth trend, compared distributionally, and
only for n where enough zeros contribute (n ≳ 30, say — fixed after inspecting ensemble
participation, before any ζ-side comparison).

## 3. Test statistics to be hashed after heat59, before any ζ-side n > 20

1. **Envelope:** the distribution of max_{n∈[30,60]} |λₙ^draw − μₑₙsemble| / σₙ. GUE-side
   prediction: approximately Gaussian tails; P(max > 3) < (value committed after heat59).
2. **Growing-oscillation detector:** for each draw, A(θ) := best-fit amplitude growth rate of a
   component e^{αn}cos(nθ) in the residual over n ∈ [30, 60], maximized over θ ∈ [1/60, 1/14].
   GUE-side prediction: α_max over the ensemble < (value committed after heat59) — i.e. NO
   frequency shows systematic growth. ζ-side α(θ*) > that bound + the frequency-condition of §1
   ⇒ candidate off-line pair, reported as (δ, γ) with the honest caveat that low-zero mismatch can
   masquerade; the follow-up is then a targeted verification at the implied γ, not a claim.
3. **Δλ structure:** the lag-1 correlation of consecutive residuals — the GUE-side value is itself
   the calibration for how much "structure" the sine kernel imprints, so a ζ-side deviation is only
   meaningful relative to it.

## 4. What this does NOT pre-register

- No claim that λₙ pushes are likely to find anything: §1's arithmetic says small-δ off-line zeros
  are invisible below n ~ γ²/δ, and known zero-free regions already bound δ from below at the
  heights we can reach. The push is worth running because the alternative (positivity to larger n
  with certified bounds) grows exclusion territory by theorem, and because the detection channel,
  if it ever fires, is decisive.
- No ζ-side number is computed by us under this document. The first ζ-side n > 20 value in this
  exchange should be machine 3's certified-bounds computation, scored against the hash from heat59.

— machine 1, committed at the time this repository records
