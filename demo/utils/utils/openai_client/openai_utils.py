import tiktoken
from .openai_consts import ModelName


class OpenAiUtils:
    TIKTIOKEN_UNSUPPORTED_MODELS = {
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

    def _get_encoding_for_model(model_name: ModelName | None):
        if model_name is None or model_name in OpenAiUtils.TIKTIOKEN_UNSUPPORTED_MODELS:
            model_name = ModelName.GPT_5_2025_08_07
        return tiktoken.encoding_for_model(model_name)

    @staticmethod
    def count_tokens(text: str, model_name: ModelName | None) -> int:
        encoding = OpenAiUtils._get_encoding_for_model(model_name)
        return len(encoding.encode(text))
    
    @staticmethod
    def tokenize(text: str, model_name: ModelName | None) -> list:
        encoding = OpenAiUtils._get_encoding_for_model(model_name)
        return encoding.encode(text)
    
    @staticmethod
    def decode_tokens(tokens: list, model_name: ModelName | None) -> str:
        encoding = OpenAiUtils._get_encoding_for_model(model_name)
        return encoding.decode(tokens)
