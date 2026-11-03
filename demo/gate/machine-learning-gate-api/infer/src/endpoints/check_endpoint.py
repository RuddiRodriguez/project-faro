from api_objects.faro.gate.input.gate_input import GateInput as ApiAccessCheckerInput
from api_objects.faro.gate.output.gate_output import GateOutput as ApiAccessCheckerOutput
from gate.access_checker import AccessChecker
from gate.access_checker_input import AccessCheckerInput as LibAccessCheckerInput


class AccessCheckerEndpoint:
    def __init__(self, access_checker: AccessChecker):
        self.access_checker = access_checker

    def handle(self, api_input: ApiAccessCheckerInput) -> ApiAccessCheckerOutput:
        access_checker_input = LibAccessCheckerInput(user_id=api_input.user_id)
        result = self.access_checker.check(access_checker_input)
        return ApiAccessCheckerOutput(user_id=result.user_id,
                                  company_id=result.company_id,
                                  permitted_scope_ids=result.permitted_scope_ids,
                                  permission_version=result.permission_version)
