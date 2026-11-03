from pydantic import BaseModel, ConfigDict

from faro_signal.classifier_input import Passage


class ClassifierInput(BaseModel):
    question: str
    matches: list[Passage]
    connected_sources: list[str] = []
    permitted_scopes: list[str]

    model_config = ConfigDict(frozen=True, extra="forbid")
