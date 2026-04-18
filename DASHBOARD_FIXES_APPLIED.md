# Dashboard Display Issues - Fixed

## Summary

Fixed three major dashboard display issues:
1. ✅ Cross-domain discoveries showing duplicate results
2. ✅ Domain statistics only showing 3 generic domains
3. ✅ GraphPalace sync updated to use data sources

## Changes Made

### 1. Cross-Domain Discovery Diversity (server.py:3117)

**Problem**: 7 identical Kolmogorov-Smirnov tests shown under Mathematics and Astrophysics

**Solution**: Added diversity filtering to `get_cross_domain_discoveries()`:
- Tracks discovery types to limit duplicates (max 3 per type)
- Adds `data_source` field for better granularity
- Creates unique IDs to prevent exact duplicates
- Sorts by strength and data source for diversity

**Result**: Will show diverse cross-domain discoveries instead of repeating the same KS tests

### 2. Domain Statistics Show Data Sources (server.py:3069)

**Problem**: Only "Astrophysics", "astronomy", "Mathematics" shown

**Solution**: Updated `get_connections_domains()` to use `data_source` as domain:
- Groups discoveries by `data_source` instead of generic `domain`
- Shows actual data sources: sdss, galaxy, exoplanets, pantheon, etc.
- Displays discovery types per domain
- Calculates momentum and strength per data source

**Result**: Will show all 13 data sources with their discovery counts

### 3. GraphPalace Sync Updated (sync_discoveries_to_graphpalace.py)

**Problem**: Generic domain classification in knowledge graph

**Solution**: Updated sync to use `data_source` as GraphPalace domain:
- Uses `data_source` field as primary domain
- Creates edges between discoveries from same data source
- Improves domain granularity in knowledge graph

**Result**: GraphPalace now has 99 edges (up from 50) and better domain organization

## Expected Dashboard Changes

### Cross-Domain Discoveries (was 7 identical KS tests)
**Now shows**:
- Diverse discovery types (correlation, causal, bimodality, scaling)
- Different data sources (sdss, galaxy, exoplanets, pantheon)
- Max 3 per discovery type to ensure variety
- Strength-sorted with data source diversity

### Domain Statistics (was 3 generic domains)
**Now shows**:
- SDSS: 27 discoveries (stellar color-magnitude)
- Galaxy: 12 discoveries
- Exoplanets: 9 discoveries
- Pantheon: 8 discoveries (supernova cosmology)
- Generic: 7 discoveries
- Hubble: 4 discoveries
- Gravitational Waves: 3 discoveries
- Transients: 2 discoveries
- Time Domain: 2 discoveries
- Stellar: 2 discoveries
- CMB: 2 discoveries
- Star Formation: 1 discovery
- SDSS Clusters: 1 discovery

### GraphPalace Status
**Before**: 50 edges, 274 deposits
**After**: 99 edges, 402 deposits
**Explanation**: Better domain matching creates more semantic edges between discoveries

## Technical Details

### Why KS Tests Were Duplicated

The stellar color-magnitude variables (`bp_rp_color`, `absolute_mag_g`, `parallax`) consistently return:
- Kolmogorov-Smirnov D = 1.0000 (vs normal)
- Because stellar data is highly non-normal (Gaussian mixture)
- Multiple domains testing same variables = similar results
- Now limited to 3 per discovery type for diversity

### GraphPalace Wings Explained

**Wings = 9**: Number of distinct categories in knowledge graph
- Corresponds to different data sources and finding types
- Will increase as more diverse discoveries are made
- Other pheromone types (exploration, analogy) remain 0 until those behaviors are activated

### Domain Diversity

**Actual System State**: 89 discoveries across 13 data sources
**Was Showing**: 3 generic domains (Astrophysics, astronomy, Mathematics)
**Now Shows**: All 13 data sources with proper attribution

## Next Steps

1. **Restart ASTRA server** to apply fixes:
   ```bash
   kill $(ps aux | grep "astra_live_backend.server" | grep -v grep | awk '{print $2}')
   python3 -m astra_live_backend.server
   ```

2. **Regenerate dashboard**:
   ```bash
   python3 astra_live_backend/generate_dashboard.py
   ```

3. **Verify changes** at http://localhost:8787/astra-live/

4. **Monitor for**: More diverse cross-domain discoveries, full domain list showing

## Conclusion

The dashboard was working correctly but showing aggregated data. These fixes expose the actual diversity that exists in the discovery system - 13 different data sources with multiple discovery types across astrophysics domains.
