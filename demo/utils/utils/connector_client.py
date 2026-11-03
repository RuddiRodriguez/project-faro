import os
import httpx
from api_objects.faro.connector.input.connector_input import ConnectorInput
from api_objects.faro.connector.output.connector_output import ConnectorOutput
from utils.service_call import call


def sources(company, scopes, action="discover", item=None):
    url=os.environ["FARO_CONNECTOR_URL"]
    request=ConnectorInput(company_id=company,permitted_scope_ids=scopes,action=action,item=item)
    try:
        return call("Connector",url,"/v1/sources",request,ConnectorOutput,timeout=15)
    except httpx.HTTPStatusError as error:
        if error.response.status_code==403:
            raise PermissionError("Connected item is outside the permitted scope.") from error
        if error.response.status_code==422:
            raise ValueError(error.response.json()["detail"]) from error
        raise
