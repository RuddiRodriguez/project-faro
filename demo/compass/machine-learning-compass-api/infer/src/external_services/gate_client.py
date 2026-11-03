from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.gate.input.gate_input import GateInput
from api_objects.faro.gate.output.gate_output import GateOutput


class GateClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Gate"

    def read_access(self, user_id: str) -> GateOutput:
        request = GateInput(user_id=user_id)
        return call(self.service_name, self.base_url, "/v1/access", request, GateOutput, timeout=10)
