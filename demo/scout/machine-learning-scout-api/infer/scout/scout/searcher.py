from threading import Lock
from utils.connector_client import sources
from knowledge_search.predictor import Predictor as SearchPredictor
from knowledge_search.retrieval.inputs.search_input import SearchFilter, SearchInput
from knowledge_search.retrieval.knowledge_base_retriever import KnowledgeBaseRetriever
from scout.searcher_input import SearcherInput
from scout.searcher_output import SearcherOutput, SearchMatch


class Searcher:
    def __init__(self, client):
        self.client = client
        self.lock = Lock()
        self.retriever = SearchPredictor(KnowledgeBaseRetriever(client), None, None)

    def search(self, searcher_input: SearcherInput) -> SearcherOutput:
        request = searcher_input
        items = sources(request.company_id, request.permitted_scope_ids).items
        if not items:
            return SearcherOutput(query=request.query, matches=[])
        def load_text():
            docs = []
            for item in items:
                text = "Fields: " + ", ".join(item.fields)
                if item.kind == "pdf":
                    pages = sources(request.company_id, request.permitted_scope_ids, "read", item.id)
                    text += "\n" + "\n".join(row["text"] for row in pages.rows)
                # Keep every passage tied to the exact connected source version.
                for number, offset in enumerate(range(0, len(text), 1200)):
                    docs.append(dict(document_id=f"{item.id}/{number}", company_id=request.company_id,
                        source=item.location, title=item.id, text=text[offset:offset+1200], version=item.version))
            return docs
        with self.lock:
            key = self.client.prepare(request.company_id, items, load_text)
            docs = self.client.indexes[key][1]
            result = self.retriever.search(SearchInput(
                query=request.query, knowledge_base_id=key,
                top_k=3, minimum_relevance_score=0.74, scope_filterable_keys=["AssetId"],
                filters=[SearchFilter(operator="In", key="AssetId", value=[d["document_id"] for d in docs])]))
        if not result.is_success:
            raise ValueError(result.error_message)
        matches = []
        for hit in result.hits:
            doc = self.client.documents[hit.file_reference]
            matches.append(SearchMatch(document_id=doc["document_id"], source=doc["source"],
                                       file_reference=hit.file_reference, title=doc["title"],
                                       text=doc["text"], version=doc["version"], score=hit.score))
        return SearcherOutput(query=searcher_input.query, matches=matches)
