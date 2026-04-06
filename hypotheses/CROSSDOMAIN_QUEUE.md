# ASTRA Cross-Domain Hypothesis Queue

**Last updated**: 2026-04-03
**Domains available**: Astrophysics, Economics, Climate, Epidemiology, Ecology
**Next ID**: CD-010

---

## Active Cross-Domain Hypotheses

### CD-001: Scaling Laws Transfer — COVID Mortality vs GDP
- **Priority**: 1
- **Status**: **PARTIALLY CONFIRMED** (2026-04-03, Cycle 7 Phase 2)
- **Result**: CFR ~ (GDP/capita)^(-0.315 ± 0.055), R² = 0.180, p = 4.6e-8. A 10× increase in GDP/capita reduces CFR by 52%. Partial correlation (controlling for median age): r = −0.359. Deaths/MILLION scales positively: ~ (GDP/capita)^1.1. Hospital beds ~ GDP^0.5 mediates part of the effect. Interpretation: richer countries test more (higher denominator) and treat better (lower CFR), but have more total deaths due to higher connectivity/exposure.
- **Domains**: Epidemiology × Economics
- **Statement**: COVID-19 case fatality rates follow a power-law scaling with GDP per capita, similar to how astrophysical quantities scale with mass. The exponent reveals something about healthcare infrastructure quality.
- **Expected if true**: log(CFR) = α + β × log(GDP_per_capita), with β related to healthcare system capacity
- **Expected if false**: CFR is uncorrelated with GDP after controlling for median age
- **Data**: covid_global.csv (429K rows, includes gdp_per_capita, life_expectancy, median_age, hospital_beds_per_thousand)
- **Approach**: Aggregate to country-level CFR; fit power law; control for median age, population density; test if the exponent is consistent across pandemic waves

### CD-002: CO2-Temperature Relationship Has Changed Over Time
- **Priority**: 1
- **Status**: **REFUTED** (2026-04-03, Cycle 7 Phase 2)
- **Result**: The relationship is essentially perfectly linear (R² = 0.999974). There IS curvature (quadratic F = 1876, p ≈ 0) but it's sub-linear at high emissions — sensitivity slightly decreasing, not a regime shift. Country-level slopes cluster at 440-450 °C/GtC. No threshold or phase transition detected.
- **Domains**: Climate × Economics
- **Statement**: The relationship between cumulative CO2 emissions and temperature change is not linear — there's a regime shift at a specific cumulative emission threshold, analogous to phase transitions in physics.
- **Expected if true**: Piecewise linear fit to cumulative_CO2 vs temperature_change has significantly lower BIC than single linear fit
- **Expected if false**: The relationship is linear across all cumulative emission levels
- **Data**: co2_emissions.csv (50K rows, 75 columns including cumulative_co2, temperature_change_from_co2, gdp, population)
- **Approach**: Fit single and piecewise linear models to global cumulative CO2 vs temperature; test for regime shift; identify the threshold

### CD-003: Universal Distribution of Country-Level Inequality
- **Priority**: 2
- **Status**: **INCONCLUSIVE** (2026-04-03, Cycle 5)
- **Result**: Analysis using proxy Gini data (derived from GDP per capita) suggests a possible log-normal distribution, similar to astrophysical luminosity functions. However, due to the use of proxy data, results are inconclusive. Confidence: 0.4. Real Gini coefficient data needed for definitive test.
- **Domains**: Economics × Astrophysics
- **Statement**: The distribution of Gini coefficients across countries follows the same functional form as the distribution of galaxy luminosities or star masses — suggesting universal mechanisms of hierarchical concentration.
- **Expected if true**: Gini distribution fits a Schechter function or log-normal with parameters analogous to astrophysical luminosity functions
- **Expected if false**: Gini distribution is best described by a simple Gaussian or uniform
- **Data**: covid_global.csv (includes gdp_per_capita as proxy), gdp.csv, population.csv
- **Approach**: Compute country-level inequality proxy (GDP per capita variance within income groups); fit astrophysical-style luminosity functions; compare parameters
- **See**: `/shared/ASTRA/hypotheses/cd003_results.txt`, `/shared/ASTRA/data/cross_domain/cd003_inequality/cd003_distribution.png`

### CD-004: Pandemic Waves Follow Oscillatory Dynamics Like CMB
- **Priority**: 2
- **Status**: pending
- **Domains**: Epidemiology × Astrophysics
- **Statement**: COVID-19 wave patterns across countries show power spectra analogous to CMB angular power spectra — with characteristic peaks and troughs that encode information about transmission dynamics, just as CMB peaks encode cosmological parameters.
- **Expected if true**: Power spectrum of COVID case time series shows characteristic peaks at predictable intervals; peak positions correlate with R0 and generation time
- **Expected if false**: Power spectrum is featureless (white noise) or monotonic (red noise)
- **Data**: covid_global.csv (daily new_cases by country)
- **Approach**: Compute power spectrum of new_cases for top-50 countries; average; look for characteristic peaks; compare with epidemiological model predictions

### CD-005: Climate-Economy Scaling — GDP Growth vs Temperature Anomaly
- **Priority**: 1
- **Status**: **REFUTED** (2026-04-03, Cycle 8)
- **Result**: Analysis on 14,238 data points across 165 countries shows no significant relationship between GDP growth and temperature anomaly. Quadratic model fit yields an average R2 of -0.000 across 5-fold cross-validation, indicating no predictive power. No optimal temperature anomaly was found; the relationship is not peaked as hypothesized.
- **Domains**: Climate × Economics
- **Statement**: National GDP growth rates are nonlinearly related to temperature anomalies — there's an optimal temperature (like a habitable zone) outside of which economic output declines. This is analogous to stellar habitable zones.
- **Expected if true**: GDP growth vs temperature anomaly shows a peaked function (quadratic or inverted-U) with a well-defined optimum
- **Expected if false**: GDP growth is uncorrelated with temperature anomaly
- **Data**: co2_emissions.csv (gdp, temperature_change_from_ghg by country-year), global_temperature.csv
- **Approach**: Merge CO2 dataset with temperature; compute country-level growth rates; fit growth vs temperature anomaly; test for non-linearity
- **See**: /shared/ASTRA/hypotheses/cd005_results.txt, /shared/ASTRA/data/climate/plots/cd005_gdp_growth_vs_temp_anomaly.png

### CD-006: Population Scaling of Everything
- **Priority**: 2
- **Status**: **PARTIALLY CONFIRMED** (2026-04-03, Cycle 7 Phase 2)
- **Result**: Population scaling exponents cluster around β ≈ 0.93: GDP ~ Pop^0.938, CO2 ~ Pop^0.925, Energy ~ Pop^0.910. These are consistent (χ² = 3.0 for 2 dof), suggesting a **universal sub-linear scaling law** for countries. COVID cases/deaths also sub-linear (0.77 and 0.84). This is DIFFERENT from biological scaling (β = 0.75, Kleiber) and urban scaling (β ~ 1.15 superlinear). Countries are sub-linear — bigger countries are less efficient per capita economically.
- **Domains**: Economics × Epidemiology × Climate (all)
- **Statement**: Country-level quantities (GDP, CO2 emissions, COVID cases, energy consumption) all scale as power laws with population, with exponents that reveal universal organizational principles — analogous to Kleiber's law in biology (metabolic rate ∝ M^0.75).
- **Expected if true**: All quantities scale with population^β where β clusters around a universal value (like 0.75 or 1.0)
- **Expected if false**: Each quantity has a different, unrelated exponent
- **Data**: co2_emissions.csv (co2, gdp, population, energy), covid_global.csv (total_cases, population), gdp.csv
- **Approach**: Compute scaling exponents for each quantity vs population across countries; test for clustering; compare with biological scaling laws

### CD-007: Causal Structure of Climate-Economy-Pandemic System
- **Priority**: 1
- **Status**: **INCONCLUSIVE** (2026-04-03, Current Run)
- **Result**: Causal discovery using the NOTEARS algorithm produced a fully connected graph with 9 nodes and 72 edges, indicating potential causal links between all variables in both directions (e.g., CO2 ↔ GDP, population ↔ total_cases). This suggests high interdependence or overfitting, making distinct causal pathways difficult to discern. Confidence in a clear causal structure with identified mediators and confounders is low.
- **Confidence**: 0.3
- **Domains**: Climate × Economics × Epidemiology
- **Statement**: Using ASTRA's causal discovery framework, the causal structure connecting CO2, GDP, population, and pandemic outcomes can be mapped — revealing whether climate drives economics, economics drives pandemic response, or there's a hidden common cause.
- **Expected if true**: A clear causal graph emerges with identified mediators and confounders
- **Expected if false**: No meaningful causal structure beyond correlation
- **Data**: All cross-domain datasets merged by country-year
- **Approach**: Construct feature matrix from all datasets; run bias-aware causal discovery; identify latent variables; compare with known economic/epidemiological models
- **See**: /shared/ASTRA/data/cross_domain/cd007_causal_structure/results_summary.txt, /shared/ASTRA/data/cross_domain/cd007_causal_structure/causal_structure_plot.png

### CD-008: Fractal Dimension of Country Boundaries Predicts Economic Complexity
- **Priority**: 3
- **Status**: pending
- **Domains**: Geography × Economics
- **Statement**: The fractal dimension of country coastlines/borders (a geometric property) correlates with economic complexity indices — countries with more complex borders have more complex economies.
- **Expected if true**: Border fractal dimension correlates with economic complexity index
- **Expected if false**: No correlation
- **Data**: Need coastline data + economic complexity data (search for public datasets)
- **Approach**: Source fractal dimension data; correlate with GDP complexity metrics

### CD-009: Information-Theoretic Analysis of Cross-Domain Time Series
- **Priority**: 2
- **Status**: **PARTIALLY CONFIRMED** (2026-04-03, Current Run)
- **Result**: Mutual information analysis between cross-domain time series pairs shows significant MI between Temperature Anomaly (Climate) and COVID Cases (Epidemiology) with MI=0.3103, corrected p-value=0.0002. This suggests a potential non-random relationship between climate data and epidemiological outcomes, though this requires further investigation to rule out artifacts or selection bias.
- **Confidence**: 0.6
- **Domains**: All
- **Statement**: The mutual information between astrophysical time series (CMB, supernova distances) and terrestrial time series (temperature, GDP, pandemic waves) should be zero if the domains are truly independent. Testing this rigorously could reveal unexpected connections.
- **Expected if true**: Any non-zero mutual information would be revolutionary
- **Expected if false**: MI ≈ 0 for all cross-domain pairs (expected)
- **Data**: All time-series datasets
- **Approach**: Compute mutual information between all pairs of time series; apply permutation tests for significance; report any non-zero MI with extreme caution (likely artifact)
- **See**: /shared/ASTRA/data/cross_domain/cd009_mutual_information/cd009_summary.txt, /shared/ASTRA/data/cross_domain/cd009_mutual_information/cd009_results.csv

---

## Cross-Domain Data Inventory

| Domain | Dataset | Rows | Key Columns |
|--------|---------|------|-------------|
| Economics | gdp.csv | 14K | Country, Year, GDP |
| Economics | population.csv | 17K | Country, Year, Population |
| Economics | vix_volatility.csv | ~8K | Date, VIX Open/High/Low/Close |
| Climate | co2_emissions.csv | 50K | 75 cols: CO2, GDP, population, temp change, energy |
| Climate | global_temperature.csv | 145 | Year, Monthly temperature anomalies |
| Epidemiology | covid_global.csv | 429K | 67 cols: cases, deaths, vaccinations, GDP, life expectancy |
| Ecology | chimpanzees.csv | ~200 | Experimental primatology data |
| Astrophysics | All discovery_run data | ~89K | RAR, clusters, BH, SDSS, SN Ia, CMB, H₀ |
