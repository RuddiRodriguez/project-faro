from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.shield.input.shield_input import ShieldInput
from api_objects.faro.shield.output.shield_output import ShieldOutput
from api_objects.faro.bridge.output.bridge_output import BridgeOutput
from api_objects.faro.gate.output.gate_output import GateOutput
from api_objects.faro.library.output.library_output import LibraryOutput


class ShieldClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Shield"

    def verify_evidence(self, access: GateOutput, information: LibraryOutput, question, evidence: BridgeOutput) -> ShieldOutput:
        request = ShieldInput(evidence=evidence, question=question, company_id=access.company_id,
                              permitted_scope_ids=access.permitted_scope_ids,
                              definition_ids=[m.document_id for m in information.documents])
        return call(self.service_name, self.base_url, "/v1/verify", request, ShieldOutput, timeout=150)
