import json
import shutil
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from fastapi.testclient import TestClient
from bridge.source import execute
from api_objects.faro.bridge.output.bridge_output import Read
from bridge.predictor_input import PredictorInput
from shield_api.infer import create_app


DATA = Path(__file__).resolve().parents[3] / "local_data/demo_dataset"


class ShieldTests(unittest.TestCase):
    def setUp(self):
        request = PredictorInput(question="Rank crane downtime highest first in North Terminal in October 2026",
            company_id="harbor", permitted_scope_ids=["harbor_north"],definition_ids=["harbor_downtime_v1"])
        read = Read(source="harbor_downtime_v1",scope_ids=["harbor_north"],group="crane",member_ids=[],
            start="2026-10-01",end_exclusive="2026-11-01",
            expression="df.groupby('asset_id')['downtime_hours'].sum().sort_values(ascending=False)")
        self.request = request.model_dump(mode="json")
        self.request["evidence"] = execute(DATA, request, read).model_dump(mode="json")
        self.totals = self.request["evidence"]["rows"]
        self.client = TestClient(create_app(DATA))
        self.addCleanup(self.client.close)

    def verify(self):
        response = self.client.post("/v1/verify", json=self.request)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def withheld(self):
        result = self.verify()
        self.assertEqual(result["status"], "withheld", result)
        self.assertIsNone(result["facts"])
        self.assertTrue(result["reason"])

    def test_valid_tie(self):
        result = self.verify()
        self.assertEqual(result["status"], "verified", result)
        self.assertEqual([c["value"] for c in result["facts"]["rows"]], [62,62])

    def test_source_corrected_after_bridge_read_it(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("activity", "manifest", "companies", "documents", "scopes", "coverage", "assets"):
                shutil.copy(DATA / f"{name}.json", root)
            path = root / "activity.json"
            rows = json.loads(path.read_text())
            record = next(r for r in rows if r["record_id"] == self.request["evidence"]["record_ids"][0])
            rows.append({**record, "revision": record["revision"] + 1, "downtime_hours": 5})
            path.write_text(json.dumps(rows))
            with TestClient(create_app(root)) as client:
                result = client.post("/v1/verify", json=self.request).json()
                self.assertEqual(result["status"], "withheld")
                self.assertIsNone(result["facts"])
                self.totals[0]["value"] = 65
                self.assertEqual(client.post("/v1/verify", json=self.request).json()["status"], "withheld")
                # Updating a total alone does not refresh the attached source records.
                from bridge.source import execute
                from bridge.predictor_input import PredictorInput
                from api_objects.faro.bridge.output.bridge_output import Read
                self.request["evidence"] = execute(root, PredictorInput(
                    company_id=self.request["company_id"],question=self.request["question"],
                    permitted_scope_ids=self.request["permitted_scope_ids"],
                    definition_ids=self.request["definition_ids"]),
                    Read.model_validate(self.request["evidence"]["read"])).model_dump(mode="json")
                self.assertEqual(client.post("/v1/verify", json=self.request).json()["status"], "verified")

    def test_wrong_total(self):
        self.totals[0]["value"] = 65
        self.withheld()

    def test_false_winner(self):
        self.totals[1]["value"] = 63
        self.withheld()

    def test_omitted_crane(self):
        self.totals.pop()
        self.withheld()

    def test_missing_source(self):
        self.request["evidence"]["record_ids"].pop()
        self.withheld()

    def test_access_changed(self):
        self.request["permitted_scope_ids"] = []
        self.withheld()

    def test_wrong_month(self):
        self.request["evidence"]["read"]["start"] = "2026-09-01"
        self.withheld()

    def test_bridge_stopped(self):
        self.request["evidence"]["status"] = "incomplete"
        self.withheld()
