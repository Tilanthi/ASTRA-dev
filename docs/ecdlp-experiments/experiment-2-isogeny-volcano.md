# Experiment 2: Isogeny Volcano Exploration — ECCp-131

**Date**: 2026-04-06  
**Status**: ✅ Complete  
**Verdict**: No weakness found via isogeny analysis  

## Curve Parameters

```
q = 0x048E1D43F293469E33194C43186B3ABC0B  (131 bits)
n = 0x048E1D43F293469E317F7ED728F6B8E6F1  (131 bits, PRIME)
t = 29529377007934231835                    (trace of Frobenius)
D = -5328143084860676590809120034441032302419  (CM discriminant, ≈131 bits)
j(E) = 0x13f849c0eed01093d8efe9c7343113569
```

## Key Invariants

| Property | Value | Implication |
|----------|-------|-------------|
| Group order n | Prime | No Pohlig-Hellman decomposition |
| Trace t | 29529377007934231835 | Not supersingular (t ≠ 0) |
| n = q? | No | Not anomalous (no Smart's attack) |
| Embedding degree k | > 10,000 | No MOV/Frey-Rück pairing attack |
| j-invariant | Non-special | j ≠ 0, j ≠ 1728 (no extra automorphisms) |
| CM discriminant |D| | ≈ 131 bits | Extremely large → no CM-based attack |
| Fundamental disc d | = D (squarefree) | Conductor f = 1 → curve on crater |

## Torsion Structure over F_q

| ℓ | E[ℓ](F_q) | Division polynomial | Notes |
|---|-----------|---------------------|-------|
| 2 | **0 points** | x³ + ax + b has no roots mod q | No rational 2-torsion |
| 3 | **0 points** | 3x⁴ + 6ax² + 12bx - a² has no roots mod q | No rational 3-torsion |

Since n is prime, there are no rational ℓ-torsion points for any ℓ > 1 dividing n. But ℓ-isogenies can still exist when the kernel is defined as a group scheme over F_q (determined by the modular polynomial).

## Kronecker Symbols and Volcano Structure

The Kronecker symbol (D/ℓ) determines whether ℓ-isogenies exist over F_q:

| ℓ | (D/ℓ) | Expected roots of Φ_ℓ(j,Y) | Actual roots | Volcano position |
|---|--------|----------------------------|--------------|------------------|
| 2 | **-1** | 0 | 0 ✓ | No 2-isogenies over F_q |
| 3 | **-1** | 0 | 0 ✓ | No 3-isogenies over F_q |
| 5 | **+1** | 2 | 2 ✓ | Crater: 2 neighbors |
| 7 | **+1** | 2 | 2 ✓ | Crater: 2 neighbors |
| 11 | **-1** | 0 | — | No 11-isogenies over F_q |
| 13 | **+1** | 2 | 2 ✓ | Crater: 2 neighbors |

**All results match theory exactly.** The curve sits on the crater of every ℓ-volcano (conductor f = 1).

## Isogenous Curves Found

Using modular polynomials from [Sutherland's database](https://math.mit.edu/~drew/ClassicalModPolys.html) (verified against the bivariate polynomial):

### 5-isogenies (2 neighbors)
```
j₁' = 0x1d1230c2ad1b24b7910d0f15bb01f284d  ✓ Φ_5(j, j₁') = 0
j₂' = 0x31dd5f0584b4c2399dc1299100d06578   ✓ Φ_5(j, j₂') = 0
```

### 7-isogenies (2 neighbors)
```
j₃' = 0x208fe914fb7e15cf822ca392dead13026  ✓ Φ_7(j, j₃') = 0
j₄' = 0xbef8ec53f6704b5802893e127cbd53e7   ✓ Φ_7(j, j₄') = 0
```

### 13-isogenies (2 neighbors)
```
j₅' = 0xebb13c892388138b22c7785397386fab   ✓ Φ_13(j, j₅') = 0
j₆' = 0x11eef0030eb5172d33e988fa998dee847  ✓ Φ_13(j, j₆') = 0
```

**Total: 6 isogenous curves found** (0 via ℓ=2,3; 2 each via ℓ=5,7,13).

None have j = 0 or j = 1728 (no special structure).

## Weakness Analysis of Isogenous Curves

### Tate's Theorem (Critical)

> **Theorem (Tate, 1966):** Two elliptic curves E, E' over F_q are isogenous over F_q if and only if #E(F_q) = #E'(F_q).

**Consequence:** ALL 6 isogenous curves have the same group order n, which is prime. Therefore they ALL share:
- Same prime order (no Pohlig-Hellman)
- Same trace of Frobenius t
- Same embedding degree (> 10,000)
- Same ECDLP difficulty

**Isogeny walking cannot find a weaker curve.** The ECDLP difficulty is an isogeny-class invariant.

### Other Structural Checks

| Check | Result |
|-------|--------|
| Anomalous neighbor | Impossible (all have order n ≠ q) |
| Supersingular neighbor | Impossible (all have trace t ≠ 0) |
| Low embedding degree | Impossible (same k > 10,000 for all) |
| Smooth order neighbor | Impossible (all have prime order n) |
| Special j-invariant | None found (no j=0 or j=1728) |

## Isogeny Graph Structure

```
                    [Crater level]
                         
     j₁'(5) ←--5--→ j(E) ←--5--→ j₂'(5)
                       ↕ ↕
              7-isog   ↕ ↕   7-isog
                       ↕ ↕
     j₃'(7) ←--7--→ j(E) ←--7--→ j₄'(7)
                       ↕ ↕
             13-isog   ↕ ↕  13-isog
                       ↕ ↕
    j₅'(13) ←-13--→ j(E) ←-13--→ j₆'(13)
    
    No 2-isogenies or 3-isogenies exist over F_q.
    Each neighbor pair can also be connected through 
    the full ℓ-isogeny graph on the crater.
```

The crater of each ℓ-volcano is an **Ramanujan graph** — each vertex has degree ℓ+1 in the full graph (over F̄_q), but only 1+(D/ℓ) edges are defined over F_q. The total number of vertices on the crater is approximately h(D) ≈ 2^56, making exhaustive exploration infeasible.

## CM Discriminant Analysis

```
D = t² - 4q = -5328143084860676590809120034441032302419
|D| ≈ 2^132 (extremely large)
Fundamental discriminant: D itself (squarefree, f=1)
Class number h(D) ≈ √|D| / (π · log|D|) ≈ 2^56
```

The large CM discriminant means:
1. **No CM method applicable** — requires |D| < 10^15 or so
2. **No Weil descent / GHS attack** — needs special algebraic structure
3. **Isogeny graph is enormous** — ~2^56 vertices, cannot traverse

## Factorization of n-1 and n+1

```
n - 1 = 2^4 × 3 × 73 × 283 × C₁₁₁
  where C₁₁₁ = 1563111918367244965086894168204743 (111 bits, composite)

n + 1 = 2 × C₁₃₀  
  where C₁₃₀ is 130 bits (composite)
```

Neither n-1 nor n+1 is smooth — no special structure exploitable.

## Conclusions

1. **No isogeny-based weakness exists.** The curve is on the crater of every ℓ-volcano, and Tate's theorem guarantees all isogenous curves share the same prime order.

2. **The curve is optimally hardened** against all known algebraic attacks:
   - Prime order (no Pohlig-Hellman)
   - Large embedding degree (no pairing attacks) 
   - Non-anomalous, non-supersingular
   - Large CM discriminant (no CM attacks)
   - No special j-invariant

3. **Generic attack complexity remains O(√n) ≈ 2^65.** This is the theoretical minimum for any curve in this isogeny class.

4. **The isogeny graph is correctly structured** — Kronecker symbols perfectly predict the number of neighbors at each prime degree, confirming the mathematical theory and our computations.

## Methodology

- **Division polynomials**: Computed ψ_2 (degree 3) and ψ_3 (degree 4) and found their roots mod q using polynomial GCD with x^q - x
- **Modular polynomials**: Used exact integer coefficients from [Sutherland's database](https://math.mit.edu/~drew/ClassicalModPolys.html) for Φ_2, Φ_3, Φ_5, Φ_7, Φ_13
- **Root finding**: Cantor-Zassenhaus algorithm over GF(q) after GCD extraction
- **Verification**: Every root j' verified by checking Φ_ℓ(j, j') = 0 using the full bivariate polynomial
- **All computations in pure Python** (no SageMath) with modular arithmetic

## Scripts

- `/workspace/experiment2_final.py` — Main computation with verified modular polynomial coefficients
- `/workspace/experiment2_isogeny_v2.py` — Initial torsion and weakness analysis
