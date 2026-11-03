"""Copy Luna's actual E5 weights and tokenizer locally, then prepare the company indexes."""
import hashlib
import shutil
from pathlib import Path
from argparse import ArgumentParser

from prepare_scout_runtime import share_openmp


if __name__ == "__main__":
    share_openmp()
    from scout.knowledge_index import MODEL, build_indexes

    parser = ArgumentParser()
    parser.add_argument("--weights", type=Path, default=Path.home() /
                        "machine-learning-luna/luna/predictor_files/e5_embedder/weights")
    args = parser.parse_args()
    MODEL.mkdir(exist_ok=True)
    revision = hashlib.sha256()
    for name in ("config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
                 "special_tokens_map.json", "sentencepiece.bpe.model"):
        dest = MODEL / name
        shutil.copyfile(args.weights / name, dest)
        with dest.open("rb") as file:
            revision.update(hashlib.file_digest(file, "sha256").digest())
    (MODEL / "revision").write_text(revision.hexdigest())
    build_indexes()
