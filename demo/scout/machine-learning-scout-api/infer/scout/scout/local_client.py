import hashlib
import json

import faiss
from scout.retrieval import Retrieval

from scout.knowledge_index import INDEXES, MODEL, reference
from scout.embedder.embedder import E5SmallEmbedder


class LocalKnowledgeBaseClient:
    """The subset of Bedrock Retrieve used by Scout, backed by saved company indexes."""

    def __init__(self, index_dir=INDEXES, model_path=MODEL):
        self.embedder = E5SmallEmbedder(model_path)
        revision = (model_path / "revision").read_text().strip()
        self.indexes = {}
        self.documents = {}
        for path in index_dir.iterdir():
            if path.suffix != ".faiss":
                continue
            manifest = json.loads(path.with_suffix(".json").read_text())
            if (manifest["model"] != revision or
                    manifest["index_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest()):
                raise ValueError(f"Rebuild Scout index for {path.stem}")
            docs = manifest["documents"]
            index = faiss.read_index(str(path))
            if index.ntotal != len(docs) or any(d["company_id"] != path.stem for d in docs):
                raise ValueError(f"Invalid Scout index for {path.stem}")
            self.indexes[path.stem] = Retrieval(index, [reference(d) for d in docs], self.embedder), docs
            self.documents.update({reference(d): d for d in docs})

    def retrieve(self, *, knowledgeBaseId, retrievalQuery, retrievalConfiguration):
        settings = retrievalConfiguration["vectorSearchConfiguration"]
        clause = settings["filter"]["in"]
        if clause["key"] != "AssetId":
            raise ValueError("Expected an AssetId filter")
        retrieval, docs = self.indexes[knowledgeBaseId]
        allowed = set(clause["value"])
        rows = [i for i, doc in enumerate(docs) if doc["document_id"] in allowed]
        if not rows:
            return {"retrievalResults": []}
        scores, references = retrieval.retrieve(retrievalQuery["text"], settings["numberOfResults"], rows)
        results = []
        for score, uri in zip(scores, references):
            doc = self.documents[uri]
            results.append({"content": {"type": "TEXT", "text": doc["title"] + "\n" + doc["text"]},
                            "location": {"type": "S3", "s3Location": {"uri": reference(doc)}},
                            "metadata": {"AssetId": doc["document_id"], "version": doc["version"]},
                            "score": float(score)})
        return {"retrievalResults": results}
