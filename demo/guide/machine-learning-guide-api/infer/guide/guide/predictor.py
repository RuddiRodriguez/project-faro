from utils.llms.llm_handler import LLMHandler
from guide.followup.generator import Generator as FollowupGenerator
from guide.followup.generator_input import GeneratorInput as FollowupGeneratorInput
from guide.predictor_input import PredictorInput
from guide.predictor_output import PredictorOutput


class Predictor:
    def __init__(self, llm_handler: LLMHandler):
        self.followup_predictor = FollowupGenerator(llm_handler)

    def predict(self, predictor_input: PredictorInput) -> PredictorOutput:
        followup_generator_input = FollowupGeneratorInput(
            **predictor_input.model_dump(),
        )
        followup = self.followup_predictor.generate_followup(followup_generator_input)
        if not followup.is_success:
            raise RuntimeError(f"Guide could not generate a question: {followup.error_code.name}")
        return PredictorOutput(followup_text=followup.followup_text, proposed_changes=followup.proposed_changes)
