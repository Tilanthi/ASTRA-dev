# m1 last-mile identification table — census quadratic form ≡ Connes's restricted Weil form

**Status: CERTIFIED-INPUT (internal build). Nothing in this directory leaves the
repository without Glenn's gate (proposal 6). Built per the m1 commitment at the
Glenn-directive-3 reply §4.6: one publishable-SHAPED artefact, self-contained,
already verified, nothing live disputing it. The a-family and D* tables are
deliberately excluded — mid-flight, bundling would target a moving object.**

Bundle architecture follows the reference design named in the external-repo
audit (robopol/Riemann-hypothesis): manifest + hash validator, per-script status
labels, and a NON-DESTRUCTIVE reproduction test — studied, not copied.

## The identification, in one line

The census kernel `K_T200` IS the zero side of the Weil explicit formula:
`K_T200[i,j] = Σ_{0<Im ρ≤200} 2Re[U_i(ρ) conj(U_j(ρ))]`, with
`U_a(ρ) = ∫φ_a(t) e^{ρt} dt` (Mellin at ρ) on the frozen M8 genome basis at
window |t|≤8 — i.e. Connes's supp [λ⁻¹, λ] with **λ = e⁸ ≈ 2980.958, not
laddered**. Measured once at machine precision (max|diff| 4.65275e−47, relative
**5.72879e−46**) and re-derivable by this bundle's own test.

## The table

| id | claim | measured | status |
|----|-------|----------|--------|
| R1 | `K_T200[s1/M8]` = Σ_{0<Imρ≤200} 2Re[U_i conj(U_j)] recomputed from frozen genomes, mpmath zetazero, dps 45 | max abs diff 4.65275e−47, scale 0.0812169, **rel 5.72879e−46** | MEASURED-REPRODUCIBLE |
| R2 | T=200 zero cut is exactly 79 zeros: Im ρ₇₉ = 198.0153097 ≤ 200 < Im ρ₈₀ = 201.2647519; agrees with the M64 build's `n_zeros` field | 79 zeros | MEASURED-REPRODUCIBLE |
| R3 | Surgery semantics: `quad_ex(g,0) = 2·gram(g)` exactly (k=2,3,7) — control cell = double zero on the line; δ>0 cells inject the conjugate-symmetric pair ½±δ+ig, exactly the zero-side contribution of a zero OFF the line | max diff 0.0 | MEASURED-REPRODUCIBLE |
| R4 | The zero-side construction is stated in the sealed artefact itself — S3's convention string, verbatim: `raw genome basis; K_FE = sum_{0<Im rho<=T} 2Re[U_a(rho) conj(U_b(rho))]; U_a(rho)=int phi_a e^{rho t}; breakpoints per spec; mp.dps 45` | verbatim | CERTIFIED-SEALED |
| R5 | W-side (prime+archimedean) equality on our basis = m3's Kowalski Prop 1.2.1 identity check, receipted in S3's note field; cited, not redone (primary measurement's own scope statement) | — | CITED-NOT-REDONE |
| R6 | CLASSIFICATION: same Weil quadratic form, **opposite sides of the identity** — ours a doubly-truncated (T=200, M-Galerkin at λ=e⁸) zero-side realisation + rank-4 falsification surgery; his the pristine operator on the λ-axis. NOT a linear reparametrisation; NOT unrelated. Consequence: our M-ladder measures Galerkin faithfulness of our probe at fixed λ=e⁸, not Connes's open (a)/(b) | — | CLASSIFICATION-FIRST-LOOK (m3 second look AWAITED) |

## Side-by-side (basis: log variable t = log u, inner product du/u)

| Connes [S4] | ours [S1,S3] |
|---|---|
| Q_W_λ(f,f) = Σ_v W_v(f∗f−conv) | K_S = K_T200 − gram(z_k) − gram(z_{k+1}) + quad_ex(g,δ) |
| prime+archimedean side of Weil EF | K_T200 = zero side, T=200 [R1] |
| operator A_λ, L²([λ⁻¹,λ]) | M×M Galerkin matrix, G-metric |
| supp [λ⁻¹,λ], λ free (→∞) | fixed window \|t\|≤8 (λ=e⁸) |
| no zero appears in construction | zeros are the construction [R1] |
| pristine form | rank-4 surgery: −2 on-line zero modes, +pair at ½±δ+ig [R3] |
| open (a): λ_min simple+even, λ→∞ | controls: surgically modified form stays ≥ −1e−12 at each M (M-axis) |
| open (b): k_λ ~ θ_x | (no counterpart) |
| Galerkin: trig N=100–250 | Galerkin: M ∈ {8,64} genome bumps |

## Bundle members

| file | role |
|------|------|
| `identification_table.json` | machine-readable table (this document rendered from it) |
| `manifest.json` | every member + input: sha256, repo, pinning commit, status label |
| `validate_manifest.py` | hash validator — all entries vs files on disk |
| `test_reproduction.py` | non-destructive reproduction test: `--quick` (manifest + convention + zero cut, ~5 s), default (+ K[0,0] re-derivation, ~2 min), `--full` (all 8×8 + surgery exact-equality, ~15 min) |
| `test_reproduction.out` | receipt of the default run |

## Sealed inputs (never modified; hashes in `manifest.json`)

- **[S1]** `data/code/machine1_heat78c_survivor_census.py` (Riemann_exchange, e926548) — sealed scored runner; `make_phi` imported from it, never re-typed (trap #S12)
- **[S2]** `data/code/machine1_heat70_genomes_m8_m64.json` (Riemann_exchange, 780f57b) — frozen genome basis
- **[S3]** `Riemann/experiments/orchestrator/heat72k_identity_target_m8.json` (ASTRA-dev-main, feee806) — K_T200/G_raw M8 + convention string + m3-identity-check note
- **[S4]** `2602.04022v1.pdf` (Riemann_exchange, 961954d) — Connes
- **[S5]** `data/machine1_heat78a_m64_kernel.json` (Riemann_exchange, 94d9e4f) — M64 build, n_zeros cross-check
- **[A1]** `data/code/machine1_ident1_connes_vs_ks.py` + **[A2]** `.out` (Riemann_exchange, 3c15f90) — primary measurement + receipt (842.4 s)

Primary measurement letter: m1-L173 (ident-check 1, first look). m3's
independent second look from sealed sources — offered at m3-L167 §2, charter
condition B — had not landed when this bundle was built; row R6 carries the
first-look label until it does.

**No proof claim. Standing sentence unchanged: we have no route to a proof.**
