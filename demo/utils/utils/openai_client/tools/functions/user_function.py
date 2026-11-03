from dataclasses import dataclass

from .function import Function
from ..user_tool import UserTool
from typing_extensions import Literal

@dataclass(kw_only=True)
class UserFunction(UserTool):
    function: Function
    tool_type: Literal["function"] = "function"

    FUNCTION_KEY_NAME = "function"

    def to_api_input(self):
        api_input = {UserFunction.TYPE_KEY_NAME: self.tool_type, UserFunction.FUNCTION_KEY_NAME: self.function.to_api_input()} 
        return api_input
