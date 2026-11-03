from pydantic import BaseModel
from api_objects.faro.thread.input.turn_input import Change


class PredictorOutput(BaseModel):
    proposed_changes: list[Change] = []
    followup_text: str
