"""Check the expanded hospital fixtures through the existing read path."""
import json
import unittest
from tests_support import ConnectedTest
from pathlib import Path
from api_objects.faro.bridge.output.bridge_output import Read
from bridge.reader_input import ReaderInput
from bridge.source import execute

DATA = Path(__file__).resolve().parents[1]/"local_data/demo_dataset"


class HospitalDataTests(ConnectedTest):
    def setUp(self):
        super().setUp()
        self.scopes = next(u["scope_ids"] for u in json.loads((DATA/"users.json").read_text())
                           if u["user_id"]=="hospital_ops")
        self.request = ReaderInput(company_id="cedar",question="Compare hospitals",
            permitted_scope_ids=self.scopes)

    def read(self, source, expression, scopes=None, start="2026-10-01", end="2026-11-01"):
        base=f"df.sort_values('revision').drop_duplicates('record_id', keep='last').query(\"deleted == False and activity_date >= '{start}' and activity_date < '{end}'\")"
        return execute(DATA,self.request,Read(source="cedar/activity",scope_ids=scopes or self.scopes,member_ids=[],
            group="",start=None,end_exclusive=None,expression=expression.replace("df",base)))

    def test_october_waiting_times_include_correction_and_ignore_withdrawn_duplicate(self):
        result=self.read("cedar_measure","df.groupby('asset_id')['wait_minutes'].sum()/df.groupby('asset_id')['visits'].sum()")
        self.assertEqual({r["asset_id"]:r["value"] for r in result.rows},
            {"Riverside Hospital":30,"Hillview Hospital":45,"Lakeside Hospital":25,
             "Westhaven Hospital":38,"Meadow Hospital":20,"Central Hospital":50})
        self.assertTrue(result.record_ids)

    def test_occupancy_and_local_access(self):
        result=self.read("cedar_occupancy",
            "100*df.groupby('asset_id')['occupied_bed_days'].sum()/df.groupby('asset_id')['available_bed_days'].sum()",
            scopes=["riverside"])
        self.assertEqual(result.rows,[{"asset_id":"Riverside Hospital","value":75.0}])
        self.request=self.request.model_copy(update={"permitted_scope_ids":["riverside"]})
        with self.assertRaises(PermissionError):
            self.read("cedar_measure","df['visits'].sum()",scopes=["hillview"])

    def test_missing_day_remains_visible_in_native_records(self):
        result=self.read("activity","df.groupby('asset_id')['activity_date'].nunique()",start="2026-09-01",end="2026-10-01")
        counts={r["asset_id"]:r["value"] for r in result.rows}
        self.assertEqual(counts["Westhaven Hospital"],29)
        self.assertEqual(counts["Riverside Hospital"],30)

    def test_complete_week_is_readable(self):
        result=self.read("cedar_measure","df['visits'].sum()",start="2026-10-19",end="2026-10-26")
        self.assertTrue(result.record_ids)
        self.assertGreater(result.rows[0]["value"],0)


if __name__=="__main__":
    unittest.main()
