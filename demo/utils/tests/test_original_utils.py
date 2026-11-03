import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from pydantic import ValidationError
from utils.llms.common.structured_output import StructuredOutput
from utils.llms.common.intelligence_level import IntelligenceLevel, ModelNameKey
from utils.llms.common.intelligence_level_resolver import resolve_intelligence_level
from utils.llms.llm_handler import LLMHandler
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage

ROOT = Path(__file__).resolve().parents[1]


class OriginalSourceTests(unittest.TestCase):
    def test_vendored_files_match_recorded_checksums(self):
        manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text())
        for entry in manifest["files"]:
            self.assertEqual(hashlib.sha256((ROOT/"utils"/entry["path"]).read_bytes()).hexdigest(),
                             entry["sha256"], entry["path"])

    def test_original_structured_output_fields_and_description(self):
        self.assertEqual(set(StructuredOutput.model_fields), {'name', 'json_schema', 'strict', 'description'})
        with self.assertRaises(ValidationError):
            StructuredOutput(name='', json_schema={})
        output = StructuredOutput(name='example', json_schema={'type': 'object'}, description='Meaning')
        self.assertEqual(output.to_api_input()['description'], 'Meaning')

    def test_original_level_resolution_does_not_mutate_conversation(self):
        conversation = Conversation(intelligence_level=IntelligenceLevel.YOLO,
                                    system_message=SystemMessage(content='Rewrite'))
        resolved, effort, verbosity = resolve_intelligence_level(conversation, model_key=ModelNameKey.MODEL_NAME)
        self.assertEqual(resolved.llm_model_name, IntelligenceLevel.YOLO.settings['model_name'])
        self.assertEqual((effort, verbosity), ('none', 'low'))
        self.assertEqual(conversation.intelligence_level, IntelligenceLevel.YOLO)
        self.assertIsNone(resolved.intelligence_level)

    def test_original_handler_calls_chat_predict_with_original_wrapper(self):
        client = Mock()
        result = Mock(is_success=True)
        client.chat_predict.return_value = result
        handler = LLMHandler(llm_client=client)
        conversation = Conversation(intelligence_level=IntelligenceLevel.YOLO,
                                    system_message=SystemMessage(content='Rewrite'))
        output = StructuredOutput(name='question', json_schema={'type': 'object'})
        self.assertIs(handler.predict(conversation=conversation, structured_output=output), result)
        self.assertIs(client.chat_predict.call_args.kwargs['structured_output'], output)
        self.assertIs(client.chat_predict.call_args.kwargs['conversation'], conversation)


if __name__ == '__main__':
    unittest.main()
