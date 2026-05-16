#!/usr/bin/env python3
"""
DisPerSE Testing for HGBS Orion B
Implementing DisPerSE with modifications from Section 2.2 of Arzoumanian et al. 2019

This script:
1. Loads the column density map
2. Calculates background parameters following Arzoumanian+2019
3. Runs DisPerSE with specified parameters
4. Compares results with existing skeleton map
"""

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from scipy import ndimage
from pathlib import Path
import subprocess
import json
import sys

class DisPerSETester:
    """Test DisPerSE implementation against existing skeleton map."""

    def __init__(self, data_dir="/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB"):
        self.data_dir = Path(data_dir)
        self.column_density_file = self.data_dir / "HGBS_orionB_column_density_map.fits"
        self.skeleton_file = self.data_dir / "HGBS_orionB_skeleton_map.fits"

        # Check if files exist
        if not self.column_density_file.exists():
            raise FileNotFoundError(f"Column density file not found: {self.column_density_file}")
        if not self.skeleton_file.exists():
            raise FileNotFoundError(f"Skeleton file not found: {self.skeleton_file}")

        # Load data
        print("Loading data...")
        with fits.open(self.column_density_file) as hdul:
            self.column_density = hdul[0].data
            self.header = hdul[0].header

        with fits.open(self.skeleton_file) as hdul:
            self.existing_skeleton = hdul[0].data

        print(f"Column density shape: {self.column_density.shape}")
        print(f"Column density range: {np.nanmin(self.column_density):.2e} to {np.nanmax(self.column_density):.2e} H2/cm^2")
        print(f"Existing skeleton non-zero pixels: {np.count_nonzero(self.existing_skeleton):,}")

        # Get pixel scale and HPBW from header
        self.pix_scale = self.header.get('CDELT2', 3.0)  # arcsec/pixel default
        self.hpbw = self.header.get('HPBW', 18.0)  # arcsec (Herschel 250 micron)

        print(f"Pixel scale: {self.pix_scale} arcsec/pixel")
        print(f"HPBW: {self.hpbw} arcsec")

    def calculate_background_parameters(self):
        """
        Calculate background parameters following Arzoumanian+2019 Section 2.2.

        Method:
        - Create histogram of column density with bin size = 10^21 cm^-2
        - Use first bin for background estimation
        - NH2_bg,min = median of first bin
        - rms_min = std of first bin
        """
        print("\n" + "="*60)
        print("CALCULATING BACKGROUND PARAMETERS")
        print("="*60)

        # Create histogram with bin size = 10^21 cm^-2
        bin_size = 1e21  # cm^-2
        data_flat = self.column_density[np.isfinite(self.column_density)]

        min_val = np.floor(np.min(data_flat) / bin_size) * bin_size
        max_val = np.ceil(np.max(data_flat) / bin_size) * bin_size
        bins = np.arange(min_val, max_val + bin_size, bin_size)

        print(f"\nHistogram parameters:")
        print(f"  Bin size: {bin_size:.2e} cm^-2")
        print(f"  Number of bins: {len(bins)}")
        print(f"  Range: {min_val:.2e} to {max_val:.2e} cm^-2")

        # Calculate histogram
        hist, bin_edges = np.histogram(data_flat, bins=bins)

        # Get first bin statistics
        first_bin_mask = (data_flat >= bins[0]) & (data_flat < bins[1])
        first_bin_values = data_flat[first_bin_mask]

        NH2_bg_min = np.median(first_bin_values)
        rms_min = np.std(first_bin_values)

        print(f"\nFirst bin (first {bin_size:.2e} cm^-2):")
        print(f"  Number of pixels: {len(first_bin_values):,}")
        print(f"  Range: {np.min(first_bin_values):.2e} to {np.max(first_bin_values):.2e} cm^-2")
        print(f"  NH2_bg,min (median): {NH2_bg_min:.4e} cm^-2")
        print(f"  rms_min (std): {rms_min:.4e} cm^-2")

        # Calculate DisPerSE thresholds
        persistence_threshold = rms_min
        robustness_threshold = 1.5 * NH2_bg_min

        print(f"\nDisPerSE thresholds:")
        print(f"  PT (persistence) = rms_min = {persistence_threshold:.4e} cm^-2")
        print(f"  RT (robustness) = 1.5 × NH2_bg,min = {robustness_threshold:.4e} cm^-2")

        # Store parameters
        self.params = {
            'NH2_bg_min': float(NH2_bg_min),
            'rms_min': float(rms_min),
            'persistence_threshold': float(persistence_threshold),
            'robustness_threshold': float(robustness_threshold),
            'assembly_angle': 50.0,  # degrees
            'n_pix_smoothing': int(2 * self.hpbw / self.pix_scale),
            'min_feature_length': int(10 * self.hpbw / self.pix_scale)
        }

        print(f"\nAdditional DisPerSE parameters:")
        print(f"  AA (assembly angle) = {self.params['assembly_angle']}°")
        print(f"  N_pix (smoothing) = 2 × HPBW / pix = {self.params['n_pix_smoothing']} pixels")
        print(f"  Min feature length = 10 × HPBW = {self.params['min_feature_length']} pixels")

        return self.params

    def save_for_disperse(self, output_file="column_density_for_disperse.fits"):
        """
        Save column density map in format suitable for DisPerSE.
        DisPerSE expects FITS files with specific formatting.
        """
        output_path = self.data_dir / output_file

        # Create new HDU with cleaned data
        clean_data = np.nan_to_num(self.column_density, nan=0.0)

        hdu = fits.PrimaryHDU(data=clean_data.astype(np.float32), header=self.header)
        hdu.writeto(output_path, overwrite=True)

        print(f"\nSaved column density map for DisPerSE: {output_path}")
        return output_path

    def run_disperse(self, input_file):
        """
        Run DisPerSE with parameters from Arzoumanian+2019.

        Note: This requires DisPerSE to be installed and accessible in PATH.
        If DisPerSE is not available, we'll implement a simplified filament finder.
        """
        output_prefix = self.data_dir / "disperse_output"

        # DisPerSE command line parameters
        cmd = [
            "disperse",
            "-input", str(input_file),
            "-persistence", f"{self.params['persistence_threshold']:.6e}",
            "-robustness", f"{self.params['robustness_threshold']:.6e}",
            "-assembly", f"{self.params['assembly_angle']}",
            "-smooth", f"{self.params['n_pix_smoothing']}",
            "-output", str(output_prefix)
        ]

        print(f"\nDisPerSE command:")
        print(" ".join(cmd))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("\nDisPerSE output:")
            print(result.stdout)

            # Check if skeleton file was created
            skeleton_file = output_prefix.with_suffix('.fits')
            if skeleton_file.exists():
                print(f"\nSkeleton created: {skeleton_file}")
                return str(skeleton_file)
            else:
                print("\nWarning: Expected skeleton file not found")
                return None

        except FileNotFoundError:
            print("\nDisPerSE not found in PATH. Implementing simplified filament finder...")
            return self.run_simplified_filament_finder(input_file)
        except subprocess.CalledProcessError as e:
            print(f"\nDisPerSE error: {e}")
            print(f"stderr: {e.stderr}")
            return None

    def run_simplified_filament_finder(self, input_file):
        """
        Implement a simplified filament finder as fallback when DisPerSE is not available.

        This uses:
        1. Gaussian smoothing
        2. Thresholding
        3. Skeletonization via morphological thinning
        """
        print("\nRunning simplified filament finder...")

        from scipy import ndimage
        from skimage.morphology import skeletonize
        from skimage.filters import threshold_otsu

        # Clean data
        data = np.nan_to_num(self.column_density, nan=0.0)

        # Smooth
        smoothed = ndimage.gaussian_filter(data, sigma=self.params['n_pix_smoothing']/4)

        # Threshold based on persistence
        threshold = self.params['persistence_threshold']
        binary = smoothed > threshold

        # Skeletonize
        skeleton = skeletonize(binary.astype(np.uint8))

        # Remove small features (less than min_feature_length)
        labeled, num_features = ndimage.label(skeleton)
        sizes = ndimage.sum(skeleton, labeled, range(num_features + 1))

        mask = sizes >= self.params['min_feature_length']
        mask[0] = False  # Remove background
        filtered_skeleton = np.isin(labeled, np.where(mask)[0])

        # Save result
        output_file = self.data_dir / "simplified_skeleton.fits"
        hdu = fits.PrimaryHDU(data=filtered_skeleton.astype(np.float32))
        hdu.writeto(output_file, overwrite=True)

        print(f"Simplified skeleton saved: {output_file}")
        print(f"Non-zero pixels: {np.count_nonzero(filtered_skeleton):,}")

        return str(output_file)

    def compare_skeletons(self, new_skeleton_file):
        """
        Compare new skeleton with existing one.

        Metrics:
        1. Number of filaments (connected components)
        2. Total length (non-zero pixels)
        3. Spatial correlation
        4. Visual comparison
        """
        print("\n" + "="*60)
        print("COMPARING SKELETONS")
        print("="*60)

        # Load new skeleton
        with fits.open(new_skeleton_file) as hdul:
            new_skeleton = hdul[0].data

        # Convert to binary
        existing_binary = (self.existing_skeleton > 0).astype(int)
        new_binary = (new_skeleton > 0).astype(int)

        # Basic statistics
        existing_pixels = np.count_nonzero(existing_binary)
        new_pixels = np.count_nonzero(new_binary)

        print(f"\nPixel counts:")
        print(f"  Existing skeleton: {existing_pixels:,} pixels")
        print(f"  New skeleton: {new_pixels:,} pixels")
        print(f"  Difference: {new_pixels - existing_pixels:,} pixels ({100*(new_pixels/existing_pixels - 1):.1f}%)")

        # Connected components (filaments)
        from scipy import ndimage
        existing_labeled, existing_num = ndimage.label(existing_binary)
        new_labeled, new_num = ndimage.label(new_binary)

        print(f"\nNumber of filaments:")
        print(f"  Existing skeleton: {existing_num}")
        print(f"  New skeleton: {new_num}")

        # Overlap analysis
        overlap = np.sum(existing_binary & new_binary)
        union = np.sum(existing_binary | new_binary)
        dice = 2 * overlap / (existing_pixels + new_pixels) if (existing_pixels + new_pixels) > 0 else 0
        iou = overlap / union if union > 0 else 0

        print(f"\nOverlap metrics:")
        print(f"  Intersection: {overlap:,} pixels")
        print(f"  Union: {union:,} pixels")
        print(f"  Dice coefficient: {dice:.3f}")
        print(f"  IoU (Jaccard index): {iou:.3f}")

        # Save comparison statistics
        stats = {
            'existing_pixels': int(existing_pixels),
            'new_pixels': int(new_pixels),
            'pixel_difference': int(new_pixels - existing_pixels),
            'pixel_difference_percent': 100 * (new_pixels / existing_pixels - 1),
            'existing_filaments': int(existing_num),
            'new_filaments': int(new_num),
            'overlap_pixels': int(overlap),
            'dice_coefficient': float(dice),
            'iou': float(iou)
        }

        stats_file = self.data_dir / "disperse_comparison_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"\nStatistics saved to: {stats_file}")

        # Create comparison figure
        self.create_comparison_figure(new_skeleton, stats)

        return stats

    def create_comparison_figure(self, new_skeleton, stats):
        """Create comparison figure showing column density and both skeletons."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # Panel 1: Column density
        ax = axes[0]
        im1 = ax.imshow(np.log10(self.column_density), origin='lower', cmap='viridis')
        ax.set_title('Column Density (log scale)', fontsize=12, fontweight='bold')
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')
        plt.colorbar(im1, ax=ax, label='log₁₀(N$_{H2}$ [cm⁻²])')

        # Panel 2: Existing skeleton
        ax = axes[1]
        ax.imshow(self.column_density, origin='lower', cmap='gray', alpha=0.3)
        existing_mask = self.existing_skeleton > 0
        ax.imshow(np.ma.masked_where(~existing_mask, self.existing_skeleton),
                  origin='lower', cmap='hot', alpha=0.8)
        ax.set_title(f'Existing Skeleton\n({np.count_nonzero(existing_mask):,} pixels)',
                    fontsize=12, fontweight='bold')
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')

        # Panel 3: New skeleton
        ax = axes[2]
        ax.imshow(self.column_density, origin='lower', cmap='gray', alpha=0.3)
        new_mask = new_skeleton > 0
        ax.imshow(np.ma.masked_where(~new_mask, new_skeleton),
                  origin='lower', cmap='plasma', alpha=0.8)
        ax.set_title(f'New DisPerSE Skeleton\n({np.count_nonzero(new_mask):,} pixels)',
                    fontsize=12, fontweight='bold')
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')

        plt.suptitle('DisPerSE Implementation Test: Orion B', fontsize=14, fontweight='bold')
        plt.tight_layout()

        output_file = self.data_dir / "disperse_comparison.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\nComparison figure saved: {output_file}")
        plt.close()

        # Create overlap figure
        self.create_overlap_figure(new_skeleton)

    def create_overlap_figure(self, new_skeleton):
        """Create figure showing overlap between skeletons."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        existing_binary = (self.existing_skeleton > 0).astype(int)
        new_binary = (new_skeleton > 0).astype(int)

        # Panel 1: Existing only
        ax = axes[0]
        only_existing = existing_binary & ~new_binary
        ax.imshow(only_existing, origin='lower', cmap='Blues')
        ax.set_title('Existing Skeleton Only', fontsize=12, fontweight='bold')
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')

        # Panel 2: New only
        ax = axes[1]
        only_new = ~existing_binary & new_binary
        ax.imshow(only_new, origin='lower', cmap='Reds')
        ax.set_title('New DisPerSE Only', fontsize=12, fontweight='bold')
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')

        # Panel 3: Overlap
        ax = axes[2]
        overlap = existing_binary & new_binary
        # Show: blue=existing only, red=new only, purple=overlap
        rgb = np.zeros((*existing_binary.shape, 3))
        rgb[..., 0] = only_new.astype(float)  # Red channel
        rgb[..., 2] = only_existing.astype(float)  # Blue channel
        rgb[..., 0] += overlap.astype(float) * 0.5  # Add to both for purple
        rgb[..., 2] += overlap.astype(float) * 0.5
        rgb = np.clip(rgb, 0, 1)

        ax.imshow(rgb, origin='lower')
        ax.set_title('Overlap (purple)', fontsize=12, fontweight='bold')
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')

        plt.suptitle('Skeleton Comparison: Overlap Analysis', fontsize=14, fontweight='bold')
        plt.tight_layout()

        output_file = self.data_dir / "disperse_overlap.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Overlap figure saved: {output_file}")
        plt.close()

    def run_full_test(self):
        """Run the complete DisPerSE testing pipeline."""
        print("\n" + "="*70)
        print("DISPERSE TESTING PIPELINE: HGBS ORION B")
        print("="*70)

        # Step 1: Calculate background parameters
        params = self.calculate_background_parameters()

        # Step 2: Save data for DisPerSE
        input_file = self.save_for_disperse()

        # Step 3: Run DisPerSE (or simplified version)
        new_skeleton_file = self.run_disperse(input_file)

        if new_skeleton_file is None:
            print("\nError: Failed to create skeleton")
            return None

        # Step 4: Compare skeletons
        stats = self.compare_skeletons(new_skeleton_file)

        print("\n" + "="*70)
        print("DISPERSE TESTING COMPLETE")
        print("="*70)

        return stats


def main():
    """Main entry point."""
    tester = DisPerSETester()
    stats = tester.run_full_test()

    if stats:
        print("\nTest completed successfully!")
        print(f"Results saved in: {tester.data_dir}")


if __name__ == "__main__":
    main()
