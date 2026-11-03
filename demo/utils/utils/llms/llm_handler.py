from __future__ import annotations


from .model_attempts import track_attempt, track_call
import backoff
import logging
from typing import Dict, List, Union
from typing_extensions import Literal

from .common.structured_output import StructuredOutput
from .common.intelligence_level import IntelligenceLevel
from .common.intelligence_level_resolver import resolve_intelligence_level
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bedrock_client.bedrock_client import BedrockClient
from .bedrock_client.bedrock_exceptions import BedRockUnRecoverableError
from ..openai_client.conversation.conversation import Conversation
from ..openai_client.exceptions import OpenAiRecoverableError
from ..openai_client.openai_client import OpenAiClient
from ..openai_client.tools.functions.function import Function
from ..openai_client.tools.functions.user_function import UserFunction

logging.getLogger('backoff').setLevel(logging.CRITICAL)


class LLMHandler:
    def __init__(self,llm_client: OpenAiClient | BedrockClient, fallback_client: OpenAiClient | BedrockClient | None = None ):
        if llm_client is None:
            raise ValueError("llm_client must be provided")

        self.llm_client = llm_client
        self.fallback_client = fallback_client
        
    def predict(
        self,
        conversation: Conversation,
        functions: List[Function] | None = None,
        structured_output: StructuredOutput | None = None,
        tool_choice: Union[Literal["none", "required", "auto"], Dict] = "auto",
        timeout: float = 60.0,
        enable_auto_fix_json=False,
        reasoning_effort: str | None = None,
        verbosity: str | None = None,
        parallel_tool_calls: bool = False,
        prompt_cache_hint: str | None = None,
        service_tier: Literal["auto", "default", "flex", "priority"] | None = None,
        intelligence_level: IntelligenceLevel | None = None, ):
        try:
            predict_output = self._llm_predict(
                llm_client=self.llm_client,
                conversation=conversation,
                functions=functions,
                structured_output=structured_output,
                tool_choice=tool_choice,
                timeout=timeout,
                enable_auto_fix_json=enable_auto_fix_json,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity,
                parallel_tool_calls=parallel_tool_calls,
                prompt_cache_hint=prompt_cache_hint,
                service_tier=service_tier,
                intelligence_level=intelligence_level,
            )
            if not predict_output.is_success and self.fallback_client is not None:
                raise RuntimeError("Primary LLM returned an unsuccessful result.")
            return predict_output
        except (BedRockUnRecoverableError, OpenAiRecoverableError):
            raise
        except Exception as e :
            if self.fallback_client is None or (
                conversation.fallback_llm_model_name is None and
                conversation.intelligence_level is None and
                intelligence_level is None
            ):
                raise

            logging.warning(f"LLM prediction failed with error: {repr(e)}. Falling back to fallback client and model.")
           
            fallback_conversation = conversation.model_copy(deep=True)
            fallback_conversation.llm_model_name = conversation.fallback_llm_model_name
            
            predict_output = self._llm_predict(
                llm_client=self.fallback_client,
                conversation=fallback_conversation,
                functions=functions,
                structured_output=structured_output,
                tool_choice=tool_choice,
                timeout=timeout,
                enable_auto_fix_json=enable_auto_fix_json,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity,
                parallel_tool_calls=parallel_tool_calls,
                prompt_cache_hint=prompt_cache_hint,
                service_tier=service_tier,
                intelligence_level=intelligence_level,
            )
            
            if not predict_output.is_success:
                logging.warning(
                    f"Fallback LLM prediction also failed. "
                    f"Original error: {repr(e)}. Raising original exception."
                )
                raise e
            return predict_output
        
            
    @track_call
    @backoff.on_exception(backoff.expo, OpenAiRecoverableError, max_tries=3)
    @track_attempt
    def _llm_predict(self, llm_client: OpenAiClient | BedrockClient, **kwargs):
        tools = [UserFunction(function=f) for f in kwargs["functions"]] if kwargs.get("functions") else None
        
        params = {
            "conversation": kwargs["conversation"],
            "timeout": kwargs["timeout"],
            "tools": tools,
            "tool_choice": kwargs["tool_choice"],
            "enable_auto_fix_json": kwargs.get("enable_auto_fix_json", False),
            "reasoning_effort": kwargs.get("reasoning_effort"),
            "verbosity": kwargs.get("verbosity"),
            "parallel_tool_calls": kwargs.get("parallel_tool_calls", False),
            "prompt_cache_hint": kwargs.get("prompt_cache_hint"),
            "intelligence_level": kwargs.get("intelligence_level"),
        }

        if kwargs.get("structured_output") is not None:
            params["structured_output"] = kwargs["structured_output"]

        if kwargs.get("service_tier") is not None:
            params["service_tier"] = kwargs["service_tier"]

        return llm_client.chat_predict(**params)
