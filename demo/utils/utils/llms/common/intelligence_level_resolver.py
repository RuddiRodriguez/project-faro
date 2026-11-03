from __future__ import annotations

from .intelligence_level import IntelligenceLevel, ModelNameKey
from ...openai_client.conversation.conversation import Conversation


def resolve_intelligence_level(conversation: Conversation,
                               intelligence_level: IntelligenceLevel | None = None,
                               reasoning_effort: str | None = None,
                               verbosity: str | None = None,
                               model_key: ModelNameKey | None = None) -> tuple[Conversation, str | None, str | None]:
    if conversation.intelligence_level is not None:
        if intelligence_level is not None:
            raise ValueError("intelligence_level cannot be supplied on both Conversation and predict")
        intelligence_level = conversation.intelligence_level
    elif intelligence_level is not None and conversation.llm_model_name is not None:
        raise ValueError("intelligence_level cannot be combined with llm_model_name")
    if intelligence_level is not None:
        if reasoning_effort is not None or verbosity is not None:
            raise ValueError("intelligence_level cannot be combined with reasoning_effort or verbosity")
        settings = intelligence_level.settings
        update_conversation = {"llm_model_name": settings[model_key], "intelligence_level": None}
        conversation = conversation.model_copy(update=update_conversation)
        reasoning_effort = settings["reasoning_effort"]
        verbosity = settings["verbosity"]
    elif conversation.llm_model_name is None:
        raise ValueError("Either llm_model_name or intelligence_level must be provided")
    return conversation, reasoning_effort, verbosity
