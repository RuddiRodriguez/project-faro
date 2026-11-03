from pydantic import BaseModel


class FileContent(BaseModel):
    file_url: str
