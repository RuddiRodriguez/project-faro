from api_objects.faro.guide.input.guide_input import GuideInput as ApiGeneratorInput
from api_objects.faro.guide.output.guide_output import GuideOutput as ApiGeneratorOutput
from guide.generator import Generator
from guide.generator_input import GeneratorInput as LibGeneratorInput, Passage


class GeneratorEndpoint:
    def __init__(self, generator: Generator):
        self.generator = generator

    def handle(self, api_input: ApiGeneratorInput) -> ApiGeneratorOutput:
        generator_input = LibGeneratorInput(question_text=api_input.question_text, user_messages=api_input.user_messages,
            missing_choice=api_input.missing_choice,
            passages=[Passage(title=d.title, text=d.text) for d in api_input.passages])
        result = self.generator.generate(generator_input)
        return ApiGeneratorOutput(followup_text=result.followup_text, initial_analysis=result.initial_analysis, reasoning=result.reasoning)
