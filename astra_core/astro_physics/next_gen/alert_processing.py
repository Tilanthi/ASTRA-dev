"""
Time-domain alert stream processing for ASTRO.

Handles real-time transient alert streams from wide-field synoptic surveys
(ZTF: Bellm+ 2019, Graham+ 2019; Vera C. Rubin Observatory / LSST: Ivezić+
2019). Provides facility-specific handlers, a configurable filter pipeline
(quality + real-bogus + novelty cuts), and a follow-up prioritiser.

Alerts are plain dicts with at least: 'ra', 'dec', 'mag', 'magerr', 'rb'
(real-bogus score), 'candidate_id'. Facility handlers normalise the survey's
schema into this common form.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional


@dataclass
class SurveySpec:
    name: str
    fov_deg2: float
    typical_depth_mag: float
    cadence_days: float


class AlertStreamProcessor:
    """Ingest and dispatch a stream of alerts through handlers + a pipeline."""

    def __init__(self, handler: Optional['FacilityAlertHandler'] = None,
                 pipeline: Optional['AlertFilterPipeline'] = None):
        self.handler = handler
        self.pipeline = pipeline

    def process(self, raw_alerts: List[Dict]) -> List[Dict]:
        alerts = raw_alerts
        if self.handler is not None:
            alerts = [self.handler.normalise(a) for a in alerts]
        if self.pipeline is not None:
            alerts = self.pipeline.apply(alerts)
        return alerts


class FacilityAlertHandler:
    """Base handler: normalises a survey's alert schema to the common form."""
    SPEC: SurveySpec = None

    def normalise(self, raw: Dict) -> Dict:
        return dict(raw)


class ZTFAlertHandler(FacilityAlertHandler):
    """Zwicky Transient Facility alert handler (ZTF alerts use 'candid',
    'rb' real-bogus score, 'magpsf')."""
    SPEC = SurveySpec('ZTF', fov_deg2=47.0, typical_depth_mag=20.5, cadence_days=1.0)

    def normalise(self, raw: Dict) -> Dict:
        return {
            'candidate_id': raw.get('candid', raw.get('objectId', '')),
            'ra': raw.get('ra'),
            'dec': raw.get('dec'),
            'mag': raw.get('magpsf', raw.get('mag')),
            'magerr': raw.get('sigmapsf', raw.get('magerr')),
            'rb': raw.get('rb', raw.get('realbogus', 0.5)),
            'survey': 'ZTF',
        }


class RubinAlertHandler(FacilityAlertHandler):
    """Vera C. Rubin Observatory (LSST) alert handler."""
    SPEC = SurveySpec('Rubin', fov_deg2=9.6, typical_depth_mag=24.5, cadence_days=3.0)

    def normalise(self, raw: Dict) -> Dict:
        dia = raw.get('diaSource', raw)
        return {
            'candidate_id': raw.get('alertId', dia.get('diaSourceId', '')),
            'ra': dia.get('ra'),
            'dec': dia.get('dec'),
            'mag': dia.get('psfFlux', raw.get('mag')),
            'magerr': dia.get('psfFluxErr', raw.get('magerr')),
            'rb': raw.get('diaSource', {}).get('snr', raw.get('rb', 0.5)),
            'survey': 'Rubin',
        }


class AlertFilterPipeline:
    """A sequence of filters applied to the alert stream."""

    def __init__(self, filters: List[Callable[[Dict], bool]] = None):
        self.filters = filters or []

    def add(self, filt: Callable[[Dict], bool]) -> 'AlertFilterPipeline':
        self.filters.append(filt)
        return self

    def apply(self, alerts: List[Dict]) -> List[Dict]:
        out = []
        for a in alerts:
            if all(f(a) for f in self.filters):
                out.append(a)
        return out

    # common filters --------------------------------------------------------
    @staticmethod
    def real_bogus_cut(threshold: float = 0.5):
        return lambda a: (a.get('rb') or 0) >= threshold

    @staticmethod
    def significance_cut(min_snr: float = 5.0):
        def f(a):
            m, e = a.get('mag'), a.get('magerr')
            return (m is not None and e is not None and e > 0 and abs(m) / e >= min_snr)
        return f

    @staticmethod
    def novelty_cut(known_positions: Optional[List[tuple]] = None,
                    radius_deg: float = 1.0 / 3600.0):
        """Drop alerts coincident with a known source within radius_deg."""
        known = known_positions or []
        def f(a):
            if not known:
                return True
            ra, dec = a.get('ra'), a.get('dec')
            if ra is None or dec is None:
                return True
            for kra, kdec in known:
                if np.hypot(ra - kra, dec - kdec) <= radius_deg:
                    return False
            return True
        return f


class FollowUpPrioritizer:
    """Rank surviving alerts for spectroscopic / imaging follow-up.

    Score rises for brighter (lower-mag), faster-rising, rare-type candidates.
    """

    # rough relative weights per transient class (higher = rarer/more urgent)
    CLASS_WEIGHTS = {'kilonova': 1.0, 'grb_afterglow': 0.95, 'sn_Ia': 0.6,
                     'sn_cc': 0.65, 'tidal_disruption': 0.9, 'cv': 0.2,
                     'asteroid': 0.05, 'unknown': 0.4}

    def score(self, alert: Dict, transient_class: str = 'unknown',
              rise_rate_mag_per_day: float = 0.0) -> float:
        mag = alert.get('mag', 24.0)
        depth = 25.0
        brightness = max(0.0, 1.0 - (mag / depth))            # 0..1
        rise = 1.0 - np.exp(-max(rise_rate_mag_per_day, 0.0))  # faster rise -> higher
        w = self.CLASS_WEIGHTS.get(transient_class, 0.4)
        return float(w * (0.5 * brightness + 0.3 * rise + 0.2))

    def prioritise(self, alerts: List[Dict],
                   classes: Optional[Dict[str, str]] = None) -> List[Dict]:
        classes = classes or {}
        scored = []
        for a in alerts:
            a = dict(a)
            a['priority'] = self.score(a, classes.get(a.get('candidate_id'), 'unknown'))
            scored.append(a)
        scored.sort(key=lambda x: x['priority'], reverse=True)
        return scored


__all__ = [
    'SurveySpec', 'AlertStreamProcessor', 'FacilityAlertHandler',
    'ZTFAlertHandler', 'RubinAlertHandler', 'AlertFilterPipeline',
    'FollowUpPrioritizer',
]
