from pydantic import BaseModel
from api_objects.faro.scout.output.scout_output import SearchMatch


class BridgeInput(BaseModel):
    question: str
    company_id: str
    permitted_scope_ids: list[str]
    passages: list[SearchMatch] = []
