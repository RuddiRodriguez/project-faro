import faiss
import numpy as np
from retrieval_utils.retrieval import Retrieval as BaseRetrieval
from retrieval_utils.index_name import IndexName


class Retrieval(BaseRetrieval):
    """Query retrieval over a saved index, restricted to the permitted rows."""

    def __init__(self, index, ordered_embedding_ids, embedder):
        self.index = index
        self.ordered_embedding_ids = ordered_embedding_ids
        self.embedder = embedder
        self.index_name = IndexName.COSINE_INDEX

    def retrieve(self, stand_alone_query, top_k, permitted_rows):
        params = faiss.SearchParameters()
        params.sel = faiss.IDSelectorBatch(np.asarray(permitted_rows, dtype="int64"))
        embedded_stand_alone_query = self._normalize(self.embedder.get_embedding(stand_alone_query))
        distances, positions = self.index.search(embedded_stand_alone_query.numpy(),
                                                 min(top_k, len(permitted_rows)), params=params)
        return distances[0].tolist(), [self.ordered_embedding_ids[i] for i in positions[0]]
