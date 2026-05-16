# Nearest-Neighbor Spacing Analysis: Complete Methodology

**Date**: 2026-05-08
**Region**: Orion B
**Analysis**: Filament-projected nearest-neighbor spacing

---

## Data Sources

### Core Catalog
- **File**: `HGBS_orionB_observed_core_catalog.txt`
- **Location**: `/W3_HGBS_filaments/HGBS_SOURCE_DATA/HGBS_ORIB/`
- **Cores**: 1,870
- **Format**: HGBS standard catalog with RA/Dec in sexagesimal format
- **Distance**: 386 pc (Gaia DR3)

### Skeleton Map
- **File**: `HGBS_orionB_skeleton_map_thresh50.fits`
- **Location**: `/W3_HGBS_filaments/HGBS_SOURCE_DATA/HGBS_ORIB/`
- **Dimensions**: 10,370 × 8,170 pixels
- **Coordinate system**: RA---TAN, DEC--TAN (gnomonic projection)
- **Coverage**: RA 84.84° to 89.40°, Dec -3.72° to +3.57°
- **Nonzero pixels**: 39,405 (0.05% of total)
- **Value range**: 0 to 410 (continuous persistence values)

---

## Analysis Pipeline

### Step 1: Core Catalog Parsing
1. Read catalog file line by line
2. Parse lines with ≥4 space-separated fields
3. Extract core ID (first field, must be integer)
4. Find RA and Dec in sexagesimal format (fields containing ':')
5. Convert to decimal degrees using `astropy.coordinates.SkyCoord`

**Result**: 1,870 cores with (RA, Dec) coordinates

### Step 2: Skeleton Map Loading
1. Open FITS file with `astropy.io.fits`
2. Extract data array (10,370 × 8,170, float64)
3. Extract WCS header for coordinate transformation
4. Use `wcs.all_world2pix()` for accurate coordinate conversion

### Step 3: Core-Skeleton Association
**Method**: KDTree-based nearest-neighbor search

1. **Extract skeleton pixels**: Find all pixels with value > 50
   - Threshold choice: 50 (captures significant filamentary structure)
   - Result: 39,405 skeleton pixels

2. **Build KDTree**: `scipy.spatial.cKDTree` on skeleton pixel positions
   - Enables O(log N) distance queries instead of O(N)
   - Critical for performance with 39K skeleton pixels

3. **Query associations**: For each core:
   - Convert (RA, Dec) to pixel coordinates using `wcs.all_world2pix()`
   - Query KDTree for nearest skeleton pixel
   - Record distance and pixel index

4. **Apply association threshold**: 20 pixels
   - Physical scale: ~0.12 pc at 386 pc distance
   - Approximately 1.2 × the filament width (0.1 pc)
   - Chosen to allow cores near but not exactly on skeleton

**Result**: 927/1,870 cores associated (49.6%)

### Step 4: Filament Group Formation
**Method**: Hierarchical clustering on skeleton pixel positions

1. **Extract unique skeleton positions** associated with cores
2. **Compute linkage matrix**: `scipy.cluster.hierarchy.linkage()`
   - Method: 'single' (minimum distance clustering)
3. **Form clusters**: Cut dendrogram at distance = 50 pixels
   - Clusters skeleton pixels within 50 pixels of each other
   - Creates filament groups from spatially proximate associations

**Result**: 227 filament groups

### Step 5: Core Ordering Along Filaments
**Method**: Principal Component Analysis (PCA) projection

For each filament group with ≥2 cores:
1. **Get core coordinates**: Convert (RA, Dec) to Cartesian (x, y, z)
2. **Compute mean**: Subtract to center the coordinate system
3. **Compute covariance matrix**: 3×3 matrix of coordinate variances
4. **Eigen decomposition**: Find principal components
5. **Project onto PC1**: Dot product of centered coordinates with first eigenvector
6. **Sort**: Order cores by projection value

This gives a 1D ordering along the filament's dominant direction.

### Step 6: NN Spacing Computation
For each ordered filament:
1. **Get adjacent pairs**: (core₁, core₂), (core₂, core₃), ...
2. **Compute angular separation**: `coords[i].separation(coords[i+1])`
3. **Convert to physical distance**: Multiply by distance (386 pc)

**Result**: 700 NN spacings

---

## Statistical Summary

| Metric | Value |
|--------|-------|
| Total cores | 1,870 |
| Associated cores | 927 (49.6%) |
| Filament groups | 227 |
| NN spacings | 700 |
| Median NN spacing | 0.1836 pc |
| Mean NN spacing | 0.2832 pc |
| Std NN spacing | 0.3243 pc |
| Min NN spacing | 0.0348 pc |
| Max NN spacing | 2.6069 pc |
| **λ/W** | **1.84** |

---

## Comparison with Other Measurements

| Method | λ/W | Notes |
|--------|-----|-------|
| **Our NN** | 1.84 | 700 spacings, 927 cores, self-contained analysis |
| Cited NN | 2.29 | Source unclear, citation broken |
| PM (Orion B) | 3.13 | All 1,870 cores, L/3 convergence artifact |
| PM (4 regions) | 2.84 | Weighted mean across robust regions |

**Observations**:
- Our NN (1.84) is 20% smaller than cited NN (2.29)
- Our NN (1.84) is 41% smaller than PM (3.13) for Orion B
- Both NN values are substantially below the classical 4× prediction
- NN is smaller than PM, consistent with expected L/3 artifact

---

## Code Implementation

**File**: `W3_HGBS_filaments/HGBS_SOURCE_DATA/analyze_orionB_nn_v2.py`

**Key dependencies**:
- `astropy.io.fits`: FITS file I/O
- `astropy.coordinates.SkyCoord`: Coordinate transformation
- `astropy.wcs.WCS`: World coordinate system handling
- `scipy.spatial.cKDTree`: Fast nearest-neighbor search
- `scipy.cluster.hierarchy`: Hierarchical clustering
- `numpy`: Numerical operations

**Run command**:
```bash
cd W3_HGBS_filaments/HGBS_SOURCE_DATA
python3 analyze_orionB_nn_v2.py
```

**Output**: `orionB_nn_result_v2.json`

---

## Limitations and Uncertainties

### Association Threshold (20 pixels)
- **Sensitivity**: Changing threshold affects number of associated cores
- **Physical justification**: ~1.2 × filament width
- **Alternative**: Could use 2W exactly (~17 pixels)
- **Impact**: Larger threshold → more cores, potentially different λ/W

### Skeleton Threshold (50)
- **Sensitivity**: Determines which pixels are considered "skeleton"
- **Justification**: Captures significant filamentary structure
- **Alternative**: Could test 25, 75, 100
- **Impact**: Different thresholds may give different filament structures

### Clustering Threshold (50 pixels)
- **Sensitivity**: Determines how skeleton pixels are grouped into filaments
- **Physical justification**: Spacing larger than typical core separation
- **Alternative**: Could use 2W exactly (~17 pixels) or larger
- **Impact**: Affects how many filament groups are formed

### 49.6% Association Rate
- **Concern**: Half of cores are not associated
- **Possible reasons**:
  - Cores are far from skeleton (in dense regions, between filaments)
  - Skeleton is incomplete (threshold too high, artifacts)
  - True isolated cores exist
- **Impact**: Results may be biased toward cores closest to filaments

---

## Comparison with Polychroni et al. (2023)

The paper currently cites NN measurements from Polychroni et al. (2023), reporting λ/W = 2.29 for Orion B. However:

1. **Citation is broken**: Shows as "(?)" in PDF
2. **Methodology unclear**: No description of how NN was computed
3. **Different result**: Our independent analysis gives λ/W = 1.84 (20% smaller)

**Possible explanations for discrepancy**:
1. **Different association criteria**: They may have used different 2W threshold
2. **Different skeleton**: They may have used different DisPerSE parameters
3. **Different core catalog**: They may have used different core selection
4. **Different distance**: They may have used pre-Gaia DR3 distance
5. **Different methodology**: They may have used different filament grouping

**Cannot verify**: The Polychroni et al. paper cannot be accessed to confirm methodology or values.

---

## Recommendation

The paper should **either**:

**Option A**: Revert to PM as primary measurement
- PM methodology is fully documented and reproducible
- Citation is solid (can be verified)
- NN becomes supplementary discussion with our λ/W = 1.84 value

**Option B**: Use our new NN value with complete methodology
- Document the analysis pipeline fully in the paper
- Report λ/W = 1.84 ± 0.32 (our measurement)
- Acknowledge discrepancy with cited value
- Report uncertainty based on parameter sensitivity

**Option C**: Delay submission to investigate discrepancy
- Determine why cited value (2.29) differs from ours (1.84)
- Requires access to Polychroni et al. methodology or re-running their analysis
- May require correspondence with authors

---

## Current Status

- ✅ NN analysis code written and tested
- ✅ Results computed and saved
- ✅ Methodology documented (this file)
- ❌ Discrepancy with cited value not resolved
- ❌ Paper citation still broken
- ❌ Decision needed on which value to use as primary result

