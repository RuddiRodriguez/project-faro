import json
from unittest.mock import Mock
from tests_support import ConnectedTest
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.bridge.output.bridge_output import Read, Finding
from api_objects.faro.shield.input.shield_input import ShieldInput
from bridge.source import execute,catalogue,snapshot_id
from shield.verifier import Verifier


class ShieldTests(ConnectedTest):
    def setUp(self):
        super().setUp()
        self.request=BridgeInput(question="How many cranes?",company_id="harbor",permitted_scope_ids=["harbor_north"])
        read=Read(source="harbor/assets",scope_ids=[],member_ids=[],group="",start=None,end_exclusive=None,expression="len(df)")
        self.evidence=execute(self.root,self.request,read)
        self.evidence.findings=[Finding(text="There are two cranes.",evidence_ids=[1])]
        self.evidence.catalogue_version=snapshot_id(catalogue(self.root,self.request))
        self.model=Mock();self.model.predict.return_value.assistant_tools=[Mock(parsed_arguments=dict(
            initial_analysis="Two permitted rows.",reasoning="The count matches.",supported_finding_numbers=[1],reason="Supported."))]
        self.shield=Verifier(self.root,self.model)

    def verify(self,request=None,evidence=None):
        return self.shield.verify(ShieldInput(**(request or self.request).model_dump(),evidence=evidence or self.evidence))

    def test_replay_then_review(self):
        self.assertEqual(self.verify().status,"verified")
        self.model.predict.assert_called_once()

    def test_tampered_number_stops_before_model(self):
        self.evidence.rows[0]["value"]=99
        self.assertEqual(self.verify().status,"withheld")
        self.model.predict.assert_not_called()

    def test_source_correction_invalidates_evidence(self):
        file=self.root/"harbor.json";data=json.loads(file.read_text());data["assets"].pop();file.write_text(json.dumps(data))
        self.assertEqual(self.verify().status,"withheld")
        self.model.predict.assert_not_called()

    def test_company_question_and_scope_changes_are_rejected(self):
        for change in ({"company_id":"retail"},{"question":"A different question"},{"permitted_scope_ids":[]}):
            self.assertEqual(self.verify(self.request.model_copy(update=change)).status,"withheld")
        self.model.predict.assert_not_called()

    def test_unknown_evidence_reference_is_rejected(self):
        self.evidence.findings[0].evidence_ids=[99]
        self.assertEqual(self.verify().status,"withheld")
        self.model.predict.assert_not_called()

    def test_model_can_withhold_unsupported_claim(self):
        self.model.predict.return_value.assistant_tools[0].parsed_arguments.update(supported_finding_numbers=[],reason="No cause is recorded.")
        self.assertEqual(self.verify().status,"withheld")

    def test_partial_answer_is_returned_unchanged_after_one_review(self):
        supported=Finding(text="The recorded count is two; other kinds are not established.",evidence_ids=[1])
        self.evidence.findings=[supported,Finding(text="This proves overall performance is best.",evidence_ids=[1])]
        result=self.verify()
        self.assertEqual(result.status,"verified")
        self.assertEqual(result.facts.findings,[supported])
        self.model.predict.assert_called_once()

    def test_rejection_does_not_generate_or_review_replacements(self):
        self.model.predict.return_value.assistant_tools[0].parsed_arguments.update(
            supported_finding_numbers=[],reason="The broader category is not established by the records.")
        result=self.verify()
        self.assertEqual(result.status,"withheld")
        self.assertIsNone(result.facts)
        self.model.predict.assert_called_once()
