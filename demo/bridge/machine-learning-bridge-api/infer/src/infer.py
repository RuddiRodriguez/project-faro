import os
from pathlib import Path

from dotenv import load_dotenv
from utils.llms.model_attempts import install_attempt_tracking
from fastapi import FastAPI
from utils.llms.llm_handler import LLMHandler
from utils.openai_client.openai_client import OpenAiClient
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.bridge.output.bridge_output import BridgeOutput
from bridge.reader import Reader
from bridge_api.endpoints.read_endpoint import ReaderEndpoint


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "local_data/demo_dataset"


def create_app(data_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Bridge — reads permitted operational records")
    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
    handler = LLMHandler(llm_client=OpenAiClient(api_key_secret_name=None, explicit_api_key=os.environ["OPENAI_API_KEY"]))
    endpoint = ReaderEndpoint(Reader(data_path or Path(os.getenv("FARO_DATA_PATH", DEFAULT_DATA_PATH)), handler))

    @app.post("/v1/evidence", response_model=BridgeOutput)
    def read_evidence(request: BridgeInput) -> BridgeOutput:
        return endpoint.handle(request)

    install_attempt_tracking(app, "Bridge")
    return app


app = create_app()
