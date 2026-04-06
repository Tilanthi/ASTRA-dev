#!/usr/bin/env python3
"""
Deep Learning Infrastructure for Astronomical Discovery

Phase 1 Implementation: Deep learning modules optimized for astronomical data.

Author: STAN Evolution Team
Date: 2026-03-18

Capabilities:
- Convolutional networks for image analysis (galaxy morphology, ISM structure)
- Autoencoders for anomaly detection (transients, unusual sources)
- Transformers for time series (stellar variability, molecular cloud dynamics)
- Physics-informed neural networks (radiative transfer, stellar structure)
- Cross-modal learning (multi-wavelength data fusion)
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import warnings

# Try to import advanced deep learning libraries
try:
    import torchvision.models as models
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False
    models = None


@dataclass
class DLConfig:
    """Configuration for deep learning models"""
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    num_workers: int = 4
    random_seed: int = 42


# =============================================================================
# CONVOLUTIONAL NEURAL NETWORKS FOR MORPHOLOGY ANALYSIS
# =============================================================================

class GalaxyMorphologyCNN(nn.Module):
    """
    CNN for galaxy morphological classification.

    Classifies galaxies into:
    - Elliptical (E0-7)
    - Lenticular (S0, SB0)
    - Spiral (Sa-d, SBa-d)
    - Irregular
    - Merging/Interacting
    - Lensing systems

    Also extracts features for:
    - Bar detection
    - Spiral arm counting
    - Asymmetry measurement
    - Star-forming knot identification
    """

    def __init__(self, num_classes: int = 10, input_channels: int = 3):
        super().__init__()

        # Feature extraction backbone
        self.features = nn.Sequential(
            # Block 1: Low-level features (edges, textures)
            nn.Conv2d(input_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 2: Mid-level features (structures, patterns)
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 3: High-level features (global morphology)
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 4: Semantic features
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        # Classification head
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(256, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )

        # Auxiliary heads for specific tasks
        self.bar_detector = nn.Sequential(
            nn.Conv2d(128, 64, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 1, kernel_size=1),
            nn.Sigmoid()
        )

        self.asymmetry_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass with multiple outputs"""
        # Extract features through backbone
        x = self.features[:8](x)  # Through Block 3
        morph_features = x

        x = self.features[8:](x)  # Through global pooling
        features = x

        # Main classification
        logits = self.classifier(features)

        # Auxiliary outputs (use Block 3 features)
        bar_score = torch.mean(self.bar_detector(morph_features))

        features_flat = torch.flatten(features, 1)
        asymmetry = self.asymmetry_head(features_flat)

        return {
            'logits': logits,
            'bar_score': bar_score,
            'asymmetry': asymmetry,
            'features': features
        }


class ISMStructureCNN(nn.Module):
    """
    CNN for Interstellar Medium structure analysis.

    Analyzes:
    - Molecular cloud boundaries and filaments
    - HII region morphologies
    - Supernova remnant shells
    - Dust lanes and filaments
    - Pillars and globules in star-forming regions

    Architecture optimized for:
    - Multi-scale structure detection
    - Curvature analysis for filaments
    - Density gradient detection
    """

    def __init__(self, input_channels: int = 1):
        super().__init__()

        # Multi-scale feature extraction (U-Net style)
        self.encoder1 = self._make_block(input_channels, 32)
        self.encoder2 = self._make_block(32, 64)
        self.encoder3 = self._make_block(64, 128)
        self.encoder4 = self._make_block(128, 256)

        # Bottleneck
        self.bottleneck = self._make_block(256, 512)

        # Decoder with skip connections
        self.decoder4 = self._make_decode_block(512, 256)
        self.decoder3 = self._make_decode_block(256, 128)
        self.decoder2 = self._make_decode_block(128, 64)
        self.decoder1 = self._make_decode_block(64, 32)

        # Segmentation outputs
        self.filament_mask = nn.Conv2d(32, 1, kernel_size=1)
        self.density_map = nn.Conv2d(32, 1, kernel_size=1)
        self.curvature_map = nn.Conv2d(32, 2, kernel_size=1)  # 2D curvature

    def _make_block(self, in_ch: int, out_ch: int) -> nn.Module:
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def _make_decode_block(self, in_ch: int, out_ch: int) -> nn.Module:
        return nn.Sequential(
            nn.ConvTranspose2d(in_ch, out_ch, kernel_size=2, stride=2),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward with skip connections"""
        # Encoder
        e1 = self.encoder1(x)
        p1 = F.max_pool2d(e1, 2)

        e2 = self.encoder2(p1)
        p2 = F.max_pool2d(e2, 2)

        e3 = self.encoder3(p2)
        p3 = F.max_pool2d(e3, 2)

        e4 = self.encoder4(p3)
        p4 = F.max_pool2d(e4, 2)

        # Bottleneck
        b = self.bottleneck(p4)

        # Decoder with skip connections
        d4 = self.decoder4(b) + e4
        d3 = self.decoder3(d4) + e3
        d2 = self.decoder2(d3) + e2
        d1 = self.decoder1(d2) + e1

        # Outputs
        filament_mask = torch.sigmoid(self.filament_mask(d1))
        density = self.density_map(d1)
        curvature = self.curvature_map(d1)

        return {
            'filament_mask': filament_mask,
            'density_map': density,
            'curvature_map': curvature,
            'features': d1
        }


# =============================================================================
# AUTOENCODERS FOR ANOMALY DETECTION
# =============================================================================

class SpectralAutoencoder(nn.Module):
    """
    Variational autoencoder for spectral data.

    Applications:
    - Anomaly detection in stellar spectra (peculiar stars, chemical peculiarities)
    - Novel line identification
    - Dimensionality reduction for large spectral surveys
    - Denoising spectra
    - Latent space clustering for stellar classification

    Supports:
    - Optical spectra (300-1000 nm)
    - Infrared spectra (1-5 μm)
    - Submillimeter/radio spectra (molecular lines)
    """

    def __init__(self, input_dim: int, latent_dim: int = 32, hidden_dims: List[int] = [256, 128, 64]):
        super().__init__()

        # Encoding
        layers = []
        prev_dim = input_dim
        for dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, dim),
                nn.ReLU(inplace=True),
                nn.Dropout(0.1),
            ])
            prev_dim = dim

        # Latent space
        self.fc_mu = nn.Linear(prev_dim, latent_dim)
        self.fc_logvar = nn.Linear(prev_dim, latent_dim)

        # Decoding
        decoder_layers = []
        prev_dim = latent_dim
        for dim in reversed(hidden_dims):
            decoder_layers.extend([
                nn.Linear(prev_dim, dim),
                nn.ReLU(inplace=True),
                nn.Dropout(0.1),
            ])
            prev_dim = dim
        decoder_layers.append(nn.Linear(prev_dim, input_dim))

        self.encoder = nn.Sequential(*layers)
        self.decoder = nn.Sequential(*decoder_layers)

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode spectrum to latent space"""
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Reparameterization trick"""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent vector to spectrum"""
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        reconstructed = self.decode(z)

        # Reconstruction loss per wavelength
        recon_loss = F.mse_loss(reconstructed, x, reduction='none')

        # KL divergence
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())

        return {
            'reconstructed': reconstructed,
            'mu': mu,
            'logvar': logvar,
            'z': z,
            'recon_loss': recon_loss,
            'kl_loss': kl_loss
        }

    def detect_anomaly(self, x: torch.Tensor, threshold: float = 3.0) -> Dict[str, torch.Tensor]:
        """Detect anomalous spectra using reconstruction error"""
        with torch.no_grad():
            mu, logvar = self.encode(x)
            z = self.reparameterize(mu, logvar)
            reconstructed = self.decode(z)

            # Reconstruction error per wavelength
            error = (x - reconstructed).pow(2)

            # Aggregate
            mse = error.mean(dim=1)
            anomaly_score = (mse - mse.mean()) / (mse.std() + 1e-10)

            anomalies = anomaly_score > threshold

        return {
            'anomaly_score': anomaly_score,
            'is_anomalous': anomalies,
            'reconstruction_error': mse
        }


class LightCurveAutoencoder(nn.Module):
    """
    LSTM-based autoencoder for time series anomaly detection.

    Applications:
    - Anomalous transients detection
    - Unusual stellar variability
    - Microlensing events
    - Exoplanet transit validation
    - Periodic vs aperiodic classification
    """

    def __init__(self, input_size: int = 1, hidden_size: int = 64, latent_size: int = 16):
        super().__init__()

        # Encoder: LSTM
        self.encoder_lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc_mu = nn.Linear(hidden_size, latent_size)
        self.fc_logvar = nn.Linear(hidden_size, latent_size)

        # Decoder: LSTM
        self.decoder_lstm = nn.LSTM(latent_size, hidden_size, batch_first=True)
        self.fc_out = nn.Linear(hidden_size, input_size)

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode time series"""
        _, (h_n, _) = self.encoder_lstm(x)
        h_last = h_n.squeeze(0)
        mu = self.fc_mu(h_last)
        logvar = self.fc_logvar(h_last)
        return mu, logvar

    def decode(self, z: torch.Tensor, seq_len: int) -> torch.Tensor:
        """Decode latent vector to time series"""
        batch_size = z.size(0)
        # Repeat latent vector for each time step
        z_repeated = z.unsqueeze(1).repeat(1, seq_len, 1)

        output, _ = self.decoder_lstm(z_repeated)
        output = self.fc_out(output)
        return output

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        seq_len = x.size(1)
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        reconstructed = self.decode(z, seq_len)

        recon_loss = F.mse_loss(reconstructed, x)
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())

        return {
            'reconstructed': reconstructed,
            'mu': mu,
            'logvar': logvar,
            'z': z,
            'recon_loss': recon_loss,
            'kl_loss': kl_loss
        }


# =============================================================================
# TRANSFORMERS FOR TIME SERIES ANALYSIS
# =============================================================================

class TimeSeriesTransformer(nn.Module):
    """
    Transformer model for astronomical time series analysis.

    Applications:
    - Stellar variability classification (eclipsing binaries, pulsations, rotation)
    - Molecular cloud dynamics evolution
    - AGN variability characterization
    - Forecasting and prediction
    - Period detection beyond Lomb-Scargle

    Features:
    - Self-attention for long-range dependencies
    - Positional encoding for temporal information
    - Multi-head attention for multiple patterns
    """

    def __init__(self,
                 input_dim: int = 1,
                 d_model: int = 64,
                 nhead: int = 4,
                 num_layers: int = 4,
                 dim_feedforward: int = 256,
                 dropout: float = 0.1,
                 max_seq_len: int = 1000):
        super().__init__()

        self.d_model = d_model
        self.max_seq_len = max_seq_len

        # Input embedding
        self.input_projection = nn.Linear(input_dim, d_model)

        # Positional encoding
        pe = self._create_positional_encoding(max_seq_len, d_model)
        self.register_buffer('pe', pe)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Output heads
        self.classification_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 10)  # 10 variability classes
        )

        self.forecasting_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1)
        )

        self.period_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(inplace=True),
            nn.Linear(d_model // 2, 1),
            nn.Sigmoid()  # Output in [0, 1], scale to period range
        )

    def _create_positional_encoding(self, max_len: int, d_model: int) -> torch.Tensor:
        """Create sinusoidal positional encoding"""
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        return pe.unsqueeze(0)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            x: Input time series [batch, seq_len, features]
            mask: Attention mask [batch, seq_len]
        """
        batch_size, seq_len, _ = x.shape

        # Project and add positional encoding
        x = self.input_projection(x) * math.sqrt(self.d_model)
        x = x + self.pe[:, :seq_len, :].transpose(0, 1)

        # Transform (src_key_padding_mask for masked positions)
        if mask is not None:
            src_key_padding_mask = mask == 0
        else:
            src_key_padding_mask = None

        x = x.transpose(0, 1)  # [seq, batch, features] for transformer
        x = self.transformer(x, src_key_padding_mask=src_key_padding_mask)
        x = x.transpose(0, 1)  # [batch, seq, features]

        # Global pooling for classification
        pooled = x.mean(dim=1)  # [batch, features]

        # Outputs
        class_logits = self.classification_head(pooled)
        forecast = self.forecasting_head(pooled)
        period_score = self.period_head(pooled)  # [batch, 1]

        return {
            'class_logits': class_logits,
            'forecast': forecast,
            'period_score': period_score,
            'features': pooled,
            'sequence_features': x
        }


# =============================================================================
# PHYSICS-INFORMED NEURAL NETWORKS (PINNs)
# =============================================================================

class RadiativeTransferPINN(nn.Module):
    """
    Physics-Informed Neural Network for radiative transfer.

    Solves the radiative transfer equation:
    dI/dτ = -I + S

    where:
    - I is specific intensity
    - τ is optical depth
    - S is source function (temperature, density profile)

    Applications:
    - Stellar atmosphere modeling
    - ISM radiative transfer
    - Photodissociation regions
    - Dust emission/absorption

    Loss function includes:
    - Data mismatch
    - PDE residual (dI/dτ + I - S)
    - Boundary conditions
    - Physical constraints (positivity, energy conservation)
    """

    def __init__(self,
                 hidden_layers: List[int] = [64, 64, 64, 64],
                 activation: str = 'tanh'):
        super().__init__()

        layers = []
        prev_dim = 2  # [τ, angle/μ]
        for dim in hidden_layers:
            layers.append(nn.Linear(prev_dim, dim))
            if activation == 'tanh':
                layers.append(nn.Tanh())
            elif activation == 'relu':
                layers.append(nn.ReLU())
            else:
                layers.append(nn.Tanh())
            prev_dim = dim

        layers.append(nn.Linear(prev_dim, 1))  # Intensity I

        self.network = nn.Sequential(*layers)

    def forward(self, tau: torch.Tensor, mu: torch.Tensor) -> torch.Tensor:
        """
        Predict intensity at given optical depth and angle.

        Args:
            tau: Optical depth [batch, 1]
            mu: Cosine of angle (μ = cos θ) [batch, 1]

        Returns:
            Specific intensity I [batch, 1]
        """
        # Normalize inputs
        tau_norm = torch.tanh(tau)
        mu_norm = mu  # Already in [-1, 1]

        # Concatenate inputs
        x = torch.cat([tau_norm, mu_norm], dim=1)

        # Predict intensity
        I = self.network(x)

        # Ensure positivity
        I = torch.relu(I)

        return I

    def compute_physics_loss(self,
                              tau: torch.Tensor,
                              mu: torch.Tensor,
                              S: torch.Tensor,
                              I_pred: torch.Tensor,
                              method: str = 'automatic') -> torch.Tensor:
        """
        Compute physics-informed loss.

        Radiative transfer equation: dI/dτ = -I + S

        Args:
            tau: Optical depth
            mu: Cosine of angle
            S: Source function
            I_pred: Predicted intensity
            method: 'automatic' or 'finite_difference'
        """
        if method == 'automatic':
            # Automatic differentiation for derivative
            tau.requires_grad_(True)

            # Re-compute I with gradient tracking
            x = torch.cat([torch.tanh(tau), mu], dim=1)

            # Forward through network with gradient
            I = I_pred

            # Derivative dI/dτ
            dI_dtau = torch.autograd.grad(
                outputs=I,
                inputs=tau,
                grad_outputs=torch.ones_like(I),
                create_graph=True,
                retain_graph=True
            )[0]

            # PDE residual
            residual = dI_dtau + I - S

        else:
            # Finite difference approximation
            epsilon = 1e-3
            tau_plus = tau + epsilon

            I_plus = self.forward(tau_plus, mu)
            dI_dtau = (I_plus - I_pred) / epsilon

            residual = dI_dtau + I_pred - S

        # Loss is mean squared residual
        physics_loss = torch.mean(residual**2)

        return physics_loss

    def compute_boundary_loss(self, I_pred: torch.Tensor, I_surface: torch.Tensor) -> torch.Tensor:
        """Boundary condition at τ=0"""
        # At surface (τ=0), I should match incident radiation
        surface_loss = torch.mean((I_pred[tau == 0] - I_surface)**2)
        return surface_loss


class StellarStructurePINN(nn.Module):
    """
    Physics-Informed Neural Network for stellar structure.

    Solves the stellar structure equations:
    1. dP/dr = -G*M*r*ρ/r²  (Hydrostatic equilibrium)
    2. dM/dr = 4π*r²*ρ     (Mass conservation)
    3. dL/dr = 4π*r²*ρ*ε (Energy generation)
    4. Equation of state: P = P(ρ, T)
    5. Energy generation: ε = ε(ρ, T)

    Applications:
    - Stellar parameter inference from observables
    - Asteroseismology (p-mode frequencies)
    - Stellar evolution modeling
    """

    def __init__(self, hidden_layers: List[int] = [64, 64, 64, 64]):
        super().__init__()

        # Input: [r/R_sun, log(T), log(ρ), log(P), log(L), log(M)]
        # Output: [log(P), log(ρ), log(T), log(L)] at next layer

        self.network = nn.Sequential(
            nn.Linear(6, hidden_layers[0]),
            nn.Tanh(),
            *[layer for _ in range(len(hidden_layers)-1) for layer in
             [nn.Linear(hidden_layers[i], hidden_layers[i+1]), nn.Tanh()]]
        )

    def forward(self, r_norm: torch.Tensor, log_P: torch.Tensor,
                log_rho: torch.Tensor, log_T: torch.Tensor,
                log_L: torch.Tensor, log_M: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Predict stellar structure at next layer.

        Args:
            r_norm: Normalized radius (r/R_sun)
            log_P: Log pressure
            log_rho: Log density
            log_T: Log temperature
            log_L: Log luminosity
            log_M: Log mass

        Returns:
            Dictionary with predicted stellar structure
        """
        x = torch.cat([r_norm, log_P, log_rho, log_T, log_L, log_M], dim=1)
        out = self.network(x)

        # Split output
        log_P_pred = out[:, 0:1]
        log_rho_pred = out[:, 1:2]
        log_T_pred = out[:, 2:3]
        log_L_pred = out[:, 3:4]

        return {
            'log_P': log_P_pred,
            'log_rho': log_rho_pred,
            'log_T': log_T_pred,
            'log_L': log_L_pred
        }

    def compute_physics_loss(self,
                             r: torch.Tensor,
                             predictions: Dict[str, torch.Tensor],
                             G_const: float = 6.674e-8) -> torch.Tensor:
        """
        Compute physics loss from stellar structure equations.
        """
        # Extract variables
        log_P = predictions['log_P']
        log_rho = predictions['log_rho']
        log_T = predictions['log_T']
        log_L = predictions['log_L']

        P = torch.exp(log_P)
        rho = torch.exp(log_rho)
        L = torch.exp(log_L)

        # Hydrostatic equilibrium: dP/dr = -GMρ/r²
        # Compute gradient w.r.t r
        dP_dr = torch.autograd.grad(
            outputs=log_P,
            inputs=r,
            grad_outputs=torch.ones_like(log_P),
            create_graph=True,
            retain_graph=True
        )[0]

        # Right side (with proper mass profile)
        # This is simplified - full version would integrate M(r)
        rhs_hydro = -G_const * rho  # Simplified, should be -G*M(r)*rho/r^2

        hydro_loss = torch.mean((dP_dr - rhs_hydro)**2)

        # Energy conservation
        # L = 4π*r²*ρ*ε where ε is energy generation rate
        # Simplified: check L increases outward
        dL_dr = torch.autograd.grad(
            outputs=log_L,
            inputs=r,
            grad_outputs=torch.ones_like(log_L),
            create_graph=True,
            retain_graph=True
        )[0]

        energy_loss = torch.mean(F.relu(-dL_dr))  # Penalize negative gradient

        return hydro_loss + energy_loss


# =============================================================================
# CROSS-MODAL LEARNING FOR MULTI-WAVELENGTH DATA
# =============================================================================

class CrossModalMatcher(nn.Module):
    """
    Siamese network for cross-wavelength matching.

    Applications:
    - Matching sources between radio, infrared, optical, X-ray catalogs
    - Cross-identification of multi-wavelength detections
    - Learning shared representations across modalities
    - Transfer learning between wavelengths

    Uses contrastive learning to learn embeddings where:
    - Same source at different wavelengths → similar embeddings
    - Different sources → dissimilar embeddings
    """

    def __init__(self, input_dims: Dict[str, int], embedding_dim: int = 128):
        """
        Args:
            input_dims: Dictionary mapping wavelength to input dimension
                e.g., {'radio': 256, 'ir': 64, 'optical': 64}
            embedding_dim: Dimension of shared embedding space
        """
        super().__init__()

        # Create encoders for each modality
        self.encoders = nn.ModuleDict()
        for wavelength, dim in input_dims.items():
            self.encoders[wavelength] = nn.Sequential(
                nn.Linear(dim, 256),
                nn.ReLU(inplace=True),
                nn.Dropout(0.1),
                nn.Linear(256, 128),
                nn.ReLU(inplace=True),
                nn.Linear(128, embedding_dim)
            )

        self.embedding_dim = embedding_dim

    def encode(self, x: torch.Tensor, wavelength: str) -> torch.Tensor:
        """Encode data from specific wavelength"""
        return self.encoders[wavelength](x)

    def forward(self, x1: torch.Tensor, x2: torch.Tensor,
                wavelength1: str, wavelength2: str) -> Dict[str, torch.Tensor]:
        """
        Compute similarity between two observations.

        Returns:
            Dictionary with embeddings and similarity score
        """
        emb1 = self.encode(x1, wavelength1)
        emb2 = self.encode(x2, wavelength2)

        # Cosine similarity
        similarity = F.cosine_similarity(emb1, emb2, dim=1)

        # Euclidean distance
        distance = torch.norm(emb1 - emb2, dim=1)

        return {
            'embedding1': emb1,
            'embedding2': emb2,
            'cosine_similarity': similarity,
            'euclidean_distance': distance
        }


# =============================================================================
# TRAINING AND EVALUATION
# =============================================================================

def train_autoencoder(model: nn.Module,
                      train_loader: DataLoader,
                      val_loader: DataLoader,
                      config: DLConfig,
                      num_epochs: int = 100) -> Dict[str, List]:
    """Train autoencoder with early stopping"""
    device = torch.device(config.device)
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(),
                                 lr=config.learning_rate,
                                 weight_decay=config.weight_decay)

    train_losses = []
    val_losses = []

    best_val_loss = float('inf')
    patience = 10
    patience_counter = 0

    for epoch in range(num_epochs):
        # Training
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            data = batch[0].to(device)
            optimizer.zero_grad()

            output = model(data)
            recon_loss = output['recon_loss'].mean()
            kl_loss = output['kl_loss']

            loss = recon_loss + 0.001 * kl_loss  # Beta-VAE
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)
        train_losses.append(train_loss)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                data = batch[0].to(device)
                output = model(data)
                loss = output['recon_loss'].mean() + 0.001 * output['kl_loss']
                val_loss += loss.item()

        val_loss /= len(val_loader)
        val_losses.append(val_loss)

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save model
            torch.save(model.state_dict(), 'best_model.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch}")
                break

        if epoch % 10 == 0:
            print(f"Epoch {epoch}: Train Loss = {train_loss:.4f}, Val Loss = {val_loss:.4f}")

    return {
        'train_losses': train_losses,
        'val_losses': val_losses
    }


# =============================================================================
# DATASETS
# =============================================================================

class SpectralDataset(Dataset):
    """Dataset for spectroscopic data"""

    def __init__(self, spectra: np.ndarray, wavelengths: np.ndarray,
                 labels: Optional[np.ndarray] = None,
                 transform=None):
        """
        Args:
            spectra: Spectral data [N, wavelength_bins]
            wavelengths: Wavelength array [wavelength_bins]
            labels: Optional labels [N]
            transform: Optional transform
        """
        self.spectra = torch.FloatTensor(spectra)
        self.wavelengths = wavelengths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.spectra)

    def __getitem__(self, idx):
        spectrum = self.spectra[idx]

        if self.transform:
            spectrum = self.transform(spectrum)

        if self.labels is not None:
            return spectrum, self.labels[idx]
        return spectrum,


class ImageDataset(Dataset):
    """Dataset for astronomical images"""

    def __init__(self, images: np.ndarray, labels: Optional[np.ndarray] = None,
                 transform=None):
        """
        Args:
            images: Image data [N, C, H, W]
            labels: Optional labels [N]
            transform: Optional transform
        """
        self.images = torch.FloatTensor(images)
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image = self.images[idx]

        if self.transform:
            image = self.transform(image)

        if self.labels is not None:
            return image, self.labels[idx]
        return image,


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DLConfig',
    'GalaxyMorphologyCNN',
    'ISMStructureCNN',
    'SpectralAutoencoder',
    'LightCurveAutoencoder',
    'TimeSeriesTransformer',
    'RadiativeTransferPINN',
    'StellarStructurePINN',
    'CrossModalMatcher',
    'train_autoencoder',
    'SpectralDataset',
    'ImageDataset',
]

# Try to import math (used in TimeSeriesTransformer)
try:
    import math
except ImportError:
    # Define minimal math functions if needed
    import numpy as np
    math = type('math', (), {
        'sqrt': np.sqrt,
    })()
