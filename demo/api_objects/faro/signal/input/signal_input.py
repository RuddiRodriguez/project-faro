from pydantic import BaseModel

from api_objects.faro.scout.output.scout_output import SearchMatch


class SignalInput(BaseModel):
    unclear_references: list[str] = []
    question: str
    matches: list[SearchMatch]
    connected_sources: list[str] = []
    permitted_scopes: list[str]
