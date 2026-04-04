"""
Alert Processing Module

Real-time transient alert stream handling for ZTF, Rubin/LSST,
and other time-domain surveys.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings
from datetime import datetime
import json


class AlertType(Enum):
    """Types of transient alerts"""
    ZTF = "ztf"
    RUBIN = "rubin"
    TESS = "tess"
    FERMI = "fermi"
    SWIFT = "swift"
    GENERIC = "generic"


class AlertPriority(Enum):
    """Alert follow-up priority levels"""
    CRITICAL = 5  # Immediate follow-up required
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    ROUTINE = 1


@dataclass
class Alert:
    """Base alert structure"""
    alert_id: str
    timestamp: datetime
    ra: float  # degrees
    dec: float  # degrees
    magnitude: float
    mag_error: float
    filter_band: str
    alert_type: AlertType
    raw_data: Dict[str, Any] = field(default_factory=dict)
    classification: str = "unknown"
    priority: AlertPriority = AlertPriority.ROUTINE


@dataclass
class LightCurvePoint:
    """Single photometric measurement"""
    mjd: float
    mag: float
    mag_err: float
    band: str
    flux: float = None
    flux_err: float = None
    is_detection: bool = True


@dataclass
class ProcessedAlert:
    """Processed alert with derived properties"""
    alert: Alert
    light_curve: List[LightCurvePoint]
    cross_matches: Dict[str, Any]
    classification: str
    classification_score: float
    priority_score: float
    follow_up_recommended: bool
    notes: List[str] = field(default_factory=list)


# =============================================================================
# ALERT STREAM PROCESSOR
# =============================================================================

class AlertStreamProcessor:
    """
    Base class for processing transient alert streams.

    Handles connection, filtering, and dispatch to handlers.
    """

    def __init__(self, filters: List[Callable] = None):
        """
        Initialize stream processor.

        Args:
            filters: List of filter functions
        """
        self.filters = filters or []
        self.handlers: Dict[AlertType, 'AlertHandler'] = {}
        self.processed_count = 0
        self.passed_count = 0
        self.alert_buffer: List[Alert] = []
        self.max_buffer_size = 10000

    def register_handler(self, alert_type: AlertType, handler: 'AlertHandler'):
        """
        Register a handler for specific alert type.

        Args:
            alert_type: Type of alerts to handle
            handler: Handler instance
        """
        self.handlers[alert_type] = handler

    def add_filter(self, filter_func: Callable[[Alert], bool]):
        """
        Add a filter function.

        Args:
            filter_func: Function returning True for alerts to keep
        """
        self.filters.append(filter_func)

    def process_alert(self, alert_data: Dict[str, Any],
                      alert_type: AlertType) -> Optional[ProcessedAlert]:
        """
        Process a single alert packet.

        Args:
            alert_data: Raw alert data
            alert_type: Type of alert

        Returns:
            ProcessedAlert if passes filters, None otherwise
        """
        self.processed_count += 1

        # Get appropriate handler
        handler = self.handlers.get(alert_type)
        if handler is None:
            handler = self.handlers.get(AlertType.GENERIC)

        if handler is None:
            warnings.warn(f"No handler for alert type: {alert_type}")
            return None

        # Parse alert
        alert = handler.parse_alert(alert_data)

        # Apply filters
        for filt in self.filters:
            if not filt(alert):
                return None

        self.passed_count += 1

        # Process with handler
        processed = handler.process(alert)

        # Buffer for batch operations
        self._add_to_buffer(processed.alert)

        return processed

    def _add_to_buffer(self, alert: Alert):
        """Add alert to buffer, maintaining max size"""
        self.alert_buffer.append(alert)
        if len(self.alert_buffer) > self.max_buffer_size:
            self.alert_buffer = self.alert_buffer[-self.max_buffer_size:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'processed': self.processed_count,
            'passed_filters': self.passed_count,
            'pass_rate': self.passed_count / max(self.processed_count, 1),
            'buffer_size': len(self.alert_buffer),
        }


# =============================================================================
# ALERT HANDLERS
# =============================================================================

class AlertHandler(ABC):
    """Base class for alert handlers"""

    @abstractmethod
    def parse_alert(self, data: Dict[str, Any]) -> Alert:
        """Parse raw alert data into Alert object"""
        pass

    @abstractmethod
    def process(self, alert: Alert) -> ProcessedAlert:
        """Process alert and return enriched data"""
        pass


class ZTFAlertHandler(AlertHandler):
    """
    Handler for Zwicky Transient Facility alerts.

    Parses ZTF alert packets and extracts relevant information.
    """

    def __init__(self):
        """Initialize ZTF handler"""
        self.band_map = {1: 'g', 2: 'r', 3: 'i'}

    def parse_alert(self, data: Dict[str, Any]) -> Alert:
        """
        Parse ZTF alert packet.

        Args:
            data: ZTF alert data (avro decoded)

        Returns:
            Alert object
        """
        candidate = data.get('candidate', data)

        alert = Alert(
            alert_id=str(data.get('candid', data.get('objectId', 'unknown'))),
            timestamp=datetime.now(),  # Would parse jd
            ra=candidate.get('ra', 0.0),
            dec=candidate.get('dec', 0.0),
            magnitude=candidate.get('magpsf', 99.0),
            mag_error=candidate.get('sigmapsf', 0.1),
            filter_band=self.band_map.get(candidate.get('fid', 1), 'r'),
            alert_type=AlertType.ZTF,
            raw_data=data
        )

        return alert

    def process(self, alert: Alert) -> ProcessedAlert:
        """
        Process ZTF alert.

        Args:
            alert: Parsed alert

        Returns:
            Processed alert with light curve and classification
        """
        # Extract light curve from previous detections
        light_curve = self._extract_light_curve(alert.raw_data)

        # Cross-match
        cross_matches = self._cross_match(alert.ra, alert.dec)

        # Classify
        classification, score = self._classify(alert, light_curve, cross_matches)

        # Priority
        priority_score = self._calculate_priority(alert, classification, score)

        return ProcessedAlert(
            alert=alert,
            light_curve=light_curve,
            cross_matches=cross_matches,
            classification=classification,
            classification_score=score,
            priority_score=priority_score,
            follow_up_recommended=priority_score > 0.7,
            notes=[]
        )

    def _extract_light_curve(self, data: Dict) -> List[LightCurvePoint]:
        """Extract light curve from alert history"""
        points = []

        # Current detection
        cand = data.get('candidate', {})
        if 'jd' in cand:
            points.append(LightCurvePoint(
                mjd=cand['jd'] - 2400000.5,
                mag=cand.get('magpsf', 99),
                mag_err=cand.get('sigmapsf', 0.1),
                band=self.band_map.get(cand.get('fid', 1), 'r')
            ))

        # Previous detections
        for prv in data.get('prv_candidates', []):
            if prv.get('magpsf') is not None:
                points.append(LightCurvePoint(
                    mjd=prv['jd'] - 2400000.5,
                    mag=prv['magpsf'],
                    mag_err=prv.get('sigmapsf', 0.1),
                    band=self.band_map.get(prv.get('fid', 1), 'r')
                ))

        # Sort by time
        points.sort(key=lambda x: x.mjd)
        return points

    def _cross_match(self, ra: float, dec: float) -> Dict[str, Any]:
        """Cross-match with catalogs"""
        # Placeholder - would query Gaia, PS1, etc.
        return {
            'gaia': None,
            'ps1': None,
            'wise': None,
            'known_transient': False
        }

    def _classify(self, alert: Alert, lc: List[LightCurvePoint],
                  xmatch: Dict) -> Tuple[str, float]:
        """Simple classification based on alert properties"""
        # Real/bogus score from ZTF
        rb_score = alert.raw_data.get('candidate', {}).get('rb', 0.5)

        if rb_score < 0.3:
            return 'bogus', rb_score

        # Check if variable star from cross-match
        if xmatch.get('known_transient'):
            return 'known_transient', 0.9

        # Light curve analysis
        if len(lc) >= 3:
            mags = [p.mag for p in lc]
            amplitude = max(mags) - min(mags)

            if amplitude > 2:
                return 'high_amplitude', 0.7
            elif amplitude > 0.5:
                return 'variable', 0.6

        # Default: new transient candidate
        return 'new_transient', rb_score

    def _calculate_priority(self, alert: Alert, classification: str,
                            score: float) -> float:
        """Calculate follow-up priority score"""
        priority = 0.5 * score

        # Bright transients get priority
        if alert.magnitude < 17:
            priority += 0.2
        elif alert.magnitude < 19:
            priority += 0.1

        # Classification-based boost
        if classification in ['new_transient', 'high_amplitude']:
            priority += 0.2

        return min(priority, 1.0)


class RubinAlertHandler(AlertHandler):
    """
    Handler for Rubin Observatory (LSST) alerts.

    Handles the expected LSST alert format.
    """

    def __init__(self):
        """Initialize Rubin handler"""
        pass

    def parse_alert(self, data: Dict[str, Any]) -> Alert:
        """
        Parse Rubin/LSST alert packet.

        Args:
            data: LSST alert data

        Returns:
            Alert object
        """
        # LSST alert schema (anticipated)
        alert = Alert(
            alert_id=str(data.get('diaSourceId', 'unknown')),
            timestamp=datetime.now(),
            ra=data.get('ra', 0.0),
            dec=data.get('decl', data.get('dec', 0.0)),
            magnitude=data.get('psFlux', 99.0),  # Would convert from flux
            mag_error=data.get('psFluxErr', 0.1),
            filter_band=data.get('filterName', 'r'),
            alert_type=AlertType.RUBIN,
            raw_data=data
        )

        return alert

    def process(self, alert: Alert) -> ProcessedAlert:
        """Process Rubin alert"""
        # Similar to ZTF but with LSST-specific handling

        light_curve = self._extract_light_curve(alert.raw_data)
        cross_matches = {}
        classification = 'unknown'
        score = 0.5

        return ProcessedAlert(
            alert=alert,
            light_curve=light_curve,
            cross_matches=cross_matches,
            classification=classification,
            classification_score=score,
            priority_score=0.5,
            follow_up_recommended=False
        )

    def _extract_light_curve(self, data: Dict) -> List[LightCurvePoint]:
        """Extract light curve from LSST history"""
        points = []

        # Previous DIASources
        for src in data.get('prvDiaSources', []):
            points.append(LightCurvePoint(
                mjd=src.get('midPointTai', 0),
                mag=self._flux_to_mag(src.get('psFlux', 1e-10)),
                mag_err=0.1,
                band=src.get('filterName', 'r')
            ))

        return points

    def _flux_to_mag(self, flux: float) -> float:
        """Convert flux to AB magnitude"""
        if flux <= 0:
            return 99.0
        return -2.5 * np.log10(flux) + 31.4  # Approximate LSST zero-point


# =============================================================================
# ALERT FILTER PIPELINE
# =============================================================================

class AlertFilterPipeline:
    """
    Configurable pipeline of filters for alert streams.

    Filters are applied in sequence with short-circuit evaluation.
    """

    def __init__(self):
        """Initialize filter pipeline"""
        self.filters: List[Tuple[str, Callable]] = []
        self.filter_stats: Dict[str, Dict[str, int]] = {}

    def add_filter(self, name: str, filter_func: Callable[[Alert], bool]):
        """
        Add a named filter to the pipeline.

        Args:
            name: Filter name for statistics
            filter_func: Filter function
        """
        self.filters.append((name, filter_func))
        self.filter_stats[name] = {'passed': 0, 'failed': 0}

    def apply(self, alert: Alert) -> Tuple[bool, str]:
        """
        Apply all filters to alert.

        Args:
            alert: Alert to filter
