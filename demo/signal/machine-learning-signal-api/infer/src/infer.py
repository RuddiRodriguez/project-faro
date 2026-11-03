import os
from pathlib import Path

from dotenv import load_dotenv
from openai import APIError
from utils.llms.model_attempts import install_attempt_tracking
from fastapi import FastAPI, HTTPException
from utils.openai_client.exceptions import OpenAiError
from utils.openai_client.openai_client import OpenAiClient

from api_objects.faro.signal.input.signal_input import SignalInput
from api_objects.faro.signal.output.signal_output import SignalOutput
from faro_signal.predictor import Predictor
from signal_api.endpoints.predict_endpoint import PredictEndpoint


def create_app() -> FastAPI:
    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
    llm_client = OpenAiClient(api_key_secret_name=None,
                             explicit_api_key=os.environ["OPENAI_API_KEY"])
    endpoint = PredictEndpoint(Predictor(llm_client))
    app = FastAPI(title="Signal — decides whether the question is clear and supported")

    @app.post("/v1/classify", response_model=SignalOutput)
    def classify(request: SignalInput) -> SignalOutput:
        try:
            return endpoint.handle(request)
        except (APIError, OpenAiError, ValueError, KeyError, RuntimeError) as error:
            raise HTTPException(status_code=502, detail="Signal classification failed; no decision returned") from error

    install_attempt_tracking(app, "Signal")
    return app


app = create_app()
