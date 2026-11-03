from typing import List

from transformers import AutoTokenizer
from transformers.tokenization_utils_base import BatchEncoding


class E5Tokenizer:
    
    def __init__(self, tokenizer_path: str) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    def tokenize(self, texts: List[str], prefix: str = "query") -> BatchEncoding:
        input_texts = [f'{prefix}: {text}' for text in texts]
        tokenized_texts = self.tokenizer(input_texts, max_length=512, padding=True, truncation=True, return_tensors='pt')
        return tokenized_texts
