import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from api_objects.faro.gate.input.gate_input import GateInput
from api_objects.faro.gate.output.gate_output import GateOutput
from gate.predictor import Predictor
from gate_api.endpoints.predict_endpoint import PredictEndpoint


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "local_data/demo_dataset"


def create_app(data_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Gate — reads demo user permissions")
    endpoint = PredictEndpoint(Predictor(data_path or Path(os.getenv("FARO_DATA_PATH", DEFAULT_DATA_PATH))))

    @app.post("/v1/access", response_model=GateOutput)
    def read_access(request: GateInput) -> GateOutput:
        try:
            return endpoint.handle(request)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    return app


app = create_app()
