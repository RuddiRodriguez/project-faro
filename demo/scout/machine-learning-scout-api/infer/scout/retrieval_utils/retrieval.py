from typing import List, Tuple

import torch

from retrieval_utils.embedder import Embedder
from retrieval_utils.embedding import Embedding
from retrieval_utils.faiss_index import FaissIndex, IndexName


class Retrieval:
    def __init__(self, embeddings: List[Embedding], embedder: Embedder, index_name: IndexName) -> None:
        self.embeddings = embeddings
        self.ordered_embedding_ids, self.ordered_embeddings = self._get_ordered_kb_embedding()

        self.embedder = embedder

        self.index_name = index_name
        self.index = FaissIndex.get_index(index_name=self.index_name, dim=self.embedder.dim)
        self.should_normalized = self.index_name in {IndexName.COSINE_INDEX}

        self._add_embeddings_to_index()
        
       
    def _add_embeddings_to_index(self):
        if self.should_normalized:
            self.ordered_normalized_embeddings = self._normalize(self.ordered_embeddings)
            self.index.add(self.ordered_normalized_embeddings)
        else:
           self.index.add(self.ordered_embeddings) 
        

    def _normalize(self, embeddings: torch.Tensor) -> torch.Tensor:
        if self.index_name==IndexName.COSINE_INDEX:
            return torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return embeddings

    def _get_ordered_kb_embedding(self) -> Tuple[List[int], torch.Tensor]:
        embedding_ids = list()
        embeddings_as_list = list()

        for embedding in self.embeddings:
            embedding_ids.append(embedding.id)
            embeddings_as_list.append(embedding.embedding.squeeze(0))
        
        embeddings = torch.stack(embeddings_as_list)
        return embedding_ids, embeddings

    
    def retrieve(self, stand_alone_query: str, top_k: int) -> Tuple[List[float], List[int]]:
        top_k = min(len(self.ordered_embedding_ids), top_k)
        embedded_stand_alone_query = self.embedder.get_embedding(stand_alone_query)

        if self.should_normalized:
            embedded_stand_alone_query = self._normalize(embedded_stand_alone_query)

        top_k_distances, top_k_idxs = self.index.search(embedded_stand_alone_query, top_k) # Shape: np.array(1, top_k), np.array(1, top_k)
        top_k_distances = top_k_distances.squeeze().tolist()
        top_k_idxs = top_k_idxs.squeeze().tolist()

        top_k_embedding_ids = [self.ordered_embedding_ids[idx] for idx in top_k_idxs]

        return top_k_distances, top_k_embedding_ids
    