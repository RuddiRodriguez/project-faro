import os
from pathlib import Path

from dotenv import load_dotenv
from utils.llms.model_attempts import install_attempt_tracking
from fastapi import FastAPI
from utils.llms.llm_handler import LLMHandler
from utils.openai_client.openai_client import OpenAiClient
from api_objects.faro.shield.input.shield_input import ShieldInput
from api_objects.faro.shield.output.shield_output import ShieldOutput
from shield.verifier import Verifier
from shield_api.endpoints.verify_endpoint import VerifierEndpoint


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "local_data/demo_dataset"


def create_app(data_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Shield — checks the read against the records")
    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
    handler = LLMHandler(llm_client=OpenAiClient(api_key_secret_name=None, explicit_api_key=os.environ["OPENAI_API_KEY"]))
    endpoint = VerifierEndpoint(Verifier(data_path or Path(os.getenv("FARO_DATA_PATH", DEFAULT_DATA_PATH)), handler))

    @app.post("/v1/verify", response_model=ShieldOutput)
    def verify_evidence(request: ShieldInput) -> ShieldOutput:
        return endpoint.handle(request)

    install_attempt_tracking(app, "Shield")
    return app


app = create_app()
