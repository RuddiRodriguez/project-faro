"""Prepare local E5 weights and indexes from a supplied folder or the public checkpoint."""
import hashlib
import shutil
from pathlib import Path
from argparse import ArgumentParser

from prepare_scout_runtime import share_openmp


if __name__ == "__main__":
    share_openmp()
    from scout.knowledge_index import MODEL, build_indexes

    parser = ArgumentParser()
    parser.add_argument("--weights", type=Path, help="Existing Luna-compatible multilingual E5 small weights")
    args = parser.parse_args()
    if args.weights is None:
        from huggingface_hub import snapshot_download
        args.weights = Path(snapshot_download("intfloat/multilingual-e5-small",
            revision="614241f622f53c4eeff9890bdc4f31cfecc418b3",
            allow_patterns=["config.json","model.safetensors","tokenizer.json","tokenizer_config.json",
                            "special_tokens_map.json","sentencepiece.bpe.model"]))
    MODEL.mkdir(parents=True, exist_ok=True)
    revision = hashlib.sha256()
    for name in ("config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
                 "special_tokens_map.json", "sentencepiece.bpe.model"):
        dest = MODEL / name
        shutil.copyfile(args.weights / name, dest)
        with dest.open("rb") as file:
            revision.update(hashlib.file_digest(file, "sha256").digest())
    (MODEL / "revision").write_text(revision.hexdigest())
    build_indexes()
