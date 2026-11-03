from api_objects.faro.voice.input.voice_input import VoiceInput as ApiGeneratorInput
from api_objects.faro.voice.output.voice_output import VoiceOutput as ApiGeneratorOutput
from voice.generator import Generator
from voice.generator_input import GeneratorInput as LibGeneratorInput


class GeneratorEndpoint:
    def __init__(self, generator: Generator):
        self.generator = generator

    def handle(self, api_input: ApiGeneratorInput) -> ApiGeneratorOutput:
        request = LibGeneratorInput.model_validate(api_input, from_attributes=True)
        result = self.generator.generate(request)
        return ApiGeneratorOutput.model_validate(result, from_attributes=True)
