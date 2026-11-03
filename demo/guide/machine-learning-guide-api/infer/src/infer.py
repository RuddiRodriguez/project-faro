import os
from pathlib import Path

from dotenv import load_dotenv
from utils.llms.model_attempts import install_attempt_tracking
from fastapi import FastAPI, HTTPException
from utils.openai_client.exceptions import OpenAiError
from utils.openai_client.openai_client import OpenAiClient
from utils.llms.llm_handler import LLMHandler

from api_objects.faro.guide.input.guide_input import GuideInput
from api_objects.faro.guide.output.guide_output import GuideOutput
from guide.predictor import Predictor
from guide_api.endpoints.predict_endpoint import PredictEndpoint


def create_app() -> FastAPI:
    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
    llm_client = OpenAiClient(api_key_secret_name=None,
                             explicit_api_key=os.environ["OPENAI_API_KEY"])
    handler = LLMHandler(llm_client=llm_client)
    endpoint = PredictEndpoint(Predictor(handler))
    app = FastAPI(title="Guide — asks for a missing detail")

    @app.post("/v1/followup", response_model=GuideOutput)
    def generate_followup(request: GuideInput) -> GuideOutput:
        try:
            return endpoint.handle(request)
        except (OpenAiError, ValueError, RuntimeError) as error:
            raise HTTPException(status_code=502, detail="Follow-up generation failed; no question returned") from error

    install_attempt_tracking(app, "Guide")
    return app


app = create_app()
