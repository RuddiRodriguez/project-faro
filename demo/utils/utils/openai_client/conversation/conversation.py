from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_serializer, validate_call


from ..conversation.assistant_message import AssistantMessage
from ..conversation.system_message import SystemMessage
from ..conversation.user_message import UserMessage
from ...llms.bedrock_client.bedrock_constants import BedrockModelName
from ...llms.common.intelligence_level import IntelligenceLevel
from ..openai_consts import ModelName as OpenAiModelName 
from ..openai_utils import OpenAiUtils

class Conversation(BaseModel):
    intelligence_level: IntelligenceLevel | None = None
    llm_model_name: OpenAiModelName | BedrockModelName | None = Field(default=None, validate_default=True)
    fallback_llm_model_name: OpenAiModelName | BedrockModelName | None = None
    system_message: SystemMessage
    messages: list[UserMessage | AssistantMessage] = Field(default_factory=list)

    @field_validator("llm_model_name")
    @classmethod
    def resolve_intelligence_level(cls, model_name: OpenAiModelName | BedrockModelName | None,
                                  info: ValidationInfo) -> OpenAiModelName | BedrockModelName | None:
        intelligence_level = info.data.get("intelligence_level")
        if intelligence_level is not None:
            if model_name is not None:
                raise ValueError("intelligence_level cannot be combined with llm_model_name")
            return intelligence_level.settings["model_name"]
        return model_name

    @model_serializer(mode="wrap")
    def serialize_conversation(self, serialize):
        data = serialize(self)
        # Persist the level without its derived model so it can be resolved again on load.
        if data.get("intelligence_level") is not None:
            data.pop("llm_model_name", None)
        return data


    @validate_call
    def add_message(self, new_message: UserMessage | AssistantMessage):
        self.messages.append(new_message)

    @validate_call
    def add_messages(self, new_messages: list[UserMessage | AssistantMessage]):
        self.messages.extend(new_messages)

    @validate_call
    def prepend_message(self, new_message: list[UserMessage | AssistantMessage]):
        self.messages.insert(0, new_message)

    def pop_message(self):
        return self.messages.pop()

    def to_api_input(self):
        return [self.system_message.to_api_input()] + [m.to_api_input() for m in self.messages]

    def has_prompt_cache_marking(self) -> bool:
        return any(
            message.has_prompt_cache_marking()
            for message in self.messages
        )

    def get_tokens_amount(self) -> int:
        system_message_tokens_amount = OpenAiUtils.count_tokens(text=self.system_message.content,
                                                                model_name=self.llm_model_name)
        user_messages_tokens_amount = sum([OpenAiUtils.count_tokens(text=m.content,
                                                                    model_name=self.llm_model_name)
                                           for m in self.messages])

        return system_message_tokens_amount + user_messages_tokens_amount
    
    def __add__(self, other):
        if not isinstance(other, Conversation):
            return NotImplemented

        if self.llm_model_name != other.llm_model_name or self.intelligence_level != other.intelligence_level:
            raise ValueError("Cannot add conversations with different model names or intelligence levels")

        return Conversation(
            llm_model_name=self.llm_model_name if self.intelligence_level is None else None,
            intelligence_level=self.intelligence_level,
            system_message=self.system_message,
            messages=self.messages + other.messages
        )

