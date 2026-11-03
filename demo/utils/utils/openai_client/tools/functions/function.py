import copy
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Function:
    name: str
    parameters: Dict[str, Any]
    strict: bool = True
    description: Optional[str] = None
 
    NAME = "name"
    DESCRIPTION = "description"
    PARAMETERS = "parameters"
    STRICT = "strict"
    PROPERTIES = "properties"
    ADDITIONAL_PROPERTIES = "additionalProperties"

    
    def _set_additional_properties_to_false(self, d):
        if isinstance(d, dict):
            if Function.PROPERTIES in d:
                d[Function.ADDITIONAL_PROPERTIES] = False
            
            # RECURSIVELY GO THROUGH THE DICTIONARY
            for key, value in d.items():
                self._set_additional_properties_to_false(value)
        
        elif isinstance(d, list):
            for item in d:
                self._set_additional_properties_to_false(item)
 
    def to_api_input(self):
        api_input = {Function.NAME: self.name,
                     Function.PARAMETERS: copy.deepcopy(self.parameters),
                     Function.STRICT: self.strict}
        
        if self.strict:
            self._set_additional_properties_to_false(api_input[Function.PARAMETERS])
            api_input[Function.PARAMETERS][Function.ADDITIONAL_PROPERTIES] = False
 
        if self.description:
            api_input[Function.DESCRIPTION] = self.description
        return api_input
