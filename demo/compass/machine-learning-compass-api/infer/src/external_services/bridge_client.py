from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.bridge.output.bridge_output import BridgeOutput
from api_objects.faro.gate.output.gate_output import GateOutput

class BridgeClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Bridge"

    def read_evidence(self, access: GateOutput, question) -> BridgeOutput:
        request = BridgeInput(question=question, company_id=access.company_id,
                              permitted_scope_ids=access.permitted_scope_ids)
        return call(self.service_name, self.base_url, "/v1/evidence", request, BridgeOutput, timeout=150)
