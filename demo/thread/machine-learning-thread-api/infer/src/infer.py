import os
from pathlib import Path

from dotenv import load_dotenv
from utils.llms.model_attempts import install_attempt_tracking
from fastapi import FastAPI, HTTPException
from utils.openai_client.exceptions import OpenAiError
from utils.openai_client.openai_client import OpenAiClient
from utils.llms.llm_handler import LLMHandler

from api_objects.faro.thread.input.thread_input import ThreadInput
from api_objects.faro.thread.output.thread_output import ThreadOutput
from thread.rewriter import Rewriter
from thread_api.endpoints.rewrite_endpoint import RewriterEndpoint


def create_app() -> FastAPI:
    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
    llm_client = OpenAiClient(api_key_secret_name=None,
                             explicit_api_key=os.environ["OPENAI_API_KEY"])
    handler = LLMHandler(llm_client=llm_client)
    endpoint = RewriterEndpoint(Rewriter(handler))
    app = FastAPI(title="Thread — combines the question and replies")

    @app.post("/v1/rewrite", response_model=ThreadOutput)
    def rewrite_question(request: ThreadInput) -> ThreadOutput:
        try:
            return endpoint.handle(request)
        except (OpenAiError, ValueError, RuntimeError) as error:
            raise HTTPException(status_code=502, detail="Question rewriting failed; no rewritten question returned") from error

    install_attempt_tracking(app, "Thread")
    return app


app = create_app()
