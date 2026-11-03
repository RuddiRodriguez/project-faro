import ast
import hashlib
import json
from pathlib import Path
import subprocess
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
    def test_selected_original_files_and_definitions_match_pinned_source(self):
        manifest = json.loads((ROOT / 'SOURCE_MANIFEST.json').read_text())
        for entry in manifest['files']:
            with self.subTest(file=entry['path']):
                actual = (ROOT / 'utils' / entry['path']).read_text()
                self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(), entry['sha256'])
                original = subprocess.check_output(
                    ['git', '-C', entry.get('source_repository', manifest['source_repository']), 'show',
                     f"{entry.get('source_commit', manifest['source_commit'])}:{entry['path']}"], text=True)
                if entry['mode'] == 'exact':
                    self.assertEqual(actual, original)
                    continue
                original_tree, actual_tree = ast.parse(original), ast.parse(actual)
                source_classes = {n.name: n for n in original_tree.body if isinstance(n, ast.ClassDef)}
                for node in actual_tree.body:
                    if not isinstance(node, ast.ClassDef):
                        continue
                    source_class = source_classes[node.name]
                    if entry['mode'] == 'chat_class_subset':
                        source_definitions = {n.name: n for n in source_class.body if isinstance(n, ast.FunctionDef)}
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                if method.name == '_decisions_api_predict':
                                    source = entry['decision_source']
                                    text = subprocess.check_output(['git', '-C', source['source_repository'], 'show',
                                        f"{source['source_commit']}:{entry['path']}"], text=True)
                                    reference = next(n for n in ast.walk(ast.parse(text))
                                                     if isinstance(n, ast.FunctionDef) and n.name == method.name)
                                    self.assertEqual(ast.dump(method), ast.dump(reference))
                                    continue
                                if method.name == '__init__':
                                    # Faro disables SDK retries; all other initialization stays original.
                                    ref = source_definitions[method.name]
                                    self.assertNotIn("max_openai_retries", ast.unparse(method))
                                    expected = ast.unparse(ref).replace('max_openai_retries: int=0, ', '').replace("'max_retries': max_openai_retries", "'max_retries': 0")
                                    self.assertEqual(ast.unparse(method), expected)
                                    continue
                                if method.name == 'chat_predict':
                                    decision_source = entry['decision_source']
                                    text = subprocess.check_output(['git', '-C', decision_source['source_repository'], 'show',
                                        f"{decision_source['source_commit']}:{entry['path']}"], text=True)
                                    reference = next(n for n in ast.walk(ast.parse(text))
                                                     if isinstance(n, ast.FunctionDef) and n.name == 'chat_predict')
                                    self.assertEqual(ast.dump(method.body.pop(0)), ast.dump(reference.body[0]))
                                    resolve = method.body[0]
                                    self.assertEqual(ast.unparse(resolve.test), 'not isinstance(conversation, DecisionsConversation)')
                                    method.body[:1] = resolve.body
                                    original_dispatch = next(n for n in reference.body if isinstance(n, ast.Try)).body[0]
                                    dispatch = next(n for n in method.body if isinstance(n, ast.Try)).body.pop(0)
                                    self.assertEqual(ast.dump(dispatch), ast.dump(original_dispatch))
                                    # Compare dispatch to the original call inside its old retry loop.
                                    ref = source_definitions[method.name]
                                    old = next(n for n in ast.walk(ref) if isinstance(n, ast.Return)
                                               and "_execute_chat_predict" in ast.unparse(n))
                                    self.assertEqual(ast.dump(method.body[-1].body[0]), ast.dump(old))
                                    self.assertEqual([ast.dump(n) for n in method.body[:-1]],
                                                     [ast.dump(n) for n in ref.body[:-2]])
                                    continue
                                self.assertEqual(ast.dump(method), ast.dump(source_definitions[method.name]))
                    else:
                        if entry["path"] == "llms/llm_handler.py":
                            fn = next(m for m in node.body if m.name == "_llm_predict")
                            self.assertEqual(ast.unparse(fn.decorator_list.pop(0)), "track_call")
                            self.assertEqual(ast.unparse(fn.decorator_list.pop()), "track_attempt")
                            self.assertEqual(ast.unparse(fn.decorator_list.pop()), "backoff.on_exception(backoff.expo, OpenAiRecoverableError, max_tries=3)")
                            fn = next(m for m in node.body if m.name == "predict")
                            handler = next(n for n in ast.walk(fn) if isinstance(n, ast.ExceptHandler))
                            self.assertEqual(ast.unparse(handler.type), "(BedRockUnRecoverableError, OpenAiRecoverableError)")
                            handler.type = handler.type.elts[0]
                        self.assertEqual(ast.dump(node), ast.dump(source_class))

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
