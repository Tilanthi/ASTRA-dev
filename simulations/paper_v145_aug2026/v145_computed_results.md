# Supporting computations for the revised manuscript (internal record)

## 1. 1024 x 256 x 256 convergence test (completed)

Both ladder endpoints repeated at three resolutions. dx = 0.0625, 0.03125 and 0.015625 lambda_J;
a factor of four in linear resolution and 64 in cell count above the production grid.
`/data/contraction_ladder_aug2026/LADXL_A0p0`, `LADXL_A1p0`.

| Run   | grid            | rho_eff/rho_0 | n_peak | lambda_peak/lambda_J | lambda_peak/22H(rho_eff) |
|-------|-----------------|---------------|--------|----------------------|--------------------------|
| A = 0 | 256 x 64^2      | 0.66          | 5      | 3.20                 | 1.088                    |
|       | 512 x 128^2     | 0.76          | 6      | 2.67                 | 0.987                    |
|       | 1024 x 256^2    | 0.79          | 6      | 2.67                 | 1.011                    |
| A = 1 | 256 x 64^2      | 0.32          | 4      | 4.00                 | 0.939                    |
|       | 512 x 128^2     | 0.24          | 4      | 4.00                 | 0.839                    |
|       | 1024 x 256^2    | 0.18          | 4      | 4.00                 | 0.729                    |

**The selected mode is converged.** n_peak is identical at 512 and 1024 for the static run and at
all three resolutions for the dynamical one, so lambda_peak takes literally the same value.
No maximum migrates towards the grid scale on refinement, and no new maximum appears at shorter
wavelength at 1024 x 256^2 in either case. That is the specific behaviour a resolution-limited
spectrum would show, and it is absent.

The residual variation in lambda_peak/22H therefore comes from rho_eff, not from the measured
wavelength: rho_eff at the mid-point of the fitting window depends slightly on how well the
rebound is resolved. The physical statement survives at every resolution and strengthens with it
(static 1.09/0.99/1.01; dynamical 0.94/0.84/0.73).

CPU: LADXL_A1p0 used 9.84e3 core-seconds at 64 ranks; both runs reached tlim = 2.0 t_J.

## 2. Contraction ladder, adopted fit (unchanged)
Censored maximum-likelihood fit over 17 runs (3 left-censored upper limits, mode quantisation in
the per-point error):

    lambda_select ~ rho_eff^(-0.485), 1-sigma [-0.540, -0.435], intrinsic scatter 0.094 dex,
    over rho_eff = 0.35-3.47 rho_0.  Predicted -1/2.

Quoted as -0.49 +/- 0.05 throughout. (The earlier -0.55 +/- 0.12 was the five-run fit and has been
removed everywhere.)

Normalised by the instantaneous equilibrium scale: lambda_peak/22H(rho_eff) = 1.09 (static),
1.12 (A = 0.1), and 0.79-1.04 with median 0.87 for the remaining fifteen. The residual deficit
relative to the *instantaneous* equilibrium is therefore ~15 per cent at production resolution,
an order of magnitude smaller than the factor of three to five obtained by comparing with the
*initial* equilibrium wavelength. This is now panel (d) of the ladder figure.

## 3. Projected Ostriker column-density FWHM (new derivation in Appendix C)
For rho(r) = rho_c [1 + (r/R_flat)^2]^-2 with R_flat = sqrt(8) H, integrating along the line of
sight gives N(x) ~ [1 + (x/R_flat)^2]^(-3/2), a Plummer of index p = 3. Half maximum at
x/R_flat = (2^(2/3) - 1)^(1/2) = 0.766, so

    W_FWHM = 1.532 R_flat = 4.33 H,   and   lambda_m / W_FWHM = 22 / 4.33 = 5.1.

The upper end of the quoted 5-6 band comes from the Gaussian inner-profile convention (~5.9).
The benchmark is now stated with its definition attached.

## 4. Numbers previously inconsistent, now reconciled
- ladder exponent: -0.49 +/- 0.05 everywhere (was -0.49 in Sec. 5.3 and -0.55 in the Conclusions)
- ladder size: 17 runs everywhere (was "five-point ladder" in the Introduction and Conclusions)
- null p-values: p_fit and p_cv given as separate labelled columns in one table
- Table 3 header f_elig [N_elig]; Table 5 caption parenthesis; "the benchmark used here is 5-6"
- "(~10 per cent for the primary regions), a change dominated by Aquila"

## 5. Still not done, and stated as such in the paper
Force-balanced Fiege-Pudritz helical equilibrium (the four specific technical obstacles are now
set out in Section 6.3); continuously driven turbulence; map-level close-pair injection;
injection-recovery validation of the core-masking step; 3-D dust reconstruction along the
Aquila/Serpens sightline.
