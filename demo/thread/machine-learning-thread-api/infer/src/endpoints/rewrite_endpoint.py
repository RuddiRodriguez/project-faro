from api_objects.faro.thread.input.thread_input import ThreadInput as ApiRewriterInput
from api_objects.faro.thread.output.thread_output import ThreadOutput as ApiRewriterOutput
from thread.rewriter import Rewriter
from thread.rewriter_input import RewriterInput as LibRewriterInput, ConversationMessage as LibConversationMessage


class RewriterEndpoint:
    def __init__(self, rewriter: Rewriter):
        self.rewriter = rewriter

    def handle(self, api_input: ApiRewriterInput) -> ApiRewriterOutput:
        rewriter_input = LibRewriterInput(question=api_input.question,
                                            conversation=[LibConversationMessage(role=message.role, content=message.content)
                                                          for message in api_input.conversation])
        result = self.rewriter.rewrite(rewriter_input)
        return ApiRewriterOutput(initial_analysis=result.initial_analysis, reasoning=result.reasoning, unclear_references=result.unclear_references, question=result.question,
                                  used_ai=result.used_ai,
                                  model_name=result.model_name,
                                  token_usage=result.token_usage)
