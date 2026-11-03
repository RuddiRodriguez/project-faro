import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from api_objects.faro.connector.output.connector_output import SourceItem
from scout.local_client import LocalKnowledgeBaseClient
from knowledge_search.retrieval.inputs.search_input import SearchInput,SearchFilter
from knowledge_search.retrieval.knowledge_base_retriever import KnowledgeBaseRetriever


class LocalSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        cls.client=LocalKnowledgeBaseClient(index_dir=Path(cls.temp.name))
        cls.items=[SourceItem(id="report/pages",kind="pdf",location="report.pdf",fields=["page","text"],scope_ids=["north"],version="v1")]
        cls.docs=[dict(company_id="new_client",document_id="report/pages/0",title="Operations report",text="Crane idle time is recorded in minutes.",version="v1",source="report.pdf#page 1")]
        cls.key=cls.client.prepare("new_client",cls.items,lambda:cls.docs)

    def retrieve(self,query,ids=None):
        return self.client.retrieve(knowledgeBaseId=self.key,retrievalQuery={"text":query},retrievalConfiguration={"vectorSearchConfiguration":{
            "numberOfResults":1,"filter":{"in":{"key":"AssetId","value":ids or ["report/pages/0"]}}}})

    def test_aws_shape_and_permission_filter(self):
        hit,=self.retrieve("crane idle time")["retrievalResults"]
        self.assertEqual(hit["content"]["type"],"TEXT")
        self.assertEqual(hit["metadata"]["AssetId"],"report/pages/0")
        self.assertEqual(self.retrieve("cranes",["other_client/private"])["retrievalResults"],[])

    def test_saved_passages_reused_for_english_questions(self):
        with patch.object(self.client.embedder,"get_passage_embeddings",side_effect=AssertionError("Rebuilt unchanged index")):
            self.assertEqual(self.client.prepare("new_client",self.items,lambda:self.fail("Reloaded content")),self.key)
            for query in ("crane idle time","hours cranes spend idle"):
                self.assertTrue(self.retrieve(query)["retrievalResults"])
        changed=[self.items[0].model_copy(update={"version":"v2"})]
        self.assertNotEqual(self.client.prepare("new_client",changed,lambda:self.docs),self.key)

    def test_threshold_filters_results(self):
        search=SearchInput(knowledge_base_id=self.key,query="cranes",minimum_relevance_score=1.0,
            scope_filterable_keys=["AssetId"],filters=[SearchFilter(operator="In",key="AssetId",value=["report/pages/0"])])
        self.assertEqual(KnowledgeBaseRetriever(self.client).search(search),[])

    def test_labelled_english_sources(self):
        import json
        data=json.loads((Path(__file__).parent/'data/search_cases.json').read_text())
        docs=[dict(company_id='evaluation',document_id=d['id'],title=d['id'],text=d['text'],
                   page=d['page'],source=d['id']+'.pdf',version='v1') for d in data['documents']]
        items=[self.items[0].model_copy(update={'id':d['id']}) for d in data['documents']]
        key=self.client.prepare('evaluation',items,lambda:docs)
        for case in data['questions']:
            with self.subTest(query=case['query']):
                hits=self.client.retrieve(knowledgeBaseId=key,retrievalQuery={'text':case['query']},retrievalConfiguration={
                    'vectorSearchConfiguration':{'numberOfResults':3,'filter':{'in':{'key':'AssetId','value':[d['document_id'] for d in docs]}}}})['retrievalResults']
                self.assertIn(case['expected'],[h['metadata']['AssetId'] for h in hits])
                for hit in hits:
                    doc=self.client.documents[hit['location']['s3Location']['uri']]
                    expected=next(d for d in data['documents'] if d['id']==doc['document_id'])
                    self.assertEqual(doc['page'],expected['page'])
                    self.assertEqual(doc['text'],expected['text'])
