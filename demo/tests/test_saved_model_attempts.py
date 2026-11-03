import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

import httpx2
import openai
from fastapi.testclient import TestClient

from api_objects.faro.gate.output.gate_output import GateOutput
from compass.data_collection import DataCollection, now
from compass.orchestrator_input import OrchestratorInput
from signal_api.infer import app
from utils.openai_client.conversation.assistant_message import AssistantMessage
from utils.openai_client.openai_client import OpenAiClient
from utils.openai_client.outputs.predict_output import PredictOutput


class SavedAttemptsTests(TestCase):
    def test_actual_signal_endpoint_records_recovery_and_exhaustion(self):
        with TemporaryDirectory() as root, patch.dict(os.environ,FARO_COLLECTION_PATH=root), patch("time.sleep"):
            store=DataCollection(root)
            access=GateOutput(user_id="maria",company_id="harbor",permitted_scope_ids=["north"],permission_version="v1")
            question="Which location had the largest total?"
            for exhaust, expected in [(False,["timeout","success"]), (True,["timeout"]*3)]:
                with store.conversation(OrchestratorInput(user_id="maria", question=question),access) as doc:
                    turn_id=str(uuid4())
                    doc["turns"].append(dict(_id=turn_id,number=1,message=question,language=None,
                        created_at=now().isoformat(),status="started",cache=[],model_attempts_tracked=True))
                    store.save_conversation(doc)
                    def decide(conversation, timeout):
                        if exhaust or provider.call_count==1:
                            raise openai.APITimeoutError(request=httpx2.Request("POST","https://example.invalid"))
                        answers=[dict(name=q["name"],type="choice",choice=("Continue" if q["name"]=="next_action" else q["choices"][0]["value"])) for q in conversation.questions]
                        return PredictOutput(conversation,AssistantMessage(content=json.dumps(answers)),None,None,None,
                                             decisions_response={"answers":answers})
                    with patch.object(OpenAiClient,"_decisions_api_predict",side_effect=decide) as provider:
                        response=TestClient(app).post("/v1/classify",headers={"x-faro-turn":turn_id,"x-faro-company":"harbor"},
                            json=dict(question=question,matches=[],permitted_scopes=["north"]))
                        self.assertEqual(response.status_code,502 if exhaust else 200)
                        self.assertEqual(provider.call_count,len(expected))
                    row=store.read_conversation("harbor",doc["_id"])["turns"][0]
                    self.assertEqual(row["model_attempts"],{"Signal":{"attempts":len(expected),"calls":[expected]}})
                    self.assertFalse((Path(root)/"other_company").exists())
