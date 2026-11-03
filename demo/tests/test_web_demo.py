"""Screen state and saved-document access; model behavior is tested separately."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from api_objects.faro.gate.output.gate_output import GateOutput
from compass_api.infer import create_app

WEB = Path(__file__).resolve().parents[1] / "web"
sys.path.insert(0, str(WEB))
ACCESS = dict(user_id="maria", company_id="harbor", permitted_scope_ids=["north"], permission_version="v1")


class WebTests(unittest.TestCase):
    def test_clarification_and_account_reset(self):
        result = dict(conversation_id=str(uuid4()), turn_id=str(uuid4()),
                      rewrite={"question": "Which cranes?"}, followup={"followup_text": "Which period?"},
                      answer=None, verification=None)
        with patch("client.sign_in", return_value=ACCESS), patch("client.ask", return_value=result) as ask, \
             patch("views.saved_turn", return_value=dict(elapsed_ms=10, cache=[], model_attempts=[])):
            app = AppTest.from_file(str(WEB / "app.py")).run()
            app.button[0].click().run()
            app.chat_input[0].set_value("Which cranes?").run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state.conversation_id, result["conversation_id"])
            app.run()
            self.assertEqual(ask.call_count, 1)
            app.chat_input[0].set_value("October").run()
            self.assertEqual(ask.call_args.args[2], result["conversation_id"])
            app.button[1].click().run()
            self.assertIsNone(app.session_state.access)
            self.assertEqual(app.session_state.messages, [])
            self.assertIsNone(app.session_state.conversation_id)

    def test_answer_context_and_new_question(self):
        result = dict(conversation_id=str(uuid4()), turn_id=str(uuid4()),
                      rewrite={"question": "How many stores?"}, followup=None,
                      answer={"text": "Two stores.", "documents": []}, verification={"status": "verified"})
        with patch("client.sign_in", return_value=ACCESS), patch("client.ask", return_value=result) as ask, \
             patch("views.saved_turn", return_value=dict(elapsed_ms=10, cache=[], model_attempts=[])):
            app = AppTest.from_file(str(WEB / "app.py")).run()
            app.button[0].click().run()
            app.chat_input[0].set_value("How many stores?").run()
            self.assertFalse(app.exception)
            self.assertIsNone(app.session_state.conversation_id)
            app.chat_input[0].set_value("And per region?").run()
            self.assertEqual(ask.call_args.args[3], result["conversation_id"])
            app.button[0].click().run()
            self.assertEqual(app.session_state.messages, [])
            self.assertIsNone(app.session_state.previous_answer_id)
            self.assertEqual(app.session_state.access, ACCESS)

    def test_unsupported_question_is_not_shown_as_waiting(self):
        result = dict(conversation_id=str(uuid4()), turn_id=str(uuid4()),
                      rewrite={"question": "Unavailable question"}, followup=None,
                      answer={"text": "That is not supported by the available data.", "documents": []},
                      verification=None)
        with patch("client.sign_in", return_value=ACCESS), patch("client.ask", return_value=result), \
             patch("views.saved_turn", return_value=dict(elapsed_ms=10, cache=[], model_attempts=[])):
            app = AppTest.from_file(str(WEB / "app.py")).run()
            app.button[0].click().run()
            app.chat_input[0].set_value("Unavailable question").run()
            self.assertFalse(app.exception)
            self.assertTrue(any("No answer was produced" in item.value for item in app.markdown))
            self.assertIsNone(app.session_state.conversation_id)

    def test_saved_document_access_and_integrity(self):
        cid, tid = str(uuid4()), str(uuid4())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "harbor/source.json"
            path.parent.mkdir()
            path.write_text('{"value": 4}')
            document = dict(uri=path.as_uri(), name=path.name, version=sha256(path.read_bytes()).hexdigest())
            doc = dict(access=ACCESS, turns=[dict(_id=tid, response={"answer": {"documents": [document]}})])
            with patch.dict("os.environ", FARO_DOCUMENT_PATH=folder), \
                 patch("compass_api.infer.GateClient.read_access", return_value=GateOutput(**ACCESS)) as gate, \
                 patch("compass_api.infer.DataCollection.read_conversation", return_value=doc):
                client = TestClient(create_app())
                url = f"/v1/conversations/{cid}/turns/{tid}/documents/0?user_id=maria"
                response = client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, path.read_bytes())
                gate.return_value = GateOutput(**{**ACCESS, "user_id": "luis"})
                self.assertEqual(client.get(url).status_code, 403)
                gate.return_value = GateOutput(**{**ACCESS, "permitted_scope_ids": []})
                self.assertEqual(client.get(url).status_code, 403)
                gate.return_value = GateOutput(**ACCESS)
                path.write_text('changed')
                self.assertEqual(client.get(url).status_code, 409)
                document["uri"] = Path(folder).joinpath("outside.json").as_uri()
                self.assertEqual(client.get(url).status_code, 403)
                self.assertEqual(client.get(url.replace(tid, "../other")).status_code, 404)


if __name__ == "__main__":
    unittest.main()
