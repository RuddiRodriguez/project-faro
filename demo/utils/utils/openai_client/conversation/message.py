from typing import List, Union

from pydantic import BaseModel
from ..openai_consts import Role
from ..openai_consts import Message as MessageConsts
from ..conversation.image_content import ImageContent
from ...llms.common.prompt_cache import PROMPT_CACHE_MARKING, explicit_prompt_cache_breakpoint
from ..conversation.file_content import FileContent


class Message(BaseModel):
    role: Role
    content: Union[str, List[Union[str, ImageContent, FileContent]]]

    def has_prompt_cache_marking(self) -> bool:
        if self.role != Role.USER:
            return False

        if isinstance(self.content, str):
            return PROMPT_CACHE_MARKING in self.content

        return any(
            PROMPT_CACHE_MARKING in entry
            for entry in self.content
            if isinstance(entry, str)
        )

    def content_without_prompt_cache_marking(self):
        if self.role != Role.USER:
            return self.content

        if isinstance(self.content, str):
            return self.content.replace(PROMPT_CACHE_MARKING, "")

        return [
            entry.replace(PROMPT_CACHE_MARKING, "") if isinstance(entry, str) else entry
            for entry in self.content
        ]

    @staticmethod
    def _get_image_url(entry: ImageContent) -> str:
        if entry.load_from_disk:
            base64_image = ImageContent.encode_image(entry.image_url)
            return f'data:image/jpeg;base64,{base64_image}'

        return entry.image_url

    def to_api_input(self):
        content = self.content_without_prompt_cache_marking()
        if isinstance(content, list) and any(isinstance(entry, FileContent) for entry in content):
            raise ValueError("FileContent requires the Responses API.")
        if isinstance(content, str):
            open_ai_content = content
        else:
            open_ai_content = []
            for entry in content:
                if isinstance(entry, str):
                    open_ai_content.append({"type": "text", "text": entry})
                elif isinstance(entry, ImageContent):
                    url = self._get_image_url(entry)
                    open_ai_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                            "detail": entry.detail
                        }
                    })

        return {
            MessageConsts.ROLE_KEY: self.role.value,
            MessageConsts.CONTENT_KEY: open_ai_content
        }

    def to_responses_api_input(self):
        entries = [self.content] if isinstance(self.content, str) else self.content

        open_ai_content = []
        for entry in entries:
            if isinstance(entry, ImageContent):
                open_ai_content.append({
                    "type": "input_image",
                    "image_url": self._get_image_url(entry),
                    "detail": entry.detail.value
                })
                continue

            if isinstance(entry, FileContent):
                open_ai_content.append({"type": "input_file", "file_url": entry.file_url})
                continue

            if PROMPT_CACHE_MARKING in entry:
                segments = entry.split(PROMPT_CACHE_MARKING)

                for index, segment in enumerate(segments):
                    open_ai_content.append({"type": "input_text", "text": segment})

                    if index == len(segments) - 1:
                        continue

                    open_ai_content[-1]["prompt_cache_breakpoint"] = explicit_prompt_cache_breakpoint()
            else:
                open_ai_content.append({"type": "input_text", "text": entry})
        return {
            MessageConsts.ROLE_KEY: self.role.value,
            MessageConsts.CONTENT_KEY: open_ai_content
        }
