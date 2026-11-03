from pydantic import BaseModel
from api_objects.faro.thread.input.turn_input import Change
from guide.common_tools.error_code import ErrorCode



class GeneratorOutput(BaseModel):

    proposed_changes: list[Change] = []
    followup_text: str | None
    followup_reasoning: str | None
    error_code: None | ErrorCode

    @property
    def is_success(self):
        return self.error_code is None
