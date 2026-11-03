from pydantic import BaseModel
from api_objects.faro.thread.input.turn_input import Change


class GuideOutput(BaseModel):
    proposed_changes: list[Change] = []
    followup_text: str
