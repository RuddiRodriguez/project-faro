from pydantic import BaseModel, Field, validate_call

from ..openai_consts import ModelName as OpenAiModelName


class DecisionsConversation(BaseModel):
    llm_model_name: OpenAiModelName
    input_text: str
    questions: list[dict] = Field(default_factory=list)

    @validate_call
    def add_choice_question(self, name: str, instructions: str,
                            choices: list[dict]) -> None:
        self.questions.append({
            "type": "choice",
            "name": name,
            "instructions": instructions,
            "choices": choices,
        })

    @validate_call
    def add_predicate_question(self, name: str, instructions: str) -> None:
        self.questions.append({
            "type": "predicate",
            "name": name,
            "instructions": instructions,
        })

    def to_api_input(self) -> dict:
        return {
            "model": self.llm_model_name.value,
            "input": self.input_text,
            "questions": self.questions,
        }
