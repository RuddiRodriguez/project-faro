"""Compare meaning search, combined search, and optional reranking on labelled test documents."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from api_objects.faro.connector.output.connector_output import SourceItem
from scout.local_client import LocalKnowledgeBaseClient

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--rerank', action='store_true')
parser.add_argument('--output', type=Path, required=True)
args=parser.parse_args()
data=json.loads((ROOT/'scout/machine-learning-scout-api/tests/data/search_cases.json').read_text())
reranker=None
if args.rerank:
    from sentence_transformers import CrossEncoder
    reranker=CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')
with TemporaryDirectory() as directory:
    client=LocalKnowledgeBaseClient(index_dir=Path(directory))
    docs=[dict(company_id='evaluation',document_id=d['id'],source_id=d['id'],title=d['id'],text=d['text'],
               page=d['page'],source=d['id']+'.pdf',version='v1') for d in data['documents']]
    items=[SourceItem(id=d['id'],kind='pdf',location=d['id']+'.pdf',fields=['page','text'],scope_ids=['test'],version='v1') for d in data['documents']]
    key=client.prepare('evaluation',items,lambda:docs)
    results=[]
    for case in data['questions']:
        start=perf_counter()
        scores,refs=client.indexes[key][0].retrieve(case['query'],3,list(range(len(docs))))
        semantic=[client.documents[ref]['document_id'] for score,ref in zip(scores,refs) if score>=.74]
        semantic_ms=(perf_counter()-start)*1000
        start=perf_counter()
        hits=client.retrieve(knowledgeBaseId=key,retrievalQuery={'text':case['query']},retrievalConfiguration={
            'vectorSearchConfiguration':{'numberOfResults':10,'filter':{'in':{'key':'AssetId','value':[d['document_id'] for d in docs]}}}})['retrievalResults']
        combined=[hit['metadata']['AssetId'] for hit in hits]
        result=dict(**case,semantic=semantic,semantic_without_cutoff=[client.documents[ref]["document_id"] for ref in refs],combined=combined[:3],semantic_ms=semantic_ms,combined_ms=(perf_counter()-start)*1000)
        if reranker and hits:
            start=perf_counter()
            scores=reranker.predict([(case['query'],hit['content']['text']) for hit in hits])
            result.update(reranked=[combined[i] for i in sorted(range(len(hits)),key=lambda i:scores[i],reverse=True)[:3]],rerank_ms=(perf_counter()-start)*1000)
        results.append(result)
    report=dict(note='Constructed evaluation documents, not client production evidence. Expected source IDs are explicitly labelled.',cases=results)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False))
    for method in ('semantic','semantic_without_cutoff','combined','reranked'):
        available=[r for r in results if method in r]
        if available:
            print(method, 'first:',sum(bool(r[method]) and r[method][0]==r['expected'] for r in available),
                  'top three:',sum(r['expected'] in r[method] for r in available),'/',len(available),flush=True)
