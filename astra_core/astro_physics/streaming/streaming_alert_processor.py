#!/usr/bin/env python3
"""
Streaming Alert Processor for Time-Domain Astronomy

Processes real-time alert streams from time-domain surveys:
- LSST (ZTF-like alert stream)
- ZTF (Zwicky Transient Facility)
- ATLAS
- Gaia
- LIGO/Virgo gravitational wave triggers
- Neutrino alerts (IceCube, Super-Kamiokande)

Capabilities:
- Real-time filtering and classification
- Cross-matching with catalogs
- Multi-wavelength follow-up coordination
- Alert aggregation and de-duplication
- Rank-based prioritization
- Machine inference for transient typing

Author: STAN Evolution Team
Date: 2025-03-18
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import deque, defaultdict


class AlertSource(Enum):
    """Alert source types"""
    LSST = "lsst"
    ZTF = "ztf"
    ATLAS = "atlas"
    GAIA = "gaia"
    LIGO = "ligo"
    ICECUBE = "icecube"
    SUPERK = "super_kamiokande"


class TransientType(Enum):
    """Transient classification types"""
    UNKNOWN = "unknown"
    SN_Ia = "sn_ia"  # Type Ia supernova
    SN_II = "sn_ii"  # Type II supernova
    SN_IBC = "sn_ibc"  # Type Ib/c supernova
    KN = "kilonova"  # Kilonova
    TDE = "tidal_disruption"  # Tidal disruption event
    CV = "cataclysmic_variable"
    AGN = "agn"
    BLAZAR = "blazar"
    GRB = "gamma_ray_burst"
    ORPHAN = "orphan_afterglow"
    MICROLENSING = "microlensing"
    VARSTAR = "variable_star"
    SOLAR_SYSTEM = "solar_system"
    SATELLITE = "satellite"


@dataclass
class AlertMetadata:
    """Metadata from alert stream"""
    alert_id: str
    source: AlertSource
    timestamp: datetime
    ra: float  # degrees
    dec: float  # degrees
    error_radius: float  # degrees
    magnitude: float
    magnitude_error: float
    filter: str  # photometric filter
    history: List[Dict] = field(default_factory=list)
    cutout_images: Dict[str, Any] = field(default_factory=dict)
    raw_packet: Dict = field(default_factory=dict)


@dataclass
class ProcessedAlert:
    """Processed alert with classification and actions"""
    metadata: AlertMetadata
    transient_type: TransientType
    confidence: float
    priority: float  # 0-1, higher = more urgent
    recommended_actions: List[str]
    classification_reasoning: str
    crossmatches: List[Dict] = field(default_factory=list)
    features: Dict[str, float] = field(default_factory=dict)


class AlertFeatureExtractor:
    """
    Extract features from alerts for classification.

    Features include:
    - Light curve statistics (rise time, amplitude, color)
    - Host galaxy properties (if available)
    - Contextual information (galaxy density, distance to nearest galaxy)
    - Historical light curve behavior
    """

    def __init__(self):
        pass

    def extract_features(self, alert: AlertMetadata) -> Dict[str, float]:
        """
        Extract features from alert.

        Args:
            alert: Alert metadata

        Returns:
            Feature dictionary
        """
        features = {}

        # Photometric features
        features['magnitude'] = alert.magnitude
        features['magnitude_error'] = alert.magnitude_error

        # Light curve features from history
        if len(alert.history) > 1:
            mags = [h['magnitude'] for h in alert.history]
            times = [h['timestamp'] for h in alert.history]

            # Amplitude
            features['amplitude'] = max(mags) - min(mags)

            # Rise time (time from minimum to current)
            min_idx = np.argmin(mags)
            max_idx = np.argmax(mags)
            if max_idx > min_idx:
                features['rise_time'] = (times[max_idx] - times[min_idx]).total_seconds() / 86400  # days
            else:
                features['rise_time'] = 0.0

            # Variability index
            features['variability'] = np.std(mags) if len(mags) > 1 else 0.0

            # Detection significance
            features['significance'] = (alert.magnitude - np.mean(mags)) / (np.std(mags) + 1e-10)
        else:
            features['amplitude'] = 0.0
            features['rise_time'] = 0.0
            features['variability'] = 0.0
            features['significance'] = 0.0

        # Positional features
        features['galactic_latitude'] = self._compute_galactic_latitude(alert.ra, alert.dec)

        # Filter-based features
        features['is_r_band'] = 1.0 if alert.filter in ['r', 'R'] else 0.0
        features['is_g_band'] = 1.0 if alert.filter in ['g', 'G'] else 0.0

        return features

    def _compute_galactic_latitude(self, ra: float, dec: float) -> float:
        """Compute galactic latitude (simplified)."""
        # Simplified conversion - real implementation would use astropy
        return dec  # Placeholder


class AlertClassifier:
    """
    Classify alerts into transient types.

    Uses a combination of:
    - Rule-based heuristics
    - Machine learning models
    - Cross-match information
    """

    def __init__(self):
        self.feature_extractor = AlertFeatureExtractor()

        # Define classification rules (simplified - would use trained models)
        self.rules = {
            TransientType.SN_Ia: self._classify_sn_ia,
            TransientType.SN_II: self._classify_sn_ii,
            TransientType.KN: self._classify_kilonova,
            TransientType.TDE: self._classify_tde,
            TransientType.CV: self._classify_cv,
            TransientType.AGN: self._classify_agn,
            TransientType.MICROLENSING: self._classify_microlensing,
            TransientType.VARSTAR: self._classify_variable_star,
        }

    def classify(self, alert: AlertMetadata,
                 crossmatches: List[Dict] = None) -> Tuple[TransientType, float, str]:
        """
        Classify alert into transient type.

        Args:
            alert: Alert metadata
            crossmatches: Cross-match results with catalogs

        Returns:
            Tuple of (type, confidence, reasoning)
        """
        features = self.feature_extractor.extract_features(alert)

        # Check cross-matches first
        if crossmatches:
            for match in crossmatches:
                if match.get('catalog') == 'known_variables':
                    return TransientType.VARSTAR, 0.9, "Matched to known variable star"
                elif match.get('catalog') == 'solar_system':
                    return TransientType.SOLAR_SYSTEM, 0.95, "Solar system object"

        # Apply classification rules
        scores = {}
        reasons = {}

        for transient_type, rule_fn in self.rules.items():
            score, reason = rule_fn(features, alert, crossmatches or [])
            scores[transient_type] = score
            if score > 0:
                reasons[transient_type] = reason

        # Get best match
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]

            if best_score > 0.5:
                return best_type, best_score, reasons.get(best_type, "Classification based on features")

        return TransientType.UNKNOWN, 0.0, "Unable to classify"

    def _classify_sn_ia(self, features: Dict, alert: AlertMetadata,
                        crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as Type Ia supernova."""
        score = 0.0
        reasons = []

        # SN Ia typically in galaxies
        has_host = any(m.get('is_host', False) for m in crossmatches)
        if has_host:
            score += 0.3
            reasons.append("Located in galaxy")

        # Amplitude
        if features['amplitude'] > 1.0 and features['amplitude'] < 5.0:
            score += 0.2
            reasons.append(f"Amplitude {features['amplitude']:.2f} mag consistent with SN")

        # Rise time
        if features['rise_time'] > 10 and features['rise_time'] < 30:
            score += 0.3
            reasons.append(f"Rise time {features['rise_time']:.1f} days consistent with SN Ia")

        # Magnitude range
        if 18 < alert.magnitude < 22:
            score += 0.2
            reasons.append("Magnitude in expected range")

        reason = "; ".join(reasons) if score > 0 else "Features not consistent with SN Ia"
        return score, reason

    def _classify_sn_ii(self, features: Dict, alert: AlertMetadata,
                        crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as Type II supernova."""
        score = 0.0
        reasons = []

        # SN II in star-forming regions
        has_host = any(m.get('is_host', False) for m in crossmatches)
        if has_host:
            score += 0.2

        # Slower rise than SN Ia
        if features['rise_time'] > 20:
            score += 0.3
            reasons.append(f"Slow rise time {features['rise_time']:.1f} days")

        # Plateau phase (would need more history)
        if features['amplitude'] > 2.0:
            score += 0.2

        reason = "; ".join(reasons) if score > 0 else "Features not consistent with SN II"
        return score, reason

    def _classify_kilonova(self, features: Dict, alert: AlertMetadata,
                           crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as kilonova."""
        score = 0.0
        reasons = []

        # Check for GW trigger coincidence
        has_gw = any(m.get('catalog') == 'gw_trigger' for m in crossmatches)
        if has_gw:
            score += 0.8
            reasons.append("Coincident with GW trigger")

        # Fast evolution
        if features['rise_time'] < 5 and features['rise_time'] > 0:
            score += 0.3
            reasons.append("Fast evolution consistent with KN")

        reason = "; ".join(reasons) if score > 0 else "No evidence for kilonova"
        return score, reason

    def _classify_tde(self, features: Dict, alert: AlertMetadata,
                      crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as tidal disruption event."""
        score = 0.0
        reasons = []

        # Near galaxy center
        has_nuclear_host = any(m.get('is_nuclear', False) for m in crossmatches)
        if has_nuclear_host:
            score += 0.5
            reasons.append("Located in galaxy nucleus")

        # Slow rise
        if features['rise_time'] > 30:
            score += 0.3
            reasons.append("Slow rise time")

        reason = "; ".join(reasons) if score > 0 else "No evidence for TDE"
        return score, reason

    def _classify_cv(self, features: Dict, alert: AlertMetadata,
                     crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as cataclysmic variable."""
        score = 0.0
        reasons = []

        # High variability
        if features['variability'] > 1.0:
            score += 0.3
            reasons.append("High variability")

        # Recurrent (would need historical data)
        # This is simplified

        reason = "; ".join(reasons) if score > 0 else "No evidence for CV"
        return score, reason

    def _classify_agn(self, features: Dict, alert: AlertMetadata,
                      crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as AGN."""
        score = 0.0
        reasons = []

        # Known AGN
        is_known_agn = any(m.get('type') == 'agn' for m in crossmatches)
        if is_known_agn:
            score += 0.9
            reasons.append("Known AGN")

        reason = "; ".join(reasons) if score > 0 else "No evidence for AGN"
        return score, reason

    def _classify_microlensing(self, features: Dict, alert: AlertMetadata,
                               crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as microlensing event."""
        score = 0.0
        reasons = []

        # Galactic plane
        if abs(features.get('galactic_latitude', 0)) < 5:
            score += 0.3
            reasons.append("Near galactic plane")

        # Symmetric light curve (would need more history)

        reason = "; ".join(reasons) if score > 0 else "No evidence for microlensing"
        return score, reason

    def _classify_variable_star(self, features: Dict, alert: AlertMetadata,
                                 crossmatches: List[Dict]) -> Tuple[float, str]:
        """Classify as variable star."""
        score = 0.0
        reasons = []

        # Periodic (would need period detection)

        # Low amplitude
        if features['amplitude'] < 1.0:
            score += 0.2
            reasons.append("Low amplitude")

        reason = "; ".join(reasons) if score > 0 else "No evidence for variable star"
        return score, reason


class AlertPrioritizer:
    """
    Prioritize alerts based on scientific value and urgency.

    Factors:
    - Transient type (rare types get higher priority)
    - Confidence in classification
    - Multi-wavelength availability
    - Observability
    - Scientific interest
    """

    def __init__(self):
        # Base priorities for different types
        self.base_priorities = {
            TransientType.KN: 1.0,  # Kilonova - highest priority
            TransientType.GRB: 0.95,
            TransientType.SN_Ia: 0.6,
            TransientType.SN_II: 0.5,
            TransientType.SN_IBC: 0.6,
            TransientType.TDE: 0.8,
            TransientType.UNKNOWN: 0.4,
            TransientType.CV: 0.2,
            TransientType.AGN: 0.1,
            TransientType.MICROLENSING: 0.3,
            TransientType.VARSTAR: 0.1,
        }

    def prioritize(self, alert: AlertMetadata, transient_type: TransientType,
                   confidence: float, crossmatches: List[Dict]) -> float:
        """
        Compute priority score for alert.

        Args:
            alert: Alert metadata
            transient_type: Classified type
            confidence: Classification confidence
            crossmatches: Cross-match results

        Returns:
            Priority score [0, 1]
        """
        priority = self.base_priorities.get(transient_type, 0.3)

        # Boost for high confidence
        if confidence > 0.8:
            priority *= 1.2
        elif confidence < 0.3:
            priority *= 0.5

        # Boost for rare events
        if transient_type == TransientType.KN:
            # Check for GW coincidence
            has_gw = any(m.get('catalog') == 'gw_trigger' for m in crossmatches)
            if has_gw:
                priority = 1.0

        # Boost for events with multi-wavelength potential
        host_distance = self._get_host_distance(crossmatches)
        if host_distance and host_distance < 100:  # Mpc
            priority *= 1.1

        # Magnitude boost
        if alert.magnitude < 20:
            priority *= 1.1

        # Clip to [0, 1]
        return max(0.0, min(1.0, priority))

    def _get_host_distance(self, crossmatches: List[Dict]) -> Optional[float]:
        """Get host galaxy distance from crossmatches."""
        for match in crossmatches:
            if 'distance' in match:
                return match['distance']
        return None


class StreamingAlertProcessor:
    """
    Main alert processing system.

    Handles high-throughput alert streams with real-time processing:
    - Ingest alerts from multiple sources
    - Extract features
    - Classify transients
    - Prioritize for follow-up
    - Coordinate multi-wavelength observations
    - Aggregate duplicate alerts

    Example:
        >>> processor = StreamingAlertProcessor()
        >>>
        >>> alert = AlertMetadata(
        ...     alert_id="ZTF21abcdef",
        ...     source=AlertSource.ZTF,
        ...     timestamp=datetime.now(),
        ...     ra=123.456,
        ...     dec=-45.678,
        ...     error_radius=0.1,
        ...     magnitude=19.5,
        ...     magnitude_error=0.1,
        ...     filter="r"
        ... )
        >>>
        >>> processed = processor.process_alert(alert)
        >>> print(f"Type: {processed.transient_type}, Priority: {processed.priority}")
    """

    def __init__(self,
                 enable_classification: bool = True,
                 enable_prioritization: bool = True,
                 enable_crossmatching: bool = True):
        """
        Initialize alert processor.

        Args:
            enable_classification: Enable ML classification
            enable_prioritization: Enable priority scoring
            enable_crossmatching: Enable catalog cross-matching
        """
        self.enable_classification = enable_classification
        self.enable_prioritization = enable_prioritization
        self.enable_crossmatching = enable_crossmatching

        # Initialize components
        if enable_classification:
            self.classifier = AlertClassifier()

        if enable_prioritization:
            self.prioritizer = AlertPrioritizer()

        # Alert history for de-duplication
        self.alert_history: deque = deque(maxlen=100000)
        self.alert_lookup: Dict[str, AlertMetadata] = {}

        # Statistics
        self.stats = defaultdict(int)

    def process_alert(self, alert: AlertMetadata) -> ProcessedAlert:
        """
        Process a single alert.

        Args:
            alert: Alert metadata

        Returns:
            Processed alert with classification and recommendations
        """
        self.stats['alerts_received'] += 1

        # Check for duplicates
        is_duplicate, original_alert = self._check_duplicate(alert)
        if is_duplicate:
            self.stats['duplicates'] += 1
            alert = self._merge_alerts(original_alert, alert)

        # Cross-match with catalogs
        crossmatches = []
        if self.enable_crossmatching:
            crossmatches = self._crossmatch_catalogs(alert)

        # Classify
        transient_type = TransientType.UNKNOWN
        confidence = 0.0
        reasoning = "Classification disabled"

        if self.enable_classification:
            transient_type, confidence, reasoning = self.classifier.classify(
                alert, crossmatches
            )

        # Prioritize
        priority = 0.5
        if self.enable_prioritization:
            priority = self.prioritizer.prioritize(
                alert, transient_type, confidence, crossmatches
            )

        # Generate recommended actions
        actions = self._generate_actions(
            alert, transient_type, confidence, priority, crossmatches
        )

        # Create processed alert
        processed = ProcessedAlert(
            metadata=alert,
            transient_type=transient_type,
            confidence=confidence,
            priority=priority,
            recommended_actions=actions,
            classification_reasoning=reasoning,
            crossmatches=crossmatches,
            features={}
        )

        # Store in history
        self.alert_history.append(alert)
        self.alert_lookup[alert.alert_id] = alert

        self.stats['alerts_processed'] += 1

        return processed

    def process_alert_batch(self, alerts: List[AlertMetadata]) -> List[ProcessedAlert]:
        """
        Process a batch of alerts.

        Args:
            alerts: List of alert metadata

        Returns:
            List of processed alerts
        """
        return [self.process_alert(alert) for alert in alerts]

    def _check_duplicate(self, alert: AlertMetadata) -> Tuple[bool, Optional[AlertMetadata]]:
        """Check if alert is duplicate of existing alert."""
        # Check by position and time
        for existing in self.alert_history:
            # Spatial proximity
            sep = self._angular_separation(alert.ra, alert.dec,
                                           existing.ra, existing.dec)
            if sep < (alert.error_radius + existing.error_radius):
                # Temporal proximity
                time_diff = abs((alert.timestamp - existing.timestamp).total_seconds())
                if time_diff < 3600:  # 1 hour
                    return True, existing

        return False, None

    def _merge_alerts(self, original: AlertMetadata,
                      new_alert: AlertMetadata) -> AlertMetadata:
        """Merge duplicate alerts."""
        # Use the brighter/better measurement
        if new_alert.magnitude < original.magnitude:
            # New alert is better
            merged = AlertMetadata(
                alert_id=original.alert_id,
                source=original.source,
                timestamp=new_alert.timestamp,
                ra=new_alert.ra,
                dec=new_alert.dec,
                error_radius=min(original.error_radius, new_alert.error_radius),
                magnitude=new_alert.magnitude,
                magnitude_error=new_alert.magnitude_error,
                filter=new_alert.filter,
                history=original.history + [{'magnitude': new_alert.magnitude,
                                            'timestamp': new_alert.timestamp}],
                cutout_images=new_alert.cutout_images,
                raw_packet=new_alert.raw_packet
            )
        else:
            merged = original

        return merged

    def _angular_separation(self, ra1: float, dec1: float,
                            ra2: float, dec2: float) -> float:
        """Compute angular separation between two positions (degrees)."""
        # Haversine formula
        ra1, dec1, ra2, dec2 = np.radians([ra1, dec1, ra2, dec2])

        dra = ra2 - ra1
        ddec = dec2 - dec1

        a = np.sin(ddec/2)**2 + np.cos(dec1) * np.cos(dec2) * np.sin(dra/2)**2
        sep = 2 * np.arcsin(np.sqrt(a))

        return np.degrees(sep)

    def _crossmatch_catalogs(self, alert: AlertMetadata,
                              search_radius: float = 0.1) -> List[Dict]:
        """Cross-match alert with catalogs."""
        matches = []

        # Simplified - would use actual catalog queries
        # In production, would query:
        # - SIMBAD (for known objects)
        # - NED (for galaxy redshifts)
        # - GLADE (for GW host galaxies)
        # - Known variable star catalogs

        return matches

    def _generate_actions(self, alert: AlertMetadata, transient_type: TransientType,
                          confidence: float, priority: float,
                          crossmatches: List[Dict]) -> List[str]:
        """Generate recommended follow-up actions."""
        actions = []

        # High priority actions
        if priority > 0.8:
            if transient_type == TransientType.KN:
                actions.append("IMMEDIATE: Trigger ToO observations on all facilities")
                actions.append("Notify GW follow-up coordination")
                actions.append("Obtain NIR spectrum")
                actions.append("Monitor at radio wavelengths")
            elif transient_type == TransientType.GRB:
                actions.append("IMMEDIATE: Swift ToO trigger")
                actions.append("Follow up with large optical telescopes")
            elif transient_type == TransientType.TDE:
                actions.append("Obtain UV spectrum")
                actions.append("Monitor X-ray emission")
            elif transient_type in [TransientType.SN_Ia, TransientType.SN_II]:
                actions.append("Obtain optical spectrum for typing")
                actions.append("Monitor light curve")

        # Medium priority actions
        elif priority > 0.5:
            if confidence < 0.5:
                actions.append("Obtain spectrum for classification")
            actions.append("Monitor light curve evolution")

        # Low priority
        else:
            if transient_type == TransientType.UNKNOWN:
                actions.append("Add to monitoring list")

        return actions

    def get_statistics(self) -> Dict[str, int]:
        """Get processing statistics."""
        return dict(self.stats)


def create_alert_processor(**kwargs) -> StreamingAlertProcessor:
    """
    Factory function to create alert processor.

    Args:
        **kwargs: Arguments to pass to StreamingAlertProcessor

    Returns:
        Configured alert processor
    """
    return StreamingAlertProcessor(**kwargs)


if __name__ == "__main__":
    print("="*70)
    print("Streaming Alert Processor")
    print("="*70)
    print()
    print("Components:")
    print("  - StreamingAlertProcessor: Main processing system")
    print("  - AlertClassifier: Transient classification")
    print("  - AlertPrioritizer: Priority scoring")
    print("  - AlertFeatureExtractor: Feature extraction")
    print()
    print("Supported Alert Sources:")
    for source in AlertSource:
        print(f"  - {source.value.upper()}")
    print()
    print("Transient Types:")
    for t in TransientType:
        print(f"  - {t.value}")
    print("="*70)
