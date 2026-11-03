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
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.revision = (model_path / "revision").read_text().strip()
        self.indexes = {}
        self.documents = {}

    def prepare(self, company, items, load_text):
        # Permissions and source versions are part of the key, including when sources disappear.
        key = hashlib.sha256(json.dumps([company, self.revision,
            [item.model_dump() for item in items]], sort_keys=True).encode()).hexdigest()
        if key in self.indexes:
            return key
        path = self.index_dir / f"{key}.faiss"
        if path.exists():
            docs = json.loads(path.with_suffix(".json").read_text())
            index = faiss.read_index(str(path))
        else:
            docs = load_text()
            vectors = self.embedder.get_passage_embeddings([d["title"] + "\n" + d["text"] for d in docs])
            vectors = vectors.detach().cpu().numpy().astype("float32")
            faiss.normalize_L2(vectors)
            index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(vectors)
            path.with_suffix(".json").write_text(json.dumps(docs, ensure_ascii=False))
            faiss.write_index(index, str(path))
        self.indexes[key] = Retrieval(index, [reference(d) for d in docs], self.embedder), docs
        self.documents.update({reference(d): d for d in docs})
        return key

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
