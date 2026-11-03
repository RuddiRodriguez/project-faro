"""Inject failures only at the provider boundary. No credentials or network needed."""
import json
import unittest
from unittest.mock import Mock, patch

import httpx2
import openai

from bridge.predictor_files.read_prompt import ReadPrompt
from faro_signal.predictor import Predictor as Signal
from faro_signal.predictor_input import PredictorInput
from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.llms.llm_handler import LLMHandler
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.assistant_message import AssistantMessage
from utils.openai_client.exceptions import OpenAiRecoverableError, OpenAiUnRecoverableError, OpenAIGeneralError
from utils.openai_client.openai_client import OpenAiClient
from utils.openai_client.outputs.predict_output import PredictOutput


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.client = OpenAiClient(None, explicit_api_key="unused-in-test")
        self.request = httpx2.Request("POST", "https://example.invalid")
        self.handler = LLMHandler(self.client)
        self.chat = Conversation(intelligence_level=IntelligenceLevel.LIGHT, system_message=SystemMessage(content="Read"))
        self.enterContext(patch("time.sleep"))

    def read(self):
        return self.handler.predict(conversation=self.chat, structured_output=ReadPrompt.STRUCTURED_OUTPUT)

    def status(self, code, body=None):
        return openai.APIStatusError("test", response=httpx2.Response(code,request=self.request),body=body)

    def test_bridge_two_timeouts_then_success_3_calls(self):
        timeout = openai.APITimeoutError(request=self.request)
        good = Mock(is_success=True)
        with patch.object(self.client, "_execute_chat_predict", side_effect=[timeout,timeout,good]) as send:
            self.assertIs(self.read(), good)
            self.assertEqual(send.call_count, 3)

    def test_permanent_or_invalid_response_1_call(self):
        for error, expected in [(self.status(401),OpenAiUnRecoverableError),
                (self.status(400,{"message":"your prompt was flagged as potentially violating our usage policy"}),OpenAiUnRecoverableError),
                (self.status(429,{"code":"insufficient_quota"}),OpenAiUnRecoverableError),
                (KeyError("missing field"),OpenAIGeneralError)]:
            with self.subTest(error=repr(error)), patch.object(self.client,"_execute_chat_predict",side_effect=error) as send:
                with self.assertRaises(expected):
                    self.read()
                self.assertEqual(send.call_count,1)

    def test_persistent_503_stops_after_3_calls(self):
        with patch.object(self.client,"_execute_chat_predict",side_effect=self.status(503)) as send:
            with self.assertRaises(OpenAiRecoverableError):
                self.read()
            self.assertEqual(send.call_count,3)

    def test_signal_rate_limit_then_continue_2_calls(self):
        def send(conversation, timeout):
            if decision.call_count==1:
                raise self.status(429)
            answers = [{"name":"next_action","type":"choice","choice":"Continue"}]
            return PredictOutput(conversation,AssistantMessage(content=json.dumps(answers)),None,None,None,
                                 decisions_response={"answers":answers})
        with patch.object(self.client, "_decisions_api_predict",side_effect=send) as decision:
            result=Signal(self.client).predict(PredictorInput(question="Compare the locations",matches=[],
                    permitted_scopes=["North"],supported_tasks=["Compare locations"]))
            self.assertEqual(result.action,"Continue")
            self.assertEqual(decision.call_count,2)
