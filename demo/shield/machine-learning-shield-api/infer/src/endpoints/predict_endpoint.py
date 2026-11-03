from api_objects.faro.shield.input.shield_input import ShieldInput as ApiPredictorInput
from api_objects.faro.shield.output.shield_output import ShieldOutput as ApiPredictorOutput
from shield.predictor import Predictor
from shield.predictor_input import PredictorInput as LibPredictorInput


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        request = LibPredictorInput.model_validate(api_input, from_attributes=True)
        result = self.predictor.predict(request)
        return ApiPredictorOutput.model_validate(result, from_attributes=True)
