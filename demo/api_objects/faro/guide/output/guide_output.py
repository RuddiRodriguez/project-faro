from pydantic import BaseModel


class GuideOutput(BaseModel):
    initial_analysis: str | None = None
    reasoning: str | None = None
    followup_text: str
