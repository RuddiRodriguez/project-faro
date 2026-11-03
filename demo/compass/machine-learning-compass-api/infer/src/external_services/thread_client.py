from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.thread.input.thread_input import ThreadInput, ConversationMessage
from api_objects.faro.thread.output.thread_output import ThreadOutput




class ThreadClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Thread"

    def rewrite_question(self, question: str, conversation) -> ThreadOutput:
        request = ThreadInput(question=question,
                              conversation=[ConversationMessage(role=message.role, content=message.content)
                                            for message in conversation])
        return call(self.service_name, self.base_url, "/v1/rewrite", request, ThreadOutput, timeout=100)
