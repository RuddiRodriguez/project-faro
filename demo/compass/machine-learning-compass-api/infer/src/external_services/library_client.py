from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.gate.output.gate_output import GateOutput
from api_objects.faro.library.input.library_input import LibraryInput
from api_objects.faro.library.output.library_output import LibraryOutput


class LibraryClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Library"

    def read_company_information(self, access: GateOutput) -> LibraryOutput:
        request = LibraryInput(company_id=access.company_id,
                               permitted_scope_ids=access.permitted_scope_ids)
        return call(self.service_name, self.base_url, "/v1/company-information", request, LibraryOutput, timeout=10)
