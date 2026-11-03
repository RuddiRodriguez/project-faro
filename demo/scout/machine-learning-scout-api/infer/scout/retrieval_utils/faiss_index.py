import faiss
from retrieval_utils.index_name import IndexName



class FaissIndex:

    INDEX_NAME_TO_INDEX_CLASS = {IndexName.DOT_PRODUCT_INDEX: faiss.IndexFlatIP,
                                 IndexName.COSINE_INDEX: faiss.IndexFlatIP}

    @staticmethod
    def get_index(index_name: IndexName, dim: int):
        if index_name not in FaissIndex.INDEX_NAME_TO_INDEX_CLASS:
            raise ValueError("Invalid index_name")
        
        return FaissIndex.INDEX_NAME_TO_INDEX_CLASS[index_name](dim)