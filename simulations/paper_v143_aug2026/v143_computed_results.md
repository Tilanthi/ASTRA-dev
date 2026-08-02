# Supporting computations for v143 (internal record, not part of the manuscript)

## 1. Extended contraction ladder (17 runs) and censored regression

Seventeen runs at A = 0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.75, 0.85,
0.9, 1.0, 1.2, 1.4 on 256x64x64 (dx = 0.0625 lambda_J), L_x = 16 lambda_J periodic, plus
512x128x128 at A = 0 and A = 1.  `/data/contraction_ladder_aug2026/`.

| A    | rho_eff/rho_0 | lambda_peak/lambda_J | lambda_peak/22H(rho_eff) | note        |
|------|---------------|----------------------|--------------------------|-------------|
| 0.00 | 1.417         | 3.20                 | 1.088                    |             |
| 0.10 | 2.961         | 2.29                 | 1.123                    |             |
| 0.15 | 3.462         | <1.60                | <0.850                   | upper limit |
| 0.20 | 3.470         | <1.60                | <0.851                   | upper limit |
| 0.25 | 3.240         | <1.60                | <0.823                   | upper limit |
| 0.30 | 2.930         | 2.00                 | 0.978                    |             |
| 0.35 | 2.525         | 2.29                 | 1.037                    |             |
| 0.40 | 2.190         | 2.29                 | 0.966                    |             |
| 0.50 | 1.825         | 2.29                 | 0.882                    |             |
| 0.60 | 1.478         | 2.67                 | 0.926                    |             |
| 0.70 | 1.202         | 2.67                 | 0.835                    |             |
| 0.75 | 1.073         | 2.67                 | 0.789                    |             |
| 0.85 | 0.878         | 3.20                 | 0.856                    |             |
| 0.90 | 0.799         | 3.20                 | 0.817                    |             |
| 1.00 | 0.676         | 4.00                 | 0.939                    |             |
| 1.20 | 0.472         | 4.00                 | 0.785                    |             |
| 1.40 | 0.349         | 5.33                 | 0.901                    |             |

512^3-equivalent endpoints: A = 0 -> lambda/22H = 0.987; A = 1 -> 0.839.

**Censored maximum-likelihood fit** (3 upper limits treated as left-censored in ln lambda;
axial mode quantisation lambda = L_x/n folded into the per-point uncertainty):

    slope = -0.485,  1-sigma [-0.540, -0.435],  intrinsic scatter 0.094 dex,
    over rho_eff = 0.35-3.47 rho_0 (factor 10).   Predicted: -1/2.

Discarding the censored points and fitting the rest by OLS gives -0.393 (r = -0.947); the
upper limits all lie at the high-density end, so omitting them flattens the fit. This is why
they must be included.

**A is not the control parameter.** rho_c(t) overshoots to as much as 11x its initial value
within ~0.3 t_J and then rebounds below it, so rho_eff is non-monotonic in A: it peaks at
~3.5 rho_0 near A ~ 0.2 and falls to 0.35 rho_0 at A = 1.4. Figure `fig_ladder.pdf` shows
rho_c(t), the mass-weighted v_r(t) within 0.6 lambda_J of the axis, the growth-fit window and
the epoch at which rho_eff is evaluated.

## 2. Core population splits

| Cloud   | sample                | N_assoc | S_local | S_global | CoV  |
|---------|-----------------------|---------|---------|----------|------|
| Orion B | all                   | 995     | 1.77    | 3.39     | 0.83 |
|         | starless + prestellar | 961     | 1.79    | 3.51     | 0.83 |
|         | prestellar            | 569     | 1.83    | 5.93     | 0.82 |
| Aquila  | all                   | 308     | 1.66    | 3.44     | 0.65 |
|         | starless + prestellar | 267     | 1.78    | 3.97     | 0.62 |
|         | prestellar            | 223     | 1.78    | 4.75     | 0.73 |
| Perseus | all                   | 501     | 2.97    | 5.78     | 0.96 |
|         | starless + prestellar | 438     | 2.99    | 6.61     | 0.95 |
|         | prestellar            | 282     | 2.83    | 10.27    | 1.01 |
| Taurus  | all                   | 463     | 1.81    | 4.52     | 1.36 |
|         | starless + prestellar | 424     | 1.84    | 4.94     | 1.34 |
|         | prestellar            | 53      | 2.04    | 39.52    | 1.30 |

Type census (starless / prestellar / protostellar): Orion B 995/806/66; Aquila 216/469/64;
Perseus 331/353/132; Taurus 437/54/40.

S_local is invariant to within 0.2 across all three samples in every cloud; CoV to within 0.1.
S_global rises steeply as the sample is restricted, since L is fixed while N falls. The
local/global separation therefore widens under restriction to prestellar cores. The Taurus
prestellar S_global (53 cores) is not meaningful.

## 3. Benchmark unit conversion

lambda_J = c_s sqrt(pi/G rho) is evaluated at the initial background density rho_0;
H = c_s/sqrt(4 pi G rho_c) at the cylinder central density rho_c = 2.24 rho_0. Then

    22H / lambda_J(rho_0) = 22 / [sqrt(4 pi x 2.24) x sqrt(pi)] = 2.34,

which is the "2.3 lambda_J" of the independent eigenvalue solve. At a common density
lambda_J = 2 pi H, so 22H = 3.50 lambda_J(rho_c). The two statements are the same number.

## 4. Still running at write-up

1024x256x256 convergence runs (LADXL_A0p0, LADXL_A1p0) launched on 96 ranks; at write-up they
had reached t ~ 0.29 of tlim = 2.0. The resolution argument in the manuscript rests on the
128^3-512^3 ladder and the 512-cell ladder endpoints, both complete.
