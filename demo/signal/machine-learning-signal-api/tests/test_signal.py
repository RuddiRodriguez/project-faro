import json
import unittest
from unittest.mock import Mock

from faro_signal.predictor import Predictor
from faro_signal.predictor_input import PredictorInput
from utils.openai_client.conversation.assistant_message import AssistantMessage
from utils.openai_client.outputs.predict_output import PredictOutput


from faro_signal.common_tools.custom_exceptions import JsonFormatError
from faro_signal.quality.classifier import Classifier
from faro_signal.quality.classifier_input import ClassifierInput


class SignalTests(unittest.TestCase):
    def test_missing_company_material_stops_without_model_call(self):
        handler = Mock()
        request = PredictorInput(question="Which cranes performed badly?", matches=[],
                                 permitted_scopes=[], supported_tasks=[])
        result = Predictor(handler).predict(request)
        self.assertEqual(result.action, "Unsupported")
        handler.chat_predict.assert_not_called()

    def test_duplicate_model_answers_do_not_become_a_decision(self):
        signal = Classifier(Mock())
        request = ClassifierInput(question="Which cranes?",
            permitted_scopes=["North Terminal"], supported_tasks=["Compare cranes"], matches=[])
        conversation = signal._build_conversation(request)
        answer = {"type": "choice", "name": "next_action", "choice": "Continue"}
        response = PredictOutput(input_conversation=conversation, assistant_message=AssistantMessage(
            content=json.dumps([answer, answer])), assistant_tools=None, finish_reason=None, token_usage=None,
            decisions_response={"answers": [answer, answer]})
        with self.assertRaisesRegex(JsonFormatError, "missing or duplicate"):
            signal._parse_prediction_output(response, request)
