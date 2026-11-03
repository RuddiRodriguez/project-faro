from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.library.output.library_output import LibraryOutput
from api_objects.faro.scout.output.scout_output import ScoutOutput
from api_objects.faro.signal.input.signal_input import SignalInput
from api_objects.faro.signal.output.signal_output import SignalOutput


class SignalClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Signal"

    def classify(self, search: ScoutOutput, information: LibraryOutput, unclear_references) -> SignalOutput:
        request = SignalInput(unclear_references=unclear_references, question=search.query, matches=search.matches,
                              connected_sources=[m.id for m in search.source_items], supported_tasks=information.supported_tasks, groups=information.groups,
                              permitted_scopes=[t.name for t in information.scopes])
        return call(self.service_name, self.base_url, "/v1/classify", request, SignalOutput, timeout=100)
