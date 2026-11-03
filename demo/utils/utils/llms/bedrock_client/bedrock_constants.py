from enum import Enum

class BedrockUrls:
    @staticmethod
    def openai(region_name: str) -> str:
        return f"https://bedrock-mantle.{region_name}.api.aws/openai/v1"


class BedrockModelName(str, Enum):
    ANTHROPIC_CLAUDE_4_6_SONNET = "us.anthropic.claude-sonnet-4-6"
    AMAZON_NOVA_PRO             = "us.amazon.nova-pro-v1:0"
    AMAZON_NOVA_2_LITE          = "us.amazon.nova-2-lite-v1:0"
    BEDROCK_OPENAI_GPT_5_4      = "openai.gpt-5.4"
    BEDROCK_OPENAI_GPT_5_5      = "openai.gpt-5.5"
    BEDROCK_OPENAI_GPT_5_6_SOL  = "openai.gpt-5.6-sol"
    BEDROCK_OPENAI_GPT_5_6_TERRA = "openai.gpt-5.6-terra"
    BEDROCK_OPENAI_GPT_5_6_LUNA = "openai.gpt-5.6-luna"
    BEDROCK_OPENAI_GPT_6_SOL   = "openai.gpt-6-sol"
    BEDROCK_OPENAI_GPT_6_1_SOL = "openai.gpt-6.1-sol"
    BEDROCK_OPENAI_GPT_6_LUNA  = "openai.gpt-6-luna"
    BEDROCK_OPENAI_GPT_6_ASTRA = "openai.gpt-6-astra"
    OPENAI_GPT_OSS_120B_1       = "openai.gpt-oss-120b-1:0"
    OPENAI_GPT_OSS_20B_1        = "openai.gpt-oss-20b-1:0"
    OPENAI_GPT_OSS_SAFEGUARD_20B = "openai.gpt-oss-safeguard-20b"
    OPENAI_GPT_OSS_SAFEGUARD_120B = "openai.gpt-oss-safeguard-120b"
    META_LLAMA3_70B_INSTRUCT_V1 = "meta.llama3-70b-instruct-v1:0"
    MISTRAL_7B_INSTRUCT_V0      = 'mistral.mistral-7b-instruct-v0:2'
    META_LLAMA3_2_3B_INSTRUCT_V1 = "us.meta.llama3-2-3b-instruct-v1:0"
    WRITER_PALMYRA_X4_V1        = "us.writer.palmyra-x4-v1:0"
    DEEPSEEK_R1_V1              = "us.deepseek.r1-v1:0"
    KIMI25                      = "moonshotai.kimi-k2.5" 
    KIMI25_THINKING             = "moonshot.kimi-k2-thinking"   
    GROK_4_3                    = "xai.grok-4.3"


class BedrockChat:
    MODEL_NAME_TO_MAX_TOKENS = {
        BedrockModelName.BEDROCK_OPENAI_GPT_5_4: 272_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_5_5: 272_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_5_6_SOL: 272_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_5_6_TERRA: 272_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_5_6_LUNA: 272_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_6_SOL: 1_050_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_6_1_SOL: 1_050_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_6_LUNA: 1_050_000,
        BedrockModelName.BEDROCK_OPENAI_GPT_6_ASTRA: 1_050_000,
    }
 
