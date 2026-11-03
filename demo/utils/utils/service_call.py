from utils.llms.model_attempts import turn_context
import httpx
from pydantic import ValidationError


def call(service_name, base_url, endpoint_path, api_input, response_object_type, timeout):
    try:
        context = turn_context.get()
        headers = {"x-faro-company": context[0], "x-faro-turn": context[1]} if context else {}
        response = httpx.post(f"{base_url}{endpoint_path}", json=api_input.model_dump(mode="json"),
                              headers=headers, timeout=timeout, follow_redirects=False)
        if service_name == "Gate" and response.status_code == 403:
            raise PermissionError("User not found or account is disabled")
        response.raise_for_status()
        return response_object_type.model_validate(response.json())
    except (httpx.HTTPError, ValueError) as error:
        reason = type(error).__name__
        if isinstance(error, httpx.HTTPStatusError):
            reason = f"HTTP {error.response.status_code}"
        elif isinstance(error, ValidationError):
            reason = ", ".join(".".join(map(str, e["loc"])) + ": " + e["type"] for e in error.errors())
        error.add_note(f"{service_name} {endpoint_path}: {reason}")
        raise
