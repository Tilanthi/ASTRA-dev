# Supporting computations for the revised manuscript (internal record)

## 1. Equilibrium-control stationarity
Run: `/data/validation_jul2026/results/EQREC_main_ctrl` (Ostriker cylinder, drag_rate = 8,
t_damp_end = 6, no kick).

| window (t_J) | |grav-E| drift | max |v_r|_rms / c_s |
|--------------|---------------|---------------------|
| 0 - 2 (drag transient) | 7.8 %  | 0.057 |
| 4 - 6 (end of relaxation) | 0.61 % | 0.012 |
| 6 - 8 (measurement window) | 1.65 % | 0.024 |
| 6 - 9.25 | 2.96 % | 0.031 |

grav-E between t = 6 and t = 8 changes by -1.71 %, i.e. the residual drift is a slow
EXPANSION, not a contraction. It therefore cannot mimic the contracting case, and biases the
control towards longer wavelengths (the conservative direction).

## 2. Imperfect periodic null
Comb with slowly varying wavelength + positional jitter + random dropouts; KS statistic
calibrated by bootstrap (300 resamples, floor p = 3.3e-3).

| Cloud | n gaps | lam0 (pc) | mild (+/-25 %, 25 % jitter, 15 % dropout) | strong (+/-50 %, 25 %, 35 %) |
|-------|--------|-----------|-------------------------------------------|------------------------------|
| Orion B | 699 | 0.1773 | p = 0.0033, D = 0.125 | p = 0.0033, D = 0.152 |
| Aquila  | 168 | 0.1662 | p = 0.0033, D = 0.125 | p = 0.0033, D = 0.192 |
| Perseus | 438 | 0.2969 | p = 0.0033, D = 0.204 | p = 0.0033, D = 0.180 |
| Taurus  | 440 | 0.1805 | p = 0.0033, D = 0.226 | p = 0.0033, D = 0.186 |

Both versions are rejected in all four clouds at the bootstrap floor. The rejection of
quasi-periodicity therefore extends beyond the idealised jittered comb.

## 3. N = 4 sampling-variance check
Observed S_local = 1.77, 1.66, 2.97, 1.81; range 1.31, sd 0.532.
Drawing four samples of the observed sizes from the pooled gap distribution of all four clouds
(20,000 trials): median range 0.242, 95th percentile 0.480, median sd 0.094.

    p(null range >= observed range) = 5e-5

The cloud-to-cloud differences in the conditional statistic are real, not finite-N noise.
What N = 4 cannot support is extrapolation to a population or identification of the driving
cloud property.

## 4. Inhomogeneous-null p-values, both versions, as tabulated

| Cloud   | F_obs | median F_null | p_fit  | p_cv  |
|---------|-------|---------------|--------|-------|
| Orion B | 2.8   | 3.6           | 0.98   | 1.00  |
| Aquila  | 1.6   | 2.1           | 0.88   | 0.27  |
| Perseus | 5.7   | 7.1           | 0.96   | 0.995 |
| Taurus  | 25.2  | 13.4          | 2e-4   | 0.005 |

p_fit uses an intensity exponent fitted to the cloud's own cores; p_cv one predicted from the
other three under leave-one-cloud-out cross-validation. Both from 1e4 realisations. The two
versions were previously quoted in different places without labels; they are now given
together in a single table and p_fit is used in the text throughout.

## 5. Numerical configuration as run (for the methods section)
Athena++ v21.0, ISOTHERMAL equation of state P = rho c_s^2 (energy equation NOT evolved, no
cooling), HLLD isothermal Riemann solver, piecewise-linear reconstruction in primitives,
second-order van Leer integrator, CFL 0.3, constrained transport, FFT Poisson solver,
gravitational boundaries periodic along the axis and zero-gradient transversely.

## 6. Still running at write-up
1024x256x256 convergence runs (LADXL_A0p0, LADXL_A1p0), 12 snapshots of 21 at write-up. The
resolution argument rests on the completed 128^3-512^3 ladder and the 512-cell ladder
endpoints.
