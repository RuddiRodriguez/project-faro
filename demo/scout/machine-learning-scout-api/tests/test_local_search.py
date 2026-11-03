import unittest
from unittest.mock import patch

from scout.embedder.embedder import E5SmallEmbedder

from knowledge_search.retrieval.inputs.search_input import SearchInput, SearchFilter
from knowledge_search.retrieval.knowledge_base_retriever import KnowledgeBaseRetriever
from scout.local_client import LocalKnowledgeBaseClient


class LocalSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(E5SmallEmbedder, "get_embedding", side_effect=AssertionError("Query at startup")), \
             patch.object(E5SmallEmbedder, "get_passage_embeddings", side_effect=AssertionError("Passage at startup")):
            cls.client = LocalKnowledgeBaseClient()

    def test_aws_shape_and_scope_before_ranking(self):
        result = self.client.retrieve(
            knowledgeBaseId="harbor", retrievalQuery={"text": "moves per working hour"},
            retrievalConfiguration={"vectorSearchConfiguration": {
                "numberOfResults": 1, "filter": {"in": {"key": "AssetId",
                    "value": ["harbor_idle_time_v1", "pacific_moves_per_hour_v1"]}}}})
        hit, = result["retrievalResults"]
        self.assertEqual(hit["metadata"]["AssetId"], "harbor_idle_time_v1")
        self.assertEqual(hit["content"]["type"], "TEXT")
        self.assertEqual(hit["location"]["type"], "S3")
        self.assertIn("s3Location", hit["location"])

    def test_only_question_is_embedded_during_search(self):
        with patch.object(self.client.embedder, "get_embedding", wraps=self.client.embedder.get_embedding) as calls, \
             patch.object(self.client.embedder, "get_passage_embeddings", side_effect=AssertionError("Passage at search")):
            self.client.retrieve(knowledgeBaseId="harbor", retrievalQuery={"text": "Movimientos por hora"},
                retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 1,
                    "filter": {"in": {"key": "AssetId", "value": ["harbor_moves_per_hour_v1"]}}}})
        self.assertEqual(calls.call_count, 1)
        calls.assert_called_once_with("Movimientos por hora")

    def test_knowledge_search_threshold_discards_real_low_score(self):
        search = SearchInput(knowledge_base_id="harbor", query="moves per working hour",
                             minimum_relevance_score=1.0, scope_filterable_keys=["AssetId"],
                             filters=[SearchFilter(operator="In", key="AssetId",
                                                   value=["harbor_idle_time_v1"])])
        self.assertEqual(KnowledgeBaseRetriever(self.client).search(search), [])
