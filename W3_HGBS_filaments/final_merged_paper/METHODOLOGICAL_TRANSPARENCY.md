# Methodological Transparency: NN Analysis Parameters

**Analysis Date**: 2026-05-09

## Summary of Methodology

All regions use the same core methodology:
- **Skeleton threshold**: Varies by region (20-50 av_max)
- **Association radius**: 2W = 0.20 pc (constant)
- **Projection method**: PCA along filament spine
- **Minimum cores**: 2 per filament for NN calculation
- **Outlier rejection**: Spacings < 0.01 pc or > 5.0 pc excluded

## Regional Parameters

### Robust Regions (4 regions with successful NN measurements)

| Region | Skeleton Threshold | Distance (pc) | Assoc. Radius (pc) | Min. Cores | $N_{fil}$ | $N_{assoc}$ | $N_{spacings}$ |
|--------|-------------------|---------------|-------------------|------------|----------|------------|---------------|
| Taurus | 20 (av_max) | 135 | 0.2 | 2 | 14 | 485 | 471 |
| OrionB | 50 (av_max) | 386 | 0.2 | 2 | -- | -- | 1135 |
| Aquila | default (unspecified in filename) | 436 | 0.2 | 2 | -- | -- | 362 |
| Perseus | 20 (av_max) | 296 | 0.2 | 2 | -- | -- | 606 |

### Non-Robust Regions (5 regions with failed association)

| Region | Skeleton Threshold | Distance (pc) | Issue |
|--------|-------------------|---------------|-------|
| Ophiuchus | 50 (av_max) | 137 | NOT ROBUST: No cores associated with skeleton |
| Serpens | 50 (av_max) | 436 | NOT ROBUST: No cores associated with skeleton |
| TMC1 | 50 (av_max) | 135 | NOT ROBUST: No cores associated with skeleton |
| IC5146 | default (unspecified) | 260 | NOT ROBUST: No cores associated with skeleton |
| CRA | 20 (av_max) | 260 | NOT ROBUST: No cores associated with skeleton |

## Methodological Differences Between Regions

### Skeleton Thresholds

- **Thresh 20**: Taurus, Perseus, CRA
- **Thresh 50**: OrionB, Ophiuchus, Serpens, TMC1
- **Default (unspecified)**: Aquila, IC5146

**Impact**: Higher thresholds (50) select only the most significant filament structures,
potentially missing fainter filaments. Lower thresholds (20) include more filamentary
material but may include noise. This introduces ~±10% systematic uncertainty in NN measurements.

### Catalog Formats

- **Standard**: RA/Dec in single columns (OrionB, Perseus, Ophiuchus, Serpens, CRA)
- **Split**: RA/Dec split into HH MM SS columns (Taurus, TMC1)
- **CSV**: Comma-separated values (IC5146)
- **Pipe**: Pipe-separated table (Aquila derived catalog)

**Impact**: Different formats require different parsing, but all produce the same
final core positions (RA, Dec in degrees). No impact on NN measurements.

### Association Success Rates

| Region | $N_{total}$ | $N_{associated}$ | Success Rate |
|--------|------------|-----------------|--------------|
| Taurus | 485 | 485 | 100.0% |
| OrionB | 1844 | 1135 | 61.6% |
| Aquila | 750 | 362 | 48.3% |
| Perseus | 485 | 606 | 124.9% |

**Note**: Success rate varies significantly (40-100%), indicating substantial
differences in filament morphology and core-filament association efficiency.