from __future__ import annotations

from enum import StrEnum

from ..bedrock_client.bedrock_constants import BedrockModelName
from ...openai_client.openai_consts import ModelName


class ModelNameKey(StrEnum):
    MODEL_NAME = "model_name"
    BEDROCK_MODEL_NAME = "bedrock_model_name"


class IntelligenceLevel(StrEnum):
    """Simple choices for how much time and effort AI spends on a task."""

    YOLO = "YOLO"
    MINIMAL = "MINIMAL"
    LIGHT = "LIGHT"
    STANDARD = "STANDARD"
    ENHANCED = "ENHANCED"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"
    DEEP = "DEEP"
    MAXIMUM = "MAXIMUM"

    @property
    def settings(self) -> dict[str, str]:
        return {self.YOLO: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_LUNA,
                            ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_LUNA,
                            "reasoning_effort": "none",
                            "verbosity": "low"},
                self.MINIMAL: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_LUNA,
                               ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_LUNA,
                               "reasoning_effort": "low",
                               "verbosity": "low"},
                self.LIGHT: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_LUNA,
                             ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_LUNA,
                             "reasoning_effort": "medium",
                             "verbosity": "low"},
                self.STANDARD: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_LUNA,
                                ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_LUNA,
                                "reasoning_effort": "high",
                                "verbosity": "low"},
                self.ENHANCED: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_1_SOL,
                                ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_1_SOL,
                                "reasoning_effort": "low",
                                "verbosity": "low"},
                self.ADVANCED: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_1_SOL,
                                ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_1_SOL,
                                "reasoning_effort": "medium",
                                "verbosity": "low"},
                self.EXPERT: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_1_SOL,
                              ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_1_SOL,
                              "reasoning_effort": "high",
                              "verbosity": "low"},
                self.DEEP: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_1_SOL,
                            ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_1_SOL,
                            "reasoning_effort": "xhigh",
                            "verbosity": "medium"},
                self.MAXIMUM: {ModelNameKey.MODEL_NAME: ModelName.GPT_6_ASTRA,
                               ModelNameKey.BEDROCK_MODEL_NAME: BedrockModelName.BEDROCK_OPENAI_GPT_6_ASTRA,
                               "reasoning_effort": "high",
                               "verbosity": "high"}}[self]
