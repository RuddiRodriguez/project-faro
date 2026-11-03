from typing import Literal
from api_objects.faro.thread.input.turn_input import Detail
from api_objects.faro.thread.output.thread_output import ThreadOutput


class TurnOutput(ThreadOutput):
    current_request: dict[Detail, str]
    intent: Literal["request", "unsupported"]
