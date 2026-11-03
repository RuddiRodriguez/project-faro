from nemo.predictor import Predictor as NemoPredictor
from nemo.retrieval.inputs.search_input import SearchFilter, SearchInput
from nemo.retrieval.knowledge_base_retriever import KnowledgeBaseRetriever
from scout.searcher_input import SearcherInput
from scout.searcher_output import SearcherOutput, SearchMatch


class Searcher:
    def __init__(self, client):
        self.client = client
        self.retriever = NemoPredictor(KnowledgeBaseRetriever(client), None, None)

    def search(self, searcher_input: SearcherInput) -> SearcherOutput:
        if not searcher_input.document_ids:
            return SearcherOutput(query=searcher_input.query, matches=[])
        indexed_ids = {doc["document_id"] for doc in self.client.documents.values()
                       if doc["company_id"] == searcher_input.company_id}
        if not indexed_ids.issuperset(searcher_input.document_ids):
            raise RuntimeError("Scout index is out of date; reload the approved documents")
        result = self.retriever.search(SearchInput(
            query=searcher_input.query, knowledge_base_id=searcher_input.company_id,
            top_k=3, minimum_relevance_score=0.74, scope_filterable_keys=["AssetId"],
            filters=[SearchFilter(operator="In", key="AssetId", value=searcher_input.document_ids)]))
        if not result.is_success:
            raise ValueError(result.error_message)
        matches = []
        for hit in result.hits:
            doc = self.client.documents[hit.file_reference]
            matches.append(SearchMatch(document_id=doc["document_id"], source=doc["source"],
                                       file_reference=hit.file_reference, title=doc["title"],
                                       text=doc["text"], version=doc["version"], score=hit.score))
        return SearcherOutput(query=searcher_input.query, matches=matches)
