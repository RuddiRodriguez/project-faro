from pathlib import Path
import torch
import faiss

torch.set_num_threads(1)
faiss.omp_set_num_threads(1)

DEMO = Path(__file__).resolve().parents[5]
MODEL = DEMO / "local_data/scout_e5"
INDEXES = DEMO / "local_data/scout_source_indexes"


def reference(document):
    return f"s3://faro-demo/{document['company_id']}/{document['document_id']}"
