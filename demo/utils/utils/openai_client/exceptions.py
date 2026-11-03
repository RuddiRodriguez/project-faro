from abc import ABC


class OpenAiError(Exception, ABC):

    def __init__(self, cause_exception=None):
        self.cause_exception = cause_exception

    def _add_cause_to_message(self, message):
        if self.cause_exception is not None:
            return f"{message} caused by {repr(self.cause_exception)}"
        return message


class OpenAiRecoverableError(OpenAiError):
    def __init__(self, cause_exception=None):
        super().__init__(cause_exception=cause_exception)

    def __str__(self):
        return self._add_cause_to_message("Open AI recoverable error")


class OpenAiUnRecoverableError(OpenAiError):
    def __init__(self, cause_exception=None):
        super().__init__(cause_exception=cause_exception)

    def __str__(self):
        return self._add_cause_to_message("Open AI unrecoverable error")


class OpenAIGeneralError(OpenAiError):
    def __init__(self, cause_exception=None):
        super().__init__(cause_exception=cause_exception)

    def __str__(self):
        return self._add_cause_to_message("Open AI general error")
 