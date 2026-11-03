import base64
from ..openai_consts import ImageDetailLevel

from pydantic import BaseModel

class ImageContent(BaseModel):
    image_url: str
    detail: ImageDetailLevel = ImageDetailLevel.AUTO
    load_from_disk: bool = False

    @staticmethod
    def encode_image(image_path: str) -> str:
        """Encodes an image from a file path to a base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')