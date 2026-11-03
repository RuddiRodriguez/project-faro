from __future__ import annotations

from typing import Any

from knowledge_search.retrieval.index_hit import IndexHit
from knowledge_search.retrieval.inputs.search_input import SearchFilter, SearchFilterOperator, SearchInput


class KnowledgeBaseRetriever:
    def __init__(self, bedrock_runtime_client):
        self.bedrock_runtime_client = bedrock_runtime_client

    def search(self, search_input: SearchInput) -> list[IndexHit]:
        request: dict[str, Any] = {"knowledgeBaseId": search_input.knowledge_base_id,
                                   "retrievalQuery": {"text": search_input.query},
                                   "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": search_input.top_k}}}
        if search_input.filters:
            request["retrievalConfiguration"]["vectorSearchConfiguration"]["filter"] = self._build_filter(search_input.filters)

        response = self.bedrock_runtime_client.retrieve(**request)
        hits: list[IndexHit] = []
        for item in response.get("retrievalResults", []):
            score = item.get("score")
            if score is None:
                continue
            if search_input.minimum_relevance_score is not None and score < search_input.minimum_relevance_score:
                continue
            hits.append(IndexHit(file_reference=(item.get("location") or {}).get("s3Location", {}).get("uri", ""),
                                 score=score,
                                 metadata=dict(item.get("metadata") or {})))
        return hits

    @staticmethod
    def _build_filter(filters: list[SearchFilter]) -> dict[str, Any]:
        clauses = []
        for search_filter in filters:
            operator = SearchFilterOperator(search_filter.operator)
            clauses.append({operator.bedrock_name: {"key": search_filter.key, "value": search_filter.value}})
        if len(clauses) == 1:
            return clauses[0]
        return {"andAll": clauses}
