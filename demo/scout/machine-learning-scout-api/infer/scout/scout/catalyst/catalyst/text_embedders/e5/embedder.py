import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel
from transformers.tokenization_utils_base import BatchEncoding


class E5Embedder(nn.Module):
    # Copied from: https://huggingface.co/intfloat/multilingual-e5-small
    def __init__(self, embedder_path) -> None:
        super().__init__()
        # ENCODER
        self.embedder_model = AutoModel.from_pretrained(embedder_path)
        self.embedding_size = self.embedder_model.config.hidden_size

    def average_pool(self, last_hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def forward(self, tokenized_output: BatchEncoding) -> torch.Tensor:
        # Compute token embeddings
        with torch.no_grad():
            model_output = self.embedder_model(**tokenized_output)
        
        # Perform pooling
        sentence_embeddings = self.average_pool(model_output.last_hidden_state, tokenized_output['attention_mask'])

        # Normalize embeddings
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

        return sentence_embeddings