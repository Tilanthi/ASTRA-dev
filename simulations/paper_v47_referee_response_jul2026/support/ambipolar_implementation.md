# Ambipolar-diffusion implementation and η_AD physical scaling (answers R2-16, R1-minor η_AD)

## Governing equations
Athena++ (Stone et al. 2020) solves the non-ideal induction equation with the ambipolar term:
  ∂B/∂t = ∇×(v×B) − ∇×[ η_AD ( (∇×B)×B̂ )×B̂ ],
i.e. the ambipolar electromotive force E_AD = −η_AD [ J⊥ ] where J = ∇×B and ⊥ denotes the
component perpendicular to B. Ohmic (η_O) and Hall (η_H) terms are set to zero in these runs.
The field-diffusion module is `src/field/field_diffusion/` with the ambipolar EMF assembled in
`diffusivity.cpp`; the coefficient is read from `<problem> eta_ad`.

## Units and physical scaling
In code units (c_s = 1, λ_J = 1, four_pi_G = 4π²), η_AD has units of [length²/time] = λ_J² / t_J.
The ambipolar diffusivity physically is
  η_AD = B² / (4π γ_AD ρ_i ρ) = v_A² / (γ_AD ρ_i),
with γ_AD ≈ 3.5×10¹³ cm³ g⁻¹ s⁻¹ and ρ_i = μ_i m_H n_i, n_i = ξ n^{1/2} (ξ ≈ 3×10⁻³ cm⁻³/² for
cosmic-ray ionisation; McKee et al. 2010). At n₀ ~ 10⁴ cm⁻³ this gives an ionisation fraction
x_e = n_i/n ~ 10⁻⁷–10⁻⁸ and an ambipolar Reynolds number R_AD = v_A L / η_AD ~ a few–tens on
filament scales, corresponding to the swept η_AD = 0.001–0.1 (dimensionless) range: η_AD = 0.001–0.01
brackets the fiducial dense-filament value, and η_AD = 0.05–0.1 represents lower-ionisation
(higher-diffusivity) conditions. State this mapping so the "32/36 bead" result is anchored to real
conditions rather than a pure numerical sweep.

## Timestep and numerical-diffusion caveat
The explicit ambipolar timestep scales as Δt_AD ∝ dx²/η_AD, which is why these runs are far slower
than the ideal grid and reach gravitational runaway before a converged wavelength (§4.6.6). A
resolution scan is needed to confirm the *physical* η_AD exceeds the *numerical* magnetic diffusivity
(η_num ~ v dx); this is the R2-13.7 pending item. NOTE: the perpendicular ambipolar beading is
measured at cells-per-Jeans ~1–2 (Truelove violated), so these wavelengths are resolution-limited.
