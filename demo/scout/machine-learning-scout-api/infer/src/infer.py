from fastapi import FastAPI, HTTPException

from api_objects.faro.scout.input.scout_input import ScoutInput
from api_objects.faro.scout.output.scout_output import ScoutOutput
from scout.local_client import LocalKnowledgeBaseClient
from scout.predictor import Predictor
from scout_api.endpoints.predict_endpoint import PredictEndpoint


def create_app() -> FastAPI:
    app = FastAPI(title="Scout — finds relevant company definitions")
    endpoint = PredictEndpoint(Predictor(LocalKnowledgeBaseClient()))

    @app.post("/v1/search", response_model=ScoutOutput)
    def search(request: ScoutInput) -> ScoutOutput:
        try:
            return endpoint.handle(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    return app


app = create_app()
