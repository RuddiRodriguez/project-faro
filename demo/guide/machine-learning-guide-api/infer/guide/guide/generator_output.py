from pydantic import BaseModel


class GeneratorOutput(BaseModel):
    initial_analysis: str | None = None
    reasoning: str | None = None
    followup_text: str
