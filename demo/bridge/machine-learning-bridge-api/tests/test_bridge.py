import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bridge.source import execute
from api_objects.faro.bridge.output.bridge_output import Read
from bridge.predictor_input import PredictorInput

DATA = Path(__file__).resolve().parents[3] / "local_data/demo_dataset"


class BridgeTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in ("activity", "manifest", "companies", "documents", "scopes", "coverage", "assets"):
            shutil.copy(DATA / f"{name}.json", self.root)
        self.request = PredictorInput(question="Compare crane downtime",company_id="harbor",
            permitted_scope_ids=["harbor_north"], definition_ids=["harbor_downtime_v1"])
        self.read = Read(source="harbor_downtime_v1", scope_ids=["harbor_north"], group="crane", member_ids=[],
            start="2026-10-01", end_exclusive="2026-11-01",
            expression="df.groupby('asset_id')['downtime_hours'].sum().sort_values(ascending=False)")

    def test_missing_structured_response_releases_no_numbers(self):
        from unittest.mock import Mock
        from bridge.predictor import Predictor
        model = Mock()
        model.predict.return_value.assistant_tools = [Mock(parsed_arguments=None)]
        result = Predictor(self.root, model).predict(self.request)
        self.assertEqual(result.status, "incomplete")
        self.assertFalse(result.findings)
        model.predict.assert_called_once()

    def run_request(self, **changes):
        return execute(self.root, self.request.model_copy(update=changes), self.read)

    def change_rows(self, change):
        p = self.root / "activity.json"
        rows = json.loads(p.read_text())
        row = next(r for r in rows if r["record_id"] == "harbor_north_c01_2026-10-01")
        change(row, rows)
        p.write_text(json.dumps(rows))

    def test_json_attachment_contains_only_the_selected_records(self):
        from urllib.parse import urlparse, unquote
        result=self.run_request()
        document=result.source_evidence[0]["document"]
        exported=json.loads(Path(unquote(urlparse(document["uri"]).path)).read_text())
        self.assertEqual(exported["record_ids"],result.record_ids)
        self.assertTrue(all(row["scope_id"]=="harbor_north" for row in exported["records"]))
        self.assertEqual(len(exported["records"]),62)

    def test_base_tie_and_sources(self):
        result = self.run_request()
        self.assertEqual(result.status, "ready", result)
        self.assertEqual(result.rows, [{"member":"harbor_north_c01","value":62},{"member":"harbor_north_c02","value":62}])
        self.assertEqual(len(result.record_ids),62)

    def test_correction_changes_order_without_counting_both_revisions(self):
        self.change_rows(lambda r, rows: rows.append({**r, "revision":2, "downtime_hours":5}))
        self.assertEqual([c["value"] for c in self.run_request().rows], [65,62])

    def test_missing_value_withholds_both_cranes(self):
        self.change_rows(lambda r, rows: r.pop("downtime_hours"))
        with self.assertRaisesRegex(ValueError, "downtime_hours"):
            self.run_request()

    def test_deleted_day_is_not_zero(self):
        self.change_rows(lambda r, rows: rows.append({**r, "revision":2, "deleted":True}))
        with self.assertRaisesRegex(ValueError, "Incomplete daily records"):
            self.run_request()

    def test_no_permitted_terminal_or_no_approved_definition(self):
        with self.assertRaises(PermissionError):
            self.run_request(permitted_scope_ids=["pacific_north"])
        with self.assertRaises(ValueError):
            self.run_request(definition_ids=["pacific_downtime_v1"])

    def test_unmapped_definition_version_stops_before_reading_hours(self):
        p = self.root / "documents.json"
        docs = json.loads(p.read_text())
        next(d for d in docs if d["document_id"] == "harbor_downtime_v1")["version"] = "v2"
        p.write_text(json.dumps(docs))
        with self.assertRaises(ValueError):
            self.run_request()

    def test_lowest_first(self):
        self.change_rows(lambda r, rows: r.update(downtime_hours=0))
        self.read.expression = self.read.expression.replace("False", "True")
        self.assertEqual([c["value"] for c in self.run_request().rows], [60, 62])

    def test_zero_denominator_has_no_rank(self):
        path = self.root / "activity.json"
        rows = json.loads(path.read_text())
        for row in rows:
            if row["company_id"] == "retail" and row["asset_id"] == "East":
                row["sold"] = 0
        path.write_text(json.dumps(rows))
        self.request = PredictorInput(question="Compare returns", company_id="retail",
            permitted_scope_ids=["retail_region"], definition_ids=["retail_rate"])
        self.read = self.read.model_copy(update=dict(source="retail_rate",scope_ids=["retail_region"],group="store", expression="(df.groupby('asset_id')['returned'].sum()/df.groupby('asset_id')['sold'].sum()*100).sort_values(ascending=False)"))
        with self.assertRaisesRegex(ValueError,"No verified value"):
            self.run_request()

    def test_writes_or_fabricated_values_cannot_run(self):
        for expression in ("__import__('os')", "42", "df.to_csv('out')"):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                self.read.expression = expression
                self.run_request()

    def test_zero_is_valid(self):
        self.change_rows(lambda r, rows: r.update(downtime_hours=0))
        self.assertEqual([c["value"] for c in self.run_request().rows], [62,60])
