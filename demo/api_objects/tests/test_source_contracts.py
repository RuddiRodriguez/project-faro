from unittest import TestCase
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.scout.input.scout_input import ScoutInput
from api_objects.faro.signal.input.signal_input import SignalInput
from api_objects.faro.compass.output.compass_output import CompassOutput


class SourceContracts(TestCase):
    def test_data_question_needs_no_glossary_or_task_list(self):
        request=dict(company_id="new_client",permitted_scope_ids=["site"],question="How many orders?")
        self.assertEqual(BridgeInput(**request).company_id,"new_client")
        self.assertNotIn("definition_ids",BridgeInput.model_fields)
        self.assertNotIn("document_ids",ScoutInput.model_fields)
        self.assertNotIn("supported_tasks",SignalInput.model_fields)
        self.assertIn("sources",CompassOutput.model_fields)
        self.assertNotIn("company_information",CompassOutput.model_fields)

    def test_reply_language_is_not_part_of_the_demo_contract(self):
        from api_objects.faro.compass.input.compass_input import CompassInput
        from api_objects.faro.guide.input.guide_input import GuideInput
        from api_objects.faro.voice.input.voice_input import VoiceInput
        from compass.orchestrator_input import OrchestratorInput
        from guide.generator_input import GeneratorInput as GuideGeneratorInput
        from voice.generator_input import GeneratorInput as VoiceGeneratorInput
        for model in (CompassInput, GuideInput, VoiceInput, OrchestratorInput, GuideGeneratorInput, VoiceGeneratorInput):
            self.assertNotIn('language',model.model_fields)

    def test_user_facing_prompts_request_english(self):
        from guide.prompts.followup_prompt import FollowUpPrompt
        from bridge.prompts.read_prompt import ReadPrompt
        from shield.prompts.review_prompt import ReviewPrompt
        from voice.prompts.answer_prompt import AnswerPrompt
        for prompt in (FollowUpPrompt, ReadPrompt, ReviewPrompt, AnswerPrompt):
            self.assertIn('English',prompt.SYSTEM_MESSAGE)
            self.assertNotIn('{language}',prompt.USER_MESSAGE)
