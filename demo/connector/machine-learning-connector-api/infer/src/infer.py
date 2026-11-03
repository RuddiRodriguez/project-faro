import os
from pathlib import Path
from fastapi import FastAPI,HTTPException
from api_objects.faro.connector.input.connector_input import ConnectorInput
from api_objects.faro.connector.output.connector_output import ConnectorOutput
from connector.predictor import Predictor
from connector_api.endpoints.predict_endpoint import PredictEndpoint

DEFAULT_ROOT=Path(__file__).resolve().parents[4]/"connector/fixtures"


def create_app(root=None):
    app=FastAPI(title="Connector — reads permitted client sources")
    endpoint=PredictEndpoint(Predictor(Path(root or os.getenv("FARO_CONNECTOR_ROOT",DEFAULT_ROOT))))

    @app.post("/v1/sources",response_model=ConnectorOutput)
    def sources(request:ConnectorInput):
        try:
            return endpoint.handle(request)
        except PermissionError as error:
            raise HTTPException(403,str(error)) from error
        except ValueError as error:
            raise HTTPException(422,str(error)) from error
    return app


app=create_app()
