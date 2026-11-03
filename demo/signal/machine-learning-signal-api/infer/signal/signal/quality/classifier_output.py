from pydantic import BaseModel

from faro_signal.common_tools.error_code import ErrorCode
from faro_signal.classifier_output import ClassifierOutput
from utils.openai_client.outputs.token_usage import TokenUsage


class ClassifierOutput(BaseModel):
    result: ClassifierOutput | None = None
    token_usage: TokenUsage | None = None
    llm_duration: float | None = None
    decisions_response: dict | None = None
    error_code: ErrorCode | None = None
    error_message: str | None = None

    @property
    def is_success(self) -> bool:
        return self.result is not None and self.error_code is None and self.error_message is None
