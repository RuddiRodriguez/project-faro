from unittest.mock import Mock
from urllib.parse import unquote, urlparse
import json
from tests_support import ConnectedTest
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.bridge.output.bridge_output import Read
from bridge.reader import Reader
from bridge.source import catalogue, execute


class BridgeTests(ConnectedTest):
    def setUp(self):
        super().setUp()
        self.request=BridgeInput(question="How many cranes?",company_id="harbor",permitted_scope_ids=["harbor_north"])
        self.read=Read(source="harbor/assets",scope_ids=[],member_ids=[],group="",start=None,end_exclusive=None,expression="len(df)")

    def test_no_prepared_information_is_needed(self):
        cat=catalogue(self.root,self.request)
        self.assertEqual(set(cat),{"connected","reference_date","scopes","data_version"})
        result=execute(self.root,self.request,self.read)
        self.assertEqual(result.rows,[{"value":2}])
        self.assertTrue(result.record_ids)

    def test_export_contains_only_permitted_rows(self):
        result=execute(self.root,self.request,self.read)
        doc=result.source_evidence[0]["document"]
        from pathlib import Path
        data=json.loads(Path(unquote(urlparse(doc["uri"]).path)).read_text())
        self.assertTrue(all(row["scope_id"]=="harbor_north" for row in data["assets"]))

    def test_access_cannot_be_expanded_by_model(self):
        for change in ({"source":"pacific/assets"},{"scope_ids":["harbor_south"]}):
            with self.assertRaises(PermissionError):
                execute(self.root,self.request,self.read.model_copy(update=change))

    def test_missing_structured_response_releases_no_numbers(self):
        model=Mock();model.predict.return_value.assistant_tools=[Mock(parsed_arguments=None)]
        result=Reader(self.root,model).read(self.request)
        self.assertEqual(result.status,"incomplete")
        self.assertFalse(result.findings)

    def test_writes_fabrication_and_invalid_numbers_fail(self):
        for expression in ("__import__('os')","42","df.to_csv('out')","len(df)/0"):
            with self.subTest(expression=expression),self.assertRaises(ValueError):
                execute(self.root,self.request,self.read.model_copy(update={"expression":expression}))

    def test_last_permitted_read_can_be_followed_by_final_answer(self):
        model=Mock()
        read=dict(initial_analysis="Read connected rows.",reasoning="Count the supplied records.",
                  action="read",read=self.read.model_dump(mode="json"),findings=[],reason=None)
        answer=dict(initial_analysis="The count is two.",reasoning="The executed read supports it.",
                    action="answer",read=None,findings=[dict(text="Two cranes.",evidence_ids=[6])],reason=None)
        model.predict.side_effect=[Mock(is_success=True,assistant_tools=[Mock(parsed_arguments=value)])
                                   for value in [read]*6+[answer]]
        result=Reader(self.root,model).read(self.request)
        self.assertEqual(result.status,"ready")
        self.assertEqual(len(result.supporting),5)
        self.assertEqual(model.predict.call_count,7)

    def test_final_decision_cannot_start_a_seventh_read(self):
        from unittest.mock import patch
        read=dict(initial_analysis="Read rows.",reasoning="Read records.",action="read",
                  read=self.read.model_dump(mode="json"),findings=[],reason=None)
        model=Mock();model.predict.return_value=Mock(is_success=True,assistant_tools=[Mock(parsed_arguments=read)])
        with patch("bridge.reader.execute",wraps=execute) as calls:
            result=Reader(self.root,model).read(self.request)
        self.assertEqual(result.status,"incomplete")
        self.assertEqual(calls.call_count,6)
