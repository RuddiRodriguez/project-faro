"""All current model prompts expose the same auditable, short explanation fields."""
import os
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

from bridge.prompts.read_prompt import ReadPrompt
from thread.prompts.standalone_query_prompt import StandaloneQueryPrompt
from guide.prompts.followup_prompt import FollowUpPrompt
from shield.prompts.review_prompt import ReviewPrompt
from voice.prompts.answer_prompt import AnswerPrompt
from utils.llms.model_attempts import track_call,track_attempt,turn_context,read_explanations,read_attempts


class ExplanationTests(TestCase):
    def test_each_prompt_requires_summaries_and_result(self):
        for prompt,attribute in [(ReadPrompt,"STRUCTURED_OUTPUT"),(StandaloneQueryPrompt,"STRUCTURED_OUTPUT"),
                (FollowUpPrompt,"STRUCTURED_OUTPUT"),(ReviewPrompt,"STRUCTURED_OUTPUT"),
                (ReviewPrompt,"FINDINGS_OUTPUT"),(AnswerPrompt,"STRUCTURED_OUTPUT")]:
            with self.subTest(prompt=prompt.__name__,attribute=attribute):
                schema=getattr(prompt,attribute).json_schema
                self.assertTrue({"initial_analysis","reasoning"}.issubset(schema["required"]))
                self.assertIn("Initial Analysis Guidelines",prompt.SYSTEM_MESSAGE)
                self.assertIn("Final Reasoning Guidelines",prompt.SYSTEM_MESSAGE)
                self.assertIn("{",prompt.USER_MESSAGE)

    def test_summaries_are_saved_per_call_and_company(self):
        with TemporaryDirectory() as temp,patch.dict(os.environ,FARO_COLLECTION_PATH=temp):
            turn=str(uuid4())
            token=turn_context.set(("test_company",turn,"Bridge"))
            @track_call
            @track_attempt
            def respond():
                return SimpleNamespace(is_success=True,decisions_response=None,assistant_tools=[
                    SimpleNamespace(parsed_arguments=dict(initial_analysis="Two permitted rows.",reasoning="A sum answers the request."))])
            try:
                respond()
                respond()
            finally:
                turn_context.reset(token)
            saved=read_explanations(temp,"test_company",turn)
            self.assertEqual(len(saved),2)
            self.assertEqual(saved[0]["explanations"][0]["reasoning"],"A sum answers the request.")
            self.assertNotEqual(saved[0]["call_id"],saved[1]["call_id"])
            self.assertEqual(read_explanations(temp,"another_company",turn),[])
            self.assertEqual(read_attempts(temp,"test_company",turn)["Bridge"]["attempts"],2)
