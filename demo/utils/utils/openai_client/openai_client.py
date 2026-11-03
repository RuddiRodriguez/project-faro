import json
from typing import Any, Dict, List, Optional, Union

import openai
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from typing_extensions import Literal

from ..llms.common.intelligence_level import IntelligenceLevel, ModelNameKey
from ..llms.common.intelligence_level_resolver import resolve_intelligence_level
from ..llms.common.prompt_cache import explicit_prompt_cache_options
from ..llms.common.structured_output import StructuredOutput
from .conversation.decisions_conversation import DecisionsConversation
from .conversation.system_message import SystemMessage
from .conversation.user_message import UserMessage
from .conversation.file_content import FileContent
from .conversation.assistant_message import AssistantMessage
from .conversation.conversation import Conversation
from .exceptions import OpenAiRecoverableError, OpenAiUnRecoverableError, OpenAIGeneralError
from .openai_consts import ResponsesApiStatus, ModelName, Temperature
from .outputs.predict_output import PredictOutput
from .outputs.token_usage import CompletionTokensDetails, TokenUsage, PromptTokensDetails
from .tools.functions.assistant_function import AssistantFunction
from .tools.user_tool import UserTool
from .tools.functions.user_function import UserFunction
from .tools.functions.function import Function


class OpenAiClient:
    REASONING_MODELS = {
        ModelName.GPT_5_2025_08_07,
        ModelName.GPT_5_NANO_2025_08_07,
        ModelName.GPT_5_MINI_2025_08_07,
        ModelName.GPT_5_2_2025_12_11,
        ModelName.GPT_5_4_2026_03_05,
        ModelName.GPT_5_4_MINI_2026_03_17,
        ModelName.GPT_5_4_NANO_2026_03_17,
        ModelName.GPT_5_6_SOL,
        ModelName.GPT_5_6_TERRA,
        ModelName.GPT_5_6_LUNA,
        ModelName.GPT_6_SOL,
        ModelName.GPT_6_1_SOL,
        ModelName.GPT_6_LUNA,
        ModelName.GPT_6_ASTRA,
    }

    @staticmethod
    def flash_model(model_in: ModelName) -> ModelName:
        if "gpt-5" in model_in or "gpt-6" in model_in:
            return ModelName.GPT_5_4_NANO_2026_03_17
        
        if "gpt-4" in model_in:
            return ModelName.GPT_4_1_NANO_2025_04_14
        
        return model_in

    DEEP_RESEARCH_MODELS = {
        ModelName.O3_DEEP_RESEARCH_2025_06_26,
        ModelName.O4_MINI_DEEP_RESEARCH_2025_06_26,
    }

    def __init__(self, api_key_secret_name: Optional[str],
                 explicit_api_key: Optional[str] = None,
                 base_url: Optional[str] = None):

        if (api_key_secret_name is None and explicit_api_key is None) or \
            (api_key_secret_name is not None and explicit_api_key is not None):
            raise ValueError("Exactly one of api_key_secret_name or explicit_api_key must be provided")

        if api_key_secret_name is not None:
            from cloud.secrets_client import SecretsClient
            api_key_secret = SecretsClient().get_secret_value_as_dict(api_key_secret_name)
            client_kwargs = {
                "api_key": api_key_secret.get("api_key"),
                "organization": api_key_secret.get("org"),
                "max_retries": 0,
            }
        
        elif explicit_api_key is not None:
            client_kwargs = {
                "api_key": explicit_api_key,
                "max_retries": 0,
            }

        if base_url is not None:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)

    # --------------------[CHAT]--------------------- #

    def _try_fix_json(self, bad_json_string: str, timeout:float) -> str:
        SYSTEM  = """You are a JSON fixer.""" 
        USER    = "The bad JSON:\n```\n{json_string}\n```"
        FIXED_JSON_KEY = 'cleaned_json'
        FUNCTION = Function(name="bad_json_handler",
                            description="Fixes a bad JSON.",
                            parameters= {
                                            "type": "object",
                                            "properties": {
                                                FIXED_JSON_KEY: {
                                                    "type": "string",
                                                    "description": "The cleaned JSON.",
                                                    },
                                                },
                                            "required": [FIXED_JSON_KEY],
                                        }
                            )
        system_message = SystemMessage(content=SYSTEM)
        conversation = Conversation(llm_model_name=ModelName.GPT_5_4_MINI_2026_03_17, system_message=system_message)
        conversation.add_message(UserMessage(content=USER.format(json_string=bad_json_string)))
        tools = [UserFunction(function=FUNCTION)]
        try:
            result = self.chat_predict(conversation, 
                                        reasoning_effort="none",
                                        verbosity="low",
                                        tools=tools, 
                                        tool_choice={'type':'function', 'function':{'name':FUNCTION.name}},
                                        timeout=timeout,
                                        enable_auto_fix_json=False)
        except Exception as ex:
            return bad_json_string

        if result.assistant_tools[0].is_valid:
            return result.assistant_tools[0].parsed_arguments[FIXED_JSON_KEY]
        
        return bad_json_string

    def _should_use_responses_api(self,
                                                 conversation: Conversation,
                                                 tools: Optional[List[UserTool]],
                                                 structured_output: Optional[StructuredOutput] = None) -> bool:
        return structured_output is not None or any(
            isinstance(entry, FileContent)
            for message in conversation.messages if isinstance(message.content, list)
            for entry in message.content
        ) or (
            conversation.llm_model_name in OpenAiClient.REASONING_MODELS and bool(tools)
        )

    @staticmethod
    def _validate_structured_output_tool_compatibility(
        tools: Optional[List[UserTool]],
        tool_choice: Union[Literal["none", "auto", "required"], Dict],
        structured_output: Optional[StructuredOutput],
    ) -> None:
        if structured_output is None:
            return

        if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            raise ValueError("structured_output cannot be used with function tool_choice.")

        for tool in tools or []:
            api_input = tool.to_api_input()
            if api_input.get("type") == "function":
                raise ValueError("structured_output cannot be used with function tools.")

    def _build_token_usage(self, usage: Any) -> Optional[TokenUsage]:
        if usage is None:
            return None

        prompt_tokens = getattr(usage, "prompt_tokens", None)
        if prompt_tokens is None:
            prompt_tokens = getattr(usage, "input_tokens", None)

        completion_tokens = getattr(usage, "completion_tokens", None)
        if completion_tokens is None:
            completion_tokens = getattr(usage, "output_tokens", None)

        if prompt_tokens is None or completion_tokens is None:
            return None

        prompt_tokens_details_raw = getattr(usage, "prompt_tokens_details", None)
        if prompt_tokens_details_raw is None:
            prompt_tokens_details_raw = getattr(usage, "input_tokens_details", None)

        prompt_tokens_details = None
        if prompt_tokens_details_raw is not None:
            prompt_tokens_details = PromptTokensDetails(
                audio_tokens=getattr(prompt_tokens_details_raw, "audio_tokens", None),
                cached_tokens=getattr(prompt_tokens_details_raw, "cached_tokens", None),
                cache_write_tokens=getattr(prompt_tokens_details_raw, "cache_write_tokens", None),
            )

        completion_tokens_details_raw = getattr(usage, "completion_tokens_details", None)
        if completion_tokens_details_raw is None:
            completion_tokens_details_raw = getattr(usage, "output_tokens_details", None)

        completion_tokens_details = None
        if completion_tokens_details_raw is not None:
            completion_tokens_details = CompletionTokensDetails(
                accepted_prediction_tokens=getattr(completion_tokens_details_raw, "accepted_prediction_tokens", None),
                audio_tokens=getattr(completion_tokens_details_raw, "audio_tokens", None),
                reasoning_tokens=getattr(completion_tokens_details_raw, "reasoning_tokens", None),
                rejected_prediction_tokens=getattr(completion_tokens_details_raw, "rejected_prediction_tokens", None)
            )

        return TokenUsage(completion_tokens=completion_tokens,
                          prompt_tokens=prompt_tokens,
                          prompt_tokens_details=prompt_tokens_details,
                          completion_tokens_details=completion_tokens_details)

    def _build_assistant_function(self,
                                  name: str,
                                  raw_arguments: str,
                                  timeout: float,
                                  enable_auto_fix_json: bool) -> AssistantFunction:
        assistant_function = AssistantFunction(name=name,
                                               raw_arguments=raw_arguments)

        if enable_auto_fix_json and not assistant_function.is_valid:
            possibly_fixed_json = self._try_fix_json(bad_json_string=raw_arguments,
                                                     timeout=timeout)
            assistant_function = AssistantFunction(name=name,
                                                   raw_arguments=possibly_fixed_json)

        return assistant_function


    def _execute_chat_predict(self,
                              conversation: Conversation,
                              temperature: float | None,
                              tools: Optional[List[UserTool]],
                              tool_choice: Union[Literal["none", "auto", "required"], Dict],
                              timeout: float,
                              reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None,
                              verbosity: Literal["low", "medium", "high"] | None,
                              service_tier: Literal["auto", "default", "flex", "priority"] | None,
                              enable_auto_fix_json: bool,
                              parallel_tool_calls: bool,
                              structured_output: Optional[StructuredOutput],
                              prompt_cache_hint: str | None) -> PredictOutput:
        self._validate_structured_output_tool_compatibility(tools=tools, tool_choice=tool_choice, structured_output=structured_output)
        should_use_responses_api = self._should_use_responses_api(
            conversation=conversation,
            tools=tools,
            structured_output=structured_output,
        )
        if structured_output is not None and not should_use_responses_api:
            raise ValueError("structured_output is only supported with Responses API models.")

        if should_use_responses_api:
            return self._responses_api_chat_predict(conversation=conversation,
                                                    tools=tools,
                                                    tool_choice=tool_choice,
                                                    timeout=timeout,
                                                    reasoning_effort=reasoning_effort,
                                                    verbosity=verbosity,
                                                    service_tier=service_tier,
                                                    enable_auto_fix_json=enable_auto_fix_json,
                                                    structured_output=structured_output,
                                                    parallel_tool_calls=parallel_tool_calls,
                                                    prompt_cache_hint=prompt_cache_hint)

        return self._completions_api_chat_predict(conversation=conversation,
                                                  temperature=temperature,
                                                  tools=tools,
                                                  tool_choice=tool_choice,
                                                  timeout=timeout,
                                                  reasoning_effort=reasoning_effort,
                                                  verbosity=verbosity,
                                                  enable_auto_fix_json=enable_auto_fix_json,
                                                  parallel_tool_calls=parallel_tool_calls)

    def _responses_api_chat_predict(self,
                                    conversation: Conversation,
                                    tools: Optional[List[UserTool]],
                                    tool_choice: Union[Literal["none", "auto", "required"], Dict],
                                    timeout: float,
                                    reasoning_effort: Literal["none" , "low" , "medium" , "high" , "xhigh"] | None,
                                    verbosity: Literal["low", "medium", "high"] | None,
                                    service_tier: Literal["auto", "default", "flex", "priority"] | None,
                                    enable_auto_fix_json: bool,
                                    structured_output: Optional[StructuredOutput],
                                    parallel_tool_calls: bool = False,
                                    prompt_cache_hint: str | None = None,
                                    store: bool | None = None) -> PredictOutput:
        self._validate_structured_output_tool_compatibility(tools=tools, tool_choice=tool_choice, structured_output=structured_output)
        responses_api_tool_choice: Union[str, Dict] = tool_choice
        if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            function_config = tool_choice.get("function")
            if isinstance(function_config, dict):
                responses_api_tool_choice = dict(function_config)
                responses_api_tool_choice["type"] = "function"

        responses_api_params = {
            "model": conversation.llm_model_name,
            "input": [message.to_responses_api_input() for message in conversation.messages],
            "timeout": timeout
        }

        responses_api_params["instructions"] = conversation.system_message.content

        if store is not None:
            responses_api_params["store"] = store

        if prompt_cache_hint is not None:
            responses_api_params["prompt_cache_key"] = prompt_cache_hint

        if conversation.has_prompt_cache_marking():
            responses_api_params["extra_body"] = {
                "prompt_cache_options": explicit_prompt_cache_options(),
            }

        if tools:
            responses_api_params["tools"] = []
            responses_api_params["tool_choice"] = responses_api_tool_choice
            responses_api_params["parallel_tool_calls"] = parallel_tool_calls
            for tool in tools:
                api_input = tool.to_api_input()
                if api_input.get("type") == "function":
                    function_config = api_input.get("function")
                    responses_api_input = dict(function_config)
                    responses_api_input["type"] = "function"
                    responses_api_params["tools"].append(responses_api_input)
                    continue

                responses_api_params["tools"].append(api_input)

        if reasoning_effort is not None:
            responses_api_params["reasoning"] = {"effort": reasoning_effort}

        if service_tier is not None:
            responses_api_params["service_tier"] = service_tier

        text_config = {}
        if verbosity is not None:
            text_config["verbosity"] = verbosity

        if structured_output is not None:
            text_config["format"] = structured_output.to_api_input()

        if text_config:
            responses_api_params["text"] = text_config

        response = self.client.responses.create(**responses_api_params)

        # if service_tier is not None:
        #     print(
        #         f"##### - [OpenAiClient][Responses API] requested service_tier={service_tier}, "
        #         f"applied service_tier={getattr(response, 'service_tier', None)}"
        #     )

        if getattr(response, "status", None) != ResponsesApiStatus.COMPLETED:
            return PredictOutput(input_conversation=conversation,
                                 assistant_message=None,
                                 assistant_tools=None,
                                 finish_reason=None,
                                 token_usage=self._build_token_usage(getattr(response, "usage", None)))

        assistant_message = None
        output_text = getattr(response, "output_text", None)
        if output_text:
            assistant_message = AssistantMessage(content=output_text.strip())

        assistant_tools = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "function_call":
                continue

            raw_arguments = getattr(item, "arguments", "")
            if not isinstance(raw_arguments, str):
                raw_arguments = json.dumps(raw_arguments)

            assistant_tools.append(self._build_assistant_function(name=getattr(item, "name", ""),
                                                                  raw_arguments=raw_arguments,
                                                                  timeout=timeout,
                                                                  enable_auto_fix_json=enable_auto_fix_json))

        if structured_output is not None and assistant_message is not None:
            assistant_tools.append(self._build_assistant_function(name=structured_output.name,
                                                                  raw_arguments=assistant_message.content,
                                                                  timeout=timeout,
                                                                  enable_auto_fix_json=enable_auto_fix_json))

        finish_reason = "tool_calls" if structured_output is None and len(assistant_tools) > 0 else "stop"


        return PredictOutput(input_conversation=conversation,
                             assistant_message=assistant_message,
                             assistant_tools=assistant_tools if len(assistant_tools) > 0 else None,
                             finish_reason=finish_reason,
                             token_usage=self._build_token_usage(getattr(response, "usage", None)))

    def _completions_api_chat_predict(self,
                                      conversation: Conversation,
                                      temperature: float | None,
                                      tools: Optional[List[UserTool]],
                                      tool_choice: Union[Literal["none", "auto", "required"], Dict],
                                      timeout: float,
                                      reasoning_effort: Literal["minimal", "low", "medium", "high", "xhigh"] | None,
                                      verbosity: Literal["low", "medium", "high"] | None,
                                      enable_auto_fix_json: bool,
                                      parallel_tool_calls: bool) -> PredictOutput:
        common_params = {
            "model": conversation.llm_model_name,
            "messages": conversation.to_api_input(),
            "timeout": timeout
        }

        if tools is not None:
            common_params.update({
                "tools": [tool.to_api_input() for tool in tools],
                "tool_choice": tool_choice,
                "parallel_tool_calls": parallel_tool_calls
            })

        if conversation.llm_model_name in OpenAiClient.REASONING_MODELS:
            common_params.update({
                "reasoning_effort": reasoning_effort,
                "verbosity": verbosity
            })
        else:
            common_params["temperature"] = temperature

        result: ChatCompletion = self.client.chat.completions.create(**common_params)

        is_success = len(result.choices) > 0
        if not is_success:
            return PredictOutput(input_conversation=conversation,
                                 assistant_message=None,
                                 assistant_tools=None,
                                 finish_reason=None,
                                 token_usage=None)

        token_usage = self._build_token_usage(result.usage)

        choice = result.choices[0]              # IT IS [0] BECAUSE N IS SET TO 1 (the number of outputs to generate) BY DEFAULT.
        finish_reason = choice.finish_reason
        gpt_result: ChatCompletionMessage = choice.message

        assistant_message = None
        if gpt_result.content:
            assistant_message = AssistantMessage(content=gpt_result.content.strip())

        assistant_tools = list()
        if gpt_result.tool_calls is not None:
            for tool_call in gpt_result.tool_calls:
                if tool_call.function:
                    assistant_tools.append(self._build_assistant_function(name=tool_call.function.name,
                                                                          raw_arguments=tool_call.function.arguments,
                                                                          timeout=timeout,
                                                                          enable_auto_fix_json=enable_auto_fix_json))

        return PredictOutput(input_conversation=conversation,
                             assistant_message=assistant_message,
                             assistant_tools=assistant_tools if len(assistant_tools) > 0 else None,
                             finish_reason=finish_reason,
                             token_usage=token_usage)

    def _decisions_api_predict(self, conversation: DecisionsConversation, timeout: float) -> PredictOutput:
        response = self.client.with_options(timeout=timeout).decisions.create(**conversation.to_api_input())
        decisions_response = response.model_dump(exclude_unset=True)
        return PredictOutput(
            input_conversation=conversation,
            assistant_message=AssistantMessage(content=json.dumps(decisions_response["answers"])),
            assistant_tools=None,
            finish_reason=None,
            token_usage=self._build_token_usage(response.usage),
            decisions_response=decisions_response,
        )

    def chat_predict(self, conversation: Conversation,
                     temperature: float | None = None,
                     tools: List[UserTool] | None = None,
                     tool_choice: Union[Literal["none", "auto", "required"], Dict] = "auto",
                     timeout: float = 60.0,
                     reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None = None,
                     verbosity: Literal["low", "medium", "high"] | None = None,
                     enable_auto_fix_json: bool = False,
                     parallel_tool_calls: bool = False,
                     structured_output: StructuredOutput | None = None,
                     prompt_cache_hint: str | None = None,
                     service_tier: Literal["auto", "default", "flex", "priority"] | None = None,
                     intelligence_level: IntelligenceLevel | None = None,
                     ) -> PredictOutput:

        if isinstance(conversation, DecisionsConversation) and (
            temperature is not None or tools or tool_choice != "auto"
            or reasoning_effort is not None or verbosity is not None
            or enable_auto_fix_json or parallel_tool_calls or structured_output is not None
            or prompt_cache_hint is not None or service_tier is not None
        ):
            raise ValueError("DecisionsConversation supports only conversation and timeout options.")
        if not isinstance(conversation, DecisionsConversation):
            conversation, reasoning_effort, verbosity = resolve_intelligence_level(
                conversation=conversation.model_copy(deep=True),
                intelligence_level=intelligence_level,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity,
                model_key=ModelNameKey.MODEL_NAME,
            )
        #! START - TEMP MAPPING OF REASONING EFFORT LEVELS
        if conversation.llm_model_name in {ModelName.GPT_6_1_SOL, ModelName.GPT_6_ASTRA} and reasoning_effort in {"none", "minimal"}:
            reasoning_effort = "low"
        elif reasoning_effort == "minimal" and \
            conversation.llm_model_name in {
                ModelName.GPT_6_SOL,
                ModelName.GPT_6_LUNA,
                ModelName.GPT_5_4_2026_03_05,
                ModelName.GPT_5_4_MINI_2026_03_17,
                ModelName.GPT_5_4_NANO_2026_03_17,
                ModelName.GPT_5_6_SOL,
                ModelName.GPT_5_6_TERRA,
                ModelName.GPT_5_6_LUNA,
            }:
            reasoning_effort = "none"
        elif reasoning_effort == "none" and \
            conversation.llm_model_name not in {
                ModelName.GPT_6_SOL,
                ModelName.GPT_6_LUNA,
                ModelName.GPT_5_4_2026_03_05,
                ModelName.GPT_5_4_MINI_2026_03_17,
                ModelName.GPT_5_4_NANO_2026_03_17,
                ModelName.GPT_5_6_SOL,
                ModelName.GPT_5_6_TERRA,
                ModelName.GPT_5_6_LUNA,
            }:
            reasoning_effort = "minimal"
        #! END - TEMP MAPPING OF REASONING EFFORT LEVELS
        
        
        if conversation.llm_model_name in OpenAiClient.DEEP_RESEARCH_MODELS:
            raise ValueError("chat_predict cannot be used with Deep Research models. Use submit_deep_research and check_deep_research instead.")

        if temperature is not None and not (Temperature.LOWER_BOUND <= temperature <= Temperature.UPPER_BOUND):
            raise ValueError(f'{temperature=} out of range, must be between {Temperature.LOWER_BOUND} and {Temperature.UPPER_BOUND}')

        self._validate_structured_output_tool_compatibility(tools=tools, tool_choice=tool_choice, structured_output=structured_output)
        if structured_output is not None and not self._should_use_responses_api(
            conversation=conversation,
            tools=tools,
            structured_output=structured_output,
        ):
            raise ValueError("structured_output is only supported with Responses API models.")
        try:
            if isinstance(conversation, DecisionsConversation):
                return self._decisions_api_predict(conversation=conversation, timeout=timeout)
            return self._execute_chat_predict(conversation=conversation,
                                              temperature=temperature,
                                              tools=tools,
                                              tool_choice=tool_choice,
                                              timeout=timeout,
                                              reasoning_effort=reasoning_effort,
                                              verbosity=verbosity,
                                              service_tier=service_tier,
                                              enable_auto_fix_json=enable_auto_fix_json,
                                              parallel_tool_calls=parallel_tool_calls,
                                              structured_output=structured_output,
                                              prompt_cache_hint=prompt_cache_hint)
        except openai.APIConnectionError as error:
            raise OpenAiRecoverableError(cause_exception=error) from error
        except openai.APIStatusError as error:
            temporary = error.status_code in (408, 409, 429) or 500 <= error.status_code < 600
            if temporary and error.code != "insufficient_quota":
                raise OpenAiRecoverableError(cause_exception=error) from error
            raise OpenAiUnRecoverableError(cause_exception=error) from error
        except Exception as e:
            raise OpenAIGeneralError(cause_exception=e) from e

