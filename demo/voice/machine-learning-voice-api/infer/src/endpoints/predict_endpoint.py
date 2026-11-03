from api_objects.faro.voice.input.voice_input import VoiceInput as ApiPredictorInput
from api_objects.faro.voice.output.voice_output import VoiceOutput as ApiPredictorOutput
from voice.predictor import Predictor
from voice.predictor_input import PredictorInput as LibPredictorInput


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        request = LibPredictorInput.model_validate(api_input, from_attributes=True)
        result = self.predictor.predict(request)
        return ApiPredictorOutput.model_validate(result, from_attributes=True)
