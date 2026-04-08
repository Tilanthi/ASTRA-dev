# Experiment 1: Endomorphism Ring Computation — ECCp-131

**Date**: 2026-04-06  
**Curve**: ECCp-131 (custom 131-bit prime-order curve)  
**Script**: `/workspace/experiment1_endomorphism.py`

## Curve Parameters

| Parameter | Hex | Decimal | Bits |
|-----------|-----|---------|------|
| q (field prime) | `0x048E1D43F293469E33194C43186B3ABC0B` | 1550031797834347859248576414813139942411 | 131 |
| a | `0x041CB121CE2B31F608A76FC8F23D73CB66` | — | — |
| b | `0x02F74F717E8DEC90991E5EA9B2FF03DA58` | — | — |
| n (group order) | `0x048E1D43F293469E317F7ED728F6B8E6F1` | 1550031797834347859219047037805205710577 | 131 |

**n is prime** ✓ — the group is cyclic of prime order.

---

## Results

### 1. Trace of Frobenius

```
t = q + 1 - n = 29,529,377,007,934,231,835
```

- **65 bits** (about half the field size, as expected by Hasse's theorem)
- Hasse bound: |t| ≤ 2√q ≈ 78,740,886,401,775,992,689 → **satisfied** ✓
- t > 0 and t is large → ordinary curve, no special structure

### 2. CM Discriminant

```
D = t² - 4q = -5,328,143,084,860,676,590,809,120,034,441,032,302,419
```

- **132 bits**, negative → ordinary elliptic curve over F_q ✓

### 3. Complete Factorization of |D|

```
|D| = 67 × 173 × 2,087 × 4,903 × 44,923,194,445,989,685,202,159,178,469
```

| Factor | Bits | Prime? |
|--------|------|--------|
| 67 | 7 | ✓ |
| 173 | 8 | ✓ |
| 2,087 | 11 | ✓ |
| 4,903 | 13 | ✓ |
| 44,923,194,445,989,685,202,159,178,469 | 96 | ✓ |

**|D| is squarefree** — all prime factors appear exactly once.

Verification: 67 × 173 × 2087 × 4903 × 44923194445989685202159178469 = |D| ✓

### 4. Fundamental Discriminant and Conductor

Since |D| is squarefree and |D₀| ≡ 3 (mod 4), the discriminant −|D₀| ≡ 1 (mod 4) is already a **fundamental discriminant**.

```
D₀ = -5,328,143,084,860,676,590,809,120,034,441,032,302,419  (= D itself)
f  = 1  (conductor)
```

**D = f² · D₀ = 1² · D₀ = D₀** — the endomorphism ring is the **maximal order** in Q(√D₀).

### 5. Class Number

|D₀| is 132 bits — far too large for exact computation via reduced forms.

**Analytic estimate** (Dirichlet class number formula):

```
h(D₀) ≈ √|D₀| / π × L(1, χ_{D₀})
      ≈ √|D₀| / π × ln|D₀|  (heuristic for L-value)
      ≈ 2.13 × 10²¹
```

**h(D) ≈ 2.1 × 10²¹** — an astronomically large class number.

This means:
- The isogeny class contains ~10²¹ curves
- Enumerating the isogeny class is **completely infeasible**
- No isogeny-based shortcuts exist

### 6. GLV Endomorphism Check

D₀ is a **132-bit discriminant** — NOT a small CM discriminant.

Small CM discriminants that enable GLV: {-3, -4, -7, -8, -11, -19, -43, -67, -163}

**Result: GLV does NOT apply.** No efficiently computable non-trivial endomorphisms exist.

The endomorphism ring is:
```
End(E) ≅ Z[(1 + √D₀)/2]  (maximal order in Q(√D₀))
```

This is the "generic" case — the endomorphism ring provides no structural advantage for ECDLP.

### 7. Embedding Degree (MOV Attack)

```
Embedding degree k = n - 1 = 1,550,031,797,834,347,859,219,047,037,805,205,710,576
```

The embedding degree is **maximal** (= n − 1, full 131 bits). This means:
- MOV attack would require discrete log in F_{q^k} where k ≈ q — **completely impractical**
- No pairing-based attack applies

**Factorization of n − 1:**
```
n - 1 = 2⁴ × 3 × 73 × 283 × 172,548,521,611,033 × 9,058,970,217,611,515,871
```

All factors verified prime.

### 8. Anomalous Curve Check

```
n ≠ q  (t = 29,529,377,007,934,231,835 ≠ 1)
```

**Not anomalous.** Smart's attack does not apply.

---

## Summary Table

| Property | Value | Security Implication |
|----------|-------|---------------------|
| Trace t | 29,529,377,007,934,231,835 (65 bits) | Ordinary curve, no special structure |
| CM discriminant D | −5.33 × 10³⁹ (132 bits, squarefree) | Generic — no CM shortcuts |
| Fundamental disc D₀ | = D (no square factor) | Maximal order endomorphism ring |
| Conductor f | 1 | Maximal order |
| Class number h(D) | ≈ 2.1 × 10²¹ | Isogeny enumeration infeasible |
| GLV endomorphism | **No** | No endomorphism speedup |
| Embedding degree | n − 1 (maximal, 131 bits) | MOV attack infeasible |
| Anomalous | **No** (t ≫ 1) | Smart's attack inapplicable |
| Curve type | Ordinary | Standard ECDLP hardness |

## Mathematical Interpretation

**This curve has no algebraic shortcuts for ECDLP.**

The endomorphism ring analysis reveals that ECCp-131 is a "generic" ordinary elliptic curve:

1. **No special endomorphisms**: The CM discriminant is enormous (132 bits) with no small square factors. There is no efficiently computable map φ: E → E beyond scalar multiplication [m].

2. **No isogeny shortcuts**: The class number h ≈ 10²¹ means the isogeny volcano has an incomprehensibly large crater — we cannot enumerate neighboring curves to find one with exploitable structure.

3. **No embedding shortcuts**: The full embedding degree eliminates all pairing-based attacks (MOV, Frey-Rück).

4. **No anomalous weakness**: t ≈ 2⁶⁵ rules out the anomalous curve attack entirely.

**Bottom line**: The ECDLP on this curve must be attacked by generic methods (Pollard's rho, baby-step giant-step, or variants). The expected complexity is **O(√n) ≈ 2⁶⁵ group operations** — which is the target for the full ECCp-131 challenge.

## Anomalies / Notable Observations

- **None found.** The curve appears to be well-chosen with no exploitable algebraic structure.
- The trace t ≈ 2⁶⁵ is typical — not suspiciously close to 0, ±1, or ±2√q.
- The discriminant factors into 4 small primes (67, 173, 2087, 4903) times one large 96-bit prime. This factorization pattern is unremarkable.

## Implications for Attack Strategy

Since no algebraic shortcuts exist, the remaining experiments should focus on:
- **Generic group algorithms**: Pollard's rho with distinguished points (Experiment 2)
- **Parallelization**: How to distribute the 2⁶⁵ work across available compute
- **Lattice methods**: L3/BKZ on the group structure (Experiment 4) — though without GLV, lattice dimension is limited
- **Summation polynomials / index calculus**: Experimental approach for curves over prime fields (Experiment 3)

The 131-bit group order means ~65.5 bits of security against birthday-type attacks. This is at the boundary of feasibility for a well-resourced computation but beyond what we can demonstrate in this research setting without massive parallelism.
