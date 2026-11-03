from __future__ import annotations

from knowledge_search.retrieval.search_predictor_output import SearchPredictorOutput
from knowledge_search.retrieval.inputs.search_input import SearchInput
from knowledge_search.retrieval.knowledge_base_retriever import KnowledgeBaseRetriever
from knowledge_search.retrieval.search_validator import Validator


class Predictor:
    def __init__(self,
                 retriever: KnowledgeBaseRetriever,
                 indexer: KnowledgeBaseIndexHandler,
                 ingestion_batch_loader: IngestionBatchLoader) -> None:
        self.retriever = retriever
        self.indexer = indexer
        self.ingestion_batch_loader = ingestion_batch_loader

    def search(self, search_input: SearchInput) -> SearchPredictorOutput:
        validation_error_message = Validator.validate(search_input)
        if validation_error_message is not None:
            return SearchPredictorOutput(error_message=validation_error_message)

        hits = self.retriever.search(search_input)
        return SearchPredictorOutput(hits=hits)
