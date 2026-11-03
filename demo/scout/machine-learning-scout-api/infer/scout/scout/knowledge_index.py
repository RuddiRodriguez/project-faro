from pathlib import Path
import os
import torch
import faiss

torch.set_num_threads(1)
faiss.omp_set_num_threads(1)

DEMO = Path(__file__).resolve().parents[5]
MODEL = Path(os.getenv("FARO_MODEL_PATH", DEMO / "local_data/scout_e5"))
INDEXES = Path(os.getenv("FARO_INDEX_PATH", DEMO / "local_data/scout_source_indexes"))


def reference(document):
    return f"s3://faro-demo/{document['company_id']}/{document['version']}/{document['document_id']}"
