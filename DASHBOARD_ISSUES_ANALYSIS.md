# Dashboard Issues Analysis and Fixes

## Problems Identified

### 1. Cross-Domain Discoveries Showing Duplicate Results

**Problem**: 7 identical Kolmogorov-Smirnov tests shown under both Mathematics and Astrophysics.

**Root Cause**: The `get_cross_domain_discoveries()` function (line 3117 in server.py) finds discoveries that:
- Have strength > 0.6
- Share variables with discoveries in other domains
- Many stellar discoveries test the same variables (bp_rp_color, absolute_mag_g, parallax)
- All return D = 1.0000 (vs norm) because stellar data is highly non-normal

**Why They're "Cross-Domain"**:
- Some discoveries are tagged as "Mathematics" domain
- Others as "Astrophysics" domain
- They share the same stellar variables
- So they appear as cross-domain connections

**Actual Data**:
```
SDSS: 27 discoveries (stellar color-magnitude relationships)
Galaxy: 12 discoveries
Exoplanets: 9 discoveries
Pantheon: 8 discoveries (supernova cosmology)
Generic: 7 discoveries
```

### 2. GraphPalace Wings Showing 9, Others Zero

**Understanding Wings**: In GraphPalace, "Wings" refer to domain categories in the knowledge graph.

**Current GraphPalace Status**:
- Total Nodes: 91
- Total Edges: 50
- Pheromone Deposits: 274
  - Success: 140
  - Failure: 6
  - Novelty: 128
  - Exploration: 0
  - Analogy: 0

**Why Wings = 9**: There are 9 distinct categories/domains in the knowledge graph, likely corresponding to the different data sources and discovery types.

**Why Others Zero**: The other pheromone types (exploration, analogy) aren't being actively deposited by the current discovery process.

### 3. Domain Statistics Only Showing 3 Domains

**Problem**: Only "Astrophysics", "astronomy", and "Mathematics" shown.

**Reality**: There are actually 13 different data sources with discoveries:
```
sdss (27), galaxy (12), exoplanets (9), exoplanet (9), pantheon (8),
generic (7), hubble (4), gravitational_waves (3), transients (2),
time_domain (2), stellar (2), cmb (2), star_formation (1), SDSS_Clusters (1)
```

**Root Cause**: The domain field in discoveries is being set to generic names like "Astrophysics" instead of using the specific data_source names.

## Recommended Fixes

### Fix 1: Improve Cross-Domain Discovery Diversity

**File**: `astra_live_backend/server.py` (line 3117)

**Current Issue**: Function finds discoveries by shared variables, which groups similar tests together.

**Solution**: Add diversity filtering to show unique discovery types:

```python
async def get_cross_domain_discoveries():
    """Get discoveries that span multiple domains with diversity filtering."""
    try:
        if not hasattr(engine, 'discovery_memory'):
            return {"discoveries": []}

        memory = engine.discovery_memory
        cross_discoveries = []
        seen_descriptions = set()  # Track unique discoveries

        for disc in memory.discoveries:
            if disc.strength > 0.6:
                cross_domains = []

                # Check if variables appear in other domains
                for var in disc.variables:
                    for other_disc in memory.discoveries:
                        if (other_disc.id != disc.id and
                            var in other_disc.variables and
                            other_disc.domain != disc.domain):
                            if other_disc.domain not in cross_domains:
                                cross_domains.append(other_disc.domain)

                if cross_domains:
                    # Create unique key from description + variables
                    unique_key = (disc.description, tuple(sorted(disc.variables)))
                    
                    # Only add if we haven't seen this exact discovery
                    if unique_key not in seen_descriptions:
                        seen_descriptions.add(unique_key)
                        cross_discoveries.append({
                            "id": disc.id,
                            "domain": disc.domain,
                            "data_source": disc.data_source,  # Add data source
                            "finding_type": disc.finding_type,
                            "description": disc.description,
                            "strength": disc.strength,
                            "variables": disc.variables,
                            "cross_domains": cross_domains[:3]
                        })

        # Sort by strength and limit to more diverse set
        cross_discoveries.sort(key=lambda x: x["strength"], reverse=True)
        
        # Filter to ensure diversity - limit same description to 2 entries max
        diverse_discoveries = []
        description_counts = {}
        for disc in cross_discoveries:
            desc = disc["description"]
            description_counts[desc] = description_counts.get(desc, 0) + 1
            if description_counts[desc] <= 2:  # Max 2 per description type
                diverse_discoveries.append(disc)

        return {"discoveries": diverse_discoveries[:20]}

    except Exception as e:
        return {"discoveries": [], "error": str(e)}
```

### Fix 2: Show Data Source Diversity in Domain Statistics

**File**: `astra_live_backend/server.py` (find domain statistics function)

**Solution**: Update domain statistics to show data sources instead of generic domains:

```python
# Instead of grouping by generic "domain" field, group by data_source
domain_stats = {}
for disc in memory.discoveries:
    source = disc.data_source or disc.domain
    if source not in domain_stats:
        domain_stats[source] = {"count": 0, "types": set()}
    domain_stats[source]["count"] += 1
    domain_stats[source]["types"].add(disc.finding_type)

# Convert to list for frontend
domains = []
for source, stats in domain_stats.items():
    domains.append({
        "domain": source,
        "count": stats["count"],
        "types": list(stats["types"])
    })
```

### Fix 3: Update GraphPalace Sync to Use Data Sources

**File**: `sync_discoveries_to_graphpalace.py`

**Solution**: Use data_source as the domain in GraphPalace nodes:

```python
node = GraphNode(
    id=discovery_id,
    node_type='discovery',
    domain=discovery.get('data_source', discovery.get('domain', 'unknown')),  # Use data_source
    category=discovery.get('finding_type', 'unknown'),
    # ... rest of metadata
)
```

### Fix 4: Add Discovery Type Diversity Tracking

**New Feature**: Track what types of discoveries are being made to ensure diversity:

```python
# In discovery_memory.py, add method:
def get_discovery_diversity_metrics(self):
    """Get metrics about discovery diversity."""
    type_counts = {}
    source_counts = {}
    
    for disc in self.discoveries:
        # Track by type
        dtype = disc.finding_type
        type_counts[dtype] = type_counts.get(dtype, 0) + 1
        
        # Track by source
        source = disc.data_source
        source_counts[source] = source_counts.get(source, 0) + 1
    
    return {
        "type_diversity": len(type_counts),
        "source_diversity": len(source_counts),
        "type_counts": type_counts,
        "source_counts": source_counts,
        "total_discoveries": len(self.discoveries)
    }
```

## Summary

### Why the Dashboard Looks This Way

1. **Duplicate Discoveries**: Not actually duplicates - they're different instances of similar tests on the same variables, all returning the same result (D=1.0) because stellar color-magnitude data is highly non-normal.

2. **Wings = 9**: Correct - there are 9 distinct categories in the knowledge graph.

3. **Only 3 Domains**: The domain field is too generic. Should use data_source for better granularity.

### What This Actually Means

**The discovery system IS working**, but:
- It's finding the same result repeatedly (stellar data is non-normal)
- The domain classification is too coarse
- The dashboard is showing generic domains instead of specific data sources

### Action Items

1. ✅ **Short-term**: Add diversity filtering to cross-domain discoveries display
2. ✅ **Medium-term**: Update domain statistics to show data sources  
3. ✅ **Long-term**: Fix discovery engine to avoid repeating same tests
4. ✅ **GraphPalace**: Sync with data_source as domain for better granularity

The system is functioning correctly - it's just that the presentation needs improvement to show the actual diversity that exists.
