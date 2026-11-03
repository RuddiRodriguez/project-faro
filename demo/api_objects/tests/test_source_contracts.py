from unittest import TestCase
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.scout.input.scout_input import ScoutInput
from api_objects.faro.signal.input.signal_input import SignalInput
from api_objects.faro.compass.output.compass_output import CompassOutput


class SourceContracts(TestCase):
    def test_data_question_needs_no_glossary_or_task_list(self):
        request=dict(company_id="new_client",permitted_scope_ids=["site"],question="How many orders?")
        self.assertEqual(BridgeInput(**request).company_id,"new_client")
        self.assertNotIn("definition_ids",BridgeInput.model_fields)
        self.assertNotIn("document_ids",ScoutInput.model_fields)
        self.assertNotIn("supported_tasks",SignalInput.model_fields)
        self.assertIn("sources",CompassOutput.model_fields)
        self.assertNotIn("company_information",CompassOutput.model_fields)
