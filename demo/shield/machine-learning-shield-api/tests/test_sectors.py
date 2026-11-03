import unittest
from pathlib import Path

from bridge.source import execute
from api_objects.faro.bridge.output.bridge_output import Read
from bridge.predictor_input import PredictorInput as Request
from shield.predictor import Predictor as Shield
from shield.predictor_input import PredictorInput as Check


DATA = Path(__file__).resolve().parents[3] / "local_data/demo_dataset"


class SectorTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import Mock
        handler = Mock()
        handler.predict.return_value.assistant_tools = [Mock(parsed_arguments={"decision":"supported","reason":"Matches"})]
        self.shield = Shield(DATA, handler)

    def test_same_services_for_hospital_and_worldwide_hotel(self):
        for company, scopes, group, order, expected in [
            ("cedar", ["riverside", "hillview"], "hospital", "highest",
             [("Hillview Hospital", 45), ("Riverside Hospital", 30)]),
            ("meridian", ["madrid", "tokyo", "mexico_city"], "hotel", "lowest",
             [("Tokyo Bay", 70), ("Madrid Central", 80), ("Mexico City Plaza", 90)])]:
            with self.subTest(company=company):
                definition = company + "_measure"
                question = f"Compare all {group}s by {definition}, {order} first in October 2026."
                request = Request(company_id=company, question=question, permitted_scope_ids=scopes, definition_ids=[definition])
                read = Read(source=definition,scope_ids=scopes,group=group,member_ids=[],start="2026-10-01",end_exclusive="2026-11-01",
                    expression=("(df.groupby('asset_id')['wait_minutes'].sum()/df.groupby('asset_id')['visits'].sum())" if company=="cedar" else "(df.groupby('asset_id')['occupied_room_nights'].sum()/df.groupby('asset_id')['available_room_nights'].sum()*100)") + f".sort_values(ascending={order=='lowest'})")
                evidence = execute(DATA, request, read)
                result = self.shield.predict(Check(**request.model_dump(), evidence=evidence))
                self.assertEqual(result.status, "verified", result.reason)
                self.assertEqual([(r["member"], r["value"]) for r in result.facts.rows], expected)
                restricted = request.model_copy(update={"permitted_scope_ids": scopes[:1]})
                with self.assertRaises(PermissionError):
                    execute(DATA, restricted, read)
                blocked = self.shield.predict(Check(**restricted.model_dump(), evidence=evidence))
                self.assertEqual(blocked.status, "withheld")
                self.assertIsNone(blocked.facts)
