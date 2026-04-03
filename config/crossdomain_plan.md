# ASTRA Cross-Domain Expansion Plan

## Goal
Transform ASTRA from an astrophysics-specific agent into a general-purpose scientific discovery engine that finds cross-domain connections.

## Domains to Add

### Tier 1 (Immediate — data freely available)
1. **Genomics/Bioinformatics** — Gene expression, protein structures, disease correlations
2. **Economics** — Market data, GDP, inequality metrics, trade networks
3. **Climate Science** — Temperature records, CO2, ocean data, ice cores
4. **Materials Science** — Crystal structures, property databases, superconductors
5. **Epidemiology** — Disease spread, mortality data, intervention effects

### Tier 2 (Medium-term — needs API access)
6. **Drug Discovery** — Molecular properties, binding affinities, clinical trials
7. **Neuroscience** — Brain imaging, connectomics, cognitive data
8. **Particle Physics** — Collider data, particle properties, decay channels
9. **Ecology** — Species populations, biodiversity indices, ecosystem dynamics
10. **Social Science** — Survey data, behavioral experiments, network analysis

### Tier 3 (Advanced — needs partnerships)
11. **Agriculture** — Crop yields, soil data, climate interactions
12. **Energy** — Grid data, renewable output, storage dynamics
13. **Manufacturing** — Process parameters, quality metrics, supply chains

## Cross-Domain Hypothesis Types

1. **Scaling laws transfer**: Does a scaling law in one domain predict something in another? (e.g., metabolic scaling → economic scaling)
2. **Network structure parallels**: Do biological networks share topology with economic/social networks?
3. **Universal distributions**: Are there distributions (power laws, log-normal) that appear in ALL domains?
4. **Causal structure transfer**: Does the causal graph in one system inform another?
5. **Anomaly correlation**: Does an anomaly in one domain predict an anomaly in another?
6. **Dimensional analysis across domains**: Can dimensionless ratios from physics explain patterns in biology or economics?

## Technical Approach

1. Use WebSearch to discover open datasets
2. Use WebFetch to download data
3. Write parsers for each data format
4. Store in `/shared/ASTRA/data/{domain}/`
5. Update knowledge base with cross-domain observations
6. Generate cross-domain hypotheses automatically
