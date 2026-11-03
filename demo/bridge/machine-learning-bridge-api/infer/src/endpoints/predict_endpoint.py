from api_objects.faro.bridge.input.bridge_input import BridgeInput as ApiPredictorInput
from api_objects.faro.bridge.output.bridge_output import BridgeOutput as ApiPredictorOutput
from bridge.predictor import Predictor
from bridge.predictor_input import PredictorInput as LibPredictorInput


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        request = LibPredictorInput.model_validate(api_input, from_attributes=True)
        result = self.predictor.predict(request)
        return ApiPredictorOutput.model_validate(result, from_attributes=True)
