import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from api_objects.faro.compass.input.compass_input import CompassInput
from api_objects.faro.compass.output.compass_output import CompassOutput
from pathlib import Path
from compass.data_collection import ConversationInputError, DataCollection
from compass.orchestrator import Orchestrator
from compass_api.endpoints.orchestrate_endpoint import OrchestratorEndpoint
from compass_api.external_services.gate_client import GateClient
from compass_api.external_services.library_client import LibraryClient
from compass_api.external_services.thread_client import ThreadClient
from compass_api.external_services.scout_client import ScoutClient
from compass_api.external_services.voice_client import VoiceClient
from compass_api.external_services.shield_client import ShieldClient
from compass_api.external_services.bridge_client import BridgeClient
from compass_api.external_services.guide_client import GuideClient
from compass_api.external_services.signal_client import SignalClient


def create_app(gate_url: str | None = None, library_url: str | None = None,
               thread_url: str | None = None, scout_url: str | None = None, signal_url: str | None = None,
               guide_url: str | None = None, bridge_url: str | None = None, shield_url: str | None = None, voice_url: str | None = None) -> FastAPI:
    app = FastAPI(title="Compass — coordinates Gate, Library, Thread, Scout, Signal, Guide, Bridge, Shield and Voice")
    orchestrator = Orchestrator(
        collection=DataCollection(os.getenv("FARO_COLLECTION_PATH", Path(__file__).resolve().parents[4] / "local_data/data_collection")),
        gate_client=GateClient(gate_url or os.getenv("FARO_GATE_URL", "http://127.0.0.1:8002")),
        library_client=LibraryClient(library_url or os.getenv("FARO_LIBRARY_URL", "http://127.0.0.1:8001")),
        thread_client=ThreadClient(thread_url or os.getenv("FARO_THREAD_URL", "http://127.0.0.1:8003")),
        scout_client=ScoutClient(scout_url or os.getenv("FARO_SCOUT_URL", "http://127.0.0.1:8004")),
        voice_client=VoiceClient(voice_url or os.getenv("FARO_VOICE_URL", "http://127.0.0.1:8009")),
        shield_client=ShieldClient(shield_url or os.getenv("FARO_SHIELD_URL", "http://127.0.0.1:8008")),
        bridge_client=BridgeClient(bridge_url or os.getenv("FARO_BRIDGE_URL", "http://127.0.0.1:8007")),
        guide_client=GuideClient(guide_url or os.getenv("FARO_GUIDE_URL", "http://127.0.0.1:8006")),
        signal_client=SignalClient(signal_url or os.getenv("FARO_SIGNAL_URL", "http://127.0.0.1:8005")),
    )
    endpoint = OrchestratorEndpoint(orchestrator)

    @app.post("/v1/questions", response_model=CompassOutput)
    def prepare_question(request: CompassInput) -> CompassOutput:
        try:
            return endpoint.handle(request)
        except ConversationInputError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except httpx.RequestError as error:
            raise HTTPException(status_code=503, detail="A required service could not be reached") from error
        except (httpx.HTTPStatusError, ValidationError, ValueError) as error:
            raise HTTPException(status_code=502, detail=next(iter(getattr(error, "__notes__", [])), "Compass could not process a service response")) from error

    return app


app = create_app()
