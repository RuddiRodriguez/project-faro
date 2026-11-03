from api_objects.faro.gate.input.gate_input import GateInput as ApiPredictorInput
from api_objects.faro.gate.output.gate_output import GateOutput as ApiPredictorOutput
from gate.predictor import Predictor
from gate.predictor_input import PredictorInput as LibPredictorInput


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        predictor_input = LibPredictorInput(user_id=api_input.user_id)
        result = self.predictor.predict(predictor_input)
        return ApiPredictorOutput(user_id=result.user_id,
                                  company_id=result.company_id,
                                  permitted_scope_ids=result.permitted_scope_ids,
                                  permission_version=result.permission_version)
