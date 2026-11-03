import os
from pathlib import Path

from dotenv import load_dotenv
from utils.llms.model_attempts import install_attempt_tracking
from fastapi import FastAPI, HTTPException
from utils.openai_client.exceptions import OpenAiError
from utils.openai_client.openai_client import OpenAiClient
from utils.llms.llm_handler import LLMHandler

from api_objects.faro.voice.input.voice_input import VoiceInput
from api_objects.faro.voice.output.voice_output import VoiceOutput
from voice.predictor import Predictor
from voice_api.endpoints.predict_endpoint import PredictEndpoint


def create_app() -> FastAPI:
    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
    llm_client = OpenAiClient(api_key_secret_name=None,
                             explicit_api_key=os.environ["OPENAI_API_KEY"])
    handler = LLMHandler(llm_client=llm_client)
    endpoint = PredictEndpoint(Predictor(handler))
    app = FastAPI(title="Voice — explains the checked result")

    @app.post("/v1/answer", response_model=VoiceOutput)
    def write_answer(request: VoiceInput) -> VoiceOutput:
        try:
            return endpoint.handle(request)
        except (OpenAiError, ValueError, RuntimeError) as error:
            raise HTTPException(status_code=502, detail="Answer generation failed") from error

    install_attempt_tracking(app, "Voice")
    return app


app = create_app()
