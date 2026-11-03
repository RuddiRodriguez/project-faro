from api_objects.faro.connector.input.connector_input import ConnectorInput
from api_objects.faro.connector.output.connector_output import ConnectorOutput
from compass_api.external_services.http_caller_with_exception_on_error import call


class ConnectorClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def discover_sources(self, access):
        request = ConnectorInput(company_id=access.company_id,
                                 permitted_scope_ids=access.permitted_scope_ids, action="discover")
        return call("Connector", self.base_url, "/v1/sources", request, ConnectorOutput, timeout=15)
