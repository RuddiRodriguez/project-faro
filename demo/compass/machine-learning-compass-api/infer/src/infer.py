import os
from uuid import UUID
from urllib.parse import unquote, urlparse
from hashlib import sha256

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import ValidationError

from api_objects.faro.compass.input.compass_input import CompassInput
from api_objects.faro.compass.output.compass_output import CompassOutput
from pathlib import Path
from compass.data_collection import ConversationInputError, DataCollection
from compass.orchestrator import Orchestrator
from compass_api.endpoints.orchestrate_endpoint import OrchestratorEndpoint
from compass_api.external_services.gate_client import GateClient
from compass_api.external_services.connector_client import ConnectorClient
from compass_api.external_services.thread_client import ThreadClient
from compass_api.external_services.scout_client import ScoutClient
from compass_api.external_services.voice_client import VoiceClient
from compass_api.external_services.shield_client import ShieldClient
from compass_api.external_services.bridge_client import BridgeClient
from compass_api.external_services.guide_client import GuideClient
from compass_api.external_services.signal_client import SignalClient


def create_app(gate_url: str | None = None, connector_url: str | None = None,
               thread_url: str | None = None, scout_url: str | None = None, signal_url: str | None = None,
               guide_url: str | None = None, bridge_url: str | None = None, shield_url: str | None = None, voice_url: str | None = None) -> FastAPI:
    app = FastAPI(title="Compass — coordinates Gate, Connector, Thread, Scout, Signal, Guide, Bridge, Shield and Voice")
    orchestrator = Orchestrator(
        collection=DataCollection(os.getenv("FARO_COLLECTION_PATH", Path(__file__).resolve().parents[4] / "local_data/data_collection")),
        gate_client=GateClient(gate_url or os.getenv("FARO_GATE_URL", "http://127.0.0.1:8002")),
        connector_client=ConnectorClient(connector_url or os.getenv("FARO_CONNECTOR_URL", "http://127.0.0.1:8010")),
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

    def read_saved_turn(user_id, conversation_id, turn_id):
        try:
            access = orchestrator.gate_client.read_access(user_id)
        except httpx.HTTPStatusError as error:
            raise HTTPException(status_code=403, detail="Account access could not be verified") from error
        except httpx.RequestError as error:
            raise HTTPException(status_code=503, detail="The access service could not be reached") from error
        doc = orchestrator.collection.read_conversation(access.company_id, conversation_id)
        if not doc or doc["access"] != access.model_dump(mode="json"):
            raise HTTPException(status_code=403, detail="This conversation is not available to this account")
        turn = next((turn for turn in doc["turns"] if turn["_id"] == str(turn_id)), None)
        if turn is None:
            raise HTTPException(status_code=404, detail="Turn not found")
        return access, turn

    @app.get("/v1/conversations/{conversation_id}/turns/{turn_id}")
    def get_turn(conversation_id: UUID, turn_id: UUID, user_id: str):
        _, turn = read_saved_turn(user_id, conversation_id, turn_id)
        return {key: turn[key] for key in ("elapsed_ms", "model_attempts", "cache")}

    @app.get("/v1/conversations/{conversation_id}/turns/{turn_id}/documents/{index}")
    def get_document(conversation_id: UUID, turn_id: UUID, index: int, user_id: str):
        access, turn = read_saved_turn(user_id, conversation_id, turn_id)
        documents = ((turn["response"] or {}).get("answer") or {}).get("documents", [])
        if index < 0 or index >= len(documents):
            raise HTTPException(status_code=404, detail="Document not found")
        document = documents[index]
        uri = urlparse(document["uri"])
        root = Path(os.getenv("FARO_DOCUMENT_PATH", Path(__file__).resolve().parents[4] / "local_data/source_documents"))
        path = Path(unquote(uri.path)).resolve()
        if uri.scheme != "file" or uri.netloc or not path.is_relative_to((root / access.company_id).resolve()):
            raise HTTPException(status_code=403, detail="Document is outside the permitted saved sources")
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Saved document is unavailable")
        if sha256(path.read_bytes()).hexdigest() != document["version"]:
            raise HTTPException(status_code=409, detail="Saved document has changed")
        return FileResponse(path, filename=document["name"])

    return app


app = create_app()
