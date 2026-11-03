from api_objects.faro.signal.input.signal_input import SignalInput as ApiPredictorInput
from api_objects.faro.signal.output.signal_output import SignalOutput as ApiPredictorOutput
from faro_signal.predictor import Predictor
from faro_signal.predictor_input import PredictorInput as LibPredictorInput, Definition


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        predictor_input = LibPredictorInput(
            unclear_references=api_input.unclear_references,
            question=api_input.question,
            matches=[Definition(title=m.title, text=m.text, source=m.source) for m in api_input.matches],
            supported_tasks=api_input.supported_tasks,
            groups=api_input.groups, connected_sources=api_input.connected_sources,
            permitted_scopes=api_input.permitted_scopes,
        )
        result = self.predictor.predict(predictor_input)
        return ApiPredictorOutput(action=result.action, missing_choice=result.missing_choice)
