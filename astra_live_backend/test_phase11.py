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
Tests for Phase 11.1 (Provenance Tracking) and Phase 11.2 (Export Formats).
"""
import os
import sys
import json
import time
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astra_live_backend.provenance import ProvenanceTracker, ProvenanceRecord
from astra_live_backend.exporter import ASTRAExporter


class TestProvenanceRecord(unittest.TestCase):
    """Test ProvenanceRecord dataclass."""

    def test_create_record(self):
        rec = ProvenanceRecord(
            discovery_id="D-001",
            data_source="NASA Exoplanet Archive",
            data_query="select * from ps",
            test_method="pearsonr",
            test_inputs={"n": 100},
            code_version="abc1234",
        )
        self.assertEqual(rec.discovery_id, "D-001")
        self.assertIsNotNone(rec.id)
        self.assertIsNotNone(rec.timestamp)
        self.assertIsNone(rec.random_seed)
        self.assertIsNone(rec.parent_hypothesis_id)

    def test_auto_uuid(self):
        r1 = ProvenanceRecord("D-1", "src", "q", "m", {}, "v")
        r2 = ProvenanceRecord("D-1", "src", "q", "m", {}, "v")
        self.assertNotEqual(r1.id, r2.id)


class TestProvenanceTracker(unittest.TestCase):
    """Test ProvenanceTracker SQLite operations."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.tracker = ProvenanceTracker(db_path=self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_record_and_retrieve(self):
        rec = self.tracker.record(
            discovery_id="D-001",
            data_source="SDSS DR17",
            data_query="SELECT ugriz FROM specObj",
            test_method="chi_squared",
            test_inputs={"bins": 50, "alpha": 0.05},
            code_version="test123",
        )
        self.assertEqual(rec.discovery_id, "D-001")
        self.assertEqual(rec.data_source, "SDSS DR17")
        self.assertIn("python", rec.environment)

        # Retrieve
        records = self.tracker.get_by_discovery("D-001")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].test_method, "chi_squared")
        self.assertEqual(records[0].test_inputs["bins"], 50)

    def test_multiple_records_per_discovery(self):
        self.tracker.record("D-002", "Gaia DR3", "q1", "pearsonr", {"n": 100}, "v1")
        self.tracker.record("D-002", "Gaia DR3", "q2", "ks_test", {"n": 200}, "v1")
        records = self.tracker.get_by_discovery("D-002")
        self.assertEqual(len(records), 2)

    def test_get_lineage(self):
        # Create a chain: D-003 -> parent H001
        self.tracker.record("D-003", "src", "q", "method", {}, "v", parent_hypothesis_id="H001")
        self.tracker.record("H001", "src2", "q2", "method2", {}, "v")
        lineage = self.tracker.get_lineage("D-003")
        self.assertEqual(len(lineage), 2)
        # Sorted by timestamp
        self.assertTrue(lineage[0].timestamp <= lineage[1].timestamp)

    def test_empty_discovery(self):
        records = self.tracker.get_by_discovery("NONEXISTENT")
        self.assertEqual(records, [])

    def test_get_all(self):
        self.tracker.record("D-010", "src", "q", "m", {}, "v")
        self.tracker.record("D-011", "src", "q", "m", {}, "v")
        all_recs = self.tracker.get_all()
        self.assertEqual(len(all_recs), 2)
        # Returns dicts
        self.assertIsInstance(all_recs[0], dict)

    def test_count(self):
        self.assertEqual(self.tracker.count(), 0)
        self.tracker.record("D-020", "src", "q", "m", {}, "v")
        self.assertEqual(self.tracker.count(), 1)

    def test_environment_capture(self):
        env = ProvenanceTracker._get_environment()
        self.assertIn("python", env)
        self.assertIn("numpy", env)
        self.assertIn("scipy", env)

    def test_json_serialization_roundtrip(self):
        """Test that dict fields survive SQLite storage."""
        rec = self.tracker.record(
            "D-030", "src", "q", "m",
            test_inputs={"nested": {"key": [1, 2, 3]}},
            code_version="v1",
        )
        retrieved = self.tracker.get_by_discovery("D-030")
        self.assertEqual(retrieved[0].test_inputs["nested"]["key"], [1, 2, 3])


class TestASTRAExporter(unittest.TestCase):
    """Test ASTRAExporter export methods."""

    def setUp(self):
        """Create a mock engine with discoveries and hypotheses."""
        from astra_live_backend.hypotheses import Hypothesis, Phase

        self.engine = MagicMock()

        # Mock hypothesis store
        h1 = Hypothesis(
            id="H001", name="Test Hypothesis", domain="Astrophysics",
            description="A test hypothesis about stellar evolution",
            confidence=0.85, phase=Phase.VALIDATED,
        )
        h1.test_results = [
            {"test_name": "pearsonr", "statistic": 0.92, "p_value": 0.001, "details": "strong correlation"},
            {"test_name": "ks_test", "statistic": 0.15, "p_value": 0.23, "details": "consistent distribution"},
        ]
        h1.data_points_used = 500

        h2 = Hypothesis(
            id="H002", name="Galaxy Colors", domain="Astrophysics",
            description="Galaxy color bimodality",
            confidence=0.99, phase=Phase.VALIDATED,
        )
        h2.test_results = []
        h2.data_points_used = 1000

        self.engine.store.all.return_value = [h1, h2]
        self.engine.store.get.side_effect = lambda id: h1 if id == "H001" else (h2 if id == "H002" else None)

        # Mock discovery memory
        from astra_live_backend.discovery_memory import DiscoveryRecord
        d1 = DiscoveryRecord(
            id="disc-001", timestamp=time.time(), cycle=5,
            hypothesis_id="H001", domain="Astrophysics",
            finding_type="correlation", variables=["mass", "luminosity"],
            statistic=0.92, p_value=0.001,
            description="Strong mass-luminosity correlation",
            data_source="exoplanets", strength=0.9,
        )
        self.engine.discovery_memory.discoveries = [d1]

        # Mock provenance tracker
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        self.tmp_db = tmp.name
        self.prov = ProvenanceTracker(db_path=self.tmp_db)
        self.prov.record("disc-001", "NASA Exoplanet Archive", "query", "pearsonr", {"n": 500}, "abc123")
        self.engine.provenance_tracker = self.prov

        # Mock get_state
        self.engine.get_state.return_value = {"cycle": 10, "phase": "ORIENT"}

        self.exporter = ASTRAExporter(self.engine)

    def tearDown(self):
        os.unlink(self.tmp_db)

    def test_export_discoveries_json(self):
        result = self.exporter.export_discoveries_json()
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        # Check provenance is attached
        disc = data[0]
        self.assertIn("provenance", disc)

    def test_export_discoveries_json_filter(self):
        result = self.exporter.export_discoveries_json(filter_domain="Astro")
        data = json.loads(result)
        self.assertGreaterEqual(len(data), 1)

        result2 = self.exporter.export_discoveries_json(filter_domain="Economics")
        data2 = json.loads(result2)
        self.assertEqual(len(data2), 0)

    def test_export_discoveries_csv(self):
        csv_text = self.exporter.export_discoveries_csv()
        lines = csv_text.strip().split("\n")
        self.assertGreaterEqual(len(lines), 2)  # header + at least 1 row
        header = lines[0]
        self.assertIn("id", header)
        self.assertIn("p_value", header)

    def test_export_hypothesis_latex(self):
        latex = self.exporter.export_hypothesis_latex("H001")
        self.assertIsNotNone(latex)
        self.assertIn("\\subsection", latex)
        self.assertIn("Test Hypothesis", latex)
        self.assertIn("pearsonr", latex)

    def test_export_hypothesis_latex_not_found(self):
        latex = self.exporter.export_hypothesis_latex("NONEXISTENT")
        self.assertIsNone(latex)

    def test_export_full_report(self):
        result = self.exporter.export_full_report_json()
        data = json.loads(result)
        self.assertIn("hypotheses", data)
        self.assertIn("discoveries", data)
        self.assertIn("provenance", data)
        self.assertIn("engine_state", data)
        self.assertIn("export_timestamp", data)
        self.assertIn("version", data)

    def test_export_full_report_has_hypotheses(self):
        result = self.exporter.export_full_report_json()
        data = json.loads(result)
        self.assertEqual(len(data["hypotheses"]), 2)
        # Phase should be string, not enum
        for h in data["hypotheses"]:
            self.assertIsInstance(h["phase"], str)


if __name__ == "__main__":
    unittest.main()
