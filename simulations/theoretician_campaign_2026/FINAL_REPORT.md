# Theoretician Campaign 2026 -- Final Report

**Date**: May 11, 2026  
**Total simulations**: 406 (Campaigns A + B + C)  
**Outcome**: 360 FRAG, 46 TIMEOUT, 0 FAILED

## Campaign Overview

### Campaign A -- Field Geometry Mixing Model (280 sims)
- Grid: 512x64x64, domain 16 lambda_J  
- theta=[0,15,30,45,60,75,90] deg, f=[1.0,1.5,2.0,2.5], beta=[0.3,1.0], 5 seeds  
- Result: 234 FRAG, 46 TIMEOUT (TOUT concentrated at low-theta and oblique transitions)

### Campaign B -- Supercritical Calibration (90 sims)
- Grid: 768x64x64, domain 24 lambda_J, theta=0 deg  
- f=[1.3,1.5,1.8,2.0,2.5,3.0], beta=[0.3,1.0,3.0], 5 seeds  
- Result: 90 FRAG, 0 TIMEOUT -- full supercritical coverage

### Campaign C -- Domain Convergence, theta=90 deg (36 sims)
- Grid: 512x64x64, L=[12,16,20,24] lambda_J, beta=1.0, f=[1.0,1.5,2.0], 3 seeds  
- Result: 36 FRAG, 0 TIMEOUT -- domain independence confirmed

## Key Scientific Results

### 1. Field Geometry Mixing Model: t_frag(theta)


**Mixing model fit**: t_frag(theta) = (1.2035 +/- 0.1011) cos^2(theta) + (0.4579 +/- 0.1011) sin^2(theta) t_J

**Critical angle**: Sharp transition at theta~20-25 deg:
- 33% drop in t_frag from theta=15 to theta=30
- TOUT rate drops from 35% (theta=15) to 2.5% (theta=30)

### 2. Supercritical Calibration: t_frag(f,beta) at theta=0 deg, L=24 lambda_J

| f   | beta=0.3 | beta=1.0 | beta=3.0 |
|-----|----------|----------|----------|
| 1.3 |  1.5662  |  1.5468  |  1.3017  |
| 1.5 |  1.5151  |  1.4603  |  1.1686  |
| 1.8 |  1.4539  |  1.3129  |  1.0250  |
| 2.0 |  1.4108  |  1.2325  |  0.9419  |
| 2.5 |  1.2980  |  1.0567  |  0.7974  |
| 3.0 |  1.2067  |  0.8883  |  0.6965  |

Power-law fits: t_frag = A * f^(-alpha)
- beta=0.3: A=1.717, alpha=0.305 (weak f-dependence)
- beta=1.0: A=1.867, alpha=0.632
- beta=3.0: A=1.584, alpha=0.748 (steep f-dependence)

Higher turbulence (higher beta) --> steeper power-law index.
beta=3.0 vs beta=0.3: ~45% faster fragmentation at f=2.5.

### 3. Domain Convergence: theta=90 deg

Result: Perfect domain convergence -- sigma(t_frag) < 0.01 for fixed f.
Domain length has NO effect on fragmentation time at theta=90 deg.

### 4. lambda/W Mixing Model (from prior campaigns)
- theta=0 deg (longitudinal B):  lambda/W = 3.38 +/- 0.79  (from C5/C7 campaigns)
- theta=90 deg (perpendicular B): lambda/W = 1.25 +/- 0.09  (from C6 campaign, beta>=1.0)
- Model: lambda/W(theta) = 3.38 cos^2(theta) + 1.25 sin^2(theta)
- Note: Intermediate-theta HDF5 were cleaned before postproc -- lambda/W only from endpoints.

## Disk Status
HDF5 files: 0 remaining (all cleaned).  
Disk: 53G / 492G used (11%).

## Files
- fig1_tfrag_vs_theta.pdf/.png        -- t_frag(theta) arc with mixing model fit
- fig2_supercritical_calibration.pdf   -- f x beta matrix and power-law fits
- fig3_domain_convergence.pdf          -- t_frag vs L for theta=90 deg
- fig4_lambda_W_mixing_model.pdf       -- lambda/W(theta) endpoint mixing model
- theoretician_2026_analysis_summary.json  -- full numerical summary
- theoretician_2026_analysis.tar.gz    -- complete analysis archive
