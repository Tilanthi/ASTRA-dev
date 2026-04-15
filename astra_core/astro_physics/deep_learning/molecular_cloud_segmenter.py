#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Molecular Cloud Instance Segmentation using Deep Learning

Identifies and segments individual molecular clouds, clumps, and cores.
Provides physical property estimation for each segmented object.

Applications:
- Cloud identification in CO surveys (e.g., GMC cataloging)
- Clump finding in high-resolution maps
- Core identification in prestellar core surveys
- Cloud boundary delineation
- Mass and size estimation
- Star formation efficiency calculation

Author: STAN Evolution Team
Date: 2025-03-18
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class CloudProperties:
    """Physical properties of a segmented molecular cloud"""
    id: int
    mask: np.ndarray
    centroid: Tuple[float, float, float]  # (x, y, velocity) or (ra, dec, velocity)
    pixel_area: float
    physical_area: float  # pc^2 if distance provided
    mass: float  # Solar masses
    radius: float  # pc
    peak_column_density: float  # cm^-2
    mean_column_density: float  # cm^-2
    velocity_dispersion: float  # km/s
    virial_parameter: float
    star_formation_efficiency: float  # optional
    freefall_time: float  # Myr
    jeans_length: float  # pc
    bound_status: str  # 'bound', 'unbound', 'pressure-confined'
    morphology_type: str  # 'spherical', 'filamentary', 'cometary', 'irregular'


class MaskRCNNBackbone(nn.Module):
    """
    Backbone network for cloud instance segmentation.

    Uses Feature Pyramid Network (FPN) for multi-scale feature extraction.
    """

    def __init__(self, in_channels: int = 1, base_features: int = 64):
        super().__init__()

        # Bottom-up pathway
        self.conv1 = nn.Conv2d(in_channels, base_features, kernel_size=7,
                               stride=2, padding=3)
        self.bn1 = nn.BatchNorm2d(base_features)
        self.relu = nn.ReLU(inplace=True)

        # ResNet-style blocks
        self.layer1 = self._make_layer(base_features, base_features, 2)
        self.layer2 = self._make_layer(base_features, base_features * 2, 2,
                                        stride=2)
        self.layer3 = self._make_layer(base_features * 2, base_features * 4, 2,
                                        stride=2)
        self.layer4 = self._make_layer(base_features * 4, base_features * 8, 2,
                                        stride=2)

        # Top-down pathway (FPN)
        self.lat5 = nn.Conv2d(base_features * 8, 256, kernel_size=1)
        self.lat4 = nn.Conv2d(base_features * 4, 256, kernel_size=1)
        self.lat3 = nn.Conv2d(base_features * 2, 256, kernel_size=1)
        self.lat2 = nn.Conv2d(base_features, 256, kernel_size=1)

        # Smooth layers
        self.smooth5 = nn.Conv2d(256, 256, kernel_size=3, padding=1)
        self.smooth4 = nn.Conv2d(256, 256, kernel_size=3, padding=1)
        self.smooth3 = nn.Conv2d(256, 256, kernel_size=3, padding=1)

    def _make_layer(self, in_ch: int, out_ch: int, blocks: int,
                    stride: int = 1) -> nn.Module:
        layers = []

        layers.append(nn.Conv2d(in_ch, out_ch, kernel_size=3,
                                stride=stride, padding=1))
        layers.append(nn.BatchNorm2d(out_ch))
        layers.append(nn.ReLU(inplace=True))

        for _ in range(1, blocks):
            layers.append(nn.Conv2d(out_ch, out_ch, kernel_size=3,
                                    padding=1))
            layers.append(nn.BatchNorm2d(out_ch))
            layers.append(nn.ReLU(inplace=True))

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: Input image [B, C, H, W]

        Returns:
            Dictionary with feature maps at different scales
        """
        # Bottom-up
        c1 = self.relu(self.bn1(self.conv1(x)))
        c1 = F.max_pool2d(c1, kernel_size=3, stride=2, padding=1)

        c2 = self.layer1(c1)
        c3 = self.layer2(c2)
        c4 = self.layer3(c3)
        c5 = self.layer4(c4)

        # Top-down with lateral connections
        p5 = self.lat5(c5)
        p4 = self.lat4(c4) + F.interpolate(p5, scale_factor=2, mode='nearest')
        p3 = self.lat3(c3) + F.interpolate(p4, scale_factor=2, mode='nearest')
        p2 = self.lat2(c2) + F.interpolate(p3, scale_factor=2, mode='nearest')

        # Smooth
        p5 = self.smooth5(p5)
        p4 = self.smooth4(p4)
        p3 = self.smooth3(p3)

        return {
            'p2': p2,
            'p3': p3,
            'p4': p4,
            'p5': p5
        }


class RegionProposalNetwork(nn.Module):
    """
    Region Proposal Network (RPN) for cloud candidate regions.

    Proposes bounding boxes that may contain molecular clouds.
    """

    def __init__(self, in_channels: int = 256, num_anchors: int = 9):
        super().__init__()

        # Shared convolution
        self.conv = nn.Conv2d(in_channels, 256, kernel_size=3, padding=1)

        # Box regression
        self.box_pred = nn.Conv2d(256, num_anchors * 4, kernel_size=1)

        # Objectness (cloud vs background)
        self.objectness = nn.Conv2d(256, num_anchors, kernel_size=1)

    def forward(self, features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            features: Feature map [B, C, H, W]

        Returns:
            Tuple of (box_predictions, objectness_scores)
        """
        x = F.relu(self.conv(features))

        box_pred = self.box_pred(x)
        objectness = self.objectness(x)

        return box_pred, objectness


class CloudMaskHead(nn.Module):
    """
    Mask head for predicting instance segmentation masks.

    Produces a binary mask for each proposed cloud region.
    """

    def __init__(self, in_channels: int = 256):
        super().__init__()

        self.conv1 = nn.Conv2d(in_channels, 256, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(256)
        self.conv2 = nn.Conv2d(256, 256, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(256)
        self.conv3 = nn.Conv2d(256, 256, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(256)
        self.conv4 = nn.Conv2d(256, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)

        self.deconv = nn.ConvTranspose2d(256, 256, kernel_size=2, stride=2)
        self.mask_pred = nn.Conv2d(256, 1, kernel_size=1)

        self.relu = nn.ReLU(inplace=True)

    def forward(self, features: torch.Tensor, rois: torch.Tensor) -> torch.Tensor:
        """
        Args:
            features: Feature map [B, C, H, W]
            rois: Region of interest proposals [N, 5] (batch_idx, x1, y1, x2, y2)

        Returns:
            Mask predictions [N, 1, H_mask, W_mask]
        """
        x = self.relu(self.bn1(self.conv1(features)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.relu(self.bn4(self.conv4(x)))

        x = self.deconv(x)
        masks = torch.sigmoid(self.mask_pred(x))

        return masks


class CloudPropertyHead(nn.Module):
    """
    Predicts physical properties of detected clouds.

    Outputs:
    - Mass estimate
    - Radius estimate
    - Velocity dispersion
    - Virial parameter
    - Morphology class
    """

    def __init__(self, in_channels: int = 256):
        super().__init__()

        # Global average pooling
        self.gap = nn.AdaptiveAvgPool2d(1)

        # Regression heads for physical properties
        self.mass_head = nn.Sequential(
            nn.Linear(in_channels, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Softplus()  # Mass > 0
        )

        self.radius_head = nn.Sequential(
            nn.Linear(in_channels, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Softplus()  # Radius > 0
        )

        self.velocity_dispersion_head = nn.Sequential(
            nn.Linear(in_channels, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Softplus()  # Velocity dispersion > 0
        )

        self.virial_param_head = nn.Sequential(
            nn.Linear(in_channels, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Softplus()  # Virial parameter > 0
        )

        # Morphology classification
        self.morphology_head = nn.Sequential(
            nn.Linear(in_channels, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 4)  # 4 morphology types
        )

    def forward(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            features: Feature map [B, C, H, W]

        Returns:
            Dictionary with property predictions
        """
        x = self.gap(features).squeeze(-1).squeeze(-1)  # [B, C]

        mass = self.mass_head(x)
        radius = self.radius_head(x)
        velocity_dispersion = self.velocity_dispersion_head(x)
        virial_param = self.virial_param_head(x)
        morphology_logits = self.morphology_head(x)

        return {
            'mass': mass,
            'radius': radius,
            'velocity_dispersion': velocity_dispersion,
            'virial_parameter': virial_param,
            'morphology_logits': morphology_logits
        }


class MolecularCloudSegmenter(nn.Module):
    """
    Complete molecular cloud instance segmentation system.

    Combines region proposal, mask prediction, and property estimation
    to identify and characterize molecular clouds.

    Example:
        >>> segmenter = MolecularCloudSegmenter()
        >>> image = torch.randn(1, 1, 512, 512)  # CO integrated intensity
        >>> clouds = segmenter.detect_clouds(image)
        >>> for cloud in clouds:
        ...     print(f"Cloud mass: {cloud.mass:.2f} Msun")
    """

    def __init__(self, in_channels: int = 1, base_features: int = 64):
        super().__init__()

        self.backbone = MaskRCNNBackbone(in_channels, base_features)

        # RPN at multiple scales
        self.rpn_p2 = RegionProposalNetwork(256)
        self.rpn_p3 = RegionProposalNetwork(256)
        self.rpn_p4 = RegionProposalNetwork(256)
        self.rpn_p5 = RegionProposalNetwork(256)

        # Mask head
        self.mask_head = CloudMaskHead(256)

        # Property head
        self.property_head = CloudPropertyHead(256)

        # Anchor boxes (different scales and aspect ratios)
        self.anchor_scales = [32, 64, 128, 256]
        self.anchor_ratios = [0.5, 1.0, 2.0]

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: Input image [B, C, H, W]

        Returns:
            Dictionary with all predictions
        """
        # Extract features
        features = self.backbone(x)

        # Region proposals at each scale
        proposals = []
        objectness_scores = []

        for scale, rpn in [('p2', self.rpn_p2), ('p3', self.rpn_p3),
                           ('p4', self.rpn_p4), ('p5', self.rpn_p5)]:
            feat = features[scale]
            boxes, obj = rpn(feat)
            proposals.append(boxes)
            objectness_scores.append(obj)

        # For simplicity, use p3 features for mask and property prediction
        mask_pred = self.mask_head(features['p3'], proposals[1])
        properties = self.property_head(features['p3'])

        return {
            'proposals': proposals,
            'objectness': objectness_scores,
            'masks': mask_pred,
            'properties': properties,
            'features': features
        }

    def detect_clouds(
        self,
        image: torch.Tensor,
        confidence_threshold: float = 0.7,
        nms_threshold: float = 0.3
    ) -> List[CloudProperties]:
        """
        Detect and segment clouds in an image.

        Args:
            image: Input image [B, C, H, W] or [C, H, W]
            confidence_threshold: Minimum confidence for detection
            nms_threshold: IoU threshold for non-maximum suppression

        Returns:
            List of CloudProperties
        """
        self.eval()

        if image.dim() == 3:
            image = image.unsqueeze(0)

        with torch.no_grad():
            predictions = self.forward(image)

        # Extract clouds from predictions
        clouds = self._extract_clouds(predictions, image, confidence_threshold)

        # Apply NMS
        clouds = self._apply_nms(clouds, nms_threshold)

        return clouds

    def _extract_clouds(
        self,
        predictions: Dict[str, torch.Tensor],
        image: torch.Tensor,
        threshold: float
    ) -> List[CloudProperties]:
        """Extract cloud objects from network predictions."""
        clouds = []

        # This is simplified - real implementation would process proposals
        # and extract individual cloud instances

        # Get masks
        masks = predictions['masks'][0, 0].cpu().numpy()
        properties = predictions['properties']

        # Get image data for physical calculations
        img_data = image[0, 0].cpu().numpy()

        # Find connected components in mask
        from scipy.ndimage import label

        mask_binary = masks > threshold
        labeled, num_clouds = label(mask_binary)

        for i in range(1, num_clouds + 1):
            mask = labeled == i

            if np.sum(mask) < 10:  # Skip small detections
                continue

            # Extract properties
            props = self._compute_cloud_properties(
                i, mask, img_data, properties
            )

            if props is not None:
                clouds.append(props)

        return clouds

    def _compute_cloud_properties(
        self,
        cloud_id: int,
        mask: np.ndarray,
        image_data: np.ndarray,
        network_props: Dict[str, torch.Tensor]
    ) -> Optional[CloudProperties]:
        """Compute physical properties for a cloud."""

        # Centroid
        coords = np.argwhere(mask)
        centroid = tuple(np.mean(coords, axis=0))

        # Pixel area
        pixel_area = np.sum(mask)

        # Extract intensity values
        intensities = image_data[mask]
        peak_intensity = np.max(intensities)
        mean_intensity = np.mean(intensities)

        # Convert to physical units (simplified - needs calibration)
        mass = self._intensity_to_mass(mean_intensity, pixel_area)
        radius = np.sqrt(pixel_area / np.pi)

        # Velocity dispersion (from network or simple estimate)
        velocity_dispersion = 1.0  # km/s, placeholder

        # Virial parameter
        virial_param = self._compute_virial_parameter(mass, radius,
                                                       velocity_dispersion)

        # Bound status
        if virial_param < 1.0:
            bound_status = 'bound'
        elif virial_param < 2.0:
            bound_status = 'pressure-confined'
        else:
            bound_status = 'unbound'

        # Free-fall time
        freefall_time = self._compute_freefall_time(mean_intensity)

        # Jeans length
        jeans_length = self._compute_jeans_length(mean_intensity)

        # Morphology (simplified)
        morphology_type = self._classify_morphology(mask)

        return CloudProperties(
            id=cloud_id,
            mask=mask,
            centroid=centroid,
            pixel_area=pixel_area,
            physical_area=radius ** 2 * np.pi,
            mass=mass,
            radius=radius,
            peak_column_density=peak_intensity,
            mean_column_density=mean_intensity,
            velocity_dispersion=velocity_dispersion,
            virial_parameter=virial_param,
            star_formation_efficiency=0.0,  # Needs YSO data
            freefall_time=freefall_time,
            jeans_length=jeans_length,
            bound_status=bound_status,
            morphology_type=morphology_type
        )

    def _intensity_to_mass(self, intensity: float, area: float) -> float:
        """Convert intensity to mass (simplified)."""
        # Real implementation would use:
        # - Distance to source
        # - CO-to-H2 conversion factor
        # - Helium abundance correction
        return intensity * area * 0.1  # Placeholder

    def _compute_virial_parameter(self, mass: float, radius: float,
                                   sigma: float) -> float:
        """Compute virial parameter."""
        # alpha_vir = 5 * sigma^2 * R / (G * M)
        G = 0.0043  # pc Msun^-1 (km/s)^2

        return 5 * sigma ** 2 * radius / (G * mass + 1e-10)

    def _compute_freefall_time(self, density: float) -> float:
        """Compute free-fall time in Myr."""
        # t_ff = sqrt(3*pi / 32 / G / rho)
        # Simplified
        return 1.0 / np.sqrt(density + 1e-10)

    def _compute_jeans_length(self, density: float) -> float:
        """Compute Jeans length in pc."""
        # lambda_J = cs * sqrt(pi / G / rho)
        # Simplified
        return 0.1 / np.sqrt(density + 1e-10)

    def _classify_morphology(self, mask: np.ndarray) -> str:
        """Classify cloud morphology."""
        from skimage.measure import regionprops

        props = regionprops(mask.astype(int))

        if len(props) == 0:
            return 'irregular'

        prop = props[0]

        # Eccentricity
        ecc = prop.eccentricity

        # Solidity (ratio of area to convex hull area)
        solidity = prop.solidity

        if ecc > 0.9:
            return 'filamentary'
        elif ecc < 0.5 and solidity > 0.8:
            return 'spherical'
        elif solidity < 0.6:
            return 'cometary'
        else:
            return 'irregular'

    def _apply_nms(
        self,
        clouds: List[CloudProperties],
        iou_threshold: float
    ) -> List[CloudProperties]:
        """Apply non-maximum suppression to remove duplicates."""
        if len(clouds) == 0:
            return clouds

        # Compute IoU matrix
        iou_matrix = np.zeros((len(clouds), len(clouds)))

        for i, c1 in enumerate(clouds):
            for j, c2 in enumerate(clouds):
                if i == j:
                    iou_matrix[i, j] = 1.0
                else:
                    iou_matrix[i, j] = self._compute_iou(c1.mask, c2.mask)

        # NMS
        keep = []
        suppressed = set()

        # Sort by mass (largest first)
        sorted_idx = sorted(range(len(clouds)),
                           key=lambda i: clouds[i].mass, reverse=True)

        for i in sorted_idx:
            if i in suppressed:
                continue

            keep.append(i)

            # Suppress overlapping clouds
            for j in range(len(clouds)):
                if j != i and iou_matrix[i, j] > iou_threshold:
                    suppressed.add(j)

        return [clouds[i] for i in keep]

    def _compute_iou(self, mask1: np.ndarray, mask2: np.ndarray) -> float:
        """Compute IoU between two masks."""
        intersection = np.sum(mask1 & mask2)
        union = np.sum(mask1 | mask2)

        return intersection / (union + 1e-10)


class VelocityCubeSegmenter(nn.Module):
    """
    Segment clouds in 3D velocity-position-position (PPP) data cubes.

    Essential for separating overlapping clouds along the line of sight
    and identifying velocity-coherent structures.

    Applications:
    - Separating velocity components in complex regions
    - Identifying cloud-cloud interactions
    - Studying velocity gradients and collapse
    """

    def __init__(self, in_channels: int = 1, base_features: int = 32):
        super().__init__()

        # 3D encoder for position-position-velocity cubes
        self.enc1 = nn.Conv3d(in_channels, base_features,
                              kernel_size=3, padding=1)
        self.enc2 = nn.Conv3d(base_features, base_features * 2,
                              kernel_size=3, padding=1)
        self.enc3 = nn.Conv3d(base_features * 2, base_features * 4,
                              kernel_size=3, padding=1)

        # 3D decoder
        self.dec3 = nn.ConvTranspose3d(base_features * 4, base_features * 2,
                                       kernel_size=2, stride=2)
        self.dec2 = nn.ConvTranspose3d(base_features * 2, base_features,
                                       kernel_size=2, stride=2)
        self.dec1 = nn.Conv3d(base_features, 1, kernel_size=1)

        self.bn1 = nn.BatchNorm3d(base_features)
        self.bn2 = nn.BatchNorm3d(base_features * 2)
        self.bn3 = nn.BatchNorm3d(base_features * 4)
        self.relu = nn.ReLU(inplace=True)
        self.sigmoid = nn.Sigmoid()

    def forward(self, cube: torch.Tensor) -> torch.Tensor:
        """
        Args:
            cube: Input cube [B, C, V, H, W]

        Returns:
            Instance segmentation mask [B, 1, V, H, W]
        """
        # Encode
        x = self.relu(self.bn1(self.enc1(cube)))
        x = F.max_pool3d(x, 2)

        x = self.relu(self.bn2(self.enc2(x)))
        x = F.max_pool3d(x, 2)

        x = self.relu(self.bn3(self.enc3(x)))

        # Decode
        x = self.relu(self.bn2(self.dec3(x)))
        x = self.relu(self.bn1(self.dec2(x)))

        masks = self.sigmoid(self.dec1(x))

        return masks


def train_cloud_segmenter(
    model: MolecularCloudSegmenter,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    num_epochs: int = 50,
    learning_rate: float = 1e-4,
    device: str = 'cuda'
) -> MolecularCloudSegmenter:
    """
    Train cloud segmenter on annotated data.

    Args:
        model: MolecularCloudSegmenter model
        train_loader: Training data with masks and properties
        val_loader: Validation data
        num_epochs: Training epochs
        learning_rate: Learning rate
        device: Training device

    Returns:
        Trained model
    """
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    def loss_fn(predictions, targets):
        # Classification loss (objectness)
        obj_loss = F.binary_cross_entropy_with_logits(
            predictions['objectness'][0],
            targets['objectness']
        )

        # Mask loss
        mask_loss = F.binary_cross_entropy(
            predictions['masks'],
            targets['masks']
        )

        # Property regression losses
        mass_loss = F.mse_loss(
            predictions['properties']['mass'],
            targets['mass']
        )

        radius_loss = F.mse_loss(
            predictions['properties']['radius'],
            targets['radius']
        )

        # Morphology classification loss
        morph_loss = F.cross_entropy(
            predictions['properties']['morphology_logits'],
            targets['morphology']
        )

        # Combined loss
        total_loss = (
            1.0 * obj_loss +
            2.0 * mask_loss +
            0.1 * mass_loss +
            0.1 * radius_loss +
            0.5 * morph_loss
        )

        return total_loss

    best_val_loss = float('inf')

    for epoch in range(num_epochs):
        model.train()
        train_loss = 0.0

        for batch in train_loader:
            images = batch['image'].to(device)
            targets = {k: v.to(device) for k, v in batch.items()
                      if k != 'image'}

            optimizer.zero_grad()
            predictions = model(images)
            loss = loss_fn(predictions, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(device)
                targets = {k: v.to(device) for k, v in batch.items()
                          if k != 'image'}

                predictions = model(images)
                loss = loss_fn(predictions, targets)
                val_loss += loss.item()

        val_loss /= len(val_loader)

        print(f"Epoch {epoch+1}/{num_epochs}: "
              f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), 'cloud_segmenter_best.pth')

    return model


if __name__ == "__main__":
    print("="*70)
    print("Molecular Cloud Instance Segmentation Module")
    print("="*70)
    print()
    print("Components:")
    print("  - MolecularCloudSegmenter: Main instance segmentation model")
    print("  - VelocityCubeSegmenter: 3D PPP cube segmentation")
    print("  - CloudProperties: Physical property data structure")
    print("  - CloudPropertyHead: Property estimation head")
    print()
    print("Applications:")
    print("  - GMC cataloging from CO surveys")
    print("  - Clump and core identification")
    print("  - Mass and size estimation")
    print("  - Star formation efficiency calculation")
    print("  - Velocity-coherent structure analysis")
    print("="*70)
