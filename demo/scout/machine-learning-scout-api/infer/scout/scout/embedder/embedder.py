import torch

from retrieval_utils.embedder import Embedder
from scout.catalyst.catalyst.text_embedders.e5.embedder import E5Embedder
from scout.catalyst.catalyst.text_embedders.e5.tokenizer import E5Tokenizer


class E5SmallEmbedder(Embedder):
    def __init__(self, model_path):
        self.tokenizer = E5Tokenizer(str(model_path))
        self.embedder = E5Embedder(str(model_path)).eval()
        self.dim = self.embedder.embedding_size

    def get_embedding(self, text: str) -> torch.Tensor:
        tokenized_text = self.tokenizer.tokenize([text])
        return self.embedder(tokenized_text)

    def get_passage_embeddings(self, texts: list[str]) -> torch.Tensor:
        return self.embedder(self.tokenizer.tokenize(texts, "passage"))
