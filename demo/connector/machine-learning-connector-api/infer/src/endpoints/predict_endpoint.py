from api_objects.faro.connector.output.connector_output import ConnectorOutput
from connector.predictor_input import PredictorInput


class PredictEndpoint:
    def __init__(self, predictor):
        self.predictor=predictor

    def handle(self, request):
        result=self.predictor.predict(PredictorInput.model_validate(request,from_attributes=True))
        return ConnectorOutput.model_validate(result,from_attributes=True)
