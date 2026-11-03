from utils.llms.llm_handler import LLMHandler
from guide.followup.generator import Generator as FollowupGenerator
from guide.followup.generator_input import GeneratorInput as FollowupGeneratorInput
from guide.generator_input import GeneratorInput
from guide.generator_output import GeneratorOutput


class Generator:
    def __init__(self, llm_handler: LLMHandler):
        self.followup_predictor = FollowupGenerator(llm_handler)

    def generate(self, generator_input: GeneratorInput) -> GeneratorOutput:
        followup_generator_input = FollowupGeneratorInput(
            **generator_input.model_dump(),
        )
        followup = self.followup_predictor.generate_followup(followup_generator_input)
        if not followup.is_success:
            raise RuntimeError(f"Guide could not generate a question: {followup.error_code.name}")
        return GeneratorOutput(followup_text=followup.followup_text, initial_analysis=followup.initial_analysis, reasoning=followup.followup_reasoning)
