import hashlib
import json
from collections import defaultdict
from pathlib import Path

import faiss
import torch

from retrieval_utils.embedding import Embedding
from retrieval_utils.index_name import IndexName
from retrieval_utils.retrieval import Retrieval
from scout.embedder.embedder import E5SmallEmbedder

torch.set_num_threads(1)
faiss.omp_set_num_threads(1)

DEMO = Path(__file__).resolve().parents[5]
MODEL = DEMO / "local_data/scout_e5"
INDEXES = DEMO / "local_data/scout_indexes"
DOCUMENTS = DEMO / "local_data/demo_dataset/documents.json"


def reference(document):
    return f"s3://faro-demo/{document['company_id']}/{document['document_id']}.txt"


def build_indexes():
    embedder = E5SmallEmbedder(MODEL)
    companies = defaultdict(list)
    for doc in json.loads(DOCUMENTS.read_text()):
        if doc["status"] == "approved":
            companies[doc["company_id"]].append(doc)
    INDEXES.mkdir(exist_ok=True)
    for company, docs in companies.items():
        vectors = embedder.get_passage_embeddings([d["title"] + "\n" + d["text"] for d in docs])
        embeddings = [Embedding(id=d["document_id"], embedding=vector.unsqueeze(0))
                      for d, vector in zip(docs, vectors, strict=True)]
        retrieval = Retrieval(embeddings=embeddings, embedder=embedder, index_name=IndexName.COSINE_INDEX)
        index = retrieval.index
        path = INDEXES / f"{company}.faiss"
        faiss.write_index(index, str(path))
        manifest = {"model": (MODEL / "revision").read_text().strip(),
                    "index_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "documents": docs}
        path.with_suffix(".json").write_text(json.dumps(manifest, ensure_ascii=False))
        print(f"{company}: {index.ntotal} passages")
