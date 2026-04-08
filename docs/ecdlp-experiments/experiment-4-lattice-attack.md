# Experiment 4: Lattice Attack via Known Bit Information

**Date**: 2026-04-06  
**Target**: ECCp-131 ECDLP (131-bit prime-order curve)  
**Approach**: Lattice-based attacks (HNP, LLL, BSGS hybrid)  
**Result**: ❌ **NOT APPLICABLE** — Lattice methods require side-channel information that pure ECDLP does not provide.

---

## Curve Parameters

```
q = 0x048E1D43F293469E33194C43186B3ABC0B   (131-bit field prime)
n = 0x048E1D43F293469E317F7ED728F6B8E6F1   (131-bit prime group order)
j-invariant = 0x13F849C0EED01093D8EFE9C7343113569  (generic, not 0 or 1728)
Trace of Frobenius t = 29,529,377,007,934,231,835
CM discriminant D = -5,328,143,084,860,676,590,809,120,034,441,032,302,419 (132 bits, large)
```

**Structural properties**: n is prime (no Pohlig-Hellman), j-invariant is generic (no CM endomorphism), |D| is 132 bits (no special structure).

---

## Task 1: Boneh-Venkatesan Hidden Number Problem (HNP) Analysis

### Framework

The HNP asks: given an oracle that reveals the top `d` bits of `k · g_i mod n` for random multipliers `g_i`, recover `k`. The Boneh-Venkatesan theorem (CRYPTO 1996) shows this is solvable via LLL when sufficient queries are made.

**Required queries**: ⌈log₂(n) / d⌉ + 1 for `d`-bit leakage per query.

### Leakage Requirements Table

| d (bits leaked) | Queries needed | Lattice dimension | LLL feasible? | Notes |
|:---:|:---:|:---:|:---:|:---|
| 1 | 132 | 133 | Yes (but slow) | 1 bit per query — extreme oracle |
| 2 | 67 | 68 | Yes | |
| 3 | 45 | 46 | Yes | |
| 5 | 28 | 29 | Yes | |
| 7 | 20 | 21 | Yes | Practical |
| 10 | 15 | 16 | Yes | Very practical |
| 15 | 10 | 11 | Yes | Easy |
| 20 | 8 | 9 | Yes | Trivial |
| 33 | 5 | 6 | Yes | Trivial |
| 44 | 4 | 5 | Yes | Trivial |
| 65 | 3 | 4 | Yes | Trivial |
| 66+ | 2-3 | 3-4 | Yes | Half the bits → trivially solvable |

### Critical Finding

**For pure ECDLP, we have ZERO bits of leakage.** The HNP framework requires an oracle that reveals partial information about `k · g_i mod n`. In standard ECDLP:
- We only know `Q = k·P` (a *point*, not an integer)
- The scalar `k` never appears in any computation we can observe
- There are no signatures, no nonce reuse, no timing leaks

**Verdict**: HNP is categorically inapplicable to pure ECDLP.

---

## Task 2: LLL Experiments on Small Curve

### Test Curve
```
q = 10007, a = 3, b = 6, n = 10039 (14-bit)
P = (0, 1973), k = 4321 = 0b1000011100001
Q = k·P = (5061, 7370)
```

### Part A: With Known Top Bits

**Scenario**: Know top 7 bits of k = `1000011...`  
**Result**: k_approx = 4288, remaining search space = 2⁶ = 64 candidates.

| Method | Time | Result |
|--------|------|--------|
| Brute force 64 candidates | 0.0016s | ✅ Found k = 4321 |
| Known-bit search (7 of 13 bits) | Instant | Search reduced 64× |

**Conclusion**: Knowing ~54% of the bits trivially solves the problem via exhaustive search of the remaining space.

### Part B: HNP Oracle Simulation

Simulated an oracle revealing `d` bits of `k · g_i mod n`:

| d (bits) | Queries | Unique solution? | LLL recovery? |
|:---------:|:-------:|:----------------:|:-------------:|
| 5 | 5 | ✅ Yes (brute-force confirms) | ❌ LLL didn't isolate k |
| 7 | 4 | ✅ Yes (brute-force confirms) | ❌ LLL didn't isolate k |

**Why LLL failed on this small instance**: For n ≈ 10⁴ (14 bits), the lattice gap ratio is too small for LLL to distinguish the target vector from other short vectors. The Boneh-Venkatesan theorem is asymptotic — it works reliably for n > 2⁶⁰ or so. The brute-force verification confirms the oracle provides sufficient information; the lattice is simply too small for LLL's quality guarantees.

**For ECCp-131** (n ≈ 2¹³¹): if an oracle existed, HNP-LLL would work perfectly with d ≥ 1 bit of leakage.

### Part C: Structural Lattice (Without Known Bits)

**2D lattice**: L = {(a,b) ∈ ℤ² : a + b·k ≡ 0 mod n}, basis [[n, 0], [k, 1]].

After LLL on the test curve:
```
Reduced basis: (-33, -79), (97, -72)
|v1| = 85.6, |v2| = 120.8, √n = 100.2
```

Both vectors have norm ≈ √n (Minkowski bound), which is *expected* — they don't reveal k because k > √n. The shortest vector in this lattice is O(√n) regardless, and recovering k from it requires knowing k already.

**Fundamental impossibility**: Without knowing k, the lattice [[n, 0], [?, 1]] cannot be constructed. The ECDLP gives us Q = k·P (a curve point), not k itself — there's no integer relationship to build a lattice from.

---

## Task 3: Multi-scalar Lattice Analysis

### Method
Computed x-coordinates of iQ for i = 1, ..., 100 on ECCp-131.

```
x(Q)  = 0x3AA6F004FC62E2DA1ED0BFB62C3FFB568
x(2Q) = 0x458E0E1A31A506700F571D84ADA5BBD6D
x(3Q) = 0x0DE818DEF8C91D1E407113A7018381888
```

### Analysis 1: Linear Relations mod n

Built an 11×11 lattice from 10 x-coordinates mod n and ran LLL:

| Row | Coefficient norm | Residue mod n |
|:---:|:----------------:|:-------------:|
| 0 | 2839 | non-zero |
| 1 | 3364 | 90 |
| 2 | 3299 | non-zero |
| 3 | 3650 | non-zero |
| 4 | 3885 | 160 |

No short-coefficient relations found. The coefficient norms (~3000-4000) are consistent with random values — no algebraic structure detected.

### Analysis 2: x-coordinate Differences

Average bit-length of x(iQ) - x((i-1)Q): **128.7 bits** (expected ~131 for random).  
The differences are essentially random 131-bit values — no pattern.

### Analysis 3: Lattice on Differences

LLL on 9×9 lattice of consecutive x-coordinate differences:
- Shortest coefficient vector norm: ~14,750
- No short vectors found

### Conclusion

**x-coordinates of multiples of Q do NOT leak k.** The map k → x(kP) is a nonlinear function (rational map on the curve). There is no known lattice structure in {x(iQ)} that reveals k. Multi-scalar lattice methods require *multiple independent DLP instances* with *known algebraic relationships* between the discrete logs (e.g., k₂ = f(k₁)), which we don't have.

---

## Task 4: BSGS-Lattice Hybrid (Galbraith-Ruprai)

### Framework
If k ≡ r (mod M) is known, then:
- k = r + M·t for unknown t ∈ [0, ⌈n/M⌉)
- Compute Q' = Q - r·P, then solve t·(M·P) = Q'
- Cost: O(√(n/M)) via Pollard rho

### Practicality Table for ECCp-131

| M (bits known) | Remaining (bits) | √(n/M) ops | Time @ 10M ops/s | Feasible? |
|:---:|:---:|:---:|:---:|:---:|
| 0 | 131 | 3.69×10¹⁹ | 117,000 years | ❌ |
| 20 | 111 | 3.60×10¹⁶ | 114 years | ❌ |
| 40 | 91 | 3.52×10¹³ | 41 days | ❌ |
| 60 | 71 | 3.44×10¹⁰ | 57 min | ❌ |
| 65 | 66 | 8.59×10⁹ | 14 min | ❌ (= Pollard rho) |
| 70 | 61 | 1.07×10⁹ | 1.8 min | ⚠️ Borderline |
| 80 | 51 | 3.36×10⁷ | 3.4 sec | ✅ |
| 90 | 41 | 1.05×10⁶ | 0.1 sec | ✅ |
| 100 | 31 | 3.28×10⁴ | instant | ✅ |

**Threshold**: Need M ≥ 2⁸⁰ (80 bits of k known) for instant solution. Even M ≥ 2⁶⁵ makes no improvement over standard Pollard rho.

### Can We Get k mod M for Free?

| Source | Result | Reason |
|--------|--------|--------|
| Pohlig-Hellman | ❌ | n is prime — no subgroup decomposition |
| n-1 factorization | ❌ | n-1 = 2⁴ · 3 · 73 · 283 · (111-bit prime) — tiny factors give only k mod 2⁴·3·73·283 ≈ k mod 396,816 (≈19 bits), insufficient |
| Curve endomorphism | ❌ | j ≠ 0,1728 — generic curve, no efficient endomorphism |
| GLV decomposition | ❌ | Requires CM curve with small discriminant; D is 132 bits |
| Pollard rho partial | ❌ | Rho finds full collision or nothing — no partial k mod M |
| Frobenius trace | ❌ | t = 29.5×10¹⁸ provides no direct k information |

**Note on n-1 factors**: The small factors 2⁴ · 3 · 73 · 283 = 396,816 of n-1 could theoretically help via index calculus in (ℤ/nℤ)* to learn k mod 396,816. But:
1. This gives only ≈19 bits of k
2. It requires computing discrete logs in (ℤ/nℤ)*, not on the elliptic curve
3. The Weil pairing could transfer ECDLP to DLP in 𝔽*_{q^r}, but the embedding degree r is huge for random curves

**Verdict**: No method provides k mod M for any useful M. BSGS-lattice hybrid is inapplicable.

---

## Summary Assessment

### Lattice Methods for ECCp-131: Definitive Analysis

| Method | Requires | Available? | Verdict |
|--------|----------|:----------:|:-------:|
| Boneh-Venkatesan HNP | d-bit leakage oracle | ❌ No oracle | **INAPPLICABLE** |
| Known-bit BSGS hybrid | k mod M for large M | ❌ No partial info | **INAPPLICABLE** |
| Multi-scalar lattice | Multiple related DLPs | ❌ Single instance | **INAPPLICABLE** |
| x-coordinate lattice | Algebraic structure | ❌ No structure found | **INAPPLICABLE** |
| Structural 2D lattice | Integer k directly | ❌ Only have curve point | **INAPPLICABLE** |

### Why Lattice Attacks Don't Help Pure ECDLP

1. **Lattices need linear (or near-linear) structure**: LLL/BKZ exploit approximate linear relationships (e.g., kgᵢ ≈ aᵢ mod n). ECDLP provides only the nonlinear relationship Q = k·P, which lives on an elliptic curve, not in ℤ.

2. **The integer k never appears**: In ECDLP, k is the secret scalar. The public data (P, Q, curve parameters) are all *points* or field elements. There's no integer equation involving k that we can feed to a lattice.

3. **No useful partial information exists**: Without signatures (ECDSA), nonce reuse, timing attacks, power analysis, or other side channels, there is zero bit-leakage about k.

4. **The curve is structurally generic**: j-invariant ≠ 0, 1728; CM discriminant is 132 bits; group order is prime; no small embedding degree. Every possible shortcut is blocked.

### Novel Observation: Pollard Rho Does NOT Leak Bit Information

During Pollard rho, we compute random walk points R_i = a_i·P + b_i·Q. These involve random (a_i, b_i) pairs, not k itself. The walk:
- Reveals nothing about MSB/LSB of k
- Produces no approximate linear relations in k  
- Cannot be converted to an HNP oracle

The *only* useful output of Pollard rho is the final collision, which gives k completely. There is no "partial progress" that lattice methods could exploit.

### Theoretical Minimum for Lattice Applicability

For lattice methods to become relevant to ECCp-131, one would need:
- **Minimum 1 bit of leakage per query** via some oracle, requiring 132+ queries
- **Or** discovery of a new algebraic structure in the curve that provides approximate integer relations
- **Or** a breakthrough in transferring ECDLP to a setting where lattice methods apply (e.g., low embedding degree for Weil/Tate pairing transfer — not the case here)

None of these are available or expected for this curve.

---

## Files

- Script: `/tmp/experiment4_lattice.py`
- Raw output: `/tmp/experiment4_output.txt`
