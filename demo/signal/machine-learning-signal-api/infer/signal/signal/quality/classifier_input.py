from pydantic import BaseModel, ConfigDict

from faro_signal.predictor_input import Definition


class ClassifierInput(BaseModel):
    question: str
    matches: list[Definition]
    connected_sources: list[str] = []
    supported_tasks: list[str]
    groups: dict[str, list[str]] = {}
    permitted_scopes: list[str]

    model_config = ConfigDict(frozen=True, extra="forbid")
