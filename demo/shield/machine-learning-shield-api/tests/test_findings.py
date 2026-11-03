from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch
from utils.llms.llm_handler import LLMHandler
from utils.openai_client.exceptions import OpenAiRecoverableError

from api_objects.faro.bridge.output.bridge_output import Finding, Read
from bridge.predictor_input import PredictorInput as Request
from bridge.source import catalogue, execute, snapshot_id
from shield.predictor import Predictor
from shield.predictor_input import PredictorInput

DATA = Path(__file__).resolve().parents[3] / "local_data/demo_dataset"


class FindingsTests(TestCase):
    def test_replay_then_release_only_reviewed_findings(self):
        request = Request(company_id="harbor",permitted_scope_ids=["harbor_north"],
                          definition_ids=["harbor_idle_time_v1"],question="How much idle time?")
        read = Read(source="activity",scope_ids=[],member_ids=[],group="crane",start=None,
                    end_exclusive=None,expression="df['idle_hours'].sum()")
        evidence = execute(DATA,request,read)
        evidence.catalogue_version=snapshot_id(catalogue(DATA,request))
        evidence.findings=[Finding(text="366 hours.",evidence_ids=[1]),Finding(text="It caused a delay.",evidence_ids=[1])]
        model=Mock()
        model.predict.return_value.assistant_tools=[Mock(parsed_arguments={"supported_finding_numbers":[1],"narrower_findings":[],"reason":"No causal evidence."})]
        shield=Predictor(DATA,model)
        response=shield.predict(PredictorInput(**request.model_dump(),evidence=evidence))
        self.assertEqual(response.status,"verified")
        self.assertEqual(response.facts.findings,evidence.findings[:1])
        self.assertTrue(response.reason)
        evidence.rows[0]["value"]=999.0
        self.assertEqual(shield.predict(PredictorInput(**request.model_dump(),evidence=evidence)).status,"withheld")
        self.assertEqual(model.predict.call_count,1)

    def test_search_is_not_the_access_boundary(self):
        request=Request(company_id="harbor",permitted_scope_ids=["harbor_north"],definition_ids=["harbor_idle_time_v1"],question="What is available?")
        cat=catalogue(DATA,request)
        self.assertIn("idle_hours",cat["sources"]["activity"]["fields"])
        self.assertEqual(set(cat["scopes"]),{"harbor_north"})
        self.assertTrue(all(a["scope_id"]=="harbor_north" for a in cat["agreements"]))
        self.assertNotIn("harbor_south",str(cat))


    def test_review_timeout_withholds_after_three_model_calls(self):
        request = Request(company_id="harbor",permitted_scope_ids=["harbor_north"],
                          definition_ids=[],question="Which sources are available?")
        from api_objects.faro.bridge.output.bridge_output import BridgeOutput
        evidence=BridgeOutput(company_id=request.company_id,question=request.question,status="ready",source="catalogue",
            catalogue_version=snapshot_id(catalogue(DATA,request)), findings=[Finding(text="Inventory is available.",evidence_ids=[0])])
        client=Mock()
        client.chat_predict.side_effect=OpenAiRecoverableError()
        with patch("time.sleep"):
            result=Predictor(DATA,LLMHandler(client)).predict(PredictorInput(**request.model_dump(),evidence=evidence))
        self.assertEqual(client.chat_predict.call_count,3)
        self.assertEqual(result.status,"withheld")
        self.assertIsNone(result.facts)
        self.assertIn("three attempts",result.reason)
