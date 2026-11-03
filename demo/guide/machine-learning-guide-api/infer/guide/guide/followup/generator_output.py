from pydantic import BaseModel
from guide.common_tools.error_code import ErrorCode



class GeneratorOutput(BaseModel):
    initial_analysis: str | None = None

    followup_text: str | None
    followup_reasoning: str | None
    error_code: None | ErrorCode

    @property
    def is_success(self):
        return self.error_code is None
