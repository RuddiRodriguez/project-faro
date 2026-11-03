from nemo.predictor import Predictor as NemoPredictor
from nemo.retrieval.inputs.search_input import SearchFilter, SearchInput
from nemo.retrieval.knowledge_base_retriever import KnowledgeBaseRetriever
from scout.predictor_input import PredictorInput
from scout.predictor_output import PredictorOutput, SearchMatch


class Predictor:
    def __init__(self, client):
        self.client = client
        self.search = NemoPredictor(KnowledgeBaseRetriever(client), None, None)

    def predict(self, predictor_input: PredictorInput) -> PredictorOutput:
        if not predictor_input.document_ids:
            return PredictorOutput(query=predictor_input.query, matches=[])
        indexed_ids = {doc["document_id"] for doc in self.client.documents.values()
                       if doc["company_id"] == predictor_input.company_id}
        if not indexed_ids.issuperset(predictor_input.document_ids):
            raise RuntimeError("Scout index is out of date; reload the approved documents")
        result = self.search.search(SearchInput(
            query=predictor_input.query, knowledge_base_id=predictor_input.company_id,
            top_k=3, minimum_relevance_score=0.74, scope_filterable_keys=["AssetId"],
            filters=[SearchFilter(operator="In", key="AssetId", value=predictor_input.document_ids)]))
        if not result.is_success:
            raise ValueError(result.error_message)
        matches = []
        for hit in result.hits:
            doc = self.client.documents[hit.file_reference]
            matches.append(SearchMatch(document_id=doc["document_id"], source=doc["source"],
                                       file_reference=hit.file_reference, title=doc["title"],
                                       text=doc["text"], version=doc["version"], score=hit.score))
        return PredictorOutput(query=predictor_input.query, matches=matches)
