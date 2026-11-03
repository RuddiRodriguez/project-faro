from pydantic import BaseModel

from utils.openai_client.outputs.token_usage import TokenUsage


class RewriterOutput(BaseModel):
    initial_analysis: str | None = None
    reasoning: str | None = None
    unclear_references: list[str] = []
    question: str
    used_ai: bool
    model_name: str | None = None
    token_usage: TokenUsage | None = None
