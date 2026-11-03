from unittest import TestCase
from unittest.mock import Mock
from guide.followup.generator import Generator
from guide.followup.generator_input import GeneratorInput
from guide.common_tools.error_code import ErrorCode


class GuideTests(TestCase):
    def test_missing_required_prediction_field_returns_error(self):
        handler = Mock()
        handler.predict.return_value.is_success = True
        handler.predict.return_value.assistant_tools = [Mock(parsed_arguments={"reasoning": "indicator"})]
        result = Generator(handler).generate_followup(GeneratorInput(
            question_text="Which cranes performed badly?", missing_choice="performance indicator", language="en",
            passages=[]))
        self.assertEqual(result.error_code, ErrorCode.INVALID_LLM_RESPONSE)
        self.assertIsNone(result.followup_text)
